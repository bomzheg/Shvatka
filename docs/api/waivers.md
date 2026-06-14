# Waivers REST API — UI contract

Contract for the team‑waiver endpoints used by the web UI.

A *waiver* is a per‑game declaration of which players of a team intend to play
(and with what status). The endpoints below let a team manage the waivers of
**its own** team for the **current** (active) game and read the waivers of any
game by id.

## Conventions

- Base path: the API root (the same origin the UI already talks to).
- All bodies are JSON; send `Content-Type: application/json`.
- Timestamps (where present in shared models) are ISO‑8601.
- Trailing slashes are not required; the routes are exact.

### Authentication

Send the access token the same way as for every other authenticated call —
either:

- the auth cookie set by `POST /auth/token`, or
- an `Authorization: Bearer <access_token>` header.

Unauthenticated requests to the protected endpoint resolve to `401`.

### Permissions

Replacing waivers requires the caller to be a member of the team **and** to be
allowed to manage waivers, i.e. either:

- the **captain** of the team, or
- a team player with the `can_manage_waivers` permission.

A caller without that permission gets `422` (`PermissionsError`). A caller who
is not in any team gets `422` (`PlayerNotInTeam`).

## Shared models

### Player

```json
{
  "id": 42,
  "can_be_author": true,
  "name_mention": "Harry"
}
```

### Team

```json
{
  "id": 7,
  "name": "Gryffindor",
  "captain": { "id": 42, "can_be_author": true, "name_mention": "Harry" },
  "description": "best team"
}
```

`captain` and `description` may be `null`.

### Played (enum)

The participation status of a player in a game. One of:

| value         | meaning                                   |
|---------------|-------------------------------------------|
| `yes`         | will play                                 |
| `no`          | will not play                             |
| `think`       | undecided                                 |
| `revoked`     | not allowed by the captain                |
| `not_allowed` | not allowed by the organizers             |

Only players with `played = "yes"` are surfaced by the read endpoints
(see below).

---

## PUT /waivers/game/current

Replace **all** waivers of the caller's team for the **current** (active) game.

This is a full replace, not a merge:

- players present in the request are created/updated with the given `played`
  status;
- players that currently have a waiver but are **absent** from the request are
  removed.

### Request body

```json
{
  "waivers": [
    { "player_id": 42, "played": "yes" },
    { "player_id": 43, "played": "no" }
  ]
}
```

- `waivers` — array, may be empty (an empty array clears the team's waivers).
- `player_id` — required; must be a player **of the caller's team**.
- `played` — optional, defaults to `"yes"`; one of the `Played` values.

### Response `200`

The resulting waivers of the team (`TeamWaivers`):

```json
{
  "team": {
    "id": 7,
    "name": "Gryffindor",
    "captain": { "id": 42, "can_be_author": true, "name_mention": "Harry" },
    "description": null
  },
  "players": [
    { "player": { "id": 42, "can_be_author": true, "name_mention": "Harry" }, "played": "yes" },
    { "player": { "id": 43, "can_be_author": false, "name_mention": "Ron" }, "played": "no" }
  ]
}
```

### Errors

| status | when                                                                 |
|--------|----------------------------------------------------------------------|
| `401`  | not authenticated                                                    |
| `422`  | caller not in a team (`PlayerNotInTeam`)                             |
| `422`  | caller lacks `can_manage_waivers` (`PermissionsError`)              |
| `422`  | a `player_id` does not belong to the caller's team (`PlayerNotInTeam`) |
| `422`  | there is no active game (`HaveNotActiveGame`)                        |

---

## GET /waivers/game/current

Read the waivers of the **current** (active) game, for **all** teams that have
at least one player with `played = "yes"`.

### Response `200`

`WaiversDto` — the list of teams plus a map keyed by **team id** (as a string in
JSON) to the players that play:

```json
{
  "teams": [
    {
      "id": 7,
      "name": "Gryffindor",
      "captain": { "id": 42, "can_be_author": true, "name_mention": "Harry" },
      "description": null
    }
  ],
  "waivers": {
    "7": [
      { "player": { "id": 42, "can_be_author": true, "name_mention": "Harry" } }
    ]
  }
}
```

If there is **no active game** the endpoint returns `200` with a `null` body.

> Note: this read view only contains players with `played = "yes"`. The
> per‑player `played` value is therefore omitted here (it is always `yes`).

---

## GET /waivers/game/{id}

Same shape and semantics as `GET /waivers/game/current`, but for a specific
(usually past) game identified by `{id}`.

### Path parameters

- `id` — the game id (integer).

### Response `200`

`WaiversDto`, identical structure to the current‑game read above.

### Errors

| status | when                          |
|--------|-------------------------------|
| `404`  | no game with the given `id`   |

---

## Error payload

Domain errors (the `422`/`404` rows above, except FastAPI validation errors)
share this shape:

```json
{
  "type": "PermissionsError",
  "text": "...",
  "description": "human readable, safe to show to the user",
  "properties": {},
  "confidential": null
}
```

- `type` — the error class name, stable enough to branch on in the UI.
- `description` — localized, user‑facing message.

Malformed request bodies (wrong types, missing `player_id`, unknown `played`
value) produce FastAPI's standard `422` validation error payload.
