# Parallel levels — design plan

> Status: **planning only, no code yet.** Design notes for
> [#217](https://github.com/bomzheg/Shvatka/issues/217). Records the model we
> agreed on and the decisions behind it, so the implementation PRs have
> something to point at. Expected to turn into an ADR.

Today a team is on exactly one level at a time. We want a team to be able to
work several levels at once — the immediate case being the *полевой* part and
the *мозговой* part of what is currently written as one level.

## 1. The four shapes, and what is in scope

Four game mechanics motivated this. They are not four features — they fall into
two families.

| Mechanic | What it is | Family |
|---|---|---|
| **полевой + мозговой** | One level is really two: a field task and an armchair task. Today written as a single level whose puzzle says «полю: … мозгу: …» and whose win condition needs both keys. | parallel chains |
| **одинокий рыцарь** | The team walks its own chain of levels; one player walks a shorter, easier chain in parallel. When the knight is done he rejoins the team; the game ends when both chains are done. | parallel chains |
| **штурм** | Every level of the game is open from the start; the team solves all of them in any order. Hints are paid — a hint costs penalty minutes — because nobody can hold twenty levels in their head on a timer. | pool with slots |
| **своя игра** | A pool of independent tasks, two open at once. Solve one (or give it up after X minutes) and draw the next. The whole block is time-boxed; scoring is by task cost. | pool with slots |

**In scope for #217: parallel chains only.** The pool family needs two
mechanics that do not exist anywhere in the engine and are useful outside
parallelism — *hints on demand with a penalty*, and *the team choosing which
level to take next* — plus a slot count and a time-box for the block. Those get
their own issues. This document only requires that the model here does not
preclude them (§11).

Both pool mechanics can already be faked with today's tools, which is why they
can wait: a paid hint is a key whose effects carry a penalty and a hint, with
the key printed in the level text (chain the keys and successive hints cost
successively more); level choice is likewise keys with effects, at the cost of
the team having to remember which levels it has already taken.

## 2. Where "one team, one level" lives today

The whole assumption rests on one query: `LevelTimeDao._get_current` orders
`levels_times` by `start_at DESC LIMIT 1`
(`shvatka/infrastructure/db/dao/rdb/level_times.py:50`). "The team's current
level" is literally "the newest row". Everything else follows from it:

| Place | What it assumes |
|---|---|
| `KeyProcessor.submit_key` (`core/services/key.py:37`) | A key is checked against one level — `get_current_level`. |
| `TimerProcessor.process` (`core/services/key.py:159`) | Same, for level timers. |
| `game_play.send_hint` (`core/games/game_play.py:108`) | "Has the team left this level?" is `lt.id != lt_id`. |
| `GamePlayerDaoImpl.level_up` (`db/dao/complex/game_play.py:128`) | Level-up only *inserts* a new row; nothing is ever closed. |
| `LevelTime.has_finished` (`core/models/dto/levels_times.py:35`) | The team is finished when its level number ran off the end of the list. |
| `results.to_results` (`core/games/results.py`) | A level's duration is the gap to the *next row in the chain* (`zip` over adjacent pairs). |
| `CurrentHintsAndKeys` (`core/games/dto.py`), `CurrentHintResponse` (`api/games/responses.py:288`) | One `level_number`, one `level_time_id`, one hint list. |
| `LevelTimeOnGame` (`core/models/dto/levels_times.py:53`) | The spy sees one current level per team. |

So the work is not "allow two levels" — it is replacing a cursor with a set,
and carrying that set through DAO → interactors → API → UI.

## 3. The model: branches and targets

Two new domain words (to be added to `context.md`):

- **Branch** / *ветка* — one active line of progress for a team. Concretely, a
  `levels_times` row that has not been closed yet.
- **Position** / *позиция команды* — the set of a team's open branches. Replaces
  "the team's current level" everywhere.

One new column: **`levels_times.finished_at`**, nullable. Open branches are the
rows where it is null. A branch is closed when it is left, not when the next one
starts — which is what makes a duration meaningful when two branches overlap.

### 3.1 The one rule

A closing branch **points at a target** — a level, or the finish.

> **A target opens when no open branch can still reach it.**

That single rule covers all three of our chain cases, with no author-facing
flags:

- **полевой + мозговой.** 5a and 5b both point at 6. The field part closes after
  20 minutes, but 5b is open and can still reach 6 — so 6 waits. When 5b closes,
  6 opens. This reproduces today's "both keys required" semantics exactly, which
  is the point: the author writes the parts separately and the engine glues them.
- **одинокий рыцарь.** The team's chain and the knight's chain never point at the
  same level, so nothing ever waits — each branch advances on its own. Both
  chains eventually point at *the finish*, and the finish is a target like any
  other: unreachable until both are closed.
- **early finish.** In a linear game, a branch that points at the finish from any
  level ends the game for that team, because there is no other open branch.

The finish being an ordinary target is what unifies these. It also replaces
`has_finished`: a team is finished when it has **no open branches**, not when a
level number ran off the end of the list.

### 3.2 Reachability

"Can still reach" is computed over the routing graph of the scenario — the same
graph the front-end already builds for the scenario view
(`shvatka-ui/src/app/scenario_graph.part`, `routingGraphFromGame`). Cycles are
allowed in the engine (see the `allow_level_times_cycles` migration), and a
cycle upstream of a barrier can make a target permanently unreachable-but-not-
yet-arrived. This is a real deadlock risk and is called out in §11.

## 4. Scenario language

Effects get two orthogonal fields instead of one entangled pair:

- `level_up: bool` — **close the current branch**. (The name now means exactly
  that, not "move to the next level". `context.md` needs the correction; a rename
  is not proposed here.)
- `next_level: list[str] | None` — **what to open**, by `name_id`. Was a single
  optional `name_id`.

| `level_up` | `next_level` | Meaning |
|---|---|---|
| `true` | not set (`null`) | Close the branch, open the next level in order. **Today's plain level-up.** |
| `true` | `["x"]` | Close the branch, open `x`. **Today's routed level-up.** |
| `true` | `["x", "y"]` | Close the branch, open two — a fork. |
| `true` | `[]` | Close the branch, point at the finish. |
| `false` | `["x"]` | Open `x` and keep the current branch — a fork that keeps its parent. |
| `false` | `null` or `[]` | No routing; effects only. **Today's bonus/hint effects.** |

Note the two distinct empty values: `null` means "next in order" (kept for
backwards compatibility), `[]` means "the finish". JSON keeps them apart, but in
the level editor they are two different buttons, not one — worth getting right
in the UI or authors will fall into it.

`штурм` needs no special support in this language: it is one fork from the
opening level into every other level, each of which points at the finish.

Scenario model version goes **1 → 2**, migrating `next_level: "x"` to
`next_level: ["x"]` on read (`core/migration_utils/`, alongside the existing
`from_1_to_2`). Stored games keep working untouched.

## 5. Validation

`Conditions.validate_keys_unique` (`core/models/dto/scn/level.py`) enforces key
uniqueness *within* a level. With parallel branches that is no longer enough:

- **Keys must be unique across levels that can be open at the same time.** This
  is decidable statically from the fork graph, and it is what lets a submitted
  key be routed to a branch automatically (§6).
- **Fork targets must exist** — each `name_id` in `next_level` resolves.
- **Barrier reachability** — warn (or refuse) when a target sits behind a cycle
  such that it can never satisfy "no open branch can reach it".
- The existing per-level rules are unchanged: a level still needs at least one
  condition that can end it.

## 6. Runtime

**Keys.** A submitted key is checked against **every open branch**. Validation
guarantees at most one match, so there is no choosing and no ambiguity to
resolve at play time. The UI reports which branch took the key.
`LevelScenario.check` already returns a `Decisions` collection; the change is
collecting decisions across several scenarios rather than one.

**Duplicates.** Scoped to the branch, not the team — `get_correct_typed_keys`
and `get_team_typed_keys` are already keyed on `level_time`, so this falls out.
The key log records everything either way.

**Hints.** Cheapest part of the whole change: `schedule_first_hint` already
carries `lt_id` into the scheduler, and `send_hint` already compares against it.
The comparison changes from "is this the current level time" to "is this level
time still open" and the scheduler supports N parallel hint timelines unchanged.

This is also the real prize of splitting полевой from мозговой: the two parts get
**independent hint schedules**. Today they share one, so hints for the armchair
part are paced by how fast the car is moving.

**Level timers.** Already scoped by `lt_id`, so a force-level-up timer closes its
own branch and leaves the others alone.

## 7. Results and time

The results sheet already carries two independent blocks, and both survive:

- **Wall clock** — when each level was entered. Unchanged.
- **Duration** — per level. Becomes *more* correct: with `finished_at` a duration
  is `finished_at - start_at` for that branch, instead of the gap to whatever row
  happened to come next. The adjacent-pair `zip` in `to_results` goes away.

Durations of parallel branches must not be summed — they overlap in real time.
The sheet does not compute adjusted totals anyway (by design, see `results.py`),
so this is a matter of labelling the parallel block, not of new arithmetic. A
team's total remains wall-clock: finish minus start.

**Numbering stays flat.** Splitting one level into two means the levels after it
shift by one, and a parallel pair shows as two numbers at once. Accepted as-is:
teams here are never told how many levels a game has, so there is no "level 5 of
12" to break. Whether to show `name_id` to players instead is left open (§11).

## 8. API and web

`CurrentHintsAndKeys` / `CurrentHintResponse` change from one level to a list:

```
branches: [{ level_time_id, level_number, name_id, hints, started_at }, …]
typed_keys, events   # each tagged with its branch
is_finished          # now: no open branches
```

Layout, for the two-branch case: **two columns on desktop, stacked on mobile** —
not tabs. The armchair level wants to stay in view while the field level is being
driven; that is the whole reason the mechanic exists. Tabs or an accordion are
the fallback for three or more.

One key input, at the top, shared. The engine routes the key; the UI says which
branch took it. Players should not have to aim under adrenaline.

Also needed: per-branch countdown to the next hint; branch colour or icon so the
key log and event feed can be read at a glance; and the spy
(`GameStatWithHints`, `LevelTimeOnGame`) showing a team's cell as a list rather
than one level. The scenario graph already draws forks — that is where an author
will actually see what they have built.

**Branch names.** Levels have only `name_id`, which is technical and often
deliberately meaningless (a semantic one leaks the location). With two panels
side by side, "Уровень 5a / Уровень 5б" reads badly where "Полевой / Мозговой"
reads well. Whether that means a display label on levels or exposing `name_id` is
part of the open question in §11.

## 9. Telegram

Explicitly not solved in this iteration; the bot must merely not get worse.

No topics — nobody likes them. Hints from all open branches go to the team chat
as they do now, prefixed with the branch. Note that this is not a regression:
today полевой and мозговой hints already interleave in the chat, because they
are one level. Optionally the bot can post each branch's hints as **replies** to
that branch's first message, which Telegram renders as a thread — the cheapest
threading available without topics.

Key submission needs no change: auto-routing works, and the reply names the
branch.

## 10. Order of work

1. **`finished_at` + position as a set.** Pure refactor: the set always has one
   element, behaviour is identical. Already earns its keep by making durations
   honest.
2. **API returns a list of branches; web renders a list.** Still length 1, still
   looks like today.
3. **Fork and the target rule.** `next_level` becomes a list, `level_up` means
   "close the branch", finish becomes a target. Web handles 2+; bot gets prefixes.
4. **Validation** — cross-level key uniqueness, fork targets, barrier
   reachability.
5. **Editor** — fork and finish-target in the constructor and in the graph.
6. **Results** — label parallel blocks in the sheet.

Steps 1 and 2 are useful on their own and change no behaviour, so they can land
before any of the design here is finalised.

## 11. Open questions

- **Cycles plus barriers can deadlock** (§3.2). Refuse such scenarios in
  validation, or detect at runtime and force the target open? Needs a decision
  before step 4.
- **Does barrier waiting time count?** Proposal: yes — the total is wall-clock, so
  it counts automatically, and anything else invites racing to the barrier.
- **Naming branches for players** (§8) — display label on the level, exposed
  `name_id`, or nothing? Affects the web layout and the spy.
- **Nested forks** — a branch forking again is technically free. Allow in the
  model, restrict in the editor until someone asks?
- **A hint scheduled for a branch closed by a barrier** — the `lt_id` check
  suppresses it, which is right; confirm the same holds for a branch that closed
  while waiting.
- **Does the pool family need branches to carry a slot identity?** (§1) Worth a
  look before step 3 freezes the model, since штурм and своя игра are the reason
  the model must scale to N branches rather than two.

## 12. Deliberately not here

- **Paid hints** (hints on demand with a penalty) — needed by штурм, useful on its
  own. Today's workaround: a key with penalty-and-hint effects, printed in the
  level text.
- **Team-chosen levels, slot counts, block time-boxes** — needed by своя игра.
- **New condition types** — a button rather than a key; conditions over which
  levels the team has already taken; possibly conditions over what *other* teams
  have taken (in the Jeopardy version a task taken by anyone is gone for
  everyone). These are what would make the pool family pleasant rather than
  merely possible.
- **Splitting player subsets across branches.** Decided against: everyone sees
  every level and everyone can submit every key, including for the knight's
  branch. Restricting it buys nothing — the knight screenshots his task to the
  team chat anyway, and the team helping him is the point.
