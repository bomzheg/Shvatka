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

1. **Composing a season** — the year's calendar, generated from a default rule
   and freely edited **client-side**, then *confirmed* — and confirmation is
   what creates it in the engine (§5.1).
2. **Publication** — one message in the game-log channel, **pinned**, and
   **edited in place** on every later change, plus a REST endpoint so the web UI
   and anyone else can read the schedule.
3. **Change accumulation** — after publication, edits are collected and
   published **once a day** as a digest that **collapses repeated edits to the
   net change**: a new game-log message plus a `low`-severity notification to a
   defined audience.
4. **Slot taking** — an author claims a slot for themselves, for their team
   (captains only), and may list additional slot orgs. A taken slot is locked to
   its owner.

Plus the softer, UX-gated part: **linking a slot to a real game**, offered when
a game start is planned near a slot, and a warning when a game is planned with
no slot nearby.

### 1.1 What already exists and is reused

| Existing thing | Where | Role here |
|---|---|---|
| `Player.can_be_author` ("аппрув") | `core/models/dto/player.py`, `check_allow_be_author` in `core/players/player.py` | **is** the `author` gate — the аппрув the issue calls "approved" |
| Notifications feed + web push + bot DMs | `core/notifications/`, `notifications` table, `WebOrgNotifier`, `WebPushSender` | delivers the digest to players |
| `NotificationType.season_schedule_changed`, `NotificationSeverity.low` | `core/models/enums/notification.py` | already reserved for exactly this — see `docs/notifications-feature-plan.md` §12, which defers it pending this feature |
| Game-log channel | `BotConfig.game_log_chat`, `GameBotLog` (`tgbot/views/game.py:363`) | the channel the schedule is published to |
| `BotRights.can_pin(chat_id)` | `tgbot/services/bot_rights.py` | cached rights check before pinning the schedule message |
| `action_requests.bot_messages` JSONB | `infrastructure/db/models/action_request.py` | precedent for storing `(chat_id, message_id)` so a bot message can be edited later |
| `PlanGameStartInteractor` | `core/games/editor_interactors.py:88` | the seam for slot linking and the "out of schedule" marker |
| `GameScheduleSG` + aiogram_dialog `Calendar` | `tgbot/dialogs/game_manage/dialogs.py:368` | the bot flow the link offer plugs into |
| APScheduler with a Redis jobstore | `infrastructure/scheduler/` | runs the daily digest job |
| `SuperusersResolver` | `core/interfaces/superusers.py` | the only way to ask whether the actor is an админ движка |
| `context.md` (both repos) | repo root | the ubiquitous language every name below has to obey — see §3 |

Nothing named `season` exists in the codebase today — this is all new.

## 2. Decisions taken

Agreed with the author before writing this plan:

1. **Permissions: any author** (`can_be_author`) may compose, publish, edit and
   take. No new role, no grant/revoke UI. Every change is auditable
   through the change log, the channel message and the digest.
2. **No draft entity.** A season exists in the database only once it has been
   **published**. Everything before that — generating the default dates, moving
   and adding them — happens in the client's own state (aiogram_dialog
   `dialog_data` in the bot, component state in the web UI). See §5.1.
3. **One season per calendar year** (2026, 2027, …), unique on the year. Several
   coexist and **past seasons are kept**, not deleted. Next year's season can be
   published while this year's is still running.
4. **Notification audience** (see §9): everyone who is *now* in a team, or *was*
   in a team during the current or previous year, plus everyone who was an org
   for a game in the current or previous year even if they are in no team now.
5. **Digest at 10:00 MSK**, fixed, daily, only when there is something to
   report, and **collapsed per slot to the net change** — collapsing is the
   whole point of accumulating (§7.3).
6. **Slots are date-only.** No time of day; the exact start time comes from the
   real game when it is planned.
7. **Link window ±3 days** for offering a slot↔game link.
8. **One game per slot, date synced**: linking a game moves the slot onto the
   game's actual date, and that move is itself a recorded change.
9. **Slot taking records owner + optional co-orgs**: the taking player, an
   optional team (only if they captain it), a flag saying whether the author is
   the player or the team, and a list of additional org players.
10. **Default generation: 9 slots**, the first on the first Saturday **strictly
    after** 9 May, then every 21 days (§6).
11. **The schedule message is pinned** on publication and **unpinned once the
    season is over** (§7.4).
