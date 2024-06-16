from shvatka.common.config.models.main import WebConfig


class UrlFactory:
    def __init__(self, config: WebConfig):
        self.config = config

    def get_game_id_web_url(self, game_id: int) -> str:
        return f"{self.config.base_url}/games/{game_id}"
