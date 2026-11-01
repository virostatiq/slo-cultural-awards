"""Geography: how Ljubljana-centred are the awards?

Places come from the enrichment and are an unordered set of *ties* (birthplace, places
lived or worked in), not a residence; see ``frames.entity_geography``. Each person is
reduced to their Slovenian units: Ljubljana (the city municipality) or one of the 12
statistical regions, with Osrednjeslovenska meaning "central region without Ljubljana".

Measures, loosest to strictest: **Ljubljana tie** (Ljubljana among the units),
**Ljubljana only** (the only unit), **outside Ljubljana only** (units, none Ljubljana).
Shares are over people with at least one unit.

Biography richness is a confounder for all of them: a person with one recorded tie can
be "Ljubljana only", one with three almost never is, and famous people have richer
biographies. Every comparison is therefore made within strata of the number of units
(1 / 2 / 3+) as well as field and year.

Questions:
1. Shares over time, by role (winners, jury sittings).
2. Representation by region against population (people since 2000).
3. Which awards are more Ljubljana-bound than their field? Each award's winners against
   winners of other awards in the same field, year and richness stratum; null =
   shuffle award labels within those pools; BH across awards.
4. Home advantage of awards seated outside Ljubljana: are their winners more often tied
   to the seat's region than field-year peers?
5. Are juries more Ljubljana-bound than the winners they pick (same edition)?
6. Regional homophily: do juries with more members from outside Ljubljana pick more
   winners from outside Ljubljana? Within award × decade, permutation null.
7. The path into juries: do winners tied to Ljubljana reach a jury seat sooner than
   winners tied only to other places? Cox model stratified by field, with richness.
8. Ties abroad: did ties to former Yugoslavia and to the rest of the world change after
   1991? Within award, controlling for how many places a biography lists.
9. Places: distinct people tied to each Slovenian place (for the site's map).
"""

from __future__ import annotations

import json
import urllib.request
import zipfile
from io import BytesIO

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.duration.hazard_regression import PHReg
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter, NullLocator

from kulturne_nagrade import PROJECT_ROOT, frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import (
    bh_fdr,
    kaplan_meier,
    km_at,
    permutation_p,
    rng,
    wilson,
    within_stratum_slope,
)

THEME = "geography"
N_PERM = 2000
BIN = 5
MIN_BIN_N = 30
SINCE = 2000
LJ = frames.LJUBLJANA

# Where an award is administered, when that is not Ljubljana (from awards.institution).
# "municipal" awards are given by a town to its own people by statute, so a home bias
# there is expected; they are a check on the method, not a finding.
SEATS = {
    "borstnikov-prstan": ("Maribor", "Podravska", "national"),
    "borstnikovo-srecanje": ("Maribor", "Podravska", "national"),
    "vecernica": ("Maribor", "Podravska", "national"),
    "glazerjeva-nagrada": ("Maribor", "Podravska", "municipal"),
    "dnevi-komedije-celje": ("Celje", "Savinjska", "national"),
    "veronikina-nagrada": ("Celje", "Savinjska", "national"),
    "zlatnik-poezije": ("Celje", "Savinjska", "national"),
    "grumova-nagrada": ("Kranj", "Gorenjska", "national"),
    "grun-filipiceva-nagrada": ("Kranj", "Gorenjska", "national"),
    "seligova-nagrada": ("Kranj", "Gorenjska", "national"),
    "mms": ("Piran", "Obalno-kraška", "national"),
    "tantadruj": ("Nova Gorica", "Goriška", "national"),
    "hudi-macek": ("Ljutomer", "Pomurska", "national"),
    "slakov-hudi-macek": ("Ljutomer", "Pomurska", "national"),
    "hrupni-macek": ("Ljutomer", "Pomurska", "national"),
    "jazzon": ("Novo mesto", "Jugovzhodna Slovenija", "national"),
    "bernekerjeva-nagrada": ("Slovenj Gradec", "Koroška", "municipal"),
    "trdinova-nagrada": ("Novo mesto", "Jugovzhodna Slovenija", "municipal"),
}

# Awards given by a town to its own people (by statute): a home bias is expected.
MUNICIPAL = {a for a, (_, _, kind) in SEATS.items() if kind == "municipal"} | {
    "zupanciceva-nagrada"}  # Mestna občina Ljubljana

REGION_LABEL = {LJ: "Ljubljana", "Osrednjeslovenska": "Osrednjeslov. (brez LJ)",
                "Jugovzhodna Slovenija": "Jugovzhodna"}

GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SVN_{level}.json.zip"
GADM_DIR = PROJECT_ROOT / ".cache" / "geo"
GADM_RENAME = {"JugovzhodnaSlovenija": "Jugovzhodna Slovenija",
               "Notranjsko-kraška": "Primorsko-notranjska", "Spodnjeposavska": "Posavska"}


