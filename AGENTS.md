# AGENTS.md

Guidance for AI agents (and humans) working in the **Shvatka** codebase — an
engine for the night search game *Encounter/Shvatka*, exposing a REST API and a
Telegram bot.

## TL;DR for agents

- **Write new code as `Interactor` classes** (callable, DI-wired), not as free
  service functions. The project is mid-migration — see below.
- **`HolderDao` holds per-table daos only** — a complex dao is never a property
  on it; register it in `ComplexDaoProvider` and take it from DI. **Don't add new
  middleware data keys** either — prefer DI.
- **Don't rewrite existing code** unless the task requires it. Leave working
  service functions alone; only new functionality should adopt the new style.
- **Capture review feedback as rules.** When a code-review comment states a
  reusable project convention (not a one-off fix), write it down here so it's
  not re-litigated on the next PR.
- **Design decisions live in SHEPs** (`docs/modules/shep/pages/`) — one page per
  non-trivial change. Read the relevant one before touching the subsystem it
  describes, and update its status when a phase lands. This file keeps the
  *rules*; a SHEP keeps the *decision and why*.
- **Prefer `IdentityProvider` and `CurrentGameProvider`** for resolving the
  current user/player/team/game everywhere except the DAO layer.
- **New API endpoint → integration test.** New **domain** class/method →
  **unit test**.
- **Lint and tests run in CI.** Pushing and reading CI is an acceptable
  substitute for the slow testcontainer suite; run `ruff` and `pytest
  tests/unit` locally for fast feedback.

## Project layout

```
shvatka/
  core/            # Pure domain + application logic. No framework imports.
    models/        # DTOs (dto.*), enums, action models
    interfaces/    # Protocols: dal/* (DAO contracts), identity, current_game, ...
    services/      # OLD style: free service functions (e.g. game.py, key.py)
    games/         # interactors.py, adapters.py, game_play.py, dto.py
    scenario/, waiver/   # same shape: interactors.py, adapters.py, services.py
    rules/         # pure business rules / checks
    views/         # view Protocols (GameView, ViewSender, TeamNotifier, ...)
  api/             # FastAPI app, split by subdomain (see below)
  tgbot/           # aiogram 3 + aiogram_dialog bot: handlers/, dialogs/, views/
  infrastructure/
    db/            # SQLAlchemy 2 models, dao/ (impls), migrations (alembic)
    di/            # dishka Providers wiring interactors + adapters
    bus/, clients/, scheduler/, picture/, ...
tests/
  unit/            # Fast, no DB. domain/, services/, mapper/, serialization/, ...
  integration/     # Slow, real Postgres via testcontainers. api_full/, bot_full/
  fixtures/, mocks/
```

Dependency direction: `core` knows nothing about `api`, `tgbot`, or
`infrastructure`. The outer layers depend inward. Keep it that way — `core`
talks to the outside world only through Protocols in `core/interfaces/`.

## The Interactor migration (most important convention)

The codebase is evolving **from service functions to `Interactor` classes** with
an async `__call__` and constructor-injected dependencies. New code MUST follow
the Interactor style; don't gratuitously refactor the old free functions in
`core/services/`.

```python
# shvatka/core/games/interactors.py — plain class, or a frozen dataclass
# (@dataclass(kw_only=True, slots=True, frozen=True)) when there are several deps
class GameStatReaderInteractor:
    def __init__(self, dao: GameStatReader):
        self.dao = dao

    async def __call__(self, game_id: int, identity: IdentityProvider) -> dto.GameStatWithHints:
        player = await identity.get_required_player()
        game = await self.dao.get_by_id(game_id)
        return await get_game_stat_with_hints(game, player, self.dao)
```

- Live next to their domain in `core/<area>/interactors.py`.
- Depend on **Protocols**, not concrete implementations. Compose the narrow
  `core/interfaces/dal/*` protocols into an area-specific Protocol in
  `core/<area>/adapters.py` (see `shvatka/core/games/adapters.py`).
- Take `identity: IdentityProvider` (and `current_game` via a constructor dep)
  instead of receiving resolved `player`/`team`/`game` arguments.
- Reusing existing service functions internally is fine — Interactors often wrap
  them during the migration.

### Wiring with dishka

Register interactors and their adapters in `shvatka/infrastructure/di/`. Most
register with a bare `provide(SomeInteractor)`; adapters map a concrete DAO impl
onto its Protocol:

```python
class GamePlayProvider(Provider):
    scope = Scope.REQUEST

    game_stat_reader_dao = provide(GameStatReaderImpl, provides=GameStatReader)
    get_game_state_interactor = provide(GameStatReaderInteractor)
```

