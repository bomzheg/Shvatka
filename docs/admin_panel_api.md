# Admin Panel API

Reference for the web UI that drives Shvatka's admin panel. Covers the
superuser-gated `/admin/*` endpoints, the `is_admin` flag the UI uses to decide
whether to render admin controls, and the shared response shapes.

> Base path: all admin endpoints are served under the API's `context_path`
> (empty by default), same host as the rest of the REST API.

## Authorisation

- **Who is an admin.** Admins ("superusers") are configured by **telegram id**
  in the top-level `superusers:` list of the server config. There is no admin
  flag stored per user — membership in that list is the single source of truth.
- **How requests authenticate.** Exactly like the rest of the API: the JWT is
  sent in the `Authorization` cookie (`Authorization: bearer <token>`), set by
  the normal login flows (`/auth/...`). The cookie is `httpOnly`, so the UI
  cannot read the token or its claims directly — use `is_admin` (below).
- **Enforcement.** Every `/admin/*` route requires the caller to be a superuser.
  Non-superuser callers get **403**; unauthenticated callers get **404**
  (player not found). Enforcement is server-side on every route — the UI must
  never treat `is_admin` as a security boundary, only as a rendering hint.

### Telling the UI whether to show admin controls: `is_admin`

`GET /users/me` returns the current player with an `is_admin` boolean. The UI
already calls this to render the profile, so gate admin buttons on it:

```jsonc
GET /users/me
{
  "id": 42,
  "can_be_author": true,
  "name_mention": "harry",
  "username": "harry",
  "tg": { "tg_id": 666, "username": "harry", "first_name": "Harry", "last_name": "Potter" },
  "forum": null,
  "email": null,
  "is_admin": true          // ← render admin UI only when true
}
```

`is_admin` is `true` when the player's linked telegram id is in the configured
superusers list. It is also present on the admin player-detail responses, so an
admin can see whether *another* player is an admin.

## Shared response shapes

```jsonc
// Player (compact)
{ "id": 1, "can_be_author": true, "name_mention": "harry", "username": "harry" }

// TgUser
{ "tg_id": 666, "username": "harry", "first_name": "Harry", "last_name": "Potter" }

// ForumUser
{ "name": "harry" }

// EmailAccount
{ "email": "harry@example.org", "is_verified": true }

// Team
{ "id": 3, "name": "DreamTeam", "captain": { /* Player */ }, "description": "…" }

// Items<T> (list envelope)
{ "items": [ /* T, … */ ] }
```

`Played` (poll/waiver vote) is one of: `"yes"`, `"no"`, `"think"`,
`"revoked"`, `"not_allowed"`.

## Endpoints

### Players

#### `GET /admin/players` — list / search players

Query params (all optional):

| param | type | default | meaning |
|---|---|---|---|
| `username` | string | – | substring match on the player's shvatka username |
| `name` | string | – | substring match on the linked telegram first/last/username |
| `active` | bool | `true` | include players who can log in (have tg or email) |
| `archive` | bool | `false` | include archived players (no tg and no email) |
| `can_be_author` | bool | – | filter by author rights; `true` = **only promoted users** |

Response `Items<AdminPlayer>`:

```jsonc
{ "items": [
  { "id": 1, "can_be_author": true, "name_mention": "harry", "username": "harry",
    "tg": { /* TgUser */ }, "forum": null }
] }
```

> Note: the list does **not** include email (to avoid per-row lookups). Fetch
> the detail endpoint for email + `is_admin`.

#### `GET /admin/players/{id}` — player detail

Response `PlayerWithIdentities`:

```jsonc
{ "id": 1, "can_be_author": true, "name_mention": "harry", "username": "harry",
  "tg": { /* TgUser|null */ }, "forum": { /* ForumUser|null */ },
  "email": { "email": "harry@example.org", "is_verified": true },  // or null
  "is_admin": true }
```

Errors: `404` if the player does not exist.

#### `POST /admin/players/{id}/one-time-link` — create & copy a login link

Mints a one-time login link the admin can hand to the player (they open it and
are logged in as that player). No body.

```jsonc
{ "url": "https://<web>/auth/one-time-token?token=<opaque>" }
```

The token is single-use and short-lived. Errors: `404` if the player does not
exist.

#### `PUT /admin/players/{id}/email` — set / change email

Body:

```jsonc
{ "email": "new@example.org", "verified": false }
```

- `verified: true` — the email is stored **already confirmed** (admin vouches
  for it).
