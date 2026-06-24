# Notifications & Requests — design plan

> Status: **planning only, no code yet.** This document proposes how to add a
> "notifications" tab to the web frontend, backed by persistent storage, that
> covers both *informational* notifications and *actionable* user-to-user
> requests (team-join invites, join requests, org invites, …).

## 1. Scope & terminology

The feature the user describes is really **two related things**. Keeping them
separate in the data model avoids a lot of nullable-column pain later.

| Concept | Examples | Needs a decision from the recipient? | Mutable? |
|---|---|---|---|
| **Notification** (informational feed / inbox) | "org added to game", "player joined team", "player left team", "captain renamed team", "schedule changed" | No | Only `read_at` flips |
| **Request** (user → user, actionable) | captain invites player to team; player asks to join a team; invite player to be an org | Yes (accept / decline) | Yes — has a state machine |

Recommendation: model them as **two tables** —
`notifications` (the append-only feed shown in the tab) and `action_requests`
(the low-volume state machine). A notification row *may* reference a request,
so the tab can render both kinds from a single query while the request keeps
its own lifecycle.

Why not one table? An actionable request needs `status`, dedup of pending
items, expiry, and to be queryable by the *sender* too ("my outgoing
invites"). Folding that into an append-only feed forces several nullable
columns and an awkward unique index over rows that are otherwise immutable. Two
tables keep each one simple. (A single-table variant is described in
§9 as a fallback if we want the smallest possible v1.)

## 2. Data model

### 2.1 `notifications` (the inbox feed)

One row = one notification delivered to exactly one recipient.

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `recipient_id` | FK `players.id`, not null | indexed; the tab is "give me my notifications" |
| `type` | enum/text, not null | `player_joined_team`, `player_left_team`, `team_renamed`, `org_added`, `schedule_changed`, `team_join_invite`, `team_join_request`, `org_invite`, … |
| `actor_id` | FK `players.id`, nullable | who triggered it (inviter / remover / renamer) |
| `payload` | JSONB, not null, default `{}` | denormalized render context (team name, game name, role, …) so the tab renders without N+1 joins **and survives later renames** |
| `request_id` | FK `action_requests.id`, nullable | set when this feed item is/was an actionable request |
| `read_at` | timestamptz, nullable | null = unread |
| `created_at` | timestamptz, not null, server default `now()` | |

Indexes:
- `(recipient_id, created_at desc)` — the tab listing.
- partial index `(recipient_id) where read_at is null` — the unread badge count.

### 2.2 `action_requests` (the state machine)

One row = one pending/resolved request between users.

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `type` | enum/text, not null | `team_join_invite`, `team_join_request`, `org_invite` |
| `status` | enum/text, not null, default `pending` | `pending` → `accepted` / `declined` / `cancelled` / `expired` |
| `initiator_id` | FK `players.id`, not null | who sent the request |
| `target_player_id` | FK `players.id`, nullable | the specific player who must respond (invite). Null when the responder is "any authorized member" (a join *request* answered by any captain). |
| `team_id` | FK `teams.id`, nullable | for team-related requests |
| `game_id` | FK `games.id`, nullable | for org invites |
| `payload` | JSONB, not null, default `{}` | proposed role/emoji, etc. |
| `responder_id` | FK `players.id`, nullable | who actually accepted/declined (the captain who approved a join request) |
| `created_at` | timestamptz, not null | |
| `responded_at` | timestamptz, nullable | |
| `expires_at` | timestamptz, nullable | optional TTL parity with the 12h Redis invites |

Dedup: partial unique index to stop duplicate pending requests, e.g.
`unique (type, team_id, coalesce(target_player_id, 0)) where status = 'pending'`.
On conflict the create-interactor is idempotent (return the existing pending
request instead of erroring).

Both tables get a normal Alembic migration. No changes to existing tables.

## 3. Domain model (core, framework-free)

New area `shvatka/core/notifications/`:

- `dto.py` — `Notification`, `NotificationType` enum, `ActionRequest`,
  `RequestType` / `RequestStatus` enums.
- `adapters.py` — narrow DAO Protocols composed from `core/interfaces/dal/*`
  (e.g. `NotificationReader`, `NotificationWriter`, `RequestDao`,
  recipient-resolution readers), mirroring `core/games/adapters.py`.
- `interactors.py` — the use cases (see §6), Interactor-style, taking
  `identity: IdentityProvider`.

This stays within the existing convention: `core` talks to the outside only
through Protocols; the persistence implementation lives in `infrastructure/db`.

## 4. How it plugs into the existing notifiers

The existing `OrgNotifier.notify(Event)` / `TeamNotifier.notify(TeamEvent)`
hooks are exactly the right seam — they already fire **after** the business
commit and are already fanned out per-channel with swallow-and-log isolation in
`shvatka/views.py` (`ComplexTeamNotifier`, `ComplexOrgNotifier`).

Plan:

1. **Fill in the web notifiers to persist + push.** `WebTeamNotifier.notify`
   is currently a no-op; `WebOrgNotifier` only pushes. Change both so that on
   each event they:
   1. resolve recipients (§5),
   2. write `notifications` rows via a new `NotificationDAO`,
   3. `commit()` those rows (separate transaction — see §7),
   4. send a web push for each recipient via the existing `WebPushSender`.
   Steps 2–3 (durable inbox) and step 4 (transient push) are wrapped in their
   own `try/except` so one failing doesn't skip the other.

2. **No change to the business interactors' call sites.** `join_team`,
   `leave`, `agree_to_be_org`, etc. already call `notifier.notify(...)` after
   committing. They keep doing exactly that; only the web channel's behaviour
   grows.

3. **New events for things not yet wired.** "captain renamed team" and
   "schedule changed" don't emit notifier events today. Add `TeamRenamed`
   (a `TeamEvent` subclass) emitted from `EditTeamInteractor`, and a
   schedule/status event emitted from `PlanGameStartInteractor` /
   `ChangeGameStatusInteractor`. This is additive and can be phased (§8).

Optionally we add persistence as a **third channel** in the `Complex*`
wrappers instead of folding it into `Web*`. Recommendation: fold into the web
notifiers — they already own the push sender and the recipient logic, and the
empty `WebTeamNotifier` needs filling regardless.

## 5. Recipient resolution

Informational events fan out differently from the current bot behaviour (which
posts to the team chat / orgs). For the inbox we resolve concrete recipient
player-ids per event type:

| event | recipients |
|---|---|
| `PlayerJoinedTeam` | existing team members (optionally the joined player too) |
| `PlayerLeftTeam` | remaining team members |
| `TeamRenamed` | team members |
| `NewOrg` (org added) | the game's orgs + the newly added org |
| `schedule/status changed` | members of teams registered/with a waiver for the game |

The web notifier has DAO access, so recipient resolution is a read against the
team/org/waiver DAOs. This logic lives in the core notifications adapters so
it's testable without the web layer.

## 6. API surface

### Feed
- `GET  /notifications?unread=&limit=&cursor=` — list current user's feed
  (paginated). Each item embeds request status when `request_id` is set.
- `GET  /notifications/unread-count` — badge number.
- `POST /notifications/read` (body: ids) and/or `PUT /notifications/read-all`
  — mark read.

### Requests
- `POST /requests/team-join-invite` `{team_id, player_id, role?}` — captain
  invites a player.
- `POST /requests/team-join` `{team_id}` — player asks to join.
- `POST /requests/org-invite` `{game_id, player_id}` — invite an org.
- `POST /requests/{id}/accept`
- `POST /requests/{id}/decline`
- `POST /requests/{id}/cancel` — initiator withdraws.
- `GET  /requests?direction=incoming|outgoing&status=pending` — list.

Routes follow the existing thin-route pattern (`@inject`,
`FromDishka[SomeInteractor]`, `ApiIdentityProvider`, `req`/`responses` models
with `.from_core` / `.to_core`). Mirrors `shvatka/api/routes/push.py` and
`team.py`.

Frontend (out of scope for this plan): a bell/badge from `unread-count`, a tab
listing `GET /notifications`, and accept/decline buttons calling the request
endpoints.

## 7. Sessions, transactions, error handling

This answers the explicit questions.

**Same DB session or separate?** **Same** request-scoped `AsyncSession` /
`HolderDao`. By the time a notifier fires, the business operation has *already
committed* (the existing services commit, then notify). So the session is in a
clean state and reusing it to write notification rows is safe and simplest. The
new `NotificationDAO` / `RequestDAO` are provided directly from the session via
dishka — exactly like `PushSubscriptionDAO` (`di/db.py`), **not** added to
`HolderDao` (per AGENTS.md "prefer DI").

**Same transaction or separate?** **Separate transaction** for the
informational feed. Writing notification rows and `commit()`-ing them as a
*second* commit after the business commit means:
- a notification write can never roll back the user's already-durable action, and
- we don't hold the business transaction open across push I/O.

This is precisely the pattern `WebPushSender._send_one` already uses (it calls
its own `commit()` to disable a dead subscription).

**Actionable requests are different — they ARE the business operation.**
- *Creating* a request (invite / ask-to-join): insert the `action_requests`
  row **+** the recipient's `notifications` row in **one transaction**, commit,
  then fire the push post-commit. If that write fails, the endpoint returns an
  error (it's the primary operation, not a side effect).
- *Accepting* a request that performs a real change (e.g. join the team): set
  `status = accepted` on the request **in the same session**, then call the
  existing domain service (`join_team`) which commits — that single commit
  covers both the membership change and the status flip atomically, with **no
  refactor** of `join_team`. The follow-up "your invite was accepted"
  notification to the initiator is written in the same transaction. Pushes fire
  post-commit.

**Error handling summary:**
- Feed persistence + pushes are **best-effort, post-commit, swallow-and-log** —
  identical to today's `ComplexTeamNotifier` / `WebPushSender`. A user's action
  never fails because a notification couldn't be stored or pushed.
- Request **create/accept/decline** writes are **in-band**: failures surface as
  API errors. Only the downstream push is best-effort.
- Concurrency: the partial unique index makes pending-request creation
  idempotent; accepting a non-pending request raises a domain error
  (`RequestNotPending`) → 409.

**Delivery guarantee tradeoff.** The post-commit approach means a rare crash
between business commit and notification commit loses the *feed entry* (the
business change still happened). That matches how pushes already behave and is
fine for v1. If we later want at-least-once feed delivery, upgrade to a
**transactional outbox**: write the notification row in the *same* transaction
as the business change, and have a separate dispatcher send pushes. Noted as a
future option, not v1.

## 8. Pushes

Reuse `WebPushSender` unchanged. After persisting a notification row, build a
`PushMessage(title, body, url="/notifications", tag, data={...})` and
`send_to_players([recipient_id], message)`. `WebPushSender` already handles
"is configured", dead-subscription cleanup (404/410), threading, and swallowing
errors. The DB row is the **durable inbox**; the push is the **transient
nudge** — an offline user still sees it in the tab; an online user also gets the
SW notification. Use `data.kind` so the service worker routes clicks to
`/notifications` or the relevant page (same convention as existing pushes).

## 9. Bot send

The bot keeps its current behaviour (`BotTeamNotifier` posts to the team chat,
`BotOrgNotifier` DMs/pushes orgs) — that channel is untouched.

For **actionable requests** addressed to an individual user, add a
`BotRequestNotifier` that DMs the target with inline **Accept / Decline**
buttons whose callbacks hit the *same* accept/decline interactors. Because the
request state now lives in the DB (not just a Redis token), the web tab and the
bot DM act on one source of truth, and the `status='pending'` check prevents
double-accept across channels.

Relationship to the existing Redis `SecureInvite` flow (org-add, promotion):
- v1: leave Redis invites as-is; add the DB-backed feed alongside.
- Recommended follow-up: migrate **team-join** and **org-add** invites onto
  `action_requests` (durable, visible in the web tab, cancellable, deduped) and
  retire those Redis tokens. Keep Redis for ephemeral one-time confirmations
  (e.g. promotion-confirm) where no inbox entry is wanted. **This is a decision
  to confirm before building.**

### Single-table fallback (if we want the smallest v1)
Collapse into one `notifications` table with nullable `status`,
`requires_action`, `initiator_id`, `target_*` columns and the partial unique
index over pending rows. Simpler migration and one query for the tab, at the
cost of a muddier model and harder "outgoing requests" queries. Two tables is
the recommendation; this is the escape hatch.

## 10. Suggested phasing

1. **Phase 1 — feed + pushes for existing events.** Tables + migration,
   `NotificationDAO`, fill `WebTeamNotifier`/`WebOrgNotifier` to persist+push,
   `GET /notifications`, unread-count, mark-read. No new request types yet;
   wire `PlayerJoinedTeam` / `PlayerLeftTeam` / `NewOrg`.
2. **Phase 2 — actionable requests.** `action_requests` table,
   `RequestDAO`, create/accept/decline/cancel interactors + routes, feed
   embedding of request status, `BotRequestNotifier` with inline buttons.
   Covers team-join invite, ask-to-join, org invite.
3. **Phase 3 — more informational events.** `TeamRenamed`, schedule/status
   change events emitted from the relevant interactors; recipient resolution
   for game participants.

## 11. Testing

Per AGENTS.md: new domain classes/methods → unit tests
(`tests/unit/notifications/…`, plus extend `tests/unit/services/` for the
notifier persistence); new API endpoints → integration tests in
`tests/integration/api_full/test_notifications.py` (drive the real app, set up
via `dao`, `commit`, hit the route, assert). There are existing notifier mocks
(`tests/mocks/team_notifier.py`, `org_notifier.py`) to extend.

## 12. Open questions for the user

1. Migrate the existing Redis team-join / org-add invites onto the new
   `action_requests` table (recommended), or run both in parallel for now?
2. Should the joined player themselves get a feed entry, or only the rest of
   the team?
3. Retention — keep notifications forever, or prune read ones after N days?
4. Should "schedule changed" reach every player with a waiver, or only team
   captains?
