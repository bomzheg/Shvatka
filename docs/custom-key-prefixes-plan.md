# Custom key prefixes — design plan

> Status: **planning only, no code yet.** Issue
> [#162](https://github.com/bomzheg/Shvatka/issues/162) — "Кастомные префиксы
> ключей? Надо ли нам оно?"

## 1. Decisions taken

These four were settled with the author before writing this plan:

| # | Question | Decision |
|---|---|---|
| 1 | What owns the prefix? | **The level.** Each `LevelScenario` may carry its own prefix. |
| 2 | Replace or extend `SH`/`СХ`? | **Replace.** In a level with prefix `ZZ`, `SH…` and `СХ…` are no longer keys. |
| 3 | How does the bot recognise a key? | **Union prefilter.** The aiogram filter matches defaults ∪ prefixes of all levels of active games; the exact per-level decision stays in core. |
| 4 | Where is it stored? | **In the scenario** — one optional field, **no `__model_version__` bump** (see §3). |

A level with no prefix set keeps today's behaviour exactly: `("SH", "СХ")`.

## 2. Where key validation lives today

```
core/utils/input_validation.py:7    KEY_PREFIXES = ("SH", "СХ")     ← the single source of truth
core/utils/input_validation.py:9    KEY_REGEXP = ^(?:SH|СХ)[A-Z\dА-ЯЁ]+$
```

Consumed by, in order of how much per-level context each has:

| Call site | Has the level? | Note |
|---|---|---|
| `core/services/key.py:31` — `KeyProcessor.check_key` | not yet, but `submit_key:47` fetches `lvl` | validation currently happens *before* the level is known |
| `core/services/level_testing.py:84` | yes — `suite.level` | easy |
| `core/models/dto/action/keys.py:36` — `BonusKey.__post_init__` | **no** | a value object validating itself against a global |
| `tgbot/filters/is_key.py` | **no** | sync aiogram filter, no DI, no game context |
| `tgbot/dialogs/level_scn/handlers.py:69` — `convert_keys` | the level being edited | author-side input |
| `core/views/texts.py:9` — `INVALID_KEY_ERROR` | no | f-string built at *import* time from the constant |
| `core/utils/exceptions.py:366` — `InvalidKey.notify_user` | no | hardcodes "начинается не с SH/СХ" |

Note that `KeyWinCondition.keys` / `KeyEffectsCondition.keys` are **not**
validated at all today — only `BonusKey` checks itself. That asymmetry is what
makes §4.2 straightforward.

## 3. Storage — why no model version bump

`LevelScenario` is persisted as **JSONB** (`ScenarioField` in
`infrastructure/db/models/level.py`), dumped/loaded by an adaptix `Retort`.
So:

- **No alembic migration is needed.** The field lives inside the existing
  `levels.scenario` column. "Scenario + DB" is one and the same place here.
- **No `__model_version__` bump is needed.** The field is optional with a
  default, so every existing v1 scenario — in the DB and in every exported
  `.yml`/zip — loads unchanged. A version bump buys nothing: there is one
  reader, and it is this codebase. The only scenario a bump would guard is an
  *older deployment* importing a *newer* export, and there the graceful
  outcome (prefix silently ignored, defaults apply) is what a bump would
  turn into a hard parse error.
- One adaptix detail: the retort dumps every field by default, which would
  write `keys_prefix: null` into every stored scenario and every export. Add an
  `omit_default()` recipe for the field in `common/factory.py` so untouched
  scenarios round-trip byte-identically.

```python
@dataclass
class LevelScenario:
    id: str
    time_hints: HintsList
    conditions: Conditions
    __model_version__: Literal[1]
    keys_prefix: str | None = None      # None → DEFAULT_KEY_PREFIXES
```

## 4. Core changes

### 4.1 `input_validation.py` — make prefixes a parameter

```python
DEFAULT_KEY_PREFIXES = ("SH", "СХ")
KEY_PREFIX_REGEXP = re.compile(r"^[A-ZА-ЯЁ]{1,10}$")   # see open question B

def build_key_regexp(prefixes: Sequence[str]) -> re.Pattern: ...
def normalize_key(key_expectant: str, prefixes=DEFAULT_KEY_PREFIXES) -> str | None: ...
def is_key_valid(key_expectant: str, prefixes=DEFAULT_KEY_PREFIXES) -> bool: ...
def is_multiple_keys_normal(keys, prefixes=DEFAULT_KEY_PREFIXES) -> bool: ...
def validate_key_prefix(prefix: str) -> str | None: ...
```

Keeping `DEFAULT_KEY_PREFIXES` as the default argument means every call site
that has no level context keeps compiling and keeps behaving as today; each one
is then migrated deliberately. `build_key_regexp` should be `lru_cache`d — it is
called per typed key.

`KEY_PREFIXES` stays as a deprecated alias for one release so nothing outside
this list breaks silently.

### 4.2 Where authored keys get validated

`BonusKey.__post_init__` cannot know its level's prefix, so it stops being the
place where prefix correctness is decided:

- `BonusKey.__post_init__` → checks only the **body** charset (`[A-ZА-ЯЁ\d]+`,
  non-empty) and the bonus range. It no longer imports `is_key_valid`.
- `LevelScenario.__post_init__` → gains a check that **every** key in
  `self.conditions.get_keys()` matches the level's prefixes. This is strictly
  more coverage than today, because win/effects keys were never validated.

This is the one behaviour change that can reject scenarios which currently
load. Worth a scan of production scenarios before merging — if any existing
level has a key that fails the new check, the check must degrade to a warning
for `keys_prefix is None` levels.

Add to `LevelScenario`:

```python
def get_key_prefixes(self) -> tuple[str, ...]:
    return (self.keys_prefix,) if self.keys_prefix else DEFAULT_KEY_PREFIXES
```

### 4.3 Play path

`KeyProcessor.check_key` (`core/services/key.py:31`) validates before it knows
the level. The check moves into `submit_key`, right after `lvl` is fetched
(line 47, already inside `locker.lock_team`):

```python
if not is_key_valid(key, lvl.scenario.get_key_prefixes()):
    raise exceptions.InvalidKey(key=key, team=team, player=player, game=game,
                                expected_prefixes=lvl.scenario.get_key_prefixes())
```

`check_key` becomes a thin delegate. `InvalidKey` gains `expected_prefixes` so
the view can name the right prefix instead of the hardcoded "SH/СХ".

`level_testing.py:84` does the same with `suite.level.scenario.get_key_prefixes()`.

### 4.4 Texts

`INVALID_KEY_ERROR` (`core/views/texts.py:9`) and `InvalidKey.notify_user` are
built once at import from the global constant. Both become functions of the
expected prefixes, rendered per message.

## 5. Bot changes

### 5.1 The prefilter

`tgbot/filters/is_key.py` is a plain sync function with no DI, registered in
`handlers/game/play.py:35` and as a `MessageInput` filter in the level-testing
dialog (`dialogs/level_manage/dialogs.py:141`). Per decision #3 it becomes a
*candidate extractor*, not the authority:

- New core interface `ActiveKeyPrefixesProvider` with an infra implementation
  returning `DEFAULT_KEY_PREFIXES ∪ {custom prefixes of levels of active games}`.
- The implementation queries `levels.scenario ->> 'keys_prefix'` joined to
  active games — a handful of rows, and `CurrentGameProvider` already
  establishes the "one active game" pattern. Cached per request, plus a short
  process-level TTL since it is hit on every text message in team chats.
- `is_key` becomes a dishka-injected class-based filter that matches against
  that union and passes the raw candidate down.

Consequence of "union prefilter + replace semantics": in a `ZZ` level, a
message `SH123` still *passes* the filter (SH is a default) and is then
rejected by core. That is intentional — it is what lets the player be told
"keys in this game start with ZZ" instead of being ignored. See open question A
for whether that rejection is logged as a wrong key.

### 5.2 Author-side editing

`convert_keys` (`dialogs/level_scn/handlers.py:69`) validates typed keys via
`is_multiple_keys_normal` against the globals. It must validate against the
prefix of the level being edited, which imposes an ordering constraint on the
dialog: **the prefix must be settable before the keys are entered.** That means
a new window/state in `LevelKeysSG`/level-edit flow plus a place to display and
change the current prefix. See open question C for whether this ships in v1.

## 6. API / UI

The API serialises the scenario dataclasses directly through adaptix, so
`keys_prefix` appears in game/level payloads with no schema work. `shvatka-ui`
needs a change only if the prefix should be *shown* (scenario view) or *edited*
in the web editor — worth confirming, but it is not on the critical path.

## 7. Tests

- `tests/unit/input_validation/test_key_validation.py` — parametrise over
  prefixes; add cases where `SH…` is invalid under a custom prefix.
- `tests/fixtures/resources/valid_keys.txt` gets a custom-prefix sibling.
- A scenario fixture with `keys_prefix` set on one level and not on another,
  proving both round-trip and that the field is omitted when unset.
- Unit: `LevelScenario.__post_init__` rejects keys that do not match its prefix.
- Integration (`tests/integration/test_game_play.py`): in a custom-prefix
  level, a `SH…` key is not accepted, and the custom-prefix key levels up.
- Level testing: same via `test_level_tesing.py`.

## 8. Suggested order of work

1. `input_validation.py` — parametrised API + `validate_key_prefix`, defaults
   unchanged. Pure addition, no behaviour change. *(tests)*
2. `LevelScenario.keys_prefix` + `get_key_prefixes()` + `__post_init__`
   validation + `omit_default` recipe. *(tests, scenario round-trip)*
3. Move `BonusKey`'s prefix check up to the level. *(tests)*
4. Play path + level testing + `InvalidKey.expected_prefixes` + dynamic texts.
   *(integration tests)*
5. `ActiveKeyPrefixesProvider` + injected `is_key` filter.
6. Author UI in the bot dialog (if in scope — open question C).
7. Docs: `docs/modules/ROOT/pages/author/level-concept.adoc:33` currently states
   the SH/СХ rule as absolute.

Steps 1–4 are independently shippable and leave the product working with
prefixes settable via scenario upload / API only; 5 is what makes a custom
prefix usable in a real game over Telegram.

## 9. Open questions

**A. What happens to a well-formed key with the wrong prefix during play?**
`SH123` typed in a `ZZ` level. Either (a) invalid key — not written to the key
log, player gets the "keys here start with ZZ" hint, or (b) wrong key — logged
and counted in stats like any other miss. Recommendation: **(a)**, since
"replace" semantics say `SH123` is not a key in this game at all; (b) would
pollute per-team wrong-key statistics with what is really a typo about
formatting.

**B. Prefix format constraints.** Recommendation: `[A-ZА-ЯЁ]{1,10}`, letters
only, normalised to uppercase. Digits excluded on purpose — a prefix ending in
a digit makes the prefix/body boundary ambiguous. Open: is a length cap of 10
right, should mixed latin+cyrillic in one prefix be allowed (`SХ` with a
cyrillic Х is a nasty homoglyph trap), and should prefixes be reserved/unique
across games?

**C. Per-level is a lot of typing.** A 20-level game with a custom prefix means
setting it 20 times. Should there be a game-level default that levels inherit
and may override? That is a small addition now (a field on the game + fallback
in `get_key_prefixes()`) and an awkward retrofit later.

**D. Scope of v1.** Is scenario-upload/API enough to close #162, or does the
bot's level editor need the prefix UI (step 6) before this is "done"?