A `dao/complex/*` impl takes `HolderDao` as its only constructor argument, so the
class-provide shorthand is enough — write an explicit `@provide` factory only
when the impl needs something dishka can't build (`GamePlayDaoImpl`'s per-request
`cache`, say).

Consume them at the edges via `FromDishka[...]` on an `@inject`-decorated
route/handler.

A dependency that belongs to both edges — a dao, a policy, an interactor — goes
in the shared providers (`infrastructure/di/`, listed by `get_providers()`).

**Showing something in telegram stays in `tgbot`.** Never move a bot view into
the shared providers to reach it from the api. An interactor that needs the chat
to change takes a **view Protocol** from `core/views/`, and each container binds
its own implementation: the bot one in `tgbot/main_factory.py`, a web one in
`api/app/dependencies/`, a no-op in `infrastructure/di/infra.py`. (Where an
event fits better than a call, submit one to the `Bus` instead.)

**What a view showed is the view's to remember**, not the domain's. A chat or
message id must never reach a core entity: store it in its own column or table,
read/write it through dao methods returning plain values, and keep it out of
`to_dto` (see `action_requests.bot_messages`, `games.release_post`).

## Use the providers (`IdentityProvider` / `CurrentGameProvider`)

Resolve "who is acting" and "what game is active" through these Protocols
**everywhere except the DAO layer** — DAOs take concrete `dto.Player`/`dto.Team`.

- `IdentityProvider` (`core/interfaces/identity.py`) — `get_user`, `get_player`,
  `get_team`, `get_chat`, `get_full_team_player`, plus `get_required_*` variants
  that raise instead of returning `None`.
- `CurrentGameProvider` (`core/interfaces/current_game.py`) — `get_game` /
  `get_full_game` and their `get_required_*` variants.

Implementations are per-edge and cache within a request: `ApiIdentityProvider`
(`api/app/dependencies/auth.py`), `TgBotIdentityProvider`
(`tgbot/services/identity.py`), `CurrentGameProviderImpl`
(`core/services/current_game.py`).

## Background work goes through the nursery

**Never start a detached task yourself.** `asyncio.create_task` and
`asyncio.ensure_future` are banned by lint (`TID251`); spawn on the app-scoped
`Nursery` (`core/interfaces/nursery.py`), taken as `FromDishka[Nursery]`. It
opens a **fresh REQUEST scope** per task, so the task owns its own db session
instead of borrowing the handler's, and it logs failures instead of dropping
them. (`asyncio.TaskGroup` is not banned — it's the right tool when you await
the group, the wrong one here.)

A task is just an async function in `shvatka/tgbot/tasks.py`. Plain parameters
are the data of the run; `FromDishka[...]` parameters are injected:

```python
async def publish_scenario_to_forum(
    game: dto.FullGame, username: str, password: str, chat_id: int,
    bot: FromDishka[Bot],
) -> None: ...

nursery.spawn(publish_scenario_to_forum, game=game, username=..., password=..., chat_id=...)
```

**Entities travel as arguments, resources come from DI.** Domain DTOs are
detached dataclasses, so passing a loaded game is free (and keeps the
authorization the handler already did). Never pass anything tied to the caller's
scope — a dao, a session, a `HintSender`.

`tgbot/utils/fastapi_webhook.py` is exempt from the ban: it's a portable copy of
aiogram's handler that must not import from `shvatka`. Leave it alone.

### Showing the game is decided as data, shown after the commit

An interactor never shows anything while it works. It appends `ViewTask` values
(`core/views/game.py`) to a plain list, commits, and hands the list over — so a
transaction that fails shows nothing. See SHEP-0009.

```python
tasks = ShowTasks(view=self.view_(new_key, input_container))
tasks.extend(await self.process_level_up(...))
await self.dao.commit()
await self.sender.show_later(tasks)
```

- New task class plus a branch in each view's router — never a new method on
  `GameView`. `AnyViewTask` is a union, so a view that forgets one fails `mypy`.
- `GameView.show` **renders now**; `ViewSender.show_later` **arranges for it**
  (only `NurseryViewSender` implements it). A view must never spawn.
- A task carries **domain dtos only** — never a dao, session or sender — and may
  be **rendered more than once** (a failed delivery is retried whole), so a task
  that *counts* something is wrong.
- Order is per chat, not per game: `group_by_team` splits a batch and the views
  show the groups at once. Keep rendering short — shutdown cancels jobs still
  running after `drain_timeout`.

## DAO layer

- **Writes belong to the table's own DAO.** A DAO may run complex `SELECT`s with
  joins rooted at its own entity, but `INSERT`/`UPDATE`/`DELETE` for a table live
  in that table's DAO. Each DAO is parametrised with exactly one model — new
  table means a new DAO (e.g. `LevelFileDao`, `GameFileDao`).
