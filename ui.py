"""
ui.py — Streamlit UI for the World Cup Stat Bot

Run with:
    streamlit run ui.py
"""

import os
import streamlit as st
from PIL import Image

from api_client import verify_api_key, get_fixtures_by_date
from match_data import load_match
from stat_finder import find_candidates
from chart_builder import dispatch as build_chart
from compose import make_output_dir, build_caption, save_package


# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="World Cup Stat Bot",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

st.markdown(
    """
<style>
.stApp {
    background-color: #f8f9fb;
}

.block-container {
    padding-top: 1.5rem;
}

.caption-box {
    background: #0b1f3a;
    color: white;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    font-size: 0.95rem;
    line-height: 1.6;
    white-space: pre-wrap;
}

.section-label {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6b7280;
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────

defaults = {
    "meta": None,
    "team_df": None,
    "players": None,
    "historical": None,
    "candidates": [],
    "chosen_idx": 0,
    "image_path": None,
    "caption": "",
    "out_dir": None,
    "analysis_type": "TEAM",
    "fixture_id": "869653",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:

    st.title("⚽ World Cup Stat Bot")
    st.caption(
        "Generates Opta-style football charts for manual posting on X."
    )

    st.divider()

    # API Status

    with st.expander("🔑 API Status"):

        if st.button("Check API key"):

            with st.spinner("Checking..."):

                try:
                    info = verify_key = verify_api_key()

                    requests_used = (
                        info.get("requests", {})
                        .get("current", "?")
                    )

                    st.success(
                        f"Key valid · {requests_used}/100 requests used today"
                    )

                except Exception as e:
                    st.error(str(e))

    st.divider()
    # ─────────────────────────────────────────────
# Fixture selector
# ─────────────────────────────────────────────

    st.markdown(
        '<div class="section-label">1 · Select a Match</div>',
        unsafe_allow_html=True,
    )

    from datetime import date

    selected_date = st.date_input(
        "Match date",
        value=date(2024, 8, 17),
    )


    if st.button("📅 Load fixtures", use_container_width=True):

        with st.spinner("Fetching fixtures..."):

            try:

                fixtures = get_fixtures_by_date(
                    selected_date.isoformat()
                )

                if not fixtures:

                    st.warning(
                        "No fixtures found for this date."
                    )

                else:

                    for fix in fixtures:

                        fid = fix["fixture"]["id"]

                        home = fix["teams"]["home"]["name"]
                        away = fix["teams"]["away"]["name"]

                        status = fix["fixture"]["status"]["short"]

                        gh = fix["goals"]["home"]
                        ga = fix["goals"]["away"]

                        score = (
                            f"{gh}-{ga}"
                            if gh is not None
                            else "vs"
                        )

                        st.code(
                            f"{fid} | {home} {score} {away} [{status}]"
                        )


            except Exception as e:

                st.error(str(e))



    fixture_input = st.text_input(
        "Fixture ID",
        value=st.session_state.fixture_id,
        placeholder="Example: 123456",
        help="Enter API-Football fixture ID",
    )


    st.session_state.fixture_id = fixture_input



    ANALYSIS_OPTIONS = {

        "⚔️ Team Comparison": "TEAM",

        "🧑 Player Focus": "PLAYER",

        "📜 Historical Milestone": "HISTORICAL",

        "⏱️ Goal Timeline": "TIMELINE",

        "🎯 Shot Map": "SHOT_MAP",

    }



    analysis_label = st.radio(
        "What do you want to analyse?",
        list(ANALYSIS_OPTIONS.keys()),
    )


    st.session_state.analysis_type = (
        ANALYSIS_OPTIONS[analysis_label]
    )



    st.divider()



    load_btn = st.button(
        "⚡ Load Match & Analyse",
        use_container_width=True,
        type="primary",
        disabled=not fixture_input.strip().isdigit(),
    )



# ─────────────────────────────────────────────
# MAIN PANEL
# ─────────────────────────────────────────────

st.markdown("## 📊 Analysis Output")



if load_btn and fixture_input.strip().isdigit():

    fid = int(fixture_input.strip())


    with st.spinner(
        f"Fetching fixture {fid}..."
    ):

        try:

            (
                meta,
                team_df,
                players,
                historical,

            ) = load_match(fid)


            st.session_state.meta = meta
            st.session_state.team_df = team_df
            st.session_state.players = players
            st.session_state.historical = historical


            candidates = find_candidates(
                st.session_state.analysis_type,
                team_df,
                players,
                historical,
                meta,
            )


            st.session_state.candidates = candidates
            st.session_state.chosen_idx = 0
            st.session_state.image_path = None
            st.session_state.caption = ""
            st.session_state.out_dir = None



        except Exception as e:

            st.error(
                f"Error loading match: {e}"
            )
            # ─────────────────────────────────────────────
# Match header
# ─────────────────────────────────────────────

if st.session_state.meta:

    meta = st.session_state.meta


    col1, col2, col3 = st.columns([3, 1, 3])


    with col1:
        st.markdown(
            f"### {meta['team_a']}"
        )


    with col2:

        st.markdown(
            f"""
            <h2 style='text-align:center; color:#0b1f3a;'>
            {meta['score_a']} – {meta['score_b']}
            </h2>
            """,
            unsafe_allow_html=True,
        )


    with col3:

        st.markdown(
            f"### {meta['team_b']}"
        )


    st.caption(
        f"{meta.get('round','')} · "
        f"{meta.get('competition','Premier League')} · "
        f"{meta.get('venue','Unknown venue')}"
    )


    st.divider()



# ─────────────────────────────────────────────
# Candidate selector
# ─────────────────────────────────────────────

if st.session_state.candidates:


    st.markdown(
        "#### 🏆 Ranked Stat Candidates"
    )


    st.caption(
        "Select the strongest statistical angle."
    )


    candidate_labels = [

        (
            f"[{i}] score={c.score:.1f} · "
            f"{c.stat_type} — "
            f"{c.headline[:90]}"
            f"{'…' if len(c.headline) > 90 else ''}"
        )

        for i, c in enumerate(
            st.session_state.candidates
        )

    ]



    selected_candidate = st.radio(

        "Choose a candidate:",

        candidate_labels,

        index=st.session_state.chosen_idx,

    )



    new_idx = candidate_labels.index(
        selected_candidate
    )



    if new_idx != st.session_state.chosen_idx:

        st.session_state.chosen_idx = new_idx

        st.session_state.image_path = None



    st.divider()



    candidate = (
        st.session_state.candidates[
            st.session_state.chosen_idx
        ]
    )



    col_chart, col_caption = st.columns(
        [1.1, 1]
    )



    # ─────────────────────────────────────────
    # Chart area
    # ─────────────────────────────────────────

    with col_chart:


        st.markdown(
            "#### 🖼️ Chart Preview"
        )


        gen_btn = st.button(
            "🔄 Generate / Refresh Chart",
            type="primary",
        )



        if (
            gen_btn
            or (
                st.session_state.image_path is None
                and st.session_state.meta is not None
            )
        ):


            with st.spinner(
                "Building chart..."
            ):


                try:


                    out_dir = make_output_dir(
                        st.session_state.meta
                    )


                    st.session_state.out_dir = out_dir



                    image_path = build_chart(

                        candidate,

                        st.session_state.meta,

                        st.session_state.team_df,

                        out_dir,

                    )


                    caption = build_caption(

                        candidate,

                        st.session_state.meta,

                    )



                    save_package(

                        image_path,

                        caption,

                        out_dir,

                    )



                    st.session_state.image_path = image_path

                    st.session_state.caption = caption



                except Exception as e:


                    st.error(
                        f"Chart error: {e}"
                    )



        if (
            st.session_state.image_path
            and os.path.exists(
                st.session_state.image_path
            )
        ):


            img = Image.open(
                st.session_state.image_path
            )


            st.image(
                img,
                use_container_width=True,
            )


            with open(
                st.session_state.image_path,
                "rb"
            ) as f:


                st.download_button(

                    "⬇️ Download chart.png",

                    data=f,

                    file_name="chart.png",

                    mime="image/png",

                    use_container_width=True,

                )
                # ─────────────────────────────────────────
    # Caption area
    # ─────────────────────────────────────────

    with col_caption:

        st.markdown(
            "#### 📝 Caption"
        )


        if st.session_state.caption:


            char_count = len(
                st.session_state.caption
            )


            st.caption(
                f"{char_count} / 275 characters"
            )



            edited_caption = st.text_area(

                "Edit caption:",

                value=st.session_state.caption,

                height=180,

            )



            st.session_state.caption = edited_caption



            st.markdown(

                f"""
                <div class="caption-box">
                {edited_caption}
                </div>
                """,

                unsafe_allow_html=True,

            )



            if st.session_state.out_dir:


                caption_path = os.path.join(

                    st.session_state.out_dir,

                    "caption.txt",

                )


                with open(

                    caption_path,

                    "w",

                    encoding="utf-8",

                ) as f:


                    f.write(
                        edited_caption
                    )



        st.divider()



        st.markdown(
            "#### 🐦 How to Post on X"
        )


        st.markdown(
            """
1. Download **chart.png**.
2. Open X (Twitter).
3. Click Compose.
4. Upload the chart image.
5. Paste the caption.
6. Review and post.
"""
        )



        if st.session_state.out_dir:


            st.success(

                f"Files saved to: "
                f"`{os.path.abspath(st.session_state.out_dir)}`"

            )



# ─────────────────────────────────────────────
# Empty state
# ─────────────────────────────────────────────

elif not st.session_state.meta:


    st.info(

        "👈 Use the sidebar to load a completed match "
        "and choose an analysis type."

    )