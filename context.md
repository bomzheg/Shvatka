# Context — the ubiquitous language of Shvatka

This is the **ubiquitous language** (UL) of the project in the DDD sense: the one
set of words used by the game's players and organizers, by this document, by the
code, and by the tests. A term listed here means exactly what it says here — in a
commit message, in a class name, in a variable, in a docstring.

Two rules keep it useful:

- **Code follows the glossary.** If you name a class `Task`, a reader has to guess
  whether you mean a `Level`, an `ActionRequest`, or a scheduler job. Use the
  term. If a name in the code contradicts the glossary, one of the two is wrong —
  say which in your PR.
- **The glossary follows the domain.** When the domain gains a concept (or an
  existing word shifts meaning), change this file in the same PR that changes the
  code. A term nobody uses should be deleted, not left to rot.

The domain is Russian-speaking, the code is English. Every entry therefore carries
both forms: **the Russian term is what organizers and players actually say**, and
the English one is what the code calls it. User-facing strings stay Russian; code,
comments and docstrings stay English (see `AGENTS.md`).

The web front-end ([bomzheg/shvatka-ui](https://github.com/bomzheg/shvatka-ui))
carries the same glossary in its own `context.md`, mapped onto its code. The two
files describe one language — when a term changes here, change it there too.

## The domain in one paragraph

**Схватка** (*Shvatka*) is a night urban search game, of the same family as
Encounter and Дозор. An **author** writes a **game** as a sequence of **levels**;
each level poses a **puzzle** that a **team** has to solve on the ground, on foot
or by car. Solving it yields a **key** — a code string hidden at a location, held
by an agent, or encrypted in the level text — which the team sends to the engine.
The right key moves the team to the next level; **hints** are released
automatically as time on the level passes, so a stuck team eventually gets
unstuck, at the cost of time. The game is a race: the winner is the team with the
lowest total time, adjusted by **bonuses** and **penalties**. This repository is
the engine — domain, REST API and Telegram bot — that runs all of it.

## Bounded contexts

The codebase is one deployable with several entry points rather than separately
deployed contexts, but the model splits along these lines. `core` holds the domain
and knows nothing about the edges; the edges depend inward.

| Context | What it owns | Where |
| --- | --- | --- |
| **Game engine** (core domain) | Games, levels, scenarios, keys, play, results | `shvatka/core/` |
| **Players & teams** | Identity of a person, membership, roles, permissions | `shvatka/core/players/`, `shvatka/core/teams/` |
| **Waivers** | Who is allowed to play a given game | `shvatka/core/waiver/` |
| **Notifications & requests** | User-to-user requests and the inbox they produce | `shvatka/core/notifications/` |
| **Telegram bot** | The bot as a UI over the engine | `shvatka/tgbot/` |
| **REST API** | The HTTP UI over the engine, consumed by the web front-end | `shvatka/api/` |
| **Infrastructure** | Persistence, scheduling, file storage, forum import | `shvatka/infrastructure/` |

Where two contexts share a word, this glossary gives the core meaning and notes
the edge-specific twist.

---

## People and identity

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **User** | Пользователь | A Telegram account. Purely an external identity — it carries no game meaning on its own. | `dto.User` |
| **Player** | Игрок | A person as the domain knows them: the identity everything else hangs off. A player may be linked to a Telegram `User`, to a `ForumUser`, to an `EmailAccount`, or to none of these. | `dto.Player` |
| **Dummy player** | — | A player created from imported forum data with nobody behind it yet (`is_dummy`). Exists so historical games have real participants; merged into a live player later. | `Player.is_dummy` |
| **Author** | Автор | A player allowed to write games (`can_be_author`). The right is granted by another author — see *promotion*. | `Player.can_be_author` |
| **Promotion** | Аппрув | An existing author invites a player to become an author; on acceptance `can_be_author` is set. | `player.promote`, `RequestType.promotion` |
| **Superuser** | Админ движка | A configured operator of the engine itself, above the game roles. Resolved only through `SuperusersResolver` — never by re-reading config at a call site. | `core/interfaces/superusers.py` |
| **Identity provider** | — | The way any layer above the DAO asks "who is acting" — returns the current user/player/team. Interactors take it instead of a pre-resolved player. | `core/interfaces/identity.py` |
| **Forum user** | Пользователь форума | An account imported from the old forum, attached to a player. | `dto.ForumUser` |
| **Merge (player)** | Слияние игроков | Folding a dummy (usually forum-sourced) player into a live one so one person has one history. Requires admin approval and a manually built team timeline. | `player.merge_players`, `RequestType.player_merge` |
| **Timeline** | История команд | The manually built sequence of team memberships used when merging players. Must cover every *waiver point*. | `players.dto.TimelineItem` |
| **Waiver point** | — | An interval (`start_at − 1h` … `start_at + 48h`) in which a waiver proves the player was in a given team, so a merged timeline may not contradict it. | `players.dto.WaiverPoint` |
| **One-time login link** | Одноразовая ссылка | A short-lived link that logs a player into the web UI without a password. | `services/one_time_link.py` |
| **Achievement** | Ачивка | A named thing a player did once, recorded for fun. | `dto.Achievement`, `enums.Achievement` |

## Team

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Team** | Команда | The unit that plays. Has a name, a captain, optionally a Telegram chat and a forum counterpart. Teams play, players don't. | `dto.Team` |
| **Team player** | Участник команды | A player's membership in a team over an interval (`date_joined` … `date_left`), with a role, an emoji and permissions. A player is in at most one team at a time. | `dto.TeamPlayer`, `dto.FullTeamPlayer` |
| **Captain** | Капитан | The team's head: submits waivers, manages membership, implicitly holds every team permission. Held by a player, not by a membership — see *captaincy transfer*. | `Team.captain`, `FullTeamPlayer.is_captain` |
| **Captaincy transfer** | Передача капитанства | The captain making another **player of the same team** the captain. Only the current captain may (an admin may go over their head), and it is one-way — the old captain cannot take it back. | `services/team.change_captain`, `CaptainChanged` |
| **Captained team** | Команда, где я капитан | A team a player captains whether or not they play in it. The captaincy outlives the membership: a captain who moves to another team as a field player keeps leading the old one, keeps managing its roster and name, and may return to it at any time — but cannot submit its waivers, because a waiver is submitted from inside the team. | `teams.dto.CaptainedTeam`, `TeamDao.get_captained_teams` |
| **Role** | Роль | Free text describing what a member does in the field: `полевой` (default), `водитель`, `мозг`, `капитан`… Each has a default emoji. | `utils/defaults_constants.py` |
| **Team permission** | Полномочие | A right delegated by the captain: manage waivers, manage players, change the team name, add/remove players. The captain has all of them regardless. | `enums.TeamPlayerPermission` |
| **Team chat** | Чат команды | The Telegram supergroup the bot talks to the team in. | `dto.Chat`, `services/team.py` |
| **Merge (team)** | Слияние команд | Folding an imported forum team into a live team. Admin-approved, like the player merge. | `team.merge_teams`, `RequestType.team_merge` |

## Game

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Game** | Игра | The aggregate root of the engine: an author, a name, an ordered list of levels, a status, a start time, and results. | `dto.Game`, `dto.FullGame`, `dto.PreviewGame` |
| **Game status** | Статус игры | Where the game is in its lifecycle — see the table below. Nearly every permission check reads it. | `enums.GameStatus` |
| **Game number** | Номер игры | The game's place in the archive. Assigned as `max + 1` at completion, so only played games have one. | `Game.number`, `game.complete_game` |
| **Game run** | Ход игры | Everything playing a game produced: the **level times**, the typed **keys**, the **events** and the **timers**. Not part of the game — the game is what the author wrote — but what a *second* run of the same game would collide with, which is why undoing a false start sweeps it. Four tables, and only these four. | `levels_times`, `log_keys`, `event_log`, `timers_log`; `GameRuntimePurger` |
| **Organizer (org)** | Организатор (орг) | A player who runs a game rather than playing it. The author is the **primary organizer** and holds every right; anyone else invited is a **secondary organizer** with explicit permissions. | `dto.Organizer`, `dto.PrimaryOrganizer`, `dto.SecondaryOrganizer` |
| **Org permission** | Полномочие орга | What a secondary organizer may do: spy, see the key log, validate waivers, view the scenario. **Nothing is granted by default.** | `enums.OrgPermission` |
| **Manage token** | — | The game's secret, checked when someone acts on the game through an invite link. | `Game.manage_token`, `organizers.check_game_token` |
| **Publication** | Публикация | Posting a finished game's results to a Telegram channel. Possible once, after the game is finished or complete. | `GameResults.published_chanel_id`, `Game.can_be_publish` |
| **Release** | Релиз | The promo an author publishes before a game — a **banner** followed by a few words about the theme and a map of the district. The part after the banner is a plain list of hint parts, so it is written and rendered with the same machinery as a hint. Optional: a game without one is played exactly as before. | `dto.GameRelease`, `core/games/release_interactors.py` |
| **Bot message** | — | One message the bot posted, kept so it can be edited or removed later: a chat id and a message id, nothing more. Shared by everything that has to clean up after itself — an action request's messages, a release's post — and never part of a game, a request or a release itself. | `dto.BotMessage` |
| **Banner** | Баннер | The wide title picture (with its caption) that leads a release. Kept apart from the rest because it is the one part small enough to stand alone above the site's header; roughly 1280×250—1280×550, though nothing enforces that. A release may be just a banner, or have none at all. | `dto.GameRelease.banner`, `games.release_banner` |
| **Release post** | Пост релиза | Where a release currently stands in the announcements channel: one message per part, the banner first. Editing the release edits those messages; it is not a second **publication**, which stays the word for a finished game's results. Purely the bot's bookkeeping: a list of **bot messages** in `games.release_post`, read and written only by the announcing view, never through a core entity — the same arrangement as `action_requests.bot_messages`. | `GameDao.get_release_post`, `tgbot/views/game_release.py` |

### Game statuses

| Status | Русский | Meaning |
| --- | --- | --- |
| `underconstruction` | в процессе создания | Being written. Editable, deletable. |
| `ready` | полностью готова | Finished scenario, not yet collecting waivers. **Not used any more** — kept for old games; a game goes straight from `underconstruction` to `getting_waivers`. |
| `getting_waivers` | сбор вейверов | Teams are declaring who plays. Still editable. |
| `started` | началась | Being played. |
| `finished` | все команды финишировали | Every team has passed the last level; results not yet closed. |
| `complete` | завершена | **Terminal.** The game is closed and archived, and gets its number here. This is also the status that makes a game public: any player may read the game, its whole scenario, its key log and its results, with no organizer permission involved. |

`ACTIVE_STATUSES` = `getting_waivers`, `started`, `finished` — only one game may be
active at a time. `EDITABLE_STATUSES` = `underconstruction`, `ready`,
`getting_waivers`. `ADMIN_MANAGEABLE_STATUSES` = the active ones plus `complete`
— the games the **admin panel** sees at all, and of them only the *status*: an
admin may walk a game to another status (`PUT /admin/games/{id}/status`, the way
back out of waivers opened too early) but never read its content while it is not
complete. A game in `underconstruction` or `ready` is its author's alone and is
reported as not found there — including the game an admin has just moved back,
which is the point: the fix hands the game over and ends the admin's part in it.

Two more groups name the two halves of a **rewind** — an admin declaring that a
run never happened. `PLAYED_STATUSES` = `started`, `finished`, `complete` (the
ones a game only reaches by being played) and `REWOUND_STATUSES` =
`getting_waivers`, `ready`, `underconstruction` (the ones before a run). Moving
from the first group into the second is the only time the **game run** may be
swept along with the status (`purge_runtime`), because it is the only time the
run is being disowned rather than made history. The waivers are never part of
it: who signed up survives a false start. See SHEP-0013.

A game's **release** follows the statuses on its own schedule, wider than
`EDITABLE_STATUSES`: it may be rewritten up to and including `finished` (it is
promo, not part of the play) and only an admin may touch it once the game is
`complete`. It reaches the channel with the move to `getting_waivers` — written
later than that, while the game runs, it is stored but never posted, because the
audience it was meant for is already playing.

Every "is this visible?" check in the engine hangs off `complete`: `check_can_read`
and `check_can_view_scenario` in `core/rules/game.py`, and `get_typed_keys` /
`get_game_stat` in `core/services/game_stat.py`, all return early for a complete
game and only then fall back to author or organizer rights.

## Scenario — what an author writes

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Level** | Уровень | One stage of a game: a puzzle, its hints, and the conditions that end it. Belongs to its author; gets a `number_in_game` when linked into a game. | `dto.Level`, `dto.GamedLevel` |
| **Level scenario** | Сценарий уровня | The level's content proper: the time hints plus the conditions. This is what gets validated, exported and imported. | `scn.LevelScenario` |
| **Game scenario** | Сценарий игры | The whole game as a portable document — levels plus files. Uploaded and downloaded as a zip. | `scn.GameScenario`, `scn.FullGameScenario`, `scn.RawGameScenario` |
| **`name_id`** | — | The author-chosen id of a level, unique per author (`[a-zA-Z0-9_-]+`). Used to route between levels, and stable across games. | `Level.name_id`, `validate_level_id` |
| **Scenario model version** | — | The schema version of a stored scenario (`__model_version__`). Version 0 documents are upgraded on read. | `core/migration_utils/` |
| **Puzzle** | Загадка уровня | The hint released at minute 0 — the level's starting point. Not a separate concept: it is simply the first time hint, and every level must have one. A level must be solvable from its puzzle alone. | `HintsList.verify` |
| **Time hint** | Подсказка | A batch of content released this many minutes after the team reached the level. Times are unique and sorted; there is always one at 0. | `hints.TimeHint` |
| **Hint part** | Часть подсказки | One piece of a hint's content: text, photo, video, audio, document, GPS point, venue, contact, sticker… A hint is a list of parts. | `hints.AnyHint`, `enums.HintType` |
| **Key** | Ключ | The code string a team submits. Starts with `SH` or `СХ`, then uppercase Latin/Cyrillic letters and digits — e.g. `SHHELLO99`, `СХПРИВЕТ13`. | `action.SHKey`, `is_key_valid` |
| **Master key** | Мастер-ключ | The key that completes the level. Modelled as the *win condition*: a set of keys, **all** of which must be entered, in any order. At most one per level. The author need not publish it if the level ends by another route. | `action.KeyWinCondition` |
| **Effects key** | Ключ с эффектами | A key that triggers effects instead of (or as well as) completing the level. Any number per level. | `action.KeyEffectsCondition` |
| **Timer** | Таймер | Time from the start of the level at which effects fire. Any number per level; at most one may end the level, and no other timer may be set later than that one. | `action.LevelTimerEffectsCondition` |
| **Condition** | Условие | The general form of "when X, do Y" in a level — a win condition, an effects key, or an effects timer. A level must have at least one that can end it. | `action.AnyCondition`, `scn.Conditions` |
| **Effects** | Эффекты | What a condition does: award bonus minutes (or a penalty), reveal hints, complete the level, and optionally route to a named level. | `action.Effects` |
| **Routed level-up** | Переход на уровень | Completing the level *and* jumping to a specific `name_id` rather than the next one in order. This is how a non-linear game is built. | `Effects.is_routed_level_up`, `docs/…/author/level-howto.adoc` |
| **File meta / GUID** | Файл / GUID | A media file used by hints, identified by a GUID inside the scenario. The scenario references GUIDs; the actual bytes live in file storage and in Telegram. | `hints.FileMeta`, `hints.FileMetaLightweight` |
| **Level testing** | Тестирование уровня | An organizer walking a single level alone, before the game, to check it works. | `dto.LevelTestSuite`, `services/level_testing.py` |

## Play — what happens during a game

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Action** | — | Something that happens and may change the game: a team typed a key, or a level timer fired. | `action.Action`, `TypedKeyAction`, `LevelTimerAction` |
| **State** | — | What the engine knows when judging an action: which keys the team has already typed, which effects already fired. | `action.State`, `TypedKeysState`, `LevelTimerState` |
| **Decision** | — | The verdict on an action: significant, effects, no action, or not implemented. Each condition returns one; the level picks the one that counts. | `action.Decision`, `DecisionType` |
| **Level time** | Время уровня | The record that a team reached a given level at a given moment. The backbone of results — a team's progress *is* its list of level times. | `dto.LevelTime`, `levels_times` table |
| **Level up** | Переход на уровень | A team leaving its current level for the next (or a routed) one. | `Effects.level_up`, `views.game.LevelUp` |
| **Key log** | Лог ключей | Every key ever submitted, right or wrong, with who typed it and when. Visible to organizers with `can_see_log_keys`, and published with the game. | `dto.KeyTime`, `dto.InsertedKey`, `log_keys` table |
| **Key type** | Тип ключа | How a submitted key was judged: `wrong`, `simple` (correct), `bonus` (legacy bonus key), `effects`. | `enums.KeyType` |
| **Duplicate key** | Повтор | A key this team has already submitted. Recorded, but changes nothing. | `KeyTime.is_duplicate` |
| **Game event** | Событие игры | A recorded firing of effects for a team on a level — the audit trail behind bonuses and bonus hints. | `dto.GameEvent`, `games.dto.Event`, `event_log` table |
| **Spy** | Шпион | An organizer's live view of where every team is and which hint it is on. Needs `can_spy`. | `dto.SpyHintInfo`, `organizers.check_can_spy` |
| **Game log** | Лог игры | The organizers' running commentary of the game's course — started, team levelled up, finished. | `views.game.GameLogEvent`, `GameLogType` |

## Results and statistics

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Game stat** | Статистика игры | Per team, the list of level times. The raw material for every results view. | `dto.GameStat`, `dto.GameStatWithHints` |
| **Bonus** | Бонус | Minutes taken off a team's result, awarded by effects. | `Effects.bonus_minutes` > 0 |
| **Penalty** | Штраф | Minutes added to a team's result. The same field, negative — there is no separate penalty concept. | `Effects.bonus_minutes` < 0 |
| **Bonus event** | — | One bonus or penalty as it happened: when, from which effects, from a key or a timer, on which level. | `games.dto.BonusEvent`, `BonusSource` |
| **Results table** | Таблица результатов | The exported spreadsheet: level times, per-level durations, and a bonuses block. Adjusted times are deliberately **not** computed — the raw numbers are handed out so the reader can work them out. | `games/results.py` |

## Waivers

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Waiver** | Вейвер | One player's confirmed participation in one game with one team. The engine's answer to "who is allowed to play". | `dto.Waiver` |
| **Vote** | Голос | A player's own answer during collection, before the captain approves: `yes`, `no`, `think`. | `dto.Vote`, `enums.Played` |
| **Played** | — | The final state of a waiver: `yes`, `no`, `think`, `revoked` (не допущен капитаном), `not_allowed` (не допущен организаторами). | `enums.Played` |
| **Draft waivers** | Черновик вейверов | The votes collected so far, not yet approved by the captain. | `waiver/interactors.py` |
| **Approve waivers** | Утвердить вейверы | The captain fixing the team's final list, after which it goes to the organizers. | `waiver.approve_waivers` |

## Requests and notifications

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Action request** | Заявка | A user-to-user request that needs someone's decision, with a lifecycle: `pending` → `accepted` / `declined` / `cancelled` / `expired`. *Заявка* is the term — plain *запрос* is too generic, though it reads fine mid-sentence ("ваш запрос на вступление в команду"). | `notifications.dto.ActionRequest`, `enums.RequestStatus` |
| **Request type** | Тип запроса | `team_join_invite`, `team_join_request`, `org_invite`, `team_merge`, `player_merge`, `promotion`. | `enums.RequestType` |
| **Notification** | Уведомление | One inbox item for exactly one recipient — the record that something happened. A request produces notifications; a notification is not itself actionable. | `notifications.dto.Notification`, `enums.NotificationType` |
| **Severity** | Важность | How much a notification matters (`low` / `normal` / `important`); drives UI emphasis in the feed. | `enums.NotificationSeverity` |
| **Push subscription** | Подписка на пуши | A browser endpoint registered for web push. | `push_subscriptions` table |

## Search

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Hit** | Находка | One search result, always carrying the field it matched and a snippet for highlighting. | `search.dto.GameHit`, `LevelHit`, `TeamHit`, `PlayerHit` |
| **Search filters** | Фильтры поиска | Which of games / levels / teams / players to search. Everything by default. | `search.dto.SearchFilters` |

---

## Naming rules that follow from the language

- **Domain DTOs are `dto.*`** from `shvatka.core.models`; scenario documents are
  `scn.*`; play-time modelling is `action.*`. Import the module, not the name.
- **A use case is an `Interactor`** named after what it does to the domain —
  `GameStatReaderInteractor`, `ReplaceTeamWaiversInteractor` — not after the
  endpoint or the screen that calls it.
- **`level_number` counts from 0** in the model and is shown as `+ 1` to people.
  Don't rename it to hide that; convert at the edge.
- **Minutes are the domain's unit of time** for hints, timers and bonuses. Fields
  holding minutes say so in a docstring; `timedelta` is used where the code needs
  arithmetic.
- **`org` is an acceptable short form of organizer** — it is what organizers call
  themselves — and it is the only abbreviation the language sanctions.

## Words we don't use

Each of these has shown up in review or in an old name. They are ambiguous or
belong to a neighbouring game, and the right-hand column is what to say instead.

This is about **written** language — identifiers, docstrings, docs, UI copy. Some
of these words are in live spoken use and nobody needs correcting for saying them;
where that is so, the row says as much.

| Not this | Say this | Why |
| --- | --- | --- |
| Quest, task, stage, mission | **Level** (`Level`) | The domain word is уровень; the others come from other games. |
| Answer, password | **Key** (`SHKey`) | A key has a defined format and a life in the key log. |
| Code / код | **Key** (`SHKey`) | People do say *код* out loud, and that's fine in speech — but it isn't the term. In code and copy it's a key, because only a key has the `SH`/`СХ` format and a row in the key log. |
| Registration, application, sign-up | **Waiver** (`Waiver`) | Вейвер is the domain word and covers the vote → approve flow. |
| Admin (for a game) | **Organizer** / **org** | *Admin* means the engine's superuser. A game has organizers. |
| Moderator | **Organizer** or **superuser** | Neither role exists under that name. |
| Level text / текст уровня | **Puzzle** — загадка уровня | Say *текст уровня* all you like in conversation; it's the popular name and it's exact whenever the puzzle happens to be text. In writing use *загадка уровня*, because a puzzle can just as well be a photo, a video or an audio file, and because there is no separate "level text" in the model — it is the 0-minute hint. `level-concept.adoc` already says this: «Текст уровня это частный случай подсказки выходящей в 0 минут. Отдельной концепции текста уровня не существует.» |
| Clue, tip | **Hint** (`TimeHint`) | One word for the thing released on a timer. |
| Announcement, анонс | **Release** — релиз | Организаторы говорят *релиз* про промо перед игрой; *анонс* размывает его с любым другим объявлением. |
| Fine, malus | **Penalty** (negative `bonus_minutes`) | A penalty is a negative bonus, not another field. |
| Group, squad, crew | **Team** (`Team`) | Group means a Telegram chat here. |
| Member | **Team player** (`TeamPlayer`) | Membership is an interval with permissions, not a flag. |
| Finished = complete | **Finished** ≠ **complete** | Finished means all teams passed the last level; complete means the game is closed and numbered. |

## Where to read further

- `AGENTS.md` — how to write code in this repository (layering, Interactors, DI, tests).
- `docs/modules/ROOT/pages/author/level-concept.adoc` — the authoritative
  description, in Russian, of how a level scenario is put together.
- `docs/modules/ROOT/pages/author/level-howto.adoc` — building linear and
  non-linear games out of keys, timers and effects.
- `docs/modules/ROOT/pages/author/` — the rest of the author's path: writing a
  level, assembling a game out of levels, inviting organizers, scheduling a start.
- `docs/modules/ROOT/pages/setup_team/` — teams, chats and waivers from the
  captain's side, including team permissions.
- `docs/modules/ROOT/pages/player/` — joining and leaving a team, promotion,
  and how a game is played.
- `docs/modules/ROOT/pages/org/spy.adoc` — the spy, the key log and the rest of
  what an organizer sees while a game runs.

The user documentation is written for players and organizers, so it uses the
Russian half of this glossary and nothing else. Where the interface contradicts a
term, the docs use the term and mention the label in passing — see *роль*, which
the bot calls «должность».
