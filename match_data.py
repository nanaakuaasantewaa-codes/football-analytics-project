"""
match_data.py

Parses raw API-Football responses into clean structures used by the
analysis modules and chart builder.
"""

import pandas as pd
from api_client import (
    get_fixture_metadata,
    get_match_statistics,
    get_player_statistics,
    get_team_world_cup_history,
)

TEAM_STAT_KEYS = [
    "Total Shots",
    "Shots on Goal",
    "Shots off Goal",
    "Blocked Shots",
    "Shots insidebox",
    "Shots outsidebox",
    "Ball Possession",
    "Total passes",
    "Passes accurate",
    "Passes %",
    "Fouls",
    "Corner Kicks",
    "Offsides",
    "Yellow Cards",
    "Red Cards",
    "Goalkeeper Saves",
]


def _parse_value(raw) -> float:
    if raw is None:
        return 0.0
    if isinstance(raw, str) and raw.endswith("%"):
        return float(raw[:-1])
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def build_team_stats_df(fixture_id: int) -> pd.DataFrame:
    raw  = get_match_statistics(fixture_id)
    data = {}
    cols = []
    for team_block in raw:
        name = team_block["team"]["name"]
        cols.append(name)
        for stat in team_block["statistics"]:
            if stat["type"] in TEAM_STAT_KEYS:
                data.setdefault(stat["type"], {})[name] = _parse_value(stat["value"])
    df = pd.DataFrame(data).T
    if len(cols) >= 2:
        df = df[cols]
    return df


def build_player_stats(fixture_id: int) -> list[dict]:
    """
    Returns a flat list of player stat dicts, one per player.
    Keys: team, player_name, position, minutes, goals, assists,
          shots_total, shots_on_target, passes_total, passes_accuracy,
          dribbles_success, rating
    """
    raw     = get_player_statistics(fixture_id)
    players = []
    for team_block in raw:
        team_name = team_block["team"]["name"]
        for p in team_block.get("players", []):
            info  = p.get("player", {})
            stats = p.get("statistics", [{}])[0]
            players.append({
                "team":              team_name,
                "player_name":       info.get("name", "Unknown"),
                "position":          stats.get("games", {}).get("position", "—"),
                "minutes":           stats.get("games", {}).get("minutes", 0) or 0,
                "rating":            float(stats.get("games", {}).get("rating") or 0),
                "goals":             stats.get("goals", {}).get("total", 0) or 0,
                "assists":           stats.get("goals", {}).get("assists", 0) or 0,
                "shots_total":       stats.get("shots", {}).get("total", 0) or 0,
                "shots_on_target":   stats.get("shots", {}).get("on", 0) or 0,
                "passes_total":      stats.get("passes", {}).get("total", 0) or 0,
                "passes_accuracy":   stats.get("passes", {}).get("accuracy", 0) or 0,
                "dribbles_success":  stats.get("dribbles", {}).get("success", 0) or 0,
                "tackles":           stats.get("tackles", {}).get("total", 0) or 0,
                "saves":             stats.get("goals", {}).get("saves", 0) or 0,
            })
    return sorted(players, key=lambda x: x["rating"], reverse=True)


def get_historical_context(meta: dict) -> dict:
    context = {}
    for key in ("team_a", "team_b"):
        name    = meta[key]
        team_id = meta.get(f"{key}_id")
        if not team_id:
            context[name] = {}
            continue
        try:
            context[name] = get_team_world_cup_history(team_id)
        except Exception as e:
            context[name] = {"error": str(e)}
    return context


def load_match(fixture_id: int) -> tuple:
    """
    Main entry point. Returns (meta, team_df, player_list, historical).
    """
    meta      = get_fixture_metadata(fixture_id)
    team_df   = build_team_stats_df(fixture_id)
    players   = build_player_stats(fixture_id)
    historical = get_historical_context(meta)
    return meta, team_df, players, historical
