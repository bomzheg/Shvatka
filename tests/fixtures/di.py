from dishka import Provider

from shvatka.main_factory import get_root_app_providers
from tests.fixtures.db_provider import TestDbProvider
from tests.fixtures.file_storage import MemoryFileStorageProvider
from tests.mocks.bot import MockBotProvider, MockMessageManagerProvider
from tests.mocks.di import MocksProvider

TEST_PATHS_ENV = "SHVATKA_TEST_PATH"


def get_test_providers() -> list[Provider]:
    """The very same providers as the real app has, with test doubles on top.

    Everything the app can provide must stay providable in tests, so the list
    is not copied here — it is reused as is and only what tests can't afford
    (real db, real telegram, real scheduler) is overridden afterwards.
    """
    return [
        *get_root_app_providers(TEST_PATHS_ENV),
        *get_test_override_providers(),
    ]


def get_test_override_providers() -> list[Provider]:
    """Test doubles. Each one overrides (``override=True``) an app dependency.

    Must go last: dishka forbids overriding what wasn't provided before.
    """
    return [
        TestDbProvider(),
        MemoryFileStorageProvider(),
        MockBotProvider(),
        MockMessageManagerProvider(),
        MocksProvider(),
    ]
