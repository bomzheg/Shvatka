"""A load profile shaped like a real game night.

The task weights are the number of 2xx responses each endpoint actually served
during one game, as counted by ``asgi-monitor``'s request metrics. They are kept
as the raw observed numbers rather than normalised, so the mix stays readable —
and the mix is the point. Four out of five requests the api answers on a game
night are ``GET /notifications/unread-count``: the web client polls it, and it
outweighs every other endpoint by more than an order of magnitude. A load test
that spreads its calls evenly over the routes tests something the api never does.

The profile is *similar*, not exact. Endpoints are grouped into the kinds of
client that generate them, because a rate alone doesn't reproduce the load: the
orgs' keys/stat dashboards are a handful of clients hammering two expensive
queries, while the unread-count poll is hundreds of clients doing something
cheap. Locust models that with ``fixed_count`` for the few and ``weight`` for
the crowd.

A fourth class, ``KeySubmittingUser``, types keys at the running game. It is off
by default and its rates are a judgement call rather than a measurement — key
traffic reached the api through the bot webhook that night, not through
``POST /games/running/key`` — so it is kept apart from the observed weights.

Run it against a *staging* copy of the api — it writes (push subscriptions, read
marks) as the real clients do::

    SHVATKA_LOAD_PASSWORD=... uv run locust -f tests/load/locustfile.py \
        --host https://staging.example.org

Every user needs an account on the target; see ``tests/load/README.md`` for the
environment variables that name them.
"""

import logging
import os
import random
import string
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml
from locust import (  # type: ignore[import, unused-ignore]
    HttpUser,
    between,
    task,
)
from locust.exception import StopUser  # type: ignore[import, unused-ignore]

logger = logging.getLogger(__name__)

PLAYER_USERNAME = os.getenv("SHVATKA_LOAD_USERNAME", "bomzheg")
PLAYER_PASSWORD = os.getenv("SHVATKA_LOAD_PASSWORD", "1234")
ORG_USERNAME = os.getenv("SHVATKA_LOAD_ORG_USERNAME", PLAYER_USERNAME)
ORG_PASSWORD = os.getenv("SHVATKA_LOAD_ORG_PASSWORD", PLAYER_PASSWORD)
ADMIN_USERNAME = os.getenv("SHVATKA_LOAD_ADMIN_USERNAME", PLAYER_USERNAME)
ADMIN_PASSWORD = os.getenv("SHVATKA_LOAD_ADMIN_PASSWORD", PLAYER_PASSWORD)

# A game to fall back on when nothing is running on the target: the read-only
# game endpoints (card, keys, stat, release) need *some* id to ask about.
FALLBACK_GAME_ID = os.getenv("SHVATKA_LOAD_GAME_ID")
# A throwaway draft game whose scenario may be overwritten. Left unset, the
# scenario upload — the one genuinely destructive call of the night — is skipped.
SCENARIO_GAME_ID = os.getenv("SHVATKA_LOAD_SCENARIO_GAME_ID")

# How many clients type keys at the running game, and as whom. Zero (the
# default) spawns none: unlike everything else here, key submission needs the
# scenario file to match the game on the target, so it is never on by accident.
KEY_USERS = int(os.getenv("SHVATKA_LOAD_KEY_USERS", "0"))
KEY_USERNAME = os.getenv("SHVATKA_LOAD_KEY_USERNAME", PLAYER_USERNAME)
KEY_PASSWORD = os.getenv("SHVATKA_LOAD_KEY_PASSWORD", PLAYER_PASSWORD)
KEY_SCENARIO_PATH = Path(
    os.getenv("SHVATKA_LOAD_KEY_SCENARIO", str(Path(__file__).parent / "scenario.yml"))
)

# Statuses that are a legitimate answer rather than a broken server: no game is
# running (404), the level has no files yet (404), this account is not an org of
# the game it is looking at (403). Reporting them as failures would drown the
# real errors on a target that simply has no game on right now.
EXPECTED_STATUSES = (403, 404)


KEY_CONDITIONS = ("WIN_KEY", "EFFECTS_KEY")
WRONG_KEY_ALPHABET = string.ascii_uppercase + string.digits


def parse_scenario(path: Path) -> list[list[set[str]]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        [
            {str(key) for key in condition.get("keys", ())}
            for condition in level.get("conditions", ())
            if condition.get("type") in KEY_CONDITIONS and condition.get("keys")
        ]
        for level in raw.get("levels", ())
    ]


