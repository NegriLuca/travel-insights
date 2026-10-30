"""Turn the scraped travel catalogues into the JSON consumed by the dashboard."""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .canonical import COUNTRIES, canonicalise

OPERATORS = {
    "weroad": ("WeRoad", "df_viaggi_weroad.pkl"),
    "sivola": ("SiVola", "df_viaggi_sivola.pkl"),
    "viaggiavventure": ("ViaggiAvventure", "df_viaggi_viaggiavventure.pkl"),
    "fourseasons": ("FourSeasons", "df_viaggi_fourseasons.pkl"),
}

REGION_ORDER = ["Europa", "Asia", "Africa", "Americhe", "Oceania", "Altro"]

VIBES: dict[str, re.Pattern[str]] = {
    "Culture": re.compile(r"cultur|muse|arte|archeolog|monument|temp(io|le)|patrimonio", re.I),
    "History": re.compile(r"storia|history|historic|antich|imperial|romano|castell", re.I),
    "Nature": re.compile(r"natura|nature|parco|park|montagn|ghiacc|vulcan|foresta|lag[ohi]|fiord", re.I),
    "Adventure": re.compile(r"avventur|adventure|trekking|trek|hiking|zaino|4x4|canyon|rafting", re.I),
    "Relax": re.compile(r"relax|chill|terme|onsen|spa\b|benessere|tranquill", re.I),
    "Beach & islands": re.compile(r"\bmare\b|beach|spiagg|isola|island|snorkel|diving|atoll", re.I),
    "Food & wine": re.compile(r"food|cucina|gastronom|vino|wine|street food|mercato", re.I),
    "Party": re.compile(r"party|nightlife|movida|festival|club", re.I),
    "City": re.compile(r"\bcity\b|città|shopping|urbano|metropol", re.I),
    "On the road": re.compile(r"on the road|road trip|\bvan\b|itinerante|in moto", re.I),
}

REGION_COLORS = {
    "Europa": "#5b8cff",
    "Asia": "#ff8a5b",
    "Africa": "#f2c14e",
    "Americhe": "#4fd1a5",
    "Oceania": "#b388ff",
    "Altro": "#8b93a7",
}


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "{}", "[]"} else text


def _extract_days(itinerary: object, mood: object, title: object) -> int | None:
    text = " ".join(_clean(v) for v in (itinerary, mood, title))
    for pattern in (r"Giorno\s*(\d+)", r"\bDay\s*(\d+)", r"giorni?\s*(\d+)"):
        found = [int(n) for n in re.findall(pattern, text, re.I) if 0 < int(n) <= 60]
        if found:
            return max(found)
    match = re.search(r"(\d+)\s*giorn", text, re.I)
    if match and 0 < int(match.group(1)) <= 60:
        return int(match.group(1))
    return None


def _word_count(value: object) -> int:
    return len(re.findall(r"[\wÀ-ÿ]+", _clean(value)))


def _median(values: list[int]) -> int | None:
    return int(statistics.median(values)) if values else None


def load_trips(raw_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, (label, filename) in OPERATORS.items():
        path = raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"missing dataset: {path}")
        frame = pd.read_pickle(path)
        for _, row in frame.iterrows():
            name = _clean(row.get("Nome_Viaggio")) or "Senza titolo"
            subtitle = _clean(row.get("Sottotitolo_Viaggio"))
            country, region = canonicalise(
                row.get("Country"),
                fallback_text=f"{name} {subtitle}",
            )
            days = _extract_days(row.get("Itinerario"), row.get("Mood Viaggio"), name)
            words = _word_count(row.get("Descrizione Viaggio"))
            itinerary = _clean(row.get("Itinerario"))
            rows.append(
                {
                    "name": name,
                    "operator": key,
                    "operator_label": label,
                    "country": country or "Non specificato",
                    "region": region or "Altro",
                    "days": days,
                    "words": words,
                    "has_itinerary": bool(re.search(r"Giorno\s*\d+|\bDay\s*\d+", itinerary, re.I)),
                    "url": _clean(row.get("Link")),
                    "itinerary": itinerary,
                    "mood": _clean(row.get("Mood Viaggio")),
                    "subtitle": subtitle,
                }
            )
    return pd.DataFrame(rows)


def _vibes_for_trip(row: pd.Series) -> set[str]:
    # Titles, subtitles and mood tags are much less noisy than full descriptions.
    text = " ".join(str(row[k]) for k in ("name", "subtitle", "mood") if row.get(k))
    return {vibe for vibe, pattern in VIBES.items() if pattern.search(text)}


