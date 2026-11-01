"""Export site-ready JSON for the Astro site (site/).

    uv run python -m kulturne_nagrade.site_export     # -> site/src/data/*.json, site/public/data/

All counting logic stays here (sittings, fields, roles, the graph); the site only
renders. Personal data shown on pages is deliberately limited:

- birth and death years with their source; automated sources (LLM, enrichment) are
  flagged so the page can say they may be wrong. The statistical birth-year estimate
  is never exported;
- no gender on individual pages (it is used only in aggregate statistics), no places,
  no offices, no automated biography notes; political affiliation is not in the data;
- `single` marks people with one appearance, whose pages are kept out of search
  engines (noindex) until the data is checked.
"""

from __future__ import annotations

import json
import math
import shutil
from collections import defaultdict

import pandas as pd

from kulturne_nagrade import PROJECT_ROOT, frames, graph
from kulturne_nagrade import plotting as P
from kulturne_nagrade.network_map import FIELD_COLOR, ROLE_COLOR

SITE = PROJECT_ROOT / "site"
DATA = SITE / "src" / "data"
PUBLIC = SITE / "public" / "data"
RESULTS = PROJECT_ROOT / "results"
AUTOMATED = {"llm", "enrichment"}
BG = "#171022"  # the site background (site/src/styles/global.css --bg)
SOURCE_LABEL = {"wikidata": "Wikidata", "viaf": "VIAF", "llm": "samodejno (jezikovni model)",
                "enrichment": "samodejno (spletni viri)"}


def _clean(x):
    """JSON-safe: NaN/NA -> None, numpy scalars -> Python."""
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if x is None or x is pd.NA:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    if hasattr(x, "item"):
        return _clean(x.item())
    return x


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")
    return path.stat().st_size


def _life(year, source):
    if pd.isna(year):
        return None
    return {"year": int(year), "source": SOURCE_LABEL.get(source, source) if source else None,
            "automated": (source in AUTOMATED) if source else True}


