import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# MIME types (as reported by libmagic) that browsers and Telegram can't display
# inline but that we can transcode to JPEG.
HEIC_MIME_TYPES = frozenset(
    {
        "image/heic",
        "image/heif",
        "image/heic-sequence",
        "image/heif-sequence",
    }
)

JPEG_MIME_TYPE = "image/jpeg"
JPEG_EXTENSION = ".jpg"


def is_heic(mime_type: str | None) -> bool:
    return mime_type is not None and mime_type.lower() in HEIC_MIME_TYPES


def convert_heic_to_jpeg(data: bytes) -> bytes:
    """Transcode HEIC/HEIF image bytes to JPEG.

    Returns the original bytes unchanged if the conversion can't be performed
    (missing optional dependency, corrupted image, unsupported feature); the
    caller decides what to do with an unconverted file based on its upload policy.
    """
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        from PIL import Image
    except ImportError:
        logger.warning("can't convert HEIC to JPEG: pillow-heif is not installed")
        return data
    try:
        with Image.open(BytesIO(data)) as image:
            rgb_image = image.convert("RGB")
            out = BytesIO()
            rgb_image.save(out, format="JPEG", quality=90)
        return out.getvalue()
    except Exception:
        logger.exception("failed to convert HEIC image to JPEG")
        return data