def load_key_plan() -> tuple[list[list[set[str]]], set[str]]:
    if KEY_USERS <= 0:
        return [], set()
    levels = parse_scenario(KEY_SCENARIO_PATH)
    all_keys = {key for level in levels for keys in level for key in keys}
    if not all_keys:
        msg = f"{KEY_SCENARIO_PATH} holds no key conditions — nothing to type"
        raise RuntimeError(msg)
    logger.info(
        "key load: %s levels, %s keys from %s", len(levels), len(all_keys), KEY_SCENARIO_PATH
    )
    return levels, all_keys


# Key conditions of the scenario, level by level: LEVEL_KEYS[n] holds the key
# sets of level n's conditions. Empty unless key users were asked for.
LEVEL_KEYS, ALL_SCENARIO_KEYS = load_key_plan()


def plan_safe_keys(level_number: int | None, typed: set[str]) -> list[str]:
    if level_number is None or not 0 <= level_number < len(LEVEL_KEYS):
        return []
    safe: list[str] = []
    for keys in LEVEL_KEYS[level_number]:
        safe.extend(sorted(keys & typed))
        untyped = sorted(keys - typed)
        # the last one would complete the condition, so it is never sent
        safe.extend(untyped[:-1])
    return safe


def keys_of_other_levels(level_number: int | None) -> list[str]:
    if level_number is None or not 0 <= level_number < len(LEVEL_KEYS):
        # the scenario doesn't describe the level the team is on, so it cannot
        # say which keys are this level's — send none of them rather than guess
        return []
    mine = {key for keys in LEVEL_KEYS[level_number] for key in keys}
    others = {
        key
        for number, level in enumerate(LEVEL_KEYS)
        if number != level_number
        for keys in level
        for key in keys
    }
    return sorted(others - mine)


def make_wrong_key() -> str:
    for _ in range(10):
        key = "SH" + "".join(random.choices(WRONG_KEY_ALPHABET, k=7))
        if key not in ALL_SCENARIO_KEYS:
            return key
    return "SH" + uuid.uuid4().hex[:10].upper()


class ShvatkaUser(HttpUser):
    abstract = True
    username = PLAYER_USERNAME
    password = PLAYER_PASSWORD

    def on_start(self) -> None:
        self.login()

    def login(self) -> None:
        with self.measured(
            "POST",
            "/auth/token",
            "/auth/token",
            data={"username": self.username, "password": self.password},
        ) as resp:
            if not resp.ok:
                resp.failure(f"login as {self.username} failed: {resp.status_code}")
                logger.error(
                    "cannot log in as %s (%s) — stopping the user",
                    self.username,
                    resp.status_code,
                )
                raise StopUser
        # HttpSession is a requests.Session, so the Authorization cookie the
        # login set is carried by everything below without being passed around.

    @contextmanager
    def measured(self, method: str, url: str, name: str, **kwargs: Any) -> Iterator[Any]:
        catcher = self.client.request(method, url, name=name, catch_response=True, **kwargs)
        # Not dead code, and it has to happen here rather than inside the block:
        # the response is already collectable the moment `request` returns.
        _keep_reachable = catcher.request_meta["response"]
        with catcher as response:
            yield response

    def read(self, url: str, *, name: str | None = None) -> Any:
        with self.measured("GET", url, name or url) as resp:
            if resp.status_code in EXPECTED_STATUSES:
                resp.success()
                return None
            if not resp.ok:
                return None
            try:
                return resp.json()
            except ValueError:
                return None


