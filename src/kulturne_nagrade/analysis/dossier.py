"""Dossier: one person's record as juror, read against their peers.

Default subject: Ignacija J. Fridl, appointed Minister of Culture. Everything here is
public record (jury lists). Political affiliation is not used. Commission terms
were dropped on 2026-11-01 (the commission records were not reliable).

The legacy dossier ranked the subject against all jurors, most of whom sat once, so
every percentile came out extreme. Here the comparison group is **peers**: people
with at least MIN_PEER_SITTINGS jury sittings. Questions:

1. Service record: sittings by award and year, with voting power (1 / jury size: one
   seat on a 3-person jury is worth five on a 15-person one).
2. Position among peers: sittings, voting power, distinct awards and fields, span,
   wins, network betweenness.
3. Award capture: the subject's share of each award's recorded jury voting power.
4. Picks: winners of editions the subject judged; repeat picks; whether those winners
   later sat on juries more often than winners of the same awards in the same years
   from editions without the subject.
5. Ties relevant to office: co-jurors the subject sat with most, and recent winners of
   the subject's panels (who would have a declared relationship to note).

    uv run python -m kulturne_nagrade.analysis dossier          # default -> results/dossier.json
    uv run python -m kulturne_nagrade.analysis.dossier <entity_id> [...]
                                                     # -> results/dossier_<entity_id>.json
"""

from __future__ import annotations

import sys
from itertools import combinations

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import save_results, wilson

THEME = "dossier"
SUBJECT = "ignacija-j-fridl"
MIN_PEER_SITTINGS = 10
RECENT_FROM = 2012
LATER_JURY_YEARS = 10
BETWEENNESS_K = 400


def run(subject: str = SUBJECT) -> dict:
    sit = frames.jury_sittings()
    sit["power"] = 1 / sit["jury_size"]
    roles = frames.roles()
    name = frames.entities().set_index("entity_id").loc[subject, "name"]
    me = sit[sit["entity_id"] == subject].sort_values("year")
    if me.empty:
        raise SystemExit(f"{subject} has no jury sittings")

    rec = record(me, subject, roles)
    plot_record(me, name)
    peers = peer_table(sit, roles)
    pos = position(peers, subject)
    plot_position(peers, subject, name)
    cap = capture(sit, me)
    plot_capture(cap, subject, name)
    picks = panel_picks(roles, me, sit)
    ties = ties_for_office(sit, me, picks["winners"])
    return {
        "subject": subject, "name": name,
        "record": rec, "position_among_peers": pos, "award_capture": cap,
        "picks": {k: v for k, v in picks.items() if k != "winners"},
        "panel_winners": picks["winners"], "ties": ties,
    }


# --- 1. record --------------------------------------------------------------------------

def record(me, subject, roles) -> dict:
    return {
        "sittings": len(me), "awards": int(me["award_id"].nunique()),
        "fields": sorted(me["genre"].unique()),
        "first_year": int(me["year"].min()), "last_year": int(me["year"].max()),
        "voting_power": float(me["power"].sum()),
        "wins": int(((roles["entity_id"] == subject) & (roles["role"] == "winner")).sum()),
        "by_award": me.groupby("award").agg(sittings=("year", "size"),
                                            first=("year", "min"), last=("year", "max"),
                                            jury_size=("jury_size", "median"),
                                            power=("power", "sum"))
        .sort_values("first").reset_index(),
    }


def plot_record(me, name):
    rows = me.groupby("award")["year"].min().sort_values().index.tolist()
    fig, ax = P.figure(9, 0.42 * len(rows) + 2)
    y = {a: i for i, a in enumerate(rows[::-1])}
    ax.scatter(me["year"], me["award"].map(y), s=900 * me["power"], color=P.SERIES[0],
               alpha=0.85, edgecolor=P.SURFACE, zorder=3)
    ax.set_yticks(list(y.values()))
    ax.set_yticklabels(list(y.keys()), fontsize=8.5)
    ax.grid(axis="y", visible=False)
    for size in (3, 5, 15):
        ax.scatter([], [], s=900 / size, color=P.SERIES[0], label=f"žirija s {size} člani")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), labelspacing=1.4)
    ax.set_title(f"{name}: sedeži v žirijah")
    P.subtitle(ax, "Velikost kroga = glasovna moč (1 / velikost žirije)")
    P.source_note(fig)
    P.save(fig, f"{THEME}/{me['entity_id'].iloc[0]}", "zapis_sluzbe")


# --- 2. position among peers ------------------------------------------------------------

