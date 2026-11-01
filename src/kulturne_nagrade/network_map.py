"""The network map for the website: node2vec layout of the awards graph.

    uv sync --group network
    uv run python -m kulturne_nagrade.network_map

Builds the typed graph (kulturne_nagrade.graph), embeds it with node2vec and lays the
embedding out in 2D with UMAP, then writes to results/network/:

  graph.json      graphology format for sigma.js: nodes with x, y, size, color, label,
                  kind, field and the person's record; co_jury, judged and role edges
  graph.graphml   the same typed graph with positions, for networkx / Gephi queries
  nodes.csv, edges.csv   flat tables
  embedding.npz   node ids and node2vec vectors ("who sits in a similar place")

and a static preview to plots/network/zemljevid_mreze.png.

The layout is a picture, not a finding: positions summarise who sits near whom in
random walks over the graph; distances are not tested against a null (the network
theme and docs/findings.md §12 do that). Deterministic: seeded walks, one word2vec
worker, a fixed UMAP random_state.

Legacy (improved_awards_processor.py): raw rows (shared juries counted per prize),
hand-set weights (jury-winner 3.0, field hubs 4.0), commission ties, a non-seeded
multi-worker node2vec and UMAP with 5 neighbours (hundreds of islands), every label
drawn, eight colours for role combinations.
"""

from __future__ import annotations

import json

import networkx as nx
import numpy as np
import pandas as pd
from numba import njit
from scipy.sparse import csr_matrix

from kulturne_nagrade import PROJECT_ROOT, graph
from kulturne_nagrade import plotting as P

OUT = graph.OUT_DIR
SEED = 20261101
# node2vec: q < 1 favours walks that move outward (communities); p = 1 neutral.
DIM, WALKS, LENGTH, WINDOW, EPOCHS, P_RET, Q_IN = 64, 20, 40, 5, 5, 1.0, 0.5
UMAP_NEIGHBOURS, UMAP_MIN_DIST = 30, 0.8  # chosen from a grid; more room per person
N_LABELS = 40  # people labelled in the preview and flagged `landmark` for the site

ROLE_COLOR = {"winner": P.ROLE_COLOR["winner"], "jury": P.ROLE_COLOR["jury"],
              "both": P.SERIES[3]}  # role hues, never the gender pair
ROLE_LABEL = {"winner": "samo nagrajenci", "jury": "samo žiranti",
              "both": "nagrajenci in žiranti"}

FIELD_COLOR = {  # gender hues (SERIES[0], SERIES[1]) are reserved, so slots 2–7
    "literatura": P.SERIES[6], "gledališče in ples": P.SERIES[7], "film": P.SERIES[3],
    "likovna umetnost in arhitektura": P.SERIES[2], "glasba": P.SERIES[4],
    "novinarstvo": P.SERIES[5], "splošno": P.MUTED,
}


# --- embedding --------------------------------------------------------------------------

def embedding_graph(G: nx.MultiDiGraph) -> nx.Graph:
    """Undirected weighted graph for the walks: role edges weigh their count (each win
    or sitting ties a person to the award), co_jury and judged edges their weights."""
    H = nx.Graph()
    H.add_nodes_from(G.nodes)
    for u, v, d in G.edges(data=True):
        w = float(d["count"]) if d["kind"] == "role" else float(d["weight"])
        if H.has_edge(u, v):
            H[u][v]["weight"] += w
        else:
            H.add_edge(u, v, weight=w)
    return H


@njit(cache=True)
def _has_edge(indptr, indices, a, b):
    lo, hi = indptr[a], indptr[a + 1]
    while lo < hi:
        mid = (lo + hi) // 2
        if indices[mid] < b:
            lo = mid + 1
        else:
            hi = mid
    return lo < indptr[a + 1] and indices[lo] == b


