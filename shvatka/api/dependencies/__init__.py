from dishka.integrations.fastapi import DishkaApp
from fastapi import FastAPI

from shvatka.infrastructure.di import get_providers


def setup_dishka(app: FastAPI, paths_env: str) -> DishkaApp:
    return DishkaApp(providers=get_providers(paths_env), app=app)
