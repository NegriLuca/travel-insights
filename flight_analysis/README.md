# Flight Analysis (vendored fork)

Modified copy of [`celebi-pkg/flight-analysis`](https://github.com/celebi-pkg/flight-analysis)
used for the Google Flights experiments in this project.

```python
from google_flight_analysis.scrape import Scrape

result = Scrape("FCO", "JFK", "2024-06-01", "2024-06-10")
result.type = "round"
data = result.origin  # DataFrame including A_R, Price (€), ...
```

Key local fixes: EUR prices, round-trip (`A_R`) rows, `CO2e` parsing, en-dash origin/destination.
See [`NOTICE.md`](NOTICE.md) for the full list and attribution.

Requires `selenium`, `pandas`, `numpy`, `tqdm` and a matching ChromeDriver.
