"""Overview: general statistics. Who wins and who judges most often, overall, per decade
and per year.

Wins are counted per (edition, person); each prize of a multi-prize ceremony is its
own win. Jury seats are counted in sittings (frames.jury_sittings), so a jury that
awards several prizes at once counts once. People only (groups, institutions and
works are excluded). These are counts of what is recorded: coverage grows after
2000, so all-time lists favour recent careers and awards with many winners per year.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P

THEME = "overview"
TOP_N = 25
YEARS_FROM = 1990  # per-year figure; earlier years are in the results
MAX_NAMES = 2      # names shown per tied year before "+k"


def run() -> dict:
    roles_all = frames.roles(entity_types=None)
    roles = roles_all[roles_all["entity_type"] == "person"]
    wins = roles[roles["role"] == "winner"]
    sit = frames.jury_sittings()

    top_w = top_winners(wins)
    plot_top_winners(top_w.head(20))
    top_j = top_jurors(sit, wins)
    per_year = leaders_per_year(wins, sit)
    plot_leaders_per_year(per_year[per_year["year"] >= YEARS_FROM])
    return {
        "totals": totals(roles_all, wins, sit),
        "top_winners": top_w,
        "top_jurors": top_j,
        "both_roles": both_roles(wins, sit),
        "leaders_per_decade": leaders_per_decade(wins, sit),
        "leaders_per_year": per_year,
        "awards_most_winners": award_breadth(wins, sit),
    }


def totals(roles_all, wins, sit) -> dict:
    ed = frames.editions()
    w_all = roles_all[roles_all["role"] == "winner"]
    return {
        "awards": int(ed["award_id"].nunique()), "editions": len(ed),
        "years": [int(ed["year"].min()), int(ed["year"].max())],
        "wins_all_entities": len(w_all),
        "wins_people": len(wins), "winners_people": int(wins["entity_id"].nunique()),
        "winners_other": w_all[w_all["entity_type"] != "person"]
        .groupby("entity_type")["entity_id"].nunique().to_dict(),
        "jury_sittings_seats": len(sit), "jurors": int(sit["entity_id"].nunique()),
        "share_winners_once": float((wins.groupby("entity_id").size() == 1).mean()),
        "share_jurors_once": float((sit.groupby("entity_id").size() == 1).mean()),
        "median_wins_per_winner": float(wins.groupby("entity_id").size().median()),
        "median_sittings_per_juror": float(sit.groupby("entity_id").size().median()),
    }


def top_winners(wins) -> pd.DataFrame:
    g = wins.groupby(["entity_id", "name"]).agg(
        wins=("edition_id", "size"), awards=("award_id", "nunique"),
        first=("year", "min"), last=("year", "max"), top_prestige=("prestige", "max"))
    g["award_list"] = wins.groupby("entity_id")["award"].agg(
        lambda s: ", ".join(s.value_counts().index[:3]))
    return (g.reset_index().sort_values(["wins", "awards", "name"],
                                        ascending=[False, False, True])
            .head(TOP_N).reset_index(drop=True))


def top_jurors(sit, wins) -> pd.DataFrame:
    g = sit.groupby(["entity_id", "name"]).agg(
        sittings=("sitting_id", "size"), awards=("award_id", "nunique"),
        first=("year", "min"), last=("year", "max"))
    g["wins"] = wins.groupby("entity_id").size().reindex(
        g.index.get_level_values(0)).fillna(0).astype(int).to_numpy()
    return (g.reset_index().sort_values(["sittings", "awards", "name"],
                                        ascending=[False, False, True])
            .head(TOP_N).reset_index(drop=True))


def both_roles(wins, sit) -> dict:
    """People who both won and judged: how many, and the most active by both counts."""
    w = wins.groupby("entity_id").size().rename("wins")
    j = sit.groupby("entity_id").size().rename("sittings")
    b = pd.concat([w, j], axis=1, join="inner")
    names = frames.entities().set_index("entity_id")["name"]
    b["name"] = names.reindex(b.index)
    b["total"] = b["wins"] + b["sittings"]
    return {
        "people": len(b),
        "share_of_winners": len(b) / len(w), "share_of_jurors": len(b) / len(j),
        "top": b.sort_values(["total", "wins"], ascending=False).head(15)
        .reset_index().rename(columns={"index": "entity_id"}),
    }


def _leaders(df, by, count_name):
    """Per group in `by`: the people with the highest count (ties kept)."""
    c = df.groupby([by, "entity_id", "name"]).size().rename(count_name).reset_index()
    top = c[c[count_name] == c.groupby(by)[count_name].transform("max")]
    return top.groupby(by).agg(
        n=(count_name, "first"), names=("name", lambda s: sorted(s)),
        tied=("name", "size"))


def leaders_per_year(wins, sit) -> pd.DataFrame:
    w = _leaders(wins, "year", "wins").add_prefix("win_")
    j = _leaders(sit, "year", "sittings").add_prefix("jury_")
    out = w.join(j, how="outer").reset_index()
    # A year where the most anyone won is one is a tie of everyone: no leader.
    out.loc[out["win_n"] == 1, ["win_names", "win_tied"]] = pd.NA
    out.loc[out["jury_n"] == 1, ["jury_names", "jury_tied"]] = pd.NA
    return out.sort_values("year").reset_index(drop=True)


def leaders_per_decade(wins, sit) -> pd.DataFrame:
    w = wins.assign(decade=wins["year"] // 10 * 10)
    s = sit.assign(decade=sit["year"] // 10 * 10)
    out = (_leaders(w, "decade", "wins").add_prefix("win_")
           .join(_leaders(s, "decade", "sittings").add_prefix("jury_"), how="outer"))
    out.loc[out["win_n"] == 1, ["win_names", "win_tied"]] = pd.NA
    out.loc[out["jury_n"] == 1, ["jury_names", "jury_tied"]] = pd.NA
    return out.reset_index()


def award_breadth(wins, sit) -> pd.DataFrame:
    a = wins.groupby(["award_id", "award"]).agg(
        winners=("entity_id", "nunique"), wins=("edition_id", "size"),
        editions=("edition_id", "nunique"))
    a["jurors"] = sit.explode("awards").groupby("awards")["entity_id"].nunique().reindex(
        a.index.get_level_values(0)).fillna(0).astype(int).to_numpy()
    return a.sort_values("winners", ascending=False).head(15).reset_index()


# --- figures ----------------------------------------------------------------------------

def plot_top_winners(t):
    t = t.iloc[::-1]
    fig, ax = P.figure(8.5, 0.3 * len(t) + 1.8)
    y = np.arange(len(t))
    ax.barh(y, t["wins"], height=0.6, color=P.ROLE_COLOR["winner"])
    for yi, (w, a, f, la) in enumerate(zip(t["wins"], t["awards"], t["first"], t["last"])):
        where = "pri 1 nagradi" if a == 1 else f"pri {a} nagradah"
        ax.text(w + 0.2, yi, f"{w}  ·  {where}  ·  {f}–{la}", va="center", fontsize=8,
                color=P.TEXT_2)
    ax.set_yticks(y, t["name"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, t["wins"].max() * 1.45)
    ax.set_xlabel("nagrade")
    ax.set_title("Najpogostejši nagrajenci")
    P.subtitle(ax, "Vsaka nagrada šteje posebej, tudi več nagrad na isti podelitvi · samo osebe")
    P.source_note(fig)
    P.save(fig, THEME, "najpogostejsi_nagrajenci")


def _label(names, tied, n):
    if not isinstance(names, list):
        return "—"
    shown = ", ".join(names[:MAX_NAMES])
    more = f" +{int(tied) - MAX_NAMES}" if tied > MAX_NAMES else ""
    return f"{shown}{more}  ({int(n)})"


def plot_leaders_per_year(t):
    t = t.sort_values("year", ascending=False).reset_index(drop=True)
    fig, axes = P.figure(11, 0.27 * len(t) + 2, ncols=2, sharey=True)
    y = np.arange(len(t))
    for ax, role, color, title in (
            (axes[0], "win", P.ROLE_COLOR["winner"], "Največ nagrad v letu"),
            (axes[1], "jury", P.ROLE_COLOR["jury"], "Največ sedežev v žirijah v letu")):
        n = t[f"{role}_n"].fillna(0)
        ax.barh(y, n, height=0.6, color=color)
        for yi, (names, tied, k) in enumerate(zip(t[f"{role}_names"], t[f"{role}_tied"], n)):
            ax.text(k + 0.1, yi, _label(names, tied, k), va="center", fontsize=7.5,
                    color=P.TEXT)
        ax.set_xlim(0, n.max() * 3.2)
        ax.set_xticks(range(0, int(n.max()) + 1))
        ax.grid(axis="y", visible=False)
        ax.set_title(title, loc="left", fontsize=11, pad=8)
    axes[0].set_yticks(y, t["year"].astype(int), fontsize=8)
    axes[0].invert_yaxis()
    h = fig.get_figheight()
    fig.text(0.01, 1 - 0.15 / h, "Kdo je bil v posameznem letu najpogosteje nagrajen in kdo "
             "najpogosteje v žirijah", ha="left", va="top", fontsize=13, fontweight="bold")
    fig.text(0.01, 1 - 0.5 / h,
             f"Od leta {YEARS_FROM} · v oklepaju število · ob izenačenju največ dve imeni, "
             "nato število ostalih · — = nihče več kot enkrat\nŽirija, ki podeli več nagrad "
             "hkrati, šteje enkrat · samo osebe", fontsize=9, color=P.TEXT_2, va="top")
    fig.tight_layout(rect=(0, 0.01, 1, 1 - 0.95 / h))
    fig.text(0.01, 0, "Vir: zbirka Kulturne nagrade", fontsize=8, color=P.TEXT_2, ha="left",
             va="top")
    P.save(fig, THEME, "vodilni_po_letih")
