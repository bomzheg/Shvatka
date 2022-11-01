from db.dao import FileInfoDao
from shvatka.models.dto.scn.hint_part import BaseHint, TextHint, GPSHint, ContactHint
from tgbot.models.hint import BaseHintLinkView, BaseHintContentView, TextHintView, GPSHintView, ContactHintView


class HintContentResolver:
    def __init__(self, dao: FileInfoDao):
        self.dao = dao

    @staticmethod
    async def resolve_link(hint: BaseHint) -> BaseHintLinkView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case ContactHint(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                vcard=vcard,
            ):
                return ContactHintView(
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    vcard=vcard,
                )

    @staticmethod
    async def resolve_content(hint: BaseHint) -> BaseHintContentView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case ContactHint(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                vcard=vcard,
            ):
                return ContactHintView(
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    vcard=vcard,
                )