12. **Past slots are left alone.** A slot whose date passed with no linked game
    keeps its data unchanged — no "skipped" state, nothing to implement, and the
    calendar still reads honestly a year later.
13. **A season is created manually.** No auto-creation of next year's calendar.
14. **A planned date is «дата игры» — «дата» for short** — in the glossary and in
    every user-facing string. The code calls it `Slot` for identifier reasons
    only (§3.4); no Russian text says *слот*.

## 3. Ubiquitous language

`context.md` is the project glossary, and its second rule is that *the glossary
follows the domain* — a new concept is added to it **in the same PR that adds the
code**. This feature introduces a whole area, so the terms are settled here and
land in both `context.md` files (engine and `shvatka-ui`) with Phase 1.

### 3.1 Terms already in the glossary that this feature uses

Three of them fix wording the issue phrased differently:

- **Author / Автор** (`can_be_author`) is the glossary's name for what the issue
  calls an "approved player". *Approved player* is not a term — the plan says
  **author** throughout. The аппрув that grants the right is **promotion**.
- **Superuser / Админ движка** is the engine operator, resolved only through
  `SuperusersResolver`. The digest therefore says «изменено админом движка», not
  «администратором» — in this glossary *admin* means the superuser, and a game
  has *organizers*, not admins.
- **Organizer / org** is a player who runs **a game**. The people listed on a
  slot are not organizers yet — there is no game — so they get their own term
  below rather than borrowing that one.

### 3.2 Terms this feature adds

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Season** | Сезон | One calendar year's plan of games, as a list of slots. Exists in the engine only once published. | `season.dto.Season`, `seasons` table |
| **Slot** | Дата игры (в разговоре — просто «дата») | One planned date in a season, before there is a game to put in it. Date-only; may be free or taken; may be linked to exactly one game. | `season.dto.Slot`, `season_slots` table |
| **Taking a slot** | Взять дату | An author claiming a slot, declaring whether the game will be authored by them or by their team. A taken slot is locked to its owner. | `TakeSlotInteractor` |
| **Slot owner** | Владелец даты | The author who took the slot. The only person besides the superuser who may move, release or delete it. | `season_slots.owner_id` |
| **Slot org** | Орг на дату | A player the owner names as a co-organizer of the future game. Declared intent only — it becomes an `Organizer` when the game exists. | `season_slot_orgs` table |
| **Schedule publication** | Публикация расписания | Confirming a composed season: it is written to the database, announced in the game-log channel and pinned. | `PublishSeasonInteractor` |
| **Schedule change** | Изменение расписания | One recorded edit of a published season — the audit trail and the digest's raw material. | `season.dto.ScheduleChange`, `season_changes` table |
| **Change digest** | Сводка изменений | The once-a-day message collapsing every unpublished change to its net effect per slot. | `PublishSeasonDigestInteractor` |

### 3.3 Two collisions to resolve in the glossary

1. **Публикация** already means *posting a finished game's results to a Telegram
   channel* (`GameResults.published_chanel_id`). Publishing a schedule is a
   different act on a different aggregate. Since «опубликовать расписание» is
   what organizers will actually say, the fix is to qualify both entries —
   **публикация результатов** and **публикация расписания** — rather than invent
   a word nobody uses.
2. **Расписание** vs planning a game's start. The engine already *plans* a game
   start (`PlanGameStartInteractor`, «Начало игры {game} запланировано на {at}»)
   and the bot dialog is called `GameScheduleSG`. That is **planning a start**
   (планирование старта игры) and stays that way; **расписание** without
   qualification means the season schedule. `GameScheduleSG` contradicts the
   glossary and should be noted as such — renaming it is out of scope here.

### 3.4 Why «дата» in Russian and `Slot` in code

People say **«дата игры»**, or just **«дата»**. That is the term, and every
user-facing string uses it: «Взять дату», «Добавить дату», «Дата занята». A
borrowed *слот* was considered and rejected — inventing a word for something the
domain already names is exactly what the glossary exists to prevent, and generic
beats novel here.

The English half stays **`Slot`**. `date` is unusable as an identifier: it is a
Python builtin, the column's own type, and would give `season_dates.date`. The
glossary already carries pairs whose halves are unrelated words — **Promotion /
Аппрув**, **Puzzle / Загадка уровня**, **Waiver / Вейвер** — so `Slot` ↔ «дата
игры» fits the pattern. What matters is that no Russian string anywhere says
*слот*.