def _betweenness(sit) -> dict:
    G = nx.Graph()
    G.add_nodes_from(sorted(sit["entity_id"].unique()))
    for _, m in sit.groupby("sitting_id")["entity_id"]:
        G.add_edges_from(combinations(sorted(m), 2))
    return nx.betweenness_centrality(G, k=min(BETWEENNESS_K, len(G)), seed=1)


def peer_table(sit, roles) -> pd.DataFrame:
    g = sit.groupby("entity_id")
    t = pd.DataFrame({
        "name": g["name"].first(), "sittings": g.size(), "voting_power": g["power"].sum(),
        "awards": g["award_id"].nunique(), "fields": g["genre"].nunique(),
        "span": g["year"].max() - g["year"].min() + 1,
    })
    t["wins"] = roles[roles["role"] == "winner"].groupby("entity_id").size().reindex(
        t.index).fillna(0).astype(int)
    t["betweenness"] = pd.Series(_betweenness(sit)).reindex(t.index)
    return t[t["sittings"] >= MIN_PEER_SITTINGS].copy()


METRICS = {"sittings": "sedeži v žirijah", "voting_power": "glasovna moč",
           "awards": "različne nagrade", "fields": "različna področja",
           "span": "leta od prvega do zadnjega sedeža", "betweenness": "vmesnost v mreži",
           "wins": "lastne nagrade"}


def position(peers, subject) -> dict:
    out = {"peers": len(peers)}
    for m in METRICS:
        v = peers.loc[subject, m]
        out[m] = {"value": float(v), "rank": int((peers[m] > v).sum() + 1),
                  "share_of_peers_below": float((peers[m] < v).mean()),
                  "peer_median": float(peers[m].median())}
    return out


def plot_position(peers, subject, name):
    fig, ax = P.figure(9, 4.6)
    g = np.random.default_rng(0)
    for i, (m, label) in enumerate(METRICS.items()):
        pct = peers[m].rank(pct=True)
        jitter = g.uniform(-0.18, 0.18, len(peers))
        ax.scatter(pct, i + jitter, s=10, color=P.MUTED, alpha=0.6, lw=0)
        ax.scatter(pct[subject], i, s=90, color=P.SERIES[7], zorder=3,
                   edgecolor=P.SURFACE)
        v = peers.loc[subject, m]
        txt = P.dec(v, 3) if m == "betweenness" else (P.dec(v, 1) if m == "voting_power"
                                                     else f"{int(v)}")
        ax.annotate(txt, (pct[subject], i), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color=P.SERIES[7])
    ax.set_yticks(range(len(METRICS)))
    ax.set_yticklabels(list(METRICS.values()), fontsize=9)
    ax.set_xlim(0, 1.03)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlabel("percentil med primerljivimi žiranti")
    ax.grid(axis="y", visible=False)
    ax.invert_yaxis()
    ax.set_title(f"{name} med najdejavnejšimi žiranti")
    P.subtitle(ax, f"Primerjava z vsemi {len(peers)} žiranti z vsaj {MIN_PEER_SITTINGS} sedeži "
                   "· sive pike = drugi žiranti")
    P.source_note(fig)
    P.save(fig, f"{THEME}/{subject}", "polozaj_med_vrstniki")


# --- 3. award capture -------------------------------------------------------------------

def capture(sit, me) -> pd.DataFrame:
    rows = []
    for a, d in me.groupby("award_id"):
        all_a = sit[sit["award_id"] == a]
        per = all_a.groupby("entity_id")["power"].sum().sort_values(ascending=False)
        label = " in ".join(frames.awards().set_index("award_id").loc[
            sorted(set(d["awards"].iloc[0]), reverse=True), "name"])
        rows.append({"award_id": a, "award": label,
                     "share_of_power": float(d["power"].sum() / per.sum()),
                     "rank_at_award": int((per > d["power"].sum()).sum() + 1),
                     "jurors_at_award": len(per),
                     "years_recorded": int(all_a["year"].nunique())})
    return pd.DataFrame(rows).sort_values("share_of_power", ascending=False)


def plot_capture(cap, subject, name):
    d = cap.sort_values("share_of_power")
    fig, ax = P.figure(8, 0.4 * len(d) + 1.8)
    y = np.arange(len(d))
    ax.barh(y, d["share_of_power"], color=P.SERIES[0], height=0.6)
    for yi, (_, r) in zip(y, d.iterrows()):
        ax.annotate(f"{P.pct(r['share_of_power'], 1)} · {r['rank_at_award']}. od "
                    f"{r['jurors_at_award']}", (r["share_of_power"], yi), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(d["award"], fontsize=8.5)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlim(0, d["share_of_power"].max() * 1.45)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"{name}: delež glasovne moči pri posamezni nagradi")
    P.subtitle(ax, "Delež vse zabeležene glasovne moči v žirijah nagrade · uvrstitev med "
                   "vsemi žiranti te nagrade")
    P.source_note(fig)
    P.save(fig, f"{THEME}/{subject}", "delez_pri_nagradah")


