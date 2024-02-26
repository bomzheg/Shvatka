from locust import HttpUser, task, between  # type: ignore[import, unused-ignore]


class PlayerUser(HttpUser):
    wait_time = between(1, 5)
    token: str = ""

    @task
    def me(self) -> None:
        self.client.get(
            "/users/me",
            cookies={"Authorization": self.token},
        )

    @task
    def active_game(self) -> None:
        self.client.get("/games/active")

    def on_start(self) -> None:
        with self.client.post(
            "/auth/token", data={"username": "bomzheg", "password": "1234"}
        ) as resp:
            assert resp.ok
            self.token = resp.cookies["Authorization"]
