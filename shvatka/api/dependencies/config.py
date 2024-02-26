from dishka import Provider, Scope, provide

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.config.models.main import ApiConfig
from shvatka.api.config.parser.main import load_config
from shvatka.common import Paths


class ApiConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def get_api_config(self, paths: Paths) -> ApiConfig:
        return load_config(paths)

    @provide
    def get_auth_config(self, config: ApiConfig) -> AuthConfig:
        return config.auth
