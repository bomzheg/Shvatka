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
| 5 | Wrong prefix during play? | **Just a wrong key** — logged and counted like any other miss (§10 A). |
| 6 | Prefix format | **Letters only, one alphabet per prefix** — no digits, no latin/cyrillic mixing (§10 B). |
| 7 | A game-level default? | **No.** Per level only; bulk-setting is a web-editor convenience (§10 C). |
| 8 | Delivery | **Subtasks under #162**, not one change (§11). |

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
- Look at what a bump costs in this repository. `core/migration_utils/` holds
  the 0 → 1 upgrade: an entire parallel `models_0` package (`level.py`,
  `game.py`, `time_hint.py`, `hint_part.py`, …) plus a migrator per type in
  `from_1_to_2/migrators.py`. That machinery is the right shape for a
  *structural* change; spending it on one nullable string would be pure
  ceremony, and it would leave a `models_1` package to maintain forever.
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
# letters only, and one alphabet per prefix — never both (decision B)
KEY_PREFIX_REGEXP = re.compile(r"^(?:[A-Z]{1,10}|[А-ЯЁ]{1,10})$")

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

**The prefix rule is stricter than the key rule, on purpose.** A prefix is
letters only (no digits — a prefix ending in a digit makes the prefix/body
boundary ambiguous) and may not mix alphabets: `ZZ` and `ЖЖ` are fine, `SХ` —
latin S, cyrillic Х — is not. That single rule kills the homoglyph trap where
two visually identical prefixes are different strings, and a player typing on
the wrong keyboard layout cannot land on a valid-but-different prefix.

This does **not** apply to the key body, which stays deliberately mixed:
`tests/fixtures/resources/valid_keys.txt` has `SHПРИВЕТ` and `СХHFJD` as valid
today, and they must remain so. Only the prefix is single-alphabet.

The 1–10 length cap is an assumption, not a decision — nothing turns on the
exact number, but a cap keeps the union regexp bounded.

### 4.2 Where authored keys get validated

`BonusKey.__post_init__` cannot know its level's prefix, so it stops being the
place where prefix correctness is decided:

- `BonusKey.__post_init__` → checks only the **body** charset (`[A-ZА-ЯЁ\d]+`,
  non-empty) and the bonus range. It no longer imports `is_key_valid`.
- `LevelScenario.__post_init__` → gains a check that **every** key in
  `self.conditions.get_keys()` matches the level's prefixes. This is strictly
  more coverage than today, because the keys of the **master key** (win
  condition) and of **effects keys** were never validated at all.

This is the one behaviour change that can reject scenarios which currently
load. Worth a scan of production scenarios before merging — if any existing
level has a key that fails the new check, the check must degrade to a warning
for `keys_prefix is None` levels.

Add to `LevelScenario`:

```python
def get_key_prefixes(self) -> tuple[str, ...]:
    return (self.keys_prefix,) if self.keys_prefix else DEFAULT_KEY_PREFIXES
```

### 4.3 Play path — smaller than it first looks

Decision A ("a wrong-prefix key is just a wrong key") collapses most of the
work here. `SH123` typed in a `ZZ` level is simply not a member of the level's
key set, so `LevelScenario.check` already returns `WrongKeyDecision` for it and
`submit_key` already logs it. **No per-level prefix check is needed on the play
path at all.**

What *does* have to change at `core/services/key.py:31` is the opposite of a
new restriction. Today `is_key_valid(key)` rejects anything that is not
`SH…`/`СХ…`, so a perfectly correct `ZZABC` would be thrown out as invalid
before it ever reached the level. That gate has to widen to "does this look
like a key attempt at all":

```python
if not is_key_valid(key, await self.key_prefixes.get_all()):   # defaults ∪ active custom
    raise exceptions.InvalidKey(...)
```

which is the same union the bot prefilter uses (§5.1). It stays in `check_key`
— it does not need to move into `submit_key`, because it no longer depends on
the level.

So the prefix has teeth in exactly three places, none of them the play path:

1. **Authoring** — which keys the author may write into a level (§4.2).
2. **The bot prefilter** — what gets picked up as a key attempt (§5.1).
3. **Copy** — what the player is told when nothing matches (§4.4).

