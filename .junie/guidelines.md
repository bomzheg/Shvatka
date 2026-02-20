### Development Guidelines for Shvatka Project

#### 1. Build and Configuration Instructions
This project uses `uv` for dependency management.
- **Environment Setup**:
    1. Install `uv`.
    2. Copy the sample configuration: `cp config_dist config`.
    3. Fill in the required values in the `config` directory and `alembic.ini`.
    4. Install dependencies: `uv pip install .`
    5. For develop purpose available to run redis and postrges via docker-compose: `cd develop && docker-compose up -d`
- **Database Migrations**:
    Apply migrations using alembic: `python -m alembic upgrade head`.
- **Running the Project**:
    - Telegram bot: `shvatka-tgbot`
    - API: `shvatka-api`

#### 2. Testing Information
- **Configuring and Running Tests**:
    The project uses `pytest`. Tests are located in the `tests/` directory.
    - Run all tests: `pytest tests`
    - Run only unit tests: `pytest tests/unit`
    - Run with coverage: `pytest --cov=shvatka tests`
- **Adding New Tests**:
    - Place unit tests in `tests/unit` and integration tests in `tests/integration`.
    - Follow the naming convention `test_*.py` for test files and `test_*` for test functions.
- **Demonstration Test**:
    The following test demonstrates creating a simple level scenario hint:
    ```python
    from shvatka.core.models.dto import hints
    from shvatka.core.models.dto import scn

    def test_simple_hint_creation():
        text_hint = hints.TextHint(text="Hello, World!")
        time_hint = hints.TimeHint(time=0, hint=[text_hint])
        hints_list = scn.HintsList([time_hint])
        
        assert len(hints_list) == 1
        assert hints_list[0].time == 0
        assert hints_list[0].hint[0].text == "Hello, World!"
    ```

#### 3. Additional Development Information
- **Code Style and Linters**:
    The project uses `ruff` for formatting and linting, and `mypy` for static type checking.
    - Format and fix linting issues: `ruff format . && ruff check --fix .`
    - Run type checking: `mypy .`
    - Use next import patterns for next packages:
      ```python
         from shvatka.core.models.dto import hints
         from shvatka.core.models.dto import scn
         from shvatka.core.models import dto
      ```
      and never import classes without such prefix if you work out of package
- **Dependency Management**:
    If you add or update dependencies in `pyproject.toml`, update the lock file using:
    `uv pip compile pyproject.toml > lock.txt`
- **Configuration**:
    The `config/` directory contains various configuration files for the application modules (bot, api, database, etc.).
- **Docker**:
    Docker-compose is available for both development (`develop/docker-compose.yml`) and production-like setup in the project root.
