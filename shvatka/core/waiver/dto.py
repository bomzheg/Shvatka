from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(kw_only=True, frozen=True, slots=True)
class TeamWaivers:
    team: dto.Team
    waivers: list[dto.Waiver]
