from aiogram import Bot


class BotAlert:
    def __init__(self, bot: Bot, log_chat_id: int):
        self.bot = bot
        self.log_chat_id = log_chat_id

    async def alert(self, text: str):
        await self.bot.send_message(self.log_chat_id, text)
