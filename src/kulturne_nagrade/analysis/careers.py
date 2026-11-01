"""Careers: what happens after a win.

All "how many later do X" questions are right-censored: someone who first won in 2022
has had four years to do anything. Kaplan–Meier curves handle this; raw shares do not.
Left truncation also matters (a "first" win in the data may not be the first win), so
the cohorts start in 2000, when most awards are covered.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.duration.hazard_regression import PHReg

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import kaplan_meier, km_at

THEME = "careers"
COHORT_FROM = 2000
HORIZON = 10


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    end_year = int(roles["year"].max())

    to_jury = winner_to_juror(roles, sit, end_year)
    plot_km_groups(to_jury["curves"], "nagrajenec_postane_ziranti",
                   "Iz nagrajenca v žiranta",
                   "Delež nagrajencev, ki v naslednjih letih prvič sedejo v žirijo · prvi "
                   f"nagrajeni od {COHORT_FROM} naprej\nupošteva, da so nedavni nagrajenci "
                   "imeli manj časa (Kaplan–Meier)", "let po prvi nagradi")
    to_win = juror_to_winner(roles, sit, end_year)
    plot_km_groups(to_win["curves"], "ziranti_postanejo_nagrajenci",
                   "Iz žiranta v nagrajenca",
                   "Delež žirantov brez prejšnje nagrade, ki v naslednjih letih prvič dobijo "
                   f"nagrado · prvič v žiriji od {COHORT_FROM}\nupošteva, da so nedavni žiranti "
                   "imeli manj časa (Kaplan–Meier)", "let po prvem sedežu v žiriji")
    again = win_again(roles, end_year)
    plot_km_groups(again["curves"], "ponovna_nagrada", "Kdo zmaga znova?",
                   "Delež nagrajencev, ki v naslednjih letih dobijo še eno nagrado · glede na "
                   f"ugled prve nagrade · prvi nagrajeni od {COHORT_FROM}", "let po prvi nagradi")
    pres = presernov_two_step(roles, end_year)
    plot_km_groups({"Prešernov sklad → Prešernova nagrada": pres["curve"]},
                   "presernov_sklad_do_nagrade", "Od nagrade Prešernovega sklada do "
                   "Prešernove nagrade",
                   "Delež dobitnikov nagrade Prešernovega sklada, ki pozneje prejmejo še "
                   "Prešernovo nagrado (Kaplan–Meier)", "let po nagradi sklada", horizon=40)

    summarise = lambda c: {g: {f"{t}y": km_at(k, t) for t in (3, 5, 10)}
                           for g, k in c.items()}
    return {
        "winner_to_juror": {**{k: v for k, v in to_jury.items() if k != "curves"},
                            "km": summarise(to_jury["curves"])},
        "juror_to_winner": {**{k: v for k, v in to_win.items() if k != "curves"},
                            "km": summarise(to_win["curves"])},
        "win_again": {**{k: v for k, v in again.items() if k != "curves"},
                      "km": summarise(again["curves"])},
        "presernov_two_step": {k: v for k, v in pres.items() if k != "curve"}
        | {"km": {f"{t}y": km_at(pres["curve"], t) for t in (10, 20, 30)}},
    }


def _first_wins(roles) -> pd.DataFrame:
    w = roles[roles["role"] == "winner"].sort_values(["year", "prestige"], ascending=[True, False])
    return w.drop_duplicates("entity_id")[["entity_id", "year", "award_id", "prestige",
                                           "genre", "gender"]]


def winner_to_juror(roles, sit, end_year) -> dict:
    """Time from first win to first jury seat (any award) after it, by gender.
    People who judged before their first win are excluded: their path ran the other way."""
    first = _first_wins(roles)
    first_jury = sit.groupby("entity_id")["year"].min()
    f = first[first["year"] >= COHORT_FROM].copy()
    f["first_jury"] = f["entity_id"].map(first_jury)
    judged_before = (f["first_jury"] <= f["year"]).fillna(False).astype(bool)
    f = f[~judged_before]
    f["event"] = f["first_jury"].notna()
    f["t"] = (f["first_jury"].fillna(end_year) - f["year"]).astype(float)
    curves = {P.GENDER_LABEL[g]: kaplan_meier(d["t"], d["event"])
              for g, d in f.groupby("gender")}
    # Women are concentrated in fields with many juries (literature), so compare within
    # field: Cox model stratified by the genre of the first award.
    c = f[f["gender"].notna()].copy()
    c["female"] = (c["gender"] == "f").astype(float)
    c["t"] = c["t"].clip(lower=0.5)  # same-year events
    cox = PHReg(c["t"].to_numpy(), c[["female"]].to_numpy(), status=c["event"].to_numpy(),
                strata=c["genre"].to_numpy()).fit()
    return {"n": len(f), "excluded_judged_first": int(judged_before.sum()),
            "events": int(f["event"].sum()), "curves": curves,
            "hazard_ratio_female_within_genre": float(np.exp(cox.params[0])),
            "hr_ci": [float(v) for v in np.exp(cox.conf_int()[0])],
            "hr_p": float(cox.pvalues[0])}


def juror_to_winner(roles, sit, end_year) -> dict:
    """The mirror of winner_to_juror: time from a first jury sitting to a first win,
    for people with no win up to that year. Also: how many of those first wins came at
    an award whose jury they had sat on (the insider premium tests whether that is more
    than chance; this only describes the path)."""
    first_seat = (sit.sort_values(["year", "prestige"], ascending=[True, False])
                  .drop_duplicates("entity_id")
                  .set_index("entity_id")[["year", "genre", "gender"]])
    w = roles[roles["role"] == "winner"]
    first_win = w.groupby("entity_id")["year"].min()
    f = first_seat[first_seat["year"] >= COHORT_FROM].copy()
    f["first_win"] = first_win.reindex(f.index)
    won_before = (f["first_win"] <= f["year"]).fillna(False).astype(bool)
    f = f[~won_before]
    f["event"] = f["first_win"].notna()
    f["t"] = (f["first_win"].fillna(end_year) - f["year"]).astype(float)
    curves = {P.GENDER_LABEL[g]: kaplan_meier(d["t"], d["event"])
              for g, d in f.groupby("gender")}
    c = f[f["gender"].notna()].copy()
    c["female"] = (c["gender"] == "f").astype(float)
    cox = PHReg(c["t"].to_numpy(), c[["female"]].to_numpy(), status=c["event"].to_numpy(),
                strata=c["genre"].to_numpy()).fit()
    # first wins of this cohort: at an award whose jury they had sat on before?
    seats = sit.explode("awards")[["entity_id", "awards", "year"]]
    fw = (w[w["entity_id"].isin(f.index[f["event"]])]
          .sort_values("year").drop_duplicates("entity_id")[["entity_id", "award_id", "year"]])
    m = fw.merge(seats, left_on=["entity_id", "award_id"], right_on=["entity_id", "awards"],
                 suffixes=("", "_seat"))
    own = m[m["year_seat"] < m["year"]]["entity_id"].nunique()
    return {"n": len(f), "excluded_won_first": int(won_before.sum()),
            "events": int(f["event"].sum()), "curves": curves,
            "first_win_at_own_jury_award": own,
            "share_first_win_at_own_jury_award": own / max(1, int(f["event"].sum())),
            "hazard_ratio_female_within_genre": float(np.exp(cox.params[0])),
            "hr_ci": [float(v) for v in np.exp(cox.conf_int()[0])],
            "hr_p": float(cox.pvalues[0])}


def win_again(roles, end_year) -> dict:
    """Time from first win to a second win (a different edition), by the first award's
    prestige. A top award early on could open doors (a Matthew effect), or be a career
    capstone."""
    w = roles[roles["role"] == "winner"][["entity_id", "year", "edition_id"]]
    first = _first_wins(roles)
    f = first[first["year"] >= COHORT_FROM].copy()
    later = w.merge(f[["entity_id", "year"]], on="entity_id", suffixes=("", "_first"))
    later = later[later["year"] > later["year_first"]].groupby("entity_id")["year"].min()
    f["second"] = f["entity_id"].map(later)
    f["event"] = f["second"].notna()
    f["t"] = (f["second"].fillna(end_year) - f["year"]).astype(float)
    f["tier"] = f["prestige"].map({2: "ugled 2–3", 3: "ugled 2–3", 4: "ugled 4",
                                   5: "ugled 5"})
    curves = {t: kaplan_meier(d["t"], d["event"]) for t, d in f.groupby("tier")}
    return {"n": len(f), "events": int(f["event"].sum()), "curves": curves}


def presernov_two_step(roles, end_year) -> dict:
    w = roles[roles["role"] == "winner"]
    sklad = w[w["award_id"] == "presernov-sklad"].groupby("entity_id")["year"].min()
    nagrada = w[w["award_id"] == "presernova-nagrada"].groupby("entity_id")["year"].min()
    d = pd.DataFrame({"sklad": sklad})
    d["nagrada"] = nagrada.reindex(d.index)
    d.loc[d["nagrada"] <= d["sklad"], "nagrada"] = pd.NA  # not a later step
    d["event"] = d["nagrada"].notna()
    d["t"] = (d["nagrada"].fillna(end_year) - d["sklad"]).astype(float)
    # Of Prešernova nagrada winners since the sklad prizes began, how many had one first?
    since = nagrada[nagrada >= int(sklad.min()) + 10]
    had = since.index.isin(sklad.index) & (sklad.reindex(since.index) < since).fillna(False)
    gaps = d.loc[d["event"], "t"]
    return {"sklad_winners": len(d), "went_on": int(d["event"].sum()),
            "median_gap_years": float(gaps.median()),
            "nagrada_winners_checked": len(since),
            "share_nagrada_with_prior_sklad": float(had.mean()),
            "curve": kaplan_meier(d["t"], d["event"])}


def plot_km_groups(curves: dict, name: str, title: str, sub: str, xlabel: str,
                   horizon: int = HORIZON):
    fig, ax = P.figure(8.5, 4.8)
    for i, (label, k) in enumerate(curves.items()):
        k = k[k["t"] <= horizon]
        color = P.SERIES[i]
        if label in P.GENDER_LABEL.values():
            color = P.GENDER[{v: k_ for k_, v in P.GENDER_LABEL.items()}[label]]
        ax.step(k["t"], k["cum_incidence"], where="post", color=color, lw=2, label=label)
        ax.fill_between(k["t"], k["lo"], k["hi"], step="post", color=color, alpha=0.12, lw=0)
        end = k.iloc[-1]
        ax.annotate(P.pct(end['cum_incidence']), (end["t"], end["cum_incidence"]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9)
    ax.set_xlim(0, horizon + 1)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    P.subtitle(ax, sub)
    if len(curves) > 1:
        ax.legend(loc="upper left")
    P.source_note(fig)
    P.save(fig, THEME, name)
