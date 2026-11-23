"""Builds the data and the three charts for the capstone demo website.

The county table is rebuilt the way the Week 10 and Week 12 labs build it (2025 gazetteer spine,
Census 2024 population, USDA ERS employment and income, Zillow rent from the 26 Oct 2026
snapshot, Census 2023 CBSA list), from a local clone of canpacheco/fda-data at ~/fda-data. Three
public files are downloaded into data_raw/ on the first run: NOAA nClimDiv county temperatures,
County Health Rankings 2025, and Census County Business Patterns 2023.

Run from the FDA_Python repo root:
    uv run python "<course folder>/FDA_I/capstone/demo_site/build_demo_data.py"
Writes data/county_factors.csv and charts/*.png next to this script, then prints check numbers.
"""
import io
import json
import os
import re
import urllib.request
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "data_raw"
DATA_DIR = HERE / "data"
CHART_DIR = HERE / "charts"
for folder in [RAW_DIR, DATA_DIR, CHART_DIR]:
    folder.mkdir(exist_ok=True)

FDA_DATA = Path(os.path.expanduser("~")) / "fda-data"
SNAP = FDA_DATA / "snapshots" / "2026-10-26"
RAW = FDA_DATA / "raw"
UA = {"User-Agent": "Mozilla/5.0"}

NOAA_DIR_URL = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
CHR_URL = ("https://www.countyhealthrankings.org/sites/default/files/media/document/"
           "analytic_data2025_v3.csv")
CBP_URL = "https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23co.zip"

# NOAA numbers the 48 contiguous states alphabetically, then Hawaii 49 and Alaska 50
# (county-readme.txt). The Census codes are the ones the county table uses.
NOAA_ORDER = ["AL", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "ID", "IL", "IN", "IA", "KS",
              "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
              "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
              "VT", "VA", "WA", "WV", "WI", "WY", "HI", "AK"]
CENSUS_CODE = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
               "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
               "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25",
               "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32",
               "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
               "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
               "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
               "WY": "56"}
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def download(url, path):
    if path.exists():
        return path
    print("downloading", url)
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=300) as response:
        path.write_bytes(response.read())
    return path


def noaa_file():
    existing = sorted(RAW_DIR.glob("climdiv-tmpccy-*"))
    if existing:
        return existing[-1]
    request = urllib.request.Request(NOAA_DIR_URL, headers=UA)
    listing = urllib.request.urlopen(request, timeout=120).read().decode("utf-8", "replace")
    names = sorted(set(re.findall(r"climdiv-tmpccy-v[\d.]+-\d{8}", listing)))
    newest = names[-1]
    return download(NOAA_DIR_URL + newest, RAW_DIR / newest)


# ------------------------------------------------------------------ the Week 10 county table
with zipfile.ZipFile(SNAP / "census_gazetteer_counties_2025.zip") as z:
    gaz = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="|", dtype={"GEOID": str})
gaz.columns = [c.strip() for c in gaz.columns]
t = gaz[["GEOID", "USPS", "NAME", "INTPTLAT", "INTPTLONG"]].rename(columns={"INTPTLAT": "lat", "INTPTLONG": "lon"}).copy()

pop = pd.read_csv(RAW / "census_popest_counties_2024.csv", encoding="latin-1", dtype=str)
pop = pop[pop.SUMLEV == "050"].copy()
pop["GEOID"] = pop.STATE.str.zfill(2) + pop.COUNTY.str.zfill(3)
pop["POPESTIMATE2024"] = pd.to_numeric(pop.POPESTIMATE2024)
t = t.merge(pop[["GEOID", "POPESTIMATE2024"]], on="GEOID", how="left", validate="one_to_one")

ers = pd.read_excel(RAW / "ers_unemployment_income_2023.xlsx", sheet_name=0, skiprows=4,
                    dtype={"FIPS_Code": str}).copy()
ers["GEOID"] = ers.FIPS_Code.str.zfill(5)
ers = ers[~ers.GEOID.str.endswith("000")].copy()
ers["job_growth"] = 100 * (ers.Employed_2023 / ers.Employed_2018 - 1)
t = t.merge(ers[["GEOID", "job_growth", "Median_Household_Income_2022"]], on="GEOID", how="left",
            validate="one_to_one")

