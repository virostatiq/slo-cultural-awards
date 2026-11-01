"""Numbers and charts for the site's findings pages (/ugotovitve/), from results/*.json.

    from kulturne_nagrade import site_findings
    site_findings.build()   # {finding_id: {"n": {...}, "chart": {...}}}

Each finding's text lives in site/src/content/ugotovitve/<id>.md and refers to numbers
as {{key}}; the numbers and the chart data come from here, so the pages follow the
analyses on every re-run. Charts are specs for the site's components (Bars, Lines),
written for the general public: plain labels, verdicts in words, no p-values.
"""

from __future__ import annotations

import json

from kulturne_nagrade import PROJECT_ROOT
from kulturne_nagrade import plotting as P

RESULTS = PROJECT_ROOT / "results"
JURY, WINNER = P.ROLE_COLOR["jury"], P.ROLE_COLOR["winner"]
WOMEN, MEN = "#e4622e", P.SERIES[0]  # gender pair; orange one step darker for the dark site
GRAY = "#8a8199"  # context marks on the dark site (between --muted and --ink-2)
SIG = 0.05
SURE = "razlika je prevelika, da bi bila naključna"
MAYBE = "razlika je lahko naključna"


def _verdict(p) -> str:
    return SURE if p is not None and p < SIG else MAYBE


def _dec(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def _n_awards(n: int, adj: str = "") -> str:
    """Slovenian plural: 1 nagrada, 2 nagradi, 3–4 nagrade, 5+ nagrad (with an adjective)."""
    m = n % 100
    k = 0 if m == 1 else 1 if m == 2 else 2 if m in (3, 4) else 3
    a = {"različn": ["različna", "različni", "različne", "različnih"]}.get(adj, [""] * 4)[k]
    noun = ["nagrada", "nagradi", "nagrade", "nagrad"][k]
    return f"{n} {a + ' ' if a else ''}{noun}"


def _points(x: float) -> str:
    """'4 odstotne točke' with the Slovenian plural."""
    n = round(x)
    m = abs(n) % 100
    w = "odstotna točka" if m == 1 else "odstotni točki" if m == 2 else \
        "odstotne točke" if m in (3, 4) else "odstotnih točk"
    return f"{n} {w}"


def _person(eid: str) -> str:
    return f"/oseba/{eid}/"


def _award(aid: str) -> str:
    return f"/nagrada/{aid}/"


def _res(name: str) -> dict:
    return json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))


def _pct(x: float) -> str:
    return f"{round(100 * x)} %"


def _int(x: float) -> str:
    return f"{round(x):,}".replace(",", ".")


def _period(p: int, length: int = 5) -> str:
    """A period label (five years by default); the current period ends at the last year
    in the data."""
    from kulturne_nagrade import frames
    last = int(frames.editions()["year"].max())
    return f"{p}–{str(min(p + length - 1, last))[-2:]}"


# --- findings ----------------------------------------------------------------------------

def women() -> dict:
    """§1: women's share of jury seats and of awards, by five-year period."""
    g = _res("gender")
    ts = [r for r in g["time_series"] if r["n"] >= 20]
    periods = sorted({r["period"] for r in ts})
    val = lambda role: [next((r["share"] for r in ts if r["period"] == p and r["role"] == role),
                             None) for p in periods]
    band = lambda role: [next(([r["lo"], r["hi"]] for r in ts if r["period"] == p
                               and r["role"] == role), None) for p in periods]
    by = {(r["period"], r["role"]): r for r in g["time_series"]}
    first_jury_half = next((p for p in periods if by.get((p, "jury"), {}).get("share", 0) > 0.5),
                           None)
    return {
        "n": {"jury_recent": _pct(g["female_share_2016_on"]["jury"]),
              "win_recent": _pct(g["female_share_2016_on"]["winners"]),
              "jury_half_from": _period(first_jury_half) if first_jury_half else None,
              "win_1950s": _pct(by[(1950, "winner")]["share"]),
              "win_1960s": _pct(by[(1960, "winner")]["share"])},
        "chart": {"type": "lines", "props": {
            "x": [_period(p) for p in periods], "xEvery": 2, "yMax": 0.7,
            "ticks": [0, 0.25, 0.5], "refLine": {"value": 0.5, "label": "polovica"},
            "label": "Delež žensk v žirijah in med nagrajenci",
            "series": [
                {"label": "ženske med žiranti", "color": JURY, "values": val("jury"),
                 "band": band("jury")},
                {"label": "ženske med nagrajenci", "color": WINNER, "values": val("winner"),
                 "band": band("winner")}]}},
    }