`level_testing.py:84` widens the same way. One consequence to accept
deliberately: with the union gate, a key belonging to *another* concurrently
active game's prefix is logged as a wrong key rather than rejected. Given
`ACTIVE_STATUSES` allows only one active game at a time (`context.md`), the
union is in practice "defaults + this game's prefixes", so this is close to
theoretical.

### 4.4 Texts

`INVALID_KEY_ERROR` (`core/views/texts.py:9`) and `InvalidKey.notify_user` are
built once at import from the global constant, both naming SH/СХ. They become
functions of the prefixes in play, rendered per message. Note that after
decision A this copy is seen *less* often than today — a well-formed key with
the wrong prefix now gets the ordinary wrong-key response, not a format
complaint.

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
message `SH123` still *passes* the filter (SH is a default), reaches the level,
matches no key, and is **logged as a wrong key** (decision A). This is the
combination that makes the whole design cheap — the filter stays a coarse,
cacheable prefilter precisely because it is allowed to over-accept, and the
level's key set is the only thing that decides correctness.

### 5.2 Author-side editing

`convert_keys` (`dialogs/level_scn/handlers.py:69`) validates typed keys via
`is_multiple_keys_normal` against the globals. It must validate against the
prefix of the level being edited, which imposes an ordering constraint on the
dialog: **the prefix must be settable before the keys are entered.** That means
a new window/state in `LevelKeysSG`/level-edit flow plus a place to display and
change the current prefix. This is subtask 5 (§11) — the engine works without
it, since prefixes can be set through the API and scenario upload.

## 6. API / UI

The API serialises the scenario dataclasses directly through adaptix, so
`keys_prefix` appears in game/level payloads with no schema work. `shvatka-ui`
needs *code* changes only if the prefix should be *shown* (scenario view) or
*edited* in the web editor — worth confirming, but not on the critical path.
Its `context.md` is a different matter and does have to change; see §7.

## 7. Ubiquitous language (`context.md`)

`context.md` states its own rule: *"The glossary follows the domain. When the
domain gains a concept (or an existing word shifts meaning), change this file in
the same PR that changes the code."* This feature does both, so the glossary
edits are part of the work, not a follow-up:

**A term shifts meaning.** The **Key / Ключ** row currently reads "Starts with
`SH` or `СХ`, then uppercase Latin/Cyrillic letters and digits". That stops
being true. It becomes: starts with the level's **key prefix** — `SH` or `СХ`
unless the author set another — then uppercase Latin/Cyrillic letters and
digits.

**A second row leans on the same claim.** In *Words we don't use*, the
`Code / код` row justifies itself with "only a key has the `SH`/`СХ` format and
a row in the key log". The justification survives, the wording does not: it
should say *the key format defined by the level* rather than naming the two
default prefixes.

**The domain gains a concept**, so a new row belongs in *Scenario — what an
author writes*, next to **Master key** and **Effects key**:

| Term | Русский | Meaning | Where |
| --- | --- | --- | --- |
| **Key prefix** | Префикс ключа | The leading letters every key of a level must start with. `SH` and `СХ` by default; an author may set another for a level, and then the defaults are no longer keys there. | `LevelScenario.keys_prefix`, `DEFAULT_KEY_PREFIXES` |

The Russian term is settled by the issue title itself — «Кастомные префиксы
ключей» — so *префикс ключа* is what organizers already say.