@njit(cache=True)
def _walks(indptr, indices, weights, starts, length, p, q, seed):
    np.random.seed(seed)
    out = np.full((len(starts), length), -1, dtype=np.int64)
    for i in range(len(starts)):
        cur, prev = starts[i], -1
        out[i, 0] = cur
        for t in range(1, length):
            s, e = indptr[cur], indptr[cur + 1]
            if s == e:
                break
            w = weights[s:e].copy()
            if prev >= 0:
                for k in range(e - s):
                    x = indices[s + k]
                    if x == prev:
                        w[k] /= p
                    elif not _has_edge(indptr, indices, prev, x):
                        w[k] /= q
            c = np.cumsum(w)
            r = np.random.random() * c[-1]
            k = np.searchsorted(c, r, side="right")
            prev, cur = cur, indices[s + min(k, e - s - 1)]
            out[i, t] = cur
    return out


def node2vec(H: nx.Graph) -> tuple[list[str], np.ndarray]:
    from gensim.models import Word2Vec

    nodes = sorted(H.nodes)
    A = nx.to_scipy_sparse_array(H, nodelist=nodes, weight="weight", format="csr")
    A = csr_matrix(A)
    A.sort_indices()
    starts = np.tile(np.arange(len(nodes)), WALKS)
    np.random.default_rng(SEED).shuffle(starts)
    W = _walks(A.indptr.astype(np.int64), A.indices.astype(np.int64),
               A.data.astype(np.float64), starts, LENGTH, P_RET, Q_IN, SEED)
    sentences = [[str(x) for x in row[row >= 0]] for row in W]
    m = Word2Vec(sentences, vector_size=DIM, window=WINDOW, min_count=1, sg=1, workers=1,
                 epochs=EPOCHS, seed=SEED)
    return nodes, np.vstack([m.wv[str(i)] for i in range(len(nodes))])


def layout(vectors: np.ndarray) -> np.ndarray:
    from umap import UMAP

    xy = UMAP(n_neighbors=UMAP_NEIGHBOURS, min_dist=UMAP_MIN_DIST, metric="cosine",
              random_state=SEED, n_jobs=1).fit_transform(vectors)
    xy = xy - xy.mean(axis=0)
    return xy / np.abs(xy).max() * 100


# --- export -----------------------------------------------------------------------------

def decorate(G, nodes, xy):
    for n, (x, y) in zip(nodes, xy):
        d = G.nodes[n]
        d["x"], d["y"] = round(float(x), 3), round(float(y), 3)
        d["color"] = FIELD_COLOR[d["field"]]
        if d["kind"] == "award":
            d["size"] = round(5 + 2 * d["prestige"], 2)
        else:
            d["size"] = round(1.5 + 1.2 * np.sqrt(d["wins"] + d["sittings"]), 2)
            d["role"] = ("both" if d["wins"] and d["sittings"]
                         else "winner" if d["wins"] else "jury")
    people = [n for n in G if G.nodes[n]["kind"] != "award"]
    top = sorted(people, key=lambda n: -(G.nodes[n]["wins"] + G.nodes[n]["sittings"]))
    for n in G:
        G.nodes[n]["landmark"] = G.nodes[n]["kind"] == "award" or n in set(top[:N_LABELS])


def regions(G) -> list[dict]:
    """Where to put each field's name: the densest spot of its people (a smoothed 2D
    histogram's peak). The median would fall between the clusters of a split field."""
    from scipy.ndimage import gaussian_filter

    out = []
    for f in FIELD_COLOR:
        pts = np.array([(d["x"], d["y"]) for _, d in G.nodes(data=True)
                        if d["field"] == f and d["kind"] != "award"])
        if len(pts) < 20:
            continue
        h, xe, ye = np.histogram2d(pts[:, 0], pts[:, 1], bins=60, range=[[-100, 100]] * 2)
        i, j = np.unravel_index(np.argmax(gaussian_filter(h, 2)), h.shape)
        out.append({"field": f, "x": float((xe[i] + xe[i + 1]) / 2),
                    "y": float((ye[j] + ye[j + 1]) / 2), "people": len(pts),
                    "color": FIELD_COLOR[f]})
    return out


