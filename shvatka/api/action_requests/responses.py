import typing
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping

from shvatka.core.notifications.dto import ActionRequest as ActionRequestDto


@dataclass(kw_only=True, frozen=True, slots=True)
class ActionRequest:
    id: int
    type: str
    status: str
    initiator_id: int
    target_player_id: int | None
    team_id: int | None
    game_id: int | None
    payload: Mapping[str, typing.Any]
    created_at: datetime
    responded_at: datetime | None

    @classmethod
    def from_core(cls, core: ActionRequestDto) -> "ActionRequest":
        return cls(
            id=core.id,
            type=core.type.name,
            status=core.status.name,
            initiator_id=core.initiator_id,
            target_player_id=core.target_player_id,
            team_id=core.team_id,
            game_id=core.game_id,
            payload=core.payload,
            created_at=core.created_at,
            responded_at=core.responded_at,
        )
