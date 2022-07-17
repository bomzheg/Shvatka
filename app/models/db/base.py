from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.models.config.db import DBConfig


Base = declarative_base()


def create_pool(db_config: DBConfig) -> sessionmaker:
    engine = create_async_engine(url=make_url(db_config.uri))
    pool = sessionmaker(bind=engine, class_=AsyncSession,
                        expire_on_commit=False, autoflush=False)
    return pool
