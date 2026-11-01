"""Integrity checks for the dataset in data/."""

import json
from collections import defaultdict

from kulturne_nagrade import DATA_DIR
from kulturne_nagrade.dataset import datapackage, load, validate


def test_schema_constraints_and_keys():
    errors = validate()
    assert not errors, "\n".join(errors[:30])


def test_datapackage_is_up_to_date():
    on_disk = json.loads((DATA_DIR / "datapackage.json").read_text(encoding="utf-8"))
    assert on_disk == datapackage(), "run: python -m kulturne_nagrade.dataset --write-datapackage"


def test_jury_known_matches_roles():
    has_jury = {r["edition_id"] for r in load("roles") if r["role"] == "jury"}
    wrong = [e["edition_id"] for e in load("editions")
             if e["jury_known"] != (e["edition_id"] in has_jury)]
    assert not wrong, wrong[:10]


def test_edition_years_within_award_history():
    awards = {a["award_id"]: a for a in load("awards")}
    wrong = [e["edition_id"] for e in load("editions")
             if (a := awards[e["award_id"]])["ended"] and e["year"] > a["ended"]]
    assert not wrong, wrong[:10]


def test_life_dates_are_consistent():
    wrong = [e["entity_id"] for e in load("entities")
             if e["year_birth"] and e["year_death"] and e["year_death"] < e["year_birth"]]
    assert not wrong, wrong


def test_only_persons_have_personal_data():
    wrong = [e["entity_id"] for e in load("entities") if e["entity_type"] != "person"
             and (e["gender"] or e["year_birth"] or e["year_birth_estimate"])]
    assert not wrong, wrong


def test_birth_year_and_estimate_are_exclusive():
    wrong = [e["entity_id"] for e in load("entities")
             if e["year_birth"] and e["year_birth_estimate"]]
    assert not wrong, wrong
    unsourced = [e["entity_id"] for e in load("entities")
                 if e["year_birth"] and not e["year_birth_source"]]
    assert not unsourced, unsourced


def test_names_are_clean():
    bad = [e["name"] for e in load("entities")
           if e["name"] != e["name"].strip() or "  " in e["name"] or "," in e["name"]]
    assert not bad, bad


def test_aliases_do_not_shadow_canonical_names():
    names = {e["name"] for e in load("entities")}
    clash = [a["alias"] for a in load("aliases") if a["alias"] in names]
    assert not clash, clash


def test_role_order_is_unique_within_edition():
    seen = defaultdict(list)
    for r in load("roles"):
        seen[(r["edition_id"], r["role"])].append(r["ord"])
    dup = [k for k, ords in seen.items() if len(ords) != len(set(ords))]
    assert not dup, dup[:10]
