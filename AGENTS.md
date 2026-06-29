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
  api/             # FastAPI app: routes/, dependencies/, models/ (req + responses)
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
# shvatka/api/routes/game.py
@inject
async def get_game_stat(
    interactor: FromDishka[GameStatReaderInteractor],
    identity: FromDishka[ApiIdentityProvider],
    id_: Annotated[int, Path(alias="id")],
) -> responses.GameStat:
    stat = await interactor(identity=identity, game_id=id_)
    return responses.GameStat.from_core(stat)
```

## Use the providers (`IdentityProvider` / `CurrentGameProvider`)

Resolve "who is acting" and "what game is active" through these Protocols as
much as possible — **everywhere except the DAO layer**.

- `IdentityProvider` (`core/interfaces/identity.py`) — `get_user`,
  `get_player`, `get_team`, `get_chat`, `get_full_team_player`, plus
  `get_required_*` variants that raise instead of returning `None`.
- `CurrentGameProvider` (`core/interfaces/current_game.py`) — `get_game` /
  `get_full_game` and their `get_required_*` variants.

Implementations are per-edge and cache within a request:

- API: `ApiIdentityProvider` in `shvatka/api/dependencies/auth.py`.
- Bot: `TgBotIdentityProvider` in `shvatka/tgbot/services/identity.py`.
- Game: `CurrentGameProviderImpl` in `shvatka/core/services/current_game.py`.

So: an Interactor takes `identity: IdentityProvider` as a `__call__` arg (or a
`current_game: CurrentGameProvider` constructor dep) and calls e.g.
`await identity.get_required_player()` — it should not receive a pre-resolved
player/team, and it should not re-implement auth. The DAO layer is the
exception: DAOs take concrete `dto.Player`/`dto.Team`/etc.

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

Run locally:

```shell
pytest tests            # everything (needs Docker for testcontainers)
pytest tests/unit       # fast unit-only loop, no DB
```

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
  asyncpg), Alembic, **dishka** (DI), adaptix/dataclass_factory (serialization),
  pydantic, redis, APScheduler.
- DB migrations: `python -m alembic upgrade head` (DB URL in `alembic.ini`).
- Entry points: `shvatka-tgbot`, `shvatka-api` (see `[project.scripts]`).
- Config: copy `config_dist` → `config` and fill it in.

## Conventions cheat sheet

- Domain DTOs are referenced as `dto.*` from `shvatka.core.models`.
- API response/request models live in `shvatka/api/models/` and convert with
  `.from_core(...)` / `.to_core(...)` helpers.
- Keep `core` framework-free; put framework glue in `api`, `tgbot`,
  `infrastructure`.
- Line length 99. Match surrounding style; don't reformat untouched code.
- Some docstrings/comments are in Russian — that's expected; keep the existing
  language of the file you're editing.
</content>
</invoke>
