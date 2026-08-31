"""A load profile shaped like a real game night.

The task weights are the number of 2xx responses each endpoint actually served
during one game, as counted by ``asgi-monitor``'s request metrics. They are kept
as the raw observed numbers rather than normalised, so the mix stays readable —
and the mix is the point. Four out of five requests the api answers on a game
night are ``GET /notifications/unread-count``: the web client polls it, and it
outweighs every other endpoint by more than an order of magnitude. A load test
that spreads its calls evenly over the routes tests something the api never does.

The profile is *similar*, not exact. Endpoints are grouped into the three kinds
of client that generate them, because a rate alone doesn't reproduce the load:
the orgs' keys/stat dashboards are a handful of clients hammering two expensive
queries, while the unread-count poll is hundreds of clients doing something
cheap. Locust models that with ``fixed_count`` for the few and ``weight`` for
the crowd.

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
import uuid
from typing import Any

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

# Statuses that are a legitimate answer rather than a broken server: no game is
# running (404), the level has no files yet (404), this account is not an org of
# the game it is looking at (403). Reporting them as failures would drown the
# real errors on a target that simply has no game on right now.
EXPECTED_STATUSES = (403, 404)


class ShvatkaUser(HttpUser):
    """Logs in once and keeps the auth cookie on the session, like a browser."""

    abstract = True
    username = PLAYER_USERNAME
    password = PLAYER_PASSWORD

    def on_start(self) -> None:
        self.login()

    def login(self) -> None:
        with self.client.post(
            "/auth/token",
            data={"username": self.username, "password": self.password},
            name="/auth/token",
            catch_response=True,
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

    def read(self, url: str, *, name: str | None = None) -> Any:
        """GET ``url``, returning the decoded body or ``None``.

        ``name`` is the templated path (``/games/{id}``) the request is counted
        under, so locust's stats line up with the Grafana panel this profile was
        built from instead of exploding into one row per id.
        """
        with self.client.get(url, name=name or url, catch_response=True) as resp:
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
    """The crowd: a phone in a car with the game open, polling.

    This is what ``-u`` spawns. Weights are the observed 2xx counts, so the
    unread-count poll dominates here exactly as it does in production.
    """

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
        """Find a game, a team and some file guids to ask for.

        Everything the parametrised tasks need is read from the target itself,
        so the profile runs against any environment without a fixture dump.
        """
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

    @task(15_700)
    def unread_count(self) -> None:
        """The poll that is four fifths of everything the api answers."""
        self.read("/notifications/unread-count")

    @task(909)
    def active_game(self) -> None:
        self.read("/games/active", name="/games/active")

    @task(789)
    def game_file(self) -> None:
        """A hint's picture. The heaviest response a player pulls."""
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
        """The other poll: what the team is looking at right now.

        It also refreshes the guids the file task downloads, so a level change
        during the run moves the load onto the new level's pictures.
        """
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
        """Subscribe and unsubscribe a synthetic endpoint.

        Paired on purpose: the subscription is deleted again, so a load run
        doesn't leave a row per virtual user behind on the target.
        """
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
        """Marking read is what the list is opened for, so it follows it."""
        if not self.unread_ids:
            return
        batch, self.unread_ids = self.unread_ids[:10], self.unread_ids[10:]
        self.client.post("/notifications/read", json={"ids": batch}, name="/notifications/read")


class OrganizerUser(ShvatkaUser):
    """A few people watching the game from the other side.

    ``fixed_count`` rather than ``weight``: there are three orgs on a night
    whether two hundred players are playing or two thousand, and it is the
    absolute number that matters — these two dashboards are the expensive
    queries of the profile, and their cost does not scale with the crowd.
    """

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
        """The keys table, reloaded over and over while the game runs."""
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
        """Rewrite a draft game's scenario — the heaviest write of the night.

        Off unless ``SHVATKA_LOAD_SCENARIO_GAME_ID`` names a game that may be
        overwritten: unlike everything else here, this one destroys what it
        touches, so it is never pointed at a game by discovery.
        """
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
    """One person in the admin panel, mostly looking players up."""

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


def collect_guids(node: Any, found: list[str]) -> list[str]:
    """Every ``file_guid`` anywhere in a hints tree.

    Hint parts nest (a hint holds parts, a part may carry a thumbnail), and the
    shape differs per hint type, so walking the json beats mirroring the models.
    """
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
    """A structurally real scenario for the upload task.

    Shaped after ``tests/fixtures/resources/simple_scn.yml`` — the endpoint
    parses and stores the whole tree, so a payload that skips the model version
    or the conditions would be rejected before any of that work happens, and
    would measure the validator instead of the write.
    """
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
