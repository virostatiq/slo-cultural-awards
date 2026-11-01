"""The awards network as a typed graph: build it from data/, save it, query it.

Nodes
  person / group / institution / work   entity_id
  award                                 "award:<award_id>"

Edges (a MultiDiGraph; each edge has `kind`)
  co_jury   person — person, stored once per pair (u < v) with `sittings`, `weight`
            (Σ 1/(jury size − 1): a seat on a 3-person jury ties you to each
            co-juror more than a seat on a 15-person one), `first`, `last`, `awards`
  judged    juror → winner, with `editions` (count), `weight` (Σ 1/number of
            jurors), `first`, `last`, `awards`
  role      entity → award, `role` = winner | jury, `count`, `first`, `last`

Jury seats are sittings (frames.jury_sittings), so a jury that awards several prizes
at once ties its members once. `judged` edges come from each edition's own jury list,
so every prize a sitting gave is a separate judged tie, as it should be.

    from kulturne_nagrade import graph
    G = graph.load()                       # results/network/graph.graphml
    graph.summary(G, "ignacija-j-fridl")   # a person's record from the graph
    graph.judged_by(G, "dusan-jovanovic")  # who sat on juries that awarded them
    graph.connection(G, "a", "b")          # shortest chain of co-jury/judged ties
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd

from kulturne_nagrade import PROJECT_ROOT, frames

OUT_DIR = PROJECT_ROOT / "results" / "network"
GRAPHML = OUT_DIR / "graph.graphml"

# Fields for display: 10 genres merged to 6, plus "splošno" for umbrella awards.
FIELD = {
    "literatura": "literatura", "poezija": "literatura",
    "gledališče": "gledališče in ples", "ples": "gledališče in ples",
    "film": "film",
    "likovno-vizualna umetnost": "likovna umetnost in arhitektura",
    "arhitektura": "likovna umetnost in arhitektura",
    "glasba": "glasba", "novinarstvo": "novinarstvo",
    "umetnost in kultura": "splošno",
}


def award_node(award_id: str) -> str:
    return f"award:{award_id}"


def build() -> nx.MultiDiGraph:
    roles = frames.roles(entity_types=None)
    sit = frames.jury_sittings(entity_types=None)
    ent = frames.entities().set_index("entity_id")
    aw = frames.awards().set_index("award_id")
    G = nx.MultiDiGraph()

    for a, r in aw.iterrows():
        G.add_node(award_node(a), kind="award", label=r["name"], genre=r["genre"],
                   field=FIELD[r["genre"]], prestige=int(r["prestige"]))

    people = set(roles["entity_id"])
    wins = roles[roles["role"] == "winner"]
    for e in people:
        G.add_node(e, kind=ent.loc[e, "entity_type"], label=ent.loc[e, "name"])
    nwin = wins.groupby("entity_id").size()
    nsit = sit.groupby("entity_id").size()
    yrs = pd.concat([wins[["entity_id", "year"]], sit[["entity_id", "year"]]])
    span = yrs.groupby("entity_id")["year"].agg(["min", "max"])
    field = _main_field(wins, sit)
    for e in people:
        G.nodes[e].update(wins=int(nwin.get(e, 0)), sittings=int(nsit.get(e, 0)),
                          first=int(span.loc[e, "min"]), last=int(span.loc[e, "max"]),
                          field=field.get(e, "splošno"))

    # role edges: entity -> award
    for role, df in (("winner", wins), ("jury", sit)):
        g = df.groupby(["entity_id", "award_id"])["year"].agg(["size", "min", "max"])
        for (e, a), r in g.iterrows():
            G.add_edge(e, award_node(a), kind="role", role=role, count=int(r["size"]),
                       first=int(r["min"]), last=int(r["max"]))

    # co_jury edges: once per pair and sitting
    pair: dict[tuple, dict] = {}
    for _, d in sit.groupby("sitting_id"):
        m = sorted(d["entity_id"])
        if len(m) < 2:
            continue
        y, a = int(d["year"].iloc[0]), d["award"].iloc[0]
        for u, v in combinations(m, 2):
            p = pair.setdefault((u, v), {"sittings": 0, "weight": 0.0, "first": y,
                                         "last": y, "awards": set()})
            p["sittings"] += 1
            p["weight"] += 1 / (len(m) - 1)
            p["first"], p["last"] = min(p["first"], y), max(p["last"], y)
            p["awards"].add(a)
    for (u, v), p in pair.items():
        G.add_edge(u, v, kind="co_jury", sittings=p["sittings"], weight=round(p["weight"], 4),
                   first=p["first"], last=p["last"], awards="; ".join(sorted(p["awards"])))

    # judged edges: juror -> winner, per edition
    jury = roles[roles["role"] == "jury"]
    jd: dict[tuple, dict] = {}
    for ed, d in roles.groupby("edition_id"):
        js = d.loc[d["role"] == "jury", "entity_id"].tolist()
        ws = d.loc[d["role"] == "winner", "entity_id"].tolist()
        if not js or not ws:
            continue
        y, a = int(d["year"].iloc[0]), d["award"].iloc[0]
        for j in js:
            for w in ws:
                if j == w:
                    continue
                p = jd.setdefault((j, w), {"editions": 0, "weight": 0.0, "first": y,
                                           "last": y, "awards": set()})
                p["editions"] += 1
                p["weight"] += 1 / len(js)
                p["first"], p["last"] = min(p["first"], y), max(p["last"], y)
                p["awards"].add(a)
    del jury
    for (j, w), p in jd.items():
        G.add_edge(j, w, kind="judged", editions=p["editions"], weight=round(p["weight"], 4),
                   first=p["first"], last=p["last"], awards="; ".join(sorted(p["awards"])))
    return G


def _main_field(wins, sit) -> dict:
    """The display field of each entity: the merged field of most of its wins at field
    awards; jury seats decide only for entities with no field wins (a juror often sits
    outside their own field, e.g. writers on the journalism jury of the Jurčičeva
    nagrada). Ties go to the most recent role. Entities with roles at umbrella awards
    only are 'splošno'."""
    def top(r):
        r = r.assign(field=r["genre"].map(FIELD))
        r = r[r["field"] != "splošno"]
        g = r.groupby(["entity_id", "field"]).agg(n=("year", "size"), last=("year", "max"))
        g = g.reset_index().sort_values(["entity_id", "n", "last"],
                                        ascending=[True, False, False])
        return g.drop_duplicates("entity_id").set_index("entity_id")["field"].to_dict()

    return {**top(sit[["entity_id", "genre", "year"]]),
            **top(wins[["entity_id", "genre", "year"]])}


def save(G: nx.MultiDiGraph, path: Path = GRAPHML) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, path)
    return path


def load(path: Path = GRAPHML) -> nx.MultiDiGraph:
    """The saved graph. graph.graphml is not committed (14 MB, regenerated by
    network_map); without it the graph is rebuilt from data/ (about 2 s) and the map
    positions are attached from the committed nodes.csv, if present."""
    if path.exists():
        return nx.read_graphml(path, force_multigraph=True)
    G = build()
    nodes = OUT_DIR / "nodes.csv"
    if nodes.exists():
        pos = pd.read_csv(nodes, usecols=["id", "x", "y"]).set_index("id")
        for n in G:
            if n in pos.index:
                G.nodes[n]["x"], G.nodes[n]["y"] = (float(v) for v in pos.loc[n])
    return G


# --- queries ----------------------------------------------------------------------------

def _edges(G, kind):
    return [(u, v, d) for u, v, d in G.edges(data=True) if d.get("kind") == kind]


def summary(G, node: str) -> dict:
    """A person's record as the graph holds it."""
    n = G.nodes[node]
    roles = [(d["role"], G.nodes[v]["label"], d["count"], d["first"], d["last"])
             for _, v, d in G.out_edges(node, data=True) if d["kind"] == "role"]
    mine = [(u, v, d) for u, v, d in G.out_edges(node, data=True)] + \
           [(u, v, d) for u, v, d in G.in_edges(node, data=True)]
    co = sorted(((G.nodes[v if u == node else u]["label"], d["sittings"])
                 for u, v, d in mine if d["kind"] == "co_jury"), key=lambda t: -t[1])
    return {**n, "roles": sorted(roles, key=lambda t: t[3]), "co_jurors": co[:20],
            "judged": sum(1 for u, _, d in mine if d["kind"] == "judged" and u == node),
            "judged_by": sum(1 for _, v, d in mine if d["kind"] == "judged" and v == node)}