zil = pd.read_csv(SNAP / "zillow_zori_county.csv").copy()
month_cols = [c for c in zil.columns if c[:2] == "20" and len(c) == 10]
zil["GEOID"] = (zil.StateCodeFIPS.astype(int).map("{:02d}".format)
                + zil.MunicipalCodeFIPS.astype(int).map("{:03d}".format))
zil["rent_2026_09"] = zil[month_cols[-1]]
t = t.merge(zil[["GEOID", "rent_2026_09"]], on="GEOID", how="left", validate="one_to_one")

cbsa = pd.read_excel(RAW / "census_cbsa_delineation_2023.xlsx", skiprows=2, dtype=str)
cbsa = cbsa.dropna(subset=["FIPS State Code"]).copy()
cbsa["GEOID"] = cbsa["FIPS State Code"].str.zfill(2) + cbsa["FIPS County Code"].str.zfill(3)
cbsa = cbsa.rename(columns={"CBSA Title": "area_name",
                            "Metropolitan/Micropolitan Statistical Area": "area_type"})
t = t.merge(cbsa[["GEOID", "area_name", "area_type"]], on="GEOID", how="left", validate="one_to_one")

# ------------------------------------------------------------------ comfortable weather (NOAA)
noaa_to_census = {f"{i + 1:02d}": CENSUS_CODE[s] for i, s in enumerate(NOAA_ORDER)}
rows = []
with open(noaa_file()) as f:
    for line in f:
        year = int(line[7:11])
        if 2015 <= year <= 2024:
            values = [float(v) for v in line[11:].split()]
            rows.append([noaa_to_census[line[0:2]] + line[2:5]] + values)
temps = pd.DataFrame(rows, columns=["GEOID"] + MONTHS)
temps = temps.groupby("GEOID")[MONTHS].mean()
temps.columns = ["temp_" + m for m in MONTHS]
temps["avg_temp"] = temps.mean(axis=1)
t = t.merge(temps.reset_index(), on="GEOID", how="left", validate="one_to_one")

# ------------------------------------------------------------------ education (County Health Rankings)
chr_ = pd.read_csv(download(CHR_URL, RAW_DIR / "analytic_data2025_v3.csv"), skiprows=[1],
                   dtype={"5-digit FIPS Code": str}, low_memory=False)
chr_ = chr_[chr_["County FIPS Code"].astype(int) != 0].copy()
chr_["GEOID"] = chr_["5-digit FIPS Code"]
chr_["some_college"] = 100 * chr_["Some College raw value"]
t = t.merge(chr_[["GEOID", "some_college"]], on="GEOID", how="left", validate="one_to_one")

# ------------------------------------------------------------------ culture (County Business Patterns)
with zipfile.ZipFile(download(CBP_URL, RAW_DIR / "cbp23co.zip")) as z:
    cbp = pd.read_csv(z.open("cbp23co.txt"), dtype=str)
cbp = cbp[cbp.fipscty != "999"].copy()
cbp["GEOID"] = cbp.fipstate + cbp.fipscty
in_cbp = set(cbp[cbp.naics == "------"].GEOID)
arts = cbp[cbp.naics == "71----"].set_index("GEOID").est.astype(int)
t["arts_businesses"] = t.GEOID.map(arts)
# County Business Patterns lists only the industries a county has, so a county in the file
# with no arts row has zero arts businesses. A county missing from the file stays blank.
t.loc[t.GEOID.isin(in_cbp) & t.arts_businesses.isna(), "arts_businesses"] = 0
t["culture"] = 10_000 * t.arts_businesses / t.POPESTIMATE2024

t["label"] = t.NAME + ", " + t.USPS
t.to_csv(DATA_DIR / "county_factors.csv", index=False)

# ------------------------------------------------------------------ the three charts
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
BLUE = "#2f6db5"

by_state = (t.dropna(subset=["rent_2026_09"]).groupby("USPS").rent_2026_09
            .agg(["median", "count"]).sort_values("median", ascending=False))
top10 = by_state.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(top10.index, top10["median"], color=BLUE)
for y, (value, n) in enumerate(zip(top10["median"], top10["count"])):
    ax.text(value + 30, y, f"${value:,.0f} ({n} {'county' if n == 1 else 'counties'})", va="center", fontsize=9)
