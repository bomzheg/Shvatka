---
name: Bot regression pass
about: Manual checklist to run against a real bot before merging a middleware, DI or filter change
title: 'Bot regression pass: '
---

**Branch / commit under test:**
**Run by:**

Open this as an issue and tick the boxes as you go — GitHub only makes task
lists interactive in issues and comments, never when viewing a file.

Run it after anything that touches **middleware, DI wiring, filters, or how the
acting user is resolved**. That is the class of change whose damage the
automated suite cannot see: unit tests cover the domain and
`test_dialogs_preview` renders every window, but neither can check whether a
real update still reaches the right handler with the right person attached.

The order is **by how quietly a bug would hide**, not by feature area. Section 1
is the part worth doing carefully; everything below it fails in a way you would
notice anyway. Delete the sections a given change can't possibly affect rather
than ticking them untested.

## Accounts and fixtures

| | who |
|---|---|
| **A** | approved author (`can_be_author`), and captain of a team |
| **B** | plain account, member of A's team, no team permissions |
| **C** | in no team, and never seen by the bot before — needed for first-contact checks |
| **S** | listed in `superusers`, for the merge commands |

Also: the team's group chat, one fresh group the bot has just been added to, a
game you can put into waivers and start, and a level you can send to testing.

## 1. Filters — a wrong answer here is silent

Filters resolve the acting player from the container. One that wrongly returns
`False` raises nothing — the command simply stops responding; one that wrongly
returns `True` hands someone rights they should not have. Both directions
matter, so each check names the account to use.

- [ ] **A** — `/new_level`, `/new_game`, `/my_games`, `/levels` in private each open their dialog. `can_be_author`
- [ ] **B** — the same four commands get no reply at all. `can_be_author`, negative
- [ ] **A** — `/manage_team` opens the Captain's bridge with team name, motto and captain. `TeamPlayerFilter(is_captain=True)`
- [ ] **B** — `/manage_team` with no permissions does nothing. `TeamPlayerFilter`, negative
- [ ] **B** — grant only «Переименовывать команду», then `/manage_team` still opens. This is the `or_f` branch and the likeliest thing to break.
- [ ] **A** — in the bridge, open «Игроки» → B and flip a permission: buttons appear and disappear with it, and the card keeps showing B's role and emoji. `F["team_player"]` in `when=`
- [ ] **A** — in the team chat, reply to a newcomer with `/add_in_team водитель`: added with that role, team notified. `IsTeamFilter` + `TeamPlayerFilter` + `HasTargetFilter`
- [ ] In the fresh group with no team, `/who_there` answers «тут нет команды». `IsTeamFilter`, negative
- [ ] **A** — add C to the team chat and **read the name in the prompt**: it must say «Принять **C** в команду …?». Naming the person who did the adding is a bug that has happened before. `user_join_chat_with_team`
- [ ] Press «Принять» on that prompt; repeat the flow and press «Отказать». C joins on accept, declined on refuse, and neither says «уже находится в команде». `button_join` / `button_join_no`
- [ ] Add another bot to the team chat: no prompt at all. `is_bot` guard
- [ ] With a game running, a correct key sent from the team chat by a member is accepted. `play.py`: `IsTeamFilter` + `TeamPlayerFilter`
- [ ] **org** — with the game active, `/spy` opens the spy menu. `OrgFilter(only_for_running_game=False)`
- [ ] `/spy_levels` and `/spy_keys` as an org *without* those rights are silent; grant the rights and they open. `OrgFilter(can_spy)` / `OrgFilter(can_see_log_keys)`
- [ ] **B** — `/spy` while not an org does nothing. `OrgFilter`, negative
- [ ] **A** — send an inline «Аппрувнуть» invite to C, then **click your own button**: alert «ну и смысл?». `is_inviter`
- [ ] **C** — click «согласен» on that invite: C is promoted. Getting «ну и смысл?» here means `is_inviter` is inverted. `is_inviter`
- [ ] **C** — on a fresh invite, «не согласен» declines and edits the message.
- [ ] **A** — invite B to be an organizer inline; your own click gives «ну и смысл?», B's acceptance makes them an org and refreshes B's open main menu. `is_inviter` + `BgManagerFactory`

## 2. Identity is still written on every update

Resolving the identity is a write: it upserts the user and the chat, and creates
the player for a first-time user. Handlers are not obliged to touch every
entity, so the middleware triggers those lookups itself
(`tests/unit/test_identity_middleware.py` guards it). These confirm it end to
end against a real database.

