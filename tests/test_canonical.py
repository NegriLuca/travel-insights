from travel_insights.canonical import canonicalise, match_country


def test_exact_country():
    assert match_country("Italia") == ("Italia", "Europa")


def test_alias_city():
    assert match_country("New York") == ("Stati Uniti", "Americhe")


def test_marketing_collection_is_skipped():
    assert match_country("Hai voglia di vibes da isola?") == ("", "")


def test_macro_region_without_country():
    assert match_country("Sud Europa") == ("", "Europa")
    assert match_country("Sud Est Asiatico") == ("", "Asia")


def test_country_wins_over_macro_region():
    assert match_country("I nostri viaggi in Francia, Belgio e Paesi Bassi") == ("Francia", "Europa")


def test_list_picks_first_resolved_country():
    assert canonicalise(["India", "Nepal", "Africa Centrale"]) == ("India", "Asia")


def test_fallback_text():
    assert canonicalise("", "Alla scoperta della Grecia più autentica") == ("Grecia", "Europa")


def test_empty():
    assert canonicalise(None) == ("", "")
    assert canonicalise("") == ("", "")