def run() -> dict:
    geo = frames.entity_geography().set_index("entity_id")
    roles = frames.roles()
    winners = attach(roles[roles["role"] == "winner"].drop_duplicates(["edition_id", "entity_id"]),
                     geo)
    jury = attach(frames.jury_sittings(), geo)
    cov = coverage(winners, jury)
    ts = shares_over_time(winners, jury)
    plot_shares_over_time(ts)
    rep = representation(winners, jury)
    plot_representation(rep)
    plot_map(rep)
    trend = within_award_trend(winners)
    per_award = award_vs_field(winners)
    plot_award_vs_field(per_award)
    home = home_advantage(winners)
    plot_home_advantage(home)
    jvw = jury_vs_winners(roles, geo)
    hom = homophily(roles, geo)
    plot_homophily(hom)
    path = jury_path(roles, geo)
    plot_jury_path(path)
    abroad = foreign_ties(roles, geo)
    plot_foreign_ties(abroad)

    return {
        "coverage": cov,
        "shares_by_period": ts,
        "shares_since_2000": overall(winners, jury),
        "richness": richness(winners, jury),
        "representation": rep,
        "within_award_trend": trend,
        "awards_vs_field": per_award,
        "awards_more_lj_than_field": per_award.loc[
            (per_award["q"] < 0.05) & (per_award["observed"] > per_award["expected"]),
            "award"].tolist(),
        "awards_less_lj_than_field": per_award.loc[
            (per_award["q"] < 0.05) & (per_award["observed"] < per_award["expected"]),
            "award"].tolist(),
        "home_advantage": home,
        "jury_vs_winners": jvw,
        "homophily": {k: v for k, v in hom.items() if k != "null"},
        "jury_path": {k: v for k, v in path.items() if k != "curves"}
        | {"km": {g: {f"{t}y": km_at(k, t) for t in (3, 5, 10)}
                  for g, k in path["curves"].items()}},
        "foreign_ties": abroad,
        "places": places(roles),
    }


# --- data -------------------------------------------------------------------------------

def attach(df: pd.DataFrame, geo: pd.DataFrame) -> pd.DataFrame:
    cols = ["units", "placed", "lj", "lj_only", "prov_only", "foreign_only", "n_si_units",
            "n_places"]
    out = df.join(geo[cols], on="entity_id")
    out["richness"] = out["n_si_units"].clip(upper=3)
    return out


def coverage(winners, jury) -> dict:
    def cov(df):
        return {"rows": len(df), "placed": float(df["placed"].mean()),
                "foreign_only": float(df["foreign_only"].mean()),
                "no_places": float((df["n_places"] == 0).mean())}
    return {"winners": cov(winners), "jury": cov(jury)}


def overall(winners, jury) -> dict:
    out = {}
    for role, df in (("winner", winners), ("jury", jury)):
        d = df[(df["year"] >= SINCE) & df["placed"]]
        out[role] = {"n": len(d), "people": int(d["entity_id"].nunique()),
                     **{m: float(d[m].mean()) for m in ("lj", "lj_only", "prov_only")}}
    return out


def richness(winners, jury) -> dict:
    """How biography richness drives the strict measures."""
    w = winners[(winners["year"] >= SINCE) & winners["placed"]]
    by = w.groupby("richness")[["lj", "lj_only", "prov_only"]].mean()
    by["n"] = w.groupby("richness").size()
    return {
        "winners_by_units": by.reset_index(),
        "mean_units_winners": float(w["n_si_units"].mean()),
        "mean_units_jury": float(jury.loc[(jury["year"] >= SINCE) & jury["placed"],
                                          "n_si_units"].mean()),
    }


# --- 1. shares over time ----------------------------------------------------------------

def shares_over_time(winners, jury) -> pd.DataFrame:
    rows = []
    for role, df in (("winner", winners), ("jury", jury)):
        d = df[df["placed"]].copy()
        d["bin"] = d["year"] // BIN * BIN
        for b, g in d.groupby("bin"):
            if len(g) < MIN_BIN_N:
                continue
            for m in ("lj", "lj_only", "prov_only"):
                k = int(g[m].sum())
                lo, hi = wilson(k, len(g))
                rows.append({"role": role, "bin": int(b), "measure": m, "n": len(g),
                             "share": k / len(g), "lo": float(lo), "hi": float(hi)})
    return pd.DataFrame(rows)


