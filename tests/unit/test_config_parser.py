from datetime import timedelta
from pathlib import Path

from shvatka.api.app.config.parser.main import load_config as load_api_config
from shvatka.common import Paths
from shvatka.infrastructure.db.config.models.storage import StorageType
from shvatka.tgbot.config.models.bot import BotApiType
from shvatka.tgbot.config.models.main import TgBotConfig


def test_load_bot_config(bot_config: TgBotConfig):
    assert "shvatka-pytest" == bot_config.app.name
    assert [666, 46866565] == bot_config.superusers
    assert "123:ABC" == bot_config.bot.token
    assert -1001234567890 == bot_config.bot.log_chat
    assert -1009876543210 == bot_config.bot.game_log_chat
    assert [] == bot_config.bot.public_chats
    assert not bot_config.bot.enabled_capcha
    assert BotApiType.official == bot_config.bot.bot_api.type
    assert bot_config.bot.webhook is not None
    assert "my-$ecr3t" == bot_config.bot.webhook.secret  # never expanded as an env var
    assert StorageType.memory == bot_config.storage.type_
    assert bot_config.storage.redis is None
    assert "postgresql+asyncpg://test:test@localhost:5432/test" == bot_config.db.uri
    assert not bot_config.db.echo
    assert 1 == bot_config.redis.db
    assert "https://shvatka-test.bomzheg.dev" == bot_config.web.base_url
    # the docs domain is a deploy decision, so it is read from the file
    assert "https://docs.shvatka-test.bomzheg.dev/" == bot_config.docs.base_url
    assert "3.7.0" == bot_config.docs.version
    assert "shvatka" == bot_config.docs.component  # the file declares no component
    assert Path("local-storage/files") == bot_config.file_storage_config.path
    # the test config declares no mail section at all
    assert not bot_config.mail.enabled


def test_load_api_config(paths: Paths):
    config = load_api_config(paths)
    assert "" == config.api.context_path
    assert not config.api.enable_logging
    assert timedelta(minutes=30) == config.api.auth.token_expire
    assert "shvatkatestbot" == config.api.auth.bot_username
    # the file names no cookie domain, so the cookie is host-only
    assert config.api.auth.domain is None
    assert config.api.auth.cookie_domain is None
    assert "Authorization" == config.api.auth.cookie_name
    assert "none" == config.api.auth.samesite
    assert not config.api.auth.secure
    assert not config.api.auth.httponly
    assert not config.api.auth.disable_cors
    # the test config declares no push section at all
    assert not config.api.push.is_configured
    # the same top level sections are shared with the bot config
    assert [666, 46866565] == config.superusers
    assert "shvatka-pytest" == config.app.name