**And the front-end carries the same glossary.** `context.md` says
[bomzheg/shvatka-ui](https://github.com/bomzheg/shvatka-ui) has its own copy and
that "when a term changes here, change it there too". So the UI repo's
`context.md` needs the same three edits even if no UI code changes — which
makes the shvatka-ui side of this feature non-optional, unlike §6 suggests.

One naming check against the glossary's own rules: `ActiveKeyPrefixesProvider`
(§5.1) follows the `CurrentGameProvider` / `IdentityProvider` pattern the
glossary sanctions for "the way any layer above the DAO asks a question", and
`keys_prefix` sits in `scn.*` where scenario documents live. No new interactor
is introduced, so the *use case is an `Interactor`* rule does not bite.

## 8. Tests

- `tests/unit/input_validation/test_key_validation.py` — parametrise over
  prefixes; add cases where `SH…` is invalid under a custom prefix.
- `tests/fixtures/resources/valid_keys.txt` gets a custom-prefix sibling.
- A scenario fixture with `keys_prefix` set on one level and not on another,
  proving both round-trip and that the field is omitted when unset.
- Unit: `LevelScenario.__post_init__` rejects keys that do not match its prefix.
- Integration (`tests/integration/test_game_play.py`): in a custom-prefix
  level, a `SH…` key is not accepted, and the custom-prefix key levels up.
- Level testing: same via `test_level_tesing.py`.

## 9. Suggested order of work

1. `input_validation.py` — parametrised API + `validate_key_prefix`, defaults
   unchanged. Pure addition, no behaviour change. *(tests)*
2. `LevelScenario.keys_prefix` + `get_key_prefixes()` + `__post_init__`
   validation + `omit_default` recipe. *(tests, scenario round-trip)*
3. Move `BonusKey`'s prefix check up to the level. *(tests)*
4. Play path + level testing + `InvalidKey.expected_prefixes` + dynamic texts.
   *(integration tests)*
5. `ActiveKeyPrefixesProvider` + injected `is_key` filter.
6. Author UI in the bot dialog and in the web editor.
7. Docs: `docs/modules/ROOT/pages/author/level-concept.adoc:33` currently states
   the SH/СХ rule as absolute.

Glossary edits (§7) ride along with whichever step first makes the term real —
step 2 — in that same PR, in both repositories.

Steps 1–4 are independently shippable and leave the product working with
prefixes settable via scenario upload / API only; 5 is what makes a custom
prefix usable in a real game over Telegram.

## 10. Decisions on the second round

**A. A wrong-prefix key is just a wrong key.** `SH123` typed in a `ZZ` level is
logged and counted like any other miss — no special "wrong format" path. This
is what makes §4.3 nearly empty: set membership already produces
`WrongKeyDecision`, so the play path needs no prefix awareness. It also means
the engine never has to explain the prefix mid-game, which keeps the copy
change (§4.4) to the edges.

**B. Letters only, one alphabet per prefix.** No digits, and no mixing latin
with cyrillic in a single prefix. The key *body* keeps mixing freely. See §4.1;
the length cap remains an implementation choice.

**C. Per level, and only per level.** No game-level field, no inheritance. If
setting the prefix on twenty levels proves tedious, the answer is a *"apply to
all levels"* affordance in the web editor that writes the same value into each
level — a UI convenience over the existing per-level model, not a second place
where a prefix can live. Worth stating plainly because it is the tempting
shortcut: the moment a prefix can be stored in two places, every read needs a
precedence rule and every level needs to know whether its value is its own or
inherited.

**D. Ship as subtasks.** The steps in §9 become separate issues under #162
rather than one change; see below.

## 11. Subtasks

§9 splits into sub-issues of #162 along the seams where each piece is
independently mergeable and independently useful:

| Issue | Subtask | Depends on |
| --- | --- | --- |
| #326 | Parametrise `input_validation` by prefixes + `validate_key_prefix` | — |
| #327 | `LevelScenario.keys_prefix`, validation of authored keys, glossary edits in both repos | #326 |
| #328 | Widen the play-path and level-testing gate to the prefix union; prefix-aware copy | #326, #327 |
| #329 | `ActiveKeyPrefixesProvider` + injected `is_key` filter | #326, #327 |
| #330 | Author UI: set the prefix in the bot level editor | #327 |
| #331 | Author UI: set the prefix in the web editor, incl. "apply to all levels" (decision C) | #327 |
| #332 | User docs — `level-concept.adoc` states the SH/СХ rule as absolute | #327 |

After #326–#328 the feature works end to end for scenarios uploaded via
API/zip. #329 is what makes a custom-prefix key typeable in a Telegram game, so
it is the last *required* piece; #330–#332 are ergonomics and documentation.
