= Game Engine "Shvatka"

image:https://wakatime.com/badge/github/bomzheg/Shvatka.svg[wakatime,link=https://wakatime.com/badge/github/bomzheg/Shvatka]
image:https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/bomzheg/99469cb5f8a18784c1f03d229a799427/raw/bage.json[coverage]

Engine for the night search game https://en.wikipedia.org/wiki/Encounter_(game)[Shvatka/Encounter]

Allows planning and running games. Consists of a REST interface and a Telegram bot.

.Core functionality:
* Game scenario editor,
* Game preparation management,
* Team formation by the captain,
* Assigning deputy captains with different permissions,
* Collecting game applications,
* Running the game,
* Informing organizers about game progress,
* Generating game results,
* Storing statistics of past games

https://bomzheg.github.io/Shvatka[Documentation]

== How to run without Docker:

. `cp config_dist config`
. Fill in the configs in `config`
. Set the database URL in `alembic.ini`
. Run and apply migrations `python -m alembic upgrade head`
.
[source,shell]
----
uv pip install .
export BOT_PATH=$PWD
shvatka-tgbot
----

== How to run with Docker

. `cp config_dist config`
. Fill in the configs in `config`
. Set the database URL in `alembic.ini`
. Run and apply migrations `docker-compose run cli -c "python -m alembic upgrade head"`
. `docker-compose up -d`

== How to fix dependencies

[source,shell]
----
uv pip compile pyproject.toml > lock.txt
----

== How to test

[source,shell]
----
pytest tests
----

or only unit tests (faster):

[source,shell]
----
pytest tests/unit
----

== Linters

Linux:

[source,shell]
----
ruff format . && ruff --fix . && mypy .
----

Windows:

[source,shell]
----
ruff format . ; ruff --fix . ; mypy .
----
