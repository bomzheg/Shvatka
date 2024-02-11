import pytest
from dataclass_factory import Factory
from httpx import AsyncClient

from shvatka.api.dependencies import AuthProvider
from shvatka.api.models import responses
from shvatka.api.models.auth import Token
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.team import create_team_
from tests.mocks.game_log import GameLogWriterMock


@pytest.fixture
def token(user: dto.User, auth: AuthProvider) -> Token:
    return auth.create_user_token(user)


@pytest.mark.asyncio
async def test_get_team(
    client: AsyncClient,
    harry: dto.Player,
    token: Token,
    dao: HolderDao,
    game_log: GameLogWriterMock,
):
    team = await create_team_(harry, create_gryffindor_dto_chat(), dao, game_log)
    resp = await client.get(
        "/teams/my",
        cookies={"Authorization": f"{token.token_type} {token.access_token}"},
        follow_redirects=True,
    )
    assert resp.is_success
    dcf = Factory()
    resp.read()
    assert responses.Team.from_core(team) == dcf.load(resp.json(), responses.Team)
