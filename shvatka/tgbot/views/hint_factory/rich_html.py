"""Rich message -> Rich HTML, the way ``Message.html_text`` renders entities.

Telegram takes a rich message as markup (``InputRichMessage.html``) but gives it
back as parsed blocks (``Message.rich_message``), and aiogram has no way back:
``Message.html_text`` unparses ``text`` + entities, which a rich message has
none of. This module is that way back, so an incoming rich message can be stored
as the markup a ``RichHint`` keeps.

Every block renders as the HTML tag the Bot API documents for it (``<p>`` for a
paragraph, ``<table>`` for a table, ``<tg-map>`` for a map, ...). Inline nodes
follow telegram's usual HTML formatting - ``<b>``, ``<i>``, ``<a href>``,
``<tg-spoiler>``, ``<tg-emoji>``. Nodes that only mark up text telegram detects
by itself (mentions, hashtags, phone numbers, bank cards, bot commands) render
as their plain text: with entity detection left on, telegram finds them again
when the message goes back out.

Media blocks carry files rather than markup. They are rendered as the
``tg://photo?id=`` / ``tg://video?id=`` / ``tg://audio?id=`` links telegram
resolves against the ``media`` list, and the files behind them are returned
alongside the html for the caller to store - rendering itself stays pure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from aiogram import types

from shvatka.core.models import enums

MEDIA_ID_PREFIX = "media"
"""Ids are generated as media1, media2, ... - telegram allows 1-64 chars of
``A-Za-z0-9_-`` in a media id, and a running number stays well inside that."""

_MEDIA_SCHEME: dict[enums.HintType, str] = {
    enums.HintType.photo: "photo",
    enums.HintType.video: "video",
    enums.HintType.animation: "video",
    enums.HintType.audio: "audio",
    enums.HintType.voice: "audio",
}
"""Telegram addresses embedded media by three link schemes only, so an
animation travels as a video and a voice note as audio."""

_MEDIA_TAG: dict[enums.HintType, str] = {
    enums.HintType.photo: "img",
    enums.HintType.video: "video",
    enums.HintType.animation: "video",
    enums.HintType.audio: "audio",
    enums.HintType.voice: "audio",
}

_TEXT_TAGS: dict[type, str] = {
    types.RichTextBold: "b",
    types.RichTextItalic: "i",
    types.RichTextUnderline: "u",
    types.RichTextStrikethrough: "s",
    types.RichTextSpoiler: "tg-spoiler",
    types.RichTextCode: "code",
    types.RichTextMarked: "mark",
    types.RichTextSubscript: "sub",
    types.RichTextSuperscript: "sup",
}


@dataclass(kw_only=True, slots=True, frozen=True)
class RichMediaSource:
    """A file the rendered markup points at, and where to fetch it from."""

    id: str
    file_id: str
    content_type: enums.HintType


@dataclass(kw_only=True, slots=True)
class RenderedRichMessage:
    html: str
    media: list[RichMediaSource] = field(default_factory=list)


def rich_message_to_html(rich_message: types.RichMessage) -> RenderedRichMessage:
    """Render an incoming rich message as the Rich HTML it came from."""
    renderer = _Renderer()
    html = renderer.blocks(rich_message.blocks)
    return RenderedRichMessage(html=html, media=renderer.media)


class _Renderer:
    def __init__(self) -> None:
        self.media: list[RichMediaSource] = []

    # -----------------------------------------------------------------
    # blocks
    # -----------------------------------------------------------------

    def blocks(self, blocks: list) -> str:
        return "".join(self.block(block) for block in blocks)

    def block(self, block) -> str:
        match block:
            case types.RichBlockParagraph():
                return f"<p>{self.text(block.text)}</p>"
            case types.RichBlockSectionHeading():
                level = min(max(block.size, 1), 6)
                return f"<h{level}>{self.text(block.text)}</h{level}>"
            case types.RichBlockPreformatted():
                return self._preformatted(block)
            case types.RichBlockFooter():
                return f"<footer>{self.text(block.text)}</footer>"
            case types.RichBlockDivider():
                return "<hr/>"
            case types.RichBlockMathematicalExpression():
                return f"<tg-math-block>{escape(block.expression)}</tg-math-block>"
            case types.RichBlockAnchor():
                return f'<a name="{escape(block.name, quote=True)}"></a>'
            case types.RichBlockList():
                return self._list(block)
            case types.RichBlockBlockQuotation():
                quoted = self.blocks(block.blocks) + self._credit(block.credit)
                return f"<blockquote>{quoted}</blockquote>"
            case types.RichBlockPullQuotation():
                return f"<aside>{self.text(block.text)}{self._credit(block.credit)}</aside>"
            case types.RichBlockCollage():
                return self._grouped("tg-collage", block)
            case types.RichBlockSlideshow():
                return self._grouped("tg-slideshow", block)
            case types.RichBlockTable():
                return self._table(block)
            case types.RichBlockDetails():
                return self._details(block)
            case types.RichBlockMap():
                return self._map(block)
            case types.RichBlockPhoto():
                return self._media(block.photo[-1].file_id, enums.HintType.photo, block)
            case types.RichBlockVideo():
                return self._media(block.video.file_id, enums.HintType.video, block)
            case types.RichBlockAnimation():
                return self._media(block.animation.file_id, enums.HintType.animation, block)
            case types.RichBlockAudio():
                return self._media(block.audio.file_id, enums.HintType.audio, block)
            case types.RichBlockVoiceNote():
                return self._media(block.voice_note.file_id, enums.HintType.voice, block)
            case types.RichBlockThinking():
                return f"<tg-thinking>{self.text(block.text)}</tg-thinking>"
            case _:
                # a block type newer than this code: keep whatever text it has
                return f"<p>{self.text(getattr(block, 'text', ''))}</p>"

    def _preformatted(self, block: types.RichBlockPreformatted) -> str:
        code = self.text(block.text)
        if block.language:
            language = escape(block.language, quote=True)
            return f'<pre><code class="language-{language}">{code}</code></pre>'
        return f"<pre><code>{code}</code></pre>"

    def _list(self, block: types.RichBlockList) -> str:
        # only a numbered list carries values; an unordered one has none
        ordered = any(item.value is not None for item in block.items)
        tag = "ol" if ordered else "ul"
        items = "".join(self._list_item(item) for item in block.items)
        return f"<{tag}>{items}</{tag}>"

    def _list_item(self, item: types.RichBlockListItem) -> str:
        attributes = ""
        if item.value is not None:
            attributes += f' value="{item.value}"'
        if item.has_checkbox:
            checked = " checked" if item.is_checked else ""
            attributes += f' type="checkbox"{checked}'
        return f"<li{attributes}>{self.blocks(item.blocks)}</li>"

    def _grouped(self, tag: str, block) -> str:
        return f"<{tag}>{self.blocks(block.blocks)}{self._caption(block.caption)}</{tag}>"

    def _table(self, block: types.RichBlockTable) -> str:
        attributes = ""
        if block.is_bordered:
            attributes += " bordered"
        if block.is_striped:
            attributes += " striped"
        caption = f"<caption>{self.text(block.caption)}</caption>" if block.caption else ""
        rows = "".join(
            f"<tr>{''.join(self._cell(cell) for cell in row)}</tr>" for row in block.cells
        )
        return f"<table{attributes}>{caption}{rows}</table>"

    def _cell(self, cell: types.RichBlockTableCell) -> str:
        tag = "th" if cell.is_header else "td"
        attributes = ""
        if cell.align:
            attributes += f' align="{escape(cell.align, quote=True)}"'
        if cell.valign:
            attributes += f' valign="{escape(cell.valign, quote=True)}"'
        if cell.colspan:
            attributes += f' colspan="{cell.colspan}"'
        if cell.rowspan:
            attributes += f' rowspan="{cell.rowspan}"'
        return f"<{tag}{attributes}>{self.text(cell.text)}</{tag}>"

    def _details(self, block: types.RichBlockDetails) -> str:
        open_ = " open" if block.is_open else ""
        summary = f"<summary>{self.text(block.summary)}</summary>"
        return f"<details{open_}>{summary}{self.blocks(block.blocks)}</details>"

    def _map(self, block: types.RichBlockMap) -> str:
        attributes = (
            f' latitude="{block.location.latitude}" longitude="{block.location.longitude}"'
            f' zoom="{block.zoom}" width="{block.width}" height="{block.height}"'
        )
        return f"<tg-map{attributes}>{self._caption(block.caption)}</tg-map>"

    def _media(self, file_id: str, content_type: enums.HintType, block) -> str:
        source = RichMediaSource(
            id=f"{MEDIA_ID_PREFIX}{len(self.media) + 1}",
            file_id=file_id,
            content_type=content_type,
        )
        self.media.append(source)
        tag = _MEDIA_TAG[content_type]
        link = f"tg://{_MEDIA_SCHEME[content_type]}?id={source.id}"
        element = f'<{tag} src="{link}"></{tag}>' if tag != "img" else f'<img src="{link}"/>'
        if getattr(block, "has_spoiler", None):
            element = f"<tg-spoiler>{element}</tg-spoiler>"
        caption = self._caption(getattr(block, "caption", None))
        return f"<figure>{element}{caption}</figure>" if caption else element

    def _caption(self, caption: types.RichBlockCaption | None) -> str:
        if caption is None:
            return ""
        return f"<figcaption>{self.text(caption.text)}{self._credit(caption.credit)}</figcaption>"

    def _credit(self, credit) -> str:
        if credit is None:
            return ""
        return f"<cite>{self.text(credit)}</cite>"

    # -----------------------------------------------------------------
    # inline text
    # -----------------------------------------------------------------

    def text(self, text) -> str:
        if text is None:
            return ""
        if isinstance(text, str):
            return escape(text)
        if isinstance(text, list):
            return "".join(self.text(part) for part in text)

        if (tag := _TEXT_TAGS.get(type(text))) is not None:
            return f"<{tag}>{self.text(text.text)}</{tag}>"

        match text:
            case types.RichTextUrl():
                return self._link(text.url, self.text(text.text))
            case types.RichTextEmailAddress():
                return self._link(f"mailto:{text.email_address}", self.text(text.text))
            case types.RichTextPhoneNumber():
                return self._link(f"tel:{text.phone_number}", self.text(text.text))
            case types.RichTextTextMention():
                return self._link(f"tg://user?id={text.user.id}", self.text(text.text))
            case types.RichTextAnchorLink():
                return self._link(f"#{text.anchor_name}", self.text(text.text))
            case types.RichTextAnchor():
                return f'<a name="{escape(text.name, quote=True)}"></a>'
            case types.RichTextCustomEmoji():
                emoji_id = escape(text.custom_emoji_id, quote=True)
                return (
                    f'<tg-emoji emoji-id="{emoji_id}">{escape(text.alternative_text)}</tg-emoji>'
                )
            case types.RichTextMathematicalExpression():
                return f"<tg-math>{escape(text.expression)}</tg-math>"
            case _:
                # everything else marks up text telegram detects on its own
                # (mentions, hashtags, cashtags, bot commands, bank cards,
                # dates, references) - the plain text is enough to send back
                return self.text(getattr(text, "text", ""))

    def _link(self, href: str, text: str) -> str:
        return f'<a href="{escape(href, quote=True)}">{text}</a>'
