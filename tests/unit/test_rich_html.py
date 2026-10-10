from datetime import UTC, datetime

import pytest
from aiogram import types

from shvatka.core.models import enums
from shvatka.tgbot.views.hint_factory.rich_html import rich_message_to_html


def render(*blocks: types.RichBlockUnion) -> str:
    return rich_message_to_html(types.RichMessage(blocks=list(blocks))).html


def photo(file_id: str = "PHOTO_ID", **kwargs) -> types.RichBlockPhoto:
    return types.RichBlockPhoto(
        photo=[types.PhotoSize(file_id=file_id, file_unique_id="u", width=1, height=1)],
        **kwargs,
    )


def test_paragraph():
    assert render(types.RichBlockParagraph(text="загадка")) == "<p>загадка</p>"


def test_text_is_escaped():
    assert render(types.RichBlockParagraph(text="1 < 2 & 3")) == "<p>1 &lt; 2 &amp; 3</p>"


def test_heading_keeps_its_level():
    assert render(types.RichBlockSectionHeading(text="Глава", size=3)) == "<h3>Глава</h3>"


@pytest.mark.parametrize("size", [0, 7])
def test_heading_level_stays_within_html(size: int):
    html = render(types.RichBlockSectionHeading(text="Глава", size=size))

    assert html in ("<h1>Глава</h1>", "<h6>Глава</h6>")


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (types.RichTextBold(text="жирный"), "<b>жирный</b>"),
        (types.RichTextItalic(text="курсив"), "<i>курсив</i>"),
        (types.RichTextUnderline(text="подчёркнутый"), "<u>подчёркнутый</u>"),
        (types.RichTextStrikethrough(text="зачёркнутый"), "<s>зачёркнутый</s>"),
        (types.RichTextSpoiler(text="секрет"), "<tg-spoiler>секрет</tg-spoiler>"),
        (types.RichTextCode(text="code()"), "<code>code()</code>"),
        (types.RichTextMarked(text="важно"), "<mark>важно</mark>"),
        (types.RichTextSubscript(text="2"), "<sub>2</sub>"),
        (types.RichTextSuperscript(text="2"), "<sup>2</sup>"),
        (
            types.RichTextUrl(text="сайт", url="https://example.com"),
            '<a href="https://example.com">сайт</a>',
        ),
        (
            types.RichTextEmailAddress(text="почта", email_address="a@b.c"),
            '<a href="mailto:a@b.c">почта</a>',
        ),
        (
            types.RichTextCustomEmoji(custom_emoji_id="5443038", alternative_text="🔥"),
            '<tg-emoji emoji-id="5443038">🔥</tg-emoji>',
        ),
        (
            types.RichTextMathematicalExpression(expression="x^2"),
            "<tg-math>x^2</tg-math>",
        ),
    ],
)
def test_inline_nodes(node, expected: str):
    assert render(types.RichBlockParagraph(text=node)) == f"<p>{expected}</p>"


def test_nested_inline_nodes():
    text = ["обычный ", types.RichTextBold(text=["жирный ", types.RichTextItalic(text="курсив")])]

    assert render(types.RichBlockParagraph(text=text)) == (
        "<p>обычный <b>жирный <i>курсив</i></b></p>"
    )


def test_detected_entities_keep_only_their_text():
    # telegram finds a hashtag again on the way out, the markup need not say so
    text = types.RichTextHashtag(text="#схватка", hashtag="схватка")

    assert render(types.RichBlockParagraph(text=text)) == "<p>#схватка</p>"


def test_text_mention_becomes_a_user_link():
    user = types.User(id=42, is_bot=False, first_name="Гарри")
    text = types.RichTextTextMention(text="Гарри", user=user)

    assert (
        render(types.RichBlockParagraph(text=text)) == '<p><a href="tg://user?id=42">Гарри</a></p>'
    )


def test_date_time_keeps_its_text():
    text = types.RichTextDateTime(
        text="1 января",
        unix_time=int(datetime(2026, 1, 1, tzinfo=UTC).timestamp()),
        date_time_format="d MMMM",
    )

    assert render(types.RichBlockParagraph(text=text)) == "<p>1 января</p>"


def test_preformatted_with_language():
    block = types.RichBlockPreformatted(text="print(1)", language="python")

    assert render(block) == '<pre><code class="language-python">print(1)</code></pre>'


def test_preformatted_without_language():
    assert render(types.RichBlockPreformatted(text="text")) == "<pre><code>text</code></pre>"


def test_divider_and_footer():
    assert render(types.RichBlockDivider()) == "<hr/>"
    assert render(types.RichBlockFooter(text="подпись")) == "<footer>подпись</footer>"


