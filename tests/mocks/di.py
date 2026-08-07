from dishka import Provider, Scope, provide

from shvatka.core.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.core.views.game import GameReleasePublisher
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from tests.mocks.datetime_mock import ClockMock
from tests.mocks.game_log import GameLogWriterMock
from tests.mocks.game_release import GameReleasePublisherMock
from tests.mocks.scheduler_mock import LevelSchedulerMock, SchedulerMock
from tests.mocks.user_getter import UserGetterMock


class MocksProvider(Provider):
    """Replaces everything talking to the outer world with in-memory mocks."""

    scope = Scope.APP

    clock = provide(ClockMock)
    # not an override: the app's own (complex) writer stays in place for
    # container-resolved code, the mock is for services called by hand
    game_log = provide(GameLogWriterMock)

    @provide(override=True)
    def release_publisher(self) -> GameReleasePublisher:
        # nothing is announced to telegram in tests
        return GameReleasePublisherMock()

    @provide(override=True)
    def user_getter(self) -> UserGetter:
        return UserGetterMock()

    @provide(override=True)
    def scheduler(self) -> Scheduler:
        return SchedulerMock()

    @provide(override=True)
    def level_test_scheduler(self) -> LevelTestScheduler:
        return LevelSchedulerMock()
