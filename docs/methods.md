# Analysis methods

All analyses live in `src/kulturne_nagrade/analysis/`, one module per theme. To run them:

```bash
uv run python -m kulturne_nagrade.analysis            # all themes, ~2.5 min (network ~2 min)
uv run python -m kulturne_nagrade.analysis gender     # one theme
```

Figures go to `plots/<theme>/` and key numbers to `results/<theme>.json`. Permutation
tests use a fixed seed, so reruns give identical numbers.

## Ground rules used everywhere

These address the systematic problems in the legacy analyses.

| Problem | Rule |
|---|---|
| One jury awards several prizes (Prešeren, ZDUS, DSKP) | Count **jury sittings**, not jury roles. In a given year, editions whose juries overlap by ≥ 80% (relative to the smaller jury, which must have at least 2 members) are one sitting (`frames.jury_sittings`). This removes 1,496 of 7,569 jury seats (20%) that the legacy code double-counted. |
| Uneven coverage: 36% of editions lack a jury, and awards enter the data at different times | Comparisons are made **within award** (fixed effects or stratified permutations), or against a null that shares the same coverage. "First win" cohorts start in 2000. |
| Recent winners have had less time to judge or win again (right censoring) | Kaplan–Meier curves and Cox models, never raw "share who later did X". |
| "Significant" by construction (a juror vs. a uniform random person) | Nulls are drawn from **comparable peers**: winners of other awards in the same field and year, optionally also the same 10-year age band. |
| Many awards tested at once | Benjamini–Hochberg q-values; per-award claims require q < 0.05. |
| LLM-estimated birth years | Only sourced birth years are used. The statistical estimate (`year_birth_estimate`) is derived from award timing, so it would be circular. Age results are re-checked on Wikidata/VIAF ages only. |
| Posthumous credits and wrong-person matches | Wins after the recorded death year are flagged and excluded from age analyses. |
| Non-persons (bands, films, institutions) | Excluded from all person-level counts by default. |

Gender comes from search-grounded LLM enrichment (99% of persons). It has not
been validated against a hand-checked sample yet.

## Themes

### coverage
Award × year matrix of what the dataset has: no record, winners only, or
winners and jury. For each award, `history_share` is the share of the award's
real history (from founding) that the data covers. This module is the first
thing to look at before reading any trend.

### gender
- **Shares over time.** The female share among winners and jury sittings, in
  5-year bins with Wilson 95% intervals. A bin is shown
  only if it has at least 30 people.
- **Homophily.** Do juries with more women pick more women? The unit is one
  winner in an edition with a known jury of at least 3 people. A linear
  probability model regresses "winner is a woman" on the female share of the
  jury. It includes award × decade fixed effects, with standard errors
  clustered by award. A permutation null reassigns jury compositions among
  editions of the same award and decade (2,000 permutations). The raw slope is
  reported alongside, to show how much confounding there is.
- **Top-prestige gap.** Are women less likely to win the prestige-5 awards
  since 2010? The same kind of model, controlled for birth decade and field,
  with standard errors clustered by award.

### age
- **Age at win by award.** The median and interquartile range for awards with
  at least 15 winners whose age is known.
- **Trend.** Age at win regressed on year, both raw and with award fixed
  effects (the within-award trend). Robustness check: Wikidata/VIAF ages only.
- **Juries vs. winners.** Median age per 5-year bin, using sittings.
- **Gender gap at win.** Age regressed on female, within award × decade.
- **Honoured late in life.** Per award (at least 30 winners since 1970): the
  share of winners who died within 5 and 10 years of the award. Kaplan–Meier,
  with people without a death year censored at the last data year. This is a
  lower bound (an undetected death counts as alive). Posthumous credits are
  excluded.

### juries (who judges whom)
- **Insider premium.** For each winner, did they sit on this award's jury in
  an earlier year? Compare this with peers: winners of other awards in the
  same genre and year, checked against the same award's jury history, so
  coverage gaps cancel. Null: shuffle award labels within each (genre, year)
  pool, 2,000 times. Per-award p-values are corrected with Benjamini–Hochberg.
  An age-matched variant also requires peers to be in the same 10-year age
  band.
- **Reciprocity.** Pairs where A sat on a jury that awarded B, and B sat on a
  jury that awarded A. Null: shuffle winners between editions of the same
  genre and year, keeping juries fixed (500 simulations).