- `verified: false` — stored **unverified**; the panel does **not** send a
  confirmation code. The player triggers confirmation themselves via the normal
  `/auth/email/resend` + `/auth/email/confirm` flow.

Replaces any existing email on the player. Response `EmailAccount`:

```jsonc
{ "email": "new@example.org", "is_verified": false }
```

Errors: `422` invalid email; `409` email already used by **another** player;
`404` player not found.

#### `PUT /admin/players/{id}/tg` — relink telegram

Attaches a (different) telegram account to the player, replacing any current
one. Body:

```jsonc
{ "tg_id": 555000111, "username": "new_handle", "first_name": "New", "last_name": null }
```

`username`, `first_name`, `last_name` are optional. Response is the updated
`PlayerWithIdentities`. Errors: `409` if that telegram account is already linked
to **another** player; `404` player not found.

### Poll (pre-game participation votes)

The "poll" is the live pre-game vote where players mark whether they will play.
Entries live per team, keyed by the current game context.

#### `GET /admin/poll` — show poll entries

Response `AdminPoll` — teams, each with their vote entries:

```jsonc
{ "teams": [
  { "team": { /* Team */ },
    "entries": [
      { "player": { /* Player */ }, "vote": "yes" },
      { "player": { /* Player */ }, "vote": "think" }
    ] }
] }
```

Returns `{ "teams": [] }` when nobody has voted.

#### `DELETE /admin/poll/{team_id}/players/{player_id}` — remove a poll entry

Removes one player's poll vote for a team. Returns **204 No Content**.
Idempotent — deleting a non-existent entry still returns 204.

### Merge (destructive)

Both merges fold a `secondary` record into a `primary` one and then **delete
the secondary**. They are irreversible — the UI should require an explicit
confirmation. Same body shape for both:

```jsonc
{ "primary_id": 1, "secondary_id": 2 }   // 2 is merged into 1, then deleted
```

#### `POST /admin/players/merge`

Moves the secondary player's games, levels, keys, org roles, waivers, forum
identity and team history onto the primary, then deletes the secondary.
Constraints (else `422`): the secondary must have **no telegram account**
(typically a forum-only player), and the primary must have **no forum identity**
already. `primary_id == secondary_id` → `422`. Missing id → `404`. Response is
the primary `Player`.

> A merge can also fail (`500`) if the two players' team histories overlap in
> time and can't be ordered automatically — surface a "couldn't merge
> automatically" message if that happens.

#### `POST /admin/teams/merge`

Moves the secondary team's waivers, keys, level times, players and forum team
onto the primary, then deletes the secondary. Constraints (else `422`): the
secondary must have **no active chat**, and the primary must have **no forum
team** already. `primary_id == secondary_id` → `422`. Missing id → `404`.
Response is the primary `Team`.

### Waivers (approved rosters)

#### `GET /admin/waivers/game/{id}` — approved waivers for a game

Read-only view of who is confirmed to play a given game, grouped by team.
Response `WaiversDto`:

```jsonc
{ "teams": [ { /* Team */ } ],
  "waivers": { "3": [ { "player": { /* Player */ } } ] } }  // keyed by team id
```

Errors: `404` if the game does not exist.

## Error format

Domain errors come back with the standard API error envelope and an
appropriate status (`403` admin required, `404` not found, `409` conflict,
`422` validation):

```jsonc
{ "type": "NotAuthorizedForAdmin", "text": "…", "description": "…", "properties": { … } }
```

The UI should branch on **HTTP status**; `type`/`description` are for
diagnostics and user-facing messages.

## Current admin use cases

What the panel is expected to let a superuser do today (phase 1):

1. **Find a player** — search/list, optionally filtered to promoted users
   (`can_be_author=true`), then open a player's detail.
2. **Log in as a player / hand them access** — create a one-time login link and
   copy it (e.g. to help a user who can't log in).
3. **Fix a player's email** — set or replace it, choosing whether it counts as
   verified; if not, the user confirms it themselves.
4. **Fix a player's telegram** — relink to the correct telegram account.
5. **Moderate the poll** — see who voted for the current game per team and
   remove a stray/incorrect entry.
6. **Inspect approved waivers** — read the confirmed roster for any game.
7. **Merge duplicates** — fold a duplicate player or team into the canonical
   one (e.g. a forum-only player into their telegram player). Destructive —
   confirm first.

### Not yet available (planned)

- Promote / demote authors from the panel (today you can only *see* promoted
  users via the `can_be_author` filter).
- Removing **approved** waiver entries (only poll entries can be removed today).
