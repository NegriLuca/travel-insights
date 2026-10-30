"""Country / region normalisation for the scraped travel catalogues.

The source catalogues expose destinations in very different ways: clean country
names, marketing collections ("Hai voglia di vibes da isola?"), macro regions
("Sud Europa") or lists of countries.  This module turns all of that into a
best-effort ``(country, region)`` pair without pretending to be perfect.
"""

from __future__ import annotations

import re
from typing import Iterable

REGIONS = {
    "Europa": "Europa",
    "Asia": "Asia",
    "Africa": "Africa",
    "Americhe": "Americhe",
    "Oceania": "Oceania",
}

# country -> continent
COUNTRIES: dict[str, str] = {
    # Europe
    "Italia": "Europa",
    "Grecia": "Europa",
    "Francia": "Europa",
    "Spagna": "Europa",
    "Portogallo": "Europa",
    "Germania": "Europa",
    "Austria": "Europa",
    "Svizzera": "Europa",
    "Paesi Bassi": "Europa",
    "Belgio": "Europa",
    "Regno Unito": "Europa",
    "Irlanda": "Europa",
    "Norvegia": "Europa",
    "Svezia": "Europa",
    "Finlandia": "Europa",
    "Danimarca": "Europa",
    "Islanda": "Europa",
    "Polonia": "Europa",
    "Repubblica Ceca": "Europa",
    "Slovacchia": "Europa",
    "Ungheria": "Europa",
    "Romania": "Europa",
    "Bulgaria": "Europa",
    "Croazia": "Europa",
    "Slovenia": "Europa",
    "Serbia": "Europa",
    "Bosnia ed Erzegovina": "Europa",
    "Montenegro": "Europa",
    "Albania": "Europa",
    "Macedonia del Nord": "Europa",
    "Kosovo": "Europa",
    "Estonia": "Europa",
    "Lettonia": "Europa",
    "Lituania": "Europa",
    "Ucraina": "Europa",
    "Russia": "Europa",
    "Turchia": "Europa",
    "Cipro": "Europa",
    "Malta": "Europa",
    # Asia
    "Giappone": "Asia",
    "Cina": "Asia",
    "Corea del Sud": "Asia",
    "Thailandia": "Asia",
    "Vietnam": "Asia",
    "Cambogia": "Asia",
    "Laos": "Asia",
    "Myanmar": "Asia",
    "Indonesia": "Asia",
    "Malesia": "Asia",
    "Singapore": "Asia",
    "Filippine": "Asia",
    "India": "Asia",
    "Nepal": "Asia",
    "Bhutan": "Asia",
    "Sri Lanka": "Asia",
    "Maldive": "Asia",
    "Pakistan": "Asia",
    "Bangladesh": "Asia",
    "Uzbekistan": "Asia",
    "Kazakistan": "Asia",
    "Kirghizistan": "Asia",
    "Tagikistan": "Asia",
    "Turkmenistan": "Asia",
    "Mongolia": "Asia",
    "Giordania": "Asia",
    "Libano": "Asia",
    "Israele": "Asia",
    "Palestina": "Asia",
    "Arabia Saudita": "Asia",
    "Emirati Arabi Uniti": "Asia",
    "Oman": "Asia",
    "Qatar": "Asia",
    "Yemen": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Georgia": "Asia",
    "Armenia": "Asia",
    "Azerbaigian": "Asia",
    # Africa
    "Egitto": "Africa",
    "Marocco": "Africa",
    "Tunisia": "Africa",
    "Algeria": "Africa",
    "Libia": "Africa",
    "Senegal": "Africa",
    "Gambia": "Africa",
    "Ghana": "Africa",
    "Nigeria": "Africa",
    "Kenya": "Africa",
    "Tanzania": "Africa",
    "Uganda": "Africa",
    "Ruanda": "Africa",
    "Etiopia": "Africa",
    "Sudafrica": "Africa",
    "Namibia": "Africa",
    "Botswana": "Africa",
    "Zimbabwe": "Africa",
    "Zambia": "Africa",
    "Malawi": "Africa",
    "Mozambico": "Africa",
    "Madagascar": "Africa",
    "Mauritius": "Africa",
    "Seychelles": "Africa",
    "Capo Verde": "Africa",
    # Americas
    "Stati Uniti": "Americhe",
    "Canada": "Americhe",
    "Messico": "Americhe",
    "Guatemala": "Americhe",
    "Belize": "Americhe",
    "Honduras": "Americhe",
    "El Salvador": "Americhe",
    "Nicaragua": "Americhe",
    "Costa Rica": "Americhe",
    "Panama": "Americhe",
    "Cuba": "Americhe",
    "Giamaica": "Americhe",
    "Repubblica Dominicana": "Americhe",
    "Haiti": "Americhe",
    "Porto Rico": "Americhe",
    "Colombia": "Americhe",
    "Venezuela": "Americhe",
    "Ecuador": "Americhe",
    "Perù": "Americhe",
    "Bolivia": "Americhe",
    "Brasile": "Americhe",
    "Argentina": "Americhe",
    "Cile": "Americhe",
    "Uruguay": "Americhe",
    "Paraguay": "Americhe",
    "Guyana": "Americhe",
    "Suriname": "Americhe",
    # Oceania
    "Australia": "Oceania",
    "Nuova Zelanda": "Oceania",
    "Polinesia": "Oceania",
    "Figi": "Oceania",
    "Papua Nuova Guinea": "Oceania",
    "Vanuatu": "Oceania",
    "Samoa": "Oceania",
    "Tonga": "Oceania",
}