def plot_shares_over_time(ts):
    """Only the 'any tie' measure: 'Ljubljana only' drifts with how detailed the
    biographies are (see within_award_trend), so its raw trend would mislead."""
    fig, ax = P.figure(8.5, 4.6)
    colors = P.ROLE_COLOR
    ends = []
    for role, c in colors.items():
        d = ts[(ts["role"] == role) & (ts["measure"] == "lj")]
        x = d["bin"] + BIN / 2
        ax.fill_between(x, d["lo"], d["hi"], color=c, alpha=0.15, lw=0)
        ax.plot(x, d["share"], color=c, marker="o", ms=4)
        ends.append([float(d["share"].iloc[-1]), role, c, float(x.iloc[-1])])
    ends.sort()
    for i in range(1, len(ends)):  # keep end labels apart
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 0.035)
    for y, role, c, x in ends:
        ax.annotate(P.ROLE_LABEL[role], (x, y), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9, color=c)
    ax.set_ylim(0.5, 1.0)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel(f"obdobje ({BIN}-letno)")
    ax.set_title("Devet od desetih ima vez z Ljubljano, in tako je že 70 let")
    P.subtitle(ax, "Delež ljudi z vsaj eno slovensko vezjo, ki imajo med njimi Ljubljano · "
                   f"pas = 95 % interval · obdobja z vsaj {MIN_BIN_N} ljudmi\n"
                   "Vezi so kraji iz življenjepisa (rojstvo, šolanje, delo), ne prebivališče")
    P.source_note(fig)
    P.save(fig, THEME, "ljubljana_skozi_cas")


# --- 2. representation vs population ----------------------------------------------------

def representation(winners, jury) -> pd.DataFrame:
    """Distinct people since SINCE; each person's weight (1) is split evenly across their
    units. index = share of people / share of population."""
    pop = frames.table("regions").set_index("region")["population"].astype(float)
    pop_share = pop / pop.sum()
    out = []
    for role, df in (("winner", winners), ("jury", jury)):
        people = df[(df["year"] >= SINCE) & df["placed"]].drop_duplicates("entity_id")
        w = people["units"].explode().to_frame("unit")
        w["weight"] = 1 / people["n_si_units"].reindex(w.index).to_numpy()
        share = w.groupby("unit")["weight"].sum() / len(people)
        # Bootstrap over people for an interval on the index.
        g = rng()
        mat = np.zeros((len(people), len(pop)))
        col = {u: i for i, u in enumerate(pop.index)}
        for i, (units, n) in enumerate(zip(people["units"], people["n_si_units"])):
            for u in units:
                mat[i, col[u]] = 1 / n
        boots = np.array([mat[g.integers(0, len(people), len(people))].mean(axis=0)
                          for _ in range(1000)])
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        for u in pop.index:
            out.append({"role": role, "unit": u, "people": len(people),
                        "share": float(share.get(u, 0.0)), "pop_share": float(pop_share[u]),
                        "index": float(share.get(u, 0.0) / pop_share[u]),
                        "index_lo": float(lo[col[u]] / pop_share[u]),
                        "index_hi": float(hi[col[u]] / pop_share[u])})
    return pd.DataFrame(out)


def plot_representation(rep):
    w = rep[rep["role"] == "winner"].sort_values("index")
    j = rep[rep["role"] == "jury"].set_index("unit").loc[w["unit"]]
    fig, ax = P.figure(8.5, 5.6)
    y = np.arange(len(w))
    ax.axvline(1, color=P.TEXT_2, lw=1)
    for off, d, c, lab in ((-0.17, w, P.SERIES[2], "nagrajenci"), (0.17, j, P.SERIES[0], "žirija")):
        ax.hlines(y + off, d["index_lo"], d["index_hi"], color=c, lw=2, alpha=0.4)
        ax.scatter(d["index"], y + off, color=c, s=36, zorder=3, label=lab)
    for yi, (_, r) in zip(y, w.iterrows()):
        ax.annotate(f"{P.dec(r['index'], 1)}×", (max(r["index_hi"], j.loc[r["unit"], "index_hi"]), yi),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8,
                    color=P.TEXT_2)
    ax.set_xscale("log")
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([0.1, 0.25, 0.5, 1, 2, 4, 8])
    ax.set_xticklabels([P.dec(v, 2 if v < 0.5 else 1).rstrip("0").rstrip(",") for v in
                        [0.1, 0.25, 0.5, 1, 2, 4, 8]])
    ax.set_yticks(y)
    ax.set_yticklabels([REGION_LABEL.get(u, u) for u in w["unit"]])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("zastopanost glede na prebivalstvo (1 = sorazmerno, logaritemska os)")
    ax.legend(loc="lower right")
    lj_idx = P.dec(w.set_index("unit").loc[LJ, "index"], 1)
    ax.set_title(f"Ljubljana ima {lj_idx}-krat več nagrajencev, kot bi jih imela po prebivalstvu")
    people = int(w["people"].iloc[0])
    P.subtitle(ax, f"Ljudje, nagrajeni ali v žiriji od leta {SINCE} · oseba z vezmi na več "
                   "regij šteje deljeno\n"
                   f"{people} nagrajencev · črta = 95 % interval (bootstrap) · prebivalstvo "
                   "1. 1. 2025 (SURS)")
    P.source_note(fig)
    P.save(fig, THEME, "zastopanost_regij")


