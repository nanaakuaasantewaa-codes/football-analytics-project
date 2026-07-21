"""
api_client.py

All communication with the API-Football REST API.
Base URL: https://v3.football.api-sports.io
Free tier: 100 requests/day. One full bot run uses ~4-6 requests.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL            = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1        # FIFA World Cup on API-Football
WORLD_CUP_SEASON    = 2026
PREMIER_LEAGUE_LEAGUE_ID = 39
PREMIER_LEAGUE_SEASON = 2024

def _headers() -> dict:
    key = os.getenv("FOOTBALL_API_KEY")
    if not key:
        raise RuntimeError(
            "FOOTBALL_API_KEY not found. "
            "Check that .env exists and contains FOOTBALL_API_KEY=<your_key>"
        )
    return {"x-apisports-key": key}


def _get(endpoint: str, params: dict = None) -> dict:
    url  = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(
            f"API-Football returned HTTP {resp.status_code} for {url}\n"
            f"Response: {resp.text[:400]}"
        )
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"API-Football error: {data['errors']}")
    return data


def verify_api_key() -> dict:
    """Lightweight check — returns account info if key is valid."""
    data = _get("status")
    return data.get("response", {})


def get_fixtures_by_date(selected_date: str) -> list:
    """Returns Premier League fixtures for a chosen date."""
    data = _get("fixtures", {
        "league": PREMIER_LEAGUE_LEAGUE_ID,
        "season": PREMIER_LEAGUE_SEASON,
        "date": selected_date,
    })
    return data.get("response", [])


def get_fixture_metadata(fixture_id: int) -> dict:
    """
    Returns structured match metadata. Raises RuntimeError if the
    match is not yet finished (requires FT, AET, or PEN status).
    """
    data     = _get("fixtures", {"id": fixture_id})
    fixtures = data.get("response", [])
    if not fixtures:
        raise RuntimeError(f"No fixture found for ID {fixture_id}.")

    fix    = fixtures[0]
    status = fix["fixture"]["status"]["short"]
    if status not in ("FT", "AET", "PEN"):
        raise RuntimeError(
            f"Fixture {fixture_id} is not finished yet (status: {status}). "
            "Wait for full time, then try again."
        )

    goals = []
    for event in fix.get("events", []):
        if event.get("type") == "Goal" and event.get("detail") != "Missed Penalty":
            goals.append({
                "team":   event["team"]["name"],
                "player": event["player"]["name"],
                "minute": event["time"]["elapsed"] + (event["time"].get("extra") or 0),
            })

    home = fix["teams"]["home"]
    away = fix["teams"]["away"]
    return {
        "fixture_id":   fixture_id,
        "team_a":       home["name"],
        "team_b":       away["name"],
        "team_a_id":    home["id"],
        "team_b_id":    away["id"],
        "score_a":      fix["goals"]["home"] or 0,
        "score_b":      fix["goals"]["away"] or 0,
        "round":        fix["league"]["round"],
       "competition":  "Premier League",
        "date ":         fix["fixture"]["date"][:10],
        "venue":        fix["fixture"]["venue"]["name"],
        "goal_scorers": goals,
        "went_to_pens": status == "PEN",
    }


def get_match_statistics(fixture_id: int) -> list:
    data  = _get("fixtures/statistics", {"fixture": fixture_id})
    stats = data.get("response", [])
    if not stats:
        raise RuntimeError(
            f"No statistics available for fixture {fixture_id}. "
            "Statistics are usually published 10-15 minutes after full time."
        )
    return stats

def get_player_statistics(fixture_id: int) -> list:
    """Returns per-player stats for both teams in a fixture."""
    data = _get("fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def get_team_world_cup_history(team_id: int) -> dict:
    """Fetches historical World Cup results for a team."""
    data     = _get("fixtures", {
        "team":   team_id,
        "league": WORLD_CUP_LEAGUE_ID,
        "season": WORLD_CUP_SEASON,
    })
    fixtures = data.get("response", [])

    knockout_kw      = ("Round of", "Quarter", "Semi", "Final", "3rd")
    knockout_apps    = 0
    knockout_wins    = 0

    for fix in fixtures:
        rnd = fix["league"]["round"]
        if any(k in rnd for k in knockout_kw):
            knockout_apps += 1
            is_home      = fix["teams"]["home"]["id"] == team_id
            won          = fix["teams"]["home"]["winner"] if is_home else fix["teams"]["away"]["winner"]
            if won:
                knockout_wins += 1

    return {
        "knockout_appearances": knockout_apps,
        "knockout_wins":        knockout_wins,
    }
if __name__ == "__main__":
    data = _get("fixtures", {
        "league": 39,
        "season": 2024,
    })

    for match in data["response"][:5]:
        print(
            match["fixture"]["id"],
            match["teams"]["home"]["name"],
            "vs",
            match["teams"]["away"]["name"]
        )