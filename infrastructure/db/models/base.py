from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
convention = {
    'ix': 'ix__%(column_0_label)s',
    'uq': 'uq__%(table_name)s__%(column_0_name)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}
meta = MetaData(naming_convention=convention)
Base = declarative_base(metadata=meta)
