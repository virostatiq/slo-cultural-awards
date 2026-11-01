"""Apply the decisions from docs/review/resolved-names.md to data/*.csv.

The decision column of the review file drives the per-row actions:

    **rename** [to X] [, id `y`]   name := X (default: resolved name); old name -> alias
    **alias** / **keep**: nickname  add the resolved name as an alias
    **group** / **institution**     fix entity_type, clear person data (matched a member)
    **wrong-person**                clear enrichment (matched someone else)
    **gender f|m**                  set gender
    **merge** into `x`              merge the entity into x
    anything else                   no change

The diacritic pairs and id renames are listed below. Applying appends to
data/meta/name_decisions.csv; re-running is harmless.

    uv run python scripts/apply_name_decisions.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REVIEW = ROOT / "docs" / "review" / "resolved-names.md"
LOG = DATA / "meta" / "name_decisions.csv"

# (merged away, kept)
PAIR_MERGES = [
    ("alma-causevic-klemencic-2", "alma-causevic-klemencic"),
    ("bojan-labovic-2", "bojan-labovic"),
    ("jaroslav-skrusny", "jaroslav-skrusny-2"),
    # the resolved name already existed as its own entity (same birth year, same field)
    ("alessio-princic", "ales-princic"),
    ("koni-steinbaher", "konrad-steinbacher"),
    ("lili-prap", "lilijana-praprotnik-zupancic"),
    ("sandi-krosl", "aleksander-krosl"),
    ("tjasa-slokar", "tjasa-slokar-kos"),
    ("tugomir-susnik", "tugo-susnik"),
    ("emerik-bernard-b", "emerik-bernard"),
]
# ids that carried junk from the legacy names, applied last
ID_RENAMES = {
    "jaroslav-skrusny-2": "jaroslav-skrusny",
    "david-verbucthe": "david-verbuc",
}
CHILD = ("entity_locations", "entity_offices", "entity_sources")
REFS = ("roles", "aliases", *CHILD)
PERSON_FIELDS = ("gender", "year_birth", "year_birth_source", "year_birth_estimate", "year_death")
ENRICHMENT = ("gender", "year_birth", "year_birth_source", "year_death", "enrichment_confidence")


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r.fieldnames), list(r)


def write(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def review_rows():
    for line in REVIEW.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| `([^`]+)` \| (.+?) \| (.+?) \| (.*?) *\|$", line)
        if m:
            yield m.groups()


def main():
    t = {n: read(DATA / f"{n}.csv") for n in ("entities", *REFS)}
    nd_path = DATA / "meta" / "not_duplicates.csv"
    nd_fields, nd = read(nd_path)
    entities = t["entities"][1]
    log = []

    def ent(eid):
        return next((e for e in entities if e["entity_id"] == eid), None)

    def note(eid, action, detail=""):
        log.append({"entity_id": eid, "action": action, "detail": detail})

    def add_alias(alias, eid):
        aliases = t["aliases"][1]
        e = ent(eid)
        if not e or alias == e["name"]:
            return
        owner = next((a["entity_id"] for a in aliases if a["alias"] == alias), None)
        if owner == eid:
            return
        clash = owner or next((x["entity_id"] for x in entities if x["name"] == alias), None)
        if clash:
            note(eid, "alias-skipped", f"{alias!r} belongs to {clash}")
            return
        aliases.append({"alias": alias, "entity_id": eid})
        note(eid, "alias", alias)

    def drop_children(eid):
        for n in CHILD:
            t[n] = (t[n][0], [r for r in t[n][1] if r["entity_id"] != eid])

    def merge(old, keep):
        o, k = ent(old), ent(keep)
        if not (o and k):
            return
        roles = t["roles"][1]
        have = {(r["edition_id"], r["role"]) for r in roles if r["entity_id"] == keep}
        t["roles"] = (t["roles"][0], [r for r in roles if not (
            r["entity_id"] == old and (r["edition_id"], r["role"]) in have)])
        for n in ("roles", "aliases"):
            for r in t[n][1]:
                if r["entity_id"] == old:
                    r["entity_id"] = keep
        drop_children(old)
        entities.remove(o)
        add_alias(o["name"], keep)
        note(keep, "merge", f"{old} -> {keep}")

    def rename_id(old, new):
        e = ent(old)
        if not e:
            return
        if ent(new):
            note(old, "id-rename-skipped", f"{new} exists")
            return
        e["entity_id"] = new
        for n in REFS:
            for r in t[n][1]:
                if r["entity_id"] == old:
                    r["entity_id"] = new
        for r in nd:
            for c in ("entity_id_a", "entity_id_b"):
                if r[c] == old:
                    r[c] = new
        note(new, "id-rename", f"{old} -> {new}")

    for eid, name, resolved, d in review_rows():
        e = ent(eid)
        if not e:
            continue
        if d.startswith("**rename**"):
            m = re.match(r"\*\*rename\*\* to (.+?)(?: \(|,|;|$)", d)
            new = m.group(1).strip() if m else resolved
            if e["name"] != new:
                old = e["name"]
                e["name"] = new
                t["aliases"] = (t["aliases"][0], [a for a in t["aliases"][1]
                                                  if not (a["alias"] == new and a["entity_id"] == eid)])
                note(eid, "rename", f"{old} -> {new}")
                add_alias(old, eid)
            for extra in re.findall(r"alias ([^;|]+?)(?:;|$)", d):
                add_alias(extra.strip(), eid)
            m = re.search(r"id `([^`]+)`", d)
            if m:
                rename_id(eid, m.group(1))
        elif d.startswith(("**alias**", "**keep**: nickname", "**keep**: absorbs")):
            add_alias(resolved, eid)
        elif d.startswith(("**group**", "**institution**")):
            kind = "group" if d.startswith("**group**") else "institution"
            if e["entity_type"] != kind or any(e[f] for f in PERSON_FIELDS):
                e["entity_type"] = kind
                for f in PERSON_FIELDS + ("enrichment_confidence",):
                    e[f] = ""
                drop_children(eid)
                e["note"] = f"enrichment had matched a member ({resolved}); cleared"
                note(eid, kind, f"cleared person data matched to {resolved}")
        elif d.startswith("**wrong-person**"):
            if any(e[f] for f in ENRICHMENT):
                for f in ENRICHMENT:
                    e[f] = ""
                drop_children(eid)
                e["note"] = f"enrichment had matched {resolved}; cleared"
                note(eid, "wrong-person", f"cleared enrichment matched to {resolved}")
        elif m := re.match(r"\*\*gender ([mf])\*\*", d):
            if e["gender"] != m.group(1):
                e["gender"] = m.group(1)
                note(eid, "gender", m.group(1))
        elif m := re.match(r"\*\*merge\*\* into `([^`]+)`", d):
            merge(eid, m.group(1))

    for old, keep in PAIR_MERGES:
        merge(old, keep)
    for old, new in ID_RENAMES.items():
        rename_id(old, new)

    t["aliases"][1].sort(key=lambda r: r["alias"])
    for n, (fields, rows) in t.items():
        write(DATA / f"{n}.csv", fields, rows)
    write(nd_path, nd_fields, nd)

    if LOG.exists():
        seen = {tuple(r.values()) for r in read(LOG)[1]}
        log = [r for r in log if tuple(r.values()) not in seen]
    if log:
        new = not LOG.exists()
        with open(LOG, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["entity_id", "action", "detail"], lineterminator="\n")
            if new:
                w.writeheader()
            w.writerows(log)
    print(f"{len(log)} changes applied; log: {LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