def build() -> dict:
    roles = frames.roles(entity_types=None)
    sit = frames.jury_sittings(entity_types=None)
    ent = frames.entities().set_index("entity_id")
    aw = frames.awards().set_index("award_id")
    ed = frames.editions()
    G = graph.build()
    sources = frames.table("entity_sources").groupby("entity_id")["source"].agg(list)

    # --- people ---------------------------------------------------------------------------
    people = {}
    wins = roles[roles["role"] == "winner"].sort_values(["year", "award"])
    by_person_w = {e: d for e, d in wins.groupby("entity_id")}
    by_person_s = {e: d for e, d in sit.sort_values(["year", "award"]).groupby("entity_id")}
    co, jin, jout = defaultdict(list), defaultdict(list), defaultdict(list)
    for u, v, d in G.edges(data=True):
        if d["kind"] == "co_jury":
            co[u].append([v, d["sittings"]])
            co[v].append([u, d["sittings"]])
        elif d["kind"] == "judged":
            jout[u].append([v, d["editions"]])
            jin[v].append([u, d["editions"]])
    srt = lambda L: sorted(L, key=lambda t: (-t[1], ent.loc[t[0], "name"]))
    pos = _map_positions()
    for e in set(roles["entity_id"]):
        r = ent.loc[e]
        w, s = by_person_w.get(e), by_person_s.get(e)
        nw, ns = (0 if w is None else len(w)), (0 if s is None else len(s))
        node = G.nodes[e]
        people[e] = {
            "id": e, "name": r["name"], "kind": r["entity_type"], "field": node["field"],
            "role": "both" if nw and ns else ("winner" if nw else "jury"),
            "birth": _life(r["year_birth"], r["year_birth_source"]),
            "death": _life(r["year_death"], r["year_birth_source"]),
            "wins": [] if w is None else [
                {"year": int(x.year), "award": x.award_id, "edition": x.edition_id,
                 "category": x.category if isinstance(x.category, str) else None}
                for x in w.itertuples()],
            "juries": [] if s is None else [
                {"year": int(x.year), "award": x.award_id, "awards": list(x.awards),
                 "edition": x.edition_id, "size": int(x.jury_size)} for x in s.itertuples()],
            "co": srt(co[e]), "judged_by": srt(jin[e]), "judged": srt(jout[e]),
            "first": node["first"], "last": node["last"],
            "pos": pos.get(e),
            "sources": sources.get(e, []),
            "single": nw + ns == 1,
        }

    # --- awards ---------------------------------------------------------------------------
    cov = frames.coverage()
    cov = cov.set_index("award_id") if "award_id" in cov.columns else cov
    res = lambda f: json.loads((RESULTS / f).read_text(encoding="utf-8"))
    insider = {r["award_id"]: r for r in res("juries.json")["insider_per_award"]}
    repeat_w = {r["award_id"]: r for r in res("awards.json")["repeat_winners_per_award"]}
    repeat_s = {r["award_id"]: r for r in res("power.json")["repeat_by_award"]}
    ages = {r["award_id"]: r for r in res("age.json")["by_award"]}
    gender = roles[roles["entity_type"] == "person"]
    awards = {}
    for a, r in aw.iterrows():
        eds = ed[ed["award_id"] == a].sort_values(["year", "edition_id"])
        rl = roles[roles["award_id"] == a]
        editions = []
        for x in eds.itertuples():
            d = rl[rl["edition_id"] == x.edition_id].sort_values("ord")
            editions.append({
                "id": x.edition_id, "year": int(x.year),
                "category": x.category if isinstance(x.category, str) else None,
                "winners": d.loc[d["role"] == "winner", "entity_id"].tolist(),
                "jury": d.loc[d["role"] == "jury", "entity_id"].tolist(),
                "jury_known": bool(x.jury_known)})
        js = sit[sit["awards"].apply(lambda t, a=a: a in t)]
        top_j = js.groupby("entity_id").size().sort_values(ascending=False)
        g = gender[gender["award_id"] == a]
        fem = lambda df: (float((df["gender"] == "f").mean()) if df["gender"].notna().sum()
                          >= 10 else None)
        c = cov.loc[a] if a in cov.index else None
        stats = {
            "winners": int(rl.loc[rl["role"] == "winner", "entity_id"].nunique()),
            "jurors": int(js["entity_id"].nunique()),
            "female_share_winners": fem(g[g["role"] == "winner"].dropna(subset=["gender"])),
            "female_share_jury": fem(js[js["entity_type"] == "person"].dropna(subset=["gender"])),
            "median_age": ages[a]["median"] if a in ages else None,
            "insider": ({k: insider[a][k] for k in ("insider_wins", "expected", "q")}
                        if a in insider else None),
            "repeat_winners": ({k: repeat_w[a][k] for k in ("repeat_wins", "expected", "q")}
                               if a in repeat_w else None),
            "repeat_seats": ({k: repeat_s[a][k] for k in ("share", "seats")}
                             if a in repeat_s else None),
            "history_share": None if c is None else c["history_share"],
            "data_from": None if c is None else c["data_from"],
            "data_to": None if c is None else c["data_to"],
        }
        awards[a] = {
            "id": a, "name": r["name"], "genre": r["genre"], "field": graph.FIELD[r["genre"]],
            "prestige": int(r["prestige"]), "institution": r["institution"],
            "founded": None if pd.isna(r["founded"]) else int(r["founded"]),
            "ended": None if pd.isna(r["ended"]) else int(r["ended"]),
            "description": r["description"] if isinstance(r["description"], str) else None,
            "editions": editions, "top_jurors": [[e, int(n)] for e, n in top_j.head(15).items()],
            "stats": stats,
        }

    meta = {
        "fields": FIELD_COLOR, "roles": ROLE_COLOR,
        "role_labels": {"winner": "samo nagrajenci", "jury": "samo žiranti",
                        "both": "nagrajenci in žiranti"},
        "kind_labels": {"person": "oseba", "group": "skupina", "institution": "ustanova",
                        "work": "delo"},
        "series": P.SERIES,
        "counts": {"people": len(people), "awards": len(awards), "editions": len(ed),
                   "wins": int((roles["role"] == "winner").sum()), "sittings": len(sit),
                   "years": [int(ed["year"].min()), int(ed["year"].max())]},
    }
    index = sorted(
        [{"id": p["id"], "t": "p", "n": p["name"], "f": p["field"], "r": p["role"],
          "w": len(p["wins"]), "s": len(p["juries"]), "a": p["first"], "b": p["last"],
          "x": sorted({w["award"] for w in p["wins"]} | {j["award"] for j in p["juries"]})}
         for p in people.values()] +
        [{"id": a["id"], "t": "a", "n": a["name"], "f": a["field"], "w": len(a["editions"]),
          "s": a["stats"]["jurors"], "a": a["stats"]["data_from"], "b": a["stats"]["data_to"]}
         for a in awards.values()],
        key=lambda r: r["n"])
    return {"people": people, "awards": awards, "meta": meta, "index": index}


