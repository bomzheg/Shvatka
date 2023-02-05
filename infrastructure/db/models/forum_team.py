from sqlalchemy import Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship, mapped_column

from infrastructure.db.models.base import Base
from shvatka.models import dto


class ForumTeam(Base):
    __tablename__ = "forum_teams"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(BigInteger, primary_key=True)
    name = mapped_column(Text, nullable=True)

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
            name=self.name,
        )
