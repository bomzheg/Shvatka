from io import BytesIO

import pytest
from aiogram.types import BufferedInputFile, InputMediaPhoto, InputMediaVideo

from shvatka.core.models import enums
from shvatka.core.utils import exceptions
from shvatka.tgbot.models.hint import RichHintContentView, RichHintLinkView, RichMediaView

HTML = '<h1>Загадка</h1><p>смотри <img src="pic"></p>'
MARKDOWN = "# Загадка\n\nсмотри ![](pic)"


def link_view(**kwargs) -> RichHintLinkView:
    kwargs.setdefault("text", HTML)
    kwargs.setdefault("format", enums.RichFormat.html)
    kwargs.setdefault("media", [])
    return RichHintLinkView(**kwargs)


def test_html_goes_to_html_field():
    rich_message = link_view().kwargs()["rich_message"]

    assert rich_message.html == HTML
    assert rich_message.markdown is None
    assert rich_message.media is None


def test_markdown_goes_to_markdown_field():
    rich_message = link_view(text=MARKDOWN, format=enums.RichFormat.markdown).kwargs()[
        "rich_message"
    ]

    assert rich_message.markdown == MARKDOWN
    assert rich_message.html is None


def test_flags_are_passed_as_is():
    rich_message = link_view(is_rtl=True, skip_entity_detection=True).kwargs()["rich_message"]

    assert rich_message.is_rtl is True
    assert rich_message.skip_entity_detection is True


def test_media_sent_by_file_id():
    view = link_view(
        media=[RichMediaView(id="pic", content_type=enums.HintType.photo, file_id="FILE_ID")]
    )

    rich_message = view.kwargs()["rich_message"]

    assert not view.is_file_id_missing()
    assert len(rich_message.media) == 1
    assert rich_message.media[0].id == "pic"
    assert rich_message.media[0].media == InputMediaPhoto(media="FILE_ID")


def test_media_sent_by_content():
    view = RichHintContentView(
        text=HTML,
        format=enums.RichFormat.html,
        media=[
            RichMediaView(
                id="clip",
                content_type=enums.HintType.video,
                content=BufferedNamedIO(b"12345"),
            )
        ],
    )

    media = view.kwargs()["rich_message"].media[0].media

    assert isinstance(media, InputMediaVideo)
    assert isinstance(media.media, BufferedInputFile)
    assert media.media.data == b"12345"


def test_missing_file_id_falls_back_to_content():
    view = link_view(
        media=[
            RichMediaView(id="pic", content_type=enums.HintType.photo, file_id="FILE_ID"),
            RichMediaView(id="clip", content_type=enums.HintType.video, file_id=None),
        ]
    )

    assert view.is_file_id_missing()


def test_no_media_is_always_sendable_by_link():
    assert not link_view().is_file_id_missing()


@pytest.mark.parametrize("content_type", [enums.HintType.document, enums.HintType.sticker, None])
def test_unsupported_media_type_rejected(content_type: enums.HintType | None):
    view = link_view(media=[RichMediaView(id="doc", content_type=content_type, file_id="FILE_ID")])

    with pytest.raises(exceptions.UnsupportedFileFormat):
        view.kwargs()


class BufferedNamedIO(BytesIO):
    @property
    def name(self) -> str:
        return "clip.mp4"
