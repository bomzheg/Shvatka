import pytest
import pytest_asyncio
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.dependencies import AuthProvider
from shvatka.api.models import responses
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user, set_password
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.team import create_team_
from tests.fixtures.user_constants import create_dto_harry


@pytest_asyncio.fixture
async def user(dao: HolderDao, auth: AuthProvider) -> dto.User:
    user_ = await upsert_user(create_dto_harry(), dao.user)
    password = auth.get_password_hash("12345")
    await set_password(user_, password, dao.user)
    return user_


@pytest.fixture
def token(user: dto.User, auth: AuthProvider) -> Token:
    return auth.create_user_token(user)


@pytest.mark.asyncio
async def test_get_team(
    client: AsyncClient, harry: dto.Player, token: Token, dao: HolderDao, game_log
):
    team = await create_team_(harry, create_gryffindor_dto_chat(), dao, game_log)
    resp = await client.get(
        "/teams/my",
        headers={"Authorization": "Bearer " + token.access_token},
        follow_redirects=True,
    )
    assert resp.is_success
    dcf = Factory()
    resp.read()
    assert responses.Team.from_core(team) == dcf.load(resp.json(), responses.Team)
