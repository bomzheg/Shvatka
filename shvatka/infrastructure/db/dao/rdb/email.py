from datetime import datetime, tzinfo
import typing

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db import models
from .base import BaseDAO


class EmailAccountDao(BaseDAO[models.EmailAccount]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(models.EmailAccount, session, clock=clock)

    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        db_account = await self._get_by_email_or_none(email)
        return db_account.to_dto() if db_account is not None else None

    async def get_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        result = await self.session.scalars(
            select(models.EmailAccount).where(models.EmailAccount.player_id == player_id)
        )
        db_account = result.one_or_none()
        return db_account.to_dto() if db_account is not None else None

    async def is_email_occupied(self, email: str) -> bool:
        result = await self._get_by_email_or_none(email)
        return result is not None

    async def create_player_for_email(
        self, username: str, email: str, hashed_password: str
    ) -> dto.Player:
        player = models.Player(username=username, hashed_password=hashed_password)
        self._save(player)
        await self._flush(player)
        account = models.EmailAccount(email=email, player=player)
        self._save(account)
        await self._flush(account)
        return player.to_dto()

    async def add_email_to_player(self, player: dto.Player, email: str) -> dto.EmailAccount:
        player_db = await self.session.get(models.Player, player.id)
        assert player_db is not None
        account = models.EmailAccount(email=email, player=player_db)
        self._save(account)
        await self._flush(account)
        return account.to_dto()

    async def set_verified(self, email: str) -> None:
        account = await self._get_by_email_or_none(email)
        if account is None:
            raise exceptions.EmailNotFound(text=f"email {email} not found")
        account.is_verified = True

    async def get_verified_player_by_email(self, email: str) -> dto.PlayerWithCreds:
        result = await self.session.scalars(
            select(models.Player)
            .join(models.Player.email)
            .options(
                joinedload(models.Player.user),
                joinedload(models.Player.forum_user),
                contains_eager(models.Player.email),
            )
            .where(
                func.lower(models.EmailAccount.email) == email.lower(),
                models.EmailAccount.is_verified.is_(True),
            )
        )
        try:
            player = result.one()
        except NoResultFound as e:
            raise exceptions.EmailNotVerified(text=f"no verified email {email}") from e
        return player.to_dto_user_prefetched().add_password(player.hashed_password)

    async def _get_by_email_or_none(self, email: str) -> models.EmailAccount | None:
        result = await self.session.scalars(
            select(models.EmailAccount).where(func.lower(models.EmailAccount.email) == email.lower())
        )
        return result.one_or_none()
