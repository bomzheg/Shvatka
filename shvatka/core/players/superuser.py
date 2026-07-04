"""Admin-panel authorisation for the domain layer.

Superusers are configured by telegram id (see ``Config.superusers``). Admin
interactors receive the set via DI and resolve the acting player through the
``IdentityProvider``, so the authorisation check lives with the use case rather
than only at the transport edge.
"""

from typing import Collection, NewType

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.utils import exceptions

# tg ids allowed to use the admin panel; provided from Config.superusers.
Superusers = NewType("Superusers", frozenset[int])


async def check_is_superuser(
    identity: IdentityProvider, superusers: Collection[int]
) -> dto.Player:
    """Resolve the acting player and ensure they are a superuser, or raise."""
    player = await identity.get_required_player()
    user = await identity.get_user()
    if user is None or user.tg_id not in superusers:
        raise exceptions.NotAuthorizedForAdmin(player=player, user=user)
    return player