def _gadm(level: int) -> dict:
    path = GADM_DIR / f"gadm41_SVN_{level}.json"
    if not path.exists():
        GADM_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(GADM_URL.format(level=level), timeout=120) as r:
            z = zipfile.ZipFile(BytesIO(r.read()))
        path.write_bytes(z.read(next(n for n in z.namelist() if n.endswith(".json"))))
    return json.loads(path.read_text(encoding="utf-8"))


def _rings(geom) -> list:
    parts = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [np.array(p[0]) for p in parts]


def plot_map(rep):
    try:
        munis = _gadm(2)
        regions = _gadm(1)
    except OSError as e:  # offline: skip the map, keep the rest
        print(f"  map skipped: {e}")
        return
    idx = rep[rep["role"] == "winner"].set_index("unit")["index"]
    norm = LogNorm(vmin=0.1, vmax=10)
    fig, ax = P.figure(9, 6)
    polys, faces = [], []
    for ft in munis["features"]:
        pr = ft["properties"]
        unit = LJ if pr["NAME_2"] == "Ljubljana" else GADM_RENAME.get(pr["NAME_1"], pr["NAME_1"])
        for ring in _rings(ft["geometry"]):
            polys.append(ring)
            faces.append(P.DIVERGING(norm(idx[unit])))
    ax.add_collection(PolyCollection(polys, facecolors=faces, edgecolors=faces, linewidths=0.3))
    outlines = [r for ft in regions["features"] for r in _rings(ft["geometry"])]
    outlines += [r for ft in munis["features"] if ft["properties"]["NAME_2"] == "Ljubljana"
                 for r in _rings(ft["geometry"])]
    ax.add_collection(PolyCollection(outlines, facecolors="none", edgecolors=P.SURFACE,
                                     linewidths=1.2))
    for ft in regions["features"]:
        name = GADM_RENAME.get(ft["properties"]["NAME_1"], ft["properties"]["NAME_1"])
        ring = max(_rings(ft["geometry"]), key=len)
        x, y = ring[:, 0].mean(), ring[:, 1].mean()
        if name == "Osrednjeslovenska":  # keep clear of the Ljubljana label
            x, y = 14.62, 45.83
        ax.text(x, y, f"{REGION_LABEL.get(name, name)}\n{P.dec(idx[name], 2)}×", ha="center",
                va="center", fontsize=7.5, color=P.TEXT)
    lj = next(ft for ft in munis["features"] if ft["properties"]["NAME_2"] == "Ljubljana")
    ring = max(_rings(lj["geometry"]), key=len)
    ax.annotate(f"Ljubljana\n{P.dec(idx[LJ], 1)}×", (ring[:, 0].mean(), ring[:, 1].mean()),
                xytext=(-10, 42), textcoords="offset points", ha="center", fontsize=9,
                fontweight="bold", color=P.TEXT, arrowprops={"arrowstyle": "-", "color": P.TEXT_2})
    ax.autoscale_view()
    ax.set_aspect(1 / np.cos(np.radians(46.1)))
    ax.set_axis_off()
    ax.set_title("Nagrajenci glede na prebivalstvo regije")
    P.subtitle(ax, f"Nagrajenci od leta {SINCE} · 1× = sorazmerno prebivalstvu · rdeče = "
                   "nadpovprečno, modro = podpovprečno")
    P.source_note(fig, "Vir: zbirka Kulturne nagrade · meje: GADM 4.1 · prebivalstvo: SURS")
    P.save(fig, THEME, "zemljevid_zastopanosti")


# --- trend within award -----------------------------------------------------------------

def within_award_trend(winners) -> dict:
    d = winners[winners["placed"]].copy()
    d["decade_c"] = (d["year"] - 2000) / 10
    out = {}
    for m in ("lj", "lj_only", "prov_only"):
        d["y"] = d[m].astype(float)
        raw = smf.ols("y ~ decade_c", d).fit(cov_type="cluster",
                                             cov_kwds={"groups": d["award_id"]})
        fe = smf.ols("y ~ decade_c + C(award_id) + C(richness)", d).fit(
            cov_type="cluster", cov_kwds={"groups": d["award_id"]})
        out[m] = {"raw_per_decade": float(raw.params["decade_c"]),
                  "fe_per_decade": float(fe.params["decade_c"]),
                  "fe_ci": [float(v) for v in fe.conf_int().loc["decade_c"]],
                  "fe_p": float(fe.pvalues["decade_c"]), "n": len(d)}
    return out


# --- 3./4. award vs field peers ---------------------------------------------------------