# --- 4. picks ---------------------------------------------------------------------------

def panel_picks(roles, me, sit) -> dict:
    eds = set(sit.loc[sit["sitting_id"].isin(me["sitting_id"]), "edition_id"]) | set(
        roles.loc[(roles["role"] == "jury") & (roles["entity_id"] == me["entity_id"].iloc[0]),
                  "edition_id"])
    w = roles[roles["role"] == "winner"]
    mine = w[w["edition_id"].isin(eds)].drop_duplicates(["edition_id", "entity_id"])
    repeat = mine.groupby(["entity_id", "name"]).size().sort_values(ascending=False)
    repeat = repeat[repeat >= 2].reset_index(name="times")
    # Later jury service: winners of the subject's panels vs winners of the same awards in
    # the same years from editions without the subject. Wins up to end - LATER_JURY_YEARS.
    end = int(roles["year"].max()) - LATER_JURY_YEARS
    years = set(me["year"])
    comp = w[w["award_id"].isin(mine["award_id"]) & w["year"].isin(years)]
    comp = comp[~comp["edition_id"].isin(eds)]
    first_seat = sit.groupby("entity_id")["year"].min()

    def later_rate(df):
        df = df[df["year"] <= end].drop_duplicates("entity_id")
        fs = df["entity_id"].map(first_seat)
        never_before = ~(fs <= df["year"]).fillna(False).astype(bool)
        df, fs = df[never_before], fs[never_before]
        k = int(((fs > df["year"]) & (fs <= df["year"] + LATER_JURY_YEARS)).sum())
        lo, hi = wilson(k, len(df)) if len(df) else (np.nan, np.nan)
        return {"winners": len(df), "later_jury": k,
                "rate": k / len(df) if len(df) else None, "ci": [float(lo), float(hi)]}

    fem = mine["gender"].dropna()
    fem_comp = comp["gender"].dropna()
    kf, kc = int((fem == "f").sum()), int((fem_comp == "f").sum())
    fisher_p = (float(fisher_exact([[kf, len(fem) - kf], [kc, len(fem_comp) - kc]]).pvalue)
                if len(fem) and len(fem_comp) else None)
    return {
        "editions": len(eds), "winner_slots": len(mine),
        "distinct_winners": int(mine["entity_id"].nunique()),
        "repeat_picks": repeat,
        "later_jury_panel_winners": later_rate(mine),
        "later_jury_same_awards_other_editions": later_rate(comp),
        "female_share_picks": float((fem == "f").mean()),
        "female_share_same_awards_years_other_editions":
            float((fem_comp == "f").mean()) if len(fem_comp) else None,
        "female_share_fisher_p": fisher_p,
        "winners": mine[["edition_id", "year", "award", "name"]].sort_values(
            ["year", "award"]).reset_index(drop=True),
    }


# --- 5. ties ----------------------------------------------------------------------------

def ties_for_office(sit, me, winners) -> dict:
    subject = me["entity_id"].iloc[0]
    co = sit[sit["sitting_id"].isin(me["sitting_id"]) & (sit["entity_id"] != subject)]
    bloc = (co.groupby(["entity_id", "name"])
            .agg(joint_sittings=("sitting_id", "nunique"), last_joint=("year", "max"),
                 awards=("award", lambda s: ", ".join(sorted(set(s)))))
            .sort_values(["joint_sittings", "last_joint"], ascending=False).reset_index())
    return {
        "co_jurors": int(bloc["entity_id"].nunique()),
        "frequent_co_jurors": bloc[bloc["joint_sittings"] >= 3].drop(columns="entity_id"),
        "recent_co_jurors": int((bloc["last_joint"] >= RECENT_FROM).sum()),
        "recent_panel_winners": winners[winners["year"] >= RECENT_FROM],
    }


def main(argv: list[str]) -> None:
    for subject in argv or [SUBJECT]:
        save_results(f"{THEME}_{subject}", run(subject))
        print(f"dossier {subject}: plots/{THEME}/{subject}/, results/{THEME}_{subject}.json")


if __name__ == "__main__":
    main(sys.argv[1:])
