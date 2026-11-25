"""Where should a finance graduate live? Demo website for the FDA I capstone.

Page 1 is an adaptive quiz (quiz.py) that ranks six factors from about ten trade-off questions.
Page 2 ranks counties by those factors and compares two counties on a small dashboard.
An Oregon Trail style homage (original pixel art, free Google fonts, no game assets).
Run locally from this folder:  streamlit run app.py
The data is built by build_demo_data.py.
"""
import json
import math
import random
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quiz  # noqa: E402
DATA = HERE / "data"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

GREEN = "#8BE04E"
AMBER = "#F2A541"
CREAM = "#E9F5DB"
PANEL = "#18211A"
INK = "#0D110C"
RED = "#E4572E"

FACTORS = {
    "Rent": {"column": "rent_2026_09", "higher_is_better": False, "header": "Rent per month",
             "format": "${:,.0f}", "table_format": "$%,.0f", "color": GREEN},
    "Job outlook": {"column": "job_growth", "higher_is_better": True, "header": "Job growth",
                    "format": "{:.1f}%", "table_format": "%.1f%%", "color": AMBER},
    "Comfortable weather": {"column": "comfortable_months", "higher_is_better": True,
                            "header": "Comfortable months", "format": "{:.0f}", "table_format": "%.0f",
                            "color": "#5BC0EB"},
    "Education": {"column": "some_college", "higher_is_better": True, "header": "Some college",
                  "format": "{:.1f}%", "table_format": "%.1f%%", "color": "#C3A6FF"},
    "Culture": {"column": "culture", "higher_is_better": True, "header": "Arts per 10,000",
                "format": "{:.1f}", "table_format": "%.1f", "color": "#FF6F91"},
    "Family": {"column": "miles_from_family", "higher_is_better": False, "header": "Miles from family",
               "format": "{:,.0f} mi", "table_format": "%,.0f", "color": CREAM},
}
PLACE_CHOICES = ["No preference", "A metro area", "A smaller city", "Outside any metro or micro area"]
# The Census Bureau's four regions. Puerto Rico belongs to none, so it shows only under All.
REGIONS = {
    "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
    "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South": ["DE", "DC", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}
SHOW_COUNTS = [10, 15, 20, 50]
CHART_MAX = 20  # the "what drives" chart stops at 20 bars, so it stays readable
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "the District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"}

st.set_page_config(page_title="Where should a finance graduate live?", page_icon="🐂", layout="wide")

# ------------------------------------------------------------------ look and feel
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Space+Mono:wght@400;700&display=swap');
* {{ font-variant-ligatures: none; font-feature-settings: "liga" 0, "clig" 0; }}
h1, h2, h3, .pixel {{ font-family: 'Press Start 2P', monospace !important; letter-spacing: 0.02em; }}
h1 {{ font-size: clamp(1.1rem, 2.6vw, 1.8rem) !important; line-height: 1.5 !important; color: {GREEN}; }}
h2 {{ font-size: clamp(0.9rem, 1.8vw, 1.15rem) !important; line-height: 1.6 !important; color: {AMBER}; }}
h3 {{ font-size: 0.85rem !important; line-height: 1.6 !important; }}
.stMarkdown p, .stMarkdown li, label, .stCaption, [data-testid="stSidebar"] p {{
  font-family: 'VT323', monospace !important; font-size: 1.3rem !important; line-height: 1.25 !important; }}
[data-testid="stTabs"] [role="tablist"] {{ gap: 16px; flex-wrap: wrap; margin: 34px 0 6px 0; overflow: visible !important; }}
.st-key-spk_box {{ position: relative; height: 0; overflow: visible; z-index: 5; margin-bottom: -1rem; }}
.st-key-spk_box [data-testid="stElementContainer"], .st-key-spk_box iframe {{
  position: absolute !important; top: 16px; right: 16px; width: 46px !important; height: 46px !important; }}
.banner.has-speaker .kicker, .banner.has-speaker h1 {{ padding-right: 56px; }}
[data-testid="stTab"] {{ flex: 1 1 0; min-width: 150px; height: auto; padding: 16px 10px; justify-content: center;
  align-items: center; min-height: 64px; background: {PANEL}; border: 3px solid {GREEN}; box-shadow: 4px 4px 0 #050705;
  transition: transform 0.1s, box-shadow 0.1s; }}
