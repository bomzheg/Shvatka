from shvatka.core.views.texts import PERMISSION_EMOJI


def bool_render(data: bool):
    return PERMISSION_EMOJI[data]
