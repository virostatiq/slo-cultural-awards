"""Who judges whom: juror-to-winner overlap, tested against proper null models.

Two questions:

1. Insider premium. Are an award's winners more likely to have previously sat on that
   award's jury than equally accomplished peers (winners of *other* awards in the same
   field and year)? The peer comparison controls for seniority and field, and coverage
   gaps in the award's jury history cancel out, since winners and peers are checked
   against the same history. Null: shuffle award labels among the winners of each
   (genre, year) pool.

2. Reciprocity. Pairs where A sat on a jury that awarded B and B sat on one that
   awarded A. In a small scene some reciprocity is inevitable; the null shuffles winners
   between editions of the same genre and year, keeping juries fixed.

3. Familiar faces. The same people, not just the same award: did the jury that decided
   a win include someone with a personal tie to the winner from an earlier year (they
   sat on a jury together, the juror had awarded the winner, or the winner had awarded
   the juror)? Same peer design as 1: would winners of other awards in the same field
   and year have found as many familiar faces on this jury? The strict variant counts
   only ties formed at other awards, so it does not repeat the insider premium.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

import numpy as np
import pandas as pd

from kulturne_nagrade import frames
from kulturne_nagrade import plotting as P
from kulturne_nagrade.analysis.common import bh_fdr, permutation_p, rng

THEME = "juries"
N_PERM = 2000
N_PERM_RECIPROCITY = 500


def run() -> dict:
    roles = frames.roles()
    ins = insider_premium(roles)
    ins_age = insider_premium(roles, age_band=10)
    plot_insider_premium(ins, ins_age)
    rec = reciprocity(roles)
    plot_reciprocity(rec)
    fam = familiar_faces(roles)
    plot_familiar_faces(fam)
    fam_age = familiar_faces(roles, age_band=10)
    same = roles[roles.duplicated(["edition_id", "entity_id"], keep=False)]

    per = ins["per_award"]
    return {
        "insider": {k: v for k, v in ins.items() if k not in ("per_award", "null_total")},
        "insider_per_award": per,
        "insider_significant_awards": per.loc[per["q"] < 0.05, "award"].tolist(),
        "insider_age_matched": {k: v for k, v in ins_age.items()
                                if k not in ("per_award", "null_total")},
        "insider_age_matched_per_award": ins_age["per_award"],
        "reciprocity": {k: v for k, v in rec.items() if k not in ("null", "pairs")},
        "reciprocal_pairs": rec["pairs"],
        "judge_and_winner_same_edition": same[["edition_id", "name", "role"]],
        "familiar_faces": fam["summary"],
        "familiar_faces_per_award": fam["per_award"],
        "familiar_faces_significant_awards":
            fam["per_award"].loc[fam["per_award"]["q"] < 0.05, "award"].tolist(),
        "familiar_faces_age_matched": fam_age["summary"],
        "familiar_faces_age_matched_per_award": fam_age["per_award"],
    }


# --- 1. Insider premium ----------------------------------------------------------------

def insider_premium(roles: pd.DataFrame, age_band: int | None = None) -> dict:
    """age_band: if set, peers must also be in the same age band (e.g. 10 years), so a
    lifetime award's winners are not compared with younger mid-career peers. Winners
    without a sourced age are dropped in that variant."""
    jury = roles[roles["role"] == "jury"]
    first_jury = jury.groupby(["entity_id", "award_id"])["year"].min()
    first_jury = {k: int(v) for k, v in first_jury.items()}
    w = roles[roles["role"] == "winner"][["entity_id", "award_id", "award", "genre", "year", "age"]]
    w = w.drop_duplicates(["entity_id", "award_id", "year"]).reset_index(drop=True)
    pool_keys = ["genre", "year"]
    if age_band:
        w = w[w["age"].notna()].reset_index(drop=True)
        w["band"] = (w["age"] // age_band).astype(int)
        pool_keys.append("band")
    return peer_premium(w, first_jury, pool_keys)


def peer_premium(w: pd.DataFrame, prior: dict | None, pool_keys: list[str],
                 n_perm: int = N_PERM,
                 tie: Callable[[str, str, int], bool] | None = None) -> dict:
    """The insider-premium engine, for any "prior tie" to an award.

    w: one row per (winner, award, year). prior: (entity_id, award_id) -> first year of
    the tie (a jury seat for the insider premium, a win for repeat winners). For each
    award, counts its winners with a tie to it before the win year, against the count
    expected if award labels were shuffled among the winners of each pool (same genre
    and year): do people with a tie to award A win A rather than a peer award?
    Keys keep the insider names (insider_wins = winners with a prior tie).
    tie: instead of `prior`, a function (entity_id, award_id, year) -> bool for ties
    that are not a single first year (see familiar_faces)."""
    awards = sorted(w["award_id"].unique())
    a_idx = {a: i for i, a in enumerate(awards)}
    observed = np.zeros(len(awards))
    null = np.zeros((n_perm, len(awards)))
    peer_rate_num = np.zeros(len(awards))
    peer_rate_den = np.zeros(len(awards))
    winners_with_peers = np.zeros(len(awards))
    g = rng()

    for _, grp in w.groupby(pool_keys):
        labels = grp["award_id"].map(a_idx).to_numpy()
        present = np.unique(labels)
        if len(present) < 2:  # no peers: contributes nothing to the comparison
            continue
        year = int(grp["year"].iloc[0])
        # M[i, k]: did winner i sit on award present[k]'s jury before this year?
        if tie is None:
            M = np.array([[prior.get((e, awards[a]), 9999) < year for a in present]
                          for e in grp["entity_id"]], dtype=float)
        else:
            M = np.array([[tie(e, awards[a], year) for a in present]
                          for e in grp["entity_id"]], dtype=float)
        col = np.searchsorted(present, labels)
        own = M[np.arange(len(labels)), col]
        np.add.at(observed, labels, own)
        np.add.at(winners_with_peers, labels, 1)
        for k, a in enumerate(present):  # peer rate: other awards' winners on a's jury
            peers = labels != a
            peer_rate_num[a] += M[peers, k].sum()
            peer_rate_den[a] += peers.sum()
        perms = np.argsort(g.random((n_perm, len(labels))), axis=1)
        pcol = col[perms]  # labels shuffled among this pool's winners
        hits = M[np.arange(len(labels))[None, :], pcol]
        for k, a in enumerate(present):
            null[:, a] += (hits * (pcol == k)).sum(axis=1)

    keep = winners_with_peers > 0
    per = pd.DataFrame({
        "award_id": np.array(awards)[keep],
        "winners": winners_with_peers[keep].astype(int),
        "insider_wins": observed[keep].astype(int),
        "expected": null[:, keep].mean(axis=0),
        "own_rate": observed[keep] / winners_with_peers[keep],
        "peer_rate": np.divide(peer_rate_num[keep], peer_rate_den[keep],
                               out=np.zeros(keep.sum()), where=peer_rate_den[keep] > 0),
    })
    per["p"] = [permutation_p(o, null[:, a_idx[a]]) for o, a in
                zip(per["insider_wins"], per["award_id"])]
    testable = per["insider_wins"] + per["expected"] > 0
    per["q"] = np.nan
    per.loc[testable, "q"] = bh_fdr(per.loc[testable, "p"])
    per = per.merge(frames.awards()[["award_id", "name", "genre"]].rename(columns={"name": "award"}))
    total_null = null.sum(axis=1)
    return {
        "winners_compared": int(winners_with_peers.sum()),
        "insider_wins": int(observed.sum()),
        "expected": float(total_null.mean()),
        "ratio": float(observed.sum() / total_null.mean()),
        "p": permutation_p(observed.sum(), total_null),
        "own_rate": float(observed.sum() / winners_with_peers.sum()),
        "null_total": total_null,
        "per_award": per.sort_values("p").reset_index(drop=True),
    }


# Notes on single awards, in plain words (checked against results/juries.json).
INSIDER_NOTES = {
    "prešernova nagrada": "deloma zaradi starosti: isti rod sodi in prejema",
    "nagrada franceta štiglica": "ob upoštevanju starosti razlika ni več zanesljiva",
    "plečnikova nagrada": "majhno področje: tudi drugi arhitekti so pogosto sodili",
}


def plot_insider_premium(ins, ins_age, min_cases: int = 3):
    """For the general public: per award, the share of wins that went to someone who had
    earlier sat on that award's jury. Winners who join the jury after winning are a
    custom, not a concern, and are not counted. Colour = whether the share is above what
    peers would give (main test, q < 0.05); notes in words where the age-matched test
    disagrees or the field is small."""
    per = ins["per_award"]
    per = per[per["insider_wins"] >= min_cases].sort_values("own_rate").reset_index(drop=True)
    sig = (per["q"] < 0.05).to_numpy()
    fig, ax = P.figure(9, 0.42 * len(per) + 2.4)
    y = np.arange(len(per))
    ax.barh(y, per["own_rate"], 0.62,
            color=np.where(sig, P.ROLE_COLOR["jury"], P.MUTED))
    for yi, r in zip(y, per.itertuples()):
        note = INSIDER_NOTES.get(r.award.lower(), "")
        ax.text(r.own_rate + 0.006, yi, f"{r.insider_wins} od {r.winners}"
                + (f"  · {note}" if note else ""), va="center", fontsize=9, color=P.TEXT_2)
    ax.set_yticks(y, per["award"], fontsize=9.5)
    ax.xaxis.set_major_formatter(P.pct_fmt)
    ax.set_xlim(0, per["own_rate"].max() * 1.9)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("delež nagrad, ki jih je dobil nekdanji žirant iste nagrade")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=P.ROLE_COLOR["jury"], label="pogosteje, kot bi pričakovali"),
                       Patch(color=P.MUTED, label="v mejah pričakovanega")],
              loc="lower right")
    ax.set_title("Kje nagrado pogosto dobijo njeni nekdanji žiranti")
    P.subtitle(ax, "Nagrade, pri katerih je nagrajenec prej že sedel v žiriji iste nagrade. Da "
                   "nagrajenci pozneje postanejo\nžiranti, je običajno, zato tega ne štejemo. "
                   f"Prikazane so nagrade z vsaj {['nič', 'enim', 'dvema', 'tremi'][min_cases]} "
                   "takimi primeri.")
    P.source_note(fig, "Pričakovano: kolikokrat bi bil nekdanji žirant med nagrajenci, če bi isti "
                       "ljudje dobili kako drugo nagrado istega področja\nv istem letu.   "
                       "Vir: zbirka Kulturne nagrade")
    P.save(fig, THEME, "nekdanji_ziranti_med_nagrajenci")


# --- 2. Reciprocity ---------------------------------------------------------------------

def _edges(jury_by_ed: dict, winners_by_ed: dict) -> set:
    return {(j, w) for ed, ws in winners_by_ed.items() for w in ws
            for j in jury_by_ed.get(ed, ()) if j != w}


def _reciprocal(edges: set) -> set:
    return {tuple(sorted(e)) for e in edges if (e[1], e[0]) in edges}


def reciprocity(roles: pd.DataFrame) -> dict:
    jury_by_ed = roles[roles["role"] == "jury"].groupby("edition_id")["entity_id"].apply(list).to_dict()
    w = roles[roles["role"] == "winner"]
    winners_by_ed = w.groupby("edition_id")["entity_id"].apply(list).to_dict()
    pairs = _reciprocal(_edges(jury_by_ed, winners_by_ed))

    # Null: shuffle winner slots between editions of the same genre and year.
    slots = w[["edition_id", "entity_id", "genre", "year"]].reset_index(drop=True)
    pools = [grp.index.to_numpy() for _, grp in slots.groupby(["genre", "year"]) if len(grp) > 1]
    ents = slots["entity_id"].to_numpy()
    eds = slots["edition_id"].to_numpy()
    g, null = rng(), np.empty(N_PERM_RECIPROCITY)
    for i in range(N_PERM_RECIPROCITY):
        perm = ents.copy()
        for idx in pools:
            perm[idx] = g.permutation(ents[idx])
        by_ed = defaultdict(list)
        for ed, e in zip(eds, perm):
            by_ed[ed].append(e)
        null[i] = len(_reciprocal(_edges(jury_by_ed, by_ed)))

    names = frames.entities().set_index("entity_id")["name"]
    first = {}  # earliest year each direction happened
    yr = roles.drop_duplicates("edition_id").set_index("edition_id")["year"]
    for ed, ws in winners_by_ed.items():
        for wi in ws:
            for j in jury_by_ed.get(ed, ()):
                if tuple(sorted((j, wi))) in pairs:
                    first[(j, wi)] = min(first.get((j, wi), 9999), int(yr[ed]))
    pair_rows = [{"a": names[a], "b": names[b], "a_judged_b": first.get((a, b)),
                  "b_judged_a": first.get((b, a))} for a, b in sorted(pairs)]
    return {
        "pairs_observed": len(pairs), "pairs_expected": float(null.mean()),
        "ratio": float(len(pairs) / null.mean()), "p": permutation_p(len(pairs), null),
        "null": null, "pairs": pd.DataFrame(pair_rows),
    }


def plot_reciprocity(rec):
    fig, ax = P.figure(8, 4.2)
    ax.hist(rec["null"], bins=30, color="#b7d3f6", edgecolor=P.SURFACE, linewidth=1)
    ax.axvline(rec["pairs_observed"], color=P.SERIES[1], lw=2)
    ax.annotate(f"opaženo: {rec['pairs_observed']}\npričakovano: {rec['pairs_expected']:.0f}",
                (rec["pairs_observed"], ax.get_ylim()[1] * 0.8), xytext=(-8, 0),
                textcoords="offset points", ha="right", fontsize=9)
    ax.set_xlabel("pari, ki sta drug drugemu podelila nagrado")
    ax.set_ylabel("simulacije")
    ax.grid(axis="y", visible=False)
    ax.set_title("»Jaz tebi, ti meni«: vzajemno nagrajevanje")
    P.subtitle(ax, f"Histogram = {N_PERM_RECIPROCITY} simulacij, v katerih so nagrajenci "
                   "naključno premešani med podelitvami istega področja in leta")
    P.source_note(fig)
    P.save(fig, THEME, "vzajemno_nagrajevanje")


# --- 3. Familiar faces ------------------------------------------------------------------

TIE_KINDS = {
    "co_jury": "sedela sta v isti žiriji",
    "judged_winner": "žirant je nagrajencu že podelil nagrado",
    "judged_juror": "nagrajenec je žirantu že podelil nagrado",
}


def _tie_history(roles: pd.DataFrame) -> dict:
    """Earlier personal ties between two people, as lists of (year, award_ids).
    co[(u, v)]: u and v sat on a jury together (frames.jury_sittings, so a joint jury
    counts once; stored both ways). judged[(j, w)]: j sat on a jury that awarded w."""
    co, judged = defaultdict(list), defaultdict(list)
    for _, d in frames.jury_sittings().groupby("sitting_id"):
        y, aw, m = int(d["year"].iloc[0]), d["awards"].iloc[0], list(d["entity_id"])
        for u in m:
            for v in m:
                if u != v:
                    co[(u, v)].append((y, aw))
    for _, d in roles.groupby("edition_id"):
        y, a = int(d["year"].iloc[0]), d["award_id"].iloc[0]
        for j in d.loc[d["role"] == "jury", "entity_id"]:
            for w in d.loc[d["role"] == "winner", "entity_id"]:
                if j != w:
                    judged[(j, w)].append((y, (a,)))
    # tie kind -> (history, key for winner e and juror j)
    return {"co_jury": (co, lambda e, j: (e, j)),
            "judged_winner": (judged, lambda e, j: (j, e)),
            "judged_juror": (judged, lambda e, j: (e, j))}


def familiar_faces(roles: pd.DataFrame, n_perm: int = N_PERM,
                   age_band: int | None = None) -> dict:
    """For every win at an award whose jury is recorded that year: did the jury include
    someone with an earlier personal tie to the winner? Tested with peer_premium against
    winners of other awards in the same genre and year that also have a recorded jury,
    so each winner's own tie history is held fixed and only the jury they face changes.

    Variants: every tie kind together and each kind alone, each counting ties formed
    anywhere ('all') or only at other awards ('other_awards'). Per-award results are
    for the strict headline: any tie, formed at other awards. age_band: as in
    insider_premium (peers also in the same age band; winners without a sourced age
    dropped)."""
    jury = roles[roles["role"] == "jury"]
    panel = jury.groupby(["award_id", "year"])["entity_id"].agg(frozenset).to_dict()
    hist = _tie_history(roles)
    w = roles[roles["role"] == "winner"][["entity_id", "award_id", "award", "genre", "year", "age"]]
    w = w.drop_duplicates(["entity_id", "award_id", "year"])
    w = w[[(a, y) in panel for a, y in zip(w["award_id"], w["year"])]].reset_index(drop=True)
    pool_keys = ["genre", "year"]
    if age_band:
        w = w[w["age"].notna()].reset_index(drop=True)
        w["band"] = (w["age"] // age_band).astype(int)
        pool_keys.append("band")

    def make_tie(kinds, strict):
        def tie(e, a, year):
            for j in panel.get((a, year), ()):
                if j == e:
                    continue
                for k in kinds:
                    h, key = hist[k]
                    if any(y < year and not (strict and a in aw) for y, aw in h.get(key(e, j), ())):
                        return True
            return False
        return tie

    rows, per = [], None
    for name, kinds in [("any", list(TIE_KINDS)), *[(k, [k]) for k in TIE_KINDS]]:
        for scope, strict in (("all", False), ("other_awards", True)):
            r = peer_premium(w, None, pool_keys, n_perm, tie=make_tie(kinds, strict))
            rows.append({"tie": name, "scope": scope, "winners_compared": r["winners_compared"],
                         "with_tie": r["insider_wins"], "expected": r["expected"],
                         "ratio": r["ratio"], "p": r["p"], "own_rate": r["own_rate"]})
            if name == "any" and strict:
                per, headline = r["per_award"].rename(columns={"insider_wins": "with_tie"}), r
    return {"summary": pd.DataFrame(rows), "per_award": per,
            "null_total": headline["null_total"]}


FAMILIAR_ROWS = [  # (tie kind, label), the total first
    ("any", "vsaj ena od spodnjih vezi"),
    ("judged_winner", "žirant je nagrajencu že podelil\ndrugo nagrado"),
    ("judged_juror", "nagrajenec je žirantu že\npodelil drugo nagrado"),
    ("co_jury", "sedela sta skupaj v žiriji\ndruge nagrade"),
]


def plot_familiar_faces(fam):
    """For the general public: observed against expected counts, strict variant (ties
    from other awards only), with the test result in words instead of p-values."""
    s = fam["summary"].query("scope == 'other_awards'").set_index("tie")
    n = int(s.loc["any", "winners_compared"])
    fig, ax = P.figure(9, 5.6)
    h, gap = 0.36, 0.04
    y = np.arange(len(FAMILIAR_ROWS))[::-1] * 1.25
    xmax = s["with_tie"].max()
    for yi, (k, _) in zip(y, FAMILIAR_ROWS):
        obs, exp, pv = int(s.loc[k, "with_tie"]), s.loc[k, "expected"], s.loc[k, "p"]
        ax.barh(yi + (h + gap) / 2, obs, h, color=P.ROLE_COLOR["jury"])
        ax.barh(yi - (h + gap) / 2, exp, h, color=P.MUTED)
        ax.text(obs + xmax * 0.012, yi + (h + gap) / 2, f"{obs}", va="center", fontsize=10,
                color=P.TEXT, fontweight="bold")
        ax.text(exp + xmax * 0.012, yi - (h + gap) / 2, f"{exp:.0f}", va="center", fontsize=10,
                color=P.TEXT_2)
        verdict = ("razlika je prevelika,\nda bi bila naključna" if pv < 0.05
                   else "razlika je lahko\nnaključna")
        ax.text(xmax * 1.13, yi, f"{obs - exp:+.0f} ({P.dec(100 * (obs / exp - 1), 0, sign=True)} %)"
                f"\n{verdict}", va="center", fontsize=9, color=P.TEXT_2)
    ax.set_yticks(y, [lab for _, lab in FAMILIAR_ROWS], fontsize=9.5)
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.set_xlim(0, xmax * 1.45)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=P.ROLE_COLOR["jury"], label="dejansko"),
                       Patch(color=P.MUTED, label="pričakovano")],
              loc="lower right", bbox_to_anchor=(1, -0.02), ncols=2)
    ax.set_title("V žiriji nekoliko pogosteje sedi kdo, ki je nagrajenca že nagradil")
    P.subtitle(ax, f"Pri koliko od {n} nagrad z znano žirijo je v žiriji sedel kdo, s katerim je bil "
                   "nagrajenec že povezan\nprek druge nagrade. Pričakovano: kolikokrat bi to doživeli "
                   "isti nagrajenci, če bi namesto te dobili\nkako drugo nagrado istega področja "
                   "v istem letu.")
    P.source_note(fig, "Upoštevane so le vezi iz prejšnjih let in drugih nagrad. Vez ne pomeni nujno "
                       "naklonjenosti: pogosto gre le za isti ožji krog\n(npr. mladinska književnost "
                       "ali likovna kritika).   Vir: zbirka Kulturne nagrade")
    P.save(fig, THEME, "znani_obrazi_v_ziriji")
