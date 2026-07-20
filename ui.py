"""
ui.py  —  Streamlit UI for the World Cup Stat Bot

Run with:
    streamlit run ui.py

The UI has three panels:
  LEFT SIDEBAR  — fixture lookup and analysis-type selector
  MAIN PANEL    — ranked candidate list, chart preview, caption
  BOTTOM BAR    — save confirmation and posting instructions
"""

import os
import streamlit as st
from PIL import Image

from api_client   import verify_api_key, get_todays_fixtures
from match_data   import load_match
from stat_finder  import find_candidates
from chart_builder import dispatch as build_chart
from compose       import make_output_dir, build_caption, save_package

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="World Cup Stat Bot",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8f9fb; }
    .block-container { padding-top: 1.5rem; }
    .caption-box {
        background: #0b1f3a;
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        font-size: 0.95rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────
for key, default in {
    "meta":          None,
    "team_df":       None,
    "players":       None,
    "historical":    None,
    "candidates":    [],
    "chosen_idx":    0,
    "image_path":    None,
    "caption":       "",
    "out_dir":       None,
    "analysis_type": "TEAM",
    "fixture_id":    "869653",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚽ World Cup Stat Bot")
    st.caption("Generates @OptaAnalystUS-style charts for manual posting on X.")

    st.divider()

    # ── API status ────────────────────────────────────────────────
    with st.expander("🔑 API Status", expanded=False):
        if st.button("Check API key"):
            with st.spinner("Checking…"):
                try:
                    info = verify_api_key()
                    requests_used = (info.get("requests", {})
                                         .get("current", "?"))
                    st.success(f"Key valid  ·  {requests_used}/100 requests used today")
                except Exception as e:
                    st.error(str(e))

    st.divider()

    # ── Fixture selector ──────────────────────────────────────────
    st.markdown('<div class="section-label">1 · Select a Match</div>',
                unsafe_allow_html=True)

    if st.button("📅 Load today's fixtures", use_container_width=True):
        with st.spinner("Fetching today's fixtures…"):
            try:
                fixtures = get_todays_fixtures()
                if not fixtures:
                    st.warning("No World Cup fixtures found for today.")
                else:
                    for fix in fixtures:
                        fid    = fix["fixture"]["id"]
                        home   = fix["teams"]["home"]["name"]
                        away   = fix["teams"]["away"]["name"]
                        status = fix["fixture"]["status"]["short"]
                        gh     = fix["goals"]["home"]
                        ga     = fix["goals"]["away"]
                        score  = f"{gh}-{ga}" if gh is not None else "vs"
                        done   = status in ("FT", "AET", "PEN")
                        icon   = "✅" if done else "🕐"
                        st.code(f"{icon} {fid}  |  {home} {score} {away}  [{status}]")
            except Exception as e:
                st.error(str(e))

    fixture_input = st.text_input(
        "Fixture ID",
        placeholder="e.g. 1234567",
        value=st.session_state.fixture_id,
        help="Enter the API-Football fixture ID of a completed match.",
    )
    st.session_state.fixture_id = fixture_input

    # ── Analysis type ─────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-label">2 · Analysis Type</div>',
                unsafe_allow_html=True)

    ANALYSIS_OPTIONS = {
        "⚔️  Team Comparison":      "TEAM",
        "🧑  Player Focus":          "PLAYER",
        "📜  Historical Milestone":  "HISTORICAL",
        "⏱️  Goal Timeline":         "TIMELINE",
        "🎯  Shot Map":              "SHOT_MAP",
    }

    chosen_label = st.radio(
        "What do you want to analyse?",
        list(ANALYSIS_OPTIONS.keys()),
        index=list(ANALYSIS_OPTIONS.values()).index(
            st.session_state.analysis_type),
        label_visibility="collapsed",
    )
    st.session_state.analysis_type = ANALYSIS_OPTIONS[chosen_label]

    st.divider()

    # ── Load match button ─────────────────────────────────────────
    load_btn = st.button(
        "⚡ Load Match & Analyse",
        use_container_width=True,
        type="primary",
        disabled=not fixture_input.strip().isdigit(),
    )

# ── MAIN PANEL ────────────────────────────────────────────────────
st.markdown("## 📊 Analysis Output")

if load_btn and fixture_input.strip().isdigit():
    fid = int(fixture_input.strip())
    with st.spinner(f"Fetching fixture {fid}…"):
        try:
            meta, team_df, players, historical = load_match(fid)
            st.session_state.meta       = meta
            st.session_state.team_df    = team_df
            st.session_state.players    = players
            st.session_state.historical = historical

            candidates = find_candidates(
                st.session_state.analysis_type,
                team_df, players, historical, meta,
            )
            st.session_state.candidates  = candidates
            st.session_state.chosen_idx  = 0
            st.session_state.image_path  = None
            st.session_state.caption     = ""
            st.session_state.out_dir     = None

        except Exception as e:
            st.error(f"Error loading match: {e}")

# ── Match header ─────────────────────────────────────────────────
if st.session_state.meta:
    meta = st.session_state.meta
    col1, col2, col3 = st.columns([3, 1, 3])
    with col1:
        st.markdown(f"### {meta['team_a']}")
    with col2:
        st.markdown(
            f"<h2 style='text-align:center; color:#0b1f3a;'>"
            f"{meta['score_a']} – {meta['score_b']}</h2>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(f"### {meta['team_b']}")

    st.caption(
        f"{meta['round']}  ·  {meta['competition']}  ·  "
        f"{meta['venue']}  ·  {meta['date']}"
    )
    st.divider()

# ── Candidate selector ────────────────────────────────────────────
if st.session_state.candidates:
    st.markdown("#### 🏆 Ranked Stat Candidates")
    st.caption("The bot has ranked these angles by tweetability. "
               "Select the one you want to use.")

    candidate_labels = [
        f"[{i}]  score={c.score:.1f}  ·  {c.stat_type}  —  {c.headline[:90]}{'…' if len(c.headline)>90 else ''}"
        for i, c in enumerate(st.session_state.candidates)
    ]

    chosen_label = st.radio(
        "Choose a candidate:",
        candidate_labels,
        index=st.session_state.chosen_idx,
        label_visibility="collapsed",
    )
    new_idx = candidate_labels.index(chosen_label)
    if new_idx != st.session_state.chosen_idx:
        st.session_state.chosen_idx = new_idx
        st.session_state.image_path = None  # force chart rebuild

    st.divider()

    # ── Generate chart ────────────────────────────────────────────
    candidate = st.session_state.candidates[st.session_state.chosen_idx]

    col_chart, col_caption = st.columns([1.1, 1])

    with col_chart:
        st.markdown("#### 🖼️ Chart Preview")
        gen_btn = st.button("🔄 Generate / Refresh Chart", type="primary")

        if gen_btn or (st.session_state.image_path is None and
                       st.session_state.meta is not None):
            with st.spinner("Building chart…"):
                out_dir = make_output_dir(st.session_state.meta)
                st.session_state.out_dir = out_dir
                try:
                    image_path = build_chart(
                        candidate,
                        st.session_state.meta,
                        st.session_state.team_df,
                        out_dir,
                    )
                    caption = build_caption(candidate, st.session_state.meta)
                    save_package(image_path, caption, out_dir)
                    st.session_state.image_path = image_path
                    st.session_state.caption    = caption
                except Exception as e:
                    st.error(f"Chart error: {e}")

        if st.session_state.image_path and os.path.exists(st.session_state.image_path):
            img = Image.open(st.session_state.image_path)
            st.image(img, use_container_width=True)

            with open(st.session_state.image_path, "rb") as f:
                st.download_button(
                    "⬇️  Download chart.png",
                    data=f,
                    file_name="chart.png",
                    mime="image/png",
                    use_container_width=True,
                )

    with col_caption:
        st.markdown("#### 📝 Caption")
        if st.session_state.caption:
            char_count = len(st.session_state.caption)
            color = "green" if char_count <= 275 else "red"
            st.markdown(
                f'<div class="section-label" style="color:{color};">'
                f'{char_count} / 275 characters</div>',
                unsafe_allow_html=True,
            )
            edited_caption = st.text_area(
                "Edit caption if needed:",
                value=st.session_state.caption,
                height=180,
                label_visibility="collapsed",
            )
            st.session_state.caption = edited_caption

            st.markdown(
                f'<div class="caption-box">{edited_caption}</div>',
                unsafe_allow_html=True,
            )

            # Save edited caption
            if st.session_state.out_dir:
                caption_path = os.path.join(st.session_state.out_dir, "caption.txt")
                with open(caption_path, "w", encoding="utf-8") as f:
                    f.write(edited_caption)

        st.divider()

        # ── Posting instructions ──────────────────────────────────
        st.markdown("#### 🐦 How to Post on X")
        st.markdown("""
1. Click **⬇️ Download chart.png** above to save the image.
2. Open [x.com](https://x.com) → click the **✏️ Compose** button.
3. Click the **🖼️ Image icon** and upload `chart.png`.
4. Copy the caption text above and paste it into the post field.
5. Review, then click **Post**.
        """)

        if st.session_state.out_dir:
            st.success(
                f"Files saved to: `{os.path.abspath(st.session_state.out_dir)}`"
            )

# ── Empty state ───────────────────────────────────────────────────
elif not st.session_state.meta:
    st.info(
        "👈  Use the sidebar to load a completed match and choose your "
        "analysis type, then click **Load Match & Analyse**."
    )
