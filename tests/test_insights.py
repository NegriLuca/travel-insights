from pathlib import Path

import pytest

from travel_insights.insights import build_payload

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


@pytest.fixture(scope="module")
def payload():
    if not (RAW / "df_viaggi_weroad.pkl").exists():
        pytest.skip("raw scraped data not available")
    return build_payload(RAW)


def test_shape(payload):
    meta = payload["meta"]
    assert meta["trips"] > 2000
    assert meta["operators"] == 4
    assert meta["countries"] > 100
    assert meta["destination_coverage"] > 90


def test_operator_totals(payload):
    total = sum(operator["trips"] for operator in payload["operators"])
    assert total == payload["meta"]["trips"]
    assert {operator["label"] for operator in payload["operators"]} == {
        "WeRoad",
        "SiVola",
        "ViaggiAvventure",
        "FourSeasons",
    }


def test_top_countries(payload):
    countries = [row["country"] for row in payload["top_countries"]]
    assert "Italia" in countries
    assert payload["top_countries"][0]["trips"] > 0


def test_vibes_and_trips(payload):
    assert payload["vibes"]
    assert payload["vibes"][0]["total"] > 0
    assert len(payload["trips"]) == payload["meta"]["trips"]
    assert all("words" in trip for trip in payload["trips"])
    assert any(trip["days"] for trip in payload["trips"])


def test_regions(payload):
    regions = {row["region"] for row in payload["meta"]["regions"]}
    assert {"Europa", "Asia", "Africa", "Americhe"}.issubset(regions)