INSIDER_NOTES = {  # plain-word notes where the simple verdict needs a qualifier
    "presernova-nagrada": "deloma zaradi starosti: isti rod sodi in prejema",
    "nagrada-franceta-stiglica": "ob upoštevanju starosti razlika ni več zanesljiva",
    "plecnikova-nagrada": "majhno področje: tudi drugi arhitekti so pogosto sodili",
}


def former_jurors() -> dict:
    """§3 + familiar faces: wins that went to someone who had earlier judged the same
    award (winners joining the jury later are a custom and are not counted)."""
    j = _res("juries")
    per = [r for r in j["insider_per_award"] if r["insider_wins"] >= 3]
    per.sort(key=lambda r: -r["own_rate"])
    ff = {(r["tie"], r["scope"]): r for r in j["familiar_faces"]}
    strict = ff[("any", "other_awards")]
    rows = [{"label": r["award"], "href": f"/nagrada/{r['award_id']}/", "value": r["own_rate"],
             "text": f"{r['insider_wins']} od {r['winners']}",
             "color": JURY if (r["q"] is not None and r["q"] < SIG) else GRAY,
             "note": INSIDER_NOTES.get(r["award_id"])} for r in per]
    ins = j["insider"]
    return {
        "n": {"insider": _int(ins["insider_wins"]), "insider_expected": _int(ins["expected"]),
              "insider_pct_more": _pct(ins["ratio"] - 1),
              "wins_compared": _int(ins["winners_compared"]),
              "familiar": _int(strict["with_tie"]), "familiar_expected": _int(strict["expected"]),
              "familiar_compared": _int(strict["winners_compared"]),
              "awarded_before": _int(ff[("judged_winner", "other_awards")]["with_tie"]),
              "awarded_before_expected": _int(ff[("judged_winner", "other_awards")]["expected"])},
        "chart": {"type": "bars", "props": {
            "rows": rows, "format": "pct", "valueLabel": "nagrade nekdanjim žirantom",
            "label": "Delež nagrad, ki jih je dobil nekdanji žirant iste nagrade",
            "legend": [{"label": "pogosteje, kot bi pričakovali", "color": JURY},
                       {"label": "v mejah pričakovanega", "color": GRAY}]}},
    }


def late_in_life() -> dict:
    """§18: share of laureates who died within ten years of the award, by award."""
    a = _res("age")
    rows = [r for r in a["honoured_late"] if r["winners"] >= 30]
    rows.sort(key=lambda r: -r["died_within_10y"])
    rows = rows[:10]
    pres = next(r for r in a["honoured_late"] if r["award_id"] == "presernova-nagrada")
    return {
        "n": {"pres_5y": _pct(pres["died_within_5y"]), "pres_10y": _pct(pres["died_within_10y"]),
              "pres_age": _int(pres["median_age_at_win"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": r["award"], "href": f"/nagrada/{r['award_id']}/",
                      "value": r["died_within_10y"],
                      "color": JURY if r["award_id"] == "presernova-nagrada" else GRAY,
                      "note": f"srednja starost ob nagradi {round(r['median_age_at_win'])} let"
                      if r.get("median_age_at_win") else None} for r in rows],
            "format": "pct", "valueLabel": "umrli v 10 letih",
            "label": "Delež nagrajencev, ki so umrli v desetih letih po nagradi"}},
    }


