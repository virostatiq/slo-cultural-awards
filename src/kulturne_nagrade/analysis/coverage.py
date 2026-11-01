"""Coverage: which award-years the dataset has, and with or without the jury.

Every other analysis is shaped by these gaps, so this comes first.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P

THEME = "coverage"
GENRE_ORDER = ["literatura", "poezija", "gledališče", "ples", "film", "glasba",
               "likovno-vizualna umetnost", "arhitektura", "novinarstvo", "umetnost in kultura"]


def run() -> dict:
    cov = frames.coverage()
    ed = frames.editions()
    plot_matrix(cov, ed)
    plot_editions_per_year(ed)

    first_year = int(ed["year"].min())
    by_decade = ed.assign(decade=ed["year"] // 10 * 10).groupby("decade").agg(
        editions=("edition_id", "size"), awards=("award_id", "nunique"),
        jury_share=("jury_known", "mean"))
    return {
        "awards": len(cov), "editions": len(ed), "first_year": first_year,
        "editions_with_jury": int(ed["jury_known"].sum()),
        "jury_share": float(ed["jury_known"].mean()),
        "median_history_share": float(cov["history_share"].median()),
        "awards_full_history": int((cov["history_share"] >= 0.95).sum()),
        "awards_no_jury_data": cov.loc[cov["jury_known"] == 0, "name"].tolist(),
        "by_decade": by_decade.reset_index(),
        "editions_before_1991": int((ed["year"] < 1991).sum()),
        "awards_spanning_1991": int(ed.groupby("award_id")["year"]
                                    .agg(lambda y: y.min() < 1991 <= y.max()).sum()),
    }


def plot_matrix(cov, ed):
    """Award × year grid: absent / winners only / winners and jury."""
    cov = cov.copy()
    cov["g"] = cov["genre"].map({g: i for i, g in enumerate(GENRE_ORDER)})
    cov = cov.sort_values(["g", "data_from"], ascending=[True, False])
    years = np.arange(ed["year"].min(), ed["year"].max() + 1)
    idx = {a: i for i, a in enumerate(cov["award_id"])}
    grid = np.zeros((len(cov), len(years)))
    founded = cov.set_index("award_id")["founded"]
    ended = cov.set_index("award_id")["ended"]
    for a, i in idx.items():  # light gray: the award existed but we have no record
        lo = years[0] if pd.isna(founded[a]) else founded[a]
        hi = years[-1] if pd.isna(ended[a]) else ended[a]
        grid[i, (years >= lo) & (years <= hi)] = 1
    for e in ed.itertuples():
        grid[idx[e.award_id], e.year - years[0]] = max(
            grid[idx[e.award_id], e.year - years[0]], 3 if e.jury_known else 2)

    cmap = ListedColormap([P.SURFACE, "#ebeae4", "#86b6ef", "#184f95"])
    fig, ax = P.figure(11, 15)
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=3, interpolation="nearest",
              extent=(years[0] - 0.5, years[-1] + 0.5, len(cov) - 0.5, -0.5))
    ax.set_yticks(range(len(cov)), cov["name"], fontsize=7)
    ax.grid(False)
    ax.set_title("Kaj zbirka pokriva: nagrade po letih")
    P.subtitle(ax, "Temno modro: nagrajenci in žirija · svetlo modro: samo nagrajenci · "
                   "sivo: nagrada je obstajala, podatkov ni")
    # Genre separators and labels.
    prev = None
    for i, g in enumerate(cov["genre"]):
        if g != prev:
            ax.axhline(i - 0.5, color=P.TEXT_2, lw=0.6)
            ax.text(years[-1] + 1.5, i, g, fontsize=7.5, color=P.TEXT_2, va="top")
            prev = g
    ax.set_xlim(years[0] - 0.5, years[-1] + 0.5)
    P.source_note(fig)
    P.save(fig, THEME, "matrika_pokritosti")


def plot_editions_per_year(ed):
    per_year = ed.groupby("year").agg(n=("edition_id", "size"), jury=("jury_known", "sum"))
    fig, ax = P.figure(9, 4.2)
    ax.bar(per_year.index, per_year["n"], width=0.8, color="#86b6ef", label="vse podelitve")
    ax.bar(per_year.index, per_year["jury"], width=0.8, color="#184f95", label="z znano žirijo")
    ax.set_title("Število podelitev v zbirki po letih")
    P.subtitle(ax, "Zbirka je močno nagnjena k zadnjim desetletjem — "
                   "primerjave čez čas to upoštevajo")
    ax.set_ylabel("podelitve")
    ax.legend(loc="upper left")
    P.source_note(fig)
    P.save(fig, THEME, "podelitve_po_letih")
