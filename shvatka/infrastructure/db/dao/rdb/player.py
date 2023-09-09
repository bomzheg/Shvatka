import typing
from typing import Iterable

from sqlalchemy import select, func, Result, case, delete, ScalarResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, contains_eager

from shvatka.core.models import dto, enums
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db import models
from .base import BaseDAO


class PlayerDao(BaseDAO[models.Player]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(models.Player, session)

    async def upsert_player(self, user: dto.User) -> dto.Player:
        try:
            return await self.get_by_user(user)
        except exceptions.PlayerNotFoundError:
            return await self.create_for_user(user)

    async def get_by_id(self, id_: int) -> dto.Player:
        player = await self._get_by_id(
            id_,
            (
                selectinload(models.Player.forum_user),
                selectinload(models.Player.user),
            ),
            populate_existing=True,
        )
        return player.to_dto_user_prefetched()

    async def get_player_with_stat(self, id_: int) -> dto.PlayerWithStat:
        result: Result[tuple[models.Player, int, int]] = await self.session.execute(
            select(
                models.Player,
                func.count(models.Player.typed_keys),
                func.count(
                    case(
                        (models.KeyTime.type_.in_([enums.KeyType.simple, enums.KeyType.bonus]), 1)
                    )
                ),
            )
            .outerjoin(models.Player.typed_keys)
            .options(
                selectinload(models.Player.forum_user),
                selectinload(models.Player.user),
            )
            .where(models.Player.id == id_)
            .group_by(models.Player.id)
        )
        (
            player,
            keys_total_count,
            keys_correct_count,
        ) = result.unique().one()  # type: models.Player, int, int
        return player.to_dto_user_prefetched().with_stat(
            typed_keys_count=keys_total_count,
            typed_correct_keys_count=keys_correct_count,
        )

    async def get_by_user(self, user: dto.User) -> dto.Player:
        return await self.get_by_user_id(user.tg_id)

    async def get_by_user_id(self, user_id: int) -> dto.Player:
        result: ScalarResult[models.Player] = await self.session.scalars(
            select(models.Player)
            .join(models.Player.user)
            .options(
                joinedload(models.Player.forum_user),
                contains_eager(models.Player.user),
            )
            .where(models.User.tg_id == user_id)
        )
        try:
            player = result.one()
        except NoResultFound as e:
            raise exceptions.PlayerNotFoundError from e
        if forum_user_db := player.forum_user:
            forum_user = forum_user_db.to_dto()
        else:
            forum_user = None
        return player.to_dto(user=player.user.to_dto(), forum_user=forum_user)

    async def create_for_user(self, user: dto.User) -> dto.Player:
        user_db = await self.session.get(models.User, user.db_id)
        assert user_db
        player = models.Player()
        user_db.player = player
        self._save(player)
        await self._flush(player)
        return player.to_dto(user=user)

    async def get_by_forum_player_name(self, name: str) -> dto.Player | None:
        result = await self.session.scalars(
            select(models.Player)
            .join(models.Player.forum_user)
            .options(
                selectinload(models.Player.forum_user),
                selectinload(models.Player.user),
            )
            .where(models.ForumUser.name == name)
        )
        try:
            return result.one().to_dto_user_prefetched()
        except NoResultFound:
            return None

    async def create_for_forum_user_name(self, forum_user_name: str) -> dto.Player:
        forum_user_db = models.ForumUser(name=forum_user_name)
        player = await self._create_dummy()
        forum_user_db.player = player
        self.session.add(forum_user_db)
        await self._flush(forum_user_db)
        return player.to_dto(forum_user=forum_user_db.to_dto())

    async def create_for_forum_user(self, user: dto.ForumUser) -> dto.Player:
        forum_user_db = await self.session.get(models.ForumUser, user.db_id)
        assert forum_user_db
        assert isinstance(forum_user_db, models.ForumUser)
        if forum_user_db.player_id:
            player = await self._get_by_id(typing.cast(int, forum_user_db.player_id))
        else:
            player = await self._create_dummy()
            forum_user_db.player = player
        return player.to_dto(forum_user=forum_user_db.to_dto())

    async def link_forum_user(self, player: dto.Player, user: dto.ForumUser) -> None:
        forum_user_db = await self.session.get(models.ForumUser, user.db_id)
        player_db = await self.get_by_id(player.id)
        assert forum_user_db is not None
        forum_user_db.player = player_db

    async def link_user(self, player: dto.Player, user: dto.User) -> None:
        user_db = await self.session.get(models.User, user.db_id)
        player_db = await self.get_by_id(player.id)
        assert user_db is not None
        user_db.player = player_db

    async def upsert_author_dummy(self) -> dto.Player:
        result = await self.session.scalars(
            select(models.Player).where(
                models.Player.is_dummy,
                models.Player.can_be_author,
            )
        )
        try:
            dummy = result.one()
        except NoResultFound:
            dummy = await self._create_dummy()
            dummy.can_be_author = True
        return dummy.to_dto()

    async def _create_dummy(self) -> models.Player:
        player = models.Player(is_dummy=True)
        self._save(player)
        await self._flush(player)
        return player

    async def promote(self, actor: dto.Player, target: dto.Player):
        target_player = await self._get_by_id(target.id)
        target_player.can_be_author = True
        target_player.promoted_by_id = actor.id

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        result = await self.session.execute(
            select(models.Player, models.TeamPlayer)
            .options(
                joinedload(models.Player.user),
                joinedload(models.Player.forum_user),
            )
            .join(models.Player.teams)
            .where(
                models.Player.id.in_(ids),
                models.TeamPlayer.date_left.is_(None),
            )
        )
        players = result.all()
        return [
            dto.VotedPlayer(
                player.to_dto_user_prefetched(),
                pit.to_dto(),
            )
            for player, pit in players
        ]

    async def delete(self, player: dto.Player) -> None:
        await self.session.execute(delete(models.Player).where(models.Player.id == player.id))
