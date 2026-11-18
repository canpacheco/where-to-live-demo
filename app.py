"""Where should a finance graduate live? Demo website for the FDA I capstone.

An Oregon Trail style homage (original pixel art, free Google fonts, no game assets).
Run locally from this folder:  streamlit run app.py
The data and the static charts are built by build_demo_data.py.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from streamlit_sortables import sort_items

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

GREEN = "#8BE04E"
AMBER = "#F2A541"
CREAM = "#E9F5DB"
PANEL = "#18211A"
INK = "#0D110C"
RED = "#E4572E"

FACTORS = {
    "Rent": {"column": "rent_2026_09", "higher_is_better": False, "header": "Rent per month",
             "format": "${:,.0f}", "table_format": "$%,.0f"},
    "Job outlook": {"column": "job_growth", "higher_is_better": True, "header": "Job growth",
                    "format": "{:.1f}%", "table_format": "%.1f%%"},
    "Comfortable weather": {"column": "comfortable_months", "higher_is_better": True,
                            "header": "Comfortable months", "format": "{:.0f}", "table_format": "%.0f"},
    "Education": {"column": "some_college", "higher_is_better": True, "header": "Some college",
                  "format": "{:.1f}%", "table_format": "%.1f%%"},
    "Culture": {"column": "culture", "higher_is_better": True, "header": "Arts per 10,000",
                "format": "{:.1f}", "table_format": "%.1f"},
}
FACTOR_NAMES = list(FACTORS)
PLACE_CHOICES = ["No preference", "A metro area", "A smaller city", "Outside any metro or micro area"]

st.set_page_config(page_title="Where should a finance graduate live?", page_icon="🐂", layout="wide")

# ------------------------------------------------------------------ look and feel
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');
h1, h2, h3, .pixel {{ font-family: 'Press Start 2P', monospace !important; letter-spacing: 0.02em; }}
h1 {{ font-size: clamp(1.1rem, 2.6vw, 1.8rem) !important; line-height: 1.5 !important; color: {GREEN}; }}
h2 {{ font-size: clamp(0.9rem, 1.8vw, 1.15rem) !important; line-height: 1.6 !important; color: {AMBER}; }}
h3 {{ font-size: 0.85rem !important; line-height: 1.6 !important; }}
.stMarkdown p, .stMarkdown li, label, .stCaption, [data-testid="stSidebar"] p {{
  font-family: 'VT323', monospace !important; font-size: 1.3rem !important; line-height: 1.25 !important; }}
[data-testid="stTabs"] [role="tablist"] {{ gap: 16px; flex-wrap: wrap; margin: 18px 0 6px 0; overflow: visible !important; }}
[data-testid="stTab"] {{ flex: 1 1 0; min-width: 150px; height: auto; padding: 16px 10px;
  justify-content: center; align-items: center; min-height: 64px; background: {PANEL}; border: 3px solid {GREEN}; box-shadow: 4px 4px 0 #050705;
  transition: transform 0.1s, box-shadow 0.1s; }}
[data-testid="stTab"]:hover {{ transform: translate(-2px, -2px); box-shadow: 6px 6px 0 #050705; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {GREEN}; }}
[data-testid="stTab"] p {{ font-family: 'Press Start 2P', monospace !important; font-size: 0.72rem !important;
  line-height: 1.6 !important; text-align: center; color: {CREAM}; white-space: normal !important; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: {INK} !important; }}
[data-testid="stTabs"] [role="tablist"] > :not([data-testid="stTab"]) {{ display: none; }}
[data-testid="stTabs"] [role="tablist"], [data-testid="stTabs"] [role="tablist"]::after {{ border: 0 !important; }}
[data-testid="stTabPanel"] {{ padding-top: 22px; }}
.banner {{ border: 4px solid {GREEN}; background: {PANEL}; padding: 18px 22px 10px 22px; margin-bottom: 10px;
  box-shadow: 6px 6px 0 {INK}, 6px 6px 0 2px {GREEN}; }}
.banner .kicker {{ font-family: 'Press Start 2P', monospace; color: {AMBER}; font-size: 0.75rem; }}
.banner .tag {{ font-family: 'VT323', monospace; font-size: 1.45rem; color: {CREAM}; }}
.track {{ position: relative; height: 70px; overflow: hidden; border-bottom: 4px dashed #3c5236; margin: 6px 0 4px 0; }}
.wagon {{ position: absolute; bottom: 2px; left: calc(100% - 200px); animation: roll 3.2s steps(16) 1 both; }}
@keyframes roll {{ from {{ left: -200px; }} to {{ left: calc(100% - 200px); }} }}
.panel {{ border: 3px solid {GREEN}; background: {PANEL}; padding: 14px 18px; margin: 10px 0;
  box-shadow: 4px 4px 0 #050705; }}
.panel {{ container-type: inline-size; }}
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
@media (prefers-reduced-motion: reduce) {{
  .wagon, .arrived, .card, .hazard {{ animation: none !important; opacity: 1 !important; }}
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


# ------------------------------------------------------------------ data
@st.cache_data
def load_counties():
    return pd.read_csv(DATA / "county_factors.csv", dtype={"GEOID": str})


@st.cache_data
def load_geojson():
    with open(DATA / "us_counties.json") as f:
        return json.load(f)


@st.cache_data
def load_chart_data():
    states = pd.read_csv(DATA / "state_rent.csv")
    series = pd.read_csv(DATA / "rent_series.csv", parse_dates=["month"])
    return states, series


def comfortable_months(table, low, high):
    temps = table[["temp_" + m for m in MONTHS]]
    months = ((temps >= low) & (temps <= high)).sum(axis=1).astype(float)
    months[temps.isna().any(axis=1)] = float("nan")
    return months


def rank_counties(table, weights, states, place):
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
    ranked = ranked.dropna(subset=[FACTORS[n]["column"] for n in FACTOR_NAMES]).copy()
    total = 0
    for name in FACTOR_NAMES:
        column = FACTORS[name]["column"]
        ranked["score_" + name] = 100 * ranked[column].rank(pct=True, ascending=FACTORS[name]["higher_is_better"])
        total = total + weights[name] * ranked["score_" + name]
    ranked["fit_score"] = total / sum(weights.values())
    ranked = ranked.sort_values("fit_score", ascending=False)
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked, in_scope


def plotly_look(fig, height):
    fig.update_layout(template="plotly_dark", paper_bgcolor=PANEL, plot_bgcolor=PANEL, height=height,
                      font=dict(family="Courier New, monospace", color=CREAM, size=14),
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


counties = load_counties()

# ------------------------------------------------------------------ sidebar
MUSIC_HTML = (HERE / "music.html").read_text(encoding="utf-8")

with st.sidebar:
    components.html(MUSIC_HTML, height=46)
    st.markdown("## Outfit your wagon")
    st.write("Drag the five factors into order. The top one matters most to you.")
    order = sort_items(
        ["Rent", "Job outlook", "Comfortable weather", "Education", "Culture"],
        direction="vertical", key="factor_order",
        custom_style=f"""
        .sortable-component {{ border: 3px solid {GREEN}; background-color: {PANEL}; padding: 6px; counter-reset: item; }}
        .sortable-container {{ background-color: {PANEL}; counter-reset: item; }}
        .sortable-container-body {{ background-color: {PANEL}; }}
        .sortable-item, .sortable-item:hover {{ background-color: #24331F; color: {CREAM}; border: 2px solid {GREEN};
            font-family: 'Courier New', monospace; font-weight: bold; font-size: 15px; }}
        .sortable-item::before {{ content: counter(item) ". "; counter-increment: item; color: {AMBER}; }}
        """)
    if not order or sorted(order) != sorted(FACTOR_NAMES):
        order = ["Rent", "Job outlook", "Comfortable weather", "Education", "Culture"]
    weights = {name: 5 - order.index(name) for name in FACTOR_NAMES}
    rows_html = []
    for name in order:
        pips = "".join(f'<span class="pip{" on" if k < weights[name] else ""}"></span>' for k in range(5))
        rows_html.append(f'<div class="row"><span>{name}</span><span class="pips" title="weight {weights[name]}">'
                         f'{pips}</span></div>')
    st.markdown('<div class="supplies"><div style="color:#F2A541">Weight of each factor</div>'
                + "".join(rows_html) + "</div>", unsafe_allow_html=True)

    st.markdown("## Must-haves")
    comfort = st.slider("A comfortable month averages between (degrees F)", 20, 90, (50, 75))
    states = st.multiselect("States you would consider (leave empty for all)", sorted(counties["USPS"].unique()))
    place = st.selectbox("Kind of place", PLACE_CHOICES)
    top_n = st.slider("Counties to show", 5, 50, 10)

counties["comfortable_months"] = comfortable_months(counties, comfort[0], comfort[1])
counties["rent_share"] = 100 * 12 * counties["rent_2026_09"] / counties["Median_Household_Income_2022"]
ranked, in_scope = rank_counties(counties, weights, states, place)

# ------------------------------------------------------------------ banner
st.markdown(f"""
<div class="banner">
  <div class="kicker">THE GRADUATE TRAIL</div>
  <h1 style="margin:8px 0 2px 0;">Where should a finance graduate live?</h1>
  <div class="tag">Rank what matters, and see which county your wagon reaches. Try not to die of rent burden.</div>
  <div class="track"><div class="wagon">{WAGON_SVG}</div></div>
