# Where should a finance graduate live?

This is a demo website that ranks US counties by what matters to the visitor. The visitor drags five factors into order of importance, and the order sets how much each factor counts. The factors are rent, job outlook, education, culture, and comfortable weather.

The website has four parts. The Ranking tab shows the counties with the highest fit score, a county map of the scores, and a few trail hazards. The Compare tab shows two counties side by side. The Charts tab shows three interactive charts of county rents. The How this works tab explains the data, the sources, and the fit score.

## Data

| Factor | Measure | Source |
|---|---|---|
| Rent | typical monthly rent, September 2026 | Zillow Observed Rent Index |
| Job outlook | change in employed residents, 2018 to 2023 | USDA Economic Research Service |
| Education | share of adults aged 25 to 44 with some college | County Health Rankings, 2025 |
| Culture | arts, entertainment, and recreation businesses per 10,000 residents | Census County Business Patterns, 2023 |
| Comfortable weather | months a year with an average temperature in the visitor's range | NOAA county temperatures, 2015 to 2024 |

`data/county_factors.csv` holds one row per county. `build_demo_data.py` rebuilds it and the chart data from the public files.

The look is a homage to a classic computer game about moving west. The pixel wagon is original art drawn in code, and the fonts are Press Start 2P and VT323 from Google Fonts.

The trail music is an original 8-bit arrangement of Korobeiniki, a Russian folk song in the public domain, synthesized in the browser with the Web Audio API. It starts on the first click or key press, since browsers block sound before that, and the speaker button mutes it.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```
