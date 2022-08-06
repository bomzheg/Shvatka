from dataclass_factory import Factory

from app.dao.holder import HolderDao
from app.models import dto
from app.services.scenario.game_ops import load_game


async def upsert_game(scn: dict, author: dto.Player, dao: HolderDao, dcf: Factory) -> dto.Game:
    game_scn = load_game(scn, dcf)
    game = await dao.game.upsert_game(author, game_scn)
    await dao.level.unlink_all(game)
    levels = []
    for number, level in enumerate(game_scn.levels):
        saved_level = await dao.level.upsert(author, level, game, number)
        levels.append(saved_level)
    game.levels = levels
    await dao.commit()
    return game
