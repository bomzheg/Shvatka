# Admin Panel — API changes for the UI

What changed in the REST API that the web UI needs to adopt. This is the delta
(a changelog); for the full endpoint reference see
[`admin_panel_api.md`](./admin_panel_api.md). Nothing here is a breaking change
to existing endpoints — everything is additive.

## Phase 1

### `/users/me` gained an `is_admin` flag (adopt this first)

`GET /users/me` now returns an extra boolean, `is_admin`:

```jsonc
{
  "id": 42, "can_be_author": true, "name_mention": "harry", "username": "harry",
  "tg": { … }, "forum": null, "email": null,
  "is_admin": true            // ← NEW
}
```

- **Use it to decide whether to render admin UI** (buttons, an "Admin" nav entry,
  etc.). The field is `true` when the logged-in player's telegram id is in the
  server's configured superusers.
- The auth cookie is `httpOnly`, so the UI can't read admin status from the
  token — this flag is the intended channel.
- It is **only a rendering hint, not a security boundary**: every `/admin/*`
  endpoint is enforced server-side and returns `403` for non-admins even if the
  UI shows the controls.

Existing `/users/me` consumers keep working — the field is just added.

### New superuser-only admin surface: `/admin/*`

All new, all requiring the caller to be a superuser (authenticated via the same
cookie as the rest of the API). Non-admin → `403`; unauthenticated → `404`.

| Method | Path | What the UI can now do |
|---|---|---|
| GET | `/admin/players` | player list + search; filter `can_be_author=true` to show promoted users |
| GET | `/admin/players/{id}` | player detail: identities, email, `is_admin` |
| POST | `/admin/players/{id}/one-time-link` | get a one-time login link to copy/hand to a player |
| PUT | `/admin/players/{id}/email` | set/replace a player's email (`{email, verified}`) |
| PUT | `/admin/players/{id}/tg` | relink a player's telegram account |
| GET | `/admin/poll` | show the current participation poll per team |
| DELETE | `/admin/poll/{team_id}/players/{player_id}` | remove one poll entry |
| GET | `/admin/waivers/game/{id}` | view approved waivers for a game |

New response shapes the UI will render: `AdminPlayer` (list row),
`PlayerWithIdentities` (detail, now with `is_admin`), `OneTimeLink` (`{url}`),
`AdminPoll` (teams → entries), and the existing `EmailAccount` / `Team` /
`WaiversDto`. See the reference doc for exact fields.

New request bodies: `{email, verified}` for email; `{tg_id, username?,
first_name?, last_name?}` for tg.

### Error codes the UI should handle on these endpoints

- `403` — caller isn't an admin.
- `404` — target player/game not found.
- `409` — email already used by another player; or the telegram account is
  already linked to another player.
- `422` — invalid email.

Error bodies use the standard envelope (`{type, text, description, properties}`);
branch on the **HTTP status**, surface `description` to the user if helpful.

## Phase 2

### Two new destructive endpoints: merge

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/players/merge` | fold a secondary player into a primary, then delete the secondary |
| POST | `/admin/teams/merge` | fold a secondary team into a primary, then delete the secondary |

Both take the same body and are **irreversible — require an explicit
confirmation in the UI** before calling:

```jsonc
{ "primary_id": 1, "secondary_id": 2 }   // 2 is merged into 1, then deleted
```

- `POST /admin/players/merge` → returns the primary `Player`. `422` if the
  secondary still has a telegram account or the primary already has a forum
  identity, or if `primary_id == secondary_id`; `404` for a missing id.
  A `500` "couldn't merge automatically" is possible if the two players' team
  histories overlap in time — surface that message and don't retry blindly.
- `POST /admin/teams/merge` → returns the primary `Team`. `422` if the secondary
  still has an active chat or the primary already has a forum team, or if
  `primary_id == secondary_id`; `404` for a missing id.

No other endpoints changed in phase 2.

## Quick adoption checklist for the UI

1. Read `is_admin` from `/users/me`; gate all admin UI on it.
2. Build the players view on `GET /admin/players` (+ `can_be_author` filter) and
   the detail on `GET /admin/players/{id}`.
3. Wire the per-player actions: one-time link, change email, change tg.
4. Add the poll moderation view (`GET /admin/poll` + `DELETE …`).
5. Add merge flows with a confirmation dialog (players and teams).
6. Handle `403/404/409/422` per the tables above; treat server enforcement as
   authoritative regardless of what the UI renders.