def records(G) -> dict:
    """Per person: wins and jury sittings as [year, award] lists (win_list, jury_list),
    for the info panel."""
    from kulturne_nagrade import frames

    roles = frames.roles(entity_types=None)
    sit = frames.jury_sittings(entity_types=None)
    rec = {}
    for role, df in (("win_list", roles[roles["role"] == "winner"]), ("jury_list", sit)):
        for e, d in df.sort_values("year").groupby("entity_id"):
            rec.setdefault(e, {})[role] = [[int(y), a] for y, a in zip(d["year"], d["award"])]
    return rec


def to_graphology(G, regs) -> dict:
    rec = records(G)
    nodes = []
    for n, d in G.nodes(data=True):
        a = {k: d[k] for k in ("label", "x", "y", "size", "color", "kind", "field",
                               "role", "landmark") if k in d}
        if d["kind"] == "award":
            a.update(prestige=d["prestige"], genre=d["genre"])
        else:
            a.update(wins=d["wins"], sittings=d["sittings"], first=d["first"],
                     last=d["last"], **rec.get(n, {}))
        nodes.append({"key": n, "attributes": a})
    # The page draws people-to-people ties; role edges and per-edge details (years,
    # awards) are in the records and graph.graphml, which keeps the file light.
    keep = {"co_jury": ("sittings", "weight"), "judged": ("editions", "weight")}
    edges = [{"source": u, "target": v,
              "attributes": {"kind": d["kind"], **{k: d[k] for k in keep[d["kind"]]}}}
             for u, v, d in G.edges(data=True) if d["kind"] in keep]
    return {"attributes": {"name": "Slovenske kulturne nagrade: mreža", "regions": regs,
                           "layout": "node2vec + UMAP (cosine)", "fields": FIELD_COLOR,
                           "roles": ROLE_COLOR},
            "options": {"type": "mixed", "multi": True, "allowSelfLoops": False},
            "nodes": nodes, "edges": edges}


def write(G, nodes, vectors, regs):
    OUT.mkdir(parents=True, exist_ok=True)
    graph.save(G)
    (OUT / "graph.json").write_text(json.dumps(to_graphology(G, regs), ensure_ascii=False,
                                               separators=(",", ":")), encoding="utf-8")
    pd.DataFrame([{"id": n, **d} for n, d in G.nodes(data=True)]).to_csv(
        OUT / "nodes.csv", index=False)
    pd.DataFrame([{"source": u, "target": v, **d} for u, v, d in G.edges(data=True)]).to_csv(
        OUT / "edges.csv", index=False)
    np.savez_compressed(OUT / "embedding.npz", ids=np.array(nodes), vectors=vectors)


def preview(G, regs):
    """Static check of legibility; the site renders the interactive version."""
    fig, ax = P.figure(12, 12)
    d = pd.DataFrame([{"id": n, **a} for n, a in G.nodes(data=True)])
    pe, aw = d[d["kind"] != "award"], d[d["kind"] == "award"]
    ax.scatter(pe["x"], pe["y"], s=pe["size"] ** 2 * 0.6, c=pe["color"], alpha=0.75,
               linewidths=0)
    ax.scatter(aw["x"], aw["y"], s=aw["size"] ** 2 * 0.9, c=aw["color"], marker="D",
               edgecolors=P.TEXT, linewidths=0.8, zorder=3)
    for r in regs:
        ax.text(r["x"], r["y"], r["field"].upper(), ha="center", va="center", fontsize=15,
                fontweight="bold", color=P.TEXT, alpha=0.55, zorder=4)
    for _, r in aw.nlargest(20, "size").iterrows():
        ax.annotate(r["label"], (r["x"], r["y"]), xytext=(6, 4), textcoords="offset points",
                    fontsize=8, color=P.TEXT, zorder=5)
    ax.set_axis_off()
    ax.set_title("Mreža slovenskih kulturnih nagrad")
    P.subtitle(ax, f"{len(pe)} ljudi in skupin, {len(aw)} nagrad · bližina = pogosto skupaj "
                   "v žirijah ali v vlogi žirant–nagrajenec (node2vec + UMAP)\nbarva = "
                   "področje večine vlog · romb = nagrada")
    P.source_note(fig)
    P.save(fig, "network", "zemljevid_mreze")