def _vs_peers(w: pd.DataFrame, hit, award_ids=None) -> pd.DataFrame:
    """For each award, count its winners with hit(person, award) True, against a null
    that shuffles award labels within (genre, year, richness) pools.

    hit(units_series, award_id) -> boolean array for the pool's people.
    """
    w = w[w["placed"]].reset_index(drop=True)
    awards = sorted(w["award_id"].unique())
    a_idx = {a: i for i, a in enumerate(awards)}
    observed = np.zeros(len(awards))
    n_comp = np.zeros(len(awards))
    null = np.zeros((N_PERM, len(awards)))
    g = rng()
    for _, grp in w.groupby(["genre", "year", "richness"]):
        labels = grp["award_id"].map(a_idx).to_numpy()
        present = np.unique(labels)
        if len(present) < 2:
            continue
        M = np.column_stack([hit(grp, awards[a]) for a in present]).astype(float)
        col = np.searchsorted(present, labels)
        np.add.at(observed, labels, M[np.arange(len(labels)), col])
        np.add.at(n_comp, labels, 1)
        perms = np.argsort(g.random((N_PERM, len(labels))), axis=1)
        pcol = col[perms]
        hits = M[np.arange(len(labels))[None, :], pcol]
        for k, a in enumerate(present):
            null[:, a] += (hits * (pcol == k)).sum(axis=1)
    keep = n_comp > 0
    if award_ids is not None:
        keep &= np.isin(awards, list(award_ids))
    per = pd.DataFrame({
        "award_id": np.array(awards)[keep], "winners": n_comp[keep].astype(int),
        "observed": observed[keep].astype(int), "expected": null[:, keep].mean(axis=0)})
    per["share"] = per["observed"] / per["winners"]
    per["expected_share"] = per["expected"] / per["winners"]
    per["p"] = [permutation_p(abs(o - e), np.abs(null[:, a_idx[a]] - e))
                for o, e, a in zip(per["observed"], per["expected"], per["award_id"])]
    per["q"] = bh_fdr(per["p"])
    return per.merge(frames.awards()[["award_id", "name", "genre"]]
                     .rename(columns={"name": "award"})).sort_values("p").reset_index(drop=True)


def award_vs_field(winners) -> pd.DataFrame:
    """Two-sided: Ljubljana tie among an award's winners vs field-year-richness peers."""
    per = _vs_peers(winners, lambda grp, a: grp["lj"].to_numpy())
    per["municipal"] = per["award_id"].isin(MUNICIPAL)
    return per


def plot_award_vs_field(per, min_n: int = 25):
    d = per[per["winners"] >= min_n].copy()
    d["diff"] = d["share"] - d["expected_share"]
    d = d.sort_values("diff")
    fig, ax = P.figure(8.5, 0.27 * len(d) + 2)
    y = np.arange(len(d))
    sig = d["q"] < 0.05
    ax.hlines(y, d["expected_share"], d["share"], color=P.GRID, lw=3)
    ax.scatter(d["expected_share"], y, s=40, color=P.MUTED, zorder=3,
               label="pričakovano pri vrstnikih")
    ax.scatter(d["share"], y, s=46, zorder=4, label="nagrada",
               color=np.where(sig, np.where(d["diff"] > 0, P.SERIES[7], P.SERIES[0]), P.TEXT_2))
    ax.set_yticks(y)
    ax.set_yticklabels([f"{a}{' *' if s else ''}{' †' if i in MUNICIPAL else ''}"
                        for a, s, i in zip(d["award"], sig, d["award_id"])], fontsize=8)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("delež nagrajencev z vezjo na Ljubljano")
    _dumbbell_legend(ax)
    ax.set_title("Katere nagrade so bolj ljubljanske od svojega področja?")
    P.subtitle(ax, "Primerjava z nagrajenci drugih nagrad istega področja, leta in enako "
                   "bogatega življenjepisa\n"
                   f"* = razlika ostane po popravku za {len(per)} testov (q < 0,05) · "
                   f"† = občinska nagrada · nagrade z vsaj {min_n} primerljivimi nagrajenci")
    P.source_note(fig)
    P.save(fig, THEME, "nagrade_proti_podrocju")


def _dumbbell_legend(ax):
    dot = {"marker": "o", "ls": "", "ms": 7}
    ax.legend(handles=[Line2D([], [], color=P.MUTED, label="pričakovano pri vrstnikih", **dot),
                       Line2D([], [], color=P.TEXT_2, label="nagrada", **dot),
                       Line2D([], [], color=P.SERIES[7], label="nagrada, značilno več", **dot),
                       Line2D([], [], color=P.SERIES[0], label="nagrada, značilno manj", **dot)],
              loc="lower right")


def home_advantage(winners) -> pd.DataFrame:
    per = _vs_peers(winners, lambda grp, a: grp["units"].apply(
        lambda u: SEATS[a][1] in u if a in SEATS else False).to_numpy(), award_ids=SEATS)
    per["q"] = bh_fdr(per["p"])  # within the seated awards only
    per["seat"] = per["award_id"].map(lambda a: SEATS[a][0])
    per["region"] = per["award_id"].map(lambda a: SEATS[a][1])
    per["kind"] = per["award_id"].map(lambda a: SEATS[a][2])
    per["municipal"] = per["award_id"].isin(MUNICIPAL)
    per["ratio"] = per["observed"] / per["expected"].where(per["expected"] > 0)
    return per