def women_to_juries() -> dict:
    """§5: from a first win to a jury seat (and back), women against men."""
    c = _res("careers")
    w, j = c["winner_to_juror"], c["juror_to_winner"]
    kw, kj = w["km"], j["km"]
    rows = [
        {"label": "ženske", "value": kw["ženske"]["10y"], "color": WOMEN},
        {"label": "moški", "value": kw["moški"]["10y"], "color": MEN,
         "note": _verdict(w["hr_p"])},
    ]
    return {
        "n": {"w2j_f": _pct(kw["ženske"]["10y"]), "w2j_m": _pct(kw["moški"]["10y"]),
              "w2j_ratio": _dec(w["hazard_ratio_female_within_genre"]),
              "j2w_n": _int(j["n"]), "j2w_f": _pct(kj["ženske"]["10y"]),
              "j2w_m": _pct(kj["moški"]["10y"]), "j2w_events": _int(j["events"]),
              "j2w_own": _pct(j["share_first_win_at_own_jury_award"])},
        "chart": {"type": "bars", "props": {
            "rows": rows, "format": "pct", "max": 0.3, "valueLabel": "v žiriji v 10 letih",
            "label": "Delež nagrajencev, ki v desetih letih sedejo v žirijo, po spolu"}},
    }


def reciprocity() -> dict:
    """§4: pairs who each sat on a jury that awarded the other."""
    r = _res("juries")["reciprocity"]
    return {
        "n": {"pairs": _int(r["pairs_observed"]), "expected": _int(r["pairs_expected"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": "pari, ki sta drug drugemu podelila nagrado",
                      "value": r["pairs_observed"], "compare": r["pairs_expected"],
                      "color": GRAY, "note": _verdict(r["p"])}],
            "valueLabel": "pari", "label": "Vzajemno nagrajevanje",
            "legend": [{"label": "dejansko", "color": GRAY},
                       {"label": "pričakovano", "color": "", "tick": True}]}},
    }


def same_lineups() -> dict:
    """§12: juries reappointed in the same line-up; no groups moving between awards."""
    n = _res("network")
    rep, trav = n["pairs_vs_field_period_null"]["repeat_pairs"], n["pairs_vs_award_null"]["travelling_pairs"]
    rep_award = n["pairs_vs_award_null"]["repeat_pairs"]
    return {
        "n": {"repeat": _int(rep["observed"]), "repeat_expected": _int(rep["expected"]),
              "repeat_ratio": _dec(rep["ratio"]), "repeat_award_ratio": _dec(rep_award["ratio"], 2),
              "travel": _int(trav["observed"]), "travel_expected": _int(trav["expected"])},
        "chart": {"type": "bars", "props": {
            "rows": [
                {"label": "pari, ki so skupaj sedeli v vsaj treh žirijah", "value": rep["observed"],
                 "compare": rep["expected"], "color": JURY, "note": _verdict(rep["p"])},
                {"label": "pari, ki so skupaj sedeli v žirijah dveh ali več nagrad",
                 "value": trav["observed"], "compare": trav["expected"], "color": GRAY,
                 "note": _verdict(trav["p"])}],
            "valueLabel": "pari", "label": "Pari žirantov, ki sedijo skupaj",
            "legend": [{"label": "dejansko", "color": JURY},
                       {"label": "pričakovano", "color": "", "tick": True}]}},
    }


def rotation() -> dict:
    """§9 + §14: repeat seats by decade, concentration, new juries and newcomers."""
    pw = _res("power")
    dec = [r for r in pw["repeat_seats"]["by_decade"] if r["size"] >= 100]
    ren = {r["period"]: r for r in pw["renewal"]}
    old = [ren[y]["top10_share"] for y in (1970, 1975, 1980, 1985) if y in ren]
    new = [ren[y]["top10_share"] for y in (2005, 2010, 2015, 2020) if y in ren]
    by = {r["period"]: r["mean"] for r in dec}
    pl = _res("pipeline")["new_juries_newcomers"]
    return {
        "n": {"repeat_1990s": _pct(by[1990]), "repeat_2020s": _pct(by[2020]),
              "top10_old": _pct(sum(old) / len(old)), "top10_new": _pct(sum(new) / len(new)),
              "multi_share": _pct(pw["multi_jury_load"]["share_multi_since_2010"]),
              "new_jury_diff": _points(100 * pl["fe_slope"])},
        "chart": {"type": "lines", "props": {
            "x": [_period(r["period"], 10) for r in dec],
            "yMax": 1, "ticks": [0, 0.25, 0.5, 0.75, 1],
            "label": "Delež sedežev, ki jih zasede nekdo, ki je v isti žiriji že sedel",
            "series": [{"label": "sedeži ljudi, ki so v isti žiriji sedeli že v prejšnjih treh letih",
                        "color": JURY, "values": [r["mean"] for r in dec]}]}},
    }


