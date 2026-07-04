from typing import NewType

from dishka import Provider, Scope, provide

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.superuser import check_is_superuser

# A player authorised as a superuser (admin panel operator). Depending on it in a
# route enforces the admin check before the body runs. Used by admin routes whose
# interactor is shared with public routes and so cannot self-check.
Superuser = NewType("Superuser", dto.Player)


class AdminProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_superuser(self, identity: ApiIdentityProvider, config: ApiConfig) -> Superuser:
        return Superuser(await check_is_superuser(identity, config.superusers))
