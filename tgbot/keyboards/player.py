from tgbot.services.inline_data import InlineData


class PromotePlayerID(InlineData, prefix="promote"):
    token: str