class PlayerUser(ShvatkaUser):
    weight = 1
    wait_time = between(1, 3)

    game_id: int | None = None
    team_id: int | None = None
    player_id: int | None = None

    def on_start(self) -> None:
        super().on_start()
        self.file_guids: list[str] = []
        self.unread_ids: list[int] = []
        self.discover()

    def discover(self) -> None:
        game = self.read("/games/active", name="/games/active")
        if game:
            self.game_id = game.get("id")
        elif FALLBACK_GAME_ID:
            self.game_id = int(FALLBACK_GAME_ID)
        else:
            page = self.read("/games", name="/games")
            content = (page or {}).get("content") or []
            if content:
                self.game_id = random.choice(content).get("id")

        me = self.read("/users/me", name="/users/me")
        if me:
            self.player_id = me.get("id")

        role = self.read("/games/active/me", name="/games/active/me")
        team = (role or {}).get("team")
        if team:
            self.team_id = team.get("id")

        self.refresh_level()

    def refresh_level(self) -> None:
        level = self.read("/games/running/level/current", name="/games/running/level/current")
        if level:
            self.file_guids = collect_guids(level.get("hints"), [])

    @task(100)
    def unread_count(self) -> None:
        self.read("/notifications/unread-count")

    @task(909)
    def active_game(self) -> None:
        self.read("/games/active", name="/games/active")

    @task(789)
    def game_file(self) -> None:
        if self.game_id is None or not self.file_guids:
            return
        guid = random.choice(self.file_guids)
        self.read(
            f"/cdn/games/{self.game_id}/files/{guid}",
            name="/cdn/games/{id}/files/{guid}",
        )

    @task(387)
    def game_release(self) -> None:
        if self.game_id is None:
            return
        self.read(f"/games/{self.game_id}/release", name="/games/{id}/release")

    @task(228)
    def current_waivers(self) -> None:
        self.read("/waivers/game/current", name="/waivers/game/current")

    @task(227)
    def version(self) -> None:
        self.read("/version")

    @task(212)
    def users_me(self) -> None:
        self.read("/users/me", name="/users/me")

    @task(210)
    def current_level(self) -> None:
        self.refresh_level()

    @task(201)
    def my_role(self) -> None:
        self.read("/games/active/me", name="/games/active/me")

    @task(119)
    def game_card(self) -> None:
        if self.game_id is None:
            return
        self.read(f"/games/{self.game_id}", name="/games/{id}")

    @task(111)
    def team_players(self) -> None:
        if self.team_id is None:
            return
        self.read(f"/teams/{self.team_id}/players", name="/teams/{id}/players")

    @task(70)
    def user_details(self) -> None:
        if self.player_id is None:
            return
        self.read(f"/users/{self.player_id}/details", name="/users/{id}/details")

    @task(63)
    def games_list(self) -> None:
        self.read("/games", name="/games")

    @task(59)
    def push_config(self) -> None:
        self.read("/push/config", name="/push/config")

    @task(51)
    def push_subscription(self) -> None:
        subscription = {
            "endpoint": f"https://fcm.googleapis.com/fcm/send/{uuid.uuid4()}",
            "keys": {"p256dh": "BL" + "a" * 85, "auth": "b" * 22},
        }
        self.client.put("/push/subscriptions", json=subscription, name="/push/subscriptions")
        self.client.delete("/push/subscriptions", json=subscription, name="/push/subscriptions")

    @task(43)
    def user_stat(self) -> None:
        if self.player_id is None:
            return
        self.read(f"/users/{self.player_id}/stat", name="/users/{id}/stat")

    @task(40)
    def requests_list(self) -> None:
        self.read("/requests?direction=incoming&pending=true", name="/requests")

    @task(39)
    def teams_list(self) -> None:
        self.read("/teams", name="/teams")

    @task(27)
    def team_card(self) -> None:
        if self.team_id is None:
            return
        self.read(f"/teams/{self.team_id}", name="/teams/{id}")

    @task(24)
    def team_stat(self) -> None:
        if self.team_id is None:
            return
        self.read(f"/teams/{self.team_id}/stat", name="/teams/{id}/stat")

    @task(24)
    def my_captained_teams(self) -> None:
        self.read("/teams/my/captained", name="/teams/my/captained")

    @task(21)
    def notifications(self) -> None:
        page = self.read("/notifications?limit=50&offset=0", name="/notifications")
        self.unread_ids = [n["id"] for n in (page or {}).get("items", []) if not n["read"]]

    @task(16)
    def mark_read(self) -> None:
        if not self.unread_ids:
            return
        batch, self.unread_ids = self.unread_ids[:10], self.unread_ids[10:]
        self.client.post("/notifications/read", json={"ids": batch}, name="/notifications/read")


class OrganizerUser(ShvatkaUser):
    fixed_count = 3
    wait_time = between(2, 8)
    username = ORG_USERNAME
    password = ORG_PASSWORD

    game_id: int | None = None

    def on_start(self) -> None:
        super().on_start()
        self.my_game_ids: list[int] = []
        game = self.read("/games/active", name="/games/active")
        if game:
            self.game_id = game.get("id")
        elif FALLBACK_GAME_ID:
            self.game_id = int(FALLBACK_GAME_ID)
        page = self.read("/games/my", name="/games/my")
        self.my_game_ids = [g["id"] for g in (page or {}).get("content", [])]

    @task(394)
    def game_keys(self) -> None:
        if self.game_id is None:
            return
        self.read(f"/games/{self.game_id}/keys", name="/games/{id}/keys")

    @task(382)
    def game_stat(self) -> None:
        if self.game_id is None:
            return
        self.read(f"/games/{self.game_id}/stat", name="/games/{id}/stat")

    @task(105)
    def upload_scenario(self) -> None:
        if SCENARIO_GAME_ID is None:
            return
        self.client.put(
            f"/games/my/{SCENARIO_GAME_ID}/scenario",
            json=build_scenario(),
            name="/games/my/{id}/scenario",
        )

    @task(23)
    def my_games(self) -> None:
        self.read("/games/my", name="/games/my")

    @task(19)
    def my_game(self) -> None:
        if not self.my_game_ids:
            return
        self.read(f"/games/my/{random.choice(self.my_game_ids)}", name="/games/my/{id}")

    @task(16)
    def organizers(self) -> None:
        if self.game_id is None:
            return
        self.read(f"/games/{self.game_id}/organizers", name="/games/{id}/organizers")


