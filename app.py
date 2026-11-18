"""Where should a finance graduate live? Demo website for the FDA I capstone.

Run locally from this folder:  uv run streamlit run app.py
The data and charts are built by build_demo_data.py.
"""
from itertools import combinations
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

# Each factor: the column it uses, whether a higher value is better, and how to show it.
FACTORS = {
    "Rent": {"column": "rent_2026_09", "higher_is_better": False,
             "header": "Rent per month", "format": "${:,.0f}", "table_format": "$%,.0f"},
    "Job outlook": {"column": "job_growth", "higher_is_better": True,
                    "header": "Job growth", "format": "{:.1f}%", "table_format": "%.1f%%"},
    "Education": {"column": "some_college", "higher_is_better": True,
                  "header": "Some college", "format": "{:.1f}%", "table_format": "%.1f%%"},
    "Culture": {"column": "culture", "higher_is_better": True,
                "header": "Arts per 10,000", "format": "{:.1f}", "table_format": "%.1f"},
    "Comfortable weather": {"column": "comfortable_months", "higher_is_better": True,
                            "header": "Comfortable months", "format": "{:.0f}", "table_format": "%.0f"},
}
FACTOR_NAMES = list(FACTORS)
PAIRS = list(combinations(FACTOR_NAMES, 2))
EXAMPLE_ORDER = ["Rent", "Job outlook", "Comfortable weather", "Education", "Culture"]
PLACE_CHOICES = ["No preference", "A metro area", "A smaller city", "Outside any metro or micro area"]

st.set_page_config(page_title="Where should a finance graduate live?", layout="wide")


@st.cache_data
def load_counties():
    table = pd.read_csv(HERE / "data" / "county_factors.csv", dtype={"GEOID": str})
    return table


def comfortable_months(table, low, high):
    temps = table[["temp_" + m for m in MONTHS]]
    in_range = (temps >= low) & (temps <= high)
    months = in_range.sum(axis=1).astype(float)
    months[temps.isna().any(axis=1)] = float("nan")
    return months


def pair_key(pair):
    return "pair_" + pair[0] + "_" + pair[1]


def fill_example_answers():
    for pair in PAIRS:
        if EXAMPLE_ORDER.index(pair[0]) < EXAMPLE_ORDER.index(pair[1]):
            st.session_state[pair_key(pair)] = pair[0]
        else:
            st.session_state[pair_key(pair)] = pair[1]


def wins_and_weights(answers):
    wins = {name: 0 for name in FACTOR_NAMES}
    for winner in answers.values():
        wins[winner] += 1
    weights = {name: wins[name] + 1 for name in FACTOR_NAMES}
    return wins, weights


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
    in_scope = len(ranked)
    columns = [FACTORS[name]["column"] for name in FACTOR_NAMES]
    ranked = ranked.dropna(subset=columns).copy()
    total = 0
    for name in FACTOR_NAMES:
        column = FACTORS[name]["column"]
        ascending = FACTORS[name]["higher_is_better"]
        ranked["score_" + column] = 100 * ranked[column].rank(pct=True, ascending=ascending)
        total = total + weights[name] * ranked["score_" + column]
    ranked["fit_score"] = total / sum(weights.values())
    ranked = ranked.sort_values("fit_score", ascending=False)
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked, in_scope


counties = load_counties()

# ------------------------------------------------------------------ sidebar form
st.sidebar.header("What matters to you?")
st.sidebar.write("For each of the ten pairs below, pick the factor that matters more to you.")
st.sidebar.button("Fill in example answers", on_click=fill_example_answers,
                  help="Rent first, then job outlook, comfortable weather, education, and culture.")

with st.sidebar.form("questions"):
    for number, pair in enumerate(PAIRS, start=1):
        st.radio(f"{number}. {pair[0]} or {pair[1]}?", list(pair), index=None, horizontal=True,
                 key=pair_key(pair))
    comfort = st.slider("Comfortable range for a month's average temperature (degrees F)",
                        min_value=20, max_value=90, value=(50, 75))
    states = st.multiselect("Which states would you consider? (leave empty for every state)",
                            sorted(counties["USPS"].unique()))
    place = st.selectbox("What kind of place do you want?", PLACE_CHOICES)
    top_n = st.number_input("How many counties should we show?", min_value=5, max_value=50, value=10)
    st.form_submit_button("Show my ranking", type="primary")