## 4. Data model

Four new tables. No changes to existing tables.

### 4.1 `seasons`

Every row is a published season — there is no draft status to model.

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `year` | int, not null, **unique** | 2026, 2027 … |
| `published_by_id` | FK `players.id`, not null | who confirmed and published it |
| `published_at` | timestamptz, not null | |
| `log_chat_id` | bigint, nullable | channel the schedule message lives in |
| `log_message_id` | bigint, nullable | **the message edited in place on every change** |
| `unpinned_at` | timestamptz, nullable | set when the season ended and the message was unpinned (§7.4) |
| `updated_at` | timestamptz, not null | |

`log_chat_id` / `log_message_id` stay nullable because publication to Telegram is
best-effort: a failed channel post must not roll back a published season.

### 4.2 `season_slots`

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
(§10) can push two slots onto the same day, and two short games in one night is a
legitimate plan.

### 4.3 `season_slot_orgs`

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `slot_id` | FK `season_slots.id` ON DELETE CASCADE, not null | |
| `player_id` | FK `players.id` ON DELETE CASCADE, not null | |

`unique (slot_id, player_id)`. These are the **slot orgs** (§3.2) — the co-orgs
the owner names for a game that does not exist yet. They are *declared intent*,
independent of the `organizers` table, which only gets rows once there is a real
game to organize.

### 4.4 `season_changes` — the accumulator

One row per mutation. Because a season is only ever persisted in its published
form, every change row is by definition post-publication: this is both the audit
trail **and** the source of the daily digest.

| column | type | notes |
|---|---|---|
| `id` | bigint PK | |
| `season_id` | FK `seasons.id` ON DELETE CASCADE, not null | |
| `slot_id` | FK `season_slots.id` ON DELETE SET NULL, nullable | null once the slot is gone |
| `type` | text, not null | `slot_added`, `slot_moved`, `slot_removed`, `slot_taken`, `slot_released`, `slot_orgs_changed`, `slot_note_changed`, `slot_game_linked`, `slot_game_unlinked` |
| `actor_id` | FK `players.id`, nullable | who did it |
| `by_superuser` | bool, not null, default false | drives «изменено админом движка» wording |
| `payload` | JSONB, not null, default `{}` | denormalized: `old_date`, `new_date`, `owner_name`, `team_name`, `game_name`, `org_names` — so the digest renders with no joins and **survives later renames and deletes** |
| `published_at` | timestamptz, nullable | null ⇒ not yet in a digest |
| `created_at` | timestamptz, not null | |

Partial index `(season_id) where published_at is null` — the digest query.

## 5. Domain model (`shvatka/core/season/`)

Following the Interactor conventions in `AGENTS.md`:

```
core/season/
  dto.py           Season, Slot, SlotAuthor, ScheduleChange, ChangeType
  rules.py         pure: default_slot_dates(year), permission checks, "near" search,
                   digest collapsing
  adapters.py      Protocols, composed from core/interfaces/dal/*
  interactors.py   the use cases
```

`dto.Slot` carries the denormalized view the calendar needs without extra
queries: `id, date, note, owner: dto.Player | None, author_kind, team: dto.Team
| None, orgs: Sequence[dto.Player], game: dto.Game | None`, plus helpers
`is_free`, `is_mine(player)`.

### 5.1 Composing a season without a draft entity

The engine never stores a half-built calendar. The flow is:

1. The client asks the engine for the **default dates**:
   `GetDefaultSlotDatesInteractor(year)` — a pure call, no reads, no writes,
   returning the 9 dates of §6. The engine stays the single source of truth for
   the rule while nothing is persisted.
