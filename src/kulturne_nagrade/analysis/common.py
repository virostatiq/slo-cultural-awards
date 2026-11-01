"""Statistical helpers shared by the analysis modules."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from kulturne_nagrade import PROJECT_ROOT

RESULTS_DIR = PROJECT_ROOT / "results"
RNG_SEED = 20261101


def rng() -> np.random.Generator:
    return np.random.default_rng(RNG_SEED)


def wilson(k, n, z: float = 1.96):
    """Wilson score interval for a proportion. Works on scalars and arrays."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = k / n
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def bh_fdr(p: pd.Series) -> pd.Series:
    """Benjamini–Hochberg adjusted p-values (q-values)."""
    p = p.astype(float)
    order = p.sort_values().index
    m = len(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1].clip(upper=1)
    return pd.Series(q.values, index=order).reindex(p.index)


def kaplan_meier(duration: pd.Series, event: pd.Series) -> pd.DataFrame:
    """Kaplan–Meier estimate of the share who have had the event by time t.

    duration: time to event or to censoring; event: True if observed.
    Returns columns t, at_risk, events, cum_incidence (1 - S(t)), lo, hi (Greenwood, log-log).
    """
    d = pd.DataFrame({"t": duration.astype(float), "e": event.astype(bool)}).dropna()
    times = np.sort(d.loc[d["e"], "t"].unique())
    rows, s, var_sum = [], 1.0, 0.0
    for t in times:
        at_risk = (d["t"] >= t).sum()
        events = ((d["t"] == t) & d["e"]).sum()
        s *= 1 - events / at_risk
        if at_risk > events:
            var_sum += events / (at_risk * (at_risk - events))
        if 0 < s < 1:
            se = np.sqrt(var_sum) / abs(np.log(s))
            lo_s, hi_s = s ** np.exp(1.96 * se), s ** np.exp(-1.96 * se)
        else:
            lo_s = hi_s = s
        rows.append((t, at_risk, events, 1 - s, 1 - hi_s, 1 - lo_s))
    out = pd.DataFrame(rows, columns=["t", "at_risk", "events", "cum_incidence", "lo", "hi"])
    start = pd.DataFrame([{"t": 0.0, "at_risk": len(d), "events": 0, "cum_incidence": 0.0,
                           "lo": 0.0, "hi": 0.0}])
    return pd.concat([start, out[out["t"] > 0]], ignore_index=True)


def km_at(km: pd.DataFrame, t: float) -> float:
    """Cumulative incidence at time t from a kaplan_meier() table."""
    return float(km.loc[km["t"] <= t, "cum_incidence"].iloc[-1])


def permutation_p(observed: float, null: np.ndarray, alternative: str = "greater") -> float:
    null = np.asarray(null)
    if alternative == "greater":
        k = (null >= observed).sum()
    elif alternative == "less":
        k = (null <= observed).sum()
    else:
        k = (np.abs(null - null.mean()) >= abs(observed - null.mean())).sum()
    return (k + 1) / (len(null) + 1)


def decade(year) -> pd.Series:
    return (pd.Series(year) // 10 * 10).astype("Int64")


def save_results(theme: str, results: dict) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{theme}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=_jsonable) + "\n",
                    encoding="utf-8")


def _jsonable(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if np.isnan(x) else round(float(x), 4)
    if isinstance(x, pd.DataFrame):
        return x.to_dict(orient="records")
    if isinstance(x, pd.Series):
        return x.to_dict()
    if x is pd.NA:
        return None
    raise TypeError(type(x))


def within_stratum_slope(d: pd.DataFrame, x: str, y: str, stratum: str, unit: str,
                         controls: str = "", n_perm: int = 2000,
                         cluster: str = "award_id") -> dict:
    """Effect of an edition-level x (e.g. a jury's composition) on a winner-level y.

    d has one row per winner; `unit` identifies the edition, x is constant within it.
    Reports the raw OLS slope, the slope with stratum fixed effects (plus optional
    `controls`, a formula fragment such as "+ C(richness)"), both with SE clustered by
    `cluster`, and a permutation test that reassigns x among editions of the same
    stratum. Strata without variation in x or y carry no within information and are
    dropped first.
    """
    import statsmodels.formula.api as smf

    var = d.groupby(stratum).agg(xv=(x, "nunique"), yv=(y, "nunique"))
    d = d[d[stratum].isin(var[(var["xv"] > 1) & (var["yv"] > 1)].index)].reset_index(drop=True)
    groups_cl = {"groups": d[cluster]}
    raw = smf.ols(f"{y} ~ {x}", d).fit(cov_type="cluster", cov_kwds=groups_cl)
    fe = smf.ols(f"{y} ~ {x} {controls} + C({stratum})", d).fit(cov_type="cluster",
                                                                  cov_kwds=groups_cl)
    eds = d.drop_duplicates(unit)[[unit, stratum, x]].reset_index(drop=True)
    pos = d[unit].map(pd.Series(eds.index, index=eds[unit])).to_numpy()
    strata = d[stratum].to_numpy()
    y_dm = (d[y] - d.groupby(stratum)[y].transform("mean")).to_numpy()

    def beta(x_eds: np.ndarray) -> float:
        xs = pd.Series(x_eds[pos])
        x_dm = (xs - xs.groupby(strata).transform("mean")).to_numpy()
        return float((x_dm * y_dm).sum() / (x_dm**2).sum())

    vals = eds[x].to_numpy(dtype=float)
    observed = beta(vals)
    groups = [idx.to_numpy() for idx in eds.groupby(stratum).groups.values()]
    g, null = rng(), np.empty(n_perm)
    for i in range(n_perm):
        perm = vals.copy()
        for idx in groups:
            perm[idx] = g.permutation(vals[idx])
        null[i] = beta(perm)
    return {
        "n_winners": len(d), "n_editions": int(d[unit].nunique()),
        "n_strata": int(d[stratum].nunique()), "n_awards": int(d["award_id"].nunique()),
        "raw_slope": float(raw.params[x]), "raw_ci": [float(v) for v in raw.conf_int().loc[x]],
        "fe_slope": float(fe.params[x]), "fe_ci": [float(v) for v in fe.conf_int().loc[x]],
        "fe_p": float(fe.pvalues[x]),
        "perm_slope": observed, "perm_p": permutation_p(observed, null, "two-sided"),
        "null": null,
    }
