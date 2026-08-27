import pytest

from shvatka.core.models import dto


def _forum_user(name: str = "forum_harry", player_id: int = 3) -> dto.ForumUser:
    return dto.ForumUser(db_id=1, forum_id=7, name=name, registered=None, player_id=player_id)


def test_plain_player_does_not_carry_the_forum_identity():
    """The base dto must not grow the forum account back: it costs a join everywhere."""
    player = dto.Player(id=1, can_be_author=False, is_dummy=False, username="harry")
    assert not hasattr(player, "forum_user")
    assert not hasattr(player, "has_forum_user")
    assert not hasattr(player, "get_forum_name")


def test_player_with_forum_exposes_the_account():
    player = dto.PlayerWithForum(
        id=3, can_be_author=False, is_dummy=False, username="harry", forum_user=_forum_user()
    )
    assert player.has_forum_user()
    assert player.get_forum_name() == "forum_harry"


def test_player_with_forum_without_account():
    player = dto.PlayerWithForum(id=3, can_be_author=False, is_dummy=False, username="harry")
    assert not player.has_forum_user()
    assert player.get_forum_name() is None


def test_username_wins_over_forum_name_in_mention():
    player = dto.PlayerWithForum(
        id=3, can_be_author=True, is_dummy=True, username="harry", forum_user=_forum_user()
    )
    assert player.name_mention == "harry"


def test_forum_dummy_with_placeholder_username_is_mentioned_by_forum_name():
    player = dto.PlayerWithForum(
        id=3, can_be_author=False, is_dummy=True, username="id3", forum_user=_forum_user()
    )
    assert player.name_mention == "forum_harry"


def test_dummy_without_forum_account_falls_back_to_its_id():
    assert (
        dto.Player(id=3, can_be_author=False, is_dummy=True, username=None).name_mention
        == "dummy-3"
    )


@pytest.mark.parametrize("cls", [dto.Player, dto.PlayerWithForum])
def test_tg_accessors_are_shared(cls):
    user = dto.User(tg_id=100500, db_id=1, username="tg_harry", first_name="Harry")
    player = cls(id=8, can_be_author=False, is_dummy=False, username="harry", user=user)
    assert player.get_chat_id() == 100500
    assert player.get_tg_username() == "tg_harry"
