# Load test

`locustfile.py` replays the shape of a real game night against the api.

## Where the numbers come from

The task weights are the number of 2xx responses each endpoint served during one
actual game, read off the `asgi-monitor` request counters (the *Percent of 2xx
Requests* panel). They are written into the file as those raw counts rather than
normalised, so the profile can be re-derived from a later game by pasting new
numbers in.

The one thing worth knowing before reading them: `GET /notifications/unread-count`
is **~80% of everything the api answers on a game night** — 15.7K calls against
909 for the next endpoint. The web client polls it. Any load test that spreads
its calls evenly across the routes is testing traffic the api never sees.

## Four kinds of client

The endpoints split by who calls them, and the split matters as much as the
rates — the same request count means something different coming from three
dashboards than from three hundred phones. Three of these classes are the
measured night; the fourth is opt-in and explained at the end.

| class            | how many                | what it does |
|------------------|-------------------------|--------------|
| `PlayerUser`     | whatever `-u` says      | polls unread-count and the current level, pulls hint files, browses teams and games |
| `OrganizerUser`  | `fixed_count = 3`       | reloads the keys and stat dashboards — the two expensive queries of the night |
| `AdminUser`      | `fixed_count = 1`       | looks players up in the admin panel |
| `KeySubmittingUser` | off by default       | types keys at the running game — see below |

`fixed_count` on the org and admin classes is deliberate: there are three orgs on a night
whether two hundred people are playing or two thousand, so their load must not
scale with `-u`.

## Running it

```shell
uv sync --group dev
SHVATKA_LOAD_PASSWORD=... uv run locust -f tests/load/locustfile.py \
    --host https://staging.example.org
```

or headless, for a fixed shape:

```shell
uv run locust -f tests/load/locustfile.py --host http://localhost:8000 \
    --headless -u 200 -r 10 -t 10m
```

**Point it at staging, not production.** The profile writes the way the real
clients do: it marks notifications read, and it subscribes and unsubscribes a
synthetic push endpoint (paired, so it leaves no rows behind).

### Accounts

| variable | default | used by |
|---|---|---|
| `SHVATKA_LOAD_USERNAME` / `SHVATKA_LOAD_PASSWORD` | `bomzheg` / `1234` | `PlayerUser`, and the fallback for the two below |
| `SHVATKA_LOAD_ORG_USERNAME` / `SHVATKA_LOAD_ORG_PASSWORD` | the player's | `OrganizerUser` — needs to be an org of the running game, or the keys/stat calls answer 403 |
| `SHVATKA_LOAD_ADMIN_USERNAME` / `SHVATKA_LOAD_ADMIN_PASSWORD` | the player's | `AdminUser` — needs to be a superuser |

Every virtual user of a class logs in as the same account. That is fine for the
read load and wrong for anything that measures per-player cache behaviour; if
you need distinct players, that is the change to make.

### What to point it at

The profile discovers its own targets on start — the active game, the player's
team, and the file guids of the current level — so it runs against any
environment without a fixture dump. Two knobs cover what it cannot discover:

- `SHVATKA_LOAD_GAME_ID` — a game to fall back on when nothing is running, so
  the game card / keys / stat / release calls still have something to ask about.
  Without it the profile falls back to a random completed game, and if there are
  none, quietly skips those tasks.
- `SHVATKA_LOAD_SCENARIO_GAME_ID` — a **throwaway draft game whose scenario may
  be overwritten**. This is the one genuinely destructive call of the night
  (`PUT /games/my/{id}/scenario`, 105 calls on the measured game, and the
  heaviest write the api takes), so it is off unless you name a game for it.
  Discovery never picks one.

## Typing keys (opt-in)

`KeySubmittingUser` submits keys to `POST /games/running/key`. It is off unless
you ask for it:

```shell
SHVATKA_LOAD_KEY_USERS=5 uv run locust -f tests/load/locustfile.py \
    --host https://staging.example.org
```

