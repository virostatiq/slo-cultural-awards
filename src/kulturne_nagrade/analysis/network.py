"""Network: factions and brokers among jurors.

The data is a bipartite graph of people and jury sittings (``frames.jury_sittings``,
so a jury that awards several prizes at once is one sitting). The one-mode projection
links two people who sat together.

Null model: a **bipartite configuration model within blocks**. Sittings are grouped by
(genre, 5-year period); a curveball algorithm repeatedly picks two sittings of the same
block and reshuffles the members they do not share. This keeps every sitting's size and
every person's number of sittings in each block, so each person keeps their field, era
and activity. What it destroys is *who sits with whom*. (The legacy code used a
degree-preserving edge swap on the projection, which breaks the clique structure the
projection gets from each jury and so makes any clustering look significant.)

Questions:
1. Standing juries: pairs who sit together again and again. Mostly the same award
   re-appointing the same jury; measured to separate it from 2.
2. Travelling pairs: pairs who sat together on the juries of at least two different
   awards. If juries were assembled independently within a field and period, how many
   such pairs would there be?
3. Communities: Louvain communities of the projection, their modularity against the
   null, and how far they just follow genre.
4. Brokers: betweenness in the projection, against each person's own null expectation
   (which keeps their fields and activity).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx
import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import permutation_p, rng

THEME = "network"
BLOCK_YEARS = 5
N_NULL = 300           # pair statistics, per null model
N_NULL_HEAVY = 40      # Louvain and betweenness (slow)
TRADES_PER_SITTING = 5
BETWEENNESS_K = 400    # sampled sources for betweenness
MIN_CO_SITTINGS = 3


def run() -> dict:
    j = frames.jury_sittings()
    sittings, award_of, block_of, names, genre_of = build(j)
    g = rng()

    obs = pair_stats(sittings, award_of)
    nulls = [pair_stats(curveball(sittings, block_of, g), award_of) for _ in range(N_NULL)]
    pairs = test_pairs(obs, nulls)
    # Award-preserving null: everyone keeps their awards (and periods); only who sits
    # with whom inside an award's juries is shuffled.
    award_block = {s: f"{award_of[s]}_{b.rsplit('_', 1)[1]}" for s, b in block_of.items()}
    nulls_aw = [pair_stats(curveball(sittings, award_block, g), award_of)
                for _ in range(N_NULL)]
    pairs_aw = test_pairs(obs, nulls_aw)
    plot_pair_tests(pairs, pairs_aw)

    G = projection(sittings)
    comm = communities(G, sittings, block_of, genre_of, g)
    plot_community_genres(comm)
    brokers = broker_scores(G, sittings, block_of, names, genre_of, g)
    plot_brokers(brokers)

    top = obs["co"].sort_values(ascending=False).head(25)
    return {
        "n_sittings": len(sittings), "n_people": len(names),
        "n_pairs": len(obs["co"]),
        "pairs_vs_field_period_null": {k: v for k, v in pairs.items()
                                       if not k.startswith("null_")},
        "pairs_vs_award_null": {k: v for k, v in pairs_aw.items() if not k.startswith("null_")},
        "top_co_sitting_pairs": [{"a": names[a], "b": names[b], "co_sittings": int(n),
                                  "awards": int(obs["n_awards"][(a, b)])}
                                 for (a, b), n in top.items()],
        "top_travelling_pairs": travelling_table(obs, names),
        "communities": {k: v for k, v in comm.items() if k not in ("null", "table")},
        "community_table": comm["table"],
        "brokers": brokers.head(25),
    }


# --- data -------------------------------------------------------------------------------

def build(j: pd.DataFrame):
    j = j.copy()
    j["block"] = j["genre"] + "_" + (j["year"] // BLOCK_YEARS * BLOCK_YEARS).astype(str)
    first = j.drop_duplicates("sitting_id").set_index("sitting_id")
    sittings = {s: frozenset(grp) for s, grp in j.groupby("sitting_id")["entity_id"]}
    award_of = first["award_id"].to_dict()
    block_of = first["block"].to_dict()
    names = j.drop_duplicates("entity_id").set_index("entity_id")["name"].to_dict()
    # a person's main field: the genre of most of their sittings
    genre_of = j.groupby("entity_id")["genre"].agg(lambda s: s.value_counts().index[0]).to_dict()
    return sittings, award_of, block_of, names, genre_of


def curveball(sittings: dict, block_of: dict, g: np.random.Generator) -> dict:
    """One draw from the within-block bipartite configuration model."""
    out = {s: set(m) for s, m in sittings.items()}
    blocks = defaultdict(list)
    for s in out:
        blocks[block_of[s]].append(s)
    for ids in blocks.values():
        if len(ids) < 2:
            continue
        for _ in range(TRADES_PER_SITTING * len(ids)):
            a, b = g.choice(len(ids), 2, replace=False)
            A, B = out[ids[a]], out[ids[b]]
            a_only, b_only = sorted(A - B), sorted(B - A)  # sorted: hash-order independent
            if not a_only or not b_only:
                continue
            pool = a_only + b_only
            g.shuffle(pool)
            shared = A & B
            out[ids[a]] = shared | set(pool[:len(a_only)])
            out[ids[b]] = shared | set(pool[len(a_only):])
    return out


def pair_stats(sittings: dict, award_of: dict) -> dict:
    co, awards = Counter(), defaultdict(set)
    for s, members in sittings.items():
        for a, b in combinations(sorted(members), 2):
            co[(a, b)] += 1
            awards[(a, b)].add(award_of[s])
    co = pd.Series(co, dtype=int)
    n_awards = pd.Series({k: len(v) for k, v in awards.items()}, dtype=int)
    return {
        "co": co, "n_awards": n_awards,
        "repeat_pairs": int((co >= MIN_CO_SITTINGS).sum()),
        "travelling_pairs": int((n_awards >= 2).sum()),
        "travelling_pairs_3": int((n_awards >= 3).sum()),
        "max_co": int(co.max()),
    }


def test_pairs(obs: dict, nulls: list[dict]) -> dict:
    out = {}
    for k in ("repeat_pairs", "travelling_pairs", "travelling_pairs_3"):
        null = np.array([n[k] for n in nulls])
        out[k] = {"observed": obs[k], "expected": float(null.mean()),
                  "null_lo": float(np.percentile(null, 2.5)),
                  "null_hi": float(np.percentile(null, 97.5)),
                  "ratio": obs[k] / null.mean(), "p": permutation_p(obs[k], null)}
        out[f"null_{k}"] = null
    return out


def travelling_table(obs: dict, names: dict, n: int = 25) -> list[dict]:
    t = pd.DataFrame({"co": obs["co"], "n_awards": obs["n_awards"]})
    t = t[t["n_awards"] >= 2].sort_values(["n_awards", "co"], ascending=False).head(n)
    return [{"a": names[a], "b": names[b], "awards": int(r["n_awards"]),
             "co_sittings": int(r["co"])} for (a, b), r in t.iterrows()]


def projection(sittings: dict) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(sorted({v for m in sittings.values() for v in m}))
    for members in sittings.values():
        for a, b in combinations(sorted(members), 2):
            w = G[a][b]["weight"] + 1 if G.has_edge(a, b) else 1
            G.add_edge(a, b, weight=w)
    return G


# --- communities ------------------------------------------------------------------------

def _louvain(G: nx.Graph, seed: int) -> tuple[list, float]:
    parts = nx.community.louvain_communities(G, weight="weight", seed=seed)
    return parts, nx.community.modularity(G, parts, weight="weight")


def _genre_modularity(G: nx.Graph, genre_of: dict) -> float:
    groups = defaultdict(set)
    for v in G:
        groups[genre_of[v]].add(v)
    return nx.community.modularity(G, list(groups.values()), weight="weight")


def communities(G, sittings, block_of, genre_of, g) -> dict:
    """Modularity of Louvain communities vs. the null, and vs. a partition by main genre.
    The null keeps fields and periods, so its modularity already contains all the
    structure that genre and era explain."""
    parts, q = _louvain(G, 1)
    null_q = []
    for i in range(N_NULL_HEAVY):
        Gn = projection(curveball(sittings, block_of, g))
        null_q.append(_louvain(Gn, i + 2)[1])
    null_q = np.array(null_q)
    rows = []
    for k, c in enumerate(sorted(parts, key=len, reverse=True)):
        genres = dict(sorted(Counter(genre_of[v] for v in c).items(),
                             key=lambda kv: (-kv[1], kv[0])))
        top, n_top = next(iter(genres.items()))
        rows.append({"community": k + 1, "size": len(c), "top_genre": top,
                     "top_genre_share": n_top / len(c),
                     "genres": genres})
    table = pd.DataFrame(rows)
    big = table[table["size"] >= 20]
    return {
        "n_communities": len(parts), "n_communities_20plus": len(big),
        "modularity": q, "modularity_genre_partition": _genre_modularity(G, genre_of),
        "null_modularity": float(null_q.mean()),
        "null_modularity_range": [float(null_q.min()), float(null_q.max())],
        "p": permutation_p(q, null_q),
        "mean_top_genre_share_20plus": float(np.average(big["top_genre_share"],
                                                        weights=big["size"])),
        "null": null_q, "table": table,
    }


def plot_community_genres(comm):
    t = comm["table"]
    t = t[t["size"] >= 20]
    genres = sorted({gname for d in t["genres"] for gname in d},
                    key=lambda x: -sum(d.get(x, 0) for d in t["genres"]))
    M = np.array([[d.get(gn, 0) / s for gn in genres] for d, s in zip(t["genres"], t["size"])])
    fig, ax = P.figure(9, 0.42 * len(t) + 2.4)
    im = ax.imshow(M, cmap=P.SEQUENTIAL, vmin=0, vmax=1, aspect="auto")
    for (i, k), v in np.ndenumerate(M):
        if v >= 0.05:
            ax.text(k, i, P.pct(v), ha="center", va="center", fontsize=7,
                    color="white" if v > 0.55 else P.TEXT)
    ax.set_xticks(range(len(genres)))
    ax.set_xticklabels(genres, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels([f"skupnost {c} ({s})" for c, s in zip(t["community"], t["size"])],
                       fontsize=8)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.03, format=P.pct_fmt)
    ax.set_title("Skupnosti žirantov so predvsem področja")
    P.subtitle(ax, "Skupnosti (Louvain) v mreži ljudi, ki so sedeli v isti žiriji · "
                   "delež članov po glavnem področju\n"
                   f"modularnost {P.dec(comm['modularity'], 2)}, delitev po področjih "
                   f"{P.dec(comm['modularity_genre_partition'], 2)}, naključne žirije "
                   f"istega področja in obdobja {P.dec(comm['null_modularity'], 2)}")
    P.source_note(fig)
    P.save(fig, THEME, "skupnosti_in_podrocja")


# --- brokers ----------------------------------------------------------------------------

def broker_scores(G, sittings, block_of, names, genre_of, g) -> pd.DataFrame:
    """Betweenness (sampled) on the unweighted projection, with each person's mean
    betweenness over null draws. Excess = observed - null: brokerage beyond what the
    person's fields, periods and number of sittings would give anyway."""
    obs = nx.betweenness_centrality(G, k=min(BETWEENNESS_K, len(G)), seed=1)
    acc = defaultdict(float)
    for i in range(N_NULL_HEAVY):
        Gn = projection(curveball(sittings, block_of, g))
        for v, b in nx.betweenness_centrality(Gn, k=min(BETWEENNESS_K, len(Gn)),
                                              seed=i + 2).items():
            acc[v] += b / N_NULL_HEAVY
    seats = Counter(v for m in sittings.values() for v in m)
    fields = defaultdict(set)
    for s, m in sittings.items():
        for v in m:
            fields[v].add(block_of[s].rsplit("_", 1)[0])
    df = pd.DataFrame({"entity_id": list(obs), "betweenness": list(obs.values())})
    df["null"] = df["entity_id"].map(acc).fillna(0.0)
    df["excess"] = df["betweenness"] - df["null"]
    df["name"] = df["entity_id"].map(names)
    df["sittings"] = df["entity_id"].map(seats)
    df["fields"] = df["entity_id"].map(lambda v: len(fields[v]))
    df["main_genre"] = df["entity_id"].map(genre_of)
    return df.sort_values("betweenness", ascending=False).reset_index(drop=True)


