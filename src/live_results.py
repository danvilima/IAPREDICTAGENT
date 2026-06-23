from datetime import date, datetime
from typing import Any

import requests


BASE_URL = "https://worldcup26.ir"


def _to_int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None

        text = str(value).strip()

        if text.lower() in ["", "null", "none", "nan"]:
            return None

        return int(text)
    except Exception:
        return None


def _parse_finished(value: Any) -> bool:
    return str(value).strip().upper() in ["TRUE", "1", "YES", "FINISHED"]


def _parse_local_date(value: Any) -> str | None:
    """
    A API worldcup26 usa local_date no formato exemplo:
    06/11/2026 13:00
    """
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        dt = datetime.strptime(text, "%m/%d/%Y %H:%M")
        return dt.isoformat()
    except Exception:
        return text


def _get_games_payload() -> list[dict[str, Any]]:
    url = f"{BASE_URL}/get/games"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict) and "games" in data:
        games = data["games"]
    elif isinstance(data, list):
        games = data
    else:
        raise RuntimeError(f"Formato inesperado da API worldcup26: {data}")

    if not isinstance(games, list):
        raise RuntimeError("A chave 'games' não retornou uma lista.")

    return games


def _convert_worldcup26_to_api_football(game: dict[str, Any]) -> dict[str, Any]:
    finished = _parse_finished(game.get("finished"))
    time_elapsed = str(game.get("time_elapsed", "")).strip().lower()

    if finished:
        status_short = "FT"
        status_long = "Match Finished"
    elif time_elapsed and time_elapsed not in ["notstarted", "not_started"]:
        status_short = "LIVE"
        status_long = "Live"
    else:
        status_short = "NS"
        status_long = "Not Started"

    match_type = str(game.get("type", "")).upper()
    group_or_round = str(game.get("group", "")).strip()

    if match_type == "GROUP" or group_or_round in list("ABCDEFGHIJKL"):
        round_name = f"Group {group_or_round}"
    else:
        round_name = group_or_round or match_type

    home_name = game.get("home_team_name_en") or game.get("home_team_label") or "TBD"

    away_name = game.get("away_team_name_en") or game.get("away_team_label") or "TBD"

    fixture_id = _to_int_or_none(game.get("id")) or 0
    home_goals = _to_int_or_none(game.get("home_score"))
    away_goals = _to_int_or_none(game.get("away_score"))

    return {
        "fixture": {
            "id": fixture_id,
            "date": _parse_local_date(game.get("local_date")),
            "status": {
                "short": status_short,
                "long": status_long,
            },
        },
        "league": {
            "id": 1,
            "season": 2026,
            "round": round_name,
        },
        "teams": {
            "home": {
                "id": _to_int_or_none(game.get("home_team_id")),
                "name": home_name,
            },
            "away": {
                "id": _to_int_or_none(game.get("away_team_id")),
                "name": away_name,
            },
        },
        "goals": {
            "home": home_goals,
            "away": away_goals,
        },
        "score": {
            "penalty": {
                "home": None,
                "away": None,
            }
        },
        "raw_worldcup26": game,
    }


def fetch_all_fixtures() -> list[dict[str, Any]]:
    games = _get_games_payload()
    return [_convert_worldcup26_to_api_football(game) for game in games]


def fetch_daily_fixtures(data_jogo: date | None = None) -> list[dict[str, Any]]:
    if data_jogo is None:
        data_jogo = date.today()

    fixtures = fetch_all_fixtures()
    daily_fixtures: list[dict[str, Any]] = []

    for fixture in fixtures:
        fixture_date = fixture.get("fixture", {}).get("date")

        if not fixture_date:
            continue

        try:
            dt = datetime.fromisoformat(str(fixture_date))
            if dt.date() == data_jogo:
                daily_fixtures.append(fixture)
        except Exception:
            continue

    return daily_fixtures


def fetch_fixtures() -> list[dict[str, Any]]:
    return fetch_all_fixtures()
