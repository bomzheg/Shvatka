from shvatka.core.views.game import GameLogWriter, GameView, OrgNotifier, ShowTasks, ViewSender


class ViewSenderMock(ViewSender):
    """Shows straight away instead of handing the tasks to a nursery."""

    def __init__(self, view: GameView, org_notifier: OrgNotifier, game_log: GameLogWriter) -> None:
        self.view = view
        self.org_notifier = org_notifier
        self.game_log = game_log

    async def show_later(self, tasks: ShowTasks) -> None:
        if tasks.view:
            await self.view.show(tasks.view)
        for event in tasks.org:
            await self.org_notifier.notify(event)
        for log_event in tasks.log:
            await self.game_log.log(log_event)