def concentration() -> dict:
    """§16: jury seats are more concentrated than awards; no climb to the crown."""
    c = _res("crown")
    con, cl = c["concentration"], c["climb"]
    return {
        "n": {"seats_top10": _pct(con["sittings"]["top10_share"]),
              "wins_top10": _pct(con["wins"]["top10_share"]),
              "once": _pct(con["wins"]["share_with_one"]),
              "crown_prior_win": _pct(cl["ugled 5"]["prior_win"]["share"]),
              "crown_prior_jury": _pct(cl["ugled 5"]["prior_jury"]["share"]),
              "tier3_prior_win": _pct(cl["ugled 3"]["prior_win"]["share"])},
        "chart": {"type": "bars", "props": {
            "rows": [
                {"label": "sedeži v žirijah, ki jih zaseda najbolj dejavnih 10 % žirantov",
                 "value": con["sittings"]["top10_share"], "color": JURY},
                {"label": "nagrade, ki jih je prejelo najbolj nagrajenih 10 % nagrajencev",
                 "value": con["wins"]["top10_share"], "color": WINNER}],
            "format": "pct", "max": 0.6, "valueLabel": "delež",
            "label": "Kako zgoščeni so sedeži v žirijah in nagrade"}},
    }


def jury_careers() -> dict:
    """§17: long careers on juries, not on winner lists; fields stay separate."""
    m = _res("mobility")
    st, cr = m["streaks"], m["crossing"]
    top = st["top_jury"][:8]
    return {
        "n": {"jury_max": _int(st["jury_max"]), "jury_max_name": st["top_jury"][0]["name"],
              "winner_max": _int(st["winner_max"]),
              "winner_max_name": st["top_winner"][0]["name"],
              "jury5": _pct(st["jury_share_5plus"]), "win3": _pct(st["winner_share_3plus"]),
              "multi_field": _pct(cr["multi_field_share"]),
              "multi_field_expected": _pct(cr["multi_field_expected"] / cr["winners"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": r["name"], "value": r["streak"], "color": JURY,
                      "text": f"{r['streak']} let", "note": f"{r['start']}–{r['end']} · {r['awards']}"}
                     for r in top],
            "valueLabel": "zaporednih let v žiriji",
            "label": "Najdaljši nizi zaporednih let v žirijah"}},
    }


def kingmakers() -> dict:
    """§20: no juror's panels produce future jurors; few cross-award paths."""
    k = _res("influence")
    km, ca = k["kingmakers"], k["cross_award"]
    return {
        "n": {"jurors": _int(km["jurors_tested"]), "winners": _int(km["panel_winners_tested"]),
              "later": _int(km["observed_total"]), "expected": _int(km["expected_total"]),
              "pairs": _int(ca["pairs_tested"]), "pairs_sig": _int(ca["significant_pairs"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": "nagrajenci najbolj dejavnih žirantov, ki so v 10 letih sami sedli v žirijo",
                      "value": km["observed_total"], "compare": km["expected_total"], "color": GRAY,
                      "note": MAYBE}],
            "valueLabel": "nagrajencev", "label": "Ali nagrajenci nekaterih žirantov pogosteje postanejo žiranti",
            "legend": [{"label": "dejansko", "color": GRAY},
                       {"label": "pričakovano", "color": "", "tick": True}]}},
    }


