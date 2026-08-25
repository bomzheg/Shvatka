# AGENTS.md

Guidance for AI agents (and humans) working in the **Shvatka** codebase — an
engine for the night search game *Encounter/Shvatka*, exposing a REST API and a
Telegram bot.

## TL;DR for agents

- **Write new code as `Interactor` classes** (callable, DI-wired), not as free
  service functions. The project is mid-migration — see below.
- **Don't add new to HolderDAO properties** - prefer DI
- **Don't add to middleware data new keys** - prefer DI
- **Don't rewrite existing code** unless the task requires it. Leave working
  service functions alone; only new functionality should adopt the new style.
- **Capture review feedback as rules.** When you act on a code-review comment,
  decide whether it states a one-off fix or a reusable project convention. If
  it's a convention, write it down in this file so it's not re-litigated on the
  next PR.
- **Design decisions live in SHEPs** (`docs/modules/shep/`) — one page per
  non-trivial change, in the Antora docs. Read the relevant one before touching
  the subsystem it describes, and update its status section when a phase lands.
  This file keeps the *rules*; a SHEP keeps the *decision and why*.
- **Prefer `IdentityProvider` and `CurrentGameProvider`** for resolving the
  current user/player/team/game everywhere except the DAO layer.
- **New API endpoints → integration tests.** New **domain** classes/methods →
  **unit tests.**
- **Lint and tests run in CI.** You may push to the branch and read the CI
  status instead of running the full (slow, testcontainer-backed) suite
  locally. Running `pytest tests/unit` locally for fast feedback is fine.

## Project layout

```
shvatka/
  core/            # Pure domain + application logic. No framework imports.
    models/        # DTOs (dto.*), enums, action models
    interfaces/    # Protocols: dal/* (DAO contracts), identity, current_game, ...
    services/      # OLD style: free service functions (e.g. game.py, key.py)
    games/         # interactors.py, adapters.py, game_play.py, dto.py
    scenario/      # interactors.py ...
    waiver/        # interactors.py, services.py, adapters.py
    rules/         # pure business rules / checks
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
the Interactor style.

### Old style (don't add more of these; don't gratuitously refactor them)

```python
# shvatka/core/services/game.py
async def upsert_game(
    raw_scn: scn.RawGameScenario,
    author: dto.Player,
    dao: GameUpserter,
    ...
) -> dto.FullGame:
    ...
```

### New style — write this

An Interactor is a class whose dependencies (DAO adapters, providers,
sub-processors) are injected via `__init__`, and whose `__call__` runs the use
case. Two equivalent forms are used; pick whichever fits:

```python
# shvatka/core/games/interactors.py  — plain class
class GameStatReaderInteractor:
    def __init__(self, dao: GameStatReader):
        self.dao = dao

    async def __call__(self, game_id: int, identity: IdentityProvider) -> dto.GameStatWithHints:
        player = await identity.get_required_player()
        game = await self.dao.get_by_id(game_id)
        return await get_game_stat_with_hints(game, player, self.dao)


# or as a frozen dataclass when there are several deps
@dataclass(kw_only=True, slots=True, frozen=True)
class GamePlayReaderInteractor:
    current_game: CurrentGameProvider
    game_play_dao: GamePlayDao

    async def __call__(self, identity: IdentityProvider) -> CurrentHintsAndKeys:
        ...
