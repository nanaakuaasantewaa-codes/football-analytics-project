"""
stat_finder.py

Surfaces ranked "tweetable" insights across five analysis types:
  TEAM        — team-level stat comparisons and discrepancies
  PLAYER      — standout individual performances
  HISTORICAL  — milestones and all-time records
  TIMELINE    — late drama, stoppage-time goals, penalty shootouts
  SHOT_MAP    — shot volume and conversion efficiency

Each candidate has a headline (ready-to-post sentence), a score, and
instructions for chart_builder telling it what to draw.
"""

from dataclasses import dataclass, field


@dataclass
class StatCandidate:
    headline:      str
    analysis_type: str    # TEAM | PLAYER | HISTORICAL | TIMELINE | SHOT_MAP
    stat_type:     str    # finer label used for scoring display
    score:         float
    chart_data:    dict = field(default_factory=dict)


def _safe(df, stat, team, default=0.0):
    try:
        return float(df.loc[stat, team])
    except (KeyError, TypeError, ValueError):
        return default


# ------------------------------------------------------------------
# TEAM analysis candidates
# ------------------------------------------------------------------
def find_team_candidates(df, meta) -> list[StatCandidate]:
    cands  = []
    team_a = meta["team_a"]
    team_b = meta["team_b"]
    score_a, score_b = meta["score_a"], meta["score_b"]
    margin = abs(score_a - score_b)

    shots_a = _safe(df, "Total Shots", team_a)
    shots_b = _safe(df, "Total Shots", team_b)
    sot_a   = _safe(df, "Shots on Goal", team_a)
    sot_b   = _safe(df, "Shots on Goal", team_b)
    poss_a  = _safe(df, "Ball Possession", team_a)
    poss_b  = _safe(df, "Ball Possession", team_b)
    pass_a  = _safe(df, "Passes accurate", team_a)
    pass_b  = _safe(df, "Passes accurate", team_b)
    save_a  = _safe(df, "Goalkeeper Saves", team_a)
    save_b  = _safe(df, "Goalkeeper Saves", team_b)

    # Shot dominance vs tight result
    if shots_a > 0 and shots_b > 0:
        dom   = team_a if shots_a >= shots_b else team_b
        und   = team_b if shots_a >= shots_b else team_a
        ds, ws = (shots_a, shots_b) if shots_a >= shots_b else (shots_b, shots_a)
        ratio = round(ds / ws, 1) if ws > 0 else ds
        if ratio >= 3.0:
            cands.append(StatCandidate(
                headline=(f"{dom} outshot {und} {int(ds)}-{int(ws)} ({ratio}x) "
                          f"but won by just {margin} goal{'s' if margin>1 else ''}."),
                analysis_type="TEAM", stat_type="shot_dominance",
                score=8.5 if ratio >= 4 else 7.5,
                chart_data={"type": "bar", "stat": "Total Shots"},
            ))

    # Low conversion despite shots
    if shots_a >= 10 and score_a < 2:
        conv = round(score_a / shots_a * 100, 1) if shots_a else 0
        cands.append(StatCandidate(
            headline=(f"{team_a} had {int(shots_a)} shots but converted just "
                      f"{conv}% — a wasteful afternoon in front of goal."),
            analysis_type="TEAM", stat_type="low_conversion",
            score=7.0,
            chart_data={"type": "bar", "stat": "Total Shots"},
        ))

    # Goalkeeper heroics
    hero_saves = max(save_a, save_b)
    hero_team  = team_a if save_a >= save_b else team_b
    if hero_saves >= 6:
        cands.append(StatCandidate(
            headline=(f"{hero_team}'s goalkeeper made {int(hero_saves)} saves "
                      f"to keep their side in the tournament."),
            analysis_type="TEAM", stat_type="goalkeeper_saves",
            score=7.5,
            chart_data={"type": "bar", "stat": "Goalkeeper Saves"},
        ))

    # Possession without reward
    if poss_a > 60 and score_a <= score_b:
        cands.append(StatCandidate(
            headline=(f"{team_a} dominated possession ({int(poss_a)}%) "
                      f"but couldn't turn it into a win."),
            analysis_type="TEAM", stat_type="possession_paradox",
            score=7.0,
            chart_data={"type": "bar", "stat": "Ball Possession"},
        ))
    elif poss_b > 60 and score_b <= score_a:
        cands.append(StatCandidate(
            headline=(f"{team_b} dominated possession ({int(poss_b)}%) "
                      f"but couldn't turn it into a win."),
            analysis_type="TEAM", stat_type="possession_paradox",
            score=7.0,
            chart_data={"type": "bar", "stat": "Ball Possession"},
        ))

    # Pass volume
    if pass_a > 0 and pass_b > 0:
        pr = round(max(pass_a, pass_b) / min(pass_a, pass_b), 1)
        dom_p = team_a if pass_a >= pass_b else team_b
        if pr >= 2.0:
            cands.append(StatCandidate(
                headline=(f"{dom_p} completed {int(max(pass_a, pass_b))} accurate passes "
                          f"— {pr}x more than their opponents."),
                analysis_type="TEAM", stat_type="pass_volume",
                score=6.0,
                chart_data={"type": "bar", "stat": "Passes accurate"},
            ))

    return cands