- **Juror and winner in the same edition.** Listed for verification.
- **Familiar faces (the same people, not just the same award).** For each win at
  an award whose jury is recorded that year: did that jury include someone with a
  personal tie to the winner from an earlier year? Ties: they sat on a jury together
  (sittings, so a joint jury counts once), the juror had awarded the winner, or the
  winner had awarded the juror. Same peer design and null as the insider premium
  (`peer_premium` with a tie function): each winner's own tie history is held fixed and
  only the jury they face changes, so a well-connected winner is not counted as an
  insider just for being well connected. Peers are limited to awards with a recorded
  jury that year. Reported for every tie kind together and each alone, counting ties
  formed anywhere or **only at other awards** (the strict headline, which does not
  repeat the insider premium), with an age-matched variant (10-year bands). Caveat:
  genre is the finest field we have, so a tie may reflect a sub-field circle
  (children's literature, criticism) rather than a personal favour; the measure cannot
  tell the two apart. Replaces the legacy "incestuousness" test, which compared
  ever-jurors with everyone ever active in the discipline, ignoring time and order.

### power
- **Renewal.** Distinct people per 100 jury seats per 5-year period, and the
  share of seats held by the top 10% of that period's jurors.
- **Repeat seats.** The share of an award's jury seats held by someone who sat
  on that award's jury in the previous 3 years. Only seats where the award's
  jury is recorded in that window count, so gaps don't look like rotation.
- **Top jurors and multi-jury load**, both counted in sittings.

### careers
- **Winner → juror.** Kaplan–Meier curve of the time from a first win (2000
  onward) to a first jury seat. People who judged before their first win are
  excluded. Gender is compared with a Cox model stratified by the field of the
  first award.
- **Winning again.** Kaplan–Meier curve of the time from a first win to a
  second, by the prestige tier of the first award.
- **The Prešeren two-step.** Kaplan–Meier curve of the time from a nagrada
  Prešernovega sklada to the Prešernova nagrada, and the share of Prešernova
  nagrada winners who had won a sklad prize first.

### geography
Places are an unordered set of ties from the enrichment (`entity_locations` →
`places`). Each person is reduced to their Slovenian **units**: Ljubljana (the
city municipality) or one of the 12 statistical regions, where Osrednjeslovenska
means the central region without Ljubljana. Measures: **Ljubljana tie** (any
unit is Ljubljana), **Ljubljana only**, and **outside Ljubljana only**. Shares
are over people with at least one unit. Vague ties ("Slovenija", "Primorska")
and foreign-only people are left out of the denominator and reported as
coverage.

Biography richness confounds every measure: people with more recorded ties are
more likely to have a Ljubljana tie and can never be "Ljubljana only". All
comparisons are therefore made within the number of units (1 / 2 / 3+).

- **Shares over time** by role (winner appearances, jury sittings), 5-year bins with Wilson intervals. Only the "any tie" measure is
  plotted, because the raw "Ljubljana only" trend moves with biography detail.
- **Within-award trend.** A linear probability model of each measure on year,
  with award and richness fixed effects, and standard errors clustered by
  award.
- **Representation.** Distinct people since 2000. Each person's weight is
  split evenly across their units. Index = share of people / share of
  population (`regions.csv`, SURS, 1 January 2025), with a bootstrap 95%
  interval over people. This describes the field, not the juries, because the
  comparison population is all residents and not working artists.
- **Awards vs. their field.** For each award: the number of winners with a
  Ljubljana tie, compared with a null that shuffles award labels within (genre,
  year, richness) pools, 2,000 times. Two-sided, with Benjamini–Hochberg
  correction across awards.
- **Home advantage.** For the 18 awards seated outside Ljubljana (`SEATS` in
  the module; hand-coded from `awards.institution`): the number of winners tied
  to the seat's region, against the same null. Municipal awards are flagged,
  because a home bias is part of their rules.
- **Juries vs. their winners.** Jurors and winners of the same edition are
  stacked, and each measure is regressed on `is_jury` with edition and richness
  fixed effects.
- **Regional homophily.** The same design as gender homophily: x = the share
  of placed jurors who are outside-Ljubljana-only, y = the winner is; award ×
  decade fixed effects plus richness; permutation of jury compositions within
  strata.

Maps use GADM 4.1 boundaries (levels 1 and 2), downloaded at runtime to
`.cache/geo/`. They are not committed, because the GADM licence does not allow
redistribution.

### network
The data is a bipartite graph of people and jury sittings; two people are linked
in the projection if they sat together.

**Null model.** A bipartite configuration model within blocks (curveball
algorithm). Pick two sittings in the same block and randomly redistribute the
members they don't share. This keeps every sitting's size and every person's
number of sittings in each block. Two block definitions are used:
- **(genre, 5-year period):** people keep their field, era and activity.
- **(award, 5-year period):** people also keep their awards. Only who sits
  with whom within an award's juries is shuffled.

300 draws each, 5 trades per sitting per draw. Iteration is sorted, so the
results don't depend on Python's hash seed.

- **Repeat pairs.** The number of pairs with at least 3 joint sittings, under
  both nulls.
- **Travelling pairs.** The number of pairs who sat together on the juries of
  at least 2 (and 3) different awards. Tested only against the
  award-preserving null: the field-period null spreads each person over all of
  a field's awards, so there it would measure award loyalty, not faction.
- **Communities.** Louvain on the weighted projection, with modularity
  compared with 40 null draws and with a partition by each person's main
  genre.
- **Brokers.** Betweenness on the unweighted projection, sampled from 400
  source nodes. Each person's observed value is compared with their mean over
  40 null draws.

### transition
Did the 1991 break interrupt careers? The real break and placebo breaks (1971,
1981, 2001, 2011) are measured the same way:
- a 10-year window before and after the break;
- only awards with editions in both windows;
- people active before the break (as winner or juror) and not dead before it.

"Continued" means active again, in any role, in a spanning award in the
after-window. The comparison is made raw (by person) and within award: an LPM
of same-award continuation on break dummies, with award fixed effects and
standard errors clustered by award. The raw rates rise with the number of
spanning awards (more chances to reappear), so the within-award comparison is
the one to read.

The yearly share of new faces (people seen for the first time) is descriptive.
Left truncation inflates the early years, and new awards entering the data
inflate the late 1990s.

### pipeline
Jury → winner. (The commission tier, commission → jury, was dropped on
2026-11-01 together with the commission data; see "Commission data dropped"
below.)
- **New juries and newcomers.** Unit: a winner since 2005 in an edition with
  at least 3 recorded jurors. x = share of jurors not on that award's jury in
  the previous 3 years (only years in which the award's jury is recorded
  count). y = first win in the data. The `within_stratum_slope` design (award
  × decade fixed effects, permutation of x among editions in the stratum).

### dossier
A record of one person's jury service, compared with **peers**
(people with at least 10 jury sittings) rather than with all jurors. Measures:
- sittings and voting power (Σ 1/jury size);
- distinct awards and fields, and span of years;
- sampled betweenness on the co-jury network;
- the person's share of each award's recorded jury voting power.

Winners of the subject's panels are compared with winners of the same awards
in the same years from editions the subject did not judge:
- later jury service within 10 years (wins up to 2016, people with no earlier
  seat; Wilson intervals);
- gender (Fisher's exact test).

Co-jurors and recent panel winners are listed as ties of record. Political
affiliation is not used. Default subject: Ignacija J. Fridl. Other people can
be run with `python -m kulturne_nagrade.analysis.dossier <entity_id>`.

### crown
- **Concentration.** Gini and top-10% shares since 2000, over distinct people,
  for wins, prestige (the sum of the prestige of one's wins), jury sittings
  and jury voting power (Σ 1/jury size).
- **The climb.** A person's first win at each prestige tier (3, 4, 5) from
  2005. Measures: was there an earlier win, an earlier jury seat? Tiers are
  compared within field × year (LPM with genre × year cells, standard errors
  clustered by award). Using each tier's *first* win keeps the comparison
  symmetric; comparing crowns with arbitrary tier-3–4 wins would not be.
- **After the crown.** Kaplan–Meier curves of the time to the next jury seat
  and the next win after the first win at each tier.

### mobility
- **Crossing fields.** People with wins in two fields, against a null that
  shuffles the genre labels of all win events since 2000 (keeping field totals
  and each person's number of wins; 1,000 permutations). Lift =
  observed / expected. The null spreads a multi-winner across fields, so most
  pairs fall below 1. Read pairs relative to each other.
- **Streaks.** The longest run of consecutive years with at least one jury
  sitting, or at least one win. A missing year in the data breaks a run, so
  runs are lower bounds.
- **Several awards in one year.** Distinct awards per person-year, since 2000.
  Jurors on several juries in one year are covered in power.

## Not yet ported

Nothing substantive. Every legacy theme is ported or deliberately dropped.

Legacy analyses deliberately dropped:
- the rising-star forecasts, which used hand-tuned weights and were never
  backtested;
- the node2vec similarity "findings", which had no validation;
- the rich-club and clique counts, which are artifacts of the one-mode
  projection;
- commission "reach", which measures award size × term length;
- every commission analysis (see below);
- the minister dossier's "what-if" machinery (Markov projections, succession
  simulation). The dossier itself was rebuilt with a peer comparison (see
  `dossier`).

### overview
General counts, descriptive only. Wins are counted per (edition, person), so
each prize of a multi-prize ceremony is a win. Jury seats are counted in
sittings. People only. Lists: top 25 winners and jurors; people in both roles;
the leader(s) of each year and decade, with ties kept, and no leader when the
maximum is one; and awards by number of distinct winners. All-time lists
reflect coverage, which is dense only from about 2000.

### influence
- **Kingmakers.** For every juror with at least 10 sittings: the winners of the
  editions they judged (wins up to end − 10, people with no earlier seat),
  outcome = first jury sitting within 10 years. Each panel winner's baseline
  is the same outcome among winners of the same award within ±5 years from
  editions the juror did not judge, shrunk toward the overall rate (5
  pseudo-winners) so a small group with no later jurors does not make one look
  impossible. Null: each outcome drawn from its baseline (Poisson-binomial,
  5,000 simulations), two-sided p, BH across jurors. Jurors who sat together
  share panel winners, so the tests are not independent.
- **Jury of X → win of Y.** The §3 design for award pairs. Within a (genre,
  year) pool, shuffling award labels makes the number of X-jurors among Y's
  winners hypergeometric; pools are independent, so the exact null is the
  convolution of those pmfs (exact p, no Monte Carlo floor), BH across pairs.
  Seats are sittings filed under the sitting's main award (a ZDUS or Prešeren
  sitting is one X). A winner of Y counts only if they never sat on a jury
  that decided Y; those wins belong to §3. The cross-award total is the mirror
  of §3 (a fixed number of earlier seats is split between "own" and "other"
  awards), so only pairs are tested.

### awards
- **Repeat winners.** The §3 engine (`juries.peer_premium`) with "won this award
  before" as the prior tie. Shuffling winners across an award's own editions
  would keep each person's number of wins, so it cannot test repetition.
- **Shared juror pools.** People who sat on both juries of an award pair
  (sittings under the main award), against the network theme's curveball null
  within (genre, 5-year period), 200 draws. With ~2,900 pairs, the empirical
  tail cannot go below 1/201, so p-values come from a count distribution
  matched to the null draws' mean and variance (Poisson, or negative binomial
  if overdispersed); BH across pairs.
- **Stability and award age.** Seat-level repeat (same award's jury in the
  previous 3 recorded years) on award age (years since founding). Within one
  award, age moves with the calendar, so awards are compared with others in
  the same 5-year period (`within_stratum_slope`, period strata, award
  clusters), since 1990.

Additions to existing themes (same session):
- **careers: juror → winner.** Kaplan–Meier time from a first sitting (2000
  onward, no earlier win) to a first win; Cox by gender stratified by the field
  of the first sitting.
- **age: gap within the edition.** Median juror age minus median winner age per
  edition (sourced ages, ≥ 2 jurors and ≥ 1 winner), with the within-award
  trend (`within_stratum_slope`, award strata).
- **mobility: jurors from other fields.** Home field = field of most earlier
  wins (umbrella awards excluded, poetry as literature, ties including the
  jury's field count as inside); umbrella juries excluded; within-award trend
  by a linear probability model with award fixed effects.
- **`scripts/data_issues.py`: unusual jury sizes.** Editions at most half or at
  least double (and ≥ 2 off) the median of the same award's juries within
  ±10 years, or 1–2 jurors where that median is ≥ 4.

Legacy plots in `plots/detailed/` (66 files) were inventoried on 2026-11-01:
about 35 are covered by the themes above, about 15 were dropped as low value
(chord diagram, treemap, award name cloud, the node2vec embedding, centrality
vs wins, which is mechanical, and career timelines, which are illustrations
only), and the rest were ported with corrected methods as listed here. Not
ported yet: time-respecting jury "chains" (plot 14) and per-award reciprocity
and co-winner lift (20, 27, 46).

### network map (website)
Not an analysis theme: an interactive picture of the scene for the site,
built with node2vec and UMAP from the typed graph in `kulturne_nagrade.graph`.
It makes no claims. Method, files and the `graph.json` format are in
`docs/network-map.md`. The node2vec *findings* of the legacy project remain
dropped; here the embedding only places the nodes.

## Commission data dropped (2026-11-01)

The legacy data had member lists of the bodies that appoint juries
(`commissions.csv`, 48 awards). The user dropped them as unreliable: many
recorded "terms" spanned 8–30 years and were probably board-membership spans,
and for several awards (Prešeren above all) the "commission" and the "jury"
could not be told apart. Removed with them: commissioners on their own juries
(power), the commission ladder and closed loops (pipeline), the commission
tier of the dossier, and the commission series in the gender and geography
charts. `scripts/migrate_legacy.py` still knows the legacy file but must not
be re-run (see `docs/handoff.md`).
