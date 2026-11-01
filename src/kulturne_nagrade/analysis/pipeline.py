"""The pipeline: jury -> winner. Do new juries pick newcomers?

x = share of an edition's jurors who had not sat on the same award's jury in the
previous LOOKBACK years; y = winner had no earlier win in the data. Within award x
decade, permutation null (common helper).

The commission tier (commission -> jury) was dropped on 2026-11-01: the commission
records were not reliable (recorded "terms" were often board-membership spans).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import within_stratum_slope

THEME = "pipeline"
NEWCOMER_FROM = 2005  # a 15-year lookback from 1990 for "no earlier win"
LOOKBACK = 3
N_PERM = 2000


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    newc = new_juries_newcomers(roles, sit)
    plot_newcomers(newc)
    return {"new_juries_newcomers": {k: v for k, v in newc.items() if k != "null"}}


# --- new juries and newcomers -----------------------------------------------------------

def new_juries_newcomers(roles, sit) -> dict:
    seats = sit.explode("awards")[["entity_id", "awards", "year", "sitting_id"]].rename(
        columns={"awards": "award_id"})
    seat_set = set(zip(seats["entity_id"], seats["award_id"], seats["year"]))
    jury_years = seats.groupby("award_id")["year"].agg(set).to_dict()
    jur = roles[roles["role"] == "jury"][["edition_id", "entity_id", "award_id", "year"]]
    rows = []
    for (ed, a, y), g in jur.groupby(["edition_id", "award_id", "year"]):
        known = [y - k for k in range(1, LOOKBACK + 1) if y - k in jury_years.get(a, ())]
        if not known or len(g) < 3:
            continue
        new = [not any((e, a, py) in seat_set for py in known) for e in g["entity_id"]]
        rows.append({"edition_id": ed, "jury_new": float(np.mean(new))})
    jn = pd.DataFrame(rows)
    w = roles[roles["role"] == "winner"]
    first_win = w.groupby("entity_id")["year"].min()
    d = w[w["year"] >= NEWCOMER_FROM].merge(jn, on="edition_id")
    d = d.drop_duplicates(["edition_id", "entity_id"]).copy()
    d["y"] = (d["entity_id"].map(first_win) == d["year"]).astype(float)
    d["stratum"] = d["award_id"] + "_" + (d["year"] // 10 * 10).astype(str)
    res = within_stratum_slope(d, "jury_new", "y", "stratum", "edition_id", n_perm=N_PERM)
    res["newcomer_share"] = float(d["y"].mean())
    res["mean_jury_new"] = float(d["jury_new"].mean())
    return res


def plot_newcomers(h):
    fig, ax = P.figure(8, 4.4)
    ax.hist(h["null"], bins=40, color="#b7d3f6", edgecolor=P.SURFACE, linewidth=1)
    top = ax.get_ylim()[1]
    ax.axvline(h["perm_slope"], color=P.SERIES[7], lw=2)
    ax.annotate(f"opaženo: {P.dec(h['perm_slope'], 2, sign=True)}\np = {P.dec(h['perm_p'], 2)}",
                (h["perm_slope"], top * 0.85), xytext=(8, 0), textcoords="offset points",
                fontsize=9, color=P.TEXT)
    ax.axvline(h["raw_slope"], color=P.MUTED, lw=1.5)
    ax.annotate(f"brez kontrol: {P.dec(h['raw_slope'], 2, sign=True)}",
                (h["raw_slope"], top * 0.6), xytext=(8, 0), textcoords="offset points",
                fontsize=9, color=P.TEXT_2)
    ax.xaxis.set_major_formatter(lambda v, _: P.dec(v, 2))
    ax.set_xlabel("sprememba verjetnosti, da zmaga nekdo brez prejšnje nagrade, če je žirija "
                  "v celoti nova\nnamesto v celoti ista kot v zadnjih letih")
    ax.set_ylabel("permutacije")
    ax.grid(axis="y", visible=False)
    ax.set_title("Ali nove žirije nagrajujejo nove obraze?")
    P.subtitle(ax, "Primerjava znotraj iste nagrade in desetletja · histogram = naključno "
                   f"premešane žirije ({N_PERM}×)\n{h['n_winners']} nagrajencev od "
                   f"{NEWCOMER_FROM}, {h['n_editions']} podelitev, {h['n_awards']} nagrad")
    P.source_note(fig)
    P.save(fig, THEME, "nove_zirije_novi_obrazi")
