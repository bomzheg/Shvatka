from typing import BinaryIO

from db.dao import FileInfoDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models.dto.scn.hint_part import BaseHint, TextHint, GPSHint, ContactHint, PhotoHint, VenueHint
from tgbot.models.hint import BaseHintLinkView, BaseHintContentView, TextHintView, GPSHintView, ContactHintView, \
    PhotoLinkView, PhotoContentView, VenueHintView


class HintContentResolver:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage):
        self.dao = dao
        self.storage = file_storage

    async def resolve_link(self, hint: BaseHint) -> BaseHintLinkView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case VenueHint(
                latitude=latitude,
                longitude=longitude,
                title=title,
                address=address,
                foursquare_id=foursquare_id,
                foursquare_type=foursquare_type,
            ):
                VenueHintView(
                    latitude=latitude,
                    longitude=longitude,
                    title=title,
                    address=address,
                    foursquare_id=foursquare_id,
                    foursquare_type=foursquare_type,
                )
            case PhotoHint(file_guid=guid, caption=caption):
                return PhotoLinkView(file_id=await self._resolve_file_id(guid), caption=caption)
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

    async def _resolve_file_id(self, guid: str) -> str:
        tg_link = (await self.dao.get_by_guid(guid)).tg_link
        return tg_link.file_id

    async def resolve_content(self, hint: BaseHint) -> BaseHintContentView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case VenueHint(
                latitude=latitude,
                longitude=longitude,
                title=title,
                address=address,
                foursquare_id=foursquare_id,
                foursquare_type=foursquare_type,
            ):
                VenueHintView(
                    latitude=latitude,
                    longitude=longitude,
                    title=title,
                    address=address,
                    foursquare_id=foursquare_id,
                    foursquare_type=foursquare_type,
                )
            case PhotoHint(file_guid=guid, caption=caption):
                return PhotoContentView(content=await self._resolve_bytes(guid), caption=caption)
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

    async def _resolve_bytes(self, guid: str) -> BinaryIO:
        file_info = await self.dao.get_by_guid(guid)
        return await self.storage.get(file_info.file_content_link)

