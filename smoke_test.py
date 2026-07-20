"""Offline smoke test — validates the full pipeline with mocked match data."""
import os, shutil
import pandas as pd
from stat_finder import find_candidates
from chart_builder import dispatch as build_chart
from compose import make_output_dir, build_caption, save_package

meta = {
    "fixture_id": 999, "team_a": "Brazil", "team_b": "Japan",
    "team_a_id": 6, "team_b_id": 12, "score_a": 2, "score_b": 1,
    "round": "Round of 16", "competition": "FIFA World Cup 2026",
    "date": "2026-06-29", "venue": "MetLife Stadium",
    "goal_scorers": [
        {"team": "Brazil", "player": "Vini Silva", "minute": 34},
        {"team": "Japan",  "player": "Kaoru Tanaka", "minute": 78},
        {"team": "Brazil", "player": "Rafael Costa", "minute": 93},
    ],
    "went_to_pens": False,
}

df = pd.DataFrame({
    "Brazil": {"Total Shots": 21, "Shots on Goal": 8, "Shots insidebox": 14,
               "Ball Possession": 63, "Passes accurate": 512,
               "Goalkeeper Saves": 3},
    "Japan":  {"Total Shots": 6,  "Shots on Goal": 4, "Shots insidebox": 3,
               "Ball Possession": 37, "Passes accurate": 240,
               "Goalkeeper Saves": 6},
})

players = [
    {"team": "Brazil", "player_name": "Vini Silva", "position": "F",
     "minutes": 90, "rating": 8.7, "goals": 1, "assists": 1,
     "shots_total": 6, "shots_on_target": 3, "passes_total": 41,
     "passes_accuracy": 88, "dribbles_success": 5, "tackles": 1, "saves": 0},
    {"team": "Japan", "player_name": "Kaoru Tanaka", "position": "M",
     "minutes": 90, "rating": 7.9, "goals": 1, "assists": 0,
     "shots_total": 3, "shots_on_target": 2, "passes_total": 55,
     "passes_accuracy": 91, "dribbles_success": 2, "tackles": 3, "saves": 0},
    {"team": "Brazil", "player_name": "Rafael Costa", "position": "F",
     "minutes": 30, "rating": 7.6, "goals": 1, "assists": 0,
     "shots_total": 2, "shots_on_target": 2, "passes_total": 12,
     "passes_accuracy": 83, "dribbles_success": 1, "tackles": 0, "saves": 0},
    {"team": "Brazil", "player_name": "Marco Nunes", "position": "M",
     "minutes": 90, "rating": 7.4, "goals": 0, "assists": 1,
     "shots_total": 1, "shots_on_target": 0, "passes_total": 88,
     "passes_accuracy": 94, "dribbles_success": 3, "tackles": 4, "saves": 0},
]

historical = {
    "Brazil": {"knockout_appearances": 5, "knockout_wins": 4},
    "Japan":  {"knockout_appearances": 4, "knockout_wins": 0},
}

if os.path.isdir("output"):
    shutil.rmtree("output")

chart_types_seen = set()
for atype in ["TEAM", "PLAYER", "HISTORICAL", "TIMELINE", "SHOT_MAP"]:
    cands = find_candidates(atype, df, players, historical, meta)
    assert cands, f"{atype}: no candidates"
    assert cands == sorted(cands, key=lambda c: c.score, reverse=True)
    print(f"{atype:11s} -> {len(cands)} candidates | top: {cands[0].headline[:70]}")
    for i, c in enumerate(cands):
        out_dir = make_output_dir(meta)
        img = build_chart(c, meta, df, out_dir)
        assert os.path.exists(img) and os.path.getsize(img) > 5000
        cap = build_caption(c, meta)
        assert len(cap) <= 275, f"caption too long: {len(cap)}"
        save_package(img, cap, out_dir)
        chart_types_seen.add(c.chart_data.get("type", "stat_card"))
        # keep one rendered sample per analysis type
        if i == 0:
            shutil.copy(img, f"output/sample_{atype}.png")

print("\nChart types exercised:", sorted(chart_types_seen))
expected = {"bar", "stat_card", "timeline", "player_bar", "player_spotlight", "shot_breakdown"}
missing = expected - chart_types_seen
print("Missing chart types:", missing or "none")
print("caption.txt exists:", os.path.exists("output/2026-06-29_BRA_JAP/caption.txt"))
print("\nALL SMOKE TESTS PASSED")
