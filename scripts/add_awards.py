"""Add awards that were not in the legacy data, from sources listed per edition.

Each award is listed below as data; applying appends a row to
data/meta/edition_decisions.csv (action `add-award` / `add-edition`). Awards,
editions and entities that already exist are left alone, so re-running is harmless.

Conventions: one edition per ceremony year with every category in it (as for
Borštnikovo srečanje); productions credited to a whole team are a `work` entity;
special mentions (posebne omembe) are not wins and are left out; new entities are
not enriched (no gender or birth year).

    uv run python scripts/add_awards.py
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
LOG = DATA / "meta" / "edition_decisions.csv"
NEW_NOTE = "added with a new award 2026-11-01; not enriched"

AWARDS = {
    "zlata-strela": {
        "name": "Zlata strela", "genre": "gledališče", "prestige": "2",
        "institution": "Zavod Bunker (Stara mestna elektrarna)",
        "funding_source": "mixed", "funding_confidence": "low",
        "founded": "2024", "ended": "",
        "description": (
            "Zlata strela je nagrada Zavoda Bunker za najbolj izstopajoče dogodke, dosežke "
            "in ustvarjalce minule sezone v Stari mestni elektrarni v Ljubljani. Uvedli so jo "
            "leta 2024 ob 20-letnici prizorišča. Podeljujejo jo konec avgusta na festivalu "
            "Mladi levi. Petčlanska strokovna žirija si ogleda vse dogodke sezone in sama "
            "določi kategorije in število nagrad, na primer za potencial, za dolgoživost in "
            "za presežno stvaritev sezone."),
        "editions": {
            2024: {
                "source": "https://www.aplavz.art/post/zlate-strele (3. 9. 2024); rtvslo 719616",
                "winners": [
                    # najbolj izstopajoč dogodek sezone: ustvarjalna ekipa koncerta (zavod Sploh)
                    "zdej-loh-spokam-zdej-loh-grem",
                    "gregor-kamnikar",      # delo z občinstvom (Časni plesi, Druge kože)
                    "catherine-malabou",    # filozofsko predavanje Klitoris je anarhistka
                    "ida-hirsenfelder",     # zvočna krajina v predstavi Za-mišljen
                    "marjeta-pogacnik",     # posebna: predanost Stari elektrarni
                    "roman-jesenko",        # posebna: dolgoletno sodelovanje in podpora
                ],
                "jury": ["tjasa-crnigoj", "suzana-koncut", "gregor-butala", "mojca-jug",
                         "spela-kopitar"],
            },
            2025: {
                "source": ("https://www.aplavz.art/post/zlate-strele-v-sezoni-2024-2025; "
                           "rtvslo 755941 (ceremony 28. 8. 2025)"),
                "winners": [  # za presežno stvaritev
                    "klemen-kovacic",       # Agmisterij (z ekipo)
                    "medvedek-mraz",        # Bunker, Asociacija, Glej, Plesni Teater Ljubljana
                    "maja-delak",           # Izrekanja (z ekipo)
                ],
                "jury": ["mateja-bucar", "klara-drnovsek-solina", "spela-kopitar",
                         "katarina-stegnar", "benjamin-zajc"],
            },
            2026: {
                "source": ("https://www.aplavz.art/post/zlate-strele-v-sezoni-2025-2026; "
                           "https://www.aplavz.art/post/zlate-strele-2025-2026-orakelj-je-"
                           "spregovoril-pot-v-prihodnost-tlakovana-z-zlatom (ceremony 29. 8. 2026)"),
                "winners": [
                    "leon-maric",           # za potencial: Kvir kot vsi drugi
                    "pia-macerol",          # za potencial: Izbrano telo 2
                    "natasa-zivkovic",      # za dolgoživost: Sine (she also sat on the jury)
                    "beton-ltd",            # za dolgoživost: Vse, kar smo izgubili, ...
                    "rok-kravanja",         # sezona: Slovenska transverzala
                    "barbara-kukovec",      # sezona: Umetnost življenja: Umor na podeželju
                    "katarina-stegnar",
                    "urska-brodar",
                ],
                "jury": ["natasa-zivkovic", "blaz-sef", "zala-dobovsek", "spela-kopitar",
                         "maja-vizin"],
            },
        },
    },
}

NEW_ENTITIES = {
    "zdej-loh-spokam-zdej-loh-grem": ("Zdej loh spokam zdej loh grem", "work"),
    "mojca-jug": ("Mojca Jug", "person"),
    "spela-kopitar": ("Špela Kopitar", "person"),
    "catherine-malabou": ("Catherine Malabou", "person"),
    "ida-hirsenfelder": ("Ida Hiršenfelder", "person"),
    "marjeta-pogacnik": ("Marjeta Pogačnik", "person"),
    "roman-jesenko": ("Roman Jesenko", "person"),
    "klara-drnovsek-solina": ("Klara Drnovšek Solina", "person"),
    "benjamin-zajc": ("Benjamin Zajc", "person"),
    "medvedek-mraz": ("Medvedek Mraz", "work"),
    "leon-maric": ("Leon Marič", "person"),
    "pia-macerol": ("Pia Mačerol", "person"),
    "beton-ltd": ("Beton Ltd.", "group"),
    "maja-vizin": ("Maja Vižin", "person"),
}


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
    t = {n: read(n) for n in ("awards", "editions", "roles", "entities")}
    log = []

    def note(eid, action, target, detail, source):
        log.append({"edition_id": eid, "action": action, "target": target,
                    "detail": detail, "source": source})

    ent_fields, entities = t["entities"]
    have = {e["entity_id"] for e in entities}
    for eid, (name, typ) in NEW_ENTITIES.items():
        if eid not in have:
            entities.append({**dict.fromkeys(ent_fields, ""), "entity_id": eid, "name": name,
                             "entity_type": typ, "note": NEW_NOTE})
            note("", "new-entity", eid, name, "scripts/add_awards.py")
            have.add(eid)

    a_fields, awards = t["awards"]
    e_fields, editions = t["editions"]
    roles = t["roles"][1]
    for aid, spec in AWARDS.items():
        if not any(a["award_id"] == aid for a in awards):
            awards.append({"award_id": aid, **{k: v for k, v in spec.items() if k != "editions"}})
            note("", "add-award", aid, spec["name"], "scripts/add_awards.py")
        for year, ed in spec["editions"].items():
            eid = f"{aid}-{year}"
            if any(e["edition_id"] == eid for e in editions):
                continue
            missing = [x for x in ed["winners"] + ed["jury"] if x not in have]
            assert not missing, f"{eid}: unknown entities {missing}"
            editions.append({"edition_id": eid, "award_id": aid, "year": str(year),
                             "category": "", "jury_known": str(bool(ed["jury"])),
                             "source": ed["source"]})
            for role, ids in (("winner", ed["winners"]), ("jury", ed["jury"])):
                roles += [{"edition_id": eid, "entity_id": x, "role": role, "ord": str(i)}
                          for i, x in enumerate(ids, 1)]
            note(eid, "add-edition", aid,
                 f"{len(ed['winners'])} winners, {len(ed['jury'])} jurors", ed["source"])

    awards.sort(key=lambda a: a["award_id"])
    order = {e: i for i, e in enumerate(sorted(e["edition_id"] for e in editions))}
    editions.sort(key=lambda e: e["edition_id"])
    roles.sort(key=lambda r: (order[r["edition_id"]], r["role"] != "winner", int(r["ord"])))
    for name, (fields, rows) in t.items():
        write(name, fields, rows)

    if log:
        with open(LOG, "a", encoding="utf-8", newline="") as fh:
            csv.DictWriter(fh, fieldnames=list(log[0]), lineterminator="\n").writerows(log)
    print(f"{len(log)} changes applied; log: {LOG.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
