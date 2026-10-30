# Notebooks

Original collection notebooks, kept for provenance. They are numbered in the order they were
written and are **not required** to rebuild the dashboard: `data/raw/*.pkl` is the committed,
reproducible input for `scripts/build_data.py`.

| Notebook | Site | Output |
|---|---|---|
| `01_fourseasons_scraper.ipynb` | viagginaturaecultura.it (FourSeasons) | `df_viaggi_fourseasons.pkl` |
| `02_sivola_scraper.ipynb` | sivola.it | `df_viaggi_sivola.pkl` |
| `03_viaggiavventure_scraper.ipynb` | viaggiavventurenelmondo.it | `df_viaggi_viaggiavventure.pkl` |
| `04_weroad_scraper.ipynb` | weroad.it | `df_viaggi_weroad.pkl` |
| `05_google_flights_scraper.ipynb` | Google Flights | flight experiments (see `../flight_analysis/`) |
| `06_langchain_tools.ipynb` | — | early LangChain over trip text |

## Notes

- The WeRoad notebook originally captured a Google Maps API key embedded in the site's HTML.
  It has been replaced with `REDACTED_GOOGLE_MAPS_KEY` in the committed copy.
- Outputs and execution counts were cleared so the repository stays small and free of scraped
  page dumps. The notebooks are brittle by nature: selectors and page layouts change. Treat them
  as a record of how the data was collected, not as a maintained library.
- To rerun a notebook, install `requirements.txt` and provide your own ChromeDriver / browser
  environment. Some notebooks reference Google Colab paths.
