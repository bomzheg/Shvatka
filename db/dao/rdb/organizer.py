from sqlalchemy import update, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from db import models
from shvatka.models import dto
from shvatka.models.enums.org_permission import OrgPermission
from .base import BaseDAO


class OrganizerDao(BaseDAO[models.Organizer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Organizer, session)

    async def get_orgs(self, game: dto.Game) -> list[dto.SecondaryOrganizer]:
        orgs = await self._get_orgs(game)
        return [
            org.to_dto(
                player=org.player.to_dto_user_prefetched(),
                game=game,
            )
            for org in orgs
        ]

    async def get_orgs_count(self, game: dto.Game) -> int:
        return len(await self._get_orgs(game)) + 1

    async def add_new(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        org = models.Organizer(
            game_id=game.id,
            player_id=player.id
        )
        self._save(org)
        await self._flush(org)
        return org.to_dto(player=player, game=game)

    async def get_by_id(self, id_: int) -> dto.SecondaryOrganizer:
        options = [
            joinedload(models.Organizer.player).joinedload(models.Player.user),
            joinedload(models.Organizer.game).joinedload(models.Game.author).joinedload(models.Player.user),
        ]
        result = await self._get_by_id(id_, options)
        return result.to_dto(
            player=result.player.to_dto_user_prefetched(),
            game=result.game.to_dto(author=result.game.author.to_dto_user_prefetched()),
        )

    async def flip_permission(self, org: dto.SecondaryOrganizer, permission: OrgPermission):
        await self.session.execute(
            update(models.Organizer)
            .where(models.Organizer.id == org.id)
            .values(**{permission.name: not_(getattr(models.Organizer, permission.name))})
        )

    async def _get_orgs(self, game: dto.Game) -> list[models.Organizer]:
        result = await self.session.execute(
            select(models.Organizer)
            .where(models.Organizer.game_id == game.id)
            .options(
                joinedload(models.Organizer.player)
                .joinedload(models.Player.user)
            )
        )
        return result.scalars().all()
