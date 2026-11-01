"""Gender: who wins, who judges, who appoints, and whether juries favour their own.

Gender comes from search-grounded LLM enrichment (persons only, ~99% known).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import wilson, within_stratum_slope

THEME = "gender"
PERIOD = 5  # years per bin in time series
MIN_N = 30  # minimum people-in-role per bin to plot a point
N_PERM = 2000


def run() -> dict:
    roles = frames.roles()
    winners = roles[(roles["role"] == "winner") & roles["gender"].notna()]
    jury = frames.jury_sittings()
    jury = jury[jury["gender"].notna()]
    ts = shares_over_time(winners, jury)
    plot_shares_over_time(ts)
    prestige = by_prestige(winners)
    plot_by_prestige(prestige)
    genre = by_genre(winners, jury, since=2010)
    plot_by_genre(genre)
    homo = homophily(roles)
    plot_homophily(homo)

    recent = lambda df: df[df["year"] >= 2016]
    return {
        "female_share_winners_all": float((winners["gender"] == "f").mean()),
        "female_share_jury_all": float((jury["gender"] == "f").mean()),
        "female_share_2016_on": {
            "winners": float((recent(winners)["gender"] == "f").mean()),
            "jury": float((recent(jury)["gender"] == "f").mean()),
        },
        "time_series": ts,
        "by_prestige": prestige,
        "top_prestige_gap_since_2010": top_prestige_gap(roles),
        "by_genre_since_2010": genre,
        "homophily": {k: v for k, v in homo.items() if k != "null"},
    }


def shares_over_time(winners, jury) -> pd.DataFrame:
    out = []
    for role, df in (("winner", winners), ("jury", jury)):
        g = df.assign(period=df["year"] // PERIOD * PERIOD).groupby("period")["gender"]
        t = pd.DataFrame({"n": g.size(), "f": g.apply(lambda s: (s == "f").sum())})
        t["share"] = t["f"] / t["n"]
        t["lo"], t["hi"] = wilson(t["f"], t["n"])
        out.append(t.reset_index().assign(role=role))
    return pd.concat(out, ignore_index=True)


def plot_shares_over_time(ts):
    fig, ax = P.figure(9, 5)
    colors = P.ROLE_COLOR
    labelled: list[float] = []
    for role in ("winner", "jury"):
        d = ts[(ts["role"] == role) & (ts["n"] >= MIN_N)]
        x = d["period"] + PERIOD / 2
        ax.fill_between(x, d["lo"], d["hi"], color=colors[role], alpha=0.12, lw=0)
        ax.plot(x, d["share"], color=colors[role], marker="o", ms=5,
                markeredgecolor=P.SURFACE, markeredgewidth=1.5, label=P.ROLE_LABEL[role])
        last = d.iloc[-1]
        if any(abs(last["share"] - v) < 0.04 for v in labelled):
            continue  # would collide; the legend carries identity
        labelled.append(last["share"])
        ax.annotate(P.pct(last['share']), (x.iloc[-1], last["share"]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=P.TEXT)
    ax.axhline(0.5, color=P.TEXT_2, lw=0.8)
    ax.text(ax.get_xlim()[0], 0.505, " enakost", fontsize=8, color=P.TEXT_2, va="bottom")
    ax.set_ylim(0, 0.75)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_title("Delež žensk med nagrajenci in v žirijah")
    P.subtitle(ax, f"Petletna obdobja z vsaj {MIN_N} osebami · pas = 95 % interval zaupanja · "
                   "žirija, ki podeli več nagrad hkrati, šteje enkrat")
    ax.legend(loc="upper left")
    P.source_note(fig)
    P.save(fig, THEME, "delez_zensk_skozi_cas")


def by_prestige(winners) -> pd.DataFrame:
    w = winners[winners["year"] >= 1991].copy()
    w["period"] = np.where(w["year"] >= 2010, "2010–", "1991–2009")
    g = w.groupby(["period", "prestige"])["gender"]
    t = pd.DataFrame({"n": g.size(), "f": g.apply(lambda s: (s == "f").sum())}).reset_index()
    t["share"] = t["f"] / t["n"]
    t["lo"], t["hi"] = wilson(t["f"], t["n"])
    return t


def top_prestige_gap(roles) -> dict:
    """Are women less likely to win the top-prestige (5) awards, since 2010?

    Linear probability model with birth-decade and genre controls; SE clustered by
    award, since there are only about a dozen prestige-5 awards."""
    w = roles[(roles["role"] == "winner") & (roles["year"] >= 2010)
              & roles["gender"].notna() & roles["year_birth"].notna()].copy()
    w["f"] = (w["gender"] == "f").astype(float)
    w["top"] = (w["prestige"] == 5).astype(float)
    w["cohort"] = (w["year_birth"] // 10 * 10).astype(int)
    out = {"n": len(w)}
    for name, formula in (("raw", "f ~ top"), ("controlled", "f ~ top + C(cohort) + C(genre)")):
        m = smf.ols(formula, w).fit(cov_type="cluster", cov_kwds={"groups": w["award_id"]})
        out[name] = {"diff": float(m.params["top"]), "p": float(m.pvalues["top"]),
                     "ci": [float(v) for v in m.conf_int().loc["top"]]}
    return out


def plot_by_prestige(t):
    fig, ax = P.figure(8, 4.6)
    for i, (period, d) in enumerate(t.groupby("period")):
        x = d["prestige"] + (i - 0.5) * 0.18
        ax.errorbar(x, d["share"], yerr=[d["share"] - d["lo"], d["hi"] - d["share"]],
                    fmt="o", color=P.SERIES[i], ms=7, elinewidth=1.5, capsize=0,
                    markeredgecolor=P.SURFACE, markeredgewidth=1.5, label=period)
    ax.axhline(0.5, color=P.TEXT_2, lw=0.8)
    ax.set_xticks([2, 3, 4, 5], ["2", "3", "4", "5\n(najvišji)"])
    ax.set_xlabel("ugled nagrade")
    ax.set_ylim(0, 0.75)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_title("Ženske med nagrajenci glede na ugled nagrade")
    P.subtitle(ax, "Ugled 2–5 je ročna ocena · navpične črte = 95 % interval zaupanja · razlika "
                   "pri ugledu 5 ni statistično značilna,\nko upoštevamo nagrado, generacijo in "
                   "področje")
    ax.legend(loc="upper right", title="obdobje")
    P.source_note(fig)
    P.save(fig, THEME, "delez_zensk_po_ugledu")


def by_genre(winners, jury, since: int) -> pd.DataFrame:
    def share(df, role):
        d = df[df["year"] >= since].groupby("genre")["gender"]
        return pd.DataFrame({f"{role}_n": d.size(), f"{role}_share": d.apply(
            lambda s: (s == "f").mean())})
    t = share(winners, "winner").join(share(jury, "jury"), how="inner")
    t = t[(t["winner_n"] >= MIN_N) & (t["jury_n"] >= MIN_N)]
    return t.sort_values("winner_share").reset_index()


def plot_by_genre(t):
    fig, ax = P.figure(8, 0.5 * len(t) + 1.6)
    y = np.arange(len(t))
    ax.hlines(y, t[["winner_share", "jury_share"]].min(axis=1),
              t[["winner_share", "jury_share"]].max(axis=1), color=P.GRID, lw=3)
    ax.scatter(t["jury_share"], y, s=70, color=P.SERIES[1], zorder=3, label="žirija",
               edgecolors=P.SURFACE, linewidths=1.5)
    ax.scatter(t["winner_share"], y, s=70, color=P.SERIES[0], zorder=3, label="nagrajenci",
               edgecolors=P.SURFACE, linewidths=1.5)
    ax.axvline(0.5, color=P.TEXT_2, lw=0.8)
    ax.set_yticks(y, t["genre"])
    ax.set_xlim(0, 0.8)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.grid(axis="y", visible=False)
    ax.set_title("Delež žensk po področjih, od leta 2010")
    P.subtitle(ax, f"Področja z vsaj {MIN_N} nagrajenci in {MIN_N} sedeži v žirijah")
    ax.legend(loc="lower right")
    P.source_note(fig)
    P.save(fig, THEME, "delez_zensk_po_podrocjih")


def homophily(roles) -> dict:
    """Do juries with more women pick more women?

    Unit: a winner in an edition with a known jury. x = female share of that edition's
    jury, y = winner is a woman. Both the jury's and the winners' gender mix drift
    over time and differ by field, so a raw correlation is confounded. The estimate is
    within award × decade (fixed effects, cluster-robust SE by award), and the
    permutation null shuffles juries between editions of the same award and decade.
    """
    jur = (roles[(roles["role"] == "jury") & roles["gender"].notna()]
           .groupby("edition_id")["gender"].agg(jury_f=lambda s: (s == "f").mean(),
                                                jury_n="size"))
    w = roles[(roles["role"] == "winner") & roles["gender"].notna()]
    d = w.merge(jur, left_on="edition_id", right_index=True)
    d = d[d["jury_n"] >= 3].copy()
    d["y"] = (d["gender"] == "f").astype(float)
    d["stratum"] = d["award_id"] + "_" + (d["year"] // 10 * 10).astype(str)
    # Keep strata with variation in both x and y; others carry no within information.
    var = d.groupby("stratum").agg(xv=("jury_f", "nunique"), yv=("y", "nunique"))
    d = d[d["stratum"].isin(var[(var["xv"] > 1) & (var["yv"] > 1)].index)].reset_index(drop=True)

    res = within_stratum_slope(d, "jury_f", "y", "stratum", "edition_id", n_perm=N_PERM)

    # Descriptive: P(female winner) by jury majority, within-stratum adjusted.
    d["jury_majority_f"] = d["jury_f"] > 0.5
    return {
        **res,
        "share_f_winner_jury_majority_f": float(d.loc[d["jury_majority_f"], "y"].mean()),
        "share_f_winner_jury_majority_m": float(d.loc[~d["jury_majority_f"], "y"].mean()),
    }


def plot_homophily(h):
    fig, ax = P.figure(8, 4.4)
    ax.hist(h["null"], bins=40, color="#b7d3f6", edgecolor=P.SURFACE, linewidth=1)
    ax.axvline(h["perm_slope"], color=P.SERIES[1], lw=2)
    ax.annotate(f"opaženo: {P.dec(h['perm_slope'], 2, sign=True)}\np = {P.dec(h['perm_p'], 2)}",
                (h["perm_slope"], ax.get_ylim()[1] * 0.85), xytext=(8, 0),
                textcoords="offset points", fontsize=9, color=P.TEXT)
    ax.axvline(h["raw_slope"], color=P.MUTED, lw=1.5, ls="-")
    ax.annotate(f"brez kontrol: {P.dec(h['raw_slope'], 2, sign=True)}", (h["raw_slope"], ax.get_ylim()[1] * 0.6),
                xytext=(8, 0), textcoords="offset points", fontsize=9, color=P.TEXT_2)
    ax.set_xlabel("sprememba verjetnosti, da zmaga ženska, če je žirija v celoti ženska "
                  "namesto v celoti moška")
    ax.set_ylabel("permutacije")
    ax.grid(axis="y", visible=False)
    ax.set_title("Ali žirije z več ženskami nagrajujejo več žensk?")
    P.subtitle(ax, "Primerjava znotraj iste nagrade in desetletja · histogram = naključno "
                   f"premešane žirije ({N_PERM}×)\n{h['n_winners']} nagrajencev, "
                   f"{h['n_editions']} podelitev, {h['n_awards']} nagrad")
    P.source_note(fig)
    P.save(fig, THEME, "homofilija_zirij")
