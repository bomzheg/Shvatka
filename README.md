# new shvatka bot

[![wakatime](https://wakatime.com/badge/github/bomzheg/Shvatka.svg)](https://wakatime.com/badge/github/bomzheg/Shvatka)

Движок для ночной поисковой игры [Схватка](https://ru.wikipedia.org/wiki/%D0%A1%D1%85%D0%B2%D0%B0%D1%82%D0%BA%D0%B0_(%D0%B8%D0%B3%D1%80%D0%B0)) (похожа на Дозоры, Энакунтер)

Позволяет проводить планировать и проводить игры.

Core-функционал: 
- редактор сценария игры, 
- управление подготовкой к игре, 
- формирование команды капитаном, 
- назначение заместителей капитана с разными полномочиями, 
- сборка заявок на игру, 
- проведение игры, 
- информирование организаторов о ходе игры, 
- формирование результатов игры, 
- сохранение статистики прошедших игр


## How to run without docker:
1. `cp config_dist config`
2. Заполнить конфиги в config
3. Заполнить урл бд в alembic.ini
4. Запустить и применить миграции `python -m alembic upgrade head`
5. 
```shell
uv pip install .
export BOT_PATH=$PWD
shvatka-tgbot
```

## How to run with Docker
1. `cp config_dist config`
2. Заполнить конфиги в config
3. Заполнить урл бд в alembic.ini
4. Запустить и применить миграции `docker-compose run cli -c "python -m alembic upgrade head"`
5. `docker-compose up -d`


## How to fix deps
```shell
uv pip compile pyproject.toml > lock.txt
```

## How to test
```shell
pytest tests
```
or only unittests (faster):
```shell
pytest tests/unit
```

## Linters

Linux:
```shell
ruff format . && ruff --fix . && mypy .
```

Windows:
```shell
ruff format . ; ruff --fix . ; mypy .
```
