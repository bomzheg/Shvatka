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

## Three kinds of client

The endpoints split by who calls them, and the split matters as much as the
rates — the same request count means something different coming from three
dashboards than from three hundred phones.

| class            | how many                | what it does |
|------------------|-------------------------|--------------|
| `PlayerUser`     | whatever `-u` says      | polls unread-count and the current level, pulls hint files, browses teams and games |
| `OrganizerUser`  | `fixed_count = 3`       | reloads the keys and stat dashboards — the two expensive queries of the night |
| `AdminUser`      | `fixed_count = 1`       | looks players up in the admin panel |

`fixed_count` on the last two is deliberate: there are three orgs on a night
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

## Reading the results

Requests are reported under templated names (`/games/{id}/keys`, not
`/games/17/keys`), the same way `asgi-monitor` labels them — so locust's table
lines up row for row with the Grafana panel it was built from.

An idle target is not an error: no running game means 404 from `/games/active`
and friends, and 403 means this account is not an org of the game it is looking
at. Both are counted as successes, because reporting them as failures buries the
real ones on any environment that simply has no game on right now.
