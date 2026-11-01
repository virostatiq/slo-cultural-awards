"""One-off: build data/places.csv and data/regions.csv from the legacy geocoding.

The legacy project geocoded every free-text place string of the person enrichment
(OpenStreetMap Nominatim, plus GADM 4.1 point-in-polygon for the 12 statistical regions;
see ../test/nagrade/geo_locations.py). This script maps each distinct
``entity_locations.place`` string to its geocoded record through the legacy
canonicaliser, applies the hand fixes in ``FIXES`` and writes one row per place string.

Like migrate_legacy.py, it refuses to overwrite data/places.csv: once written, the CSV
is the source of truth and is edited directly.

    uv run python scripts/migrate_places.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / "test" / "nagrade"
OUT = ROOT / "data" / "places.csv"
REGIONS_OUT = ROOT / "data" / "regions.csv"

FIELDS = ["place", "canonical", "kind", "scope", "country_code", "si_region",
          "si_municipality", "is_ljubljana", "lat", "lon", "resolution", "confidence", "note"]

# Hand fixes to the legacy geocoding, found while checking the ambiguous and
# low-confidence matches (2026-11-01). Keyed by canonical name.
FIXES = {
    # "Slovenian reading wins" picked a hamlet near Črnomelj; in these biographies it is Rome.
    "Rim": {"kind": "settlement", "scope": "foreign", "country_code": "it", "si_region": "",
                "si_municipality": "", "lat": 41.89332, "lon": 12.48293, "resolution": "override",
                "confidence": "high", "note": "Rim = Rome (legacy geocoder chose a hamlet near Črnomelj)"},
    # Fuzzy matches that landed in the wrong country.
    "Metelkova Mesto": {"kind": "other", "scope": "si", "country_code": "si",
                            "si_region": "Osrednjeslovenska", "si_municipality": "Ljubljana",
                            "is_ljubljana": True, "lat": 46.05697, "lon": 14.51708,
                            "resolution": "override", "confidence": "high",
                            "note": "autonomous cultural centre in Ljubljana"},
    "Latinska Amerika": {"kind": "region", "scope": "foreign", "country_code": "", "lat": "", "lon": "",
                             "resolution": "override", "confidence": "high", "note": "world region"},
    "University of Oxford": {"kind": "other", "scope": "foreign", "country_code": "gb",
                                 "lat": 51.7548, "lon": -1.2544, "resolution": "override",
                                 "confidence": "high", "note": ""},
    "Rab": {"kind": "settlement", "scope": "foreign", "country_code": "hr", "lat": 44.7562,
                "lon": 14.7600, "resolution": "override", "confidence": "high", "note": "island of Rab"},
    "Seattle, Washington, ZDA": {"kind": "settlement", "scope": "foreign", "country_code": "us",
                                     "lat": 47.6062, "lon": -122.3321, "resolution": "override",
                                     "confidence": "high", "note": ""},
    # Ljubljana districts the legacy flagged as separate places.
    "Šentvid pri Ljubljani": {"is_ljubljana": True, "si_municipality": "Ljubljana"},
    "Polje pri Ljubljani": {"is_ljubljana": True, "si_municipality": "Ljubljana"},
    # Žabja vas is in Nova Gorica, not a Ljubljana district.
    "Žabja vas": {"is_ljubljana": False, "si_region": "Goriška", "si_municipality": "Nova Gorica",
                      "lat": 45.9469, "lon": 13.6497, "note": "Nova Gorica"},
}

# Population on 1 January 2025 (SURS). Ljubljana = the City Municipality of Ljubljana
# (SURS, mid-2024), carved out of Osrednjeslovenska as its own unit: the
# Osrednjeslovenska row excludes it.
REGIONS = [
    ("Ljubljana", 297_575),
    ("Osrednjeslovenska", 569_475 - 297_575),
    ("Gorenjska", 209_921), ("Goriška", 118_096), ("Obalno-kraška", 119_627),
    ("Primorsko-notranjska", 53_826), ("Jugovzhodna Slovenija", 148_670),
    ("Posavska", 75_993), ("Zasavska", 57_083), ("Savinjska", 262_814),
    ("Podravska", 331_815), ("Koroška", 70_358), ("Pomurska", 113_172),
]


def main() -> None:
    if OUT.exists():
        sys.exit(f"{OUT} exists; it is the source of truth now. Edit it directly.")
    sys.path.insert(0, str(LEGACY))
    from geo_locations import canonical  # legacy alias folding

    geo = {p["canon"]: p for p in json.loads(
        (LEGACY / "data/reference/locations_geo.json").read_text())["places"]}
    with open(ROOT / "data/entity_locations.csv", encoding="utf-8") as fh:
        places = sorted({r["place"] for r in csv.DictReader(fh)})

    rows = []
    for place in places:
        canon = canonical(place)
        g = dict(geo[canon])  # KeyError = a place the legacy never geocoded: stop
        g.update(FIXES.get(canon, {}))
        row = {k: g.get(k, "") for k in FIELDS}
        row.update(place=place, canonical=canon)
        if row["scope"] != "si":
            row["is_ljubljana"] = False
        for k in ("lat", "lon"):
            row[k] = "" if row[k] in ("", None) else f"{float(row[k]):.5f}"
        row["note"] = (row["note"] or "").replace("\n", " ").strip()
        if row["kind"] == "unknown":
            row["scope"] = ""
        rows.append(row)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(REGIONS_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["region", "population", "population_date", "source", "note"])
        for name, pop in REGIONS:
            note = {"Ljubljana": "Mestna občina Ljubljana",
                    "Osrednjeslovenska": "brez Mestne občine Ljubljana"}.get(name, "")
            w.writerow([name, pop, "2025-01-01", "SURS", note])
    print(f"wrote {len(rows)} places, {len(REGIONS)} regions")


if __name__ == "__main__":
    main()
