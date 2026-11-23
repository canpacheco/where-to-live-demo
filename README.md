# Where should a finance graduate live?

This is a demo website that helps a new finance graduate decide where to live. It opens with a short quiz of about a dozen silly trade-off questions, such as a hike on a perfect day against a stadium concert. The quiz picks each question from the earlier answers and ranks six factors: rent, job outlook, comfortable weather, education, culture, and distance to family.

The results page ranks US counties by those factors. The Ranking section shows the top three, a chart of what drives the top ten, a county map of fit scores, the top counties, and a few trail hazards. The Compare section is a small dashboard of two counties, with rent over time and a year of weather. The How this works section explains the data, the sources, the quiz, and the fit score.

## Data

| Factor | Measure | Source |
|---|---|---|
| Rent | typical monthly rent, September 2026 | Zillow Observed Rent Index |
| Job outlook | change in employed residents, 2018 to 2023 | USDA Economic Research Service |
| Comfortable weather | months a year with an average temperature in the visitor's range | NOAA county temperatures, 2015 to 2024 |
| Education | share of adults aged 25 to 44 with some college | County Health Rankings, 2025 |
| Culture | arts, entertainment, and recreation businesses per 10,000 residents | Census County Business Patterns, 2023 |
| Distance to family | straight-line miles between county centers | Census Bureau 2025 county list |

`data/county_factors.csv` holds one row per county, and `data/rent_history.csv` holds each county's monthly rent. `build_demo_data.py` rebuilds both from the public files.

The look is a homage to a classic computer game about moving west. The pixel wagon is original art drawn in code, and the fonts are Press Start 2P and VT323 from Google Fonts.

The trail music is an original 8-bit arrangement of Korobeiniki, a Russian folk song in the public domain, synthesized in the browser with the Web Audio API. It starts on the first click or key press, since browsers block sound before that, and the speaker button mutes it.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```
