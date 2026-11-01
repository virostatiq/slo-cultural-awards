"""The 1991 break: did independence interrupt careers in the award field?

The legacy analysis reported raw continuation (about 27% of pre-1991 winners won again
after 1991). Such a number cannot be read on its own: careers end anyway, and the
pre-1991 data covers few awards. So every rate here is computed the same way at the
real break and at placebo breaks (1971, 1981, 2001, 2011):

  * window: W years before the break and W years from it;
  * only awards with editions in both windows ("spanning awards"), so a person can
    only "disappear" from an award that is still recorded;
  * people active before the break in a spanning award (as winner or juror), alive at
    the break; "continued" = active again, in any role, in any spanning award in the
    after-window.

If independence disrupted careers, the 1991 rate should fall below the placebo rates.
The comparison is also made within award: an LPM of continuation on break dummies with
award fixed effects (only awards spanning several breaks identify it), SE clustered by
award.
"""

from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import wilson

THEME = "transition"
BREAK = 1991
BREAKS = [1971, 1981, 1991, 2001, 2011]
W = 10


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    act = activity(roles, sit)
    people = continuation(act)
    rates = rates_by_break(people)
    plot_rates(rates)
    model = within_award(people)
    turnover = new_entrants(act)
    plot_turnover(turnover)
    return {
        "window_years": W, "rates": rates, "within_award": model,
        "spanning_awards": {b: sorted(people.loc[people["break"] == b, "award"].unique())
                            for b in BREAKS},
        "new_entrant_share": turnover,
    }


def activity(roles, sit) -> pd.DataFrame:
    """One row per (person, award, year, role): winners and jury sittings (a sitting
    counts for each award it decided)."""
    w = roles[roles["role"] == "winner"][["entity_id", "award_id", "award", "year",
                                          "year_death", "gender"]].assign(role="winner")
    j = sit.explode("awards")[["entity_id", "awards", "year", "year_death", "gender"]]
    j = j.rename(columns={"awards": "award_id"}).assign(role="jury")
    j = j.merge(frames.awards()[["award_id", "name"]].rename(columns={"name": "award"}))
    return pd.concat([w, j], ignore_index=True).drop_duplicates()


def continuation(act: pd.DataFrame) -> pd.DataFrame:
    """One row per (break, award, person active before in that award)."""
    rows = []
    for b in BREAKS:
        before = act[act["year"].between(b - W, b - 1)]
        after = act[act["year"].between(b, b + W - 1)]
        spanning = set(before["award_id"]) & set(after["award_id"])
        before = before[before["award_id"].isin(spanning)]
        before = before[~(before["year_death"] < b).fillna(False)]
        after_any = set(after.loc[after["award_id"].isin(spanning), "entity_id"])
        after_same = set(zip(after["entity_id"], after["award_id"]))
        p = before.groupby(["entity_id", "award_id", "award"]).agg(
            roles=("role", lambda s: "+".join(sorted(set(s)))),
            last_year=("year", "max"), gender=("gender", "first")).reset_index()
        p["break"] = b
        p["n_spanning"] = len(spanning)
        p["cont_any"] = p["entity_id"].isin(after_any)
        p["cont_same_award"] = [(e, a) in after_same for e, a in zip(p["entity_id"],
                                                                    p["award_id"])]
        rows.append(p)
    return pd.concat(rows, ignore_index=True)


