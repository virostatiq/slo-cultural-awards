"""Influence: does sitting on a jury carry over to other people's careers and other awards?

1. Kingmakers. For every juror with at least MIN_SITTINGS sittings: do the winners of
   their panels go on to sit on juries (within LATER_YEARS) more often than winners of
   the same award in nearby years (±WINDOW) from editions the juror did not judge?
   Only winners without an earlier seat count, and only wins up to end − LATER_YEARS, so
   everyone has the full window (no censoring). Each panel winner's baseline is the rate
   among those comparison winners; the null draws each panel winner's outcome from that
   baseline (Poisson-binomial, simulated). Two-sided p, BH across jurors. Jurors who sat
   together share panel winners, so their results are not independent.

2. Jury of X → win of Y. Extends the insider premium (juries §3) beyond the same award:
   for award pairs, winners of Y who earlier sat on X's jury, against the count expected
   if award labels were shuffled among the winners of each (genre, year) pool. Do people
   who judged X win Y rather than a peer award of the same field and year?

Legacy: plots 17 and 61–66 (kingmakers; no comparison group, open-ended windows) and
40/50 (cross-award flows; raw counts, no expected values).
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import bh_fdr, rng

THEME = "influence"
MIN_SITTINGS = 10
LATER_YEARS = 10
WINDOW = 5
MIN_TESTED = 10      # panel winners with a baseline, per juror
PRIOR_WEIGHT = 5     # baseline shrinkage toward the overall rate (pseudo-winners)
N_SIM = 5000
MIN_PAIR_OBS = 3


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    king = kingmakers(roles, sit)
    plot_kingmakers(king)
    cross = cross_award(roles)
    plot_cross_award(cross)
    return {
        "kingmakers": {k: v for k, v in king.items() if k != "table"},
        "kingmakers_table": king["table"],
        "cross_award": {k: v for k, v in cross.items() if k != "pairs"},
        "cross_award_pairs": cross["pairs"],
    }


# --- 1. kingmakers ----------------------------------------------------------------------

def kingmakers(roles, sit) -> dict:
    end = int(roles["year"].max()) - LATER_YEARS
    first_seat = sit.groupby("entity_id")["year"].min()
    jury = roles[roles["role"] == "jury"][["edition_id", "entity_id"]]
    w = roles[(roles["role"] == "winner") & (roles["year"] <= end)][
        ["edition_id", "entity_id", "award_id", "year"]].drop_duplicates(
        ["edition_id", "entity_id"])
    fs = w["entity_id"].map(first_seat)
    w = w[~(fs <= w["year"]).fillna(False).astype(bool)].copy()  # no seat before the win
    fs = w["entity_id"].map(first_seat)
    w["later"] = ((fs > w["year"]) & (fs <= w["year"] + LATER_YEARS)).fillna(False).astype(bool)

    base_rate = float(w["later"].mean())
    judges = jury.groupby("entity_id")["edition_id"].agg(set)
    busy = sit.groupby("entity_id").size()
    busy = busy[busy >= MIN_SITTINGS]
    names = frames.entities().set_index("entity_id")["name"]
    by_award = {a: d for a, d in w.groupby("award_id")}
    g = rng()
    rows = []
    for j in busy.index:
        eds = judges.get(j, set())
        mine = w[w["edition_id"].isin(eds)].sort_values("year").drop_duplicates("entity_id")
        p_base, obs = [], []
        for r in mine.itertuples():
            c = by_award[r.award_id]
            c = c[(~c["edition_id"].isin(eds)) & c["year"].between(r.year - WINDOW,
                                                                     r.year + WINDOW)]
            c = c[c["entity_id"] != r.entity_id]
            if len(c) < 3:
                continue
            # small comparison groups are shrunk toward the overall rate, so a group
            # that happens to have no later jurors does not make one look impossible
            p_base.append((c["later"].sum() + PRIOR_WEIGHT * base_rate)
                          / (len(c) + PRIOR_WEIGHT))
            obs.append(r.later)
        if len(obs) < MIN_TESTED:
            continue
        p_base = np.array(p_base)
        o, e = int(np.sum(obs)), float(p_base.sum())
        sims = (g.random((N_SIM, len(p_base))) < p_base).sum(axis=1)
        p_hi = (1 + (sims >= o).sum()) / (N_SIM + 1)
        p_lo = (1 + (sims <= o).sum()) / (N_SIM + 1)
        rows.append({"entity_id": j, "name": names.get(j, j), "sittings": int(busy[j]),
                     "panel_winners": len(mine), "tested": len(obs), "later_jurors": o,
                     "expected": e, "ratio": o / e if e else np.nan,
                     "p": min(1.0, 2 * min(p_hi, p_lo))})
    t = pd.DataFrame(rows)
    t["q"] = bh_fdr(t["p"])
    t = t.sort_values("p").reset_index(drop=True)
    return {
        "jurors_tested": len(t), "min_sittings": MIN_SITTINGS, "wins_up_to": end,
        "overall_later_jury_rate": base_rate,
        "panel_winners_tested": int(t["tested"].sum()),
        "observed_total": int(t["later_jurors"].sum()),
        "expected_total": float(t["expected"].sum()),
        "significant_more": t.loc[(t["q"] < 0.05) & (t["ratio"] > 1), "name"].tolist(),
        "significant_fewer": t.loc[(t["q"] < 0.05) & (t["ratio"] < 1), "name"].tolist(),
        "table": t,
    }


def plot_kingmakers(k):
    t = k["table"].sort_values("expected", ascending=False).head(30).sort_values("ratio")
    fig, ax = P.figure(8.5, 0.3 * len(t) + 2.2)
    y = np.arange(len(t))
    ax.hlines(y, t["expected"], t["later_jurors"], color=P.GRID, lw=3)
    ax.scatter(t["expected"], y, s=50, color=P.MUTED, zorder=3, edgecolors=P.SURFACE,
               linewidths=1.5, label="pričakovano (ista nagrada, sosednja leta)")
    sig = (t["q"] < 0.05).to_numpy()
    ax.scatter(t.loc[~sig, "later_jurors"], y[~sig], s=60, color=P.ROLE_COLOR["jury"],
               alpha=0.45, zorder=4, edgecolors=P.SURFACE, linewidths=1.5, label="opaženo")
    if sig.any():
        ax.scatter(t.loc[sig, "later_jurors"], y[sig], s=60, color=P.ROLE_COLOR["jury"],
                   zorder=4, edgecolors=P.SURFACE, linewidths=1.5,
                   label="opaženo, značilno (q < 0,05)")
    ax.set_yticks(y, t["name"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"nagrajenci njihovih žirij, ki so v {LATER_YEARS} letih sami sedli v žirijo")
    ax.set_title("Ali žirije nekaterih žirantov »ustvarjajo« nove žirante?")
    P.subtitle(ax, f"30 žirantov z največ preverljivimi nagrajenci · nagrade do leta "
                   f"{k['wins_up_to']}, nagrajenci brez prejšnjega sedeža\nPrimerjava: "
                   f"nagrajenci iste nagrade ±{WINDOW} let, ki jih žirant ni izbral")
    ax.legend(loc="lower right", fontsize=8)
    P.source_note(fig)
    P.save(fig, THEME, "kraljevi_ustvarjalci")


# --- 2. jury of X -> win of Y -----------------------------------------------------------

def cross_award(roles) -> dict:
    """Within a (genre, year) pool, shuffling award labels makes the number of X-jurors
    among Y's winners hypergeometric (pool size, X-jurors in the pool, Y's winners).
    Pools are independent, so the exact null of the total is the convolution of those
    pmfs: exact p-values, with no Monte Carlo floor. The same-award diagonal is juries §3;
    the cross-award total is its mirror image (a fixed number of earlier seats is split
    between "own award" and "other awards"), so only pairs are tested.

    Seats are sittings, filed under the sitting's main award, so a jury that decides
    several prizes (ZDUS, Prešeren) is one X, not four. A winner of Y counts for X only
    if they never sat on a jury that decided Y: those wins are the insider premium."""
    sit = frames.jury_sittings()
    first_x = sit.groupby(["entity_id", "award_id"])["year"].min()
    first_any = sit.explode("awards").groupby(["entity_id", "awards"])["year"].min()
    seats, decided = {}, {}
    for (e, a), y in first_x.items():
        seats.setdefault(e, []).append((a, int(y)))
    for (e, a), y in first_any.items():
        decided.setdefault(e, []).append((a, int(y)))
    w = roles[roles["role"] == "winner"][["entity_id", "award_id", "genre", "year"]]
    w = w.drop_duplicates(["entity_id", "award_id", "year"]).reset_index(drop=True)
    obs, parts = defaultdict(int), defaultdict(list)
    for (_, year), grp in w.groupby(["genre", "year"]):
        labels = grp["award_id"].to_numpy()
        present, n_y = np.unique(labels, return_counts=True)
        if len(present) < 2:
            continue
        n = len(labels)
        held = [{a for a, y in seats.get(e, ()) if y < year} for e in grp["entity_id"]]
        dec = [{a for a, y in decided.get(e, ()) if y < year} for e in grp["entity_id"]]
        for x in set().union(*held):
            for y_aw, ny in zip(present, n_y):
                if y_aw == x:
                    continue
                has = np.array([x in h and y_aw not in d for h, d in zip(held, dec)])
                k = int(has.sum())
                if not k:
                    continue
                parts[(x, y_aw)].append((n, k, int(ny)))
                obs[(x, y_aw)] += int(has[labels == y_aw].sum())
    rows = []
    for (x, y_aw), ps in parts.items():
        pmf = np.array([1.0])
        for n, k, ny in ps:
            pmf = np.convolve(pmf, hypergeom.pmf(np.arange(min(k, ny) + 1), n, k, ny))
        o = obs[(x, y_aw)]
        rows.append({"jury_award_id": x, "win_award_id": y_aw, "observed": o,
                     "expected": float(sum(ny * k / n for n, k, ny in ps)),
                     "p": float(min(1.0, pmf[o:].sum()))})
    pairs = pd.DataFrame(rows)
    pairs["q"] = bh_fdr(pairs["p"])
    pairs["ratio"] = pairs["observed"] / pairs["expected"]
    nm = frames.awards().set_index("award_id")["name"]
    pairs["jury_award"] = pairs["jury_award_id"].map(nm)
    pairs["win_award"] = pairs["win_award_id"].map(nm)
    sig = (pairs["q"] < 0.05) & (pairs["ratio"] > 1)
    return {
        "pairs_tested": len(pairs), "significant_pairs": int(sig.sum()),
        "pairs": pairs[pairs["observed"] >= MIN_PAIR_OBS].sort_values("p")
        .reset_index(drop=True),
    }


def plot_cross_award(c):
    t = c["pairs"]
    t = t[(t["q"] < 0.05) & (t["ratio"] > 1)].head(25).iloc[::-1]
    if t.empty:
        t = c["pairs"].head(15).iloc[::-1]
    fig, ax = P.figure(9, 0.32 * len(t) + 2.2)
    y = np.arange(len(t))
    ax.hlines(y, t["expected"], t["observed"], color=P.GRID, lw=3)
    ax.scatter(t["expected"], y, s=50, color=P.MUTED, zorder=3, edgecolors=P.SURFACE,
               linewidths=1.5, label="pričakovano pri vrstnikih")
    ax.scatter(t["observed"], y, s=60, color=P.ROLE_COLOR["winner"], zorder=4,
               edgecolors=P.SURFACE, linewidths=1.5, label="opaženo")
    ax.set_yticks(y, [f"{a}  →  {b}" for a, b in zip(t["jury_award"], t["win_award"])],
                  fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("nagrajenci, ki so prej sedeli v žiriji prve nagrade")
    ax.set_title("Iz žirije ene nagrade do zmage pri drugi")
    P.subtitle(ax, "Pari nagrad, kjer nagrado (desno) pogosteje dobijo nekdanji žiranti druge "
                   "nagrade (levo),\nkot bi pričakovali pri nagrajencih drugih nagrad istega "
                   f"področja in leta · q < 0,05 · {c['significant_pairs']} od "
                   f"{c['pairs_tested']} preverjenih parov")
    ax.legend(loc="lower right", fontsize=8)
    P.source_note(fig)
    P.save(fig, THEME, "iz_zirije_v_drugo_nagrado")
