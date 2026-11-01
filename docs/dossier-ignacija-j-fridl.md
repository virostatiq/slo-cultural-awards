# Dossier: Ignacija J. Fridl

Ignacija J. Fridl was appointed Minister of Culture. This is a record of Fridl's
service on award juries, drawn only from the public jury lists in the dataset
and compared with peers. Political affiliation
is not used (see `docs/review/party-offices.md`).

Numbers come from `results/dossier.json` and figures from
`plots/dossier/ignacija-j-fridl/`. To rerun, or to build the same dossier for
someone else:

```bash
uv run python -m kulturne_nagrade.analysis dossier
uv run python -m kulturne_nagrade.analysis.dossier <entity_id>
```

## Method in brief
- **Peers** are the 129 people with at least 10 jury sittings. The legacy
  dossier ranked against all ~1,700 jurors, most of whom sat once, so every
  percentile looked extreme.
- **Sittings**, not raw jury roles: the Prešeren jury that awards both prizes
  counts once.
- **Voting power** = 1 / jury size. One seat on a 3-person jury weighs five
  times as much as one seat on a 15-person jury.
- Network **betweenness** is computed on the co-jury network, as in the
  network theme.

## Record (`zapis_sluzbe.png`)
- **34 jury sittings** on **9 awards** in 3 fields (theatre, literature,
  general culture), 1997–2019. Voting power 6.5.
- **No awards won** in the data.
- The longest service is at the **Rožančeva nagrada** (10 sittings, 2002–2015).
  Early seats were on small theatre juries: Grumova nagrada (3 members, 4×)
  and Borštnikovo srečanje (4×).

## Position among peers (`polozaj_med_vrstniki.png`)
| measure | Fridl | rank among 129 peers | peer median |
|---|---|---|---|
| jury sittings | 34 | 5th | 14 |
| voting power | 6.5 | 5th | 2.5 |
| distinct awards | 9 | 2nd | 3 |
| distinct fields | 3 | 6th (tied) | 2 |
| betweenness | 0.068 | 1st or 2nd (sampled) | 0.006 |
| own awards | 0 | one of the 40% of peers with none | 1 |

Fridl is among the most active jurors, and is one of the **two most central
people in the co-jury network**, with Andrej Blatnik (betweenness is sampled, so
the two swap first place between runs). That comes from serving on many
different awards across fields. Compared with random juries that keep each
person's fields and number of sittings, Fridl is more central than expected
(network theme, `plots/network/povezovalci.png`).

## Share of each award's juries (`delez_pri_nagradah.png`)
- **Fabula:** 9% of all recorded jury voting power, the largest of 21 jurors.
- **Rožančeva nagrada:** 9%, second of 27 jurors.
- At every other award the share is 4% or less.

## Picks
- Fridl's panels decided **38 editions**, with 103 winner slots and 94 distinct
  winners. The repeat picks are **Igor Samobor** (3×) and seven people
  picked twice: Aldo Kumar, Goran Vojnović, Primož Čučnik, Vito Taufer, Matjaž
  Zupančič, Peter Musevski and Uroš Smolej.
- **Did Fridl's panels produce future jurors?** 24% of winners from Fridl's
  panels (17 of 71) sat on a jury within 10 years. For winners of the same
  awards in the same years from editions Fridl did not judge, the rate is 18%
  (38 of 215). The intervals overlap (16–35% vs. 13–23%), so there is no clear
  difference. The legacy "juror pipeline" did not have this comparison.
- **Gender:** 28% of the winners Fridl's panels picked were women, against 35%
  at the same awards in the same years without Fridl (29 of 103). The difference is within chance (Fisher p = 0.24).

## Ties to note in office
These are relationships of record, listed for transparency rather than as
findings:
- **72 co-jurors**, 30 of them in 2012 or later. The most frequent are Edvard
  Kovač (10 joint sittings, Rožančeva, until 2015), Jaroslav Skrušný (7), Vasja
  Predan (6), and Nadja Zgonik and Milček Komelj (5 each, until 2019 and 2017).
  The full list is in `results/dossier.json` → `ties`.
- **17 winners** picked by Fridl's panels since 2012.

## Caveats
- The data covers 95 awards; juries are missing for 36% of editions. Seats on
  awards that are not in the dataset are not counted.
- Commission (board) terms are not used: the commission data was dropped as
  unreliable on 2026-11-01.
- Betweenness is sampled (400 source nodes), so ranks near the top can swap
  between runs with a different seed.
