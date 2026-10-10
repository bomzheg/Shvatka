import enum


class RichFormat(enum.Enum):
    """Markup language a rich hint is written in.

    Telegram accepts a rich message either as Rich HTML or as Rich Markdown
    (GitHub flavoured), never both at once, so the hint says which one it is.
    """

    html = "html"
    markdown = "markdown"