ALIASES: dict[str, str] = {
    "stati uniti d'america": "Stati Uniti",
    "stati uniti d’america": "Stati Uniti",
    "stati uniti": "Stati Uniti",
    "usa": "Stati Uniti",
    "new york": "Stati Uniti",
    "hawaii": "Stati Uniti",
    "california": "Stati Uniti",
    "regno unito": "Regno Unito",
    "inghilterra": "Regno Unito",
    "scozia": "Regno Unito",
    "gran bretagna": "Regno Unito",
    "madeira": "Portogallo",
    "canarie": "Spagna",
    "andalusia": "Spagna",
    "fuerteventura": "Spagna",
    "sicilia": "Italia",
    "sardegna": "Italia",
    "zanzibar": "Tanzania",
    "bali": "Indonesia",
    "tokyo": "Giappone",
    "kyoto": "Giappone",
    "dubai": "Emirati Arabi Uniti",
    "abu dhabi": "Emirati Arabi Uniti",
}

# Macro-region / marketing labels.  Checked only when no country matched.
REGION_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"nord europa|sud europa|est europa|europa dell'est|europa|balcani|scandinavia", re.I), "Europa"),
    (re.compile(r"asia|estremo oriente|medio oriente|sud est asiatico|dintorni", re.I), "Asia"),
    (re.compile(r"africa", re.I), "Africa"),
    (re.compile(r"america", re.I), "Americhe"),
    (re.compile(r"oceania|pacifico", re.I), "Oceania"),
]

SKIP_HINTS = re.compile(
    r"inusual|vibes|piedi per terra|collections?|tutti da scoprire|desideri|"
    r"isola\?|restare con",
    re.I,
)


def _candidate_aliases() -> list[tuple[str, str]]:
    pairs = {**{k.lower(): k for k in COUNTRIES}, **{k.lower(): v for k, v in ALIASES.items()}}
    return sorted(pairs.items(), key=lambda item: len(item[0]), reverse=True)


_ALIAS_PAIRS = _candidate_aliases()


def _iter_strings(value: object) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        text = value.strip()
        if text and text.lower() != "nan":
            yield text
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, dict):
        for key in value:
            yield from _iter_strings(key)


def match_country(text: str) -> tuple[str, str]:
    """Return ``(country, region)`` for a free-text destination label."""
    if not text:
        return "", ""
    haystack = text.lower()
    matches: list[tuple[int, int, str]] = []
    for alias, country in _ALIAS_PAIRS:
        found = re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", haystack)
        if found:
            # earliest mention wins; on a tie prefer the longer (more specific) alias
            matches.append((found.start(), -len(alias), country))
    if matches:
        country = min(matches)[2]
        return country, COUNTRIES.get(country, "")
    if SKIP_HINTS.search(text):
        return "", ""
    for pattern, region in REGION_HINTS:
        if pattern.search(text):
            return "", region
    return "", ""


def canonicalise(value: object, fallback_text: str = "") -> tuple[str, str]:
    """Resolve a raw ``Country`` value, optionally falling back to title/subtitle."""
    for candidate in _iter_strings(value):
        country, region = match_country(candidate)
        if country:
            return country, region
    if fallback_text:
        return match_country(fallback_text)
    return "", ""