2. The user edits that list **locally** — moves, adds, deletes, writes notes.
   In the bot that list lives in `dialog_data`; in the web UI in component state
   (optionally mirrored to `localStorage` so a refresh doesn't lose it).
3. «Опубликовать» submits the **whole list at once**:
   `PublishSeasonInteractor(year, slots)` inserts the `seasons` row and all
   `season_slots` in **one transaction**, then announces (§7).

Consequences worth being explicit about:

- An unfinished composition is lost if the dialog is cancelled or the browser
  cache cleared. That is acceptable — it is nine dates, one tap to regenerate.
- Two people could compose 2027 in parallel; the first to publish wins and the
  second gets `SeasonAlreadyExists` → HTTP 409, with the UI offering to open the
  now-published season and edit it slot by slot instead.
- After publication there is exactly one editing path — the per-slot endpoints
  of §11 — so "edit the schedule" always means "make a tracked change".

### 5.2 Interactors

| Interactor | Does |
|---|---|
| `GetDefaultSlotDatesInteractor` | the 9 default dates for a year; pure, no persistence |
| `PublishSeasonInteractor` | create the season + its slots from a submitted list, announce, pin, notify |
| `GetSeasonInteractor` | read one season with its slots (public) |
| `ListSeasonsInteractor` | the years that exist |
| `AddSlotInteractor` / `MoveSlotInteractor` / `RemoveSlotInteractor` / `EditSlotNoteInteractor` | structural edits |
| `TakeSlotInteractor` / `ReleaseSlotInteractor` / `SetSlotOrgsInteractor` | ownership (§8) |
| `LinkGameToSlotInteractor` / `UnlinkGameFromSlotInteractor` | the game link (§10) |
| `FindSlotsNearGameStartInteractor` | read-only ±3-day lookup used by both edges (§10) |
| `SyncLinkedSlotInteractor` | move a linked slot when its game's `start_at` moves |
| `PublishSeasonDigestInteractor` | the 10:00 MSK job — digest **and** end-of-season unpin (§7.3, §7.4) |

Per the "at most one DAO per interactor" rule, all of them take a single
composed `SeasonScheduleDao` Protocol (`core/season/adapters.py`), implemented
by `infrastructure/db/dao/complex/season.py` over per-table DAOs `SeasonDao`,
`SeasonSlotDao`, `SeasonSlotOrgDao`, `SeasonChangeDao` — writes for each table
stay in that table's own DAO, and the interactor decides the ordering.

New exceptions in `core/utils/exceptions.py`: `SeasonAlreadyExists`,
`SeasonNotFound`, `SlotAlreadyTaken`, `NotSlotOwner`, `SlotAlreadyLinked`,
`GameAlreadyInSchedule`.

## 6. Default generation

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
January–April or November–December — before publication in the client, after it
through the tracked endpoints.

## 7. Publication, the channel message, the digest

### 7.1 A dedicated announcer protocol, not `GameLogWriter`

`GameLogWriter.log()` returns `None`, and `ComplexGameLogWriter` fans out to
several channels swallowing errors — so it cannot hand back the `message_id` we
must store, edit and later unpin. Rather than distort it, add a sibling protocol
in `core/views/season.py`:

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
    async def close(self, season: dto.Season) -> None: ...           # unpin at season end
```

- `BotSeasonAnnouncer` (`tgbot/views/season.py`) — sends, pins, edits and
  unpins in `BotConfig.game_log_chat`; checks `BotRights.can_pin` first, exactly
  as `MessagePinner` does, and treats a missing pin right as a logged no-op;
  `update` is a no-op when the season has no stored message; swallows Telegram's
  "message is not modified".
- `WebSeasonAnnouncer` (`api/utils/web_input.py`) — no-op; the web side is served
  by the REST endpoint and the notification feed, not by an announcement.
- `ComplexSeasonAnnouncer` (`shvatka/views.py`) — same swallow-and-log shape as
  `ComplexGameLogWriter`, except `publish` returns the **bot's** announcement so
  the interactor can persist it.

### 7.2 Publishing

`PublishSeasonInteractor`: insert season + slots → commit → `announcer.publish`
(send + pin) → store `log_chat_id`/`log_message_id` → commit → write
`season_schedule_changed` notifications (severity `low`) to the §9 audience.

The publication itself produces **no** `season_changes` rows: the pinned message
and the "новое расписание сезона" notification already say everything, and the
first digest should describe changes *to* the published plan, not the plan
itself.

### 7.3 After publication: edit immediately, digest daily

Every mutating interactor:

1. performs the write **and** inserts the `season_changes` row **in the same
   transaction** (the audit trail must not be lost — this deliberately differs
   from the informational notification feed, which is best-effort post-commit);
2. commits;
3. calls `announcer.update(season)` post-commit, best-effort, so the pinned
   channel message always shows current truth.

The daily job (`PublishSeasonDigestInteractor`, 10:00 MSK) then, per season:

1. selects `season_changes` with `published_at is null`;
2. **collapses them per slot to the net change** — five edits of one slot before
   10:00 report as one line, and a slot that was moved and then moved back
   drops out of the digest entirely. The full step-by-step trail stays in
   `season_changes`. Collapsing lives in `core/season/rules.py` as a pure
   function over a list of changes, so it is unit-testable without a DB;
3. marks the rows published and writes `season_schedule_changed` notifications
   with severity `low` — **one transaction**, committed;
4. posts the digest as a **new** message in the game-log channel (best-effort,
   post-commit — consistent with the rest of the codebase's post-commit
   notification pattern). Nothing to post ⇒ nothing sent, no empty daily noise.

If the channel post fails after the commit the digest is skipped for that day;
the schedule message — edited in place on every change by step 3 above — still
shows the correct state, and players still got the notification. The reverse
order (send, then commit) was rejected because a crash in between would re-post
the same digest.

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

### 7.4 Unpinning when the season ends

The same daily job also closes finished seasons: for every season with
`unpinned_at is null` whose **latest slot date is in the past**, call
`announcer.close(season)` (unpin, best-effort) and set `unpinned_at`. No extra
scheduling is needed, and "latest slot date" naturally follows slots that moved
or were synced to a late game.

The message itself is kept and stays editable — only the pin is released, so the
channel keeps a permanent record of the year.

## 8. Slot ownership

Taking (`TakeSlotInteractor`):

- requires `can_be_author` (`check_allow_be_author`);
- the slot must be free, **or** already owned by the acting player (re-taking
  your own slot is how you change its author/orgs), **or** the actor is a
  superuser (asked through `SuperusersResolver`, never by re-reading config);
- `author_kind = team` additionally requires the actor to captain that team
  (`is_team_captain`);
- `org_player_ids` are stored in `season_slot_orgs` as **slot orgs**. Any player
  may be listed — being an org does not require promotion to author.

Locking:

- **A taken slot may only be released, re-assigned, moved or deleted by its
  owner** — or by a superuser. Anyone else gets `NotSlotOwner`.
- A **free** slot may be added, moved or deleted by **any** author.
- Superuser actions take the same routes and set `by_superuser = true` on the
  change row, so the digest can say «изменено админом движка», and are logged
  with the acting admin's id per `AGENTS.md`.

Concurrency: `TakeSlotInteractor` re-reads the slot `FOR UPDATE` inside the
transaction and raises `SlotAlreadyTaken` (→ HTTP 409) if someone won the race.

## 9. Notification audience

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
**today**, so a 2027 season published in 2026 still reaches the people active in
2025–2026.

## 10. Linking a game to a slot

The requirement is explicitly UX-gated ("only if without bad ux"), so nothing is
linked automatically — the engine only *offers*.

**A. Planning a game near a slot.** Both edges call the read-only
`FindSlotsNearGameStartInteractor(at: datetime)` before or right after planning. It
returns slots of the current season whose date is within **±3 days** of `at`
(MSK) and that are free or already owned by the acting player, nearest first.
The edge shows «Привязать игру к дате 27.06?» with confirm/skip.

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

## 11. API surface

Reading a season is public (the issue asks for the schedule to be "available by
API"); all writes require an authenticated author.

```
GET    /seasons                                 list of years
GET    /seasons/current                         the current year's season
GET    /seasons/{year}                          season + slots
GET    /seasons/defaults?year=2027              the 9 default dates, nothing persisted
POST   /seasons  {year, slots: [{date, note?}]} publish a composed season
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
Conflicts map to 409 (`SeasonAlreadyExists`, `SlotAlreadyTaken`,
`GameAlreadyInSchedule`), permission failures to 403 via the existing
`error_converter`.

## 12. Bot UX

New `SeasonSG` states group: `calendar`, `slot`, `take`, `orgs`, `compose`,
`confirm_publish`.

**Composing.** For a year with no season yet, `compose` starts from
`GET /seasons/defaults`, keeps the working list in `dialog_data`, and lets the
user tap days to add/remove and pick a slot to move. «Опубликовать» leads to a
confirm window (publication announces to everyone, so it deserves one) and
submits the whole list. Cancelling drops `dialog_data` — nothing was persisted.

**The calendar widget.** As the author expected, aiogram_dialog's `Calendar` is
subclassed rather than used as-is:

```python
class SeasonCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        # same views as the base, but the days view gets a custom `text=`
        # so each day cell can be marked
```

Day marks come from a getter that loads the season (or the `dialog_data` draft)
once: `🟢` free slot, `🔒` taken by someone else, `⭐` taken by you, `🎮` linked
to a game, plain number otherwise. `CalendarConfig(min_date, max_date)` pins the
view to the season's year, with month scope as the entry point so a whole season
is two taps away.

Flows on a published season:

- tap a day **with** a slot → slot window: take / release / change author
  (self vs team) / edit orgs / move / delete / open the linked game;
- tap a day **without** a slot → «Добавить дату» for authors.

**Link offer inside the existing flow.** `GameScheduleSG` gets one extra window
after `confirm`: if `FindSlotsNearGameStartInteractor` returns candidates, offer the
nearest with «Привязать» / «Не привязывать»; if it returns nothing, show the
warning with the three §10B options.

## 13. Web UI (shvatka-ui)

New standalone component `src/app/season/` plus `season.service.ts`, route
`/season` and `/season/:year`, entry in the header.

- **Season grid**: months **May–October** by default, rendered as month cards
  with day cells. If the season has slots outside that range the view
  auto-extends to cover them; «← Раньше» / «Позже →» buttons extend month by
  month up to the full January–December so a user can plan a cold-month game.
- **Cell states** mirror the bot marks: free, taken (owner or team name +
  emoji), linked game (links to the game page), your slot highlighted.
- **Compose mode** for a year with no season: fetch the defaults, edit the list
  in component state (mirrored to `localStorage` so a refresh is survivable),
  publish in one request. A 409 means someone else published first — offer to
  reload the now-published season.
- **Actions** on a published season, for authors: take (dialog choosing
  self vs team, plus an org picker reusing the existing player search), release,
  add slot, move slot. Everything else is read-only, and a published season
  renders for anonymous visitors.
- **Notifications tab**: add a `season_schedule_changed` renderer to
  `notification-render.ts` producing e.g. «Расписание сезона 2027: 3 изменения»
  linking to `/season/2027`.

## 14. Testing

Per `AGENTS.md`:

- **Unit** (`tests/unit/season/`): `default_slot_dates` for several years
  including the 9 May-is-Saturday case and the count/interval invariants; the
  ownership rules (free/owner/superuser/captain matrix); the ±3-day nearest-slot
  search including ties; **digest collapsing** (repeated moves of one slot → one
  line; move-and-move-back → nothing; take then release → nothing).
- **Integration** (`tests/integration/api_full/test_season.py`): publish a
  composed season → row + slots + pinned announcement; publish the same year
  twice → 409; take → 409 on a second taker, 403 for a non-author; link
  a game → slot date syncs; re-plan the game → slot follows; run the digest
  interactor → changes marked published and notifications written; run it on a
  season whose last slot has passed → `unpinned_at` set. Assert through
  `check_dao` as the existing tests do.
- Announcer and notification side effects are asserted through mocks in the
  style of `tests/mocks/org_notifier.py`.

## 15. Phasing

1. **Phase 1 — engine.** Tables + migration, `core/season/`, DAOs, DI wiring,
   REST API, `SeasonAnnouncer` + bot implementation, publication with pinning,
   the daily digest + unpin job, and the notification audience. **Plus the
   glossary entries of §3.2 in both `context.md` files** — the engine's in this
   PR, the UI's in the same one, since the two files describe one language. This
   is the reviewable core and makes the schedule real and readable everywhere.
2. **Phase 2 — bot.** `SeasonSG` dialogs including compose-in-`dialog_data`, the
   `SeasonCalendar` subclass, and the link offer / no-slot warning grafted onto
   `GameScheduleSG`.
3. **Phase 3 — web UI.** The season calendar component, compose mode, the
   extend-months controls, and the `season_schedule_changed` notification
   renderer.

Phases 2 and 3 are independent of each other and can land in either order.

## 16. Open questions

None outstanding — every question raised while drafting has been answered and
folded into §2 and §3. Two things are worth a second look during implementation
rather than now:

- **Digest wording** once collapsing is implemented — a slot that was taken and
  then moved on the same day is one line or two? (Proposal: one line per slot,
  listing its net state change.)
- **Compose-mode conflict UX** on the web: whether "someone published first"
  should try to merge the local list into the published season, or simply
  discard and reload. (Proposal: discard and reload — the local list is nine
  dates.)
