# Handoff: state as of 2026-11-01 (end of session 5)

Read this first in a new session, together with `CLAUDE.md`,
`docs/data-model.md`, `docs/methods.md` and `docs/findings.md`.

## Last session (2026-11-01, session 5)

**Site design makeover.** The phase-1 site looked generic, so three dark static proposals
were built (bronze plaque, year strip, network sky); the user chose **"Mreža"** (the network
sky). Applied to every page; see `docs/site.md`, "Design":
- dark only (light mode removed), plum `--bg #171022`; Newsreader + Hanken Grotesk,
  self-hosted via `@fontsource-variable` (new npm dependencies);
- `site/src/lib/sky.ts` draws the network map on a canvas from the new
  `public/data/tocke.json` (`site_export.map_points`); home-page hero and the
  "Na zemljevidu" panel on person pages (new `pos` field per person);
- no all-caps labels; pill buttons and fields; map page restyled to match;
- headline changed by the user to "Kdo podeljuje slovenske kulturne nagrade in kdo jih
  **prejema**?" (site and OG card);
- person stats now use correct plurals ("2 nagradi").
Checked in Chrome at desktop and phone width. Not done: the year index (`/leta/`) still uses
plain lilac bars (could use field colours).

## Session 4 (2026-11-01)

Review decisions by the user, applied through the decision scripts:
- **Commission data dropped** as unreliable. `data/commissions.csv` is gone, and
  so are `frames.commission_terms()`/`commission_seats()` and every commission
  analysis: power (commissioners on own juries), pipeline (ladder, closed
  loops; it is now jury → winner only), dossier (commission tier), and the
  commission series in gender and geography. Findings §10 is a placeholder,
  §14 keeps only "new juries and newcomers". See `docs/methods.md`,
  "Commission data dropped".
- **Party offices deleted:** 12 rows in `entity_offices.csv` (Vane Gošnik's
  assembly office kept). `DELETE_OFFICES` in `apply_edition_decisions.py`.
- **Zlata ptica relabelled to the ceremony year (+1 for the whole series,
  now 1976–2015).** Every dated source has the ceremony in the spring after
  the year the awards are for, from "prvič podeljena za leto 1975" to 2012
  → 5. 6. 2013 (sources in `duplicate-editions.md`). `SHIFT_SERIES` in
  `apply_edition_decisions.py`; the series' first label (1975) is the
  re-run sentinel, and pre-shift drops are skipped once shifted.
- **New award: Zlata strela** (Bunker, Stara mestna elektrarna, 2024–2026;
  from aplavz.art and rtvslo), via the new `scripts/add_awards.py` (awards
  as data, idempotent). 14 new, unenriched entities. Nataša Živković is both
  juror and laureate in 2026 (both aplavz.art reports say so).
- **New test** `tests/test_decision_scripts.py`: every decision script must
  leave `data/` byte-identical on a re-run. It caught a bug where the old
  `zlata-ptica-2013` drop deleted the shifted 2012 edition.
- **New theme `overview`** (findings §19): most frequent winners and jurors,
  overall, per decade and per year (`plots/overview/`). Also new:
  `plotting.ROLE_COLOR` (winners green, jurors violet). Gender and geography
  used blue/orange for roles, which clashed with the gender hues; both now
  use it.
- **Legacy `plots/detailed/` ported** (66 plots inventoried; see the end of
  `docs/methods.md`). New themes `influence` (kingmakers for every juror with
  ≥10 sittings; jury of X → win of Y, exact hypergeometric p) and `awards`
  (repeat winners via `juries.peer_premium`, shared juror pools, stability vs
  award age). Additions: careers juror → winner, age gap within the edition,
  mobility jurors from other fields, and an "unusual jury sizes" list in
  `data_issues.py` (36 editions to review). Findings §5, §6, §17, §20, §21.
  `juries.insider_premium` now wraps the general `peer_premium` (output
  verified identical).