# ------------------------------------------------------------------
# PLAYER analysis candidates
# ------------------------------------------------------------------
def find_player_candidates(players: list, meta: dict) -> list[StatCandidate]:
    cands = []
    if not players:
        return cands

    # Top rated player
    top = players[0]
    cands.append(StatCandidate(
        headline=(f"{top['player_name']} ({top['team']}) rated {top['rating']:.1f}/10 — "
                  f"the standout performer in {meta['team_a']} "
                  f"{meta['score_a']}-{meta['score_b']} {meta['team_b']}."),
        analysis_type="PLAYER", stat_type="top_rated",
        score=8.0,
        chart_data={"type": "player_bar", "players": players[:5], "metric": "rating"},
    ))

    # Goalscorer spotlight
    scorers = [g for g in meta.get("goal_scorers", [])]
    for g in scorers:
        player_stats = next(
            (p for p in players if p["player_name"] == g["player"]), None
        )
        if player_stats:
            cands.append(StatCandidate(
                headline=(f"{g['player']} scored in the {g['minute']}' "
                          f"and completed {player_stats['passes_total']} passes "
                          f"with a {player_stats['rating']:.1f}/10 rating."),
                analysis_type="PLAYER", stat_type="goalscorer_spotlight",
                score=8.5,
                chart_data={
                    "type": "player_spotlight",
                    "player": player_stats,
                    "minute": g["minute"],
                },
            ))

    # Most shots (individual)
    by_shots = sorted(players, key=lambda p: p["shots_total"], reverse=True)
    if by_shots and by_shots[0]["shots_total"] >= 4:
        p = by_shots[0]
        cands.append(StatCandidate(
            headline=(f"{p['player_name']} had {p['shots_total']} shots "
                      f"({p['shots_on_target']} on target) — the most of any player."),
            analysis_type="PLAYER", stat_type="most_shots",
            score=7.0,
            chart_data={"type": "player_bar",
                        "players": by_shots[:6], "metric": "shots_total"},
        ))

    # Best passer (>50 passes)
    by_passes = [p for p in players if p["passes_total"] >= 50]
    by_passes.sort(key=lambda p: p["passes_total"], reverse=True)
    if by_passes:
        p = by_passes[0]
        cands.append(StatCandidate(
            headline=(f"{p['player_name']} completed {p['passes_total']} passes "
                      f"at {p['passes_accuracy']}% accuracy — the engine of the game."),
            analysis_type="PLAYER", stat_type="best_passer",
            score=6.5,
            chart_data={"type": "player_bar",
                        "players": by_passes[:6], "metric": "passes_total"},
        ))

    return cands


# ------------------------------------------------------------------
# HISTORICAL analysis candidates
# ------------------------------------------------------------------
def find_historical_candidates(historical: dict, meta: dict) -> list[StatCandidate]:
    cands   = []
    team_a  = meta["team_a"]
    team_b  = meta["team_b"]
    score_a = meta["score_a"]
    score_b = meta["score_b"]

    for team_name, ctx in historical.items():
        wins = ctx.get("knockout_wins")
        apps = ctx.get("knockout_appearances")
        if wins is None or apps is None:
            continue
        is_winner = (
            (team_name == team_a and score_a > score_b) or
            (team_name == team_b and score_b > score_a)
        )
        if wins == 0 and not is_winner and apps and apps > 0:
            cands.append(StatCandidate(
                headline=(f"{team_name} have still never won a World Cup knockout "
                          f"match ({apps} appearance{'s' if apps > 1 else ''}, 0 wins)."),
                analysis_type="HISTORICAL", stat_type="knockout_drought",
                score=10.0,
                chart_data={"type": "stat_card", "team": team_name},
            ))
        elif wins == 0 and is_winner:
            suffix = {1:"st",2:"nd",3:"rd"}.get(apps, "th")
            cands.append(StatCandidate(
                headline=(f"{team_name} win a World Cup knockout game for the "
                          f"first time at the {apps}{suffix} attempt."),
                analysis_type="HISTORICAL", stat_type="historic_first",
                score=10.0,
                chart_data={"type": "stat_card", "team": team_name},
            ))
        elif wins and wins >= 1:
            cands.append(StatCandidate(
                headline=(f"{team_name} have now won {wins} of their "
                          f"{apps} World Cup knockout appearances."),
                analysis_type="HISTORICAL", stat_type="record_update",
                score=5.5,
                chart_data={"type": "stat_card", "team": team_name},
            ))

    return cands


