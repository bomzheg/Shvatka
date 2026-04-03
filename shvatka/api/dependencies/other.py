from dishka import Provider, Scope, provide

from shvatka.api.utils.web_input import WebInput


class OtherApiProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def input(self) -> WebInput:
        return WebInput()