```

Conventions for Interactors:

- Live next to their domain in `core/<area>/interactors.py`.
- Depend on **Protocols**, not concrete implementations. DAO contracts are
  "adapters" — compose the narrow `core/interfaces/dal/*` protocols into an
  area-specific Protocol in `core/<area>/adapters.py` (see
  `shvatka/core/games/adapters.py`).
- Take `identity: IdentityProvider` (and `current_game` via a constructor dep)
  instead of receiving resolved `player`/`team`/`game` arguments.
- Reuse existing service functions internally where helpful — Interactors often
  wrap them during the migration. That's fine.

### Wiring with dishka

Register interactors and their adapters in `shvatka/infrastructure/di/`
(`interactors.py` and friends). Most interactors register with a bare
`provide(SomeInteractor)`; adapters map a concrete DAO impl onto its Protocol:

```python
class GamePlayProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_state(self, dao: HolderDao) -> GameStatReader:
        return GameStatReaderImpl(dao)

    get_game_state_interactor = provide(GameStatReaderInteractor)
```

Consume them at the edges via `FromDishka[...]`:

```python
# shvatka/api/games/routes.py
@inject
async def get_game_stat(
    interactor: FromDishka[GameStatReaderInteractor],
    identity: FromDishka[ApiIdentityProvider],
    id_: Annotated[int, Path(alias="id")],
) -> responses.GameStat:
    stat = await interactor(identity=identity, game_id=id_)
    return responses.GameStat.from_core(stat)
```

**Showing something in telegram stays in `tgbot`.** Never move a bot view or
its tools into the shared providers to reach them from the api — an interactor
that needs the chat to change takes a **view Protocol** from `core/views/` and
each container binds its own implementation: the bot one in
`tgbot/main_factory.py`, a web one in `api/app/dependencies/`, a no-op in
`infrastructure/di/infra.py`. (Where an event fits better than a call, submit
one to the `Bus` instead.) That way the same use case reaches the channel from
the site, without `HintSender` leaking into every container.

**What a view showed is the view's to remember**, not the domain's. Postgres is
fine for it — what must not happen is a chat or message id reaching a core
entity. Store it in its own column (or its own table), read and write it
through dao methods that return plain values, and keep it out of `to_dto`:
`action_requests.bot_messages` and `games.release_post` both work that way,
and `MessagePinner` keeps its ids in redis for the same reason.

A dependency that genuinely belongs to both edges — a dao, a policy, an
interactor — does go in the shared providers (`infrastructure/di/`, listed by
`get_providers()`). The integration tests build their container by hand in
`tests/integration/conftest.py`, so a new shared provider has to be added
there as well.

## Use the providers (`IdentityProvider` / `CurrentGameProvider`)

Resolve "who is acting" and "what game is active" through these Protocols as
much as possible — **everywhere except the DAO layer**.

- `IdentityProvider` (`core/interfaces/identity.py`) — `get_user`,
  `get_player`, `get_team`, `get_chat`, `get_full_team_player`, plus
  `get_required_*` variants that raise instead of returning `None`.
- `CurrentGameProvider` (`core/interfaces/current_game.py`) — `get_game` /
  `get_full_game` and their `get_required_*` variants.

Implementations are per-edge and cache within a request:

- API: `ApiIdentityProvider` in `shvatka/api/app/dependencies/auth.py`.
- Bot: `TgBotIdentityProvider` in `shvatka/tgbot/services/identity.py`.
- Game: `CurrentGameProviderImpl` in `shvatka/core/services/current_game.py`.

So: an Interactor takes `identity: IdentityProvider` as a `__call__` arg (or a
`current_game: CurrentGameProvider` constructor dep) and calls e.g.
`await identity.get_required_player()` — it should not receive a pre-resolved
player/team, and it should not re-implement auth. The DAO layer is the
exception: DAOs take concrete `dto.Player`/`dto.Team`/etc.

## Background work goes through the nursery

**Never start a detached task yourself.** `asyncio.create_task` and
`asyncio.ensure_future` are banned by lint (`TID251`); the single caller is
`AsyncioNursery` in `shvatka/infrastructure/nursery.py`. Everything that has to
outlive the request that asked for it — publishing a scenario, uploading to the
forum, sending a pile of hints — is spawned on the app-scoped `Nursery`
(`core/interfaces/nursery.py`), taken as `FromDishka[Nursery]`.

A task is just an async function in `shvatka/tgbot/tasks.py` — no class, no
params object, nothing to register. Plain parameters are the data of the run;
`FromDishka[...]` parameters are injected, same as in the scheduler wrappers
(`infrastructure/scheduler/wrappers.py`), which use the same mechanism:

```python
async def publish_scenario_to_forum(
    game: dto.FullGame, username: str, password: str, chat_id: int,
    bot: FromDishka[Bot],
) -> None: ...

nursery.spawn(publish_scenario_to_forum, game=game, username=..., password=..., chat_id=...)
```

Why it matters: the nursery opens a **fresh REQUEST scope** per task and
resolves the injected parameters there, so the task acquires and finalizes its
own db session (and views, clients, …) instead of borrowing the handler's,
which is closed the moment the handler returns. The nursery also keeps a strong
reference until the task ends, logs failures instead of dropping them, and
cancels what is still running when the app shuts down.

One rule for writing one: **entities travel as arguments, resources come from
DI.** Domain DTOs are plain dataclasses detached from any session, so handing a
loaded game or level to a task is free — and it keeps the authorization the
handler already did (the load *is* the check) instead of repeating it. What
must never cross the boundary is anything tied to the caller's scope: a dao, a
session, a `HintSender`. Those the task takes from DI, so its own scope owns
them.

`asyncio.TaskGroup` is *not* banned — it is the right tool when you await the
group. It is the wrong tool for the nursery: its exit waits for every child
(shutdown would block on a half-hour scenario publish) and a raising child
cancels its siblings, which is exactly what independent background jobs must
not do.

### Showing the game is decided as data, and shown after the commit

An interactor never shows anything while it works. It decides *what* to show,
appends it to a plain list as `ViewTask` values (`core/views/game.py`), commits,
and only then hands the list over:

```python
tasks = ShowTasks(view=self.view_(new_key, input_container))
tasks.extend(await self.process_level_up(...))
await self.dao.commit()
await self.show(tasks)
```

Before the commit it is a list and nothing else, so **a transaction that does
not land shows nothing** — that is the point of the shape, not an optimisation.
There is no finalizer that flushes what you forgot: showing is a line you write
after the commit. See
`docs/modules/shep/pages/shep-0009-key-submission-latency.adoc`; durable
delivery, if a lost message ever turns out to matter, is planned in
`docs/modules/shep/pages/shep-0010-message-outbox.adoc`.

`GameView` has one method, `show(tasks)`. Adding something to show is a new
`ViewTask` plus a branch in each view's router — never a new method on the
protocol. `AnyViewTask` is a union, so a view that forgets one fails `mypy`.

`process_level_up` and its two halves keep doing their reads and writes — they
just return the tasks instead of showing them. When you add something to a level
up, append a task; do not reach for a view.

Order is a promise about **a chat, not the game**: `group_by_team` splits a
batch per team and the views show the groups at once. A game starting must
reach the twelfth team as fast as the first, so never make a view walk a batch
in one sequence.

Rules that follow when you add a view task:

- A task carries **domain dtos only** (an aiogram `Message` inside an
  `InputContainer` is fine — it is detached too). Never a dao, a session or a
  sender: it is rendered later, in a scope of its own.
- Anything the caller needs back belongs in the returned list, not in a
  container the view writes into. `CheckKeyInteractor` returns its view tasks
  and the api builds `InsertedKey` from them; that is why `WebInput` is gone.
- A task may be **rendered more than once**: a failed delivery is retried whole,
  so rendering one task can resend messages that already arrived. A resent
  puzzle is acceptable; a task that *counts* something is not.
- Keep rendering short. Shutdown gives running jobs `drain_timeout` before
  cancelling them (`AsyncioNursery.close`); minutes-long work is still cancelled
  on restart.

`ComplexView.show` hands the whole list to the nursery as one job, so the
messages of one request keep their order. Between concurrent requests nothing is
promised, and never was.

One file is exempt from the ban: `tgbot/utils/fastapi_webhook.py` is a
portable copy of aiogram's webhook handler, meant to be pasted into another
bot as-is. It must not import from `shvatka`, so it keeps managing its own
background updates. Leave it alone — if you need to touch it, keep it
self-contained and close to upstream.

## DAO layer

- **Writes belong to the table's own DAO.** A plain `core/.../rdb/*.py` DAO may
  run complex `SELECT`s with joins rooted at its own entity, but
  `INSERT`/`UPDATE`/`DELETE` for a table must live in that table's DAO. Need a
  new table? Add a new DAO for it (e.g. `LevelFileDao` for `level_files`,
  `GameFileDao` for `game_files`); each DAO is parametrised with exactly one
  model — don't make one DAO write to several models.
- **Orchestration is a use-case action, not a DAO action.** When an operation
  spans tables (resolve ids in one table, then write links in another), the DAO
  only *provides* the per-table methods; the use case (a service function /
  Interactor) decides *when* and in what order to call them. A `dao/complex/*`
  impl may exist to expose those methods behind one Protocol, but it should not
  itself drive the sequence.
- **At most one DAO per interactor.** Don't inject several DAOs into an
  interactor/service. Compose what it needs behind a single Protocol and a
  single `dao/complex/*` adapter, and pass that one adapter.
- **Generic SQLAlchemy by default; dialect-specific when justified.** Prefer
  creating a model and adding it to the session (or generic `select`/`delete`).
  Dialect-specific helpers (e.g. `postgresql.insert(...).on_conflict_do_nothing()`)
  are fine when they make a query meaningfully better or faster — just don't
  reach for them without that justification.

## API layout (subdomain packages)

`shvatka/api/` separates **what the API is about** (subdomains) from **how the
app is wired** (`app/`). Each subdomain is a package holding its own endpoints
and the models only it speaks:

```
shvatka/api/
  __main__.py        # entrypoints stay at the top
  main_factory.py    #   create_app / get_paths
  password_hash.py   #   shvatka-password script
  app/               # framework plumbing — nothing subdomain-specific
    router.py        #   aggregates every subdomain router; called by main_factory
    error_handler.py #   SHError -> HTTP response
    config/          #   ApiConfig models + parsers
    dependencies/    #   dishka providers, ApiIdentityProvider, AuthProperties
    middlewares/     #   logging, CORS
    utils/           #   cookie auth, web views/notifiers, push sender
  shared/            # models used by more than one subdomain
    responses.py     #   Page, Items, Player, Team, Game, TgUser, ForumUser, EmailAccount
    requests.py      #   MergeRequest, TimelineItem
  auth/              # routes.py + requests.py + responses.py
  players/           # /users (players in core and db)
  teams/
  games/             # game cards, play, orgs
  waivers/
  files/             # /cdn — game file upload/download/rename
  notifications/
  action_requests/   # /requests — invites and join requests
  search/
  push/
  admin/             # /admin panel
  version/
```

Rules:

- A subdomain package contains `routes.py` (with `setup() -> APIRouter`) plus
  `requests.py` / `responses.py` as needed. Register the router in
  `shvatka/api/app/router.py`.
- `app/` holds only what every subdomain shares — config, DI, middlewares,
  framework helpers. Endpoints and their models never go there; if something in
  `app/` knows about one subdomain, it belongs in that subdomain.
- A model belongs in `shared/` only when **two or more** subdomains use it.
  Anything one subdomain owns stays in that subdomain, even if it looks generic.
- Cross-subdomain reuse is fine and explicit — import
  `from shvatka.api.waivers import responses as waivers_responses` rather than
  copying the model or promoting it to `shared/`.

## Testing

Framework: **pytest** + `pytest-asyncio` (mark async tests with
`@pytest.mark.asyncio`). Integration tests use **testcontainers** (real
Postgres) and **httpx** `AsyncClient`.

Rules for new work:

- **New API endpoint or behavior → integration test** in
  `tests/integration/api_full/`. Drive the real app through the `client`
  fixture; authenticate by creating a token (`auth.create_user_token(...)`) and
  passing it as a cookie. See `tests/integration/api_full/test_game.py` for the
  pattern (set up data via `dao`, `await dao.commit()`, hit the route, assert on
  the response).
- **New domain class/method → unit test** in `tests/unit/` (e.g.
  `tests/unit/domain/`, `tests/unit/services/`). Unit tests are pure/fast and do
  not touch the DB.
- **Assert through `check_dao`, not the acting `dao`.** Integration tests get a
  separate `check_dao` (its own session) for reading back state — use it for
  assertions so you observe committed data, and keep `dao` for the action.

### The test container is the app container plus overrides

`tests/fixtures/di.py` builds the integration container from
`get_root_app_providers(...)` — the very list `create_root_app` runs on — and
only then adds the test doubles. Don't copy provider lists into tests: a new app
provider must reach the tests without touching `tests/`.

Test doubles live in `get_test_override_providers()` and go **last**: dishka
rejects `override=True` for something nobody provided yet.

- Replacing an app dependency → `@provide(override=True)` **in the same scope**
  as the factory being replaced. A different scope leaves the original factory
  alive in its own registry and it wins there — the override silently does
  nothing.
- A double that's only passed to services by hand (`GameLogWriterMock`,
  `MemoryFileStorage`) is provided under its own concrete type, without
  `override=True`, so container-resolved code keeps using the real
  implementation.
- The container is built with `STRICT_VALIDATION`, so an override that overrides
  nothing (or a shadowed factory) fails the build instead of quietly changing
  behavior. `tests/unit/test_di.py` builds every container (api, bot, root,
  tests) and is the fast check that DI still holds together.

Run locally:

```shell
pytest tests            # everything (needs Docker for testcontainers)
pytest tests/unit       # fast unit-only loop, no DB
```

### Coverage

`fail_under` in `[tool.coverage.report]` is the floor, and coverage itself
enforces it — the CI `pytest --cov` step goes red below it. `branch = true`
means the number counts branches next to statements, so one threshold guards
both. Raise it as the number grows; don't lower it to turn a build green.
Nothing enforces it locally unless you ask for coverage: the fast loop
(`pytest tests/unit`) passes no `--cov`, so it never reports and never fails.

`[tool.coverage.run] omit` in `pyproject.toml` drops what tests are never going
to reach: the bot layer, alembic migrations, and **one-shot scripts** — the
forum crawler (parsers, loader, uploader), the 0→1 scenario migration, and the
maintenance scripts over prod data. New code of that kind belongs in the omit
list with a comment saying why; everything else stays measured.

### What the suite can't see

The bot behaves differently in each game status: the ordinary routers switch
themselves off once a game is **started**, waiver commands exist only during
**getting_waivers**, editing closes after that, results appear only when it is
**finished**. Nothing in the automated suite drives a real update through those
states, and the usual failure is silent — a filter that wrongly answers `False`
raises nothing, it just makes a command stop responding.

So changes to the bot get a manual pass against a real one: open an issue from
the **Bot regression pass** template
(`.github/ISSUE_TEMPLATE/tgbot-regression-pass.md`) and work through it there,
where the checkboxes actually tick. It is grouped by game status; run the states
your change can reach and delete the rest. Checks marked **⚠ regression** are
places that have broken before — read those rather than skim them.

## Linting & CI

CI (`.github/workflows/test.yml`) runs three gates on PRs to `master` and on
push to the dev branch: dependency build, **lint**, and **test**. The lint job
runs:

```shell
ruff format --check .
ruff check .
mypy .
```

To fix locally before pushing:

```shell
ruff format . && ruff check --fix . && mypy .
```

You may rely on CI for the authoritative result: push to the working branch and
read the CI status rather than reproducing the full testcontainer suite
locally. Still run `ruff format`/`ruff check` and `pytest tests/unit` locally
when practical to avoid round-trips. Config (line length 99, ruff `select=ALL`
with a curated ignore list, mypy overrides) lives in `pyproject.toml`.

## Environment & tooling

- Python **>=3.13,<3.15**. Package/dependency manager: **uv**.
- Setup: `uv venv && uv sync --group test`.
- Key stack: FastAPI, aiogram 3 + aiogram_dialog, SQLAlchemy 2 (async,
  asyncpg), Alembic, **dishka** (DI), **adaptix** (serialization),
  **dature** (config), pydantic, redis, APScheduler.
- DB migrations: `python -m alembic upgrade head` (DB URL in `alembic.ini`).
- Entry points: `shvatka-tgbot`, `shvatka-api` (see `[project.scripts]`).
- Config: copy `config_dist` → `config` and fill it in.

## Conventions cheat sheet

- Domain DTOs are referenced as `dto.*` from `shvatka.core.models`.
- **Serialization is adaptix, and only adaptix.** `dataclass_factory` is gone —
  don't reintroduce it. Take the game `Retort` from DI (`FromDishka[Retort]` or
  a constructor dep); it carries `REQUIRED_GAME_RECIPES`, which is what teaches
  adaptix the non-model scenario types (`HintsList`, `Conditions`). Build a
  `Retort` locally only for a format the game recipes don't describe — see
  `infrastructure/crawler/retort.py` — and never at module level.
- API endpoints and their models live together in `shvatka/api/<subdomain>/`
  (see the API layout section). Models convert with `.from_core(...)` /
  `.to_core(...)` helpers.
- Import the model module, not a bag of names: `from shvatka.api.games import
  requests, responses`, then `responses.FullGame` — so the reader sees which
  subdomain a model came from.
- Keep `core` framework-free; put framework glue in `api`, `tgbot`,
  `infrastructure`.
- **The config model mirrors `config.yml`, and `dature` loads the whole file in
  one call.** `ApiConfig` and `TgBotConfig` are the two roots; each is loaded by
  a single `dature.load(config_source(paths), schema=TheConfig)`, so a new
  section in the file means **one new field** on the model and nothing else — no
  loader function, no prefix, no wiring. Field names map to kebab-case keys
  automatically, nested sections are nested dataclasses (`api:` → `ApiSection`),
  and an absent optional section falls back to the field's default. Keep it that
  way:
  - models are bare `@dataclass`es — never decorated with `@dature.load`, never
    carrying loading metadata;
  - don't add a field that isn't in the file. `Paths` is the input that *locates*
    `config.yml`, so it is not part of `Config` — take it from DI. Anything
    derived (e.g. `TgClientConfig` from the bot token) is built in a dishka
    provider, not stored in the config tree;
  - a value belongs to exactly one field. `field_mapping` **moves** a source key
    rather than copying it, so two fields cannot read the same key — superusers
    live on `Config.superusers` alone;
  - keep loaders free of module-level retorts/factories — build the source per
    call.
- Line length 99. Match surrounding style; don't reformat untouched code.
- **Log exceptions with an explicit `exc_info=e`.** Capture the exception
  (`except SomeError as e:`) and pass it to the logging call
  (`logger.warning("...", exc_info=e)` / `logger.error("...", exc_info=e)`)
  rather than using `logger.exception(...)` or `exc_info=True`. Being explicit
  keeps the logged exception independent of the active `except` block and lets
  you choose the log level.
- **Write comments and docstrings in English.** Some older ones are in Russian —
  that's expected, and there's no need to translate them when you touch a file —
  but anything you add should be English. User-facing strings (bot replies,
  Excel report headers, etc.) stay Russian.
- **Every aiogram_dialog `Window` with a getter needs `preview_data`.** Getters
  are not called in preview mode, so a window without it renders against an
  empty dict. Reuse the fixtures in `shvatka/tgbot/dialogs/preview_data.py` and
  add new ones there. `tests/unit/test_dialogs_preview.py` renders every window
  and fails when one is missing; `python -m shvatka.tgbot.dialogs.__init__`
  writes the page to `out/shvatka-dialogs-preview.html`. Each state of a
  `StatesGroup` must have a window too — the same test asserts it.
- **A handler that jumps to another window must declare it in
  `preview_add_transitions`.** The transitions diagram is built from the
  `Start` / `SwitchTo` / `Next` / `Back` / `Cancel` widgets it can see in a
  window; a `manager.start(...)` / `manager.switch_to(...)` inside an
  `on_click` / `on_success` / `MessageInput` handler is invisible to it, so
  add `PreviewStart(state)` / `PreviewSwitchTo(state)` (and `Cancel()` when the
  handler closes the dialog as its normal outcome — not for error-only
  `done()` paths). `tests/unit/test_dialogs_transitions.py` fails on an
  undeclared jump; `python -m shvatka.tgbot.dialogs.__init__` writes the
  diagram to `out/shvatka-dialogs.png` (needs graphviz).
- **A dialog re-checks the state it was opened for, and says so when it's gone.**
  A telegram window stays clickable forever, so anything a dialog captured on
  start (a team id in `dialog_data`, a permission a button was shown for) may be
  false by the time the button is pressed. Don't `assert` it and don't quietly
  `done()`: raise `DialogOutdated` (`tgbot/dialogs/outdated.py`) from the getter
  or the handler — `OutdatedDialogMiddleware` answers the user and restarts them
  in the main menu. For the acting player's team use
  `get_actual_team_player(identity)` (it translates `PlayerNotInTeam` for you
  and carries `.team`), and `get_actual_teammate` for anybody else. Better
  still, don't cache the state: resolve it in the getter on every render, the
  way `my_team_getter` does. See SHEP-0005.
- **In aiogram / aiogram_dialog handlers, take dependencies from DI**
  (`FromDishka[...]` on an `@inject`-decorated handler) rather than reaching
  into `manager.middleware_data` / event middleware data. That includes
  `dao: FromDishka[HolderDao]`.
- **Superuser rights resolve through `SuperusersResolver`**
  (`core/interfaces/superusers.py`) — the single source for who the configured
  admins are. `IdentityProvider` derives `get_superuser` / `is_superuser` from
  one `_get_optional_superuser` hook; per-edge providers override only that hook.
  Don't re-read `config.superusers` at a new call site.
- **A user-facing error points at the documentation.** When you add an `SHError`
  that refuses something a rule explains, set `doc_page` on it (a `DocPage` from
  `core/utils/doc_pages.py`), or pass `doc_page=` at the raise site when only
  that one place means that page. The edges turn it into a link on their own —
  the bot appends it to the error message, the API returns it as `docUrl` — so
  never build a docs URL in `core`, and never hardcode the docs domain: it comes
  from `docs:` in `config.yml` through `DocsUrlFactory`. A new `DocPage` needs
  the `.adoc` to exist; the unit suite checks that. The web ui links its own
  hints to the same pages and asks `GET /docs/pages` for their urls, keyed by
  the `DocPage` **member name** — so renaming a page is safe, but renaming a
  member is not. See SHEP-0007.
- **Log admin/superuser actions with the acting admin's id** so there's an
  audit trail, e.g. `logger.warning("admin %s accepted merge request %s", admin.id, request.id)`.
</content>
</invoke>
