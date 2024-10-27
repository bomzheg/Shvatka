from base64 import b64encode
from typing import Any


def obfuscate_sensitive(information: Any) -> str:
    return b64encode(str(information).encode("utf8")).decode("utf8")