ax.set_xlim(0, 3800)
ax.set_xlabel("Median of the county rents, dollars per month")
ax.set_title("The ten states with the highest median rent, September 2026")
fig.tight_layout()
fig.savefig(CHART_DIR / "top10_rent.png", dpi=150)
plt.close(fig)

series = zil.set_index("GEOID")[month_cols].T
series.index = pd.to_datetime(series.index)
fig, ax = plt.subplots(figsize=(8, 5))
for geoid, name, color in [("05007", "Benton County, AR", BLUE), ("05143", "Washington County, AR", "#d9822b")]:
    ax.plot(series.index, series[geoid], label=name, color=color, linewidth=2)
ax.set_ylim(0, 1800)
ax.set_ylabel("Typical monthly rent, dollars")
ax.set_title("Typical monthly rent, January 2015 to September 2026")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(CHART_DIR / "rent_over_time.png", dpi=150)
plt.close(fig)

both = t.dropna(subset=["rent_2026_09", "Median_Household_Income_2022"])
shown = both[both.rent_2026_09 <= 4000]
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(shown.Median_Household_Income_2022 / 1000, shown.rent_2026_09, s=8, alpha=0.4, color=BLUE)
ax.set_xlabel("Median household income, 2022, thousands of dollars")
ax.set_ylabel("Typical monthly rent, September 2026, dollars")
ax.set_ylim(0, 4000)
ax.set_xlim(0, 180)
ax.set_title("Rent and income by county")
fig.tight_layout()
fig.savefig(CHART_DIR / "rent_income.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------------ data files for the interactive charts
by_state.rename(columns={"median": "median_rent", "count": "counties_with_rent"}).to_csv(
    DATA_DIR / "state_rent.csv")
history = zil.set_index("GEOID")[month_cols].round(0)
history.columns = [c[:7] for c in month_cols]
history.to_csv(DATA_DIR / "rent_history.csv")
two = series[["05007", "05143"]].rename(columns={"05007": "Benton County, AR", "05143": "Washington County, AR"})
two.index.name = "month"
two.to_csv(DATA_DIR / "rent_series.csv")
GEOJSON = HERE.parent.parent / "materials" / "data" / "us_counties_geojson.json"
# Simplified shapes: the map is a few hundred pixels wide, so detail finer than about half a
# kilometer is invisible, and the smaller file is sent to the browser on every redraw.
from shapely.geometry import mapping, shape  # noqa: E402


def round_coords(obj, digits=3):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, digits) for v in obj]
        return [round_coords(v, digits) for v in obj]
    return obj


geo = json.loads(GEOJSON.read_text())
for feature in geo["features"]:
    simple = shape(feature["geometry"]).simplify(0.005, preserve_topology=True)
    geometry = mapping(simple)
    feature["geometry"] = {"type": geometry["type"], "coordinates": round_coords(geometry["coordinates"])}
    feature["properties"] = {"NAME": feature["properties"].get("NAME")}
(DATA_DIR / "us_counties.json").write_text(json.dumps(geo, separators=(",", ":")))
print("map file", round(GEOJSON.stat().st_size / 1e6, 2), "MB ->",
      round((DATA_DIR / "us_counties.json").stat().st_size / 1e6, 2), "MB")

# ------------------------------------------------------------------ check numbers
benton = t[t.GEOID == "05007"].iloc[0]
print("rows", len(t))
for column in ["rent_2026_09", "job_growth", "avg_temp", "some_college", "culture"]:
    print(f"{column:14s} non-blank {t[column].notna().sum():5d}  median {t[column].median():9.1f}"
          f"  Benton {benton[column]:9.1f}")
print("Benton arts businesses", benton.arts_businesses, "| months 50-75 F",
      int(((benton[["temp_" + m for m in MONTHS]] >= 50) & (benton[["temp_" + m for m in MONTHS]] <= 75)).sum()))
print("top10 states", [(s, round(v)) for s, v in by_state.head(10)["median"].items()])
print("Benton rent Jan 2015", round(series["05007"].iloc[0]), "Sep 2026", round(series["05007"].iloc[-1]))
print("scatter points shown", len(shown), "left off", len(both) - len(shown),
      both[both.rent_2026_09 > 4000].label.tolist())
