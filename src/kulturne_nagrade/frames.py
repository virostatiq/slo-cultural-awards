"""Analysis-ready pandas views of the dataset.

Everything an analysis needs should come from here, so that filters (period, entity
types) and caveats (coverage, estimated ages) are handled the same way everywhere.
"""

from __future__ import annotations

from functools import cache

import pandas as pd

from kulturne_nagrade import DATA_DIR
from kulturne_nagrade.dataset import SCHEMA

_PD_TYPES = {"integer": "Int64", "number": "Float64", "boolean": "boolean", "string": "string",
             "date": "string"}


@cache
def _table(name: str) -> pd.DataFrame:
    dtypes = {f["name"]: _PD_TYPES[f["type"]] for f in SCHEMA[name]["fields"]}
    bools = [c for c, t in dtypes.items() if t == "boolean"]
    read_types = {c: ("string" if t == "boolean" else t) for c, t in dtypes.items()}
    df = pd.read_csv(DATA_DIR / f"{name}.csv", dtype=read_types,
                     keep_default_na=False, na_values=[""])
    for c in bools:
        df[c] = df[c].map({"True": True, "False": False}).astype("boolean")
    return df


def table(name: str) -> pd.DataFrame:
    """A copy of one raw table with schema dtypes (nullable Int64, string, boolean)."""
    return _table(name).copy()


def awards() -> pd.DataFrame:
    return table("awards")


def entities() -> pd.DataFrame:
    return table("entities")


def editions(min_year: int | None = None, max_year: int | None = None) -> pd.DataFrame:
    """Editions joined with award attributes."""
    ed = table("editions").merge(
        awards()[["award_id", "name", "genre", "prestige", "funding_source"]]
        .rename(columns={"name": "award"}),
        on="award_id", validate="many_to_one",
    )
    return _period(ed, "year", min_year, max_year)


def roles(min_year: int | None = None, max_year: int | None = None,
          entity_types: tuple[str, ...] | None = ("person",)) -> pd.DataFrame:
    """One row per (edition, entity, role), with award and entity attributes.

    Adds
      age        age at the time of the role, from a *sourced* birth year only
      age_any    age from the sourced year, falling back to the statistical estimate.
                 Use only where the estimate's circularity (it is derived from award
                 timing) cannot bias the result, and say so.
    """
    ent = entities()
    df = (table("roles")
          .merge(editions(), on="edition_id", validate="many_to_one")
          .merge(ent, on="entity_id", validate="many_to_one"))
    if entity_types is not None:
        df = df[df["entity_type"].isin(entity_types)]
    df["age"] = df["year"] - df["year_birth"]
    df["age_any"] = df["year"] - df["year_birth"].fillna(df["year_birth_estimate"])
    # Credited after death: a posthumous honour, or the enrichment matched the wrong
    # person. Either way the age is meaningless, so it is blanked.
    df["posthumous"] = (df["year"] > df["year_death"]).fillna(False).astype(bool)
    df.loc[df["posthumous"], ["age", "age_any"]] = pd.NA
    return _period(df, "year", min_year, max_year).reset_index(drop=True)


SHARED_JURY_OVERLAP = 0.8
SHARED_JURY_MIN_SIZE = 2  # a one-person jury overlaps 100% with any jury its member sits on


@cache
def _sitting_ids() -> pd.Series:
    """edition_id -> sitting_id. Editions in the same year whose juries overlap by at
    least SHARED_JURY_OVERLAP (relative to the smaller jury, which must have at least
    SHARED_JURY_MIN_SIZE members) are one sitting: e.g. the
    Prešeren jury awards both the Prešernova nagrada and the nagrade Prešernovega
    sklada, and the ZDUS and DSKP juries award several prizes at once."""
    j = table("roles").query("role == 'jury'").merge(table("editions")[["edition_id", "year"]])
    juries = j.groupby("edition_id")["entity_id"].apply(frozenset)
    years = table("editions").set_index("edition_id")["year"]
    parent = {e: e for e in juries.index}

    def find(e):
        while parent[e] != e:
            parent[e] = parent[parent[e]]
            e = parent[e]
        return e

    for _, eds in years[juries.index].groupby(years[juries.index]):
        ids = sorted(eds.index)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ja, jb = juries[a], juries[b]
                if min(len(ja), len(jb)) < SHARED_JURY_MIN_SIZE:
                    continue
                if len(ja & jb) / min(len(ja), len(jb)) >= SHARED_JURY_OVERLAP:
                    parent[find(b)] = find(a)
    return pd.Series({e: find(e) for e in juries.index}, name="sitting_id")