- **Orchestration is a use-case action, not a DAO action.** When an operation
  spans tables, the DAO only *provides* the per-table methods; the use case
  decides when and in what order to call them. A `dao/complex/*` impl may expose
  those methods behind one Protocol, but it should not drive the sequence.
- **At most one DAO per interactor.** Compose what it needs behind a single
  Protocol and a single `dao/complex/*` adapter.
- **A complex dao reaches its consumer through DI**, never as a `HolderDao`
  attribute. Cross-table adapters all live in `dao/complex/*`, one module per
  area — there is no second package. They import `HolderDao` directly and are
  registered once in `ComplexDaoProvider` (`infrastructure/di/db.py`), so both
  edges see them. Handlers, interactors and scheduler wrappers take the
  Protocol, not `HolderDao`.
- **Generic SQLAlchemy by default.** Dialect-specific helpers (e.g.
  `postgresql.insert(...).on_conflict_do_nothing()`) are fine when they make a
  query meaningfully better or faster — not by reflex.

## API layout (subdomain packages)

`shvatka/api/` separates **what the API is about** (subdomains: `auth`,
`players`, `teams`, `games`, `waivers`, `files`, `notifications`,
`action_requests`, `search`, `push`, `admin`, `version`) from **how the app is
wired** (`app/`: router, error handler, config, dependencies, middlewares,
utils). `shared/` holds models used by more than one subdomain.

- A subdomain package contains `routes.py` (with `setup() -> APIRouter`) plus
  `requests.py` / `responses.py` as needed. Register the router in
  `shvatka/api/app/router.py`.
- `app/` holds only what every subdomain shares. If something in `app/` knows
  about one subdomain, it belongs in that subdomain.
- A model belongs in `shared/` only when **two or more** subdomains use it.
- Cross-subdomain reuse is explicit — import `from shvatka.api.waivers import
  responses as waivers_responses` rather than copying or promoting the model.

## Testing

**pytest** + `pytest-asyncio` (mark async tests with `@pytest.mark.asyncio`).
Integration tests use **testcontainers** (real Postgres) and **httpx**
`AsyncClient`.

```shell
pytest tests            # everything (needs Docker for testcontainers)
pytest tests/unit       # fast unit-only loop, no DB
```

- **New API endpoint or behavior → integration test** in
  `tests/integration/api_full/`. Drive the real app through the `client`
  fixture; authenticate with `auth.create_user_token(...)` passed as a cookie.
  See `tests/integration/api_full/test_game.py` for the pattern.
- **New domain class/method → unit test** in `tests/unit/`.
- **Assert through `check_dao`, not the acting `dao`** — it has its own session,
  so assertions observe committed data.
- **The test container is the app container plus overrides.**
  `tests/fixtures/di.py` builds it from `get_root_app_providers(...)`, so a new
  app provider reaches the tests without touching `tests/`. Test doubles live in
  `get_test_override_providers()` and go **last**. An override must use
  `@provide(override=True)` **in the same scope** as the factory it replaces —
  a different scope silently does nothing. A double only passed by hand
  (`GameLogWriterMock`, `MemoryFileStorage`) is provided under its own concrete
  type without `override=True`. The container uses `STRICT_VALIDATION`;
  `tests/unit/test_di.py` builds every container and is the fast DI check.
- **Coverage**: `fail_under` in `[tool.coverage.report]` is enforced by the CI
  `pytest --cov` step. Raise it as the number grows; don't lower it to turn a
  build green. `[tool.coverage.run] omit` drops the bot layer, migrations, and
  one-shot scripts — new code of that kind goes in the list with a comment.
- **The bot's per-status behavior isn't covered.** Routers switch themselves off
  once a game is started, waiver commands exist only during `getting_waivers`,
  and a wrongly-`False` filter fails silently. Changes to the bot get a manual
  pass: open an issue from the **Bot regression pass** template
  (`.github/ISSUE_TEMPLATE/tgbot-regression-pass.md`) and work the states your
  change can reach. Checks marked **⚠ regression** have broken before.

## Linting & CI

CI (`.github/workflows/test.yml`) runs dependency build, **lint**, and **test**.
Before pushing:

```shell
ruff format . && ruff check --fix . && mypy .
```

Config (line length 99, ruff `select=ALL` with a curated ignore list, mypy
overrides) lives in `pyproject.toml`.

## Environment & tooling

- Python **>=3.14,<3.16**. Package/dependency manager: **uv**.
- Setup: `uv venv && uv sync --group test`.
- Key stack: FastAPI, aiogram 3 + aiogram_dialog, SQLAlchemy 2 (async,
  asyncpg), Alembic, **dishka** (DI), **adaptix** (serialization),
  **dature** (config), pydantic, redis, APScheduler.