def repeat_winners() -> dict:
    """§21: awards given again to their own past winners; Prešernov sklad the opposite."""
    a = _res("awards")
    per = [r for r in a["repeat_winners_per_award"] if r["q"] is not None and r["q"] < SIG]
    per.sort(key=lambda r: -r["repeat_wins"])
    sklad = next(r for r in a["repeat_winners_per_award"] if r["award_id"] == "presernov-sklad")
    rows = [{"label": r["award"], "href": _award(r["award_id"]), "value": r["repeat_wins"],
             "compare": r["expected"], "color": WINNER} for r in per[:10]]
    rows.append({"label": sklad["award"], "href": _award("presernov-sklad"),
                 "value": sklad["repeat_wins"], "compare": sklad["expected"], "color": GRAY,
                 "note": "redkeje, kot bi pričakovali"})
    rw = a["repeat_winners"]
    return {
        "n": {"repeat": _int(rw["repeat_wins"]), "expected": _int(rw["expected"]),
              "awards": _int(len(rw["significant_awards"])),
              "sklad": _int(sklad["repeat_wins"]), "sklad_expected": _int(sklad["expected"])},
        "chart": {"type": "bars", "props": {
            "rows": rows, "valueLabel": "ponovne nagrade",
            "label": "Nagrade, ponovno podeljene prejšnjim nagrajencem",
            "legend": [{"label": "pogosteje, kot bi pričakovali", "color": WINNER},
                       {"label": "pričakovano", "color": "", "tick": True}]}},
    }


def presernov_two_step() -> dict:
    """§8: from a Prešernov sklad prize to the Prešernova nagrada."""
    p = _res("careers")["presernov_two_step"]
    km = p["km"]
    return {
        "n": {"share_prior": _pct(p["share_nagrada_with_prior_sklad"]),
              "gap": _int(p["median_gap_years"]), "within30": _pct(km["30y"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": f"v {y} letih", "value": km[f"{y}y"], "color": WINNER}
                     for y in (10, 20, 30)],
            "format": "pct", "max": 0.25, "valueLabel": "prejeli Prešernovo nagrado",
            "label": "Delež nagrajencev Prešernovega sklada, ki pozneje prejmejo Prešernovo nagrado"}},
    }


def ages() -> dict:
    """§6 + §7: winners getting older at the same award; women win younger."""
    a = _res("age")
    gap = [r for r in a["jury_winner_gap"] if r["winner_n"] >= 30 and r["jury_n"] >= 30]
    t, g = a["trend"]["all"], a["gender_age_gap"]
    return {
        "n": {"per_decade": _dec(t["within_award_per_decade"]),
              "gender_gap": _dec(-g["within_diff_years"]),
              "median_f": _int(g["median_f"]), "median_m": _int(g["median_m"]),
              "win_now": _int(gap[-1]["winner_median"]), "jury_now": _int(gap[-1]["jury_median"])},
        "chart": {"type": "lines", "props": {
            "x": [_period(r["period"]) for r in gap], "xEvery": 2, "format": "int",
            "yMin": 30, "yMax": 65, "ticks": [30, 40, 50, 60],
            "label": "Srednja starost nagrajencev in žirantov",
            "series": [
                {"label": "žiranti", "color": JURY, "values": [r["jury_median"] for r in gap]},
                {"label": "nagrajenci", "color": WINNER, "values": [r["winner_median"] for r in gap]}]}},
    }


def ljubljana() -> dict:
    """§11: Ljubljana ties against population, by region (winners since 2000)."""
    g = _res("geography")
    rep = [r for r in g["representation"] if r["role"] == "winner"]
    rep.sort(key=lambda r: -r["share"])
    lj = next(r for r in rep if r["unit"] == "Ljubljana")
    return {
        "n": {"lj_win": _pct(g["shares_since_2000"]["winner"]["lj"]),
              "lj_jury": _pct(g["shares_since_2000"]["jury"]["lj"]),
              "lj_index": _dec(lj["index"]), "lj_pop": _pct(lj["pop_share"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": r["unit"], "value": r["share"], "compare": r["pop_share"],
                      "color": JURY if r["unit"] == "Ljubljana" else GRAY} for r in rep],
            "format": "pct", "valueLabel": "delež nagrajencev", "compareLabel": "delež prebivalcev",
            "label": "Nagrajenci po regijah v primerjavi s prebivalstvom",
            "legend": [{"label": "delež nagrajencev", "color": GRAY},
                       {"label": "delež prebivalcev", "color": "", "tick": True}]}},
    }


