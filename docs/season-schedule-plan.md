# Season schedule in the engine — design plan

> Status: **planning only, no code yet.** Issue
> [#167](https://github.com/bomzheg/Shvatka/issues/167), milestone «к сезону 2027».
> This document proposes how to move the season schedule (the rough plan of the
> year's games) out of a hand-maintained Telegram channel post and into the
> engine, so that slots are owned, editable, linkable to real games, published
> through the game-log channel, and — the point of the issue — deliverable as
> per-player notifications.

## 1. What we are building

Today the season plan lives as a message an org edits by hand in a Telegram
channel. Nothing else knows about it: the engine can't tell whether a planned
game matches the season plan, players can't subscribe to changes, and the web UI
can't show the year at a glance.

The feature has four parts:

1. **A season** — the year's calendar, generated from a default rule, freely
   editable, then *confirmed and published*.
2. **Publication** — one message in the game-log channel that is **edited in
   place** on every later change, plus a REST endpoint so the web UI and anyone
   else can read the schedule.
3. **Change accumulation** — after publication, edits are collected and
   published **once a day** as a digest: a new game-log message plus a
   `low`-severity notification to a defined audience.
4. **Slot taking** — an approved player claims a slot for themselves, for their
   team (captains only), and may list additional orgs. A taken slot is locked to
   its owner.

Plus the softer, UX-gated part: **linking a slot to a real game**, offered when
a game start is planned near a slot, and a warning when a game is planned with
no slot nearby.

### 1.1 What already exists and is reused

| Existing thing | Where | Role here |
|---|---|---|
| `Player.can_be_author` ("аппрув") | `core/models/dto/player.py`, `check_allow_be_author` in `core/players/player.py` | **is** the "approved player" gate |
| Notifications feed + web push + bot DMs | `core/notifications/`, `notifications` table, `WebOrgNotifier`, `WebPushSender` | delivers the digest to players |
| `NotificationType.season_schedule_changed`, `NotificationSeverity.low` | `core/models/enums/notification.py` | already reserved for exactly this — see `docs/notifications-feature-plan.md` §12, which defers it pending this feature |
| Game-log channel | `BotConfig.game_log_chat`, `GameBotLog` (`tgbot/views/game.py:363`) | the channel the schedule is published to |
| `action_requests.bot_messages` JSONB | `infrastructure/db/models/action_request.py` | precedent for storing `(chat_id, message_id)` so a bot message can be edited later |
| `PlanGameStartInteractor` | `core/games/editor_interactors.py:88` | the seam for slot linking and the "out of schedule" marker |
| `GameScheduleSG` + aiogram_dialog `Calendar` | `tgbot/dialogs/game_manage/dialogs.py:368` | the bot flow the link offer plugs into |
| APScheduler with a Redis jobstore | `infrastructure/scheduler/` | runs the daily digest job |

Nothing named `season` exists in the codebase today — this is all new.

## 2. Decisions taken

Agreed with the author before writing this plan:

1. **Permissions: any approved player** (`can_be_author`) may create, generate,
   edit, publish and take. No new role, no grant/revoke UI. Every change is
   auditable through the change log, the channel message and the digest.
2. **One season per calendar year** (2026, 2027, …), unique on the year. Several
   coexist — 2026 published while 2027 is still a draft — and **past seasons are
   kept**, not deleted.
3. **Notification audience** (see §8): everyone who is *now* in a team, or *was*
   in a team during the current or previous year, plus everyone who was an org
   for a game in the current or previous year even if they are in no team now.
4. **Digest at 10:00 MSK**, fixed, daily, only when there is something to report.
5. **Slots are date-only.** No time of day; the exact start time comes from the
   real game when it is planned.
6. **Link window ±3 days** for offering a slot↔game link.
7. **One game per slot, date synced**: linking a game moves the slot onto the
   game's actual date, and that move is itself a recorded change.
8. **Slot taking records owner + optional co-orgs**: the taking player, an
   optional team (only if they captain it), a flag saying whether the author is
   the player or the team, and a list of additional org players.
9. **Default generation: 9 slots**, the first on the first Saturday **strictly
   after** 9 May, then every 21 days (§5).

## 3. Data model

Four new tables. No changes to existing tables.

### 3.1 `seasons`

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `year` | int, not null, **unique** | 2026, 2027 … |
| `status` | text, not null, default `draft` | `draft` → `published` |
| `created_by_id` | FK `players.id`, not null | who created the draft |
| `published_by_id` | FK `players.id`, nullable | who confirmed it |
| `published_at` | timestamptz, nullable | |
| `log_chat_id` | bigint, nullable | channel the schedule message lives in |
| `log_message_id` | bigint, nullable | **the message edited in place on every change** |
| `created_at` / `updated_at` | timestamptz, not null | |

### 3.2 `season_slots`

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `season_id` | FK `seasons.id` ON DELETE CASCADE, not null | indexed |
| `date` | date, not null | **date only**, interpreted in MSK (`tz_game`) |
| `note` | text, nullable | free-text ("зимняя игра", "город N") |
| `owner_id` | FK `players.id`, nullable | null ⇒ the slot is free |
| `author_kind` | text, nullable | `player` \| `team`; null while free |
| `team_id` | FK `teams.id`, nullable | set only when `author_kind = 'team'` |
| `game_id` | FK `games.id` ON DELETE SET NULL, nullable, **unique** | at most one game per slot, and a game sits in at most one slot |
| `taken_at` | timestamptz, nullable | |
| `created_at` / `updated_at` | timestamptz, not null | |

Indexes: `(season_id, date)` for the calendar query, `unique (game_id) where
game_id is not null`, `(owner_id)` for "my slots".

**No unique constraint on `(season_id, date)`** — two slots may share a date.
The generator never produces duplicates, but date syncing from a linked game
(§9) can push two slots onto the same day, and two short games in one night is a
legitimate plan.

### 3.3 `season_slot_orgs`

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `slot_id` | FK `season_slots.id` ON DELETE CASCADE, not null | |
| `player_id` | FK `players.id` ON DELETE CASCADE, not null | |

`unique (slot_id, player_id)`. These are the "other orgs" the taker adds — they
are *declared intent*, independent of the `organizers` table, which only gets
rows once a real game exists.

### 3.4 `season_changes` — the accumulator

One row per mutation after the season was published. This is the audit trail
**and** the source of the daily digest.

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `season_id` | FK `seasons.id` ON DELETE CASCADE, not null | |
| `slot_id` | FK `season_slots.id` ON DELETE SET NULL, nullable | null once the slot is gone |
| `type` | text, not null | `season_published`, `slot_added`, `slot_moved`, `slot_removed`, `slot_taken`, `slot_released`, `slot_orgs_changed`, `slot_note_changed`, `slot_game_linked`, `slot_game_unlinked` |
| `actor_id` | FK `players.id`, nullable | who did it |
| `by_superuser` | bool, not null, default false | drives «изменено администратором» wording |
| `payload` | JSONB, not null, default `{}` | denormalized: `old_date`, `new_date`, `owner_name`, `team_name`, `game_name`, `org_names` — so the digest renders with no joins and **survives later renames and deletes** |
| `published_at` | timestamptz, nullable | null ⇒ not yet in a digest |
| `created_at` | timestamptz, not null | |

Partial index `(season_id) where published_at is null` — the digest query.

Changes made while the season is still a **draft** are not recorded: there is
nothing to diff against and nobody has been told about the schedule yet.

## 4. Domain model (`shvatka/core/season/`)

Following the Interactor conventions in `AGENTS.md`:

```
core/season/
  dto.py           Season, SeasonStatus, Slot, SlotAuthor, ScheduleChange, ChangeType
  rules.py         pure: default_slot_dates(year), permission checks, "near" search
  adapters.py      Protocols, composed from core/interfaces/dal/*
  interactors.py   the use cases
```

`dto.Slot` carries the denormalized view the calendar needs without extra
queries: `id, date, note, owner: dto.Player | None, author_kind, team: dto.Team
| None, orgs: Sequence[dto.Player], game: dto.Game | None`, plus helpers
`is_free`, `is_mine(player)`.

Interactors (all take `identity: IdentityProvider`, none take a resolved player):

| Interactor | Does |
|---|---|
| `GetSeasonInteractor` | read one season with its slots (public for `published`) |
| `ListSeasonsInteractor` | the years that exist |
| `CreateSeasonInteractor` | create a `draft` for a year, generating the 9 default slots (§5) |
| `RegenerateSlotsInteractor` | reset a **draft** back to the default slots |
| `AddSlotInteractor` / `MoveSlotInteractor` / `RemoveSlotInteractor` / `EditSlotNoteInteractor` | structural edits |
| `PublishSeasonInteractor` | draft → published, post the channel message, store its id, notify |
| `TakeSlotInteractor` / `ReleaseSlotInteractor` / `SetSlotOrgsInteractor` | ownership (§7) |
| `LinkGameToSlotInteractor` / `UnlinkGameFromSlotInteractor` | the game link (§9) |
| `SuggestSlotsForGameInteractor` | read-only ±3-day lookup used by both edges (§9) |
| `SyncLinkedSlotInteractor` | move a linked slot when its game's `start_at` moves |
| `PublishSeasonDigestInteractor` | the 10:00 MSK job (§6.2) |

Per the "at most one DAO per interactor" rule, all of them take a single
composed `SeasonScheduleDao` Protocol (`core/season/adapters.py`), implemented
by `infrastructure/db/dao/complex/season.py` over per-table DAOs `SeasonDao`,
`SeasonSlotDao`, `SeasonSlotOrgDao`, `SeasonChangeDao` — writes for each table
stay in that table's own DAO, and the interactor decides the ordering.

New exceptions in `core/utils/exceptions.py`: `SeasonAlreadyExists`,
`SeasonNotPublished`, `SeasonAlreadyPublished`, `SlotAlreadyTaken`,
`NotSlotOwner`, `SlotAlreadyLinked`, `GameAlreadyInSchedule`.

## 5. Default generation

Pure function in `core/season/rules.py`:

```python
SEASON_SLOTS_COUNT = 9
SEASON_SLOT_INTERVAL = timedelta(days=21)
SEASON_START_AFTER = (5, 9)  # 9 May

def default_slot_dates(year: int) -> list[date]:
    first = _first_saturday_after(date(year, *SEASON_START_AFTER))
    return [first + SEASON_SLOT_INTERVAL * i for i in range(SEASON_SLOTS_COUNT)]

def _first_saturday_after(day: date) -> date:
    # strictly after: a Saturday falling exactly on 9 May is skipped
    delta = (SATURDAY - day.weekday()) % 7
    return day + timedelta(days=delta or 7)
```

Verified output:

| year | 9 May is | generated slots |
|---|---|---|
| 2026 | **Saturday** (skipped) | 16.05, 06.06, 27.06, 18.07, 08.08, 29.08, 19.09, 10.10, **31.10** |
| 2027 | Sunday | 15.05, 05.06, 26.06, 17.07, 07.08, 28.08, 18.09, 09.10, **30.10** |
| 2028 | Tuesday | 13.05, 03.06, 24.06, 15.07, 05.08, 26.08, 16.09, 07.10, **28.10** |

Nine slots always land the season's last game in the second half of October,
which is what "every 3 weeks up to October" means in practice — without needing
a fragile end-boundary rule.

The user may then change anything: move, add, delete slots, including into
January–April or November–December.

## 6. Publication and the channel message

### 6.1 A dedicated announcer protocol, not `GameLogWriter`

`GameLogWriter.log()` returns `None`, and `ComplexGameLogWriter` fans out to
several channels swallowing errors — so it cannot hand back the `message_id` we
must store and edit later. Rather than distort it, add a sibling protocol in
`core/views/season.py`:

```python
@dataclass
class Announcement:
    chat_id: int
    message_id: int

class SeasonAnnouncer(Protocol):
    async def publish(self, season: dto.Season) -> Announcement | None: ...
    async def update(self, season: dto.Season) -> None: ...          # edits the stored message
    async def announce_digest(self, season: dto.Season,
                              changes: Sequence[dto.ScheduleChange]) -> None: ...
```

- `BotSeasonAnnouncer` (`tgbot/views/season.py`) — sends/edits in
  `BotConfig.game_log_chat`; `update` is a no-op when the season has no stored
  message; swallows Telegram's "message is not modified".
- `WebSeasonAnnouncer` (`api/utils/web_input.py`) — no-op; the web side is served
  by the REST endpoint and the notification feed, not by an announcement.
- `ComplexSeasonAnnouncer` (`shvatka/views.py`) — same swallow-and-log shape as
  `ComplexGameLogWriter`, except `publish` returns the **bot's** announcement so
  the interactor can persist it.

`PublishSeasonInteractor`: flip status → commit → `announcer.publish(...)` →
store `log_chat_id`/`log_message_id` → commit → write `season_schedule_changed`
notifications (`low`) to the §8 audience.

### 6.2 After publication: edit immediately, digest daily

Every mutating interactor, when the season is `published`:

1. performs the write **and** inserts the `season_changes` row **in the same
   transaction** (the audit trail must not be lost — this deliberately differs
   from the informational notification feed, which is best-effort post-commit);
2. commits;
3. calls `announcer.update(season)` post-commit, best-effort, so the pinned
   channel message always shows current truth.

The daily job (`PublishSeasonDigestInteractor`, 10:00 MSK) then:

1. selects `season_changes` with `published_at is null` per published season;
2. renders them grouped by slot in date order;
3. marks them published and writes `season_schedule_changed` notifications with
   severity `low` — **one transaction**, committed;
4. posts the digest as a **new** message in the game-log channel (best-effort,
   post-commit — consistent with the rest of the codebase's post-commit
   notification pattern).

If the channel post fails after the commit the digest is skipped for that day;
the schedule message — edited in place on every change by step 3 above — still
shows the correct state, and players still got the notification. The reverse order (send, then commit) was
rejected because a crash in between would re-post the same digest.

Wiring: a cron job registered once at scheduler start with a fixed id and
`replace_existing=True`:

```python
self.scheduler.add_job(
    func="shvatka.infrastructure.scheduler.wrappers:publish_season_digest_wrapper",
    trigger="cron", hour=10, minute=0, timezone=tz_game,
    id="season_digest_daily", replace_existing=True,
)
```

Note this is the first *recurring* job in `ApScheduler` — every existing job is
a one-shot `date` trigger. The Redis jobstore keeps it across restarts, and
`replace_existing` keeps redeploys idempotent.

## 7. Slot ownership

Taking (`TakeSlotInteractor`):

- requires `can_be_author` (`check_allow_be_author`);
- requires the season to be `published` — a draft has nothing to claim;
- the slot must be free, **or** already owned by the acting player (re-taking
  your own slot is how you change its author/orgs), **or** the actor is a
  superuser;
- `author_kind = team` additionally requires the actor to captain that team
  (`is_team_captain`);
- `org_player_ids` are stored in `season_slot_orgs`. Any player may be listed —
  being an org does not require the аппрув.

Locking:

- **A taken slot may only be released, re-assigned, moved or deleted by its
  owner** — or by a superuser. Anyone else gets `NotSlotOwner`.
- A **free** slot may be added, moved or deleted by **any** approved player.
- Superuser actions take the same routes and set `by_superuser = true` on the
  change row, so the digest can say «изменено администратором», and are logged
  with the acting admin's id per `AGENTS.md`.

Concurrency: `TakeSlotInteractor` re-reads the slot `FOR UPDATE` inside the
transaction and raises `SlotAlreadyTaken` (→ HTTP 409) if someone won the race.

## 8. Notification audience

Per the decision: *everyone in a team now, or in a team during the current or
previous year, plus everyone who was an org for a game in the current or
previous year even if they have no team now.*

One DAO method, `SeasonAudienceReader.get_recipient_ids(since: datetime) -> set[int]`,
where `since` = 1 January of `now(MSK).year - 1`, as a `UNION` of:

- `team_players` where `date_left is null or date_left >= since` (a membership
  that overlaps the window);
- `organizers` where `deleted is false`, joined to `games` with
  `start_at >= since`;
- `games.author_id` for the same games — the author is an org too.

Recipients get a `season_schedule_changed` notification, severity `low`, with a
payload carrying the season year and a short change summary, so
`notification-render.ts` in the UI can render it without extra fetches. Web push
follows automatically via the existing `WebPushSender` path; `low` severity
already means the service worker treats it quietly.

The season year is *not* used for the window — the window is relative to
**today**, so a 2027 draft published in 2026 still reaches the people active in
2025–2026.

## 9. Linking a game to a slot

The requirement is explicitly UX-gated ("only if without bad ux"), so nothing is
linked automatically — the engine only *offers*.

**A. Planning a game near a slot.** Both edges call the read-only
`SuggestSlotsForGameInteractor(at: datetime)` before or right after planning. It
returns slots of the current published season whose date is within **±3 days**
of `at` (MSK) and that are free or already owned by the acting player, nearest
first. The edge shows «Привязать игру к слоту 27.06?» with confirm/skip.

**B. Planning a game with no slot nearby.** The same interactor returning an
empty list drives the warning, offering three actions:

1. add a new slot on the game's date (`AddSlotInteractor` + `TakeSlotInteractor`
   + link, one flow);
2. move the nearest slot before or after onto the game's date
   (`MoveSlotInteractor` + link);
3. plan without the schedule.

**C. Confirmed link** (`LinkGameToSlotInteractor`): sets `slot.game_id`, sets
`slot.date` to the game's `start_at` date in MSK (**synced**, per the decision),
takes the slot for the game's author if it was free, and records
`slot_game_linked` (plus `slot_moved` when the date actually changed).

**D. Keeping it synced.** `PlanGameStartInteractor` gains one new dependency,
`SyncLinkedSlotInteractor`, invoked after a successful re-plan: if the game
already sits in a slot, the slot's date follows the new `start_at` and a
`slot_moved` change is recorded with `payload.reason = "game_rescheduled"`.
Cancelling a planned start unlinks nothing — the slot keeps the game, it just
has no date to sync from. The *suggestion* logic stays out of
`PlanGameStartInteractor`; it is a separate read-only interactor the edges call,
so no UI decision leaks into the planner.

**E. "Out of schedule" marker.** The existing `GameLogType.GAME_PLANED` message
gains a suffix when the freshly planned game has no linked slot — «(вне
расписания сезона)» — so the channel and the org see it immediately.

## 10. API surface

Read of a **published** season is public (the issue asks for the schedule to be
"available by API"); drafts and all writes require an authenticated approved
player.

```
GET    /seasons                                 list of years + status
GET    /seasons/current                         the current year's season
GET    /seasons/{year}                          season + slots
POST   /seasons                {year}           create draft with default slots
POST   /seasons/{year}/regenerate               reset a draft to defaults
POST   /seasons/{year}/publish                  confirm & publish
POST   /seasons/{year}/slots   {date, note?}    add a slot
PATCH  /seasons/{year}/slots/{id}  {date?, note?}
DELETE /seasons/{year}/slots/{id}
POST   /seasons/{year}/slots/{id}/take
       {author_kind, team_id?, org_player_ids?} take / re-assign
DELETE /seasons/{year}/slots/{id}/take          release
POST   /seasons/{year}/slots/{id}/game {game_id}  link
DELETE /seasons/{year}/slots/{id}/game            unlink
GET    /seasons/slots/suggest?at=<iso datetime>   ±3-day candidates for the offer
```

Thin routes in `api/routes/season.py` following the existing pattern (`@inject`,
`FromDishka[SomeInteractor]`, `ApiIdentityProvider`, `req`/`responses` models
with `.from_core` / `.to_core`), registered in `api/routes/__init__.py`.
Conflicts map to 409 (`SlotAlreadyTaken`, `SeasonAlreadyExists`,
`GameAlreadyInSchedule`), permission failures to 403 via the existing
`error_converter`.

## 11. Bot UX

New `SeasonSG` states group: `calendar`, `slot`, `take`, `orgs`, `confirm_publish`.

**The calendar widget.** As the author expected, aiogram_dialog's `Calendar` is
subclassed rather than used as-is:

```python
class SeasonCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        # same views as the base, but the days view gets a custom `text=`
        # so each day cell can be marked
```

Day marks come from a getter that loads the season once: `🟢` free slot, `🔒`
taken by someone else, `⭐` taken by you, `🎮` linked to a game, plain number
otherwise. `CalendarConfig(min_date, max_date)` pins the view to the season's
year, with month scope as the entry point so a whole season is two taps away.

Flows:

- tap a day **with** a slot → slot window: take / release / change author
  (self vs team) / edit orgs / move / delete / open the linked game;
- tap a day **without** a slot → «Добавить слот на эту дату» for approved
  players;
- a season menu window with «Сгенерировать по умолчанию» (draft only) and
  «Опубликовать» (with a confirm step, since publication announces to everyone).

**Link offer inside the existing flow.** `GameScheduleSG` gets one extra window
after `confirm`: if `SuggestSlotsForGameInteractor` returns candidates, offer the
nearest with «Привязать» / «Не привязывать»; if it returns nothing, show the
warning with the three §9B options.

## 12. Web UI (shvatka-ui)

New standalone component `src/app/season/` plus `season.service.ts`, route
`/season` and `/season/:year`, entry in the header.

- **Season grid**: months **May–October** by default, rendered as month cards
  with day cells. If the season has slots outside that range the view
  auto-extends to cover them; «← Раньше» / «Позже →» buttons extend month by
  month up to the full January–December so a user can plan a cold-month game.
- **Cell states** mirror the bot marks: free, taken (owner or team name +
  emoji), linked game (links to the game page), your slot highlighted.
- **Actions** for approved players: take (dialog choosing self vs team, plus an
  org picker reusing the existing player search), release, add slot, move slot,
  publish. Everything else is read-only, and the published season renders for
  anonymous visitors.
- **Notifications tab**: add a `season_schedule_changed` renderer to
  `notification-render.ts` producing e.g. «Расписание сезона 2027: 3 изменения»
  linking to `/season/2027`.

## 13. Testing

Per `AGENTS.md`:

- **Unit** (`tests/unit/season/`): `default_slot_dates` for several years
  including the 9 May-is-Saturday case and the count/interval invariants; the
  ownership rules (free/owner/superuser/captain matrix); the ±3-day nearest-slot
  search including ties; digest rendering from a list of changes.
- **Integration** (`tests/integration/api_full/test_season.py`): create draft →
  9 slots; publish → status flips and the change row appears; take → 409 on a
  second taker, 403 for a non-approved player; link a game → slot date syncs;
  re-plan the game → slot follows; run the digest interactor → changes marked
  published and notifications written. Assert through `check_dao` as the
  existing tests do.
- Announcer and notification side effects are asserted through mocks in the
  style of `tests/mocks/org_notifier.py`.

## 14. Phasing

1. **Phase 1 — engine.** Tables + migration, `core/season/`, DAOs, DI wiring,
   REST API, `SeasonAnnouncer` + bot implementation, publication, the daily
   digest job and the notification audience. This is the reviewable core and
   makes the schedule real and readable everywhere.
2. **Phase 2 — bot.** `SeasonSG` dialogs, the `SeasonCalendar` subclass, and the
   link offer / no-slot warning grafted onto `GameScheduleSG`.
3. **Phase 3 — web UI.** The season calendar component, the extend-months
   controls, and the `season_schedule_changed` notification renderer.

Phases 2 and 3 are independent of each other and can land in either order.

## 15. Open questions

- **Who creates next year's draft?** Currently a manual `POST /seasons`. Should
  the engine auto-create a draft for year+1 at some point (say, after the last
  slot of the current season), or is manual creation fine?
- **Pinning.** Should the published schedule message be pinned in the game-log
  channel? (The bot already handles pin permissions for puzzle messages, so it's
  cheap either way.)
- **Digest wording for a busy day.** If one slot is edited five times before
  10:00, do we report every step, or collapse to the net before/after? Collapsing
  reads better; the full trail stays in `season_changes` either way. Proposal:
  collapse per slot, listing the net change.
- **Past-slot hygiene.** A slot whose date has passed with no linked game — leave
  as-is, or mark it as skipped so the calendar reads honestly a year later?
- **Draft visibility.** Should a draft season be readable by *any* authenticated
  player (so people can see what's coming), or only by approved players as
  proposed here?