**These rates are the one judgement call in the profile, not a measurement.**
On the measured night keys arrived through the bot webhook (`/webhook/bot`,
3.54K) rather than through the api, so the panel says nothing about how often
this endpoint was called. What is modelled is the *shape* of what a team types —
mostly wrong, some right, plenty of repeats — at weights chosen to look like a
team playing, not to reproduce a measured rate. Faking the webhook itself was
considered and dropped: it would mean forging Telegram updates and having the
bot answer them, which is a different test.

### `scenario.yml` is part of the test, not documentation

The profile parses `tests/load/scenario.yml` before the run and works out which
keys it may send. **It must be the scenario of the game on the target.**

A level advances when every key of a condition has been typed, so the plan holds
one key of every condition back and never sends it. What is safe to send is
recomputed from `/games/running/level/current` on every poll, because a key
somebody typed before the run counts towards the condition just the same — a
level the team is halfway through yields *more* safe keys, not fewer. Keys of
other levels are sent too, as realistic wrong keys; the current level's keys are
never among them, the held-back one least of all.

The consequence to keep in mind:

- A scenario naming **fewer** keys than the real level is safe. Worst case
  nothing it sends is correct at all, and the run is just wrong-key load.
- A scenario naming **more** is not. If this file thinks a level has three keys
  and the real one has a single key, the "safe" pair includes the real level's
  only key, and the team levels up.
- A level number the file doesn't cover degrades to generated keys only, with a
  warning naming the level — that warning means the file does not match the game.

So it never *finishes* a game, and a run can be repeated against the same game
indefinitely. It is still not read-only: every submission is written to the key
log, and correct ones count as found for the team. Point it at staging.

The account in `SHVATKA_LOAD_KEY_USERNAME` / `SHVATKA_LOAD_KEY_PASSWORD`
(defaulting to the player account) must be **waivered for the running game** and
in a team, or every submission comes back 422. That shows up in locust's error
table as `key refused: WaiverError` rather than as a latency number, which is
the intended way to notice.

| variable | default | meaning |
|---|---|---|
| `SHVATKA_LOAD_KEY_USERS` | `0` (off) | how many clients type keys |
| `SHVATKA_LOAD_KEY_USERNAME` / `_PASSWORD` | the player's | who types them |
| `SHVATKA_LOAD_KEY_SCENARIO` | `tests/load/scenario.yml` | the scenario of the game on the target |


## A note on the locust version

The lockfile pins **locust 2.39.1**, which has a bug that crashes a run at
random on python 3.13: up to 2.40, `ResponseContextManager` aliases the
response's `__dict__` rather than copying it, while `request_meta` inside that
dict points back at the response — so once `HttpSession.request` returns, the
response is reachable only through that cycle. A garbage collection inside a
`with ... catch_response=True` block then clears the dict the context manager is
living in, and `__exit__` dies with `KeyError: 'name'`
([locustio/locust#3050](https://github.com/locustio/locust/issues/3050),
[#3207](https://github.com/locustio/locust/issues/3207)).

`ShvatkaUser.measured` works around it by binding the response before entering
the block, which keeps the cycle reachable for as long as the block runs. That
is why every request here goes through it rather than calling `self.client.get`
directly — a plain `with self.client.get(..., catch_response=True)` in this file
will crash under load.

The workaround can go once locust can be bumped past 2.40. It cannot be bumped
today: locust >= 2.41 requires `pytest >= 8.3.3` and this project pins
`pytest < 8.0`, so raising the floor makes the dependencies unsatisfiable.
Either move the suite to pytest 8 first, or declare the two groups mutually
exclusive so uv resolves them apart:

```toml
[tool.uv]
conflicts = [[{ group = "dev" }, { group = "test" }]]
```

That resolves (locust 2.46.4 for `dev`, pytest 7.4.4 for `test`, and CI's
`uv sync --group test` is unaffected), at the cost of not being able to install
both groups into one environment.

## Reading the results

Requests are reported under templated names (`/games/{id}/keys`, not
`/games/17/keys`), the same way `asgi-monitor` labels them — so locust's table
lines up row for row with the Grafana panel it was built from.

An idle target is not an error: no running game means 404 from `/games/active`
and friends, and 403 means this account is not an org of the game it is looking
at. Both are counted as successes, because reporting them as failures buries the
real ones on any environment that simply has no game on right now.