def independence() -> dict:
    """§13: careers across 1991 against placebo breaks."""
    t = _res("transition")
    rows = [r for r in t["rates"] if r["role"] == "winner"]
    jur = {r["break"]: r for r in t["rates"] if r["role"] == "jury"}
    by = {r["break"]: r for r in rows}
    return {
        "n": {"win_1991": _pct(by[1991]["rate_any"]), "win_1971": _pct(by[1971]["rate_any"]),
              "win_1981": _pct(by[1981]["rate_any"]), "jury_1991": _pct(jur[1991]["rate_any"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": f"čez leto {r['break']}", "value": r["rate_any"],
                      "color": JURY if r["break"] == 1991 else GRAY} for r in rows],
            "format": "pct", "max": 0.6, "valueLabel": "nadaljevali v naslednjih 10 letih",
            "label": "Delež nagrajencev, ki so po prelomnem letu znova nagrajeni"}},
    }


def dossier() -> dict:
    """§15: the record of the dossier subject (Ignacija J. Fridl) among frequent jurors."""
    d = _res("dossier")
    ov = _res("overview")
    rec, pos, pk = d["record"], d["position_among_peers"], d["picks"]
    top = ov["top_jurors"][:10]
    if d["subject"] not in {r["entity_id"] for r in top}:
        top.append(next(r for r in ov["top_jurors"] if r["entity_id"] == d["subject"]))
    return {
        "n": {"name": d["name"], "sittings": _int(rec["sittings"]), "awards": _int(rec["awards"]),
              "first": str(rec["first_year"]), "last": str(rec["last_year"]),
              "peers": _int(pos["peers"]), "rank_sittings": _int(pos["sittings"]["rank"]),
              "rank_awards": _int(pos["awards"]["rank"]),
              "panel_later": _pct(pk["later_jury_panel_winners"]["rate"]),
              "other_later": _pct(pk["later_jury_same_awards_other_editions"]["rate"]),
              "panel_f": _pct(pk["female_share_picks"]),
              "other_f": _pct(pk["female_share_same_awards_years_other_editions"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": r["name"], "href": _person(r["entity_id"]), "value": r["sittings"],
                      "color": JURY if r["entity_id"] == d["subject"] else GRAY,
                      "note": f"{_n_awards(r['awards'])} · {r['first']}–{r['last']}"} for r in top],
            "valueLabel": "sedežev v žirijah", "label": "Največ sedežev v žirijah"}},
    }


def records() -> dict:
    """§19: who wins and who judges most often."""
    ov = _res("overview")
    t = ov["totals"]
    top = ov["top_winners"][:10]
    j = ov["top_jurors"][0]
    return {
        "n": {"wins": _int(t["wins_people"]), "winners": _int(t["winners_people"]),
              "seats": _int(t["jury_sittings_seats"]), "jurors": _int(t["jurors"]),
              "once": _pct(t["share_winners_once"]), "jurors_once": _pct(t["share_jurors_once"]),
              "top_name": top[0]["name"], "top_wins": _int(top[0]["wins"]),
              "top_juror": j["name"], "top_juror_n": _int(j["sittings"])},
        "chart": {"type": "bars", "props": {
            "rows": [{"label": r["name"], "href": _person(r["entity_id"]), "value": r["wins"],
                      "color": WINNER, "note": f"{_n_awards(r['awards'], 'različn')} · {r['first']}–{r['last']}"}
                     for r in top],
            "valueLabel": "nagrad", "label": "Največ prejetih nagrad"}},
    }


FINDINGS = {
    "zenske-v-zirijah": women, "zenske-hitreje-v-zirije": women_to_juries,
    "nekdanji-ziranti": former_jurors, "vzajemno-nagrajevanje": reciprocity,
    "iste-zasedbe": same_lineups, "menjava-zirij": rotation, "zgoscenost": concentration,
    "kariere-v-zirijah": jury_careers, "kraljevi-ustvarjalci": kingmakers,
    "ponovni-nagrajenci": repeat_winners, "presernov-sklad": presernov_two_step,
    "pozne-nagrade": late_in_life, "starost": ages, "ljubljana": ljubljana,
    "osamosvojitev": independence, "ignacija-j-fridl": dossier, "rekorderji": records,
}


def build() -> dict:
    return {k: f() for k, f in FINDINGS.items()}