- **Network map for the website** (`docs/network-map.md`): typed graph in
  `kulturne_nagrade.graph` (build, load, summary, judged_by, connection),
  node2vec (seeded numba walks + gensim) → UMAP layout in
  `kulturne_nagrade.network_map`. Outputs in `results/network/`: `graph.json`
  (graphology for sigma.js), `nodes.csv`, `embedding.npz`. `graph.graphml` and
  `edges.csv` are regenerated and gitignored. Previews:
  `plots/network/zemljevid_mreze.png` (by field) and `zemljevid_vloge.png` (by
  role, every award and the 40 most active people named). New optional dependency
  group `network` (gensim, umap-learn, adjustText). 4 graph tests (30 in total).
  Standalone offline page: `python -m kulturne_nagrade.network_page` →
  `results/network/zemljevid.html` (gitignored; template in
  `src/kulturne_nagrade/templates/`). Tested in Chrome: search, selection, ties,
  role toggle, dark mode.
- **Astro site started** (`site/`, `docs/site.md`): home, `/seznam/` (the list,
  renamed from "Iskanje" by the user; sort by clicking a column heading; search
  field on its own row, smaller dropdowns below), a page per person (4,062) and
  award (96), year pages, the map (full record in the side panel, as in the
  standalone page), about the data, corrections. Long name lists collapse behind
  a "pokaži vse (N)" button. Data from `kulturne_nagrade.site_export`. OG tags
  on every page (default card `/og/privzeto.png`; per-page images to come).
  Decisions: local editor (not built yet), pages for everyone (one-off people
  noindex), Slovenian only.
- **Wording chosen by the user** (keep it): "Nagrada je ponovno podeljena
  prejšnjim nagrajencem" (also the repeat-winners plot title); "to osebo so
  nagradili"; "Nagrajenci tega žiranta"; "žirant–nagrajenec" for the green tie
  type (not "žirant in nagrajenec", which read as a role).
- Findings and the dossier doc re-checked against the new results. §12 had
  been stale since the session-3 jury-sittings fix (travelling pairs are 243
  against 246 by chance, and 10 against 12 for 3+ awards).

## Session 3 (2026-11-01)

Ported every remaining legacy analysis, as eight new themes (findings §11–18):
geography, network, transition (1991 against placebo breaks), pipeline
(commission → jury → winner), dossier (Ignacija J. Fridl, peer comparison;
`docs/dossier-ignacija-j-fridl.md`), crown (concentration, the climb),
mobility (crossing fields, streaks) and, in age, honoured late in life.

**Bug fixed in `frames.jury_sittings`:** a one-person jury was merged with any
jury its member sat on (chaining Bert/Kosobrin into Prešeren 2024). Also new:
`common.within_stratum_slope()` (shared by gender, geography and pipeline).
(The commission helpers added that session were removed in session 4.)

Details of the first part of the session:
- **Geography.** The legacy geocoding was migrated into `data/places.csv`
  (1,598 place strings, with 9 hand fixes such as *Rim* = Rome) and
  `data/regions.csv` (population, with Ljubljana carved out), with schema and
  FK checks. New code: `frames.entity_geography()` and `analysis/geography.py`
  (6 figures). Findings §11.
- **Network.** `analysis/network.py` (3 figures), using a curveball bipartite
  null within (genre, period) and (award, period) blocks. Findings §12.

Both are in `docs/methods.md`. The tests were extended (23 pass).

## Session 2 (2026-11-01)

Resolved the duplicate-editions and resolved-names reviews: 30 editions
dropped, 14 merged, Desetnica/Kresnik 2026 added, 8 winnerless editions
filled or dropped; 57 entity renames, ~160 aliases, 4 groups un-personed,
6 wrong-person enrichments cleared, 11 entity merges (incl. 7 hidden
duplicates). Analyses re-run and `docs/findings.md` updated; no headline
changed. `scripts/data_issues.py` now skips aliases already decided in the
names review.

## Where things stand

| Goal (from CLAUDE.md) | Status |
|---|---|
| Restructure the dataset | **Done.** Normalized CSVs in `data/`, schema in `src/kulturne_nagrade/dataset.py`, `datapackage.json` generated, integrity tests. |
| Analyse trends | **Done.** 17 themes: coverage, gender, age, juries, power, careers, geography, network, transition, pipeline, dossier, crown, mobility, overview, influence, awards (+ honoured late, in age). Every legacy analysis is ported or deliberately dropped (`docs/methods.md`). |
| Submit to GitHub | **Not started.** No remote. Branch is `main`. Decide on a licence first (data + code). |
| Astro site with backend editor | **In progress.** Phase 1 built and reviewed; design "Mreža" applied (session 5, `docs/site.md`). Phase 2 and the local editor to come. |
| Social-media visuals (Slovenian) | **Not started.** The analysis plots in `plots/` already use Slovenian labels and number format, but they are analysis figures, not social cards. |

