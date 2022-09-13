import logging

from redis.asyncio.client import Redis

from shvatka.models.config.db import RedisConfig

logger = logging.getLogger(__name__)


def create_redis(config: RedisConfig) -> Redis:
    logger.info("created redis for %s", config)
    return Redis(host=config.url, port=config.port, db=config.db)
