"""Age: how old people are when they win and when they judge.

Only sourced birth years are used (never the statistical estimate, which is itself
derived from award timing). Posthumous credits are excluded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import kaplan_meier, km_at, within_stratum_slope

THEME = "age"
PERIOD = 5
MIN_N = 30
MIN_PER_AWARD = 15
ROBUST_SOURCES = ("wikidata", "viaf")


def run() -> dict:
    roles = frames.roles()
    winners = roles[(roles["role"] == "winner") & roles["age"].notna()]
    jury = frames.jury_sittings()
    jury = jury[jury["age"].notna()]

    per_award = by_award(winners)
    plot_by_award(per_award)
    trend = age_trend(winners)
    plot_trend(trend)
    gap = jury_winner_gap(winners, jury)
    plot_jury_winner_gap(gap)
    gap_ed = gap_within_award(roles)
    gender_gap = gender_age_gap(winners)
    late = honoured_late(roles)
    plot_honoured_late(late)

    return {
        "n_winner_ages": len(winners),
        "winner_age_coverage": float(roles.loc[roles["role"] == "winner", "age"].notna().mean()),
        "median_age_winner": float(winners["age"].median()),
        "median_age_jury": float(jury["age"].median()),
        "by_award": per_award,
        "trend": {k: v for k, v in trend.items() if k != "series"},
        "trend_series": trend["series"],
        "jury_winner_gap": gap,
        "jury_winner_gap_within_award": {k: v for k, v in gap_ed.items() if k != "null"},
        "gender_age_gap": gender_gap,
        "honoured_late": late,
        "youngest_awards": per_award.nsmallest(5, "median")[["award", "median", "n"]],
        "oldest_awards": per_award.nlargest(5, "median")[["award", "median", "n"]],
    }


def by_award(winners) -> pd.DataFrame:
    g = winners.groupby(["award_id", "award", "genre"])["age"]
    t = pd.DataFrame({"n": g.size(), "median": g.median(), "q1": g.quantile(0.25),
                      "q3": g.quantile(0.75)}).reset_index()
    return t[t["n"] >= MIN_PER_AWARD].sort_values("median").reset_index(drop=True)


def plot_by_award(t):
    fig, ax = P.figure(8.5, 0.26 * len(t) + 1.8)
    y = np.arange(len(t))
    ax.hlines(y, t["q1"], t["q3"], color="#b7d3f6", lw=4, capstyle="round")
    ax.scatter(t["median"], y, s=36, color=P.SERIES[0], zorder=3,
               edgecolors=P.SURFACE, linewidths=1.5)
    ax.set_yticks(y, t["award"], fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("starost ob nagradi (leta)")
    ax.set_title("Pri kateri starosti nagrade najdejo nagrajence")
    P.subtitle(ax, f"Pika = mediana, črta = srednja polovica nagrajencev · nagrade z vsaj "
                   f"{MIN_PER_AWARD} nagrajenci z znano letnico rojstva")
    P.source_note(fig)
    P.save(fig, THEME, "starost_po_nagradah")


def age_trend(winners) -> dict:
    """Raw trend in age at win vs the trend within the same award.

    The raw trend mixes two things: awards getting older winners, and the award mix
    shifting (lifetime prizes early in the data, youth prizes added later). The
    within-award trend (award fixed effects) isolates the first. Re-estimated on
    Wikidata/VIAF ages only as a robustness check against LLM-reported ages.
    """
    w = winners[winners["year"] >= 1960].copy()
    w["decades"] = (w["year"] - 2000) / 10
    out = {"n": len(w)}
    for name, df in (("all", w), ("robust", w[w["year_birth_source"].isin(ROBUST_SOURCES)])):
        raw = smf.ols("age ~ decades", df).fit(cov_type="cluster",
                                               cov_kwds={"groups": df["award_id"]})
        fe = smf.ols("age ~ decades + C(award_id)", df).fit(
            cov_type="cluster", cov_kwds={"groups": df["award_id"]})
        out[name] = {"n": len(df),
                     "raw_per_decade": float(raw.params["decades"]),
                     "raw_ci": [float(v) for v in raw.conf_int().loc["decades"]],
                     "within_award_per_decade": float(fe.params["decades"]),
                     "within_ci": [float(v) for v in fe.conf_int().loc["decades"]],
                     "within_p": float(fe.pvalues["decades"])}
    # Series for plotting: raw median, and age relative to the award's own mean.
    w["rel"] = w["age"] - w.groupby("award_id")["age"].transform("mean") + w["age"].mean()
    w["period"] = w["year"] // PERIOD * PERIOD
    s = w.groupby("period").agg(n=("age", "size"), raw=("age", "median"), within=("rel", "median"))
    out["series"] = s[s["n"] >= MIN_N].reset_index()
    return out


def plot_trend(t):
    s = t["series"]
    x = s["period"] + PERIOD / 2
    fig, ax = P.figure(8.5, 4.8)
    ax.plot(x, s["raw"], color=P.MUTED, marker="o", ms=5, label="vsi nagrajenci (surovo)",
            markeredgecolor=P.SURFACE, markeredgewidth=1.5)
    ax.plot(x, s["within"], color=P.SERIES[0], marker="o", ms=5,
            label="znotraj iste nagrade", markeredgecolor=P.SURFACE, markeredgewidth=1.5)
    a = t["all"]
    ax.set_ylabel("mediana starosti ob nagradi")
    ax.set_title("Ali so nagrajenci vse starejši?")
    P.subtitle(ax, f"Znotraj iste nagrade: {P.dec(a['within_award_per_decade'], sign=True)} leta na desetletje "
                   f"(surovo {P.dec(a['raw_per_decade'], sign=True)}) · modra črta odšteje vpliv tega, "
                   "katere nagrade so v zbirki")
    ax.legend(loc="lower right")
    P.source_note(fig)
    P.save(fig, THEME, "trend_starosti")


def jury_winner_gap(winners, jury) -> pd.DataFrame:
    def med(df, name):
        g = df.assign(period=df["year"] // PERIOD * PERIOD).groupby("period")["age"]
        return pd.DataFrame({f"{name}_n": g.size(), f"{name}_median": g.median()})
    t = med(winners, "winner").join(med(jury, "jury"), how="inner")
    t = t[(t["winner_n"] >= MIN_N) & (t["jury_n"] >= MIN_N)]
    t["gap"] = t["jury_median"] - t["winner_median"]
    return t.reset_index()


def plot_jury_winner_gap(t):
    x = t["period"] + PERIOD / 2
    fig, ax = P.figure(8.5, 4.6)
    ax.fill_between(x, t["winner_median"], t["jury_median"], color=P.SERIES[1], alpha=0.1, lw=0)
    ax.plot(x, t["jury_median"], color=P.SERIES[1], marker="o", ms=5, label="žirija",
            markeredgecolor=P.SURFACE, markeredgewidth=1.5)
    ax.plot(x, t["winner_median"], color=P.SERIES[0], marker="o", ms=5, label="nagrajenci",
            markeredgecolor=P.SURFACE, markeredgewidth=1.5)
    ax.set_ylabel("mediana starosti")
    ax.set_title("Kdo sodi komu: starost žirij in nagrajencev")
    P.subtitle(ax, f"Petletna obdobja z vsaj {MIN_N} osebami v vsaki vlogi · žirija, ki "
                   "podeli več nagrad hkrati, šteje enkrat")
    ax.legend(loc="lower right")
    P.source_note(fig)
    P.save(fig, THEME, "starost_zirij_in_nagrajencev")


def gap_within_award(roles) -> dict:
    """The jury-winner age gap per edition (median juror age minus median winner age,
    sourced ages, at least 2 jurors and 1 winner with an age), and its trend within the
    same award (award fixed effects; permutation of years among an award's editions).
    The pooled gap by period (jury_winner_gap) mixes awards that enter and leave the
    data; this one compares an award with itself. Legacy: plot 29 (generation hand-off,
    raw pair counts by decade of first appearance)."""
    a = roles[roles["age"].notna()]
    j = a[a["role"] == "jury"].groupby("edition_id").agg(jury_age=("age", "median"),
                                                        jurors=("age", "size"))
    w = a[a["role"] == "winner"].groupby("edition_id").agg(
        winner_age=("age", "median"), award_id=("award_id", "first"), year=("year", "first"))
    d = w.join(j, how="inner")
    d = d[d["jurors"] >= 2].reset_index()
    d["gap"] = d["jury_age"] - d["winner_age"]
    d["decade_x"] = d["year"] / 10
    res = within_stratum_slope(d, "decade_x", "gap", "award_id", "edition_id", n_perm=1000)
    res["editions"] = len(d)
    res["mean_gap"] = float(d["gap"].mean())
    res["share_jury_older"] = float((d["gap"] > 0).mean())
    res["by_decade"] = (d.assign(decade=d["year"] // 10 * 10).groupby("decade")["gap"]
                        .agg(["size", "mean", "median"]).reset_index())
    return res


def gender_age_gap(winners) -> dict:
    """Do women win younger than men, comparing within the same award and decade?"""
    w = winners[winners["gender"].notna()].copy()
    w["female"] = (w["gender"] == "f").astype(float)
    w["stratum"] = w["award_id"] + "_" + (w["year"] // 10 * 10).astype(str)
    raw = w.groupby("gender")["age"].median()
    fe = smf.ols("age ~ female + C(stratum)", w).fit(
        cov_type="cluster", cov_kwds={"groups": w["award_id"]})
    return {"median_f": float(raw["f"]), "median_m": float(raw["m"]),
            "within_diff_years": float(fe.params["female"]),
            "ci": [float(v) for v in fe.conf_int().loc["female"]],
            "p": float(fe.pvalues["female"]), "n": len(w)}


# --- honoured late in life --------------------------------------------------------------

LATE_FROM, LATE_HORIZON, LATE_MIN_N = 1970, 5, 30


def honoured_late(roles) -> pd.DataFrame:
    """Per award: share of winners who died within LATE_HORIZON years of the award
    (Kaplan–Meier; no death year = alive, censored at the last data year), with median
    age at win. Wins from LATE_FROM; posthumous credits excluded.

    A missing death year usually means alive but can mean undetected, so the shares are
    lower bounds, and detection may be better for famous people. Descriptive only."""
    end = int(roles["year"].max())
    w = roles[(roles["role"] == "winner") & (roles["year"] >= LATE_FROM) & ~roles["posthumous"]]
    w = w.drop_duplicates(["award_id", "entity_id"]).copy()
    w["event"] = w["year_death"].notna()
    w["t"] = (w["year_death"].fillna(end) - w["year"]).astype(float)
    rows = []
    for (a, name), d in w.groupby(["award_id", "award"]):
        if len(d) < LATE_MIN_N:
            continue
        km = kaplan_meier(d["t"], d["event"])
        rows.append({"award_id": a, "award": name, "winners": len(d),
                     "deaths": int(d["event"].sum()),
                     f"died_within_{LATE_HORIZON}y": km_at(km, LATE_HORIZON),
                     "died_within_10y": km_at(km, 10),
                     "median_age_at_win": float(d["age"].median())})
    return pd.DataFrame(rows).sort_values(f"died_within_{LATE_HORIZON}y", ascending=False)


def plot_honoured_late(t):
    col = f"died_within_{LATE_HORIZON}y"
    fig, ax = P.figure(8.5, 5.4)
    ax.scatter(t["median_age_at_win"], t[col], s=t["winners"] / 3, color=P.SERIES[0],
               alpha=0.7, edgecolor=P.SURFACE)
    for _, r in t.nlargest(8, col).iterrows():
        ax.annotate(r["award"], (r["median_age_at_win"], r[col]), xytext=(6, 2),
                    textcoords="offset points", fontsize=7.5, color=P.TEXT_2)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel("mediana starosti ob nagradi")
    ax.set_ylabel(f"umrli v {LATE_HORIZON} letih po nagradi")
    ax.set_title("Nagrade, ki pridejo pozno v življenju")
    P.subtitle(ax, f"Nagrade z vsaj {LATE_MIN_N} nagrajenci od leta {LATE_FROM} · Kaplan–Meier "
                   "· velikost = število nagrajencev\nZnana leta smrti so spodnja meja: "
                   "manjkajoča smrt pomeni živ ali neodkrit podatek")
    P.source_note(fig)
    P.save(fig, THEME, "pozne_nagrade")

