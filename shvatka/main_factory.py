from dishka import Provider, Scope, AsyncContainer, provide
from dishka.exceptions import NoContextValueError

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.tgbot.services.identity import TgBotIdentityProvider


class IdpProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_idp(self, container: AsyncContainer) -> IdentityProvider:
        try:
            return await container.get(TgBotIdentityProvider)
        except NoContextValueError:
            return await container.get(ApiIdentityProvider)


def get_complex_only_providers() -> list[Provider]:
    return [
        IdpProvider(),
    ]
