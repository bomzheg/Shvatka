from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from src.infrastructure.db.models.base import Base
from src.shvatka.models import dto


class ForumTeam(Base):
    __tablename__ = "forum_teams"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    forum_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    url: Mapped[str]

    team_id = mapped_column(ForeignKey("teams.id"), unique=True, nullable=True)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="forum_team",
        uselist=False,
    )

    def __repr__(self):
        return f"<ForumName ID={self.id} name={self.name} >"

    def to_dto(self) -> dto.ForumTeam:
        return dto.ForumTeam(
            id=self.id,
            forum_id=self.forum_id,
            name=self.name,
            url=self.url,
        )