def _map_positions() -> dict:
    """Network-map positions (x, y) by entity id, rounded; empty if the map is not built."""
    nodes = RESULTS / "network" / "nodes.csv"
    if not nodes.exists():
        return {}
    d = pd.read_csv(nodes, usecols=["id", "kind", "x", "y"])
    d = d[d["kind"] != "award"]
    return {i: [round(float(x), 1), round(float(y), 1)] for i, x, y in zip(d["id"], d["x"], d["y"])}


def map_points(meta: dict) -> dict | None:
    """Every node of the network map as [x, y, field index, is award], for the home-page
    and person-page backdrops (much lighter than graph.json)."""
    nodes = RESULTS / "network" / "nodes.csv"
    if not nodes.exists():
        return None
    d = pd.read_csv(nodes, usecols=["kind", "field", "x", "y"])
    fields = list(meta["fields"])
    idx = {f: i for i, f in enumerate(fields)}
    pts = [[round(float(x), 1), round(float(y), 1), idx.get(f, len(fields) - 1), int(k == "award")]
           for k, f, x, y in zip(d["kind"], d["field"], d["x"], d["y"])]
    return {"fields": fields, "points": pts}


def og_default(meta: dict) -> Path:
    """The site-wide Open Graph card (1200 x 630): title, a line of numbers and the
    network map as the image. Per-page cards come later and use the same frame."""
    import matplotlib.pyplot as plt

    nodes = RESULTS / "network" / "nodes.csv"
    out = SITE / "public" / "og" / "privzeto.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    bg, ink, ink2 = BG, "#efe9f4", "#a89fb8"
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=bg)
    if nodes.exists():
        d = pd.read_csv(nodes, usecols=["kind", "x", "y", "color", "size"])
        ax = fig.add_axes((0.44, 0.02, 0.56, 0.96))
        ax.set_facecolor(bg)
        pe = d[d["kind"] != "award"]
        ax.scatter(pe["x"], pe["y"], s=pe["size"] ** 2 * 0.25, c=pe["color"], alpha=0.85,
                   linewidths=0)
        ax.set_xlim(-75, 75)
        ax.set_ylim(-85, 85)
        ax.set_axis_off()
    c = meta["counts"]
    fig.text(0.05, 0.70, "Kulturne\nnagrade", color=ink, fontsize=58, fontweight="normal",
             va="top", family="serif", linespacing=1.0)
    fig.text(0.05, 0.36, "Kdo podeljuje slovenske kulturne\nnagrade in kdo jih prejema?",
             color=ink2, fontsize=21, va="top", linespacing=1.3)
    fig.text(0.05, 0.12, f"{c['awards']} nagrad · {c['people']:,} ljudi · {c['years'][0]}–"
             f"{c['years'][1]}".replace(",", "."), color=ink2, fontsize=16, va="bottom")
    fig.savefig(out, facecolor=bg)
    plt.close(fig)
    return out


def main() -> None:
    out = build()
    sizes = {name: _write(DATA / f"{name}.json", out[name]) for name in ("people", "awards",
                                                                         "meta")}
    sizes["index (public)"] = _write(PUBLIC / "index.json", out["index"])
    g = RESULTS / "network" / "graph.json"
    if g.exists():
        shutil.copy(g, PUBLIC / "graph.json")
        sizes["graph (public)"] = (PUBLIC / "graph.json").stat().st_size
    pts = map_points(out["meta"])
    if pts:
        sizes["map points (public)"] = _write(PUBLIC / "tocke.json", pts)
    from kulturne_nagrade import site_findings
    sizes["findings"] = _write(DATA / "findings.json", site_findings.build())
    og_default(out["meta"])
    print("site export: " + ", ".join(f"{k} {v / 1e6:.1f} MB" for k, v in sizes.items()))


if __name__ == "__main__":
    main()