## Commands

```bash
uv sync
uv run pytest                                  # dataset, helpers, decision scripts, graph (30 tests)
uv run python -m kulturne_nagrade.analysis     # all analyses (~2.5 min) -> plots/<theme>/, results/<theme>.json
uv sync --group network && uv run python -m kulturne_nagrade.network_map   # website network map (~80 s)
uv run python -m kulturne_nagrade.analysis.dossier <entity_id>   # dossier for anyone else
uv run python scripts/data_issues.py           # refresh docs/review/data-issues.md
uv run python scripts/apply_edition_decisions.py  # idempotent; decisions as data in the script
uv run python scripts/apply_name_decisions.py     # idempotent; reads docs/review/resolved-names.md
uv run python -m kulturne_nagrade.network_page    # standalone offline map -> results/network/zemljevid.html

# website (site/)
cd site && npm install
npm run data                                   # export JSON from Python (needs the network map built)
npx astro dev --port 4321 --host 127.0.0.1     # Astro 7 runs it as a daemon: `npx astro dev stop|status|logs`
npx astro build                                # ~4,200 pages in seconds; SITE_URL=https://… for OG/canonical URLs
```

## Key decisions (made by the user)

- Branch `main`.
- **Political affiliation is not published.**
- Entity types: `person`, `group`, `institution`, `work`.
- English column names, Slovenian content.
- Plots go to `plots/<theme>/` at the repo root.
- Review items: the user researches and reports decisions; don't guess.
  Prefill a proposed decision per row marked [sure] / [check], so the user
  only answers the [check] ones.
- Year label = **ceremony year** for every award (Zlata ptica relabelled in
  session 4).
- **No commission data.** Dropped as unreliable (session 4); don't re-add it
  from the legacy project.

## Important conventions

- **`data/` is now the source of truth.** Do not re-run
  `scripts/migrate_legacy.py`: it would overwrite manual edits (one has
  already been made, the Dragica Haramija title fix). Edit the CSVs directly
  and keep `aliases.csv` updated when renaming.
- **Record data fixes as decisions**, not ad hoc edits: add them to
  `scripts/apply_edition_decisions.py` (editions/roles), `scripts/add_awards.py`
  (new awards with their editions) or the review file read
  by `scripts/apply_name_decisions.py` (entities). Both append to a log in
  `data/meta/` with a source, and re-running is a no-op.
