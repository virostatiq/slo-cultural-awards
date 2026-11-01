"""Awards as institutions: which awards go back to their own past winners, which share
juror pools, and whether older awards keep more stable juries.

1. Repeat winners. The insider-premium engine (juries.peer_premium) with "won this
   award before" as the prior tie: among the winners of a (genre, year) pool, do past
   winners of award A win A again rather than a peer award? Shuffling winners across an
   award's own editions would keep each person's count of wins, so it cannot test this.
2. Shared juror pools. For award pairs, the number of people who sat on both juries
   (sittings, filed under the sitting's main award), against the within-(genre, 5-year)
   curveball null of the network theme (each sitting keeps its size, each person their
   number of sittings per block). Tail p-values from a count distribution matched to
   the null draws (see _count_tail), BH across pairs.
3. Jury stability and award age. Seat-level "repeat" (the person sat on the same
   award's jury in the previous 3 years; power theme) against the award's age (years
   since founding). Within one award, age moves with the calendar, so awards are
   compared with other awards in the same 5-year period (period fixed effects;
   permutation of age among editions of the period).

Legacy: plots 49/37 (unnormalized HHI, raw Lorenz per award), 33/38 (Jaccard of raw
juror pools, no null) and 39 ("age" = span of coverage, one point per award).
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from scipy.stats import nbinom, poisson

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import bh_fdr, rng, wilson, within_stratum_slope
from kulturne_nagrade.analysis.juries import peer_premium
from kulturne_nagrade.analysis.network import build, curveball
from kulturne_nagrade.analysis.power import LOOKBACK

THEME = "awards"
N_NULL = 200
MIN_SHARED = 3
STABILITY_FROM = 1990
AGE_BANDS = [(0, 9), (10, 24), (25, 49), (50, 200)]


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    rep = repeat_winners(roles)
    plot_repeat_winners(rep)
    pools = shared_pools(sit)
    plot_shared_pools(pools)
    stab = stability_vs_age(sit)
    plot_stability(stab)
    return {
        "repeat_winners": {k: v for k, v in rep.items() if k != "per_award"},
        "repeat_winners_per_award": rep["per_award"],
        "shared_pools": {k: v for k, v in pools.items() if k != "pairs"},
        "shared_pool_pairs": pools["pairs"],
        "stability_vs_age": {k: v for k, v in stab.items() if k not in ("null", "bands")},
        "stability_by_age_band": stab["bands"],
    }


# --- 1. repeat winners ------------------------------------------------------------------

def repeat_winners(roles) -> dict:
    w = roles[roles["role"] == "winner"][["entity_id", "award_id", "award", "genre", "year",
                                          "age"]]
    w = w.drop_duplicates(["entity_id", "award_id", "year"]).reset_index(drop=True)
    first_win = {k: int(v) for k, v in w.groupby(["entity_id", "award_id"])["year"].min().items()}
    res = peer_premium(w, first_win, ["genre", "year"])
    per = res["per_award"].rename(columns={"insider_wins": "repeat_wins"})
    out = {k: v for k, v in res.items() if k not in ("null_total", "per_award")}
    out["repeat_wins"] = out.pop("insider_wins")
    out["per_award"] = per
    out["significant_awards"] = per.loc[(per["q"] < 0.05) &
                                        (per["repeat_wins"] > per["expected"]), "award"].tolist()
    return out


def plot_repeat_winners(rep):
    per = rep["per_award"]
    per = per[(per["repeat_wins"] >= 3) | (per["q"] < 0.05)].sort_values("repeat_wins")
    fig, ax = P.figure(8.5, 0.32 * len(per) + 2.2)
    y = np.arange(len(per))
    ax.hlines(y, per["expected"], per["repeat_wins"], color=P.GRID, lw=3)
    ax.scatter(per["expected"], y, s=50, color=P.MUTED, zorder=3, edgecolors=P.SURFACE,
               linewidths=1.5, label="pričakovano pri vrstnikih")
    sig = (per["q"] < 0.05).to_numpy()
    c = P.ROLE_COLOR["winner"]
    ax.scatter(per.loc[~sig, "repeat_wins"], y[~sig], s=60, color=c, alpha=0.45, zorder=4,
               edgecolors=P.SURFACE, linewidths=1.5, label="opaženo")
    ax.scatter(per.loc[sig, "repeat_wins"], y[sig], s=60, color=c, zorder=4,
               edgecolors=P.SURFACE, linewidths=1.5, label="opaženo, značilno (q < 0,05)")
    ax.set_yticks(y, per["award"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("nagrade, ki so šle nekomu, ki je isto nagrado že dobil")
    ax.set_title("Katere nagrade so ponovno podeljene prejšnjim nagrajencem?")
    P.subtitle(ax, f"Skupaj {rep['repeat_wins']} ponovnih nagrad, pri vrstnikih bi pričakovali "
                   f"{rep['expected']:.0f} · vrstniki = nagrajenci drugih nagrad istega\n"
                   "področja v istem letu · prikazane nagrade z vsaj tremi ponovitvami")
    ax.legend(loc="lower right", fontsize=8)
    P.source_note(fig)
    P.save(fig, THEME, "ponovni_nagrajenci_po_nagradah")


# --- 2. shared juror pools --------------------------------------------------------------

def _pool_pairs(sittings: dict, award_of: dict) -> Counter:
    held: dict[str, set] = {}
    for s, members in sittings.items():
        for e in members:
            held.setdefault(e, set()).add(award_of[s])
    c = Counter()
    for aw in held.values():
        aw = sorted(aw)
        for i, a in enumerate(aw):
            for b in aw[i + 1:]:
                c[(a, b)] += 1
    return c


def _count_tail(obs: np.ndarray, null: np.ndarray) -> np.ndarray:
    """P(X >= obs) under a count distribution matched to the null draws' mean and
    variance (Poisson, or negative binomial when overdispersed). With thousands of
    pairs, the empirical tail of N_NULL draws cannot go below 1/(N_NULL+1), too coarse
    for BH; the moment-matched tail can."""
    m, v = null.mean(axis=0), null.var(axis=0, ddof=1)
    p = np.ones(len(obs))
    for i, (o, mi, vi) in enumerate(zip(obs, m, v)):
        if o == 0:
            continue
        if mi == 0:
            p[i] = 1 / (null.shape[0] + 1)  # never seen in the null: bounded, not zero
        elif vi <= mi:
            p[i] = poisson.sf(o - 1, mi)
        else:
            r = mi**2 / (vi - mi)
            p[i] = nbinom.sf(o - 1, r, r / (r + mi))
    return p


def shared_pools(sit) -> dict:
    sittings, award_of, block_of, _, _ = build(sit)
    obs = _pool_pairs(sittings, award_of)
    g = rng()
    nulls = [_pool_pairs(curveball(sittings, block_of, g), award_of) for _ in range(N_NULL)]
    keys = sorted(set(obs) | set().union(*nulls))
    o = np.array([obs.get(k, 0) for k in keys])
    nm = np.array([[n.get(k, 0) for k in keys] for n in nulls])
    p = _count_tail(o, nm)
    a = frames.awards().set_index("award_id")
    pairs = pd.DataFrame({"a_id": [k[0] for k in keys], "b_id": [k[1] for k in keys],
                          "shared": o, "expected": nm.mean(axis=0), "p": p})
    pairs["q"] = bh_fdr(pairs["p"])
    pairs["ratio"] = pairs["shared"] / pairs["expected"].where(pairs["expected"] > 0)
    pairs["a"], pairs["b"] = pairs["a_id"].map(a["name"]), pairs["b_id"].map(a["name"])
    pairs["same_genre"] = pairs["a_id"].map(a["genre"]) == pairs["b_id"].map(a["genre"])
    sig = (pairs["q"] < 0.05) & (pairs["shared"] > pairs["expected"])
    tot = nm.sum(axis=1)
    return {
        "pairs_with_shared_jurors": int((o > 0).sum()), "pairs_tested": len(keys),
        "significant_pairs": int(sig.sum()),
        "significant_pairs_cross_genre": int((sig & ~pairs["same_genre"]).sum()),
        "shared_total": int(o.sum()), "expected_total": float(tot.mean()),
        "pairs": pairs[pairs["shared"] >= MIN_SHARED].sort_values(["p", "shared"],
                                                                   ascending=[True, False])
        .reset_index(drop=True),
    }


def plot_shared_pools(pools):
    t = pools["pairs"]
    t = t[t["shared"] > t["expected"]].head(20).iloc[::-1]
    fig, ax = P.figure(9, 0.32 * len(t) + 2.4)
    y = np.arange(len(t))
    ax.hlines(y, t["expected"], t["shared"], color=P.GRID, lw=3)
    ax.scatter(t["expected"], y, s=50, color=P.MUTED, zorder=3, edgecolors=P.SURFACE,
               linewidths=1.5, label="pričakovano pri naključnih žirijah")
    sig = ((t["q"] < 0.05)).to_numpy()
    ax.scatter(t.loc[~sig, "shared"], y[~sig], s=60, color=P.ROLE_COLOR["jury"], alpha=0.45,
               zorder=4, edgecolors=P.SURFACE, linewidths=1.5, label="opaženo")
    if sig.any():
        ax.scatter(t.loc[sig, "shared"], y[sig], s=60, color=P.ROLE_COLOR["jury"], zorder=4,
                   edgecolors=P.SURFACE, linewidths=1.5, label="opaženo, značilno (q < 0,05)")
    ax.set_yticks(y, [f"{a}  ·  {b}" for a, b in zip(t["a"], t["b"])], fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("ljudje, ki so sedeli v žirijah obeh nagrad")
    ax.set_title("Nagrade si ne delijo žirantov bolj, kot bi si jih naključno")
    verdict = (f"{pools['significant_pairs']} parov je značilnih (q < 0,05)"
               if pools["significant_pairs"] else "po popravku za mnogo testov ni značilen "
               "noben par")
    P.subtitle(ax, "20 parov z največjim presežkom skupnih žirantov nad naključnimi žirijami "
                   f"istega področja in obdobja\n{verdict}\nVseh skupnih žirantov je "
                   f"{pools['shared_total']}, naključne žirije bi jih dale "
                   f"{pools['expected_total']:.0f}: žiranti ostajajo pri svoji nagradi")
    ax.legend(loc="center right", fontsize=8)
    P.source_note(fig)
    P.save(fig, THEME, "skupni_ziranti_nagrad")


# --- 3. jury stability vs award age -----------------------------------------------------

def stability_vs_age(sit) -> dict:
    s = sit[["entity_id", "award_id", "year"]].drop_duplicates()
    seats = set(zip(s["entity_id"], s["award_id"], s["year"]))
    jury_years = s.groupby("award_id")["year"].apply(set).to_dict()
    founded = frames.awards().set_index("award_id")["founded"]
    rows = []
    for e, a, y in sorted(seats):  # sorted: set order varies between runs
        known = [y - k for k in range(1, LOOKBACK + 1) if y - k in jury_years[a]]
        if not known or y < STABILITY_FROM or pd.isna(founded.get(a)):
            continue
        rows.append({"award_id": a, "year": y, "edition": f"{a}_{y}",
                     "repeat": float(any((e, a, py) in seats for py in known)),
                     "age": y - int(founded[a])})
    d = pd.DataFrame(rows)
    d = d[d["age"] >= 0]
    d["period"] = d["year"] // 5 * 5
    d["age10"] = d["age"] / 10
    res = within_stratum_slope(d, "age10", "repeat", "period", "edition", n_perm=1000)
    bands = []
    for lo, hi in AGE_BANDS:
        b = d[d["age"].between(lo, hi)]
        k, n = int(b["repeat"].sum()), len(b)
        l, h = wilson(k, n)
        bands.append({"band": f"{lo}–{hi}" if hi < 200 else f"{lo}+", "seats": n,
                      "awards": int(b["award_id"].nunique()), "share": k / n,
                      "lo": float(l), "hi": float(h)})
    res["bands"] = pd.DataFrame(bands)
    res["seats"] = len(d)
    return res


def plot_stability(st):
    b = st["bands"]
    fig, ax = P.figure(7.5, 4.4)
    x = np.arange(len(b))
    ax.bar(x, b["share"], width=0.6, color=P.ROLE_COLOR["jury"])
    ax.errorbar(x, b["share"], yerr=[b["share"] - b["lo"], b["hi"] - b["share"]], fmt="none",
                ecolor=P.TEXT_2, capsize=4, lw=1)
    for xi, (sh, n) in enumerate(zip(b["share"], b["awards"])):
        ax.text(xi, 0.02, f"{P.pct(sh)}\n{n} nagrad", ha="center", va="bottom", fontsize=8.5,
                color=P.SURFACE)
    ax.set_xticks(x, [f"{v} let" for v in b["band"]])
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("starost nagrade ob podelitvi")
    ax.set_ylabel("ponovljeni sedeži")
    ax.set_title("Ali starejše nagrade ohranjajo iste žirante?")
    slope = st["perm_slope"]
    P.subtitle(ax, f"Delež sedežev, ki jih zasede nekdo iz žirije zadnjih {LOOKBACK} let · od "
                   f"{STABILITY_FROM} · pas = 95 % interval\nV istem obdobju: "
                   f"{P.dec(100 * slope, 1, sign=True)} odstotne točke na 10 let starosti "
                   f"(p = {P.dec(st['perm_p'], 2)})")
    P.source_note(fig)
    P.save(fig, THEME, "stabilnost_zirij_in_starost_nagrade")
