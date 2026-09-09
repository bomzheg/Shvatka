"""The api's route table builds — the cheapest way to catch a broken model.

FastAPI resolves every request and response model when the routes are
registered, so a model pydantic cannot evaluate takes the whole app down at
startup and every integration test with it. That is a slow, confusing way to
learn about a one-word mistake; this is a fast one.
"""

from fastapi import FastAPI

from shvatka.api.app import router


def build() -> FastAPI:
    app = FastAPI()
    app.include_router(router.setup())
    return app


def test_every_route_registers() -> None:
    app = build()

    assert len(app.routes) > 1


def test_the_season_routes_are_reachable() -> None:
    paths = {route.path for route in build().routes if hasattr(route, "path")}

    assert "/seasons" in paths
    assert "/seasons/current" in paths
    assert "/seasons/defaults" in paths
    assert "/seasons/{year}" in paths
    assert "/seasons/{year}/slots/{slot_id}/take" in paths
    # the literal paths must be registered before /seasons/{year}, or a request
    # for them is swallowed by the year route
    ordered = [route.path for route in build().routes if hasattr(route, "path")]
    assert ordered.index("/seasons/current") < ordered.index("/seasons/{year}")
    assert ordered.index("/seasons/slots/suggest") < ordered.index("/seasons/{year}")
