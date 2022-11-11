from tgbot.services.inline_data import InlineData


class AddGameOrg(InlineData, prefix="add_game_org"):
    # TODO add redis saved token_urlsafe with control data
    game_manage_token: str
    game_id: int
    inviter_id: int
