# Kulturne nagrade

Who gives Slovenian cultural awards, and who receives them? A dataset of **96 awards,
1949–2026**: 2,067 editions, about 5,200 wins and 6,100 jury seats held by 4,062 people and
groups, with analyses of how juries and winners relate.

**Website (in Slovenian):** https://virostatiq.com/kulturne-nagrade/ (findings, a page for
every person and award, a network map of who sits on juries together and who picked whom).

## What is in the repository

| Path | Contents |
|---|---|
| `data/` | The dataset: normalized CSV tables with a [Frictionless](https://specs.frictionlessdata.io/) `datapackage.json` |
| `src/kulturne_nagrade/` | Python package: loading, validation, analyses, network map, site export |
| `scripts/` | Data decisions (applied as code, idempotent), review lists, deployment |
| `tests/` | Dataset integrity, helpers, decision scripts, graph |
| `plots/<theme>/` | Analysis figures (Slovenian labels) |
| `results/` | Key numbers per theme, as JSON; the network map in `results/network/` |
| `site/` | The Astro website |
| `docs/` | [Data model](docs/data-model.md), [methods](docs/methods.md), [findings](docs/findings.md), [website](docs/site.md), review lists |

## Setup

```bash
uv sync
uv run pytest                                  # dataset integrity and helpers
uv run python -m kulturne_nagrade.dataset      # validate the dataset
uv run python -m kulturne_nagrade.analysis     # all analyses -> plots/, results/ (~2.5 min)

uv sync --group network
uv run python -m kulturne_nagrade.network_map  # the network map (~80 s)

cd site && npm install && npm run data && npx astro dev   # the website
```

## Method in one paragraph

Every comparison shares the data's coverage gaps: winners of an award are compared with
winners of other awards in the same field and year (or within the same award and decade),
and tested against shuffles of those comparison groups, with corrections for testing many
awards at once. Jury seats are counted per sitting, so a jury that decides several prizes at
once counts once. Time-to-event questions (from a win to a jury seat, survival after an
award) use Kaplan–Meier estimates. Details in [`docs/methods.md`](docs/methods.md).

## Sources and caveats

The records come from public sources: award websites, press releases, news articles and
reference works. The dataset is **incomplete**, especially before 2000, and some records
may be wrong. Personal details (gender, life years, places, offices) were partly collected
by automated, search-grounded enrichment; each record carries its source or confidence, and
birth years marked as estimates are statistical. **Political affiliation is not part of the
dataset.** The website shows no gender, places or offices on individual pages.

Corrections, missing editions and removal requests:
[open an issue](https://github.com/virostatiq/slo-cultural-awards/issues).

## Licence

- Code: [MIT](LICENSE).
- Data, results and figures: [CC BY 4.0](data/LICENSE.md); `data/places.csv` contains
  OpenStreetMap-derived coordinates under ODbL 1.0.

Please cite as described in [`CITATION.cff`](CITATION.cff).
