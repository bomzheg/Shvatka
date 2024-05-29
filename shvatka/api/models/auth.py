from datetime import datetime

from pydantic import BaseModel

from shvatka.core.models import dto


class WebAppUser(BaseModel):
    id: int
    first_name: str
    is_bot: bool | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    added_to_attachment_menu: bool | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None


class WebAppInitData(BaseModel):
    user: WebAppUser
    auth_date: datetime
    hash: str
    start_param: str | None = None
    query_id: str | None = None


class WebAppAuth(BaseModel):
    init_data: str
    init_data_unsafe: WebAppInitData


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
        data = self.model_dump(exclude={"hash"}, exclude_none=True, exclude_unset=True)
        data["auth_date"] = int(self.auth_date.timestamp())
        return "\n".join([f"{key}={data[key]}" for key in sorted(data.keys()) if data.get(key)])


class Token(BaseModel):
    access_token: str
    token_type: str
