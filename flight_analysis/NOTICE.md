# Vendored notice

`google_flight_analysis/` is a modified copy of the MIT-licensed package
[`celebi-pkg/flight-analysis`](https://github.com/celebi-pkg/flight-analysis).

- Upstream commit used locally: `e73aa71` (v1.1.1-alpha line)
- Original license: MIT — see [`LICENSE`](LICENSE)
- No affiliation with the upstream author.

## Local changes

The copy in this repository includes fixes needed to parse the Google Flights page as of the
2024 experiments:

- **EUR support** — prices expressed as `€` are parsed in addition to `$`.
- **Round-trip column** — a new `A_R` field distinguishes outbound/return rows.
- **CO₂e parsing** — handles `CO2e` labels and thousands separators.
- **Origin/destination** — recognises the `–`-separated `FCO–JFK` format.
- **Round-trip / accessibility noise** — ignores labels such as `round trip`,
  `Avoids as much CO2e` and standalone `–` tokens.

The notebooks in `../notebooks/05_google_flights_scraper.ipynb` show the scraping experiments that
motivated these changes. The vendored code is provided for reference; it is not installed by
default with the analysis pipeline.