def preview_roles(G):
    """Same layout, coloured by role, with every award and the most active people named."""
    from adjustText import adjust_text

    d = pd.DataFrame([{"id": n, **a} for n, a in G.nodes(data=True)])
    pe, aw = d[d["kind"] != "award"], d[d["kind"] == "award"]
    fig, ax = P.figure(20, 20)
    for role in ("winner", "jury", "both"):  # the busiest people drawn last, on top
        r = pe[pe["role"] == role]
        ax.scatter(r["x"], r["y"], s=r["size"] ** 2 * 0.6, c=ROLE_COLOR[role], alpha=0.7,
                   linewidths=0, label=f"{ROLE_LABEL[role]} ({len(r)})")
    ax.scatter(aw["x"], aw["y"], s=aw["size"] ** 2 * 0.8, c=P.TEXT, marker="D",
               edgecolors=P.SURFACE, linewidths=1, zorder=3, label=f"nagrade ({len(aw)})")
    texts = [ax.text(r["x"], r["y"], r["label"], fontsize=7, color=P.TEXT, zorder=6)
             for _, r in aw.iterrows()]
    named = pe[pe["landmark"]]
    texts += [ax.text(r["x"], r["y"], r["label"], fontsize=8, fontweight="bold",
                      color=P.TEXT, zorder=6) for _, r in named.iterrows()]
    ax.scatter(named["x"], named["y"], s=named["size"] ** 2 * 0.6, facecolors="none",
               edgecolors=P.TEXT, linewidths=0.8, zorder=4)
    ax.set_axis_off()
    adjust_text(texts, x=np.r_[aw["x"], named["x"]], y=np.r_[aw["y"], named["y"]], ax=ax,
                expand=(1.3, 1.7), force_text=(0.6, 0.9), force_explode=(0.4, 0.8),
                iter_lim=2000, time_lim=30, min_arrow_len=3,
                arrowprops=dict(arrowstyle="-", color=P.TEXT_2, lw=0.5))
    ax.legend(loc="lower left", markerscale=1.5, fontsize=9, frameon=False)
    ax.set_title("Nagrade, nagrajenci in žiranti")
    P.subtitle(ax, f"Ista postavitev kot zemljevid področij · imenovane vse nagrade (navadno) "
                   f"in {len(named)} ljudi z največ nagradami in sedeži v žirijah (krepko)\n"
                   "bližina = pogosto skupaj v žirijah ali v vlogi žirant–nagrajenec "
                   "(node2vec + UMAP)")
    P.source_note(fig)
    P.save(fig, "network", "zemljevid_vloge")


def main(argv: list[str] | None = None) -> None:
    if argv and argv[0] == "--plots":  # re-render previews from the saved graph
        G = graph.load()
        preview(G, regions(G))
        preview_roles(G)
        return
    G = graph.build()
    H = embedding_graph(G)
    nodes, vectors = node2vec(H)
    xy = layout(vectors)
    decorate(G, nodes, xy)
    regs = regions(G)
    write(G, nodes, vectors, regs)
    preview(G, regs)
    preview_roles(G)
    kinds = pd.Series([d["kind"] for _, _, d in G.edges(data=True)]).value_counts()
    print(f"network map: {G.number_of_nodes()} nodes, {dict(kinds)} -> {OUT}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
