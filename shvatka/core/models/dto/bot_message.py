from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BotMessage:
    """One message the bot posted, so it can be edited or removed later.

    Bookkeeping for a view, not part of anything the domain reasons about: a
    game, a request or a release never carries these — only the dao that keeps
    them and the telegram view that put them there ever look at one.
    """

    chat_id: int
    message_id: int
