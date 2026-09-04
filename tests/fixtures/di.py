from dishka import Provider

from shvatka.main_factory import get_root_app_providers
from tests.fixtures.db_provider import TestDbProvider
from tests.fixtures.file_storage import MemoryFileStorageProvider
from tests.mocks.bot import MockBotProvider, MockMessageManagerProvider
from tests.mocks.di import MocksProvider
from tests.mocks.file_gateway import FileGatewayMockProvider

TEST_PATHS_ENV = "SHVATKA_TEST_PATH"


def get_test_providers() -> list[Provider]:
    return [
        *get_root_app_providers(TEST_PATHS_ENV),
        *get_test_override_providers(),
    ]


def get_test_override_providers() -> list[Provider]:
    return [
        TestDbProvider(),
        MemoryFileStorageProvider(),
        MockBotProvider(),
        MockMessageManagerProvider(),
        MocksProvider(),
        FileGatewayMockProvider(),
    ]
