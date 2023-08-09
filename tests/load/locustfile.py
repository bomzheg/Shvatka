from locust import HttpUser, task, between  # type: ignore[import]  # now locust is just PoC


class PlayerUser(HttpUser):
    wait_time = between(1, 5)
    token: str = ""

    @task
    def me(self) -> None:
        self.client.get(
            "/users/me",
            headers={"Authorization": "Bearer " + self.token},
        )

    @task
    def active_game(self) -> None:
        self.client.get("/games/active")

    def on_start(self) -> None:
        with self.client.post(
            "/auth/token", data={"username": "bomzheg", "password": "12345"}
        ) as resp:
            assert resp.ok
            self.token = resp.json()["access_token"]