def judged_by(G, node: str) -> list[tuple]:
    """Jurors who sat on juries that awarded `node`: (name, editions, awards)."""
    out = [(G.nodes[u]["label"], d["editions"], d["awards"])
           for u, _, d in G.in_edges(node, data=True) if d["kind"] == "judged"]
    return sorted(out, key=lambda t: -t[1])


def judged(G, node: str) -> list[tuple]:
    """Winners of editions `node` judged: (name, editions, awards)."""
    out = [(G.nodes[v]["label"], d["editions"], d["awards"])
           for _, v, d in G.out_edges(node, data=True) if d["kind"] == "judged"]
    return sorted(out, key=lambda t: -t[1])


def people_graph(G) -> nx.Graph:
    """Undirected person–person graph of co_jury and judged ties (award nodes dropped)."""
    H = nx.Graph()
    for u, v, d in G.edges(data=True):
        if d["kind"] in ("co_jury", "judged"):
            H.add_edge(u, v, kind=d["kind"])
    return H


def connection(G, a: str, b: str) -> list[tuple]:
    """Shortest chain of co_jury/judged ties between two people, as (name, tie, name)."""
    H = people_graph(G)
    path = nx.shortest_path(H, a, b)
    return [(G.nodes[u]["label"], H.edges[u, v]["kind"], G.nodes[v]["label"])
            for u, v in zip(path, path[1:])]
