#!/usr/bin/env python3
"""One-time migration from the legacy research codebase to the normalized dataset.

Reads the legacy project (default: ../test/nagrade) and writes the tables described
in docs/data-model.md to data/, plus review lists to docs/review/.

    uv run python scripts/migrate_legacy.py [--legacy PATH]

After the migration, the files in data/ are the source of truth. The script is kept
for provenance and for re-running if the migration logic changes, but re-running
overwrites any manual edits made to data/ since.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REVIEW = ROOT / "docs" / "review"

# --- Entity classification ---------------------------------------------------
# Legacy data had only person/group. Non-persons are split further:
#   group       ensembles and collectives of performers/artists (bands, choirs, art collectives)
#   work        a film, TV series or song credited as the winner
#   institution an organisation or legal body (bureau, society, theatre, festival, office)
# Works are mostly detected from the legacy note ("naslov ..."); the rest are listed here.
WORKS = {
    "Jezero", "Kapa", "Radio Ga Ga", "Pr' Hostar", "Poklicani", "Stekleničarji",
    "Zelena generacija", "Praslovan", "Dedek gre na jug", "Fiume o Morte!",
    "športni film ob 60-letnici NK Maribor",
}
INSTITUTIONS = {
    "a2o2 arhitekti", "ATELIER arhitekti", "Bax Studio", "DANS ARHITEKTI",
    "Ravnikar Potokar arhitekturni biro", "Dveri Pax", "Festival Sajeta",
    "Dramaturški oddelek PG Kranj", "Dramaturški oddelek SMG Ljubljana",
    "Gledališko združenje KOROŠKI DEŽELNI TEATER", "Kulturno društvo ODSEVANJA",
    "Kulturno društvo Slovenj Gradec", "Kulturno društvo Stari trg",
    "Kulturno društvo Šmartno", "Kulturno umetniško društvo Mreža",
    "Mednarodni filmski festival kratkih filmov SHOTS", "Moment collective",
    "Moment Maribor", "Pekarna magdalenske mreže", "program Ars",
    "Strokovna komisija ZAPS", "Studia Slovenica Archives Research Institute",
    "Urad za kulturo in mladino MO Maribor", "PG", "SMG", "Socialni center Rog",
    "ZIZ Collective", "Banda ferdamani",
}
# Names the legacy classification left as `person` but which are clearly not people.
EXTRA_INSTITUTIONS = {
    "MGL", "Arhitekturni Atelje Medprostor", "Asociacija", "Bevk Perović",
    "Center in galerija P74", "Center za konserviranje in restavriranje",
    "Digitalna knjižnica Slovenije", "Domovina (medijski projekt)",
    "Društvo slovenskih pisateljev", "Društvo za razvoj socialnih programov",
    "Hiša kulture Celje", "Inštitut za slovensko literaturo in literarne vede ZRC SAZU",
    "Kamra", "Kino Otok", "Kino Udarnik", "Ljubljanska Drama", "Ljudmila", "Mak fest",
    "Mercator", "Mestna občina Celje", "Mini Teater Ljubljana", "Novo kazalište Zagreb",
    "Planet TV", "PreGlej", "Republika Slovenija", "SNG NG", "Sadar+Vuga",
    "Slovenska matica", "Slovenski narodopisni inštitut Urban Jarnik", "Stripburger",
    "Tribuna", "Zavod Trajekt", "društvo Prostorož",
}
EXTRA_GROUPS = {
    "Beli sladoled", "Cirkulacija 2", "Delavska Godba Iz Trbovelj", "Eclipse", "EkstraVisor",
    "EnKnapGroup", "Fritt Vilt", "Godalni Kvartet Tartini", "Grupa Ee", "Irwin",
    "Kolektiv Narobov", "Komorni Godalni Orkester Slovenske Filharmonije", "Komorni Zbor Ave",
    "Liferanti", "Melodrom", "Mladinski Pevski Zbor Iz Maribora", "Odprti krog",
    "Partizanski Invalidski Pevski Zbor", "Slovenski Oktet", "Slovenski tolkalni projekt",
    "Slowind", "The Stroj", "Trio Lorenz", "skupina Kaverljag",
    "skupina Nonument / Nonument group",
}

# Legacy merges whose canonical form was the wrong one: wrong -> right.
REVERSED_MERGES = {"Matjaža Berger": "Matjaž Berger"}  # genitive case

# Cell-level fixes applied before alias resolution: name -> replacement names.
NAME_FIXES = {
    # Two people joined with "in" in one cell.
    "Jože Ciuha in Janez Lenassi": ["Jože Ciuha", "Janez Lenassi"],
    "Petra Vidali in Kaja bucik Vavpetič": ["Petra Vidali", "Kaja Bucik Vavpetič"],
    # Hudi maček 2006/2007: the Young Hudi maček winner was glued onto a juror's name.
    "Aleš BlatnikYoung Hudi maček: Aleksandar Radivojević": ["Aleš Blatnik"],
    "Gorazd TrušnovecYoung Hudi maček: Aleksandar Radivojević": ["Gorazd Trušnovec"],
    # Genitive case copied from a sentence ("prevod Branka Madžareviča").
    "Branka Madžareviča": ["Branko Madžarevič"],
}


def slugify(text: str) -> str:
    text = text.replace("ß", "ss").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def split_names(cell: str) -> list[str]:
    names = [n for n in (clean_name(x) for x in cell.split(",")) if n]
    return [fixed for n in names for fixed in NAME_FIXES.get(n, [n])]


def read_csv(path: Path, delimiter: str = ";") -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r[k]) for k in fields})
    print(f"  {path.relative_to(ROOT)}: {len(rows)} rows")


def unique_slug(base: str, taken: set[str]) -> str:
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    taken.add(slug)
    return slug


def load_corrections(legacy: Path) -> dict[str, str]:
    raw = json.loads((legacy / "data/corrections/potential_duplicates.json").read_text())
    mapping = {clean_name(s): clean_name(e["target"]) for e in raw for s in e["sources"]}
    for src, target in list(mapping.items()):
        if target in NAME_FIXES:  # merged into a joined cell that is now split: undo
            del mapping[src]
        elif target in REVERSED_MERGES:  # merged in the wrong direction
            mapping[src] = REVERSED_MERGES[target]
    for wrong, right in REVERSED_MERGES.items():
        mapping.pop(right, None)
        mapping[wrong] = right
    # Resolve chains (a -> b -> c) so every alias points at the final canonical name.
    def resolve(n: str, seen: tuple = ()) -> str:
        t = mapping.get(n)
        return n if t is None or t in seen else resolve(t, seen + (n,))
    return {s: resolve(s) for s in mapping}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legacy", type=Path, default=ROOT.parent / "test" / "nagrade")
    legacy = ap.parse_args().legacy.resolve()
    ld = legacy / "data"
    print(f"Migrating from {legacy}")

    corrections = load_corrections(legacy)
    canon = lambda n: corrections.get(clean_name(n), clean_name(n))

    # --- awards ---------------------------------------------------------------
    legacy_awards = read_csv(ld / "reference/awards.csv")
    site = {a["title"]: a for a in json.loads((ld / "website/awards.json").read_text())["awards"]}
    award_ids: dict[str, str] = {}
    taken: set[str] = set()
    awards = []
    for a in sorted(legacy_awards, key=lambda a: slugify(a["award_name"])):
        name = clean_name(a["award_name"])
        aid = unique_slug(slugify(name), taken)
        award_ids[name] = aid
        s = site.get(name, {})
        awards.append({
            "award_id": aid, "name": name, "genre": a["genre"],
            "prestige": int(a["prestige"]), "institution": a["institution"],
            "funding_source": a["funding_source"], "funding_confidence": a["funding_confidence"],
            "founded": s.get("founded"), "ended": s.get("ended"),
            "description": s.get("description"),
        })
    missing_site = [a["name"] for a in awards if a["name"] not in site]

    # --- editions + roles -----------------------------------------------------
    legacy_rows = []
    with open(ld / "zirije_plus_nagrajenci.csv", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for lineno, row in enumerate(reader, start=2):
            year, award, jury, winners = row
            legacy_rows.append({
                "line": lineno, "year": int(year), "award": clean_name(award),
                "jury": [canon(n) for n in split_names(jury)],
                "winners": [canon(n) for n in split_names(winners)],
                "jury_raw": jury, "winners_raw": winners,
            })

    edition_taken: set[str] = set()
    editions, role_rows = [], []
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for r in sorted(legacy_rows, key=lambda r: (award_ids[r["award"]], r["year"], r["line"])):
        aid = award_ids[r["award"]]
        eid = unique_slug(f"{aid}-{r['year']}", edition_taken)
        r["edition_id"] = eid
        by_key[(aid, r["year"])].append(r)
        editions.append({
            "edition_id": eid, "award_id": aid, "year": r["year"], "category": None,
            "jury_known": bool(r["jury"]), "source": None,
        })
        for role, names in (("winner", r["winners"]), ("jury", r["jury"])):
            seen = set()
            for i, n in enumerate(names, start=1):
                if n in seen:  # same name listed twice in one cell
                    continue
                seen.add(n)
                role_rows.append({"edition_id": eid, "name": n, "role": role, "ord": i})

    # --- commissions ------------------------------------------------------------
    commission_rows, unknown_commission_awards, seen_seats = [], set(), set()
    for path in sorted((ld / "commissions").glob("*.csv")):
        for c in read_csv(path):
            award = clean_name(c["award"])
            if award not in award_ids:
                unknown_commission_awards.add(award)
                continue
            for n in split_names(c["members"]):
                key = (award_ids[award], canon(n), int(c["from"]))
                # Prešernov_sklad.csv duplicates Prešernova_nagrada.csv (one board, the
                # Upravni odbor Prešernovega sklada, appoints both juries): keep one copy.
                if key in seen_seats:
                    continue
                seen_seats.add(key)
                commission_rows.append({
                    "award_id": award_ids[award], "name": canon(n),
                    "year_from": int(c["from"]), "year_to": int(c["to"]),
                })

    # --- entities -----------------------------------------------------------------
    enrichment = {clean_name(e["name"]): e
                  for e in json.loads((ld / "enrichment/enrichment_dated.json").read_text())}
    types = {clean_name(r["name"]): r for r in read_csv(ld / "reference/entity_types.csv")}
    reports = {k: json.loads((ld / f"enrichment/{k}_report.json").read_text())
               for k in ("wikidata", "viaf", "llm")}

    used_names = sorted({r["name"] for r in role_rows} | {c["name"] for c in commission_rows})
    entity_ids: dict[str, str] = {}
    ent_taken: set[str] = set()
    slug_collisions = defaultdict(list)
    for n in used_names:
        slug_collisions[slugify(n)].append(n)
        entity_ids[n] = unique_slug(slugify(n), ent_taken)

    def entity_type(n: str, e: dict | None) -> str:
        if n in WORKS:
            return "work"
        if n in INSTITUTIONS or n in EXTRA_INSTITUTIONS:
            return "institution"
        if n in EXTRA_GROUPS:
            return "group"
        t = types.get(n, {})
        legacy_type = t.get("entity_type") or (e or {}).get("entity_type") or "person"
        if legacy_type == "group":
            return "work" if "naslov" in (t.get("note") or "").lower() else "group"
        return "person"

    def birth_source(n: str, e: dict) -> str | None:
        if e.get("year_birth") is None:
            return None
        for k in ("wikidata", "viaf", "llm"):  # the legacy passes ran in this order
            if reports[k].get(n, {}).get("status") == "matched":
                return k
        return "enrichment"

    entities, locations, offices, sources = [], [], [], []
    not_enriched = []
    for n in used_names:
        eid, e = entity_ids[n], enrichment.get(n)
        if e is None:  # enriched under a variant spelling that now points here
            e = next((enrichment[a] for a, t in corrections.items()
                      if t == n and a in enrichment), None)
        etype = entity_type(n, e)
        if e is None and etype == "person":
            not_enriched.append(n)
        e = dict(e or {})
        # Legacy record with age and birth year swapped (year_birth=50, age=1976).
        if (e.get("year_birth") or 1900) < 1800 and (e.get("age") or 0) > 1800:
            e["year_birth"] = e["age"]
        is_person = etype == "person"
        entities.append({
            "entity_id": eid, "name": n, "entity_type": etype,
            "gender": e.get("gender") if is_person else None,
            "year_birth": e.get("year_birth") if is_person else None,
            "year_birth_source": birth_source(n, e) if is_person else None,
            "year_birth_estimate": e.get("year_birth_est") if is_person else None,
            "year_death": e.get("year_death") if is_person else None,
            "enrichment_confidence": e.get("confidence"),
            "note": None if is_person else (types.get(n, {}).get("note") or None),
        })
        for i, place in enumerate(e.get("locations") or [], start=1):
            locations.append({"entity_id": eid, "ord": i, "place": clean_name(place)})
        for kind, key in (("office", "public_offices"), ("membership", "memberships")):
            for i, text in enumerate(e.get(key) or [], start=1):
                offices.append({"entity_id": eid, "kind": kind, "ord": i, "text": clean_name(text)})
        domains = []
        for s in e.get("sources") or []:
            # Grounding URLs are expiring redirects; keep the title, which is the domain.
            d = (s.get("title") or urlparse(s.get("url", "")).netloc or "").strip().lower()
            if d and d not in domains:
                domains.append(d)
        sources += [{"entity_id": eid, "source": d} for d in domains]

    roles = [{"edition_id": r["edition_id"], "entity_id": entity_ids[r["name"]],
              "role": r["role"], "ord": r["ord"]} for r in role_rows]
    commissions = [{"award_id": c["award_id"], "entity_id": entity_ids[c["name"]],
                    "year_from": c["year_from"], "year_to": c["year_to"]}
                   for c in commission_rows]

    aliases = sorted(
        ({"alias": a, "entity_id": entity_ids[t]} for a, t in corrections.items() if t in entity_ids),
        key=lambda r: r["alias"],
    )
    rejected = json.loads((ld / "corrections/rejected_duplicates.json").read_text())
    not_duplicates = [{"name_a": a, "name_b": b,
                       "entity_id_a": entity_ids.get(canon(a)), "entity_id_b": entity_ids.get(canon(b))}
                      for a, b in rejected]

    # --- write ----------------------------------------------------------------------
    print("Writing tables:")
    write_csv(DATA / "awards.csv", ["award_id", "name", "genre", "prestige", "institution",
              "funding_source", "funding_confidence", "founded", "ended", "description"], awards)
    write_csv(DATA / "editions.csv", ["edition_id", "award_id", "year", "category",
              "jury_known", "source"], editions)
    write_csv(DATA / "entities.csv", ["entity_id", "name", "entity_type", "gender", "year_birth",
              "year_birth_source", "year_birth_estimate", "year_death",
              "enrichment_confidence", "note"], entities)
    write_csv(DATA / "roles.csv", ["edition_id", "entity_id", "role", "ord"], roles)
    write_csv(DATA / "commissions.csv", ["award_id", "entity_id", "year_from", "year_to"], commissions)
    write_csv(DATA / "aliases.csv", ["alias", "entity_id"], aliases)
    write_csv(DATA / "entity_locations.csv", ["entity_id", "ord", "place"], locations)
    write_csv(DATA / "entity_offices.csv", ["entity_id", "kind", "ord", "text"], offices)
    write_csv(DATA / "entity_sources.csv", ["entity_id", "source"], sources)
    write_csv(DATA / "meta" / "not_duplicates.csv",
              ["name_a", "name_b", "entity_id_a", "entity_id_b"], not_duplicates)

    collisions = [v for v in slug_collisions.values() if len(v) > 1]
    write_review(by_key, award_ids, editions, roles, entities, enrichment, entity_ids, collisions)

    print("\nChecks:")
    print(f"  entity types: {dict(Counter(e['entity_type'] for e in entities))}")
    print(f"  persons without enrichment record: {len(not_enriched)}", not_enriched[:15])
    print(f"  awards without website description: {missing_site}")
    print(f"  commission awards not in awards.csv: {sorted(unknown_commission_awards)}")
    print(f"  slug collisions (diacritic variants): {collisions}")


def write_review(by_key, award_ids, editions, roles, entities, enrichment, entity_ids,
                 collisions) -> None:
    names = {a: n for n, a in award_ids.items()}
    ent_name = {e["entity_id"]: e["name"] for e in entities}
    winners = defaultdict(list)
    for r in roles:
        if r["role"] == "winner":
            winners[r["edition_id"]].append(ent_name[r["entity_id"]])

    lines = [
        "# Review: duplicate award-year rows",
        "",
        "The legacy CSV has more than one row for these (award, year) pairs. The migration",
        "kept every row as its own edition (`-2`, `-3` suffixes). For each group, decide:",
        "",
        "- **keep**: they are real separate editions or categories (add `category` if known)",
        "- **merge**: the same edition split across rows (combine the winners, dedupe the jury)",
        "- **move**: a row belongs to a different year (give the correct year)",
        "- **drop**: an erroneous duplicate",
        "",
        "Lines refer to `data/zirije_plus_nagrajenci.csv` in the legacy project.",
        "",
    ]
    groups = [(k, rows) for k, rows in sorted(by_key.items()) if len(rows) > 1]
    for (aid, year), rows in groups:
        juries = {tuple(sorted(r["jury"])) for r in rows}
        hint = "same jury" if len(juries) == 1 else "different juries"
        if len({tuple(sorted(r["winners"])) for r in rows}) == 1:
            hint += ", identical winners (likely exact duplicate)"
        lines += [f"## {names[aid]} {year}  ({hint})", "",
                  "| edition_id | legacy line | winners | jury |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| `{r['edition_id']}` | {r['line']} | {', '.join(r['winners']) or '—'} "
                         f"| {', '.join(r['jury']) or '—'} |")
        lines += ["", "Decision: ", ""]
    lines.insert(2, f"{len(groups)} groups, {sum(len(r) for _, r in groups)} rows.\n")

    no_winner = [e for e in editions if not winners[e["edition_id"]]]
    lines += ["# Editions with no winners", "",
              "These rows had an empty winners cell. Fill in the winners or drop the edition.", ""]
    lines += [f"- `{e['edition_id']}`" for e in no_winner]

    REVIEW.mkdir(parents=True, exist_ok=True)
    (REVIEW / "duplicate-editions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  docs/review/duplicate-editions.md: {len(groups)} groups, {len(no_winner)} empty")

    # The legacy enrichment sometimes resolved a fuller or corrected name. Not applied
    # automatically: some are genuine fixes, others are a different person.
    resolved = sorted((n, enrichment[n]["resolved_name"]) for n in entity_ids
                      if n in enrichment and enrichment[n].get("resolved_name")
                      and clean_name(enrichment[n]["resolved_name"]) != n)
    out = ["# Review: names the enrichment resolved differently", "",
           "During enrichment, the search model sometimes identified a person under a",
           "different name. Typo fixes (Kocmu → Kocmut) should be applied as a rename",
           "plus an alias. Fuller names (added middle name or second surname) are optional.",
           "A different person means the enrichment data for that entity is wrong.", "",
           "| entity_id | name in data | resolved name | decision |", "|---|---|---|---|"]
    out += [f"| `{entity_ids[a]}` | {a} | {b} | |" for a, b in resolved]
    out += ["", "## Diacritic variants", "",
            "These names differ only in diacritics and are almost certainly the same person.",
            "Pick the correct spelling; the other becomes an alias.", "",
            "| entity_ids | spellings | correct spelling |", "|---|---|---|"]
    out += [f"| {', '.join(f'`{entity_ids[n]}`' for n in v)} | {' / '.join(v)} | |" for v in collisions]
    (REVIEW / "resolved-names.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  docs/review/resolved-names.md: {len(resolved)} names")


if __name__ == "__main__":
    main()