counties["comfortable_months"] = comfortable_months(counties, comfort[0], comfort[1])
answers = {pair: st.session_state.get(pair_key(pair)) for pair in PAIRS}
unanswered = [pair for pair, choice in answers.items() if choice is None]

# ------------------------------------------------------------------ page
st.title("Where should a finance graduate live?")
st.write("This site ranks US counties by the five factors that matter most to you: rent, job outlook, "
         "education, culture, and comfortable weather. Answer the ten questions in the sidebar, then "
         "press Show my ranking.")

ranking_tab, compare_tab, charts_tab, method_tab = st.tabs(
    ["Ranking", "Compare two counties", "Charts", "How this works"])

ranked = None
weights = None
if not unanswered:
    wins, weights = wins_and_weights(answers)
    ranked, in_scope = rank_counties(counties, weights, states, place)

with ranking_tab:
    if unanswered:
        st.info(f"Answer all ten questions in the sidebar to see your ranking. "
                f"{len(unanswered)} of the ten are still open.")
        if len(unanswered) < len(PAIRS):
            st.write("The open pairs are " + ", ".join(a + " or " + b for a, b in unanswered) + ".")
    elif ranked.empty:
        st.warning("No county matches your answers. Try more states or another kind of place.")
    else:
        best = ranked.iloc[0]
        st.metric("Your best match", best["label"])
        st.caption(f"Fit score {best['fit_score']:.1f} out of 100")

        show = ranked.head(int(top_n))
        table = pd.DataFrame({"Rank": show["rank"], "County": show["label"],
                              "Fit score": show["fit_score"].round(1)})
        for name in FACTOR_NAMES:
            table[FACTORS[name]["header"]] = show[FACTORS[name]["column"]].round(1)
        st.subheader(f"Your top {len(show)} counties")
        formats = {"Fit score": st.column_config.NumberColumn(format="%.1f")}
        for name in FACTOR_NAMES:
            formats[FACTORS[name]["header"]] = st.column_config.NumberColumn(format=FACTORS[name]["table_format"])
        st.dataframe(table, hide_index=True, width="stretch", column_config=formats)
        st.write(f"{len(ranked):,} counties were ranked. {in_scope - len(ranked):,} were left out because "
                 f"at least one of the five factors is blank for them, mostly because Zillow publishes no "
                 f"rent for smaller counties.")

        st.subheader("How your answers became weights")
        group = pd.DataFrame({"Factor": FACTOR_NAMES,
                              "Wins": [wins[n] for n in FACTOR_NAMES],
                              "Weight": [weights[n] for n in FACTOR_NAMES]})
        group = group.sort_values("Wins", ascending=False)
        st.dataframe(group, hide_index=True)
        st.write("Each pick is a win, as in a World Cup group. A factor's weight is its number of wins "
                 "plus 1, so the last factor still counts a little.")
        if group["Wins"].duplicated().any():
            sentences = []
            for weight, factors in group.groupby("Weight", sort=False)["Factor"]:
                if len(factors) > 1:
                    names = " and ".join([", ".join(factors.tolist()[:-1]), factors.tolist()[-1]])
                    sentences.append(f"{names} share a weight of {weight}.")
            st.write("Some factors have the same number of wins, which happens when your answers form a "
                     "circle. " + " ".join(sentences) + " Change one answer if you want to separate them.")

with compare_tab:
    labels = counties.sort_values(["USPS", "NAME"])["label"].tolist()
    left, right = st.columns(2)
    first = left.selectbox("First county", labels, index=labels.index("Benton County, AR"))
    second = right.selectbox("Second county", labels, index=labels.index("Washington County, AR"))
    rows = []
    for name in FACTOR_NAMES:
        column = FACTORS[name]["column"]
        fmt = FACTORS[name]["format"]
        row = {"Factor": FACTORS[name]["header"]}
        for label in [first, second]:
            value = counties.loc[counties["label"] == label, column].iloc[0]
            row[label] = "no data" if pd.isna(value) else fmt.format(value)
        row["National median"] = fmt.format(counties[column].median())
        rows.append(row)
    population = {"Factor": "Population, 2024"}
    area = {"Factor": "Metro or micro area"}
    rank_row = {"Factor": "Your rank and fit score"}
    for label in [first, second]:
        county = counties[counties["label"] == label].iloc[0]
        population[label] = "no data" if pd.isna(county["POPESTIMATE2024"]) else f"{county['POPESTIMATE2024']:,.0f}"
        area[label] = county["area_name"] if pd.notna(county["area_name"]) else "outside any area"
        if ranked is None:
            rank_row[label] = "answer the questions first"
        elif label in set(ranked["label"]):
            hit = ranked[ranked["label"] == label].iloc[0]
            rank_row[label] = f"{int(hit['rank'])} of {len(ranked):,}, score {hit['fit_score']:.1f}"
        else:
            blank = [n for n in FACTOR_NAMES if pd.isna(county[FACTORS[n]["column"]])]
            rank_row[label] = ("not ranked, no data for " + ", ".join(blank)) if blank else "not in your states or places"
    for extra in [population, area, rank_row]:
        extra["National median"] = ""
    st.dataframe(pd.DataFrame([population, area] + rows + [rank_row]), hide_index=True, width="stretch")
    st.caption(f"Comfortable months use your range of {comfort[0]} to {comfort[1]} degrees from the sidebar.")

