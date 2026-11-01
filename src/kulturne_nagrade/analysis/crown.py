"""The crown: concentration of recognition, the climb to a top award, and what follows.

1. Concentration. How unequally are wins, prestige (sum of the prestige of one's wins),
   jury sittings and jury voting power (sum of 1 / jury size) spread over people, since
   2000? Gini and top-10% shares; distinct people only.
2. The climb. For a person's first prestige-5 win ("the crown", from 2005 so that a
   15-year history exists), what came before: an earlier win, an earlier jury seat.
   The same is measured for a person's first tier-3 and first tier-4 win, which
   separates "the crown needs a record" from "any award needs a record"; compared
   within field and year.
3. After the crown. Time to the next jury seat and to the next win (Kaplan–Meier),
   after a first win at tier 5, 4 and 3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import kaplan_meier, km_at, wilson

THEME = "crown"
SINCE = 2000
CROWN_FROM = 2005
HORIZON = 10


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    end_year = int(roles["year"].max())
    conc = concentration(roles, sit)
    plot_lorenz(conc)
    events = crown_and_peers(roles)
    climb = before(events, roles, sit)
    plot_climb(climb)
    after = aftermath(events, roles, sit, end_year)
    plot_after(after)
    return {
        "concentration": {k: {kk: vv for kk, vv in v.items() if kk != "lorenz"}
                          for k, v in conc.items()},
        "climb": climb,
        "after": {k: {g: {f"{t}y": km_at(c, t) for t in (3, 5, 10)} for g, c in v.items()}
                  for k, v in after.items()},
    }


# --- 1. concentration -------------------------------------------------------------------

def _gini(x: np.ndarray) -> float:
    x = np.sort(x)
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def concentration(roles, sit) -> dict:
    w = roles[(roles["role"] == "winner") & (roles["year"] >= SINCE)].drop_duplicates(
        ["edition_id", "entity_id"])
    s = sit[sit["year"] >= SINCE]
    measures = {
        "wins": w.groupby("entity_id").size(),
        "prestige": w.groupby("entity_id")["prestige"].sum(),
        "sittings": s.groupby("entity_id").size(),
        "voting_power": (1 / s["jury_size"]).groupby(s["entity_id"]).sum(),
    }
    out = {}
    for k, v in measures.items():
        x = v.to_numpy(dtype=float)
        srt = np.sort(x)[::-1]
        top = max(1, int(np.ceil(0.1 * len(x))))
        cum = np.concatenate([[0], np.cumsum(np.sort(x))]) / x.sum()
        out[k] = {"people": len(x), "gini": _gini(x), "top10_share": float(srt[:top].sum() / x.sum()),
                  "share_with_one": float((x == x.min()).mean()) if k in ("wins", "sittings") else None,
                  "max": float(x.max()),
                  "lorenz": (np.linspace(0, 1, len(cum)), cum)}
    return out


def plot_lorenz(conc):
    labels = {"wins": "nagrade", "prestige": "ugled nagrad", "sittings": "sedeži v žirijah",
              "voting_power": "glasovna moč v žirijah"}
    colors = {"wins": P.SERIES[2], "prestige": P.SERIES[5], "sittings": P.SERIES[0],
              "voting_power": P.SERIES[6]}
    fig, ax = P.figure(6.8, 6)
    ax.plot([0, 1], [0, 1], color=P.MUTED, lw=1)
    for k, c in conc.items():
        x, y = c["lorenz"]
        ax.plot(x, y, color=colors[k], lw=2,
                label=f"{labels[k]} (Gini {P.dec(c['gini'], 2)}, zgornjih 10 %: "
                      f"{P.pct(c['top10_share'])})")
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel("delež ljudi (od najmanj do najbolj priznanih)")
    ax.set_ylabel("kumulativni delež")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_aspect("equal")
    ax.set_title("Kako neenakomerno so razdeljene nagrade in sedeži")
    P.subtitle(ax, f"Lorenzove krivulje od leta {SINCE} · samo ljudje z vsaj eno nagrado "
                   "oziroma enim sedežem")
    P.source_note(fig)
    P.save(fig, THEME, "koncentracija")


# --- 2. the climb -----------------------------------------------------------------------

TIERS = {3: "ugled 3", 4: "ugled 4", 5: "ugled 5"}
TIER_COLORS = {"ugled 5": "#184f95", "ugled 4": "#3987e5", "ugled 3": "#9fc4f2"}  # ordinal


def crown_and_peers(roles) -> pd.DataFrame:
    """A person's first win at each prestige tier 3, 4 and 5 (from CROWN_FROM). The tier-5
    event is "the crown"; tiers 3 and 4 measured the same way are the comparison."""
    w = roles[roles["role"] == "winner"].drop_duplicates(["edition_id", "entity_id"])
    w = w[w["prestige"].isin(list(TIERS))].sort_values("year")
    ev = w.drop_duplicates(["entity_id", "prestige"]).copy()
    ev["kind"] = ev["prestige"].map(TIERS)
    return ev[ev["year"] >= CROWN_FROM][["entity_id", "year", "award_id", "award", "genre",
                                         "prestige", "age", "gender", "kind"]]


def before(ev, roles, sit) -> dict:
    import warnings

    import statsmodels.formula.api as smf

    w = roles[roles["role"] == "winner"]
    first_any = pd.concat([w[["entity_id", "year"]], sit[["entity_id", "year"]]]).groupby(
        "entity_id")["year"].min()
    first_win = w.groupby("entity_id")["year"].min()
    first_seat = sit.groupby("entity_id")["year"].min()
    e = ev.copy()
    e["prior_win"] = (e["entity_id"].map(first_win) < e["year"]).fillna(False)
    e["prior_jury"] = (e["entity_id"].map(first_seat) < e["year"]).fillna(False)
    e["years_since_first"] = e["year"] - e["entity_id"].map(first_any)
    out = {}
    for k, d in e.groupby("kind"):
        res = {"n": len(d)}
        for m in ("prior_win", "prior_jury"):
            kk = int(d[m].sum())
            lo, hi = wilson(kk, len(d))
            res[m] = {"share": kk / len(d), "ci": [float(lo), float(hi)]}
        res["median_years_since_first_if_prior"] = float(
            d.loc[d["years_since_first"] > 0, "years_since_first"].median())
        res["median_age"] = float(d["age"].median())
        out[k] = res
    # Within field and year: is the crown preceded by a record more often than a tier 3
    # or tier 4 first win? LPM with genre x year cells, SE clustered by award.
    e["cell"] = e["genre"] + "_" + e["year"].astype(str)
    e["prestige"] = e["prestige"].astype(int)
    for m in ("prior_win", "prior_jury"):
        e["y"] = e[m].astype(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # singleton cells' SEs
            fit = smf.ols("y ~ C(prestige, Treatment(5)) + C(cell)", e).fit(
                cov_type="cluster", cov_kwds={"groups": e["award_id"]})
            ci = fit.conf_int()
        for t in (3, 4):
            name = f"C(prestige, Treatment(5))[T.{t}]"
            out[f"{m}_tier{t}_minus_crown"] = {
                "diff": float(fit.params[name]), "ci": [float(v) for v in ci.loc[name]],
                "p": float(fit.pvalues[name])}
    return out


def plot_climb(c):
    labels = {"prior_win": "že prej nagrajeni", "prior_jury": "že prej v žiriji"}
    fig, ax = P.figure(8, 4)
    y = np.arange(len(labels))
    cols = TIER_COLORS
    for off, k in zip((0.26, 0, -0.26), ("ugled 5", "ugled 4", "ugled 3")):
        vals = [c[k][m]["share"] for m in labels]
        lo = [c[k][m]["ci"][0] for m in labels]
        hi = [c[k][m]["ci"][1] for m in labels]
        ax.barh(y + off, vals, height=0.24, color=cols[k],
                label=f"prva nagrada z {k.replace('ugled', 'ugledom')} (n = {c[k]['n']})")
        ax.hlines(y + off, lo, hi, color=P.TEXT_2, lw=1)
        for yi, v, h in zip(y + off, vals, hi):
            ax.annotate(P.pct(v), (h, yi), xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(list(labels.values()))
    ax.set_xlim(0, 0.6)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="center right", fontsize=8)
    ax.set_title("Pred najvišjo nagrado: večina nima prejšnje nagrade v podatkih")
    P.subtitle(ax, f"Prva nagrada posamezne stopnje ugleda, prejemniki od leta {CROWN_FROM} · "
                   "črta = 95 % interval")
    P.source_note(fig)
    P.save(fig, THEME, "pred_kronanjem")


# --- 3. after ---------------------------------------------------------------------------

def aftermath(ev, roles, sit, end_year) -> dict:
    w = roles[roles["role"] == "winner"][["entity_id", "year"]]
    seats = sit[["entity_id", "year"]]
    out = {}
    for name, df in (("next_jury", seats), ("next_win", w)):
        curves = {}
        for k, d in ev.groupby("kind"):
            nxt = d[["entity_id", "year"]].merge(df, on="entity_id", suffixes=("", "_n"))
            nxt = nxt[nxt["year_n"] > nxt["year"]].groupby("entity_id")["year_n"].min()
            t = d["entity_id"].map(nxt)
            event = t.notna()
            dur = (t.fillna(end_year) - d["year"]).astype(float)
            curves[k] = kaplan_meier(dur, event)
        out[name] = curves
    return out


def plot_after(after):
    fig, axes = P.figure(11, 4.2, ncols=2, sharey=True)
    titles = {"next_jury": "naslednji sedež v žiriji", "next_win": "naslednja nagrada"}
    colors = TIER_COLORS
    for ax, (k, curves) in zip(axes, after.items()):
        for g, km in curves.items():
            d = km[km["t"] <= HORIZON]
            ax.step(d["t"], d["cum_incidence"], where="post", color=colors[g], lw=2, label=g)
            ax.fill_between(d["t"], d["lo"], d["hi"], step="post", color=colors[g],
                            alpha=0.15, lw=0)
        ax.set_xlim(0, HORIZON)
        ax.set_ylim(0, 0.5)
        ax.yaxis.set_major_formatter(P.pct_fmt)
        ax.set_xlabel("let po nagradi")
        ax.text(0.02, 0.95, titles[k], transform=ax.transAxes, fontsize=10.5,
                fontweight="bold", color=P.TEXT_2, va="top")
    axes[0].legend(loc="upper left", bbox_to_anchor=(0, 0.88))
    axes[0].set_title("Po najvišji nagradi")
    P.subtitle(axes[0], f"Prva nagrada posamezne stopnje ugleda, prejemniki od leta "
                        f"{CROWN_FROM}\nKaplan–Meier, pas = 95 % interval")
    P.source_note(fig)
    P.save(fig, THEME, "po_kronanju")
