from shvatka.models import dto
from shvatka.scheduler import LevelTestScheduler
from shvatka.views.game import OrgNotifier
from shvatka.views.level import LevelView


async def start_level_test(
    level: dto.Level,
    tester: dto.Organizer,
    scheduler: LevelTestScheduler,
    view: LevelView,
    org_notifier: OrgNotifier,
):
    pass  # TODO