- DB migrations: `python -m alembic upgrade head` (DB URL in `alembic.ini`).
- Entry points: `shvatka-tgbot`, `shvatka-api` (see `[project.scripts]`).
- Config: copy `config_dist` → `config` and fill it in.

## Conventions cheat sheet

- Domain DTOs are referenced as `dto.*` from `shvatka.core.models`.
- Line length 99. Match surrounding style; don't reformat untouched code.
- **Write comments and docstrings in English.** Older Russian ones are expected
  and need no translation. User-facing strings (bot replies, report headers)
  stay Russian.
- **Log exceptions with an explicit `exc_info=e`** (`except SomeError as e:` →
  `logger.warning("...", exc_info=e)`) rather than `logger.exception(...)` or
  `exc_info=True`.
- **Log admin/superuser actions with the acting admin's id**, e.g.
  `logger.warning("admin %s accepted merge request %s", admin.id, request.id)`.
- **Serialization is adaptix, and only adaptix.** Take the game `Retort` from DI
  (`FromDishka[Retort]` or a constructor dep) — it carries
  `REQUIRED_GAME_RECIPES`, which teaches adaptix the non-model scenario types.
  Build a `Retort` locally only for a format those recipes don't describe (see
  `infrastructure/crawler/retort.py`), and never at module level.
- Import the model module, not a bag of names: `from shvatka.api.games import
  requests, responses`, then `responses.FullGame`. Models convert with
  `.from_core(...)` / `.to_core(...)`.
- **The config model mirrors `config.yml`**, loaded by a single
  `dature.load(config_source(paths), schema=TheConfig)` per root (`ApiConfig`,
  `TgBotConfig`) — a new section means **one new field**, no loader, no wiring.
  Models are bare `@dataclass`es; don't add a field that isn't in the file
  (`Paths` and anything derived come from DI instead); a value belongs to exactly
  one field (`field_mapping` moves a key, it doesn't copy it); no module-level
  retorts in loaders.
- **In aiogram / aiogram_dialog handlers, take dependencies from DI**
  (`FromDishka[...]` on an `@inject`-decorated handler), including
  `dao: FromDishka[HolderDao]` — not `manager.middleware_data`.
- **Every aiogram_dialog `Window` with a getter needs `preview_data`** (getters
  aren't called in preview mode). Reuse/add fixtures in
  `tgbot/dialogs/preview_data.py`. Every state of a `StatesGroup` needs a window.
  `tests/unit/test_dialogs_preview.py` enforces both.
- **A handler that jumps to another window must declare it in
  `preview_add_transitions`** — a `manager.start(...)` / `switch_to(...)` inside
  `on_click` / `on_success` / `MessageInput` is invisible to the diagram, so add
  `PreviewStart(state)` / `PreviewSwitchTo(state)` (and `Cancel()` when closing
  the dialog is the normal outcome, not for error-only `done()` paths).
  `tests/unit/test_dialogs_transitions.py` fails on an undeclared jump.
  `python -m shvatka.tgbot.dialogs.__init__` writes both the preview page and
  the diagram to `out/` (the diagram needs graphviz).
- **A dialog re-checks the state it was opened for.** A telegram window stays
  clickable forever, so anything captured on start may be false by the time the
  button is pressed. Don't `assert` and don't quietly `done()`: raise
  `DialogOutdated` (`tgbot/dialogs/outdated.py`) — `OutdatedDialogMiddleware`
  answers the user and restarts them in the main menu. Use
  `get_actual_team_player(identity)` / `get_actual_teammate`, or better, resolve
  the state in the getter on every render (see `my_team_getter`). SHEP-0005.
- **Every change to a team goes through `TeamNotifier`.** Joining, leaving,
  handing over the captaincy and renaming all raise a `TeamEvent`
  (`core/views/team.py`); both edges hang behavior off it (chat announcement and
  member retagging in the bot, notification and push on the web). A new kind of
  change means a new event class plus a branch in `BotTeamNotifier` and
  `WebTeamNotifier` — never a silent write to the teams table.
- **Superuser rights resolve through `SuperusersResolver`**
  (`core/interfaces/superusers.py`). `IdentityProvider` derives
  `get_superuser` / `is_superuser` from one `_get_optional_superuser` hook that
  per-edge providers override. Don't re-read `config.superusers` at a new site.
- **A user-facing error points at the documentation.** Set `doc_page` on an
  `SHError` that refuses something a rule explains (a `DocPage` from
  `core/utils/doc_pages.py`), or pass `doc_page=` at the raise site. The edges
  build the link — never a docs URL in `core`, never a hardcoded domain. A new
  `DocPage` needs its `.adoc` to exist (the unit suite checks it), and the web ui
  keys off the **member name**, so renaming a member is a breaking change.
  SHEP-0007.
