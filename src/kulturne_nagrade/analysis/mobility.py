"""Mobility: crossing between fields, streaks, several awards in one year.

1. Crossing fields. How many winners won in two or more fields (genres), and which
   pairs of fields share winners more than chance? Null: the genre labels of all win
   events since SINCE are shuffled, which keeps every field's number of wins and every
   person's number of wins. Lift = observed people with wins in both fields / expected.
   "umetnost in kultura" is the umbrella field (Prešeren, Župančič, Ježek awards), so its
   overlap with every field is the route from a field to general recognition.
2. Streaks. The longest run of consecutive years with at least one jury sitting, and
   with at least one win. A missing year in the data breaks a streak, so streaks are
   lower bounds; standing juries (one award re-appointing the same people) produce the
   longest ones.
3. Several awards in one year: winners of at least two distinct awards in a year.

Multi-jury years are in the power theme (multi_jury_load).
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import permutation_p, rng

THEME = "mobility"
SINCE = 2000
N_PERM = 1000
GENRE_LABEL = {"likovno-vizualna umetnost": "likovna um.", "umetnost in kultura":
               "umetnost in kultura (krovne)"}


def run() -> dict:
    roles = frames.roles()
    sit = frames.jury_sittings()
    cross = crossing(roles)
    plot_crossing(cross)
    st = streaks(roles, sit)
    plot_streaks(st)
    multi = multi_award_years(roles)
    outs = outside_jurors(roles, sit)
    plot_outside_jurors(outs)
    return {
        "outside_jurors": {k: v for k, v in outs.items() if k not in ("matrix", "seats")},
        "outside_jurors_matrix": outs["matrix"],
        "crossing": {k: v for k, v in cross.items() if k not in ("lift", "observed")},
        "crossing_pairs": cross["pairs"],
        "streaks": {k: v for k, v in st.items() if k not in ("dist",)},
        "multi_award_years": multi,
    }


# --- 1. crossing fields -----------------------------------------------------------------

def _pair_counts(person_idx: np.ndarray, genre_idx: np.ndarray, n_people: int,
                 n_genres: int) -> tuple[np.ndarray, int]:
    M = np.zeros((n_people, n_genres), dtype=bool)
    M[person_idx, genre_idx] = True
    Mi = M.astype(int)
    return Mi.T @ Mi, int((M.sum(axis=1) >= 2).sum())


def crossing(roles) -> dict:
    w = roles[(roles["role"] == "winner") & (roles["year"] >= SINCE)].drop_duplicates(
        ["edition_id", "entity_id"])
    people = {e: i for i, e in enumerate(sorted(w["entity_id"].unique()))}
    genres = sorted(w["genre"].unique())
    gi = {g: i for i, g in enumerate(genres)}
    p_idx = w["entity_id"].map(people).to_numpy()
    g_idx = w["genre"].map(gi).to_numpy()
    obs, obs_multi = _pair_counts(p_idx, g_idx, len(people), len(genres))
    g = rng()
    null = np.zeros((N_PERM, len(genres), len(genres)))
    null_multi = np.zeros(N_PERM)
    for i in range(N_PERM):
        null[i], null_multi[i] = _pair_counts(p_idx, g.permutation(g_idx), len(people),
                                              len(genres))
    exp = null.mean(axis=0)
    rows = []
    for a in range(len(genres)):
        for b in range(a + 1, len(genres)):
            o, e = obs[a, b], exp[a, b]
            p_hi = permutation_p(o, null[:, a, b], "greater")
            p_lo = permutation_p(o, null[:, a, b], "less")
            rows.append({"a": genres[a], "b": genres[b], "observed": int(o),
                         "expected": float(e), "lift": float(o / e) if e else None,
                         "p": float(min(1, 2 * min(p_hi, p_lo)))})
    pairs = pd.DataFrame(rows).sort_values("lift", ascending=False).reset_index(drop=True)
    return {"winners": len(people), "multi_field": obs_multi,
            "multi_field_share": obs_multi / len(people),
            "multi_field_expected": float(null_multi.mean()),
            "multi_field_p_less": permutation_p(obs_multi, null_multi, "less"),
            "genres": genres, "lift": obs / np.where(exp > 0, exp, np.nan),
            "observed": obs, "pairs": pairs}


def plot_crossing(c):
    from matplotlib.colors import LogNorm

    genres = c["genres"]
    L = c["lift"].copy()
    np.fill_diagonal(L, np.nan)
    fig, ax = P.figure(8.5, 7.2)
    im = ax.imshow(np.clip(L, 0.25, 4), cmap=P.DIVERGING, norm=LogNorm(vmin=0.25, vmax=4))
    for (i, j), v in np.ndenumerate(L):
        if i != j and not np.isnan(v):
            n = c["observed"][i, j]
            txt = "< 0,1×" if v < 0.1 else f"{P.dec(v, 1)}×"
            ax.text(j, i, f"{txt}\n{n}", ha="center", va="center", fontsize=7,
                    color="white" if (v > 2.5 or v < 0.4) else P.TEXT)
    labels = [GENRE_LABEL.get(g, g) for g in genres]
    ax.set_xticks(range(len(genres)))
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(genres)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.set_ticks([0.25, 0.5, 1, 2, 4])
    cb.set_ticklabels(["0,25×", "0,5×", "1×", "2×", "4×"])
    cb.minorticks_off()
    ax.set_title("Katera področja si delijo nagrajence?")
    P.subtitle(ax, f"Ljudje z nagradami na obeh področjih od leta {SINCE} (število) glede na "
                   f"naključje ({N_PERM} premešanj)\n{P.pct(c['multi_field_share'])} "
                   f"nagrajencev ima nagrade na več področjih, naključno bi jih imelo "
                   f"{P.pct(c['multi_field_expected'] / c['winners'])}")
    P.source_note(fig)
    P.save(fig, THEME, "prehajanje_podrocij")


# --- 2. streaks -------------------------------------------------------------------------

def _longest_runs(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for e, years in df.groupby("entity_id")["year"]:
        ys = np.sort(years.unique())
        best, start, cur_start = 1, ys[0], ys[0]
        run = 1
        for a, b in itertools.pairwise(ys):
            run = run + 1 if b == a + 1 else 1
            if run == 1:
                cur_start = b
            if run > best:
                best, start = run, cur_start
        rows.append({"entity_id": e, "streak": best, "start": int(start),
                     "end": int(start + best - 1), "active_years": len(ys)})
    return pd.DataFrame(rows)


def streaks(roles, sit) -> dict:
    names = frames.entities().set_index("entity_id")["name"]
    j = _longest_runs(sit[["entity_id", "year"]])
    w = _longest_runs(roles[roles["role"] == "winner"][["entity_id", "year"]])
    for d in (j, w):
        d["name"] = d["entity_id"].map(names)
    # the award behind each long jury streak
    top = j.sort_values(["streak", "active_years"], ascending=False).head(15).copy()
    top["awards"] = [", ".join(sit[(sit["entity_id"] == e) & sit["year"].between(a, b)]
                               ["award"].value_counts().index[:2])
                     for e, a, b in zip(top["entity_id"], top["start"], top["end"])]
    return {
        "jury_max": int(j["streak"].max()), "winner_max": int(w["streak"].max()),
        "jury_share_5plus": float((j["streak"] >= 5).mean()),
        "winner_share_3plus": float((w["streak"] >= 3).mean()),
        "top_jury": top.drop(columns="entity_id"),
        "top_winner": w.sort_values(["streak", "active_years"], ascending=False).head(10)
        .drop(columns="entity_id"),
        "dist": (j["streak"].value_counts().sort_index(), w["streak"].value_counts().sort_index()),
    }


def _years(n: int) -> str:
    """Slovenian plural of 'leto' after a number."""
    n = int(n)
    if n % 100 == 1:
        return f"{n} leto"
    if n % 100 == 2:
        return f"{n} leti"
    if n % 100 in (3, 4):
        return f"{n} leta"
    return f"{n} let"


def plot_streaks(st):
    t = st["top_jury"].iloc[::-1]
    fig, ax = P.figure(9, 0.36 * len(t) + 2)
    y = np.arange(len(t))
    ax.hlines(y, t["start"], t["end"] + 1, color=P.SERIES[0], lw=7)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.annotate(f"{_years(r['streak'])} · {r['awards']}", (r["end"] + 1, yi), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=7.5, color=P.TEXT_2)
    ax.set_yticks(y)
    ax.set_yticklabels(t["name"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    lo, hi = int(t["start"].min()), int(t["end"].max())
    ax.set_xlim(lo - 1, hi + 12)
    ax.set_title("Najdaljši nepretrgani nizi v žirijah")
    P.subtitle(ax, "Zaporedna leta z vsaj enim sedežem v kateri koli žiriji · ob strani: "
                   "nagradi z največ sedeži v nizu\n"
                   f"Najdaljši niz nagrad: {_years(st['winner_max'])} · manjkajoče leto v "
                   "podatkih niz prekine")
    P.source_note(fig)
    P.save(fig, THEME, "nizi_v_zirijah")


# --- 3. several awards in a year --------------------------------------------------------

def multi_award_years(roles) -> dict:
    w = roles[roles["role"] == "winner"].drop_duplicates(["entity_id", "award_id", "year"])
    py = w.groupby(["entity_id", "name", "year"])["award"].agg(list).reset_index()
    py["n"] = py["award"].str.len()
    multi = py[py["n"] >= 2]
    recent = multi[multi["year"] >= SINCE]
    return {"person_years": len(py[py["year"] >= SINCE]),
            "multi_person_years": len(recent),
            "share": float(len(recent) / len(py[py["year"] >= SINCE])),
            "max": int(multi["n"].max()),
            "top": multi.sort_values(["n", "year"], ascending=False).head(15)
            .assign(award=lambda d: d["award"].map(", ".join)).reset_index(drop=True)}


# --- 4. jurors from other fields --------------------------------------------------------

UMBRELLA = "umetnost in kultura"
FIELD_MERGE = {"poezija": "literatura"}  # poets judge literature awards and vice versa


def outside_jurors(roles, sit) -> dict:
    """Seats (sittings, since SINCE) on field juries, by the juror's home field: the
    field of most of their earlier wins (umbrella awards excluded; poetry counted as
    literature; a tie that includes the jury's field counts as inside). Jurors without
    an earlier field win have no home field and are reported separately. Umbrella
    juries (Prešeren, Župančič...) are excluded: every field is inside them.
    Trend: within-award linear probability model (award fixed effects, SE clustered by
    award). Legacy: plot 28 (juror flows between fields, career-long home field
    including future service, shared juries counted per prize)."""
    import statsmodels.formula.api as smf

    f = lambda g: FIELD_MERGE.get(g, g)
    w = roles[(roles["role"] == "winner") & (roles["genre"] != UMBRELLA)]
    w = w.assign(field=w["genre"].map(f))[["entity_id", "year", "field"]]
    wins = {e: d.sort_values("year") for e, d in w.groupby("entity_id")}
    s = sit[(sit["year"] >= SINCE) & (sit["genre"] != UMBRELLA)].copy()
    s["field"] = s["genre"].map(f)
    home, inside = [], []
    for e, y, fld in zip(s["entity_id"], s["year"], s["field"]):
        d = wins.get(e)
        prev = d.loc[d["year"] < y, "field"] if d is not None else pd.Series(dtype=str)
        if prev.empty:
            home.append(None)
            inside.append(np.nan)
            continue
        vc = prev.value_counts()
        top = set(vc[vc == vc.max()].index)
        home.append(fld if fld in top else vc.index[0])
        inside.append(float(fld in top))
    s["home"], s["inside"] = home, inside
    h = s[s["home"].notna()].copy()
    h["outside"] = 1 - h["inside"]
    by_field = h.groupby("field")["outside"].agg(["size", "mean"]).reset_index()
    by_period = (h.assign(period=h["year"] // 5 * 5).groupby("period")["outside"]
                 .agg(["size", "mean"]).reset_index())
    fit = smf.ols("outside ~ year + C(award_id)", h).fit(
        cov_type="cluster", cov_kwds={"groups": h["award_id"]})
    matrix = pd.crosstab(h["field"], h["home"])
    return {
        "seats": len(s), "seats_with_home_field": len(h),
        "share_no_prior_field_win": float(s["home"].isna().mean()),
        "share_outside": float(h["outside"].mean()),
        "by_field": by_field, "by_period": by_period,
        "within_award_trend_per_decade": float(10 * fit.params["year"]),
        "trend_ci": [float(10 * v) for v in fit.conf_int().loc["year"]],
        "trend_p": float(fit.pvalues["year"]),
        "matrix": matrix.reset_index().rename(columns={"field": "jury_field"}),
    }


def plot_outside_jurors(o):
    m = o["matrix"].set_index("jury_field")
    m = m.loc[:, [c for c in m.index if c in m.columns] +
              [c for c in m.columns if c not in m.index]]
    share = m.div(m.sum(axis=1), axis=0)
    fig, ax = P.figure(8.5, 0.5 * len(share) + 2.4)
    cmap = P.SEQUENTIAL.copy()
    cmap.set_bad(P.SURFACE)  # empty cells stay blank, not the ramp's lightest step
    ax.imshow(np.ma.masked_equal(share.to_numpy(), 0), cmap=cmap, vmin=0, vmax=1,
              aspect="auto")
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            v = share.iat[i, j]
            if v >= 0.01:
                ax.text(j, i, P.pct(v), ha="center", va="center", fontsize=8,
                        color=P.SURFACE if v > 0.5 else P.TEXT)
    lab = lambda g: GENRE_LABEL.get(g, g)
    ax.set_xticks(range(share.shape[1]), [lab(c) for c in share.columns], rotation=35,
                  ha="right", fontsize=8.5)
    ax.set_yticks(range(share.shape[0]),
                  [f"{lab(r)} ({int(n)})" for r, n in zip(share.index, m.sum(axis=1))],
                  fontsize=8.5)
    ax.grid(False)
    ax.set_xlabel("domače področje žiranta (področje večine njegovih prejšnjih nagrad)")
    ax.set_ylabel("področje žirije (število sedežev)")
    ax.set_title("Iz katerih področij prihajajo žiranti?")
    P.subtitle(ax, f"Sedeži v žirijah od {SINCE}, žiranti z vsaj eno prejšnjo nagrado · "
                   f"zunaj svojega področja sodi {P.pct(o['share_outside'])}\n"
                   f"{P.pct(o['share_no_prior_field_win'])} sedežev zasedejo ljudje brez "
                   "prejšnje nagrade (niso prikazani) · poezija šteje k literaturi")
    P.source_note(fig)
    P.save(fig, THEME, "ziranti_iz_drugih_podrocij")
