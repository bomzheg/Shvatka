import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from requests import Session

BASE_URL = os.environ["SHVATKA_UI_MAIN_URL"]
USERNAME = os.environ["SHVATKA_USERNAME"]
PASSWORD = os.environ["SHVATKA_PASSWORD"]

OUTPUT_DIR = Path("game-files")


@dataclass(kw_only=True, frozen=True, slots=True)
class Results:
    errors: list[Any]
    processed_files: int


def main() -> None:
    session = auth()

    # 2. Get games.
    response = session.get(f"{BASE_URL}/api/games")
    response.raise_for_status()

    games = response.json()["content"]
    print(f"Found {len(games)} games")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Get every game's JSON and download its files.
    total_files = 0
    errors = []

    for game in games:
        game_results = single_game_files(game, session)
        total_files += game_results.processed_files
        errors.extend(game_results.errors)

    print(f"\nDone. Downloaded {total_files} files to {OUTPUT_DIR}")
    print("\nErrors:\n", "\n".join(errors))


def main_single(game) -> None:
    session = auth()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Get every game's JSON and download its files.
    total_files = 0
    errors = []

    game_results = single_game_files(game, session)
    total_files += game_results.processed_files
    errors.extend(game_results.errors)

    print(f"\nDone. Downloaded {total_files} files to {OUTPUT_DIR}")
    print("\nErrors:\n", "\n".join(errors))


def auth() -> Session:
    session = requests.Session()

    # 1. Authenticate.
    response = session.post(
        f"{BASE_URL}/api/auth/token",
        files={
            "username": (None, USERNAME),
            "password": (None, PASSWORD),
        },
    )
    response.raise_for_status()

    print("Authenticated")
    print("Cookies:", session.cookies.get_dict())
    return session


def single_game_files(game, session: Session) -> Results:
    errors = []
    total_files = 0

    game_id = game["id"]
    game_name = game.get("name", "")

    print(f"\nGame {game_id}: {game_name}")

    response = session.get(f"{BASE_URL}/api/games/{game_id}")
    response.raise_for_status()

    game_data = response.json()
    files = game_data.get("files", [])

    print(f"  Files: {len(files)}")

    game_dir = OUTPUT_DIR / str(game_id)
    game_dir.mkdir(exist_ok=True)

    for file_info in files:
        guid = file_info["guid"]
        filename = f'{file_info["original_filename"]}_{file_info["guid"]}{file_info["extension"]}'

        output_file = game_dir / filename

        url = f"{BASE_URL}/cdn/games/{game_id}/files/{guid}"

        try:
            response = session.get(url)
            response.raise_for_status()

            data = response.content

            if len(data) == 0:
                raise RuntimeError(f"Empty file: game={game_id}, guid={guid}, url={url}")

            output_file.write_bytes(data)
        except Exception as e:
            errors.append(url)
            print("error by ", url, e)
        else:
            print(f"  OK {filename}: {len(data):,} bytes")
            total_files += 1
    return Results(processed_files=total_files, errors=errors)


if __name__ == "__main__":
    main_single(dict(id=129))