def test_unordered_list():
    block = types.RichBlockList(
        items=[
            types.RichBlockListItem(label="•", blocks=[types.RichBlockParagraph(text="раз")]),
            types.RichBlockListItem(label="•", blocks=[types.RichBlockParagraph(text="два")]),
        ]
    )

    assert render(block) == "<ul><li><p>раз</p></li><li><p>два</p></li></ul>"


def test_numbered_list_keeps_its_numbers():
    block = types.RichBlockList(
        items=[
            types.RichBlockListItem(
                label="1.", blocks=[types.RichBlockParagraph(text="раз")], value=1
            ),
            types.RichBlockListItem(
                label="2.", blocks=[types.RichBlockParagraph(text="два")], value=2
            ),
        ]
    )

    assert render(block) == '<ol><li value="1"><p>раз</p></li><li value="2"><p>два</p></li></ol>'


def test_quotation_with_credit():
    block = types.RichBlockBlockQuotation(
        blocks=[types.RichBlockParagraph(text="цитата")], credit="автор"
    )

    assert render(block) == "<blockquote><p>цитата</p><cite>автор</cite></blockquote>"


def test_table():
    block = types.RichBlockTable(
        cells=[
            [types.RichBlockTableCell(align="left", valign="top", text="ключ", is_header=True)],
            [types.RichBlockTableCell(align="left", valign="top", text="SH123")],
        ],
        is_bordered=True,
    )

    assert render(block) == (
        "<table bordered>"
        '<tr><th align="left" valign="top">ключ</th></tr>'
        '<tr><td align="left" valign="top">SH123</td></tr>'
        "</table>"
    )


def test_details():
    block = types.RichBlockDetails(
        summary="подсказка", blocks=[types.RichBlockParagraph(text="ответ")], is_open=True
    )

    assert render(block) == "<details open><summary>подсказка</summary><p>ответ</p></details>"


def test_map():
    block = types.RichBlockMap(
        location=types.Location(latitude=55.75, longitude=37.61),
        zoom=16,
        width=600,
        height=400,
    )

    assert render(block) == (
        '<tg-map latitude="55.75" longitude="37.61" zoom="16" width="600" height="400"></tg-map>'
    )


def test_photo_becomes_a_media_link():
    rendered = rich_message_to_html(types.RichMessage(blocks=[photo()]))

    assert rendered.html == '<img src="tg://photo?id=media1"/>'
    assert len(rendered.media) == 1
    assert rendered.media[0].id == "media1"
    assert rendered.media[0].file_id == "PHOTO_ID"
    assert rendered.media[0].content_type == enums.HintType.photo


def test_spoilered_photo_stays_covered():
    rendered = rich_message_to_html(types.RichMessage(blocks=[photo(has_spoiler=True)]))

    assert rendered.html == '<tg-spoiler><img src="tg://photo?id=media1"/></tg-spoiler>'


def test_photo_caption():
    caption = types.RichBlockCaption(text="подпись", credit="автор")
    rendered = rich_message_to_html(types.RichMessage(blocks=[photo(caption=caption)]))

    assert rendered.html == (
        '<figure><img src="tg://photo?id=media1"/>'
        "<figcaption>подпись<cite>автор</cite></figcaption></figure>"
    )


def test_every_media_gets_its_own_id():
    video = types.RichBlockVideo(
        video=types.Video(file_id="VIDEO_ID", file_unique_id="u", width=1, height=1, duration=1)
    )
    voice = types.RichBlockVoiceNote(
        voice_note=types.Voice(file_id="VOICE_ID", file_unique_id="u", duration=1)
    )

    rendered = rich_message_to_html(types.RichMessage(blocks=[photo(), video, voice]))

    assert rendered.html == (
        '<img src="tg://photo?id=media1"/>'
        '<video src="tg://video?id=media2"></video>'
        '<audio src="tg://audio?id=media3"></audio>'
    )
    assert [m.id for m in rendered.media] == ["media1", "media2", "media3"]
    assert [m.file_id for m in rendered.media] == ["PHOTO_ID", "VIDEO_ID", "VOICE_ID"]
    # an animation travels as a video and a voice note as audio: telegram
    # addresses embedded media by three schemes only
    assert [m.content_type for m in rendered.media] == [
        enums.HintType.photo,
        enums.HintType.video,
        enums.HintType.voice,
    ]


def test_whole_message_renders_in_order():
    rendered = rich_message_to_html(
        types.RichMessage(
            blocks=[
                types.RichBlockSectionHeading(text="Загадка", size=1),
                types.RichBlockParagraph(
                    text=["найди ", types.RichTextBold(text="дом"), " на фото"]
                ),
                photo(),
            ]
        )
    )

    assert rendered.html == (
        "<h1>Загадка</h1>" "<p>найди <b>дом</b> на фото</p>" '<img src="tg://photo?id=media1"/>'
    )
