from shvatka.api.players import responses
from shvatka.core.models import dto


def test_me_from_core_tg_only():
    user = dto.User(tg_id=100500, db_id=1, username="tg_harry", first_name="Harry")
    player = dto.PlayerWithForum(
        id=1, can_be_author=False, is_dummy=False, username="harry", user=user
    )

    me = responses.PlayerWithIdentities.from_core(player, email=None)

    assert me.id == 1
    assert me.tg is not None
    assert me.tg.tg_id == 100500
    assert me.forum is None
    assert me.email is None


def test_me_from_core_email_only():
    player = dto.PlayerWithForum(id=2, can_be_author=False, is_dummy=False, username="mail_user")
    email = dto.EmailAccount(email="user@example.com", player_id=2, is_verified=True, db_id=948)

    me = responses.PlayerWithIdentities.from_core(player, email=email)

    assert me.tg is None
    assert me.forum is None
    assert me.email is not None
    assert me.email.email == "user@example.com"
    assert me.email.is_verified is True


def test_me_from_core_forum_and_unverified_email():
    forum = dto.ForumUser(db_id=1, forum_id=7, name="forum_harry", registered=None, player_id=3)
    player = dto.PlayerWithForum(
        id=3, can_be_author=False, is_dummy=False, username="harry", forum_user=forum
    )
    email = dto.EmailAccount(email="h@example.com", player_id=3, is_verified=False, db_id=918)

    me = responses.PlayerWithIdentities.from_core(player, email=email)

    assert me.tg is None
    assert me.forum is not None
    assert me.forum.name == "forum_harry"
    assert me.email is not None
    assert me.email.is_verified is False


def test_me_pending_email_is_the_address_being_moved_to():
    player = dto.PlayerWithForum(id=4, can_be_author=False, is_dummy=False, username="harry")
    email = dto.EmailAccount(email="old@example.com", player_id=4, is_verified=True, db_id=1)

    me = responses.PlayerWithIdentities.from_core(
        player, email=email, pending_email="new@example.com"
    )

    assert me.email is not None
    assert me.email.email == "old@example.com"
    assert me.pending_email == "new@example.com"


def test_me_pending_email_ignores_the_linked_address_itself():
    player = dto.PlayerWithForum(id=5, can_be_author=False, is_dummy=False, username="harry")
    email = dto.EmailAccount(email="h@example.com", player_id=5, is_verified=False, db_id=2)

    me = responses.PlayerWithIdentities.from_core(
        player, email=email, pending_email="h@example.com"
    )

    assert me.pending_email is None