</div>
""", unsafe_allow_html=True)

ranking_tab, compare_tab, charts_tab, method_tab = st.tabs(
    ["Ranking", "Compare two counties", "Charts", "How this works"])

# ------------------------------------------------------------------ ranking
with ranking_tab:
    if ranked.empty:
        st.markdown('<div class="hazard"><b>YOUR PARTY HAS RUN OUT OF COUNTIES.</b><br>'
                    'No county matches your must-haves. Try more states or another kind of place.</div>',
                    unsafe_allow_html=True)
    else:
        best = ranked.iloc[0]
        line1 = "YOUR WAGON HAS REACHED"
        line2 = best["label"].upper()
        st.markdown(f'<div class="panel"><div class="arrived" style="--n:{len(line1)};--d:0.2s">{line1}</div>'
                    f'<div class="arrived last" style="--n:{len(line2)};--d:1.3s">{line2}</div>'
                    f'<div class="supplies" style="margin-top:8px;">Fit score {best["fit_score"]:.1f} out of 100, '
                    f'the best of {len(ranked):,} counties on your trail.</div></div>', unsafe_allow_html=True)

        cards = []
        for i, (_, row) in enumerate(ranked.head(3).iterrows()):
            strongest = max(FACTOR_NAMES, key=lambda n: row["score_" + n])
            cards.append(
                f'<div class="card {"first" if i == 0 else ""}" style="animation-delay:{0.3 + 0.25 * i}s">'
                f'<span class="badge">#{i + 1}</span><div class="name">{row["label"]}</div>'
                f'<div class="score">{row["fit_score"]:.1f}</div>'
                f'<div class="line">Rent ${row["rent_2026_09"]:,.0f} a month</div>'
                f'<div class="line">Job growth {row["job_growth"]:.1f}%</div>'
                f'<div class="line">Strongest on {strongest.lower()}</div></div>')
        st.markdown(f'<div class="podium">{"".join(cards)}</div>', unsafe_allow_html=True)

        st.markdown("## Your top counties")
        show = ranked.head(top_n)
        table = pd.DataFrame({"Rank": show["rank"], "County": show["label"], "Fit score": show["fit_score"]})
        config = {"Fit score": st.column_config.ProgressColumn("Fit score", format="%.1f", min_value=0, max_value=100)}
        for name in FACTOR_NAMES:
            header = FACTORS[name]["header"]
            table[header] = show[FACTORS[name]["column"]]
            config[header] = st.column_config.NumberColumn(header, format=FACTORS[name]["table_format"])
        st.dataframe(table, hide_index=True, width="stretch", column_config=config)

        st.markdown("## The trail map")
        fig = go.Figure(go.Choropleth(
            geojson=load_geojson(), locations=ranked["GEOID"], z=ranked["fit_score"], featureidkey="id",
            colorscale=[[0, "#1f2b1c"], [0.5, "#5a8f3a"], [1, GREEN]], zmin=0, zmax=100,
            marker_line_width=0, text=ranked["label"],
            hovertemplate="%{text}<br>Fit score %{z:.1f}<extra></extra>",
            colorbar=dict(title="Fit score")))
        fig.update_geos(scope="usa", bgcolor=PANEL, showlakes=False, landcolor="#2a2f29", showland=True)
        plotly_look(fig, 460).update_layout(title="Fit score by county (gray counties are not ranked)")
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": False})

        st.markdown("## Trail hazards")
        lost = len(in_scope) - len(ranked)
        burden = in_scope[in_scope["rent_share"] > 40].sort_values("rent_share", ascending=False)
        harsh = ranked[ranked["comfortable_months"] <= 2]
        hazards = []
        if len(burden):
            names = ", ".join(burden["label"].head(3))
            hazards.append(f"<b>YOU HAVE DIED OF RENT BURDEN</b><br>In {len(burden):,} counties on your trail, "
                           f"a year of rent is more than 40 percent of the median household income. "
                           f"The worst are {names}.")
        if len(harsh):
            hazards.append(f"<b>YOU HAVE DIED OF THE WEATHER</b><br>{len(harsh):,} ranked counties have two or "
                           f"fewer months in your comfortable range of {comfort[0]} to {comfort[1]} degrees.")
        hazards.append(f"<b>{lost:,} COUNTIES WERE LOST ON THE TRAIL</b><br>They have no number for at least one "
                       f"factor, usually because Zillow publishes no rent for smaller counties, so they are not ranked.")
        for i, text in enumerate(hazards):
            st.markdown(f'<div class="hazard" style="animation-delay:{0.2 * i}s">{text}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ compare
with compare_tab:
    st.markdown("## A fork in the trail")
    labels = counties.sort_values(["USPS", "NAME"])["label"].tolist()
    left, right = st.columns(2)
    first = left.selectbox("First county", labels, index=labels.index("Benton County, AR"))
    second = right.selectbox("Second county", labels, index=labels.index("Washington County, AR"))

    national = {}
    for name in FACTOR_NAMES:
        column = FACTORS[name]["column"]
        national[name] = 100 * counties[column].rank(pct=True, ascending=FACTORS[name]["higher_is_better"])
    fig = go.Figure()
    for label, color in [(first, GREEN), (second, AMBER)]:
        idx = counties.index[counties["label"] == label][0]
        values = [national[n].loc[idx] for n in FACTOR_NAMES]
        fig.add_trace(go.Bar(y=FACTOR_NAMES, x=values, orientation="h", name=label, marker_color=color,
                             hovertemplate="%{y}<br>Better than %{x:.0f}% of counties<extra>" + label + "</extra>"))
    fig.update_layout(barmode="group",
                      xaxis=dict(range=[0, 100], title="Percentile among all counties with data (100 is best)"),
                      yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.25))
    plotly_look(fig, 420).update_layout(title="Who wins on each factor")
    st.plotly_chart(fig, width="stretch")

    rows = []
    for name in FACTOR_NAMES:
        column, fmt = FACTORS[name]["column"], FACTORS[name]["format"]
        row = {"Factor": FACTORS[name]["header"]}
        for label in [first, second]:
            value = counties.loc[counties["label"] == label, column].iloc[0]
            row[label] = "no data" if pd.isna(value) else fmt.format(value)
        row["National median"] = fmt.format(counties[column].median())
        rows.append(row)
    rank_row = {"Factor": "Your rank and fit score", "National median": ""}
    for label in [first, second]:
        if label in set(ranked["label"]):
            hit = ranked[ranked["label"] == label].iloc[0]
            rank_row[label] = f"{int(hit['rank'])} of {len(ranked):,}, score {hit['fit_score']:.1f}"
        else:
            county = counties[counties["label"] == label].iloc[0]
            blank = [n for n in FACTOR_NAMES if pd.isna(county[FACTORS[n]["column"]])]
            rank_row[label] = ("lost on the trail, no data for " + ", ".join(blank).lower()) if blank \
                else "outside your must-haves"
    st.dataframe(pd.DataFrame(rows + [rank_row]), hide_index=True, width="stretch")

# ------------------------------------------------------------------ charts
with charts_tab:
    states_rent, series = load_chart_data()

    st.markdown("## Rent by state")
    top10 = states_rent.head(10).iloc[::-1]
    fig = go.Figure(go.Bar(x=top10["median_rent"], y=top10["USPS"], orientation="h", marker_color=GREEN,
                           text=[f"${v:,.0f} ({n} {'county' if n == 1 else 'counties'})"
                                 for v, n in zip(top10["median_rent"], top10["counties_with_rent"])],
                           textposition="outside", hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"))
    fig.update_xaxes(range=[0, 3900], title="Median of the county rents, dollars per month")
    plotly_look(fig, 440).update_layout(title="The ten states with the highest median rent, September 2026")
    st.plotly_chart(fig, width="stretch")
    st.write("Median rent is highest in Hawaii and lowest in Florida among the ten states shown. Each bar is the "
             "median over the counties with a Zillow rent in that state, and the count is printed beside the bar. "
             "The other states with a rent are not drawn. The source is the Zillow Observed Rent Index, county "
             "file, September 2026.")

    st.markdown("## Rent over time")
    names = [c for c in series.columns if c != "month"]
    colors = [GREEN, AMBER]
    fig = go.Figure([go.Scatter(x=series["month"], y=series[n], mode="lines", name=n,
                                line=dict(color=c, width=3)) for n, c in zip(names, colors)])
    steps = list(range(2, len(series) + 1, 2))
    if steps[-1] != len(series):
        steps.append(len(series))
    fig.frames = [go.Frame(data=[go.Scatter(x=series["month"][:k], y=series[n][:k]) for n in names])
                  for k in steps]
    fig.update_layout(
        yaxis=dict(range=[0, 1800], title="Typical monthly rent, dollars"),
        xaxis=dict(range=[series["month"].min(), series["month"].max()]),
        legend=dict(orientation="h", x=1, xanchor="right", y=-0.18),
        updatemenus=[dict(type="buttons", x=0, y=-0.2, xanchor="left", yanchor="top", showactive=False,
                          bgcolor="#24331F", bordercolor=GREEN, font=dict(color=CREAM), buttons=[
            dict(label="Play the trail", method="animate",
                 args=[None, dict(frame=dict(duration=45, redraw=False), transition=dict(duration=0),
                                  fromcurrent=False, mode="immediate")])])])
    plotly_look(fig, 440).update_layout(title="Typical monthly rent, January 2015 to September 2026")
    st.plotly_chart(fig, width="stretch")
    st.write("Rent in Benton County rose from \\$866 in January 2015 to \\$1,607 in September 2026, an increase of 86 "
             "percent, and Washington County moved with it. Each line is one county's typical rent in each month. "
             "The source is the Zillow Observed Rent Index, county file, January 2015 to September 2026.")

    st.markdown("## Rent and income")
    both = counties.dropna(subset=["rent_2026_09", "Median_Household_Income_2022"])
    shown = both[both["rent_2026_09"] <= 4000]
    fig = go.Figure(go.Scattergl(x=shown["Median_Household_Income_2022"] / 1000, y=shown["rent_2026_09"],
                                 mode="markers", marker=dict(size=6, color=GREEN, opacity=0.45),
                                 text=shown["label"],
                                 hovertemplate="%{text}<br>Income $%{x:.0f}k<br>Rent $%{y:,.0f}<extra></extra>"))
    fig.update_xaxes(range=[0, 180], title="Median household income, 2022, thousands of dollars")
    fig.update_yaxes(range=[0, 4000], title="Typical monthly rent, September 2026, dollars")
    plotly_look(fig, 460).update_layout(title="Rent and income by county")
    st.plotly_chart(fig, width="stretch")
    st.write("Counties with higher incomes tend to have higher rents. Each dot is one of the 1,353 counties with "
             "both a rent and an income, and five counties with a rent above \\$4,000 are left off, which are San "
             "Francisco, Pitkin, Kauai, New York, and Teton in Wyoming. The sources are the Zillow Observed Rent "
             "Index for September 2026 and the USDA Economic Research Service median household income for 2022.")

# ------------------------------------------------------------------ method
with method_tab:
    st.markdown("## The trail guide")
    st.write("One row is one US county, 3,222 in all, from the Census Bureau's 2025 county list.")
    st.table(pd.DataFrame([
        ["Rent", "Typical monthly rent, September 2026", "lower", "Zillow Observed Rent Index, county file"],
        ["Job outlook", "Change in employed residents, 2018 to 2023, in percent", "higher",
         "USDA Economic Research Service, county unemployment file"],
        ["Comfortable weather", "Months a year whose average temperature falls in your comfortable range",
         "higher", "NOAA county temperatures, monthly averages for 2015 to 2024"],
        ["Education", "Share of adults aged 25 to 44 with some education after high school", "higher",
         "County Health Rankings, 2025 release"],
        ["Culture", "Arts, entertainment, and recreation businesses per 10,000 residents", "higher",
         "Census County Business Patterns 2023 (industry 71) and Census population estimates 2024"],
    ], columns=["Factor", "What it measures", "Better when", "Source"]))
    st.markdown("### How your order becomes weights")
    st.write("The factor you drag to the top gets a weight of 5, the second 4, the third 3, the fourth 2, and the "
             "last 1. The last factor still counts, but five times less than the first.")
    st.markdown("### How the fit score is computed")
    st.write("The site keeps the counties that meet your must-haves, then drops every county with no number for one "
             "of the five factors. On each factor, each remaining county gets a percentile score from 0 to 100, and "
             "the best county scores 100. The fit score is the weighted average of the five percentile scores.")
    st.markdown("### The hazards")
    st.write("Rent burden means a year of the county's typical rent is more than 40 percent of its median household "
             "income. The weather hazard counts ranked counties with two or fewer comfortable months.")
    st.markdown("### Caveats")
    st.markdown(
        "- Zillow publishes a rent for 1,358 of the 3,222 counties, mostly the larger rental markets, so the "
        "ranking covers those counties only.\n"
        "- Job growth counts employed residents where they live, not jobs where they are located.\n"
        "- Culture counts businesses, not their size, and a small county with a few golf courses or campgrounds "
        "can score high per 10,000 residents.\n"
        "- A comfortable month is judged by its average temperature, which hides hot afternoons and cold nights.\n"
        "- The map draws Connecticut's old counties, so its nine planning regions appear gray.\n"
        "- The files cover different years, from 2018 to September 2026.\n"
        "- The trail theme is a homage to a classic computer game. The pixel wagon is original art.\n"
        "- The music is an original 8-bit arrangement of Korobeiniki, a Russian folk song in the public "
        "domain. It starts on your first click or key press, and the speaker button mutes it.")
