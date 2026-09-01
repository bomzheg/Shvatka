from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(kw_only=True, frozen=True, slots=True)
class TeamWaivers:
    """One team's waivers for one game, with the team they belong to.

    The team travels next to the list rather than being read off the first
    waiver, so a team whose last waiver was just removed is still answered for.
    """

    team: dto.Team
    waivers: list[dto.Waiver]