- **Web-search answers are often Google AI overviews.** Cross-check them
  against our own data (jury overlap with adjacent years, other editions)
  before applying; several were wrong (e.g. "Bibič award did not exist in
  2016"). Mark single-source AI answers as unverified in the log.
- **Entity ids stay stable** when names are corrected; rename an id only if it
  carries junk from the legacy name.
- **Places.** `places.csv` is the source of truth now; `scripts/migrate_places.py`
  refuses to overwrite it. Every new `entity_locations.place` string needs a
  row in it (the FK test fails otherwise). GADM boundaries are downloaded to
  `.cache/geo/` at runtime and gitignored, because the licence does not allow
  redistribution.
- **Geography measures depend on how detailed a biography is.** Compare within
  the number of Slovenian ties (`richness`), never with raw "Ljubljana only"
  shares.
- New entities added from reviews have no gender or birth year yet
  (Karin Sabadin, Marjeta Drobnič, Marjan Kovačevič Beltram, Marjan Bocevski,
  Andreja Borin); they are excluded from gender/age figures until enriched.
- **Count jury seats with `frames.jury_sittings()`, never with raw jury
  roles.** Juries awarding several prizes at once (Prešeren, ZDUS, DSKP)
  would otherwise be counted several times.
- **Ages.** Use `age` (sourced birth year only). `age_any` includes the
  statistical estimate, which is circular for timing questions. Posthumous
  credits have no age.
- **Uncertainty.** Every claim needs a comparison that shares the data's
  coverage gaps (within-award fixed effects, or a stratified permutation)
  and right-censoring handling (Kaplan–Meier or Cox). See `docs/methods.md`,
  "Ground rules".
- **Site:** all counting stays in Python (`site_export`); the site only renders.
  Person pages show no gender, places, offices or automated notes; automated life
  years are flagged. Every page needs OG tags via `Base.astro` (`title`,
  `description`, optional `image`). Slovenian only; use neutral wording ("ta
  oseba") unless the user picks otherwise. sigma 2.4 / graphology 0.25 are
  CommonJS: import them through the `unwrap` helper in `zemljevid.astro`. The site is dark only;
  use the tokens in `global.css` (no new accent colours; colour comes from fields and roles).
- **Plots** go through `kulturne_nagrade.plotting` (roles use `P.ROLE_COLOR`): `P.figure`, `P.subtitle`
  after `set_title`, `P.source_note` last, then `P.save(fig, theme, name)`.
  Use `P.pct` / `P.dec` / `P.pct_fmt` for Slovenian numbers (decimal comma,
  "19 %"). Orange is reserved for women and blue for men; don't reuse them for
  other meanings.

## Open review items (waiting on the user)

All in `docs/review/`:
1. `duplicate-editions.md`: **applied** (see its status block). Left:
   - Zlata ptica pre-2000 editions list one winner a year and are incomplete
     (Jožica Avbelj's 1979 award is missing, for example); the last edition
     (2015, Kolektivni projekt Zombie) is unverified.
   - NFKP 2024 and Trubarjevo 2025: kept as two editions each, categories
     unknown (row 1 of NFKP is the FIPRESCI award).
   - 3 editions with no winners: Bernekerjeva 1996, Bert 2020 (Bert and
     Kosobrin list the DSR board as jury every year), Bibič 2016.
2. `resolved-names.md`: **applied** (see its status block). Left: Ida / Ida Weiss,
   Samo Strelec / Samo M. Strelec, Anja Bezlova.
3. `data-issues.md`: 53 roles credited after death (wrong-person enrichment
   matches or real posthumous honours), 20 suspect merges
   (Damjan/Damjana Černe, Iva/Ivo Ban…) and 36 unusual jury sizes (partial or
   merged jury lists, e.g. Kritiško sito 2012/2014/2024 with one juror).
4. In `results/juries.json` → `judge_and_winner_same_edition`: 11 people
   listed as both juror and winner of the same edition (Zlata strela 2026 is
   sourced; the others need checking).
5. ~~Commissioners on their own juries~~: dropped with the commission data.
6. ~~`party-offices.md`~~: applied.
7. ~~Closed loops~~: dropped with the commission data.
8. Prešeren jury lists: before the commission data was dropped, 92% of our
   Prešeren jury seats matched the board list. Both came from the legacy
   source, so check whether the Prešeren "jury" rows are really the jury.

Once decisions come back, apply them to `data/*.csv`, re-run the tests and
analyses, and update `docs/findings.md`.

## Suggested next steps

1. **Open review items 1–4 and 8 above.**
2. **Validate gender and places** on hand-checked samples (~100 and ~50).
3. **GitHub.** Licence (e.g. CC BY 4.0 for data, MIT for code; OSM-derived
   coordinates in `places.csv` are ODbL), README, CI running `pytest`.
4. **Social cards** from the headline findings. Strong candidates: the
   Ljubljana map (§11), jury seats more concentrated than awards (§16), the
   41-year jury streak (§17), and Prešernova coming late in life (§18). Check
   the Slovenian with the kontekst tools.
5. **Site, phase 2** (agreed plan, in this order): findings (§1–21 as short
   Slovenian stories with one chart each and a share image), statistics
   (interactive versions of the analysis charts; Observable Plot), fields
   (`/podrocje/<field>/`), downloads (CSV, datapackage, licence, citation),
   per-page OG images (person, award, year, finding). Then the **local editor**:
   forms that edit `data/*.csv`, run the dataset validation and append to the
   decision logs in `data/meta/`; local only, no login.
6. **Data check raised in review:** Drago Jančar is coloured as journalism
   (11 jury seats there); check how the Jurčičeva nagrada is classified in
   `awards.csv` (genre).
7. **Domain:** OG and canonical URLs use a placeholder until `SITE_URL` is set.

## Legacy project

`/home/virostatiq/PycharmProjects/test/nagrade`. Read-only reference. Its
`.env` holds API keys; never copy it. A critical inventory of its analyses
(what was wrong, what to keep) is summarised in `docs/methods.md`, "Not yet
ported" and "deliberately dropped".
