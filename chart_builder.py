"""
chart_builder.py

All chart rendering. Five chart types, all in the @OptaAnalystUS style:
  stat_card        — dark card, large headline text
  bar              — horizontal bars, two teams, one metric
  timeline         — horizontal goal timeline
  player_bar       — horizontal bars across top N players
  player_spotlight — single-player stat summary card
  shot_breakdown   — grouped bars for shots on/off target, inside/outside box
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

DARK    = "#0b1f3a"
LIGHT   = "#9ca3af"
ACCENT  = "#e10600"
WHITE   = "#ffffff"
BG      = "#ffffff"
DPI     = 220


def _footer(fig, source="Data: API-Football  |  api-football.com"):
    fig.text(0.99, 0.01, source, ha="right", va="bottom",
             fontsize=7, color="#aaaaaa")


# ── Stat Card ──────────────────────────────────────────────────────
def build_stat_card(meta: dict, headline: str, out_path: str) -> str:
    fig, ax = plt.subplots(figsize=(6.4, 4), dpi=DPI)
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")

    ax.text(0.05, 0.91, meta["competition"].upper(),
            color=ACCENT, weight="bold", fontsize=10,
            transform=ax.transAxes, va="top")
    ax.text(0.05, 0.81, meta["round"],
            color=LIGHT, fontsize=9,
            transform=ax.transAxes, va="top")
    ax.text(0.05, 0.63, headline,
            color=WHITE, weight="bold", fontsize=14,
            wrap=True, multialignment="left",
            transform=ax.transAxes, va="top", ha="left")
    score_line = (f"{meta['team_a']}  {meta['score_a']} – "
                  f"{meta['score_b']}  {meta['team_b']}   |   {meta['date']}")
    ax.text(0.05, 0.09, score_line,
            color=LIGHT, fontsize=8,
            transform=ax.transAxes, va="bottom")

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=DARK, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Horizontal Bar (two teams) ─────────────────────────────────────
def build_bar(meta: dict, df, stat_name: str, out_path: str) -> str:
    team_a, team_b = meta["team_a"], meta["team_b"]
    try:
        val_a = float(df.loc[stat_name, team_a])
        val_b = float(df.loc[stat_name, team_b])
    except KeyError:
        val_a, val_b = 0.0, 0.0

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.barh([team_b, team_a], [val_b, val_a],
            color=[LIGHT, DARK], height=0.45)

    mx = max(val_a, val_b, 1)
    is_pct = "%" in stat_name or "Possession" in stat_name or "Passes %" in stat_name
    for val, y in [(val_b, 0), (val_a, 1)]:
        label = f"{int(val)}%" if is_pct else str(int(val))
        ax.text(val + mx * 0.025, y, label,
                va="center", ha="left",
                fontsize=13, weight="bold", color=DARK)

    ax.set_title(stat_name, fontsize=13, weight="bold",
                 loc="left", color=DARK, pad=12)
    ax.set_xlabel(f"{meta['round']}  —  {meta['competition']}",
                  fontsize=8, color="#666")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(left=False, labelsize=10)
    ax.set_xticks([])
    ax.set_xlim(0, mx * 1.22)
    ax.set_yticks([0, 1])
    ax.set_yticklabels([team_b, team_a])

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Goal Timeline ──────────────────────────────────────────────────
def build_timeline(meta: dict, goals: list, out_path: str) -> str:
    team_a, team_b = meta["team_a"], meta["team_b"]
    fig, ax = plt.subplots(figsize=(7, 2.8), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.hlines(0, 0, 105, color="#ddd", linewidth=4, zorder=1)
    ax.vlines([45, 90], -0.12, 0.12, color="#ccc",
              linewidth=1, linestyle="--")
    ax.text(45, -0.28, "HT", ha="center", fontsize=7, color="#aaa")
    ax.text(90, -0.28, "FT", ha="center", fontsize=7, color="#aaa")

    for g in goals:
        color = DARK if g["team"] == team_a else ACCENT
        ax.plot(g["minute"], 0, "o", color=color,
                markersize=12, zorder=3)
        ax.text(g["minute"], 0.22,
                f"{g['player'].split()[-1]}\n{g['minute']}'",
                ha="center", va="bottom",
                fontsize=7.5, color=DARK, weight="bold")

    ax.legend(handles=[
        mpatches.Patch(color=DARK,   label=team_a),
        mpatches.Patch(color=ACCENT, label=team_b),
    ], loc="lower right", fontsize=8, frameon=False)

    ax.set_title(
        f"{team_a}  {meta['score_a']} – {meta['score_b']}  {team_b}   |   Goal Timeline",
        fontsize=11, weight="bold", color=DARK, loc="left")
    ax.set_xlim(-3, 108)
    ax.set_ylim(-0.65, 0.7)
    ax.axis("off")

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Player Bar ─────────────────────────────────────────────────────
def build_player_bar(meta: dict, players: list,
                     metric: str, out_path: str) -> str:
    top = players[:6]
    names  = [p["player_name"].split()[-1] for p in top]
    values = [p.get(metric, 0) for p in top]
    colors = [DARK if p["team"] == meta["team_a"] else ACCENT for p in top]

    fig, ax = plt.subplots(figsize=(6.4, 4), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.barh(names[::-1], values[::-1],
                   color=colors[::-1], height=0.55)
    mx = max(values) if values else 1
    for bar, val in zip(bars, values[::-1]):
        label = f"{val:.1f}" if isinstance(val, float) else str(val)
        ax.text(bar.get_width() + mx * 0.02, bar.get_y() + bar.get_height() / 2,
                label, va="center", fontsize=11, weight="bold", color=DARK)

    metric_label = metric.replace("_", " ").title()
    ax.set_title(f"Top Players — {metric_label}",
                 fontsize=13, weight="bold", loc="left", color=DARK, pad=12)
    ax.set_xlabel(f"{meta['round']}  —  {meta['competition']}",
                  fontsize=8, color="#666")
    ax.legend(handles=[
        mpatches.Patch(color=DARK,   label=meta["team_a"]),
        mpatches.Patch(color=ACCENT, label=meta["team_b"]),
    ], fontsize=8, frameon=False, loc="lower right")

    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(left=False, labelsize=9)
    ax.set_xticks([])
    ax.set_xlim(0, mx * 1.22)

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Player Spotlight ───────────────────────────────────────────────
def build_player_spotlight(meta: dict, player: dict,
                           minute: int, out_path: str) -> str:
    fig, ax = plt.subplots(figsize=(6.4, 4), dpi=DPI)
    fig.patch.set_facecolor(DARK)
    ax.set_facecolor(DARK)
    ax.axis("off")

    ax.text(0.05, 0.91, meta["competition"].upper(),
            color=ACCENT, weight="bold", fontsize=10,
            transform=ax.transAxes, va="top")
    ax.text(0.05, 0.81, f"GOAL {minute}' — {player['player_name']}",
            color=WHITE, weight="bold", fontsize=15,
            transform=ax.transAxes, va="top")
    ax.text(0.05, 0.68, player["team"],
            color=LIGHT, fontsize=10,
            transform=ax.transAxes, va="top")

    stats_text = (
        f"Rating: {player['rating']:.1f}/10\n"
        f"Shots: {player['shots_total']}  (on target: {player['shots_on_target']})\n"
        f"Passes: {player['passes_total']}  ({player['passes_accuracy']}% accuracy)\n"
        f"Goals: {player['goals']}   Assists: {player['assists']}"
    )
    ax.text(0.05, 0.52, stats_text,
            color=WHITE, fontsize=11, linespacing=1.7,
            transform=ax.transAxes, va="top",
            family="monospace")

    score_line = (f"{meta['team_a']}  {meta['score_a']} – "
                  f"{meta['score_b']}  {meta['team_b']}   |   {meta['date']}")
    ax.text(0.05, 0.09, score_line,
            color=LIGHT, fontsize=8,
            transform=ax.transAxes, va="bottom")

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=DARK, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Shot Breakdown ─────────────────────────────────────────────────
def build_shot_breakdown(meta: dict, chart_data: dict, out_path: str) -> str:
    teams    = chart_data["teams"]
    total    = chart_data["total"]
    on_tgt   = chart_data["on_target"]
    in_box   = chart_data["inside_box"]
    off_tgt  = [t - o for t, o in zip(total, on_tgt)]

    x    = range(len(teams))
    w    = 0.25
    fig, ax = plt.subplots(figsize=(6.4, 4), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    import numpy as np
    x = np.arange(len(teams))
    ax.bar(x - w, on_tgt,  w, label="On Target",    color=DARK)
    ax.bar(x,     off_tgt, w, label="Off Target",   color=LIGHT)
    ax.bar(x + w, in_box,  w, label="Inside Box",   color=ACCENT)

    ax.set_xticks(x)
    ax.set_xticklabels(teams, fontsize=11)
    ax.set_title("Shot Breakdown", fontsize=13, weight="bold",
                 loc="left", color=DARK, pad=12)
    ax.set_xlabel(f"{meta['round']}  —  {meta['competition']}",
                  fontsize=8, color="#666")
    ax.legend(fontsize=8, frameon=False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#ddd")
    ax.spines["left"].set_color("#ddd")

    _footer(fig)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Master Dispatcher ──────────────────────────────────────────────
def dispatch(candidate, meta: dict, df, out_dir: str) -> str:
    import os
    cd   = candidate.chart_data
    ct   = cd.get("type", "stat_card")
    path = os.path.join(out_dir, "chart.png")

    if ct == "bar":
        return build_bar(meta, df, cd.get("stat", "Total Shots"), path)
    elif ct == "timeline":
        return build_timeline(meta, cd.get("goals", []), path)
    elif ct == "player_bar":
        return build_player_bar(meta, cd["players"], cd["metric"], path)
    elif ct == "player_spotlight":
        return build_player_spotlight(meta, cd["player"], cd["minute"], path)
    elif ct == "shot_breakdown":
        return build_shot_breakdown(meta, cd, path)
    else:
        return build_stat_card(meta, candidate.headline, path)
