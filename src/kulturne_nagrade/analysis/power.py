"""Power: who holds the jury seats, how long, and how fast juries renew.

All jury counts use jury sittings (a jury awarding several prizes at once counts once).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import wilson

THEME = "power"
PERIOD = 5
LOOKBACK = 3  # years: a seat is "repeat" if the person sat on the same award's jury recently
MIN_SEATS = 40


def run() -> dict:
    sit = frames.jury_sittings()
    roles = frames.roles()
    ren = renewal(sit)
    plot_renewal(ren)
    rep = repeat_seats(sit)
    plot_repeat_by_award(rep["per_award"])
    top = top_jurors(sit, roles)
    plot_top_jurors(top)
    load = multi_jury_load(sit)
    plot_multi_jury_load(load["series"])

    return {
        "jurors": int(sit["entity_id"].nunique()), "seats": len(sit),
        "sittings": int(sit["sitting_id"].nunique()),
        "renewal": ren, "repeat_seats": {k: v for k, v in rep.items() if k != "per_award"},
        "repeat_by_award": rep["per_award"],
        "top_jurors": top,
        "top_jurors_never_won": top.loc[top["wins"] == 0, "name"].tolist(),
        "multi_jury_load": load,
    }


def renewal(sit) -> pd.DataFrame:
    """Per period: distinct people per 100 seats, and the share of seats held by the
    10% of that period's jurors with the most seats."""
    s = sit.assign(period=sit["year"] // PERIOD * PERIOD)
    rows = []
    for period, d in s.groupby("period"):
        per_person = d.groupby("entity_id").size().sort_values(ascending=False)
        k = max(1, int(np.ceil(len(per_person) * 0.1)))
        rows.append({"period": period, "seats": len(d), "jurors": len(per_person),
                     "people_per_100_seats": 100 * len(per_person) / len(d),
                     "top10_share": per_person.iloc[:k].sum() / len(d)})
    t = pd.DataFrame(rows)
    return t[t["seats"] >= MIN_SEATS].reset_index(drop=True)


def plot_renewal(t):
    x = t["period"] + PERIOD / 2
    fig, ax = P.figure(8.5, 4.6)
    ax.plot(x, t["people_per_100_seats"], marker="o", ms=5, color=P.SERIES[0],
            markeredgecolor=P.SURFACE, markeredgewidth=1.5)
    for xi, yi, n in zip(x, t["people_per_100_seats"], t["seats"]):
        ax.annotate(f"{n}", (xi, yi), xytext=(0, -14), textcoords="offset points",
                    ha="center", fontsize=7, color=P.TEXT_2)
    ax.set_ylim(0, 100)
    ax.set_ylabel("različnih oseb na 100 sedežev")
    ax.set_title("Koliko različnih ljudi zasede žirije")
    P.subtitle(ax, "100 = vsak sedež v obdobju zasede druga oseba · številke pod točkami = "
                   f"sedeži v obdobju (vsaj {MIN_SEATS})")
    P.source_note(fig)
    P.save(fig, THEME, "obnavljanje_zirij")


def repeat_seats(sit) -> dict:
    """Share of an award's jury seats held by someone who sat on that award's jury in the
    previous LOOKBACK years. Only seats where the award's jury is known for all of those
    years count, so coverage gaps do not pass for rotation."""
    s = sit[["entity_id", "award_id", "award", "year"]].drop_duplicates()
    seats = set(zip(s["entity_id"], s["award_id"], s["year"]))
    jury_years = s.groupby("award_id")["year"].apply(set).to_dict()
    rows = []
    for e, a, y in seats:
        prev_years = [y - k for k in range(1, LOOKBACK + 1)]
        known = [py for py in prev_years if py in jury_years[a]]
        if not known:
            continue  # award not judged (or not recorded) in the lookback window
        rows.append((a, y, any((e, a, py) in seats for py in known)))
    d = pd.DataFrame(rows, columns=["award_id", "year", "repeat"])
    per = d.groupby("award_id").agg(seats=("repeat", "size"), repeat=("repeat", "sum"))
    per = per[per["seats"] >= 15]
    per["share"] = per["repeat"] / per["seats"]
    per["lo"], per["hi"] = wilson(per["repeat"], per["seats"])
    per = per.join(frames.awards().set_index("award_id")["name"].rename("award"))
    by_period = d.assign(period=d["year"] // 10 * 10).groupby("period")["repeat"].agg(["size", "mean"])
    return {"overall": float(d["repeat"].mean()), "seats": len(d),
            "by_decade": by_period.reset_index(),
            "per_award": per.sort_values("share").reset_index()}


def plot_repeat_by_award(per):
    fig, ax = P.figure(8.5, 0.26 * len(per) + 1.8)
    y = np.arange(len(per))
    ax.hlines(y, per["lo"], per["hi"], color="#b7d3f6", lw=3)
    ax.scatter(per["share"], y, s=36, color=P.SERIES[0], zorder=3, edgecolors=P.SURFACE,
               linewidths=1.5)
    ax.set_yticks(y, per["award"], fontsize=8)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.grid(axis="y", visible=False)
    ax.set_title("Kako zaprte so žirije: ponovni sedeži")
    P.subtitle(ax, f"Delež sedežev, ki jih zasede nekdo, ki je v žiriji iste nagrade sedel v "
                   f"zadnjih {LOOKBACK} letih\nčrta = 95 % interval zaupanja · nagrade z vsaj 15 "
                   "takimi sedeži")
    P.source_note(fig)
    P.save(fig, THEME, "ponovni_sedezi_po_nagradah")


def top_jurors(sit, roles, n: int = 25) -> pd.DataFrame:
    g = sit.groupby(["entity_id", "name"]).agg(
        seats=("sitting_id", "size"), awards=("award_id", "nunique"),
        first=("year", "min"), last=("year", "max"), gender=("gender", "first"))
    wins = roles[roles["role"] == "winner"].groupby("entity_id").size().rename("wins")
    g = g.join(wins, on="entity_id").fillna({"wins": 0})
    g["wins"] = g["wins"].astype(int)
    return g.sort_values(["seats", "awards"], ascending=False).head(n).reset_index()


def plot_top_jurors(t):
    t = t.iloc[::-1]
    fig, ax = P.figure(8.5, 0.3 * len(t) + 1.8)
    y = np.arange(len(t))
    colors = [P.SERIES[6] if w == 0 else P.SERIES[0] for w in t["wins"]]
    ax.barh(y, t["seats"], height=0.6, color=colors)
    for yi, (s, a, f, la) in enumerate(zip(t["seats"], t["awards"], t["first"], t["last"])):
        where = "pri 1 nagradi" if a == 1 else f"pri {a} nagradah"
        ax.text(s + 0.4, yi, f"{s}  ·  {where}  ·  {f}–{la}", va="center", fontsize=8,
                color=P.TEXT_2)
    ax.set_yticks(y, t["name"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, t["seats"].max() * 1.45)
    ax.set_xlabel("sedeži v žirijah")
    ax.set_title("Najbolj zasedeni žiranti")
    P.subtitle(ax, "Vijolično: v zbirki nimajo nobene nagrade · žirija, ki podeli več nagrad "
                   "hkrati, šteje enkrat")
    P.source_note(fig)
    P.save(fig, THEME, "najbolj_zasedeni_ziranti")


def multi_jury_load(sit) -> dict:
    """How many seats go to people sitting on two or more juries in the same year."""
    per = sit.groupby(["entity_id", "year"]).size().rename("n").reset_index()
    s = sit.merge(per, on=["entity_id", "year"])
    s["period"] = s["year"] // PERIOD * PERIOD
    series = s.groupby("period").agg(seats=("n", "size"), multi=("n", lambda v: (v >= 2).mean()))
    series = series[series["seats"] >= MIN_SEATS].reset_index()
    busiest = per.sort_values("n", ascending=False).head(10).merge(
        frames.entities()[["entity_id", "name"]])
    return {"series": series, "max_in_one_year": busiest[["name", "year", "n"]],
            "share_multi_since_2010": float(s.loc[s["year"] >= 2010, "n"].ge(2).mean())}


def plot_multi_jury_load(t):
    x = t["period"] + PERIOD / 2
    fig, ax = P.figure(8.5, 4.4)
    ax.plot(x, t["multi"], marker="o", ms=5, color=P.SERIES[0], markeredgecolor=P.SURFACE,
            markeredgewidth=1.5)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_ylim(0, max(0.5, t["multi"].max() * 1.2))
    ax.set_title("Žiranti z več žirijami v istem letu")
    P.subtitle(ax, "Delež sedežev, ki jih zasedejo ljudje, ki so isto leto še v vsaj eni drugi "
                   "žiriji")
    P.source_note(fig)
    P.save(fig, THEME, "vec_zirij_hkrati")

