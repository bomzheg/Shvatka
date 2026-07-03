import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import export_stat


def make_email_only_player() -> dto.Player:
    return dto.Player(id=7, can_be_author=False, is_dummy=False, username="harry")


def make_tg_player() -> dto.Player:
    user = dto.User(tg_id=100500, db_id=1, username="tg_harry", first_name="Harry")
    return dto.Player(id=8, can_be_author=False, is_dummy=False, username="harry_tg", user=user)


def test_email_only_player_has_no_chat_id():
    player = make_email_only_player()
    assert player.get_chat_id() is None
    assert player.get_tg_username() is None
    assert player.get_tech_chat_id(reserve_chat_id=-1000) == -1000
    assert player.name_mention == "harry"


def test_tg_player_accessors_unchanged():
    player = make_tg_player()
    assert player.get_chat_id() == 100500
    assert player.get_tg_username() == "tg_harry"
    assert player.get_tech_chat_id(reserve_chat_id=-1000) == 100500


def test_export_stat_player_by_username():
    exported = export_stat.Player.from_dto(make_email_only_player())
    assert exported.identity == export_stat.PlayerIdentity.username
    assert exported.username == "harry"
    assert exported.tg_user_id is None
    assert exported.forum_name is None


def test_export_stat_player_without_any_identity():
    player = dto.Player(id=9, can_be_author=False, is_dummy=True, username=None)
    with pytest.raises(RuntimeError):
        export_stat.Player.from_dto(player)
