#!/usr/bin/env python3
"""Build ``data/processed/travel_insights.json`` from the raw scraped pickles.

Optionally copies the same payload into the portfolio repository so the
dashboard stays in sync:

    PORTFOLIO_DATA=/path/to/NegriLuca.github.io/assets/data python scripts/build_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from travel_insights import write_payload  # noqa: E402


def main() -> None:
    out = ROOT / "data" / "processed" / "travel_insights.json"
    copies: list[Path] = []
    portfolio_data = os.environ.get("PORTFOLIO_DATA")
    if portfolio_data:
        copies.append(Path(portfolio_data) / "travel_insights.json")

    payload = write_payload(ROOT / "data" / "raw", out, copies)
    meta = payload["meta"]
    print(
        f"{meta['trips']:,} trips · {meta['operators']} operators · "
        f"{meta['countries']} countries · {meta['destination_coverage']}% resolved"
    )
    print(f"wrote {out.relative_to(ROOT)}")
    for copy in copies:
        print(f"copied → {copy}")


if __name__ == "__main__":
    main()
