import importlib.resources


def load_error_img() -> bytes:
    with importlib.resources.path("infrastructure.assets", "parser_error.png") as path:
        with path.open("rb") as f:
            return f.read()
