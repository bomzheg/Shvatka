from datetime import datetime

from pydantic import BaseModel

from shvatka.core.models import dto


class UserTgAuth(BaseModel):
    id: int
    first_name: str
    auth_date: datetime
    hash: str
    photo_url: str | None = None
    username: str | None = None
    last_name: str | None = None

    def to_dto(self):
        return dto.User(
            tg_id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            is_bot=False,
        )

    def to_tg_spec(self) -> str:
        data = self.dict(exclude={"hash"})
        data["auth_date"] = int(self.auth_date.timestamp())
        return "\n".join([f"{key}={data[key]}" for key in sorted(data.keys()) if data.get(key)])


class Token(BaseModel):
    access_token: str
    token_type: str
