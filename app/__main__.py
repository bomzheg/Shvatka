import logging

from sqlalchemy.orm import close_all_sessions

from app.config import load_config
from app.config.logging_config import setup_logging
from app.main_factory import create_bot, create_dispatcher, get_paths

logger = logging.getLogger(__name__)


def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)

    dp = create_dispatcher(config)
    bot = create_bot(config)

    logger.info("started")
    try:
        dp.run_polling(bot)
    finally:
        close_all_sessions()
        logger.info("stopped")


if __name__ == '__main__':
    main()
