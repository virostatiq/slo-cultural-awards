"""Apply the decisions from docs/review/duplicate-editions.md (and party-offices.md) to data/*.csv.

Each decision is listed below as data; applying it appends a row to
data/meta/edition_decisions.csv. Steps whose target no longer exists are
skipped, so re-running is harmless.

    uv run python scripts/apply_edition_decisions.py
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
LOG = DATA / "meta" / "edition_decisions.csv"
REVIEW = "docs/review/duplicate-editions.md"
SEARCH = "web search 2026-11-01"

# --- decisions -------------------------------------------------------------

DROP = {
    **{f"vecernica-{y}-2": f"duplicate of vecernica-{y - 1} shifted one year (legacy lines 1035-1057)"
       for y in range(2002, 2025)},
    "grumova-nagrada-2014-2": "exact duplicate",
    "borstnikovo-srecanje-2012-2": "subset of borstnikovo-srecanje-2012",
    "zlata-ptica-2013": "duplicate of zlata-ptica-2012 (ceremony 5. 6. 2013, STA)",
    "zlata-ptica-2012-2": "winners not found in any source; Kino Udarnik's golden nest is in zlata-ptica-2011",
    "majski-salon-2024": "no competition in 2024 (retrospective exhibition Od svetlobe k svetlobi)",
    "nagrada-marka-slodnjaka-2022": "not awarded; the ZDUS commission's sitting is kept via the other 2022 ZDUS editions",
    "trdinova-nagrada-1990": "not awarded (nor in 1991); no jury recorded",
}

# (source edition, target edition): move winners and jurors into target, drop source
MERGE = [
    *[(f"jenkova-nagrada-{y}-2", f"jenkova-nagrada-{y}") for y in (2002, 2003, 2005, 2006, 2007, 2008, 2009, 2010)],
    ("sovretova-nagrada-2002-2", "sovretova-nagrada-2002"),
    ("askercevo-priznanje-2018-2", "askercevo-priznanje-2018"),
    ("askercevo-priznanje-2022-2", "askercevo-priznanje-2022"),
    ("askercevo-priznanje-2024-2", "askercevo-priznanje-2024"),
    ("gibanica-2013-2", "gibanica-2013"),
    ("gibanica-2023-2", "gibanica-2023"),
    ("jurciceva-nagrada-2012-2", "jurciceva-nagrada-2012"),
]

# old edition -> (new edition, year)
MOVE = {
    "desetnica-2025-2": ("desetnica-2026", 2026),
    "kresnik-2025-2": ("kresnik-2026", 2026),
}

# Zlata ptica: every edition was labelled by the year it is *for*; the ceremony is the
# following spring. Relabel the whole series to the ceremony year (+1). Sources:
# "prvič podeljena za leto 1975" (dobreknjige.si); Svetina's 1975 award presented in 1976
# (Delo); 2004 -> 14. 4. 2005, 2007 -> 26. 5. 2008 ("za leto 2007"), 2008 -> 7. 5. 2009,
# 2009 -> 10. 5. 2010, 2011 -> 5/2012 (rtvslo); 2012 -> 5. 6. 2013 (STA). 2014 unverified.
# award -> (first label before the shift, shift); the first label is the re-run sentinel
SHIFT_SERIES = {"zlata-ptica": (1975, 1)}
# award fields that move with the shift: award -> {field: new value}
# (award, field, value, source)
SET_AWARD = [
    ("zlata-ptica", "ended", "2015", None),  # last edition (for 2014) presented in 2015
    # an award for young artists in every field, not a literary prize
    ("zlata-ptica", "genre", "umetnost in kultura",
     "awards.csv description (literatura, film, glasba, scenske, vizualne in intermedijske "
     "umetnosti, arhitektura); user decision 2026-11-01"),
]
SHIFT_SOURCE = ("dobreknjige.si; delo.si (Svetina); rtvslo 135983, 155315, 159030, 229785; "
                "STA 5. 6. 2013")

# party posts in entity_offices.csv (political affiliation is not published)
PARTY_REVIEW = "docs/review/party-offices.md"
DELETE_OFFICES: list[tuple[str, str]] = []  # applied 2026-11-01; the list named people and
# their party posts, so it was removed before publication (see the review file)

# swap the jury rows of two editions (Kresnik: winners were right, juries crossed)
SWAP_JURIES = [("kresnik-2025", "kresnik-2026")]

# entity merges: (old id, kept id, alias to record)
ENTITY_MERGE = [("jaro-novak", "jaroslav-novak", "Jaro Novak")]

# entities to create: id -> name, type
NEW_ENTITIES = {
    "karin-sabadin": ("Karin Sabadin", "person"),
    "marjeta-drobnic": ("Marjeta Drobnič", "person"),
    "marjan-kovacevic-beltram": ("Marjan Kovačevič Beltram", "person"),
    "marjan-bocevski": ("Marjan Bocevski", "person"),
    "andreja-borin": ("Andreja Borin", "person"),
}
NEW_NOTE = "added from duplicate-editions review 2026-11-01; not enriched"

# edition -> {"winners": [...], "jury": [...] (replaces the jury), "note": ...}
SET_ROLES = {
    "grumova-nagrada-1986": {"winners": ["dane-zajc"], "note": "Dane Zajc, Kalevala"},
    "lastovka-2018": {
        "winners": ["karin-sabadin"],
        "jury": ["marjeta-drobnic", "veronika-simoniti", "marjan-kovacevic-beltram"],
        "note": "jury was a copy of lastovka-2023; 1st prize Karin Sabadin, Srečanja",
    },
    "kosobrin-2026": {"winners": ["marjan-bocevski"],
                      "note": "Marjan Bocevski (AI overview, unverified); DSR board kept as jury like other years"},
    "nagrada-kristine-brenkove-2025": {
        "winners": ["andreja-borin", "ana-zavadlav", "maja-p-kastelic"],
        "note": "Borin & Zavadlav, Pesmice za najmanjši žep; Nove poti: Maja P. Kastelic, Povabilo; jury matches",
    },
    "najboljsi-esej-2026": {"winners": ["nara-petrovic"],
                            "note": "Nara Petrovič, Med humanizmom in psihopatijo; jury matches"},
}

# editions confirmed as not awarded: keep (the jury sat), log only
NOT_AWARDED = {"grumova-nagrada-1997": "nagrada ni bila podeljena; jury confirmed"}


# --- io --------------------------------------------------------------------

def read(table):
    with open(DATA / f"{table}.csv", encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), list(r)


def write(table, fields, rows):
    with open(DATA / f"{table}.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    t = {name: read(name) for name in
         ("editions", "roles", "entities", "aliases", "entity_locations",
          "entity_offices", "entity_sources", "awards")}
    editions = t["editions"][1]
    roles = t["roles"][1]
    log = []

    def ed(eid):
        return next((e for e in editions if e["edition_id"] == eid), None)

    def note(eid, action, target="", detail="", source=REVIEW):
        log.append({"edition_id": eid, "action": action, "target": target,
                    "detail": detail, "source": source})

    def drop_edition(eid):
        editions[:] = [e for e in editions if e["edition_id"] != eid]
        roles[:] = [r for r in roles if r["edition_id"] != eid]

    def add_role(eid, ent, role):
        if any(r["edition_id"] == eid and r["entity_id"] == ent and r["role"] == role for r in roles):
            return
        n = sum(r["edition_id"] == eid and r["role"] == role for r in roles)
        roles.append({"edition_id": eid, "entity_id": ent, "role": role, "ord": str(n + 1)})

    # entities first, so merged editions dedupe on the kept id
    ent_fields, entities = t["entities"]
    for eid, (name, typ) in NEW_ENTITIES.items():
        if not any(e["entity_id"] == eid for e in entities):
            entities.append({**dict.fromkeys(ent_fields, ""), "entity_id": eid, "name": name,
                             "entity_type": typ, "note": NEW_NOTE})
            note("", "new-entity", eid, name)
    for old, keep, alias in ENTITY_MERGE:
        if not any(e["entity_id"] == old for e in entities):
            continue
        for r in roles:
            if r["entity_id"] == old:
                r["entity_id"] = keep
        for name in ("entity_locations", "entity_offices", "entity_sources", "aliases"):
            t[name] = (t[name][0], [r for r in t[name][1] if r["entity_id"] != old])
        t["aliases"][1].append({"alias": alias, "entity_id": keep})
        entities[:] = [e for e in entities if e["entity_id"] != old]
        note("", "merge-entity", keep, f"{old} -> {keep}; alias {alias!r}")

    # Drops name ids as they were before SHIFT_SERIES. Once a series is shifted, its ids
    # point at other editions (zlata-ptica-2013 is then the real 2012 edition), so skip.
    shifted = {a for a, (first, _) in SHIFT_SERIES.items() if ed(f"{a}-{first}") is None}
    for eid, why in DROP.items():
        if ed(eid) and ed(eid)["award_id"] not in shifted:
            drop_edition(eid)
            note(eid, "drop", detail=why)

    for src, dst in MERGE:
        if not (ed(src) and ed(dst)):
            continue
        for role in ("winner", "jury"):
            for r in sorted((r for r in roles if r["edition_id"] == src and r["role"] == role),
                            key=lambda r: int(r["ord"])):
                add_role(dst, r["entity_id"], role)
        if any(r["edition_id"] == dst and r["role"] == "jury" for r in roles):
            ed(dst)["jury_known"] = "True"
        drop_edition(src)
        note(src, "merge", dst)

    for old, (new, year) in MOVE.items():
        e = ed(old)
        if not e:
            continue
        e["edition_id"], e["year"] = new, str(year)
        for r in roles:
            if r["edition_id"] == old:
                r["edition_id"] = new
        note(old, "move", new, source=f"{REVIEW}; {SEARCH}")

    for award, (first, k) in SHIFT_SERIES.items():
        if ed(f"{award}-{first}") is None:  # already shifted
            continue
        series = sorted((e for e in editions if e["award_id"] == award),
                        key=lambda e: int(e["year"]), reverse=k > 0)
        for e in series:
            old = e["edition_id"]
            new = old.replace(f"-{e['year']}", f"-{int(e['year']) + k}", 1)
            assert ed(new) is None or new in {x["edition_id"] for x in series}
            e["edition_id"], e["year"] = new, str(int(e["year"]) + k)
            for r in roles:
                if r["edition_id"] == old:
                    r["edition_id"] = new
            note(old, "move", new, "relabel to ceremony year", source=SHIFT_SOURCE)

    for award, f, v, source in SET_AWARD:
        a = next(a for a in t["awards"][1] if a["award_id"] == award)
        if a[f] != v:
            note("", "set-award", award, f"{f}: {a[f]} -> {v}", source=source or SHIFT_SOURCE)
            a[f] = v

    off_fields, offices = t["entity_offices"]
    for ent, text in DELETE_OFFICES:
        hit = [o for o in offices if o["entity_id"] == ent and text in o["text"]]
        for o in hit:
            offices.remove(o)
            note("", "delete-office", ent, o["text"], source=PARTY_REVIEW)
    for ent in {e for e, _ in DELETE_OFFICES}:  # renumber ord per (entity, kind)
        for kind in ("office", "membership"):
            for i, o in enumerate((o for o in offices if o["entity_id"] == ent and o["kind"] == kind), 1):
                o["ord"] = str(i)

    for a, b in SWAP_JURIES:
        if not (ed(a) and ed(b)):
            continue
        ja = {r["entity_id"] for r in roles if r["edition_id"] == a and r["role"] == "jury"}
        jb = {r["entity_id"] for r in roles if r["edition_id"] == b and r["role"] == "jury"}
        if "igor-zunkovic" in ja:  # already swapped
            continue
        for r in roles:
            if r["role"] == "jury" and r["edition_id"] in (a, b):
                r["edition_id"] = b if r["edition_id"] == a else a
        note(a, "swap-jury", b, f"{sorted(ja ^ jb)}", source=f"{REVIEW}; {SEARCH}")

    for eid, spec in SET_ROLES.items():
        e = ed(eid)
        if not e:
            continue
        if "jury" in spec:
            roles[:] = [r for r in roles if not (r["edition_id"] == eid and r["role"] == "jury")]
            for ent in spec["jury"]:
                add_role(eid, ent, "jury")
            e["jury_known"] = "True"
        for ent in spec.get("winners", []):
            add_role(eid, ent, "winner")
        note(eid, "set-roles", detail=spec["note"], source=SEARCH)

    for eid, why in NOT_AWARDED.items():
        if ed(eid):
            note(eid, "not-awarded", detail=why, source=SEARCH)

    order = {r["edition_id"]: i for i, r in enumerate(sorted(editions, key=lambda e: e["edition_id"]))}
    editions.sort(key=lambda e: e["edition_id"])
    roles.sort(key=lambda r: (order.get(r["edition_id"], -1), r["role"] != "winner", int(r["ord"])))
    t["aliases"][1].sort(key=lambda r: r["alias"])
    for name, (fields, rows) in t.items():
        write(name, fields, rows)

    if LOG.exists():
        with open(LOG, encoding="utf-8", newline="") as fh:
            seen = {tuple(r.values()) for r in csv.DictReader(fh)}
        log = [r for r in log if tuple(r.values()) not in seen]
    if log:
        new = not LOG.exists()
        with open(LOG, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(log[0]), lineterminator="\n")
            if new:
                w.writeheader()
            w.writerows(log)
    print(f"{len(log)} changes applied; log: {LOG.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
