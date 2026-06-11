from dishka import Provider, provide

from shvatka.api.dependencies.api_only import MockUsedOneTimeTokenInteractor
from shvatka.infrastructure.bus.in_memory import UsedOneTimeTokenInteractor


class InfrastructureProvider(Provider):
    @provide
    def ott_provider(self) -> UsedOneTimeTokenInteractor:
        return MockUsedOneTimeTokenInteractor()


def get_infra_only_providers() -> list[Provider]:
    return [InfrastructureProvider()]