def plot_brokers(b, n: int = 20):
    d = b.head(n).iloc[::-1]
    fig, ax = P.figure(8.5, 0.32 * n + 2)
    y = np.arange(len(d))
    ax.barh(y, d["betweenness"], color=P.SERIES[0], height=0.6, label="opaženo")
    ax.scatter(d["null"], y, color=P.TEXT, marker="|", s=160, zorder=3,
               label="pričakovano pri naključnih žirijah")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{nm}  ({s} žirij, {f} podr.)" for nm, s, f in
                        zip(d["name"], d["sittings"], d["fields"])], fontsize=8)
    ax.xaxis.set_major_formatter(lambda v, _: P.dec(v, 3))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("vmesnost (delež najkrajših poti med drugimi žiranti, ki gredo skozi osebo)")
    ax.legend(loc="lower right")
    ax.set_title("Kdo povezuje svet žirij?")
    P.subtitle(ax, "Žiranti z največjo vmesnostjo v mreži skupnega sedenja v žirijah\n"
                   "Črtica = povprečje pri naključnih žirijah, ki ohranijo vsakemu njegova "
                   "področja, obdobja in število žirij")
    P.source_note(fig)
    P.save(fig, THEME, "povezovalci")


# --- plots for pairs --------------------------------------------------------------------