def build_payload(raw_dir: Path) -> dict[str, Any]:
    trips = load_trips(raw_dir)
    trips["vibes"] = trips.apply(_vibes_for_trip, axis=1)

    operator_rows = []
    for key, (label, _) in OPERATORS.items():
        group = trips[trips["operator"] == key]
        country_counts = group.loc[group["country"] != "Non specificato", "country"].value_counts()
        days = [int(d) for d in group["days"].dropna()]
        words = [int(w) for w in group["words"] if w > 0]
        vibe_counter: Counter[str] = Counter()
        for vibes in group["vibes"]:
            vibe_counter.update(vibes)
        operator_rows.append(
            {
                "key": key,
                "label": label,
                "trips": int(len(group)),
                "countries": int(country_counts.size),
                "median_days": _median(days),
                "median_words": _median(words),
                "itinerary_coverage": round(float(group["has_itinerary"].mean()) * 100, 1),
                "top_country": country_counts.index[0] if len(country_counts) else "—",
                "top_vibe": vibe_counter.most_common(1)[0][0] if vibe_counter else "—",
            }
        )

    country_counter: Counter[str] = Counter()
    country_operators: dict[str, Counter[str]] = defaultdict(Counter)
    country_region: dict[str, str] = {}
    for _, row in trips.iterrows():
        country = row["country"]
        if country == "Non specificato":
            continue
        country_counter[country] += 1
        country_operators[country][row["operator_label"]] += 1
        country_region[country] = row["region"]

    top_countries = [
        {
            "country": country,
            "region": country_region.get(country, "Altro"),
            "trips": count,
            "operators": dict(country_operators[country]),
        }
        for country, count in country_counter.most_common(18)
    ]

    region_counts = Counter(row["region"] for _, row in trips.iterrows())
    regions = [
        {
            "region": region,
            "trips": int(region_counts.get(region, 0)),
            "color": REGION_COLORS.get(region, "#8b93a7"),
        }
        for region in REGION_ORDER
        if region_counts.get(region, 0)
    ]

    vibe_totals = Counter()
    vibe_matrix: dict[str, Counter[str]] = {vibe: Counter() for vibe in VIBES}
    for _, row in trips.iterrows():
        for vibe in row["vibes"]:
            vibe_totals[vibe] += 1
            vibe_matrix[vibe][row["operator_label"]] += 1
    operator_labels = [label for label, _ in OPERATORS.values()]
    vibes = [
        {
            "vibe": vibe,
            "total": int(vibe_totals[vibe]),
            "by_operator": {label: int(vibe_matrix[vibe][label]) for label in operator_labels},
        }
        for vibe in sorted(vibe_totals, key=vibe_totals.get, reverse=True)
    ]

    buckets = list(range(1, 16))
    days_hist = []
    for key, (label, _) in OPERATORS.items():
        counts = Counter(int(d) for d in trips.loc[trips["operator"] == key, "days"].dropna())
        for bucket in buckets:
            value = sum(v for day, v in counts.items() if (day >= 15 if bucket == 15 else day == bucket))
            days_hist.append({"operator": label, "days": bucket, "trips": int(value)})

    days_values = [int(d) for d in trips["days"].dropna()]
    words_values = [int(w) for w in trips["words"] if w > 0]
    total = int(len(trips))
    covered = int((trips["country"] != "Non specificato").sum())

    trip_rows = []
    for _, row in trips.iterrows():
        trip_rows.append(
            {
                "name": row["name"],
                "operator": row["operator_label"],
                "country": row["country"],
                "region": row["region"],
                "days": int(row["days"]) if pd.notna(row["days"]) else None,
                "words": int(row["words"]),
                "url": row["url"],
            }
        )
    trip_rows.sort(key=lambda item: (item["operator"], -(item["days"] or 0), item["name"]))

    return {
        "meta": {
            "generated_from": "4 scraped catalogues (May 2024 snapshot)",
            "operators": len(OPERATORS),
            "trips": total,
            "destinations_resolved": covered,
            "destination_coverage": round(covered / total * 100, 1) if total else 0,
            "countries": int(country_counter.__len__()),
            "median_days": _median(days_values),
            "median_words": _median(words_values),
            "itinerary_coverage": round(float(trips["has_itinerary"].mean()) * 100, 1),
            "regions": regions,
        },
        "operators": operator_rows,
        "top_countries": top_countries,
        "vibes": vibes,
        "days_hist": days_hist,
        "trips": trip_rows,
    }


def write_payload(raw_dir: Path, out_path: Path, extra_copies: list[Path] | None = None) -> dict[str, Any]:
    payload = build_payload(raw_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    out_path.write_text(text, encoding="utf-8")
    for copy in extra_copies or []:
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_text(text, encoding="utf-8")
    return payload


if __name__ == "__main__":  # pragma: no cover
    root = Path(__file__).resolve().parents[2]
    write_payload(root / "data" / "raw", root / "data" / "processed" / "travel_insights.json")
    print("wrote data/processed/travel_insights.json")
