from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao


async def fill_all_file_id(dao: FileInfoDao, file_gateway: BotFileGateway):
    while batch := await dao.get_without_file_id(100):
        for file in batch:
            await file_gateway.renew_file_id(file.author, file)