def plot_pair_tests(pairs, pairs_aw):
    rows = [
        (pairs, "repeat_pairs", f"dvojice z vsaj {MIN_CO_SITTINGS} skupnimi žirijami",
         "premešano znotraj področja in petletja"),
        (pairs_aw, "repeat_pairs", f"dvojice z vsaj {MIN_CO_SITTINGS} skupnimi žirijami",
         "premešano znotraj iste nagrade in petletja"),
        (pairs_aw, "travelling_pairs", "dvojice, skupaj v žirijah vsaj 2 nagrad",
         "premešano znotraj iste nagrade in petletja"),
        (pairs_aw, "travelling_pairs_3", "dvojice, skupaj v žirijah vsaj 3 nagrad",
         "premešano znotraj iste nagrade in petletja"),
    ][::-1]
    fig, ax = P.figure(9, 4.2)
    for y, (res, k, label, null_label) in enumerate(rows):
        r = res[k]
        e = r["expected"]
        ax.hlines(y, r["null_lo"] / e, r["null_hi"] / e, color=P.MUTED, lw=8, alpha=0.5)
        ax.scatter(r["observed"] / e, y, color=P.SERIES[7] if r["p"] < 0.05 else P.TEXT_2,
                   s=60, zorder=3)
        ax.annotate(f"{r['observed']} : {P.dec(e, 0)}  ({P.dec(r['observed'] / e, 2)}×)",
                    (r["observed"] / e, y), xytext=(10, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=P.TEXT)
    ax.axvline(1, color=P.TEXT_2, lw=1)
    ax.set_xscale("log")
    ax.set_xticks([0.8, 1, 1.5, 2, 3, 4])
    ax.set_xticklabels([P.dec(v, 1).replace(",0", "") for v in [0.8, 1, 1.5, 2, 3, 4]])
    ax.minorticks_off()
    ax.set_xlim(0.75, 5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{lab}\n{nl}" for _, _, lab, nl in rows], fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("opaženo / pričakovano pri naključnih žirijah (logaritemska os)")
    ax.set_title("Žirije se obnavljajo v istem sestavu, med nagradami pa ne potujejo skupaj")
    P.subtitle(ax, f"Siv pas = 95 % razpon pri {N_NULL} naključnih razporeditvah (vsaka žirija "
                   "ohrani velikost, vsak žirant število žirij)\nRdeče = značilno (p < 0,05)")
    P.source_note(fig)
    P.save(fig, THEME, "ponavljajoce_dvojice")
