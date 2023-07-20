from locust import HttpUser, task


class PlayerUser(HttpUser):
    token: str = ""

    @task
    def me(self) -> None:
        self.client.get(
            "/users/me",
            headers={"Authorization": "Bearer " + self.token},
        )

    def on_start(self) -> None:
        with self.client.post(
            "/auth/token", data={"username": "bomzheg", "password": "12345"}
        ) as resp:
            assert resp.ok
            self.token = resp.json()["access_token"]
