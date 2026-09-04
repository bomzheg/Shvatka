from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BotMessage:
    chat_id: int
    message_id: int