- [ ] **C** — from an account the bot has never seen, `/start` greets C by name: user row and player were created by that first update.
- [ ] Change your Telegram **@username**, send any message, open `/me`: the new username shows. A stale one means the upsert stopped running.
- [ ] Change your Telegram **first name**, send any message, reopen `/start`: the greeting uses it.
- [ ] Rename the team's group chat, send a message there, `/who_there`: no error, and the chat row carries the new title.
- [ ] In a plain group run `/chat_type`, convert it to a supergroup, then `/create_team`: the group-type hint first, the team after, and the migration message handled without error. `chat_migrate`
- [ ] Add the bot to a brand-new group and immediately `/chat_id`: both ids come back — the chat is upserted by the very update that asked.
- [ ] `/about` and `/privacy` reply in both a group and private.

## 3. Dependencies resolved from DI

These fail loudly rather than silently, but they sit on paths nobody hits by
accident.

- [ ] `/games` → a completed game → the keys page gives a working Telegraph link. `Telegraph`
- [ ] The same game's results picture renders. `ResultsPainter`
- [ ] Export a scenario as zip from both `/my_games` and a completed game. `FileGateway`
- [ ] Start `/new_game` and upload that zip back: «Успешно сохранено», and the game appears in `/my_games`. `FileGateway`
- [ ] Open a level from `/levels` and start testing it: the test starts and the first timed hint arrives on schedule. `LevelTestScheduler` + `LevelView`
- [ ] Send a level to another org for testing and accept from their account. same two deps
- [ ] Create a team and watch the game-log chat for the log message. `GameLogWriter`
- [ ] **S** — `/merge_teams <new_id> <forum_id>`: merged, logged, and the captain's open dialog refreshes. `GameLogWriter` + `BgManagerFactory`
- [ ] **S** — `/merge_players` and confirm: merged, and the target's dialog refreshes.
- [ ] Play far enough into a game for a timed hint to fire: hints still arrive. `HintSender` is built lazily, so this is the check that it is still built at all.

## 4. Edges where `None` used to pass quietly

Handlers call `get_required_*`, which raises a domain error rather than
propagating `None`. Normal users see no difference; these are the paths where
the difference shows. The goal is a sensible message or silence — never a
traceback loop.

- [ ] Turn on «Remain anonymous» as a group admin and send `/chat_id` and `/start`. Watch the log for `PlayerNotFoundError` / `UserNotFoundError`.
- [ ] Have a linked channel auto-forward a post into a group the bot is in: no error storm. These updates carry no real user.
- [ ] **C** — `/team`, `/players`, `/leave` while in no team each answer «Ты не состоишь в команде».
- [ ] Full waiver flow: `/waivers` as captain, vote as B, `/approve_waivers`, force-add a player, revoke a vote, cancel. This path has the most handlers on it.
- [ ] **org** — `/get_waivers` and `/get_waivers_draft` render their lists.
- [ ] Reply to someone's message with a command that takes a target (the promotion flow): the target is resolved and upserted. `FixTargetMiddleware`

## 5. Dialog smoke

Every window that reads the player, team or team_player in its template gets
those from its own getter, so rendering should be untouched by DI work. Quick
confirmations rather than real suspects — a blank field means a getter lost a
key.

- [ ] `/start` as a player in a team with an active game: name, team flag, role emoji, active game, and either the org powers block or the waiver status.
- [ ] `/me` → «Мой профиль»: key stats, correct-key ratio, team history.
- [ ] From the profile, change the displayed username and request a login link: both windows show the current username, and the link opens the site.
- [ ] `/teams` → a team → «Моя команда»: name, captain, players, played game numbers.
- [ ] From the Captain's bridge, «Былые свершения команды» opens the merge dialog with the team preloaded.
- [ ] «Перенести в другой чат» confirms with the old and new chat ids.

## 6. What a broken injection looks like in the log

Handlers and filters are wired with dishka's `@inject`, which relies on aiogram
passing `dishka_container` to everything it calls. When that link breaks it
shows up in one of three shapes rather than as a wrong answer — worth grepping
the run for while working through the list:

| signature | meaning |
|---|---|
| `TypeError: … missing 1 required … argument: 'dishka_container'` | the container never reached the callable |
| `KeyError: 'player'` (or `'team'`, `'team_player'`) | something still reads a middleware key that no longer exists |
| a burst of `PlayerNotFoundError` / `ChatNotFound` | updates that used to carry `None` quietly now raise |