def jury_sittings(min_year: int | None = None, max_year: int | None = None,
                  entity_types: tuple[str, ...] | None = ("person",)) -> pd.DataFrame:
    """One row per (jury sitting, person). Use this, not raw jury roles, for any count
    of jury seats, so a jury that awards several prizes at once is counted once.
    `awards` lists the award_ids decided by the sitting; `award_id`/`genre`/`prestige`
    are those of the highest-prestige award among them."""
    j = roles(min_year, max_year, entity_types).query("role == 'jury'").copy()
    j["sitting_id"] = j["edition_id"].map(_sitting_ids())
    awards_by_sitting = j.groupby("sitting_id")["award_id"].agg(lambda s: tuple(sorted(set(s))))
    j = (j.sort_values(["prestige", "edition_id"], ascending=[False, True])
         .drop_duplicates(["sitting_id", "entity_id"]))
    j["awards"] = j["sitting_id"].map(awards_by_sitting)
    j["jury_size"] = j.groupby("sitting_id")["entity_id"].transform("size")
    return j.reset_index(drop=True)


def coverage() -> pd.DataFrame:
    """Per award: how much of its real history the dataset covers.

    Columns: first/last year in data, editions, editions with known jury,
    founded/ended, and `history_share` = covered years / years the award existed
    (capped at the current year). Analyses comparing awards or periods should either
    restrict to well-covered awards or report coverage alongside the result.
    """
    ed = editions()
    current = int(ed["year"].max())
    g = ed.groupby("award_id").agg(
        data_from=("year", "min"), data_to=("year", "max"),
        editions=("edition_id", "size"), jury_known=("jury_known", "sum"),
        years_present=("year", "nunique"),
    )
    a = awards().set_index("award_id")[["name", "genre", "prestige", "founded", "ended"]]
    cov = a.join(g)
    start = cov["founded"].fillna(cov["data_from"])
    end = cov["ended"].fillna(current).clip(upper=current)
    cov["history_years"] = (end - start + 1).clip(lower=1)
    cov["history_share"] = (cov["years_present"] / cov["history_years"]).clip(upper=1)
    cov["jury_share"] = cov["jury_known"] / cov["editions"]
    return cov.reset_index()


def _period(df: pd.DataFrame, col: str, lo: int | None, hi: int | None) -> pd.DataFrame:
    if lo is not None:
        df = df[df[col] >= lo]
    if hi is not None:
        df = df[df[col] <= hi]
    return df


LJUBLJANA = "Ljubljana"


@cache
def _entity_geo() -> pd.DataFrame:
    loc = table("entity_locations").merge(table("places"), on="place", validate="many_to_one")
    si = loc[loc["scope"] == "si"].copy()
    # Ljubljana (the city municipality) is its own unit; the rest of the central region
    # stays "Osrednjeslovenska". Vague Slovenian ties ("Slovenija", "Primorska", which
    # span several regions) have no unit.
    si["unit"] = si["si_region"].where(~si["is_ljubljana"].astype(bool), LJUBLJANA)
    units = si.dropna(subset=["unit"]).groupby("entity_id")["unit"].agg(
        lambda s: tuple(sorted(set(s))))
    g = pd.DataFrame({
        "n_places": loc.groupby("entity_id")["place"].size(),
        "has_foreign": loc.assign(f=loc["scope"] == "foreign").groupby("entity_id")["f"].any(),
        "has_vague_si": si.assign(v=si["unit"].isna()).groupby("entity_id")["v"].any(),
    })
    g["units"] = units
    return g


def entity_geography() -> pd.DataFrame:
    """One row per entity with geographic ties (from entity_locations + places).

    Places are an *unordered set of ties* (birthplace, places lived or worked in), not a
    residence, so every measure is phrased as a tie:

      units        Slovenian units tied to: "Ljubljana" (city municipality) or a
                   statistical region (Osrednjeslovenska = without Ljubljana)
      placed       has at least one Slovenian unit; the denominator for every share
      lj           has a Ljubljana tie
      lj_only      Ljubljana is the only Slovenian unit
      prov_only    has Slovenian units, none of them Ljubljana
      foreign_only has places, none of them placeable in Slovenia (only foreign ties)
      n_si_units   number of distinct Slovenian units
      n_places     number of place strings (a richer biography gives more ties)
    """
    ent = entities()[["entity_id", "entity_type"]].set_index("entity_id")
    g = ent.join(_entity_geo())
    g["units"] = g["units"].apply(lambda u: u if isinstance(u, tuple) else ())
    g["n_places"] = g["n_places"].fillna(0).astype(int)
    g["has_foreign"] = g["has_foreign"].fillna(False).astype(bool)
    g["has_vague_si"] = g["has_vague_si"].fillna(False).astype(bool)
    g["n_si_units"] = g["units"].str.len()
    g["placed"] = g["n_si_units"] > 0
    g["lj"] = g["units"].apply(lambda u: LJUBLJANA in u)
    g["lj_only"] = g["lj"] & (g["n_si_units"] == 1)
    g["prov_only"] = g["placed"] & ~g["lj"]
    g["foreign_only"] = g["has_foreign"] & ~g["placed"] & ~g["has_vague_si"]
    return g.drop(columns="entity_type").reset_index()
