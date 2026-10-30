# Travel Insights

Scraping and analysing **2,051 travel packages** from four Italian tour operators, then turning
the result into an interactive market dashboard.

- **Live dashboard:** https://negriluca.github.io/projects/travel-insights.html
- **Portfolio:** https://negriluca.github.io/

The project scrapes WeRoad, SiVola, ViaggiAvventure and FourSeasons, reconciles four very
different data models, and answers practical questions: which destinations dominate, how long
trips are, which "vibes" operators sell, and how much content each catalogue publishes.

---

## Results (May 2024 snapshot)

| Metric | Value |
|---|---|
| Packages | **2,051** |
| Operators | 4 |
| Resolved countries | **117** |
| Destination coverage | **94.4%** (the rest is explicit, not dropped) |
| Median trip length | 11 days |
| Median description | 467 words |

Highlights from the dashboard:

- **Italy, India and the United States** are the three largest resolved destinations.
- **Europe and Asia** account for roughly the same share of packages; Oceania is a niche.
- **Adventure** and **Nature** are the most common vibe tags, followed by Culture and History.
- **ViaggiAvventure** dominates the dataset by volume (1,345 packages) and publishes the longest
  descriptions; **SiVola** is the smallest and most concise catalogue.

---

## Why it is not trivial

The four catalogues do not share a schema:

| Operator | Destination field | Itinerary |
|---|---|---|
| WeRoad | mixes countries with marketing collections (“Hai voglia di vibes da isola?”) | nested dict serialised as a string |
| SiVola | mostly clean country/city names, some city labels (“New York”) | nested dict |
| ViaggiAvventure | **lists** of countries and macro-regions | `Giorno N` blocks |
| FourSeasons | **empty** `Country`; the country is only in the title/subtitle | nested dict |

The pipeline therefore treats everything as raw input:

1. **Scrape** — per-site collectors (Selenium, requests + trafilatura/BeautifulSoup).
2. **Normalise** — country aliases, lists, macro-regions, marketing labels and punctuation.
3. **Enrich** — trip length, description depth, structured-itinerary coverage, vibe tags.
4. **Publish** — one compact JSON payload consumed by a static Plotly dashboard.

The country resolver is deliberately explainable: it matches known countries and aliases,
falls back to the title/subtitle when the source field is empty, and labels unresolved packages
as `Non specificato` instead of guessing. See [`src/travel_insights/canonical.py`](src/travel_insights/canonical.py).

---

## Repository layout

```
travel-insights/
├── data/
│   ├── raw/                  # scraped pickles (committed, ~13 MB)
│   └── processed/            # generated travel_insights.json
├── notebooks/                # the original scrapers, numbered
├── src/travel_insights/
│   ├── canonical.py          # country / region normalisation
│   ├── insights.py           # aggregation + JSON payload
│   └── __init__.py
├── scripts/build_data.py     # CLI: raw pickles → JSON
├── flight_analysis/          # vendored fork of google-flight-analysis (MIT)
└── tests/
```

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/build_data.py
# 2,051 trips · 4 operators · 117 countries · 94.4% resolved
# wrote data/processed/travel_insights.json
```

The dashboard lives in the portfolio repository. To regenerate its copy directly:

```bash
PORTFOLIO_DATA=../NegriLuca.github.io/assets/data python scripts/build_data.py
```

### Tests

```bash
pytest
```

## Notebooks

| Notebook | What it does |
|---|---|
| `01_fourseasons_scraper.ipynb` | Scrapes FourSeasons / Viaggianaturaecultura product pages |
| `02_sivola_scraper.ipynb` | Scrapes SiVola trip cards |
| `03_viaggiavventure_scraper.ipynb` | Iterates `/viaggi/{id}` pages and extracts itineraries |
| `04_weroad_scraper.ipynb` | Scrapes WeRoad collections and trip pages |
| `05_google_flights_scraper.ipynb` | Google Flights experiments (see `flight_analysis/`) |
| `06_langchain_tools.ipynb` | Early LangChain tool experiments over the trip text |

The notebooks are kept for provenance. They are not required to rebuild the dashboard —
the committed pickles in `data/raw/` are the reproducible input. A Google Maps key that was
embedded in the scraped WeRoad HTML has been redacted to `REDACTED_GOOGLE_MAPS_KEY`.

## Data notes

- The dataset is a **May 2024 snapshot**; travel catalogues change frequently.
- `Country` resolution is best-effort: a package may span several countries. Marketing
  collections are mapped to the first concrete country found, or left unresolved.
- Trip length is the maximum `Giorno N` found in the itinerary, with a fallback to `Durata` /
  “N giorni” labels.
- Vibe tags are keyword-based (titles, subtitles, mood fields), not a trained classifier. They
  are useful for relative comparison, not for precise labelling.
- `airport-codes.csv` / airport reference data used during the flight experiments are public
  datasets and are not committed. Add them to `data/raw/` if you want to rerun those notebooks.

## Flight-analysis fork

`flight_analysis/` vendors the MIT-licensed package
[`celebi-pkg/flight-analysis`](https://github.com/celebi-pkg/flight-analysis) with local fixes
for the current Google Flights page:

- EUR prices (`€`) in addition to USD;
- round-trip (`A_R`) column;
- `CO2e` parsing and thousands separators;
- origin/destination strings using the `–` separator.

See [`flight_analysis/NOTICE.md`](flight_analysis/NOTICE.md) for attribution and the exact changes.

## Tech

Python · pandas · Selenium · BeautifulSoup · trafilatura · Plotly (dashboard) · pytest

## License

MIT — see [`LICENSE`](LICENSE). The vendored flight-analysis code remains under its original MIT
license (see `flight_analysis/LICENSE`).