[data-testid="stTab"]:hover {{ transform: translate(-2px, -2px); box-shadow: 6px 6px 0 #050705; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {GREEN}; }}
[data-testid="stTab"] p {{ font-family: 'Press Start 2P', monospace !important; font-size: 0.72rem !important;
  line-height: 1.6 !important; text-align: center; color: {CREAM}; white-space: normal !important; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: {INK} !important; }}
[data-testid="stTabs"] [role="tablist"] > :not([data-testid="stTab"]) {{ display: none; }}
[data-testid="stTabs"] [role="tablist"], [data-testid="stTabs"] [role="tablist"]::after {{ border: 0 !important; }}
[data-testid="stTabPanel"] {{ padding-top: 22px; }}
.banner {{ border: 4px solid {GREEN}; background: {PANEL}; padding: 18px 22px 10px 22px; margin-bottom: 18px;
  box-shadow: 6px 6px 0 {INK}, 6px 6px 0 2px {GREEN}; }}
.banner .kicker {{ font-family: 'Press Start 2P', monospace; color: {AMBER}; font-size: 0.75rem; }}
.banner .tag {{ font-family: 'VT323', monospace; font-size: 1.45rem; color: {CREAM}; }}
.track {{ position: relative; height: 70px; overflow: hidden; border-bottom: 4px dashed #3c5236; margin: 6px 0 4px 0; }}
.wagon {{ position: absolute; bottom: 2px; left: calc(100% - 200px); animation: roll 3.2s steps(16) 1 both; }}
@keyframes roll {{ from {{ left: -200px; }} to {{ left: calc(100% - 200px); }} }}
.panel {{ border: 3px solid {GREEN}; background: {PANEL}; padding: 14px 18px; margin: 10px 0;
  box-shadow: 4px 4px 0 #050705; container-type: inline-size; }}
.arrived {{ font-family: 'Press Start 2P', monospace; color: {GREEN}; overflow: hidden; white-space: nowrap;
  border-right: 0.6em solid transparent; width: 0; line-height: 1.8;
  font-size: min(1rem, calc(88cqw / (var(--n) + 1)));
  animation: typing 1.1s steps(var(--n)) var(--d) forwards; }}
.arrived.last {{ animation: typing 1.1s steps(var(--n)) var(--d) forwards, blink 0.8s step-end var(--d) 6; }}
@keyframes typing {{ to {{ width: calc(var(--n) * 1ch + 0.7em); }} }}
@keyframes blink {{ 0% {{ border-color: {GREEN}; }} 50% {{ border-color: transparent; }} }}
.podium {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin: 14px 0; }}
.card {{ border: 3px solid {CREAM}; background: {PANEL}; padding: 14px; opacity: 0;
  animation: rise 0.5s ease-out forwards; box-shadow: 4px 4px 0 #050705; }}
.card.first {{ border-color: {GREEN}; }}
.card .badge {{ font-family: 'Press Start 2P', monospace; font-size: 0.7rem; background: {GREEN}; color: {INK};
  padding: 4px 8px; display: inline-block; }}
.card .name {{ font-family: 'Press Start 2P', monospace; font-size: 0.78rem; line-height: 1.6; margin: 10px 0 6px 0; }}
.card .line {{ font-family: 'VT323', monospace; font-size: 1.25rem; color: {CREAM}; }}
.card .score {{ font-family: 'VT323', monospace; font-size: 2.2rem; color: {GREEN}; line-height: 1; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(18px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.hazard {{ border-left: 6px solid {RED}; background: #221614; padding: 10px 14px; margin: 8px 0;
  font-family: 'VT323', monospace; font-size: 1.3rem; opacity: 0; animation: rise 0.5s ease-out forwards; }}
.hazard b {{ font-family: 'Press Start 2P', monospace; font-size: 0.7rem; color: {RED}; }}
.supplies {{ font-family: 'VT323', monospace; font-size: 1.25rem; }}
.supplies .row {{ display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px; }}
.supplies .pips {{ display: inline-flex; gap: 3px; }}
.supplies .pip {{ width: 10px; height: 10px; background: #2c3a28; display: inline-block; }}
.supplies .pip.on {{ background: {GREEN}; }}
.strip {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; }}
.strip .persona-name {{ font-family: 'Press Start 2P', monospace; color: {GREEN}; font-size: 0.8rem; }}
.strip .chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.strip .chip {{ font-family: 'Space Mono', monospace; font-size: 0.85rem; color: {CREAM}; border: 2px solid #3c5236;
  padding: 2px 8px; background: {PANEL}; }}
.st-key-engine_only {{ position: absolute !important; width: 1px; height: 1px; overflow: hidden; opacity: 0;
  pointer-events: none; }}
.question {{ font-family: 'Space Mono', monospace; font-weight: 700; color: {CREAM}; font-size: clamp(1.2rem, 2.2vw, 1.7rem);
  line-height: 1.25; margin: 18px 0 12px 0; animation: slidein 0.4s ease-out both; }}
.progress-label {{ font-family: 'Press Start 2P', monospace; color: {AMBER}; font-size: 0.65rem; margin-top: 6px; }}
[class*="st-key-pick_"] button {{ min-height: 150px; width: 100%; background: {PANEL}; border: 3px solid {CREAM};
  box-shadow: 5px 5px 0 #050705; animation: slidein 0.45s ease-out 0.05s both; transition: transform 0.1s, border-color 0.1s, background 0.12s; }}
[class*="st-key-pick_"][class*="_right"] button, [class*="st-key-pick_comfort_1"] button,
[class*="st-key-pick_comfort_3"] button {{ animation-delay: 0.15s; }}
[class*="st-key-pick_"] button:active {{ transform: translate(3px, 3px) scale(0.98); box-shadow: 1px 1px 0 #050705;
  border-color: {GREEN}; background: #24331F; }}
@keyframes slidein {{ from {{ opacity: 0; transform: translateX(48px); }} to {{ opacity: 1; transform: none; }} }}
[class*="st-key-pick_"] button:hover {{ background: {GREEN}; border-color: {GREEN}; transform: translate(-2px, -2px); }}
[class*="st-key-pick_"] button:hover p {{ color: {INK} !important; }}
[class*="st-key-pick_"] button p {{ font-family: 'Space Mono', monospace !important; font-weight: 400 !important;
  font-size: 1.15rem !important; line-height: 1.45 !important; white-space: normal !important; color: {CREAM}; }}
[class*="st-key-go_"] button {{ background: {GREEN}; border: 0; box-shadow: 4px 4px 0 #050705; }}
[class*="st-key-go_"] button p {{ font-family: 'Press Start 2P', monospace !important; font-size: 0.75rem !important;
  color: {INK} !important; white-space: normal !important; line-height: 1.5 !important; text-align: center; }}
[class*="st-key-go_"] button:disabled {{ background: #2c3a28; box-shadow: none; }}
[class*="st-key-go_"] button:disabled p {{ color: #7d8f76 !important; }}
.persona {{ text-align: center; padding: 20px; position: relative; min-height: 190px; }}
.persona .type {{ font-family: 'Press Start 2P', monospace; color: {GREEN}; font-size: clamp(1rem, 3vw, 1.8rem);
  margin: 14px 0; animation: drop 0.55s cubic-bezier(0.2, 1.4, 0.4, 1) 1.6s both; }}
.persona .line {{ font-family: 'Space Mono', monospace; font-weight: 400; font-size: 1.15rem; color: {CREAM};
  animation: rise 0.4s ease-out 1.95s both; }}
@keyframes drop {{ from {{ opacity: 0; transform: translateY(-60px) scale(1.5); }} to {{ opacity: 1; transform: none; }} }}
.drumroll {{ position: absolute; inset: 0; background: {PANEL}; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 14px; z-index: 3; animation: drumout 0.25s ease-in 1.5s forwards; }}
.drumroll .label {{ font-family: 'Press Start 2P', monospace; color: {AMBER}; font-size: 0.8rem;
  animation: blinktext 0.5s step-end 0s 3; }}
.drumroll .bar {{ width: 60%; height: 16px; border: 3px solid {GREEN}; padding: 2px; }}
.drumroll .bar i {{ display: block; height: 100%; width: 0; background: {GREEN}; animation: load 1.4s steps(10) forwards; }}
@keyframes drumout {{ to {{ opacity: 0; visibility: hidden; }} }}
@keyframes load {{ to {{ width: 100%; }} }}
@keyframes blinktext {{ 50% {{ opacity: 0.2; }} }}
.confetti {{ position: absolute; left: 50%; top: 45%; width: 0; height: 0; z-index: 2; pointer-events: none; }}
.confetti span {{ position: absolute; width: 9px; height: 9px; opacity: 0;
  animation: burst 1.4s cubic-bezier(0.1, 0.7, 0.3, 1) var(--delay) forwards; }}
@keyframes burst {{ 0% {{ opacity: 1; transform: translate(0, 0) rotate(0deg); }}
  80% {{ opacity: 1; }} 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) rotate(var(--r)); }} }}
.rankbar {{ display: grid; grid-template-columns: 2em 15em 1fr; align-items: center; gap: 10px; margin: 6px 0;
  font-family: 'Space Mono', monospace; font-weight: 400; font-size: 1.05rem; opacity: 0; animation: rise 0.4s ease-out forwards; }}
.rankbar .fill {{ height: 16px; background: {GREEN}; animation: grow 0.6s ease-out both; animation-delay: inherit; }}
@keyframes grow {{ from {{ width: 0; }} }}
.trail {{ position: relative; height: 46px; margin: 6px 0 6px 0; border-bottom: 4px dashed #7a5a32; }}
.trail .town {{ position: absolute; right: 0; bottom: 2px; }}
.trailwagon {{ position: absolute; bottom: 2px; left: calc((100% - 132px) * var(--to));
  animation: trailmove 0.8s steps(8) both; }}
@keyframes trailmove {{ from {{ left: calc((100% - 132px) * var(--from)); }} to {{ left: calc((100% - 132px) * var(--to)); }} }}
@media (prefers-reduced-motion: reduce) {{
  .wagon, .arrived, .card, .hazard, .question, .persona .type, .persona .line, .rankbar, .rankbar .fill,
  .trailwagon, [class*="st-key-pick_"] button {{ animation: none !important; opacity: 1 !important; }}
  .drumroll, .confetti {{ display: none !important; }}
  .arrived {{ width: auto !important; }}
}}
</style>
""", unsafe_allow_html=True)


def pixel_svg(rows, palette, size=4):
    """Draws pixel art from rows of characters, one rectangle per colored character."""
    width = max(len(r) for r in rows)
    rects = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in palette:
                rects.append(f'<rect x="{x * size}" y="{y * size}" width="{size}" height="{size}" fill="{palette[ch]}"/>')
    return (f'<svg width="{width * size}" height="{len(rows) * size}" shape-rendering="crispEdges" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(rects)}</svg>')


WAGON = [
    "....wwwwwwwwwwwwww............................",
    "...wwwwwwwwwwwwwwww...........................",
    "..wwwwwwwwwwwwwwwwww..........................",
    "..wwwwwwwwwwwwwwwwww.................h....h...",
    "..wwwwwwwwwwwwwwwwww.................hoooooh..",
    "..wwwwwwwwwwwwwwwwww..........oooooooooooooo..",
    ".bbbbbbbbbbbbbbbbbbbbb.......ooooooooooooooo..",
    ".bbbbbbbbbbbbbbbbbbbbbyyyyyyyooooooooooooooo..",
    "..bbbbbbbbbbbbbbbbbbb........oooooooooooooo...",
    "...kkkk........kkkk..........oo..oo..oo..oo...",
    "..kk..kk......kk..kk.........oo..oo..oo..oo...",
    "..kk..kk......kk..kk.........oo..oo..oo..oo...",
    "...kkkk........kkkk...........................",
]
WAGON_SVG = pixel_svg(WAGON, {"w": "#F3EBD3", "b": "#8B5A2B", "k": "#C9B79C", "o": "#A0522D",
                              "h": "#F3EBD3", "y": "#6B4423"})
SMALL_WAGON_SVG = pixel_svg(WAGON, {"w": "#F3EBD3", "b": "#8B5A2B", "k": "#C9B79C", "o": "#A0522D",
                                    "h": "#F3EBD3", "y": "#6B4423"}, size=2)
TOWN = [
    ".....f.......",
    ".....fff.....",
    ".....f.......",
    "....rrrr.....",
    "...rrrrrr....",
    "..rrrrrrrr...",
    "...wwwwww....",
    "...wwddww....",
    "...wwddww....",
]
TOWN_SVG = pixel_svg(TOWN, {"f": AMBER, "r": RED, "w": "#F3EBD3", "d": "#8B5A2B"}, size=3)
CONFETTI_COLORS = [GREEN, AMBER, "#5BC0EB", "#C3A6FF", "#FF6F91", CREAM]
MUSIC_HTML = (HERE / "music.html").read_text(encoding="utf-8")


# ------------------------------------------------------------------ data
def stamp(name):
    """The file's modified time, so a rebuilt file is never served from an old cache."""
    return (DATA / name).stat().st_mtime


@st.cache_data
def load_counties(version):
    return pd.read_csv(DATA / "county_factors.csv", dtype={"GEOID": str})


@st.cache_data
def load_geojson(version):
    with open(DATA / "us_counties.json") as f:
        return json.load(f)


@st.cache_data
def load_rent_history(version):
    history = pd.read_csv(DATA / "rent_history.csv", dtype={"GEOID": str}).set_index("GEOID")
    history.columns = pd.to_datetime(history.columns)
    return history


def comfortable_months(table, low, high):
    temps = table[["temp_" + m for m in MONTHS]]
    months = ((temps >= low) & (temps <= high)).sum(axis=1).astype(float)
    months[temps.isna().any(axis=1)] = float("nan")
    return months


def miles_between(lat1, lon1, lat2, lon2):
    """Straight-line (great-circle) distance in miles."""
    p1, p2 = math.radians(lat1), lat2.apply(math.radians)
    dlat = p2 - p1
    dlon = (lon2 - lon1).apply(math.radians)
    a = (dlat / 2).apply(math.sin) ** 2 + math.cos(p1) * p2.apply(math.cos) * (dlon / 2).apply(math.sin) ** 2
    return 3958.8 * 2 * a.apply(lambda v: math.asin(math.sqrt(v)))


def rank_counties(table, weights, active, states, place):
    ranked = table.copy()
    if states:
        ranked = ranked[ranked["USPS"].isin(states)]
    if place == "A metro area":
        ranked = ranked[ranked["area_type"] == "Metropolitan Statistical Area"]
    elif place == "A smaller city":
        ranked = ranked[ranked["area_type"] == "Micropolitan Statistical Area"]
    elif place == "Outside any metro or micro area":
        ranked = ranked[ranked["area_type"].isna()]
    in_scope = ranked.copy()
    ranked = ranked.dropna(subset=[FACTORS[n]["column"] for n in active]).copy()
    total = 0
    for name in active:
        column = FACTORS[name]["column"]
        ranked["score_" + name] = 100 * ranked[column].rank(pct=True, ascending=FACTORS[name]["higher_is_better"])
        total = total + weights[name] * ranked["score_" + name]
    ranked["fit_score"] = total / sum(weights[n] for n in active)
    ranked = ranked.sort_values("fit_score", ascending=False)
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked, in_scope


def plotly_look(fig, height):
    fig.update_layout(template="plotly_dark", paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=height,
                      font=dict(family="Courier New, monospace", color=CREAM, size=13),
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def banner(tagline, wagon=True, speaker=False):
    track = f'<div class="track"><div class="wagon">{WAGON_SVG}</div></div>' if wagon else ""
    return (f'<div class="banner{" has-speaker" if speaker else ""}"><div class="kicker">THE GRADUATE TRAIL</div>'
            f'<h1 style="margin:8px 0 2px 0;">Where should a finance graduate live?</h1>'
            f'<div class="tag">{tagline}</div>{track}</div>')


def header(tagline, wagon=True, music=True):
    if music:
        # The speaker frame sits in a zero-height box just above the banner, pinned by CSS to the
        # banner's top-right corner, so the banner spans the full width.
        with st.container(key="spk_box"):
            st.iframe(MUSIC_HTML, height=46)
        st.markdown(banner(tagline, wagon, speaker=True), unsafe_allow_html=True)
    else:
        # No music on this page: the engine loads out of sight for the pick and reveal sounds only.
        st.markdown(banner(tagline, wagon) + '<div class="no-music" hidden></div>', unsafe_allow_html=True)
        with st.container(key="engine_only"):
            st.iframe(MUSIC_HTML, height=1)


# ------------------------------------------------------------------ session state
def start_quiz():
    st.session_state.page = "quiz"
    st.session_state.step = "family"
    st.session_state.seed = random.randint(0, 10**9)
    st.session_state.answers = []
    st.session_state.family = None
    st.session_state.comfort = (55, 75)
    st.session_state.retake = False


def retake_quiz():
    """A new set of trade-off questions. The family and comfy-day answers are kept."""
    st.session_state.page = "quiz"
    st.session_state.step = "tradeoffs"
    st.session_state.seed = random.randint(0, 10**9)
    st.session_state.answers = []
    st.session_state.retake = True
    st.session_state.trail_fraction = 0.0


if "page" not in st.session_state:
    start_quiz()

counties = load_counties(stamp("county_factors.csv"))
state = st.session_state


def quiz_factors():
    return [f for f in quiz.FACTORS if f != "Family" or state.family]


def choose_family(geoid):
    state.family = geoid
    state.step = "comfort"


def choose_comfort(low_high):
    state.comfort = low_high
    state.step = "tradeoffs"


def answer(winner):
    state.answers.append(winner)


def go_back():
    if state.step == "reveal":
        state.step = "tradeoffs"
        state.answers.pop()
    elif state.step == "tradeoffs" and state.answers:
        state.answers.pop()
    elif state.step == "tradeoffs" and not state.get("retake"):
        state.step = "comfort"
    elif state.step == "comfort":
        state.step = "family"


def hit_the_trail():
    state.page = "results"


# ------------------------------------------------------------------ page 1, the quiz
def trail_progress(label, fraction):
    """A dirt trail with the wagon rolling from its last spot to its new one, and a town at the end."""
    previous = state.get("trail_fraction", fraction)
    state.trail_fraction = fraction
    st.markdown(f'<div class="progress-label">{label}</div><div class="trail"><div class="town">{TOWN_SVG}</div>'
                f'<div class="trailwagon" style="--from:{previous:.3f};--to:{fraction:.3f}">{SMALL_WAGON_SVG}</div></div>',
                unsafe_allow_html=True)


def confetti_html(seed):
    rng = random.Random(seed)
    pieces = []
    for _ in range(42):
        angle = rng.uniform(0, 2 * math.pi)
        distance = rng.uniform(110, 260)
        dx = distance * math.cos(angle)
        dy = distance * math.sin(angle) * 0.7 + rng.uniform(40, 120)
        pieces.append(f'<span style="--dx:{dx:.0f}px;--dy:{dy:.0f}px;--r:{rng.randint(-540, 540)}deg;'
                      f'--delay:{1.62 + rng.uniform(0, 0.12):.2f}s;background:{rng.choice(CONFETTI_COLORS)}"></span>')
    return '<div class="confetti">' + "".join(pieces) + "</div>"


HIDE_SIDEBAR = ('[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], '
                '[data-testid="collapsedControl"] { display: none !important; } ')


def quiz_page():
    st.markdown('<style>' + HIDE_SIDEBAR +
                '.banner .tag, label, .stMarkdown p { font-family: "Space Mono", monospace !important; '
                'font-weight: 400 !important; font-size: 1rem !important; line-height: 1.45 !important; }'
                '</style>', unsafe_allow_html=True)
    header("Answer about a dozen quick questions, and we will find the county that fits you. "
           "No wrong answers, only wrong turns at the river.", wagon=False, music=False)
    factors = quiz_factors()
    setup = 0 if state.get("retake") else 2
    most = setup + quiz.most_questions(quiz.FACTORS if state.step == "family" else factors,
                                       state.seed, state.answers)

    if state.step == "tradeoffs":
        result = quiz.replay(factors, state.seed, state.answers)
        if result[0] == "done":
            state.step = "reveal"
            state.reveals = state.get("reveals", 0) + 1

    if state.step == "reveal":
        ranked = quiz.replay(factors, state.seed, state.answers)[1]
        title, line = quiz.PERSONALITIES[ranked[0]]
        trail_progress("YOU MADE IT TO TOWN", 1.0)
        cue = f"{state.seed}-{state.get('reveals', 0)}"
        st.markdown(f'<div class="panel persona"><div class="drumroll"><div class="label">READING YOUR TRAIL...</div>'
                    f'<div class="bar"><i></i></div></div>{confetti_html(cue)}'
                    f'<div class="progress-label">YOUR TRAIL PERSONALITY</div>'
                    f'<div class="type">{title}</div><div class="line">{line}</div>'
                    f'<div class="fanfare-cue" data-cue="{cue}" hidden></div></div>', unsafe_allow_html=True)
        weights = quiz.weights_from_order(ranked)
        bars = "".join(
            f'<div class="rankbar" style="animation-delay:{2.1 + 0.15 * i:.2f}s"><span>{i + 1}.</span><span>{name}</span>'
            f'<span class="fill" style="width:{weights[name] / len(ranked) * 100:.0f}%;'
            f'background:{FACTORS[name]["color"]}"></span></div>' for i, name in enumerate(ranked))
        st.markdown(f'<div class="panel">{bars}</div>', unsafe_allow_html=True)
        left, right = st.columns(2)
        left.button("HIT THE TRAIL", key="go_trail", on_click=hit_the_trail, width="stretch")
        right.button("Back", key="back_reveal", on_click=go_back)
        return

    if state.step == "family":
        number = 1
    elif state.step == "comfort":
        number = 2
    else:
        number = setup + len(state.answers) + 1
    trail_progress(f"QUESTION {number} OF UP TO {most}", min((number - 1) / most, 1.0))

    if state.step == "family":
        st.markdown('<div class="question">First things first. Where does your family live?</div>',
                    unsafe_allow_html=True)
        left, right = st.columns(2)
        us_state = left.selectbox("State", sorted(counties["USPS"].unique()), index=None,
                                  placeholder="Pick a state", key=f"fam_state_{state.seed}")
        options = []
        if us_state:
            options = counties[counties["USPS"] == us_state].sort_values("NAME")["NAME"].tolist()
        county = right.selectbox("County", options, index=None, placeholder="Pick a county",
                                 key=f"fam_county_{state.seed}", disabled=not us_state)
        geoid = None
        if us_state and county:
            geoid = counties[(counties["USPS"] == us_state) & (counties["NAME"] == county)]["GEOID"].iloc[0]
        left.button("This is where my family lives", key="go_family", on_click=choose_family, args=(geoid,),
                    disabled=geoid is None, width="stretch")
        right.button("Family isn't a factor for me", key="go_nofamily", on_click=choose_family, args=(None,),
                     width="stretch")
        return

    if state.step == "comfort":
        st.markdown('<div class="question">What does a comfy day feel like to you?</div>', unsafe_allow_html=True)
        rows = [st.columns(2), st.columns(2)]
        for i, (name, temps, low_high) in enumerate(quiz.COMFORT_CHOICES):
            rows[i // 2][i % 2].button(f"{name}  \n{temps}", key=f"pick_comfort_{i}", on_click=choose_comfort,
                                       args=(low_high,), width="stretch")
        st.button("Back", key="back_comfort", on_click=go_back)
        return

    _, a, b = quiz.replay(factors, state.seed, state.answers)
    stem, cards = quiz.QUESTIONS[frozenset([a, b])]
    left_factor, right_factor = quiz.card_order(state.seed, (a, b))
    st.markdown(f'<div class="question">{stem}</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    n = len(state.answers)
    left.button(cards[left_factor], key=f"pick_{n}_left", on_click=answer, args=(left_factor,), width="stretch")
    right.button(cards[right_factor], key=f"pick_{n}_right", on_click=answer, args=(right_factor,), width="stretch")
    if n > 0 or not state.get("retake"):
        st.button("Back", key=f"back_{n}", on_click=go_back)


# ------------------------------------------------------------------ page 2, the results
def results_page():
    factors = quiz_factors()
    quiz_order = quiz.replay(factors, state.seed, state.answers)[1]
    persona, _ = quiz.PERSONALITIES[quiz_order[0]]
    family_geoid = state.family

    order = quiz_order
    weights = quiz.weights_from_order(order)
    comfort = state.comfort
    states, place, top_n = [], "No preference", 10
    st.markdown("<style>" + HIDE_SIDEBAR + "</style>", unsafe_allow_html=True)

    table = counties.copy()
    table["comfortable_months"] = comfortable_months(table, comfort[0], comfort[1])
    table["rent_share"] = 100 * 12 * table["rent_2026_09"] / table["Median_Household_Income_2022"]
    if family_geoid:
        home_row = table[table["GEOID"] == family_geoid].iloc[0]
        table["miles_from_family"] = miles_between(home_row["lat"], home_row["lon"], table["lat"], table["lon"])
    ranked, in_scope = rank_counties(table, weights, order, states, place)
    ranked["us_rank"] = ranked["rank"]

    header("Rank what matters, and see which county your wagon reaches. Try not to die of rent burden.")
    chips = "".join(f'<span class="chip">{i + 1}. {name}</span>' for i, name in enumerate(order))
    strip_left, strip_right = st.columns([4, 1], vertical_alignment="center")
    strip_left.markdown(f'<div class="strip"><span class="progress-label">YOUR TRAIL PERSONALITY</span>'
                        f'<span class="persona-name">{persona}</span><span class="chips">{chips}</span></div>',
                        unsafe_allow_html=True)
    strip_right.button("RETAKE THE QUIZ", key="go_retake", on_click=retake_quiz, width="stretch")
    ranking_tab, compare_tab, method_tab = st.tabs(["Ranking", "Compare two counties", "How this works"])

    with ranking_tab:
        codes, place_name, top_n = filter_bar(sorted(counties["USPS"].unique()))
        view = ranked[ranked["USPS"].isin(codes)].copy()
        view["rank"] = range(1, len(view) + 1)
        ranking_section(view, in_scope[in_scope["USPS"].isin(codes)], order, weights, comfort, top_n, family_geoid,
                        place_name, len(codes) < len(counties["USPS"].unique()), table)
    with compare_tab:
        compare_section(table, ranked, order, weights, comfort, family_geoid)
    with method_tab:
        method_section(order, family_geoid)


def clear_state_filter():
    st.session_state.f_state = None


def filter_bar(all_codes):
    """Region, state and show-count controls. They narrow the list; every county keeps its national fit score."""
    for key, default in (("f_region", "All"), ("f_state", None), ("f_show", 10)):
        if key not in st.session_state:
            st.session_state[key] = default
    if st.session_state.f_region not in ["All", *REGIONS]:
        st.session_state.f_region = "All"
    with st.container(border=True):
        col_region, col_state, col_show = st.columns([5, 3, 3], vertical_alignment="bottom")
        region = col_region.segmented_control("REGION", ["All", *REGIONS], key="f_region", on_change=clear_state_filter,
                                              selection_mode="single") or "All"
        options = [c for c in all_codes if region == "All" or c in REGIONS[region]]
        if st.session_state.f_state not in options:
            st.session_state.f_state = None
        us_state = col_state.selectbox("STATE", options, key="f_state", index=None,
                                       placeholder="All states" if region == "All" else f"All of the {region}")
        top_n = col_show.segmented_control("SHOW", SHOW_COUNTS, key="f_show", selection_mode="single") or 10
    if us_state:
        return [us_state], STATE_NAMES.get(us_state, us_state), top_n
    if region == "All":
        return list(all_codes), "the US", top_n
    return REGIONS[region], f"the {region}", top_n


def contribution_chart(rows, order, weights, title, height):
    total_weight = sum(weights[n] for n in order)
    fig = go.Figure()
    for name in order:
        fig.add_trace(go.Bar(
            y=rows["label"], x=weights[name] * rows["score_" + name] / total_weight, orientation="h", name=name,
            marker_color=FACTORS[name]["color"],
            hovertemplate="%{y}<br>" + name + " adds %{x:.1f} points<extra></extra>"))
    fig.update_layout(barmode="stack", xaxis=dict(range=[0, 100], title="Fit score, split into what each factor adds"),
                      yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.25))
    return plotly_look(fig, height).update_layout(title=title)


def ranking_section(ranked, in_scope, order, weights, comfort, top_n, family_geoid, place_name, filtered, table_all):
    if ranked.empty:
        st.markdown('<div class="hazard"><b>YOUR PARTY HAS RUN OUT OF COUNTIES.</b><br>'
                    f'No county in {place_name} has a number for every one of your factors.</div>',
                    unsafe_allow_html=True)
        return
    show_n = min(top_n, len(ranked))
    chart_n = min(show_n, CHART_MAX)
    best = ranked.iloc[0]
    line1, line2 = "YOUR WAGON HAS REACHED", best["label"].upper()
    st.markdown(f'<div class="panel"><div class="arrived" style="--n:{len(line1)};--d:0.2s">{line1}</div>'
                f'<div class="arrived last" style="--n:{len(line2)};--d:1.3s">{line2}</div>'
                f'<div class="supplies" style="margin-top:8px;">Fit score {best["fit_score"]:.1f} out of 100, '
                f'the best of {len(ranked):,} counties on your trail in {place_name}.</div></div>', unsafe_allow_html=True)

    cards = []
    for i, (_, row) in enumerate(ranked.head(3).iterrows()):
        strongest = max(order, key=lambda n: row["score_" + n])
        extra = (f'<div class="line">{row["miles_from_family"]:,.0f} miles from family</div>' if family_geoid
                 else f'<div class="line">Job growth {row["job_growth"]:.1f}%</div>')
        cards.append(
            f'<div class="card {"first" if i == 0 else ""}" style="animation-delay:{0.3 + 0.25 * i}s">'
            f'<span class="badge">#{i + 1}</span><div class="name">{row["label"]}</div>'
            f'<div class="score">{row["fit_score"]:.1f}</div>'
            f'<div class="line">Rent ${row["rent_2026_09"]:,.0f} a month</div>{extra}'
            f'<div class="line">Strongest on {strongest.lower()}</div></div>')
    st.markdown(f'<div class="podium">{"".join(cards)}</div>', unsafe_allow_html=True)

    st.markdown(f"## What drives your top {chart_n}")
    st.plotly_chart(contribution_chart(ranked.head(chart_n), order, weights, f"Why each county made your top {chart_n}",
                                       max(300, 140 + 33 * chart_n)), width="stretch")
    st.caption(f"Each bar is one of your top {chart_n} counties, split into the points each factor adds to its fit score. "
               "A longer piece means that factor helps the county more. The scores come from your answers and the "
               "county data described under How this works.")

    st.markdown("## The trail map")
    fig = go.Figure(go.Choropleth(
        geojson=load_geojson(stamp("us_counties.json")), locations=ranked["GEOID"], z=ranked["fit_score"], featureidkey="id",
        colorscale=[[0, "#1f2b1c"], [0.5, "#5a8f3a"], [1, GREEN]], zmin=0, zmax=100,
        marker_line_width=0, text=ranked["label"],
        hovertemplate="%{text}<br>Fit score %{z:.1f}<extra></extra>", colorbar=dict(title="Fit score")))
    if filtered:
        outside = table_all[~table_all["USPS"].isin(in_scope["USPS"].unique())]
        fig.add_trace(go.Choropleth(
            geojson=load_geojson(stamp("us_counties.json")), locations=outside["GEOID"], z=[0] * len(outside),
            featureidkey="id", colorscale=[[0, "#141a12"], [1, "#141a12"]], showscale=False, marker_line_width=0,
            hoverinfo="skip"))
    fig.update_geos(scope="usa", bgcolor=PANEL, showlakes=False, landcolor="#2a2f29", showland=True)
    plotly_look(fig, 460).update_layout(title="Fit score by county (gray counties are not ranked)")
    st.plotly_chart(fig, width="stretch", config={"scrollZoom": False})
    st.caption("Each ranked county is shaded by its fit score, and greener means a better fit for you. Gray counties "
               "have no number for at least one factor, mostly because Zillow publishes no rent for them."
               + (" Dark counties lie outside the region or state you picked." if filtered else ""))

    st.markdown(f"## Your top {show_n} counties" + (f" in {place_name}" if filtered else ""))
    show = ranked.head(show_n)
    table = pd.DataFrame({"Rank": show["rank"], "County": show["label"], "Fit score": show["fit_score"]})
    if filtered:
        table.insert(1, "US rank", show["us_rank"])
    config = {"Fit score": st.column_config.ProgressColumn("Fit score", format="%.1f", min_value=0, max_value=100)}
    for name in order:
        header_text = FACTORS[name]["header"]
        table[header_text] = show[FACTORS[name]["column"]]
        config[header_text] = st.column_config.NumberColumn(header_text, format=FACTORS[name]["table_format"])
    st.dataframe(table, hide_index=True, width="stretch", column_config=config)

    st.markdown("## Trail hazards")
    lost = len(in_scope) - len(ranked)
    burden = in_scope[in_scope["rent_share"] > 40].sort_values("rent_share", ascending=False)
    harsh = ranked[ranked["comfortable_months"] <= 2]
    hazards = []
    if len(burden):
        hazards.append(f"<b>YOU HAVE DIED OF RENT BURDEN</b><br>In {len(burden):,} counties on your trail, a year of "
                       f"rent is more than 40 percent of the median household income. The worst are "
                       f"{', '.join(burden['label'].head(3))}.")
    if len(harsh):
        hazards.append(f"<b>YOU HAVE DIED OF THE WEATHER</b><br>{len(harsh):,} ranked counties have two or fewer "
                       f"months in your comfortable range of {comfort[0]} to {comfort[1]} degrees.")
    if family_geoid:
        far = ranked[ranked["miles_from_family"] > 1000]
        if len(far):
            hazards.append(f"<b>YOU HAVE DIED OF HOMESICKNESS</b><br>{len(far):,} ranked counties are more than "
                           f"1,000 miles from your family.")
    hazards.append(f"<b>{lost:,} COUNTIES WERE LOST ON THE TRAIL</b><br>They have no number for at least one factor, "
                   f"usually because Zillow publishes no rent for smaller counties, so they are not ranked.")
    for i, text in enumerate(hazards):
        st.markdown(f'<div class="hazard" style="animation-delay:{0.2 * i}s">{text}</div>', unsafe_allow_html=True)


def compare_section(table, ranked, order, weights, comfort, family_geoid):
    st.markdown("## A fork in the trail")
    labels = table.sort_values(["USPS", "NAME"])["label"].tolist()
    first_default = ranked.iloc[0]["label"] if not ranked.empty else "Benton County, AR"
    second_default = "Washington County, AR"
    if family_geoid:
        second_default = table.loc[table["GEOID"] == family_geoid, "label"].iloc[0]
    if second_default == first_default:
        second_default = ranked.iloc[1]["label"] if len(ranked) > 1 else "Washington County, AR"
    left, right = st.columns(2)
    first = left.selectbox("First county", labels, index=labels.index(first_default), key=f"cmp1_{state.seed}")
    second = right.selectbox("Second county", labels, index=labels.index(second_default), key=f"cmp2_{state.seed}")
    one = table[table["label"] == first].iloc[0]
    two = table[table["label"] == second].iloc[0]


    top_left, top_right = st.columns(2)
    with top_left:
        fig = go.Figure()
        for row, label, color in [(one, first, GREEN), (two, second, AMBER)]:
            values = []
            for name in order:
                column = FACTORS[name]["column"]
                pct = 100 * table[column].rank(pct=True, ascending=FACTORS[name]["higher_is_better"])
                values.append(pct.loc[row.name])
            fig.add_trace(go.Bar(y=order, x=values, orientation="h", name=label, marker_color=color,
                                 hovertemplate="%{y}<br>Better than %{x:.0f}% of counties<extra>" + label + "</extra>"))
        fig.update_layout(barmode="group", xaxis=dict(range=[0, 100], title="Percentile among all counties (100 is best)"),
                          yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(plotly_look(fig, 400).update_layout(title="Who wins on each factor"), width="stretch")
        st.caption("Each pair of bars places the two counties among all US counties with data on one factor. "
                   "A longer bar is better, whatever the direction of the factor.")
    with top_right:
        both = ranked[ranked["label"].isin([first, second])].set_index("label").reindex([first, second]).dropna(
            subset=["fit_score"]).reset_index()
        if len(both) == 0:
            st.info("Neither county is ranked on your trail, so there is no fit score to split.")
        else:
            st.plotly_chart(contribution_chart(both, order, weights, "Fit score, factor by factor", 400),
                            width="stretch")
            st.caption("Each bar is one county's fit score, split into the points each factor adds. A county that "
                       "is missing a number for one of your factors has no bar.")

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        history = load_rent_history(stamp("rent_history.csv"))
        fig = go.Figure()
        series_list = []
        for row, label, color in [(one, first, GREEN), (two, second, AMBER)]:
            if row["GEOID"] in history.index:
                s = history.loc[row["GEOID"]].dropna()
                series_list.append((label, s, color))
                fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=label, line=dict(color=color, width=3),
                                         hovertemplate="%{x|%b %Y}<br>$%{y:,.0f}<extra>" + label + "</extra>"))
        if not series_list:
            st.info("Zillow publishes no rent history for either county.")
        else:
            n_months = max(len(s) for _, s, _ in series_list)
            steps = list(range(2, n_months + 1, 2)) + [n_months]
            fig.frames = [go.Frame(data=[go.Scatter(x=s.index[:k], y=s.values[:k]) for _, s, _ in series_list])
                          for k in steps]
            top = max(s.max() for _, s, _ in series_list)
            fig.update_layout(
                yaxis=dict(range=[0, top * 1.15], title="Typical monthly rent, dollars"),
                legend=dict(orientation="h", x=1, xanchor="right", y=-0.2),
                updatemenus=[dict(type="buttons", x=0, y=-0.22, xanchor="left", yanchor="top", showactive=False,
                                  bgcolor="#24331F", bordercolor=GREEN, font=dict(color=CREAM), buttons=[
                                      dict(label="Play the trail", method="animate",
                                           args=[None, dict(frame=dict(duration=40, redraw=False),
                                                            transition=dict(duration=0), mode="immediate")])])])
            st.plotly_chart(plotly_look(fig, 400).update_layout(title="Rent over time"), width="stretch")
            st.caption("Each line is one county's typical monthly rent from January 2015 to September 2026. "
                       "The source is the Zillow Observed Rent Index, county file.")
    with bottom_right:
        fig = go.Figure()
        for row, label, color in [(one, first, GREEN), (two, second, AMBER)]:
            temps = [row["temp_" + m] for m in MONTHS]
            fig.add_trace(go.Scatter(x=MONTH_LABELS, y=temps, mode="lines+markers", name=label,
                                     line=dict(color=color, width=3),
                                     hovertemplate="%{x}<br>%{y:.0f} degrees<extra>" + label + "</extra>"))
        fig.add_hrect(y0=comfort[0], y1=comfort[1], fillcolor=GREEN, opacity=0.12, line_width=0,
                      annotation_text="your comfortable range", annotation_position="top left")
        fig.update_layout(yaxis=dict(title="Average temperature, degrees F"), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(plotly_look(fig, 400).update_layout(title="A year of weather"), width="stretch")
        st.caption("Each point is a month's average temperature over 2015 to 2024, and the shaded band is your "
                   "comfortable range. The source is NOAA's county temperature file.")


def method_section(order, family_geoid):
    st.markdown("## The trail guide")
    st.write("One row is one US county, 3,222 in all, from the Census Bureau's 2025 county list.")
    rows = [
        ["Rent", "Typical monthly rent, September 2026", "lower", "Zillow Observed Rent Index, county file"],
        ["Job outlook", "Change in employed residents, 2018 to 2023, in percent", "higher",
         "USDA Economic Research Service, county unemployment file"],
        ["Comfortable weather", "Months a year whose average temperature falls in your comfortable range",
         "higher", "NOAA county temperatures, monthly averages for 2015 to 2024"],
        ["Education", "Share of adults aged 25 to 44 with some education after high school", "higher",
         "County Health Rankings, 2025 release"],
        ["Culture", "Arts, entertainment, and recreation businesses per 10,000 residents", "higher",
         "Census County Business Patterns 2023 (industry 71) and Census population estimates 2024"],
        ["Family", "Straight-line miles from the center of your family's county", "lower",
         "Census Bureau 2025 county list (county center points)"],
    ]
    st.table(pd.DataFrame([r for r in rows if r[0] in order],
                          columns=["Factor", "What it measures", "Better when", "Source"]))
    st.markdown("### How the quiz ranks the factors")
    st.write("The quiz places the factors one at a time into a ranked list. Each trade-off question compares the "
             "factor being placed with one already in the list, the way you would slide a card into a sorted hand. "
             "That ranks six factors in 8 to 11 questions, and five factors in 6 to 8. The order of the questions "
             "and the side of each card are random.")
    st.markdown("### How your order becomes weights")
    st.write("The top factor gets the largest weight, 6 with six factors or 5 with five, and each factor below it "
             "gets one less, down to 1 for the last. Retake the quiz to get a new set of questions and a new order.")
    st.markdown("### How the fit score is computed")
    st.write("The site drops every county with no number for one "
             "of your factors. On each factor, each remaining county gets a percentile score from 0 to 100, and the "
             "best county scores 100. The fit score is the weighted average of the percentile scores.")
    st.markdown("### How the region and state filters work")
    st.write("The region and state buttons narrow the list without changing any score. Each county keeps the fit "
             "score it earns against every ranked county in the country, so its score is the same in every view. "
             "Only its rank changes, and the US rank column keeps the national rank. The regions are the Census "
             "Bureau's four regions, and Puerto Rico appears only under All.")
    st.markdown("### Caveats")
    st.markdown(
        "- Zillow publishes a rent for 1,358 of the 3,222 counties, mostly the larger rental markets, so the "
        "ranking covers those counties only.\n"
        "- Job growth counts employed residents where they live, not jobs where they are located.\n"
        "- Culture counts businesses, not their size, and a small county with a few golf courses or campgrounds "
        "can score high per 10,000 residents.\n"
        "- A comfortable month is judged by its average temperature, which hides hot afternoons and cold nights.\n"
        "- Distance to family is a straight line between county centers, not driving miles.\n"
        "- The map draws Connecticut's old counties, so its nine planning regions appear gray.\n"
        "- The files cover different years, from 2018 to September 2026.\n"
        "- The trail theme is a homage to a classic computer game. The pixel wagon is original art.\n"
        "- The music is an original 8-bit waltz arrangement of Sweet Betsy from Pike, an 1850s song about a wagon "
        "crossing the plains, in the public domain. "
        "It starts on your first click or key press, and the speaker button mutes it.")


if state.page == "quiz":
    quiz_page()
else:
    results_page()