def rates_by_break(people: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (b, role), d in _by_role(people):
        person = d.groupby("entity_id")["cont_any"].any()  # person level for "any"
        k, n = int(person.sum()), len(person)
        lo, hi = wilson(k, n)
        ks, ns = int(d["cont_same_award"].sum()), len(d)
        los, his = wilson(ks, ns)
        out.append({"break": b, "role": role, "people": n, "continued": k,
                    "rate_any": k / n, "lo": float(lo), "hi": float(hi),
                    "person_awards": ns, "rate_same_award": ks / ns,
                    "lo_same": float(los), "hi_same": float(his),
                    "spanning_awards": int(d["n_spanning"].iloc[0])})
    return pd.DataFrame(out)


def _by_role(people):
    for b, d in people.groupby("break"):
        yield (b, "winner"), d[d["roles"].str.contains("winner")]
        yield (b, "jury"), d[d["roles"].str.contains("jury")]


def within_award(people: pd.DataFrame) -> dict:
    """Same-award continuation on break dummies (reference: BREAK), award FE."""
    d = people.copy()
    d["y"] = d["cont_same_award"].astype(float)
    d["b"] = d["break"].astype(str)
    multi = d.groupby("award_id")["break"].nunique()
    d = d[d["award_id"].isin(multi[multi >= 2].index)]
    fit = smf.ols(f"y ~ C(b, Treatment('{BREAK}')) + C(award_id)", d).fit(
        cov_type="cluster", cov_kwds={"groups": d["award_id"]})
    out = {"n": len(d), "awards": int(d["award_id"].nunique()), "vs_1991": {}}
    for b in BREAKS:
        if b == BREAK:
            continue
        name = f"C(b, Treatment('{BREAK}'))[T.{b}]"
        if name in fit.params:
            out["vs_1991"][b] = {"diff": float(fit.params[name]),
                                 "ci": [float(v) for v in fit.conf_int().loc[name]],
                                 "p": float(fit.pvalues[name])}
    return out


def new_entrants(act: pd.DataFrame) -> pd.DataFrame:
    """Per year: share of that year's active people (winners + jurors) never seen in the
    data before. Only years from 1965, so a 15-year history exists; still left-truncated
    for older people, which raises early shares."""
    first = act.groupby("entity_id")["year"].min()
    a = act.drop_duplicates(["entity_id", "year"]).copy()
    a["new"] = a["year"] == a["entity_id"].map(first)
    t = a.groupby("year").agg(active=("entity_id", "size"), new=("new", "sum")).reset_index()
    t["share_new"] = t["new"] / t["active"]
    return t[(t["year"] >= 1965) & (t["active"] >= 20)].reset_index(drop=True)


def plot_rates(rates):
    fig, ax = P.figure(8.5, 4.6)
    colors = {"winner": P.SERIES[2], "jury": P.SERIES[0]}
    for i, (role, c) in enumerate(colors.items()):
        d = rates[rates["role"] == role]
        x = d["break"] + (i - 0.5) * 1.2
        ax.vlines(x, d["lo"], d["hi"], color=c, lw=2, alpha=0.5)
        ax.plot(x, d["rate_any"], color=c, marker="o", lw=1.5, label=P.ROLE_LABEL[role])
        for xi, (_, r) in zip(x, d.iterrows()):
            ax.annotate(f"n = {r['people']}", (xi, r["lo"]), xytext=(0, -12),
                        textcoords="offset points", ha="center", fontsize=7, color=P.TEXT_2)
    ax.axvspan(BREAK - 2.5, BREAK + 2.5, color=P.GRID, alpha=0.5, lw=0, zorder=0)
    ax.annotate("osamosvojitev", (BREAK, 1), xytext=(0, -4), textcoords="offset points",
                ha="center", va="top", fontsize=8, color=P.TEXT_2)
    ax.set_xticks(BREAKS)
    ax.set_xticklabels([f"{b - W}–{b - 1}\n→ {b}–{b + W - 1}" for b in BREAKS], fontsize=8)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_ylabel(f"delež aktivnih tudi v naslednjih {W} letih")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.93))
    ax.set_title("Ali je osamosvojitev prekinila kariere?")
    P.subtitle(ax, f"Ljudje, aktivni {W} let pred prelomnico, ki so bili spet nagrajeni ali v "
                   f"žiriji v naslednjih {W} letih\nSamo nagrade, zabeležene na obeh straneh "
                   "prelomnice · črta = 95 % interval")
    P.source_note(fig)
    P.save(fig, THEME, "nadaljevanje_karier")


def plot_turnover(t):
    fig, ax = P.figure(8.5, 4.2)
    ax.plot(t["year"], t["share_new"], color=P.MUTED, lw=1, marker="o", ms=3)
    roll = t.set_index("year")["share_new"].rolling(5, center=True, min_periods=3).mean()
    ax.plot(roll.index, roll.values, color=P.SERIES[0], lw=2.5)
    ax.axvline(BREAK, color=P.TEXT_2, lw=1, ls="--")
    ax.annotate("1991", (BREAK, 0.97), xytext=(4, 0), textcoords="offset points", fontsize=8,
                color=P.TEXT_2, va="top")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_title("Delež novih obrazov med nagrajenci in žiranti")
    P.subtitle(ax, "Delež letos aktivnih, ki se v podatkih pojavijo prvič · črta = 5-letno "
                   "drseče povprečje\nZgodnja leta so precenjena, ker podatki pred njimi "
                   "manjkajo")
    P.source_note(fig)
    P.save(fig, THEME, "novi_obrazi")