def plot_home_advantage(home, min_n: int = 10):
    d = home[home["winners"] >= min_n].sort_values("share")
    fig, ax = P.figure(8.5, 0.36 * len(d) + 2)
    y = np.arange(len(d))
    ax.hlines(y, d["expected_share"], d["share"], color=P.GRID, lw=3)
    ax.scatter(d["expected_share"], y, s=40, color=P.MUTED, zorder=3,
               label="pričakovano pri vrstnikih")
    ax.scatter(d["share"], y, s=46, color=np.where(d["q"] < 0.05, P.SERIES[7], P.TEXT_2),
               zorder=4, label="nagrada")
    labels = [f"{a} ({s}){' *' if q < 0.05 else ''}{' †' if k == 'municipal' else ''}"
              for a, s, q, k in zip(d["award"], d["seat"], d["q"], d["kind"])]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("delež nagrajencev z vezjo na regijo sedeža nagrade")
    _dumbbell_legend(ax)
    ax.set_title("Ali nagrade zunaj Ljubljane nagrajujejo domačine?")
    P.subtitle(ax, "Primerjava z nagrajenci drugih nagrad istega področja, leta in enako "
                   "bogatega življenjepisa\n* = q < 0,05 · † = občinska nagrada (domačini po "
                   "pravilniku) · nagrade z vsaj "
                   f"{min_n} primerljivimi nagrajenci")
    P.source_note(fig)
    P.save(fig, THEME, "domaca_prednost")


# --- 5. jury vs winners -----------------------------------------------------------------

def jury_vs_winners(roles, geo) -> dict:
    """Stack the jurors and winners of each edition with a known jury; regress the
    measure on is_jury with edition fixed effects and richness controls (SE by award)."""
    d = roles[roles["edition_id"].isin(roles.loc[roles["role"] == "jury", "edition_id"])]
    d = attach(d.drop_duplicates(["edition_id", "entity_id", "role"]), geo)
    d = d[d["placed"]].copy()
    d["is_jury"] = (d["role"] == "jury").astype(float)
    both = d.groupby("edition_id")["role"].nunique() == 2
    d = d[d["edition_id"].isin(both[both].index)]
    out = {"n_editions": int(d["edition_id"].nunique()), "n_rows": len(d)}
    for m in ("lj", "lj_only", "prov_only"):
        d["y"] = d[m].astype(float)
        fit = smf.ols("y ~ is_jury + C(richness) + C(edition_id)", d).fit(
            cov_type="cluster", cov_kwds={"groups": d["award_id"]})
        out[m] = {"jury_share": float(d.loc[d["is_jury"] == 1, m].mean()),
                  "winner_share": float(d.loc[d["is_jury"] == 0, m].mean()),
                  "diff_within_edition": float(fit.params["is_jury"]),
                  "ci": [float(v) for v in fit.conf_int().loc["is_jury"]],
                  "p": float(fit.pvalues["is_jury"])}
    return out


# --- 6. regional homophily --------------------------------------------------------------