class AdminUser(ShvatkaUser):
    fixed_count = 1
    wait_time = between(5, 15)
    username = ADMIN_USERNAME
    password = ADMIN_PASSWORD

    def on_start(self) -> None:
        super().on_start()
        self.player_ids: list[int] = []
        found = self.read("/admin/players?active=true", name="/admin/players")
        self.player_ids = [p["id"] for p in (found or {}).get("items", [])][:50]

    @task(78)
    def list_players(self) -> None:
        self.read("/admin/players?active=true", name="/admin/players")

    @task(26)
    def player_card(self) -> None:
        if not self.player_ids:
            return
        self.read(f"/admin/players/{random.choice(self.player_ids)}", name="/admin/players/{id}")

    @task(8)
    def waiver_points(self) -> None:
        if not self.player_ids:
            return
        self.read(
            f"/admin/players/{random.choice(self.player_ids)}/waiver-points",
            name="/admin/players/{id}/waiver-points",
        )


class KeySubmittingUser(ShvatkaUser):
    # `abstract` is what actually keeps it out of a run: locust reads
    # fixed_count = 0 as "not set" and falls back to weight, which would spawn
    # key typists against a target nobody opted in for.
    abstract = KEY_USERS <= 0
    fixed_count = KEY_USERS
    # ~20 keys/hour/client: 83% of tasks submit, so a 150s mean wait lands on the
    # measured rate. between(1, 4) — the first guess here — was 150x too hot.
    wait_time = between(60, 240)
    username = KEY_USERNAME
    password = KEY_PASSWORD

    def on_start(self) -> None:
        super().on_start()
        self.level_number: int | None = None
        self.safe_correct: list[str] = []
        self.other_level_keys: list[str] = []
        self.refresh_plan()

    def refresh_plan(self) -> None:
        level = self.read("/games/running/level/current", name="/games/running/level/current")
        if not level:
            self.level_number, self.safe_correct, self.other_level_keys = None, [], []
            return
        self.level_number = level.get("level_number")
        typed = {key["text"] for key in level.get("typed_keys", ()) if key.get("type_") != "wrong"}
        self.safe_correct = plan_safe_keys(self.level_number, typed)
        self.other_level_keys = keys_of_other_levels(self.level_number)
        if not self.safe_correct and not self.other_level_keys:
            logger.warning(
                "scenario %s says nothing about level %s — typing generated keys only. "
                "Is it the scenario of the game on the target?",
                KEY_SCENARIO_PATH.name,
                self.level_number,
            )

    def submit(self, key: str, name: str) -> None:
        with self.measured("POST", "/games/running/key", name, json={"text": key}) as resp:
            if resp.status_code == 422:
                # not a load problem: the account is not waivered for this game,
                # or no game is running. Name it so the error table says which.
                body = resp.json() if resp.content else {}
                resp.failure(f"key refused: {body.get('type', resp.status_code)}")
            elif resp.status_code in EXPECTED_STATUSES:
                resp.success()

    @task(70)
    def wrong_key(self) -> None:
        self.submit(make_wrong_key(), name="/games/running/key [wrong]")

    @task(15)
    def stale_key(self) -> None:
        if not self.other_level_keys:
            return
        self.submit(random.choice(self.other_level_keys), name="/games/running/key [wrong]")

    @task(15)
    def correct_key(self) -> None:
        if not self.safe_correct:
            return
        self.submit(random.choice(self.safe_correct), name="/games/running/key [correct]")

    @task(20)
    def poll_level(self) -> None:
        self.refresh_plan()


def collect_guids(node: Any, found: list[str]) -> list[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("file_guid", "thumb_guid") and isinstance(value, str):
                found.append(value)
            else:
                collect_guids(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_guids(item, found)
    return found


def build_scenario() -> dict[str, Any]:
    return {
        "__model_version__": 1,
        "name": f"load-test-{uuid.uuid4().hex[:8]}",
        "levels": [
            {
                "id": f"level-{number}",
                "__model_version__": 1,
                "conditions": [{"type": "WIN_KEY", "keys": [f"SH{number}ABC"]}],
                "time_hints": [
                    {"time": 0, "hint": [{"type": "text", "text": f"hint {number}"}]},
                    {"time": 10, "hint": [{"type": "text", "text": f"hint {number} later"}]},
                ],
            }
            for number in range(1, 6)
        ],
        "files": [],
    }
