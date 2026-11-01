"""Dataset schema, loading and validation.

The schema below is the single source of truth for the table structure.
``data/datapackage.json`` is generated from it:

    uv run python -m kulturne_nagrade.dataset --write-datapackage
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from functools import cache

from kulturne_nagrade import DATA_DIR

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
GENRES = [
    "literatura", "poezija", "film", "gledališče", "ples", "glasba",
    "likovno-vizualna umetnost", "arhitektura", "novinarstvo", "umetnost in kultura",
]
CONFIDENCE = ["high", "medium", "low"]
YEAR = {"minimum": 1900, "maximum": 2100}
SI_REGIONS = [
    "Osrednjeslovenska", "Gorenjska", "Goriška", "Obalno-kraška", "Primorsko-notranjska",
    "Jugovzhodna Slovenija", "Posavska", "Zasavska", "Savinjska", "Podravska", "Koroška",
    "Pomurska",
]


def f(name, type_="string", required=False, enum=None, pattern=None, **constraints):
    field = {"name": name, "type": type_}
    c = dict(constraints)
    if required:
        c["required"] = True
    if enum:
        c["enum"] = enum
    if pattern:
        c["pattern"] = pattern
    if c:
        field["constraints"] = c
    return field


def fk(fields, resource, ref_fields=None):
    return {"fields": fields, "reference": {"resource": resource, "fields": ref_fields or fields}}


SCHEMA: dict[str, dict] = {
    "awards": {
        "description": "One row per award.",
        "fields": [
            f("award_id", required=True, pattern=SLUG),
            f("name", required=True),
            f("genre", required=True, enum=GENRES),
            f("prestige", "integer", required=True, minimum=1, maximum=5),
            f("institution"),
            f("funding_source", enum=["state-majority", "state-agency", "mixed",
                                      "private-independent"]),
            f("funding_confidence", enum=CONFIDENCE),
            f("founded", "integer", **YEAR),
            f("ended", "integer", **YEAR),
            f("description"),
        ],
        "primaryKey": ["award_id"],
    },
    "editions": {
        "description": "One row per award edition (award + year; occasionally several per year).",
        "fields": [
            f("edition_id", required=True, pattern=SLUG),
            f("award_id", required=True),
            f("year", "integer", required=True, **YEAR),
            f("category"),
            f("jury_known", "boolean", required=True),
            f("source"),
        ],
        "primaryKey": ["edition_id"],
        "foreignKeys": [fk(["award_id"], "awards")],
    },
    "entities": {
        "description": "Award winners and jurors: people, groups, "
                       "institutions and works.",
        "fields": [
            f("entity_id", required=True, pattern=SLUG),
            f("name", required=True),
            f("entity_type", required=True, enum=["person", "group", "institution", "work"]),
            f("gender", enum=["m", "f"]),
            f("year_birth", "integer", **YEAR | {"minimum": 1800}),
            f("year_birth_source", enum=["wikidata", "viaf", "llm", "enrichment"]),
            f("year_birth_estimate", "integer", **YEAR),
            f("year_death", "integer", **YEAR | {"minimum": 1800}),
            f("enrichment_confidence", enum=CONFIDENCE),
            f("note"),
        ],
        "primaryKey": ["entity_id"],
    },
    "roles": {
        "description": "Who won or judged which edition.",
        "fields": [
            f("edition_id", required=True),
            f("entity_id", required=True),
            f("role", required=True, enum=["winner", "jury"]),
            f("ord", "integer", required=True, minimum=1),
        ],
        "primaryKey": ["edition_id", "entity_id", "role"],
        "foreignKeys": [fk(["edition_id"], "editions"), fk(["entity_id"], "entities")],
    },
    "aliases": {
        "description": "Alternate spellings of entity names found in sources.",
        "fields": [f("alias", required=True), f("entity_id", required=True)],
        "primaryKey": ["alias"],
        "foreignKeys": [fk(["entity_id"], "entities")],
    },
    "entity_locations": {
        "description": "Places associated with an entity (from enrichment).",
        "fields": [f("entity_id", required=True), f("ord", "integer", required=True),
                   f("place", required=True)],
        "primaryKey": ["entity_id", "ord"],
        "foreignKeys": [fk(["entity_id"], "entities"), fk(["place"], "places")],
    },
    "places": {
        "description": "Geocoded place strings of entity_locations (OpenStreetMap Nominatim; "
                       "statistical regions by point-in-polygon against GADM 4.1).",
        "fields": [
            f("place", required=True),
            f("canonical", required=True),
            f("kind", required=True,
              enum=["settlement", "region", "country", "natural", "other", "unknown"]),
            f("scope", enum=["si", "foreign"]),
            f("country_code", pattern=r"^[a-z]{2}$"),
            f("si_region", enum=SI_REGIONS),
            f("si_municipality"),
            f("is_ljubljana", "boolean", required=True),
            f("lat", "number", minimum=-90, maximum=90),
            f("lon", "number", minimum=-180, maximum=180),
            f("resolution", required=True),
            f("confidence", required=True, enum=CONFIDENCE),
            f("note"),
        ],
        "primaryKey": ["place"],
    },
    "regions": {
        "description": "Population of the Slovenian statistical regions, with the City "
                       "Municipality of Ljubljana carved out of Osrednjeslovenska.",
        "fields": [
            f("region", required=True, enum=["Ljubljana"] + SI_REGIONS),
            f("population", "integer", required=True, minimum=1),
            f("population_date", "date", required=True),
            f("source", required=True),
            f("note"),
        ],
        "primaryKey": ["region"],
    },
    "entity_offices": {
        "description": "Public offices and memberships held (from enrichment).",
        "fields": [f("entity_id", required=True),
                   f("kind", required=True, enum=["office", "membership"]),
                   f("ord", "integer", required=True), f("text", required=True)],
        "primaryKey": ["entity_id", "kind", "ord"],
        "foreignKeys": [fk(["entity_id"], "entities")],
    },
    "entity_sources": {
        "description": "Source domains consulted during enrichment.",
        "fields": [f("entity_id", required=True), f("source", required=True)],
        "primaryKey": ["entity_id", "source"],
        "foreignKeys": [fk(["entity_id"], "entities")],
    },
}


def _convert(value: str, type_: str):
    if value == "":
        return None
    if type_ == "integer":
        return int(value)
    if type_ == "number":
        return float(value)
    if type_ == "date" and not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise ValueError(f"not an ISO date: {value!r}")
    if type_ == "boolean":
        if value not in ("True", "False"):
            raise ValueError(f"not a boolean: {value!r}")
        return value == "True"
    return value


@cache
def load(table: str) -> tuple[dict, ...]:
    """Load a table as typed dicts (empty cells become None). Cached; treat as read-only."""
    types = {fl["name"]: fl["type"] for fl in SCHEMA[table]["fields"]}
    with open(DATA_DIR / f"{table}.csv", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != list(types):
            raise ValueError(f"{table}: columns {reader.fieldnames} != schema {list(types)}")
        return tuple({k: _convert(v, types[k]) for k, v in row.items()} for row in reader)


def validate() -> list[str]:
    """Check types, constraints, primary keys and foreign keys. Returns error messages."""
    errors: list[str] = []
    tables = {}
    for name, schema in SCHEMA.items():
        try:
            rows = tables[name] = load(name)
        except (ValueError, OSError) as e:
            errors.append(f"{name}: {e}")
            continue
        for i, row in enumerate(rows, start=2):
            for fl in schema["fields"]:
                v, c = row[fl["name"]], fl.get("constraints", {})
                where = f"{name}.csv:{i} {fl['name']}={v!r}"
                if v is None:
                    if c.get("required"):
                        errors.append(f"{where}: required")
                    continue
                if "enum" in c and v not in c["enum"]:
                    errors.append(f"{where}: not in {c['enum']}")
                if "pattern" in c and not re.match(c["pattern"], v):
                    errors.append(f"{where}: does not match {c['pattern']}")
                if "minimum" in c and v < c["minimum"] or "maximum" in c and v > c["maximum"]:
                    errors.append(f"{where}: out of range")
        pk = Counter(tuple(r[k] for k in schema["primaryKey"]) for r in rows)
        errors += [f"{name}: duplicate primary key {k}" for k, n in pk.items() if n > 1]

    for name, schema in SCHEMA.items():
        if name not in tables:
            continue
        for key in schema.get("foreignKeys", []):
            ref = key["reference"]
            if ref["resource"] not in tables:
                continue
            targets = {tuple(r[k] for k in ref["fields"]) for r in tables[ref["resource"]]}
            for i, row in enumerate(tables[name], start=2):
                v = tuple(row[k] for k in key["fields"])
                if v not in targets:
                    errors.append(f"{name}.csv:{i}: {key['fields']}={v} not in {ref['resource']}")
    return errors


CC_BY = {"name": "CC-BY-4.0", "title": "Creative Commons Attribution 4.0",
         "path": "https://creativecommons.org/licenses/by/4.0/"}
# places.csv holds coordinates geocoded with OpenStreetMap Nominatim
ODBL = {"name": "ODbL-1.0", "title": "Open Data Commons Open Database License 1.0",
        "path": "https://opendatacommons.org/licenses/odbl/1-0/"}


def datapackage() -> dict:
    return {
        "name": "kulturne-nagrade",
        "title": "Slovenske kulturne nagrade",
        "description": "Slovenian cultural awards: editions, winners and jurors.",
        "homepage": "https://virostatiq.com/kulturne-nagrade/",
        "licenses": [CC_BY],
        "resources": [
            {
                "name": name,
                "path": f"{name}.csv",
                "format": "csv",
                "encoding": "utf-8",
                "description": schema["description"],
                **({"licenses": [ODBL]} if name == "places" else {}),
                "schema": {k: v for k, v in schema.items() if k != "description"},
            }
            for name, schema in SCHEMA.items()
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-datapackage", action="store_true")
    args = ap.parse_args()
    if args.write_datapackage:
        path = DATA_DIR / "datapackage.json"
        path.write_text(json.dumps(datapackage(), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"wrote {path}")
    errors = validate()
    print("\n".join(errors[:50]) or "dataset valid")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