def homophily(roles, geo) -> dict:
    """Do juries with more members from outside Ljubljana pick more winners from outside
    Ljubljana? Same design as gender homophily: winner-level LPM, x = share of the
    edition's placed jurors who are outside-Ljubljana-only, y = winner is; award × decade
    fixed effects plus winner richness; permutation of jury compositions within strata."""
    r = attach(roles, geo)
    r = r[r["placed"]]
    jur = (r[r["role"] == "jury"].groupby("edition_id")["prov_only"]
           .agg(jury_prov="mean", jury_n="size"))
    d = r[r["role"] == "winner"].merge(jur, left_on="edition_id", right_index=True)
    d = d[d["jury_n"] >= 3].copy()
    d["y"] = d["prov_only"].astype(float)
    d["stratum"] = d["award_id"] + "_" + (d["year"] // 10 * 10).astype(str)
    return within_stratum_slope(d, "jury_prov", "y", "stratum", "edition_id",
                                controls="+ C(richness)", n_perm=N_PERM)


def plot_homophily(h):
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
    ax.set_xlabel("sprememba verjetnosti, da zmaga nekdo brez vezi z Ljubljano, če so vsi "
                  "žiranti od drugod\nnamesto nobeden")
    ax.xaxis.set_major_formatter(lambda v, _: P.dec(v, 1))
    ax.set_ylabel("permutacije")
    ax.grid(axis="y", visible=False)
    ax.set_title("Ali žirije od drugod nagrajujejo ljudi od drugod?")
    P.subtitle(ax, "Primerjava znotraj iste nagrade in desetletja · histogram = naključno "
                   f"premešane žirije ({N_PERM}×)\n{h['n_winners']} nagrajencev, "
                   f"{h['n_editions']} podelitev, {h['n_awards']} nagrad")
    P.source_note(fig)
    P.save(fig, THEME, "regionalna_homofilija")


# --- 7. the path into juries ------------------------------------------------------------

PATH_FROM = 2000
PATH_HORIZON = 10
PATH_LABEL = {True: "z vezjo na Ljubljano", False: "brez vezi z Ljubljano"}


def jury_path(roles, geo) -> dict:
    """Time from a first win (since PATH_FROM) to a first jury seat, Ljubljana tie vs
    none. Same cohort rules as careers.winner_to_juror: people who judged before their
    first win are left out. Cox model stratified by the field of the first award, with
    richness dummies; robustness: strata by award, municipal awards left out."""
    w = (roles[roles["role"] == "winner"].sort_values(["year", "prestige"],
                                                      ascending=[True, False])
         .drop_duplicates("entity_id"))
    first_jury = frames.jury_sittings().groupby("entity_id")["year"].min()
    f = w[w["year"] >= PATH_FROM][["entity_id", "year", "genre", "award_id"]].copy()
    f["first_jury"] = f["entity_id"].map(first_jury)
    f = f[~(f["first_jury"] <= f["year"]).fillna(False).astype(bool)]
    f = attach(f, geo)
    f = f[f["placed"].fillna(False).astype(bool)].copy()
    end_year = int(roles["year"].max())
    f["event"] = f["first_jury"].notna()
    f["t"] = (f["first_jury"].fillna(end_year) - f["year"]).astype(float)
    curves = {PATH_LABEL[g]: kaplan_meier(d["t"], d["event"]) for g, d in f.groupby("lj")}

    def cox(d, strata):
        x = np.column_stack([d["lj"], d["richness"] == 2, d["richness"] >= 3]).astype(float)
        fit = PHReg(d["t"].clip(lower=0.5).to_numpy(), x, status=d["event"].to_numpy(),
                    strata=d[strata].to_numpy()).fit()
        return {"hr": float(np.exp(fit.params[0])),
                "ci": [float(v) for v in np.exp(fit.conf_int()[0])],
                "p": float(fit.pvalues[0]), "n": len(d), "n_outside": int((~d["lj"]).sum())}

    return {"n": len(f), "n_lj": int(f["lj"].sum()), "n_outside": int((~f["lj"]).sum()),
            "events": int(f["event"].sum()), "curves": curves,
            "cox_by_field": cox(f, "genre"), "cox_by_award": cox(f, "award_id"),
            "cox_no_municipal": cox(f[~f["award_id"].isin(MUNICIPAL)], "genre")}


def plot_jury_path(path):
    fig, ax = P.figure(8.5, 4.8)
    colors = {PATH_LABEL[True]: P.SERIES[6], PATH_LABEL[False]: P.SERIES[1]}
    for label, k in path["curves"].items():
        k = k[k["t"] <= PATH_HORIZON]
        c = colors[label]
        ax.step(k["t"], k["cum_incidence"], where="post", color=c, lw=2, label=label)
        ax.fill_between(k["t"], k["lo"], k["hi"], step="post", color=c, alpha=0.12, lw=0)
        end = k.iloc[-1]
        ax.annotate(P.pct(end["cum_incidence"]), (end["t"], end["cum_incidence"]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9)
    ax.set_xlim(0, PATH_HORIZON + 1)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel("let po prvi nagradi")
    ax.legend(loc="upper left")
    hr = path["cox_by_field"]
    verdict = ("razlika verjetno ni naključna" if hr["p"] < 0.05
               else "razlika je lahko naključna")
    ax.set_title("Nagrajenci, povezani z Ljubljano, pogosteje sedejo v žirijo")
    P.subtitle(ax, f"Prvič nagrajeni od leta {PATH_FROM}, ki pred tem niso sodili · "
                   f"{path['n_lj']} z vezjo na Ljubljano, {path['n_outside']} brez nje\n"
                   f"Na istem področju {P.dec(hr['hr'], 1)}-krat hitreje; {verdict} · "
                   "upošteva, da so nedavni nagrajenci imeli manj časa")
    P.source_note(fig)
    P.save(fig, THEME, "pot_v_zirijo")


# --- 8. ties abroad ---------------------------------------------------------------------

EX_YU = {"hr", "rs", "ba", "mk", "me", "xk"}


def foreign_ties(roles, geo) -> dict:
    """Winner-editions of people with any recorded place. Measures: any foreign tie, a
    tie to former Yugoslavia (outside Slovenia), a tie elsewhere abroad. Raw shares by
    decade; within the same award, controlling for the number of places listed (older
    biographies list more places): the linear trend per decade, and a break at 1991 on
    top of that trend, against placebo breaks ten years either side."""
    loc = frames.table("entity_locations").merge(frames.table("places"), on="place")
    fo = loc[loc["scope"] == "foreign"]
    per = fo.groupby("entity_id").agg(
        ex_yu=("country_code", lambda s: s.isin(EX_YU).any()),
        west=("country_code", lambda s: (~s.isin(EX_YU) & s.notna()).any()))
    w = roles[roles["role"] == "winner"].drop_duplicates(["edition_id", "entity_id"])
    w = w.join(geo[["n_places"]], on="entity_id")
    w = w[w["n_places"].fillna(0) > 0].join(per, on="entity_id")
    for c in ("ex_yu", "west"):
        w[c] = w[c].fillna(False).astype(float)
    w["any"] = w[["ex_yu", "west"]].max(axis=1)
    w["lnp"] = np.log1p(w["n_places"].astype(float))
    w["yc"] = (w["year"].astype(float) - 1991) / 10
    w["decade"] = w["year"] // 10 * 10
    by = w.groupby("decade").agg(n=("any", "size"), any=("any", "mean"), ex_yu=("ex_yu", "mean"),
                                 west=("west", "mean"), places=("n_places", "mean"))
    by = by[by["n"] >= MIN_BIN_N].reset_index()
    fit = lambda f: smf.ols(f, w).fit(cov_type="cluster", cov_kwds={"groups": w["award_id"]})
    out = {"by_decade": by, "n": len(w), "trend": {}, "breaks": {}}
    for m in ("any", "ex_yu", "west"):
        t = fit(f"{m} ~ yc + lnp + C(award_id)")
        out["trend"][m] = {"per_decade": float(t.params["yc"]),
                           "ci": [float(v) for v in t.conf_int().loc["yc"]],
                           "p": float(t.pvalues["yc"])}
    for brk in (1981, 1991, 2001):
        w["post"] = (w["year"] >= brk).astype(float)
        t = fit("ex_yu ~ post + yc + lnp + C(award_id)")
        out["breaks"][brk] = {"jump": float(t.params["post"]),
                              "ci": [float(v) for v in t.conf_int().loc["post"]],
                              "p": float(t.pvalues["post"])}
    return out


def _points(x: float) -> str:
    n = round(x)
    m = abs(n) % 100
    return f"{n} " + ("odstotna točka" if m == 1 else "odstotni točki" if m == 2 else
                      "odstotne točke" if m in (3, 4) else "odstotnih točk")


def plot_foreign_ties(f):
    by = f["by_decade"]
    fig, ax = P.figure(8.5, 4.6)
    for m, c, lab in (("ex_yu", P.SERIES[1], "nekdanja Jugoslavija"),
                      ("west", P.SERIES[0], "drugod v tujini")):
        ax.plot(by["decade"] + 5, by[m], color=c, marker="o", ms=4)
        ax.annotate(lab, (by["decade"].iloc[-1] + 5, by[m].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=c)
    ax.axvline(1991, color=P.MUTED, lw=1, ls=":")
    ax.annotate("1991", (1991, 0.02), xytext=(4, 0), textcoords="offset points", fontsize=8,
                color=P.TEXT_2)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel("desetletje nagrade")
    tr = f["trend"]["ex_yu"]["per_decade"]
    ax.set_title("Vezi z nekdanjo Jugoslavijo so se rahljale postopoma, ne šele leta 1991")
    P.subtitle(ax, "Delež nagrajencev s krajem v tujini v življenjepisu · starejši "
                   "življenjepisi naštejejo več krajev\n"
                   f"Pri isti nagradi in enako podrobnem življenjepisu: vezi z nekdanjo "
                   f"Jugoslavijo {_points(-100 * tr)} manj na desetletje, "
                   "brez preloma ob osamosvojitvi")
    P.source_note(fig)
    P.save(fig, THEME, "vezi_s_tujino")


# --- 9. places (site map) ---------------------------------------------------------------

def places(roles) -> pd.DataFrame:
    """Distinct people tied to each Slovenian settlement, by role, all years. Places
    inside Ljubljana's city municipality are merged into Ljubljana; vague regional ties
    ("Primorska") are left out."""
    loc = frames.table("entity_locations").merge(frames.table("places"), on="place")
    si = loc[(loc["scope"] == "si") & (loc["kind"] == "settlement") & loc["lat"].notna()].copy()
    lj = si["is_ljubljana"].astype(bool)
    si.loc[lj, "canonical"] = LJ
    coords = si.groupby("canonical")[["lat", "lon"]].median()
    coords.loc[LJ] = (46.0511, 14.5051)
    region = si.groupby("canonical")["si_region"].agg(lambda s: s.mode().iat[0])
    region.loc[LJ] = LJ
    who = roles.drop_duplicates(["entity_id", "role"])[["entity_id", "role"]]
    tied = si.drop_duplicates(["entity_id", "canonical"])[["entity_id", "canonical"]]
    m = tied.merge(who, on="entity_id")
    out = (m.pivot_table(index="canonical", columns="role", values="entity_id",
                         aggfunc="nunique", fill_value=0)
           .rename(columns={"winner": "winners"}))
    out["people"] = m.groupby("canonical")["entity_id"].nunique()
    out = out.join(coords).join(region.rename("region")).reset_index()
    return out.rename(columns={"canonical": "place"}).sort_values("people", ascending=False)
