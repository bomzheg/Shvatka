Generic single-database configuration with an async dbapi.

For create new migration
```sh
alembic revision --autogenerate -m "add new table"
```

for migrate 
```sh
alembic upgrade +1
```

for rollback
```sh
alembic downgrade -1
```
