from typing import Mapping

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

convention: Mapping[str, str] = {
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "pk__%(table_name)s",
}
meta = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = meta
