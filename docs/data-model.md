# Data model

The dataset is a set of normalized CSV tables in `data/`. They replace the
legacy single wide CSV (`zirije_plus_nagrajenci.csv`), which packed several
names into one cell and depended on correction files that had to be
re-applied on every load.

The column definitions live in `src/kulturne_nagrade/dataset.py` (`SCHEMA`).
`data/datapackage.json` ([Frictionless Data Package](https://specs.frictionlessdata.io/data-package/))
is generated from that file, and `uv run pytest` validates every table against
it.

## Principles

1. **One fact per row.** Every entity-in-a-role is its own row.
2. **Stable slug IDs.** Awards, editions and entities have ASCII slug IDs
   (`kresnik`, `kresnik-2025`, `ana-schnabl`), so a name can be corrected
   without breaking references.
3. **Corrections are applied once.** Name merges were applied during
   migration. The variant spellings are kept in `aliases.csv`.
4. **Plain UTF-8 CSV**, comma-separated, with a header row. Empty cell = unknown.
   Booleans are `True` / `False`.
5. **English column names, Slovenian content.**

## Tables

```
data/
├── awards.csv             one row per award
├── editions.csv           one row per award edition
├── entities.csv           winners and jurors
├── roles.csv              who won or judged which edition
├── aliases.csv            alternate spellings → entity_id
├── entity_locations.csv   places associated with an entity
├── places.csv             geocoding of every place string in entity_locations
├── regions.csv            population of the statistical regions (+ Ljubljana)
├── entity_offices.csv     public offices and memberships
├── entity_sources.csv     source domains consulted during enrichment
├── meta/not_duplicates.csv  name pairs confirmed to be different people
└── datapackage.json       generated schema
```

### `awards.csv`
| column | notes |
|---|---|
| `award_id` | slug, PK |
| `name` | canonical Slovenian name |
| `genre` | literatura, poezija, film, gledališče, ples, glasba, likovno-vizualna umetnost, arhitektura, novinarstvo, umetnost in kultura |
| `prestige` | 1–5, hand-assigned |
| `institution` | awarding body |
| `funding_source` | state-majority, state-agency, mixed, private-independent |
| `funding_confidence` | high / medium / low |
| `founded`, `ended` | the award's real history, **not** the dataset's coverage |
| `description` | Slovenian, 4–6 sentences |

### `editions.csv`
| column | notes |
|---|---|
| `edition_id` | `{award_id}-{year}`, with `-2`, `-3` when a year has more than one row |
| `award_id`, `year` | |
| `category` | sub-category, where known (empty for now) |
| `jury_known` | `False` when the jury is missing from our sources |
| `source` | URL or citation (empty for now) |

### `entities.csv`
One table for everything that can win or judge.

| column | notes |
|---|---|
| `entity_id` | slug, PK |
| `name` | canonical display name |
| `entity_type` | `person`, `group` (bands, choirs, art collectives), `institution` (bureaus, societies, theatres, festivals, offices), `work` (a film, series or song credited as the winner) |
| `gender` | `m` / `f`, persons only |
| `year_birth` | a sourced birth year, persons only |
| `year_birth_source` | `wikidata`, `viaf`, `llm` (search-grounded lookup), `enrichment` (initial grounded enrichment) |
| `year_birth_estimate` | statistical estimate from award/jury timing, **only** where no sourced year exists. Never mixed into `year_birth` |
| `year_death` | |
| `enrichment_confidence` | high / medium / low |
| `note` | short Slovenian description, non-persons only |

Age is left out because it can be calculated. **Political affiliation is not
published.**

### `roles.csv`
`edition_id`, `entity_id`, `role` (`winner` / `jury`), `ord` (position in the
source list).

### `aliases.csv`
`alias`, `entity_id`. Spelling variants found in sources. An alias is never
also a canonical name.

### `entity_locations.csv`, `entity_offices.csv`, `entity_sources.csv`
Multi-valued enrichment data, one row per value. `entity_offices.kind` is
`office` or `membership`. Sources are stored as domains only: the original
grounding URLs were temporary redirects that have stopped working.

### `places.csv`
One row per distinct `entity_locations.place` string (PK `place`).

| column | notes |
|---|---|
| `canonical` | the folded name (spelling and exonym variants unified: `Ljubljana, Slovenija` → `Ljubljana`) |
| `kind` | settlement, region, country, natural, other, unknown |
| `scope` | `si` / `foreign`; empty when unresolved |
| `country_code` | ISO 3166-1 alpha-2, lowercase |
| `si_region` | statistical region, for Slovenian places that map to exactly one |
| `si_municipality`, `is_ljubljana` | `is_ljubljana` = in the City Municipality of Ljubljana (districts such as Šiška count) |
| `lat`, `lon` | WGS84 |
| `resolution`, `confidence`, `note` | how the place was resolved (Nominatim query type, hand override, anchor town) |

Built once by `scripts/migrate_places.py` from the legacy geocoder (OpenStreetMap
Nominatim, statistical regions by point-in-polygon against GADM 4.1). That script
also applied nine hand fixes, e.g. *Rim* (Rome), which the legacy geocoder had put
in a hamlet near Črnomelj. Edit the CSV directly from now on, and add a row here
whenever a new place string appears in `entity_locations.csv`; the integrity test
fails otherwise.

### `regions.csv`
`region`, `population`, `population_date`, `source`, `note`. The 12 statistical
regions with the City Municipality of Ljubljana as a 13th unit; the
Osrednjeslovenska row excludes it.

## Migration from the legacy project

`scripts/migrate_legacy.py` built these tables from the legacy research
codebase. Besides restructuring the data, it:

- applied 141 name merges, resolving chains so each alias points at the final
  canonical name;
- reclassified non-persons. The legacy data only had person/group and missed
  about 60 choirs, bands, institutes, theatres and companies, which it listed
  as persons;
- split two cells that joined people with "in" (Jože Ciuha in Janez Lenassi;
  Petra Vidali in Kaja Bucik Vavpetič);
- cleaned the 2006 and 2007 Hudi maček jury cells, where the Young Hudi maček
  winner had been glued onto a juror's name;
- fixed a genitive-case name (Branka Madžareviča → Branko Madžarevič);
- dropped the commission member lists altogether (2026-11-01; unreliable, see
  `docs/methods.md`);
- fixed one record with age and birth year swapped (Alenka Gregorič);
- left out derived outputs, enrichment backups, run logs and political
  affiliation.

Things that need a human decision are listed in `docs/review/`:

- `duplicate-editions.md`: 45 (award, year) pairs with more than one row, and
  12 editions with no winners;
- `resolved-names.md`: names the enrichment identified differently (typo
  fixes vs. fuller names vs. a different person), plus diacritic variants.

Once the review is done, `data/` is the source of truth. Re-running the
migration would overwrite any later edits.