# ------------------------------------------------------------------
# TIMELINE analysis candidates
# ------------------------------------------------------------------
def find_timeline_candidates(meta: dict) -> list[StatCandidate]:
    cands  = []
    goals  = meta.get("goal_scorers", [])
    team_a = meta["team_a"]
    team_b = meta["team_b"]

    for g in goals:
        if g["minute"] >= 90:
            extra = g["minute"] - 90
            cands.append(StatCandidate(
                headline=(f"{g['player']} scores in the {g['minute']}' (+{extra}) "
                          f"to complete a dramatic comeback for "
                          f"{g['team']} at the World Cup."),
                analysis_type="TIMELINE", stat_type="stoppage_time_goal",
                score=9.5,
                chart_data={"type": "timeline", "goals": goals},
            ))
        elif g["minute"] >= 85:
            cands.append(StatCandidate(
                headline=(f"{g['player']}'s {g['minute']}'-minute goal settles "
                          f"{team_a} {meta['score_a']}-{meta['score_b']} {team_b}."),
                analysis_type="TIMELINE", stat_type="late_goal",
                score=8.0,
                chart_data={"type": "timeline", "goals": goals},
            ))

    if meta.get("went_to_pens"):
        cands.append(StatCandidate(
            headline=(f"120 minutes couldn't separate {team_a} and {team_b} "
                      f"— it came down to penalties."),
            analysis_type="TIMELINE", stat_type="penalties",
            score=9.0,
            chart_data={"type": "timeline", "goals": goals},
        ))

    if not cands:
        cands.append(StatCandidate(
            headline=(f"{team_a} {meta['score_a']}-{meta['score_b']} {team_b} "
                      f"— full-time in the {meta['round']}."),
            analysis_type="TIMELINE", stat_type="result",
            score=3.0,
            chart_data={"type": "timeline", "goals": goals},
        ))

    return cands


# ------------------------------------------------------------------
# SHOT MAP analysis candidates
# ------------------------------------------------------------------
def find_shot_map_candidates(df, meta: dict) -> list[StatCandidate]:
    cands   = []
    team_a  = meta["team_a"]
    team_b  = meta["team_b"]
    score_a = meta["score_a"]

    total_a = _safe(df, "Total Shots", team_a)
    total_b = _safe(df, "Total Shots", team_b)
    sot_a   = _safe(df, "Shots on Goal", team_a)
    sot_b   = _safe(df, "Shots on Goal", team_b)
    inside_a = _safe(df, "Shots insidebox", team_a)
    inside_b = _safe(df, "Shots insidebox", team_b)

    if total_a > 0:
        acc = round(sot_a / total_a * 100, 1)
        cands.append(StatCandidate(
            headline=(f"{team_a} placed {int(sot_a)} of {int(total_a)} shots on target "
                      f"({acc}% accuracy) — scoring {score_a} goal{'s' if score_a!=1 else ''}."),
            analysis_type="SHOT_MAP", stat_type="shot_accuracy",
            score=7.5,
            chart_data={"type": "shot_breakdown",
                        "teams": [team_a, team_b],
                        "total": [total_a, total_b],
                        "on_target": [sot_a, sot_b],
                        "inside_box": [inside_a, inside_b]},
        ))

    cands.append(StatCandidate(
        headline=(f"Shot breakdown: {team_a} {int(total_a)} shots vs "
                  f"{team_b}'s {int(total_b)} — in the {meta['round']}."),
        analysis_type="SHOT_MAP", stat_type="shot_volume",
        score=6.0,
        chart_data={"type": "shot_breakdown",
                    "teams": [team_a, team_b],
                    "total": [total_a, total_b],
                    "on_target": [sot_a, sot_b],
                    "inside_box": [inside_a, inside_b]},
    ))

    return cands


# ------------------------------------------------------------------
# MASTER DISPATCHER
# ------------------------------------------------------------------
def find_candidates(
    analysis_type: str,
    df,
    players: list,
    historical: dict,
    meta: dict,
) -> list[StatCandidate]:
    """
    Returns a ranked list of StatCandidates for the chosen analysis type.
    analysis_type must be one of: TEAM, PLAYER, HISTORICAL, TIMELINE, SHOT_MAP
    """
    dispatch = {
        "TEAM":       lambda: find_team_candidates(df, meta),
        "PLAYER":     lambda: find_player_candidates(players, meta),
        "HISTORICAL": lambda: find_historical_candidates(historical, meta),
        "TIMELINE":   lambda: find_timeline_candidates(meta),
        "SHOT_MAP":   lambda: find_shot_map_candidates(df, meta),
    }
    fn = dispatch.get(analysis_type.upper())
    if not fn:
        raise ValueError(f"Unknown analysis type: {analysis_type}. "
                         f"Choose from: {list(dispatch.keys())}")

    candidates = fn()

    # Always append a safe fallback
    candidates.append(StatCandidate(
        headline=(f"{meta['team_a']} {meta['score_a']}-{meta['score_b']} "
                  f"{meta['team_b']} — {meta['round']}, {meta['competition']}."),
        analysis_type=analysis_type,
        stat_type="fallback",
        score=0.5,
        chart_data={"type": "stat_card", "team": meta["team_a"]},
    ))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
