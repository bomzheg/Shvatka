import hashlib
import hmac
import json
from operator import itemgetter
from urllib.parse import parse_qsl

#
from aiogram.utils.web_app import check_webapp_signature

from shvatka.api.dependencies.auth import check_webapp_hash
from shvatka.api.models.auth import WebAppAuth

DATA = {
  "init_data": "user=%7B%22id%22%3A46866565%2C%22first_name%22%3A%22%D0%AE%D1%80%D0%B8%D0%B9%22%2C%22last_name%22%3A%22%D0%A7%D0%B5%D0%B1%D1%8B%D1%88%D0%B5%D0%B2%22%2C%22username%22%3A%22bomzheg%22%2C%22language_code%22%3A%22en%22%2C%22is_premium%22%3ATrue%2C%22allows_write_to_pm%22%3ATrue%7D&chat_instance=1078446451338474017&chat_type=private&auth_date=1716442837&hash=d783dfa46fda98e7d27c80c9293511edf347f340f94060c3407730b9c88b7737",
  "init_data_unsafe": {
    "user": {
      "id": 46866565,
      "first_name": "Юрий",
      "last_name": "Чебышев",
      "username": "bomzheg",
      "language_code": "en",
      "is_premium": True,
      "allows_write_to_pm": True
    },
    "chat_instance": "1078446451338474017",
    "chat_type": "private",
    "auth_date": "1716442837",
    "hash": "d783dfa46fda98e7d27c80c9293511edf347f340f94060c3407730b9c88b7737"
  },
  "version": "7.2",
  "platform": "weba",
  "colorScheme": "light",
  "themeParams": {
    "bg_color": "#ffffff",
    "text_color": "#000000",
    "hint_color": "#707579",
    "link_color": "#3390ec",
    "button_color": "#3390ec",
    "button_text_color": "#ffffff",
    "secondary_bg_color": "#f4f4f5",
    "header_bg_color": "#ffffff",
    "accent_text_color": "#3390ec",
    "section_bg_color": "#ffffff",
    "section_header_text_color": "#707579",
    "subtitle_text_color": "#707579",
    "destructive_text_color": "#e53935"
  },
  "isExpanded": True,
  "viewportHeight": 110.33333587646484,
  "viewportStableHeight": 110.33333587646484,
  "isClosingConfirmationEnabled": False,
  "headerColor": "#ffffff",
  "backgroundColor": "#ffffff",
  "BackButton": {
    "isVisible": False
  },
  "MainButton": {
    "text": "CONTINUE",
    "color": "#3390ec",
    "textColor": "#ffffff",
    "isVisible": False,
    "isProgressVisible": False,
    "isActive": True
  },
  "SettingsButton": {
    "isVisible": False
  },
  "HapticFeedback": {},
  "CloudStorage": {},
  "BiometricManager": {
    "isInited": False,
    "isBiometricAvailable": False,
    "biometricType": "unknown",
    "isAccessRequested": False,
    "isAccessGranted": False,
    "isBiometricTokenSaved": False,
    "deviceId": ""
  }
}


def check_webapp_signature(token: str, init_data: str) -> bool:
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        # Init data is not a valid query string
        return False
    if "hash" not in parsed_data:
        # Hash is not present in init data
        return False

    hash_ = parsed_data.pop('hash')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256
    )
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_


def test_hash():
    web_app = WebAppAuth.model_validate_json(json.dumps(DATA))
    assert check_webapp_signature("337833688:AAH-77xKGbpENReeI4TIL4LVYSYeKly3l-s", web_app.init_data)
    # check_webapp_hash(
    #   web_app.init_data,
    #   web_app.init_data_unsafe.hash,
    #   "337833688:AAH-77xKGbpENReeI4TIL4LVYSYeKly3l-s",
    # )
