Generic single-database configuration with an async dbapi.

For create new migration
```
alembic revision --autogenerate -m "add new table"
```

for migrate 
```
alembic upgrade +1
```

for rollback
```
alembic downgrade -1
```