with charts_tab:
    st.image(str(HERE / "charts" / "top10_rent.png"))
    st.write("Median rent is highest in Hawaii and lowest in Florida among the ten states shown. Each bar is "
             "the median over the counties with a Zillow rent in that state, and the count is printed beside "
             "the bar. The other states with a rent are not drawn. The source is the Zillow Observed Rent Index, "
             "county file, September 2026.")
    st.image(str(HERE / "charts" / "rent_over_time.png"))
    st.write("Rent in Benton County rose from $866 in January 2015 to $1,607 in September 2026, an increase of "
             "86 percent, and Washington County moved with it. Each line is one county's typical rent in each "
             "month. The source is the Zillow Observed Rent Index, county file, January 2015 to September 2026.")
    st.image(str(HERE / "charts" / "rent_income.png"))
    st.write("Counties with higher incomes tend to have higher rents. Each dot is one of the 1,353 counties "
             "with both a rent and an income, and five counties with a rent above $4,000 are left off: San "
             "Francisco, Pitkin, Kauai, New York, and Teton in Wyoming. The sources are the Zillow Observed Rent "
             "Index for September 2026 and the USDA Economic Research Service median household income for 2022.")

with method_tab:
    st.subheader("What one row is")
    st.write("One row is one US county, 3,222 in all, from the Census Bureau's 2025 county list.")
    st.subheader("The five factors")
    st.table(pd.DataFrame([
        ["Rent", "Typical monthly rent, September 2026", "lower", "Zillow Observed Rent Index, county file"],
        ["Job outlook", "Change in employed residents, 2018 to 2023, in percent", "higher",
         "USDA Economic Research Service, county unemployment file"],
        ["Education", "Share of adults aged 25 to 44 with some education after high school", "higher",
         "County Health Rankings, 2025 release"],
        ["Culture", "Arts, entertainment, and recreation businesses per 10,000 residents", "higher",
         "Census County Business Patterns 2023 (industry 71) and Census population estimates 2024"],
        ["Comfortable weather", "Months a year whose average temperature falls in your comfortable range",
         "higher", "NOAA county temperatures, monthly averages for 2015 to 2024"],
    ], columns=["Factor", "What it measures", "Better when", "Source"]))
    st.subheader("How your answers become weights")
    st.write("The ten questions compare every factor with every other factor once. Each pick is a win. A "
             "factor's weight is its number of wins plus 1, so consistent answers give weights of 5, 4, 3, 2, "
             "and 1. Answers that form a circle give the factors in the circle the same weight.")
    st.subheader("How the fit score is computed")
    st.write("The site keeps the counties in your states and kind of place, then drops every county that has "
             "no value for one of the five factors. On each factor, each remaining county gets a percentile "
             "score from 0 to 100, and the best county scores 100. The fit score is the weighted average of "
             "the five percentile scores.")
    st.subheader("Caveats")
    st.markdown(
        "- Zillow publishes a rent for 1,358 of the 3,222 counties, mostly the larger rental markets, so the "
        "ranking covers those counties only.\n"
        "- Job growth counts employed residents where they live, not jobs where they are located.\n"
        "- Culture counts businesses, not their size, and a small county with a few golf courses or campgrounds "
        "can score high per 10,000 residents.\n"
        "- A comfortable month is judged by its average temperature, which hides hot afternoons and cold nights.\n"
        "- The files cover different years, from 2018 to September 2026.")
