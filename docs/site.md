# Website (`site/`)

Static Astro site, Slovenian only. Every page is generated at build time from JSON
exported by Python, so all counting logic stays in `kulturne_nagrade`.

```bash
cd site
npm install
npm run data        # python export: site/src/data/*.json, site/public/data/, OG card
npx astro build     # ~4,200 pages in a few seconds -> site/dist/
npx astro preview   # serves dist/ (Astro 7 runs it as a daemon; `astro preview stop`)
SITE_URL=https://… npx astro build   # set the public domain for canonical and OG URLs
SITE_BASE=/kulturne-nagrade npx astro build   # when served from a subfolder
```

## Deployment

The site is served at https://virostatiq.com/kulturne-nagrade/ (a subfolder of a cPanel
host; the static folder sits next to a WordPress install, whose rewrite rules leave real
folders alone).

```bash
uv run python scripts/deploy_site.py            # npm run data, build with SITE_URL/SITE_BASE, upload over FTPS
uv run python scripts/deploy_site.py --no-build # upload site/dist as it is
```

The script reads `docs/deployment/remote_ftp.txt` (git-ignored, never commit it) and uploads
to `public_html/kulturne-nagrade`. Every internal link goes through `src/lib/url.ts`, so the
same code works at `/` in development; links inside data (chart rows, finding text) are
prefixed when rendered.

## Analytics and consent

Google Analytics (GA4) loads only after the visitor clicks "Sprejmi" in the bottom-right
banner (`src/components/Consent.astro`); "Zavrni" loads nothing and removes `_ga` cookies.
The choice is stored in localStorage; footer link "Nastavitve piškotkov" and the button on
`/zasebnost/` reopen the banner. Google signals and ad personalisation are off. Analytics
never loads on localhost.

The network map (`results/network/graph.json`) must be built first
(`python -m kulturne_nagrade.network_map`); `npm run data` copies it.

## Pages

| URL | Content |
|---|---|
| `/` | intro, counts, entry points, top awards, most awards and jury seats |
| `/seznam/` | all people and awards; search without diacritics; filters by type, field, role, award, decade; sorting by clicking a column heading; the state is kept in the URL |
| `/oseba/<id>/` | a person: field, role, years in the data, life years (flagged when automated), wins, jury seats (a shared jury listed once), two-column ego network (static SVG), closest co-jurors, jurors who awarded them, winners of their juries, link to the map |
| `/nagrada/<id>/` | an award: description, organiser, numbers (coverage, median age, share of women, repeat seats), tested notes (insider wins, repeat winners) when q < 0.05, all editions with winners and jury, most frequent jurors |
| `/leta/`, `/leto/<year>/` | years by decade with a bar for the number of awards; everything awarded in a year |
| `/zemljevid/` | the interactive network map (sigma.js 2.4, graphology 0.25); `?oseba=<id>` opens on a person |
| `/o-podatkih/` | sources, what is missing, how we count (`#metode`), the map (`#zemljevid`) |
| `/popravki/` | how to report a correction; `?zapis=oseba/<id>` shows the record (noindex) |

| `/ugotovitve/`, `/ugotovitve/<id>/` | findings for the general public: a plain headline, one chart, short text, "Kako smo merili" |

To come: statistics (folded into findings, a few overview charts), fields, downloads,
per-page OG images, the local editor.

## Findings

Text in `site/src/content/ugotovitve/<id>.md` (frontmatter: title, lede, order, chartTitle,
chartNote, method, awards). Numbers appear as `{{key}}` and are filled from
`src/data/findings.json`, written by `kulturne_nagrade.site_findings` from `results/*.json`
during `npm run data`; an unknown key stays visible so it shows up in review. Each finding
has one chart spec (`bars`, `lines` or `placemap`) rendered by `src/components/charts/`
(HTML/SVG at build time, a table view in a `<details>`), and optionally `extra` charts
(title, note, spec) shown after the text. `placemap` (Ljubljana finding) is a bubble map
of places with a Vsi / Nagrajenci / Žiranti switch and a hover tooltip; counts only. Charts are for the general public: plain
labels, verdicts in words ("razlika je prevelika, da bi bila naključna"), no p-values.
Only "judged first, then won" counts as an insider; laureates joining juries later is a
custom. Individuals are written about in neutral grammar (no gendered verb forms).

## Design ("Mreža")

Dark only: a plum night sky (`--bg #171022`) with the network map as the site's identity.
Chosen by the user from three static proposals (bronze plaque, year strip, network).

- **Type:** Newsreader (serif, light weight for headings and big numbers) and Hanken Grotesk
  (text and interface), both self-hosted through `@fontsource-variable` (no Google Fonts calls).
- **Colour:** the chrome stays neutral (ink, lilac `--accent` only for focus and the current
  page); colour in the content comes from the data (fields, roles). Blue and orange stay
  reserved for gender.
- **The sky:** `src/lib/sky.ts` draws every node of the network map on a canvas from
  `public/data/tocke.json` (`site_export.map_points`, ~70 kB). It is the home-page backdrop and,
  dimmed with the person's ties, the "Na zemljevidu" panel on person pages
  (`people[*].pos` from `results/network/nodes.csv`).
- No all-caps labels; headings are sentence case. Buttons and fields are pills.

## Rules

- **Personal data:** birth and death years appear with their source; automated
  ones are flagged ("samodejno pridobljeno, morda netočno"). The statistical
  estimate is never exported. Gender, places, offices and automated biography
  notes are not shown on individual pages. Political affiliation is not in the data.
- **Search engines:** people with one appearance get `noindex` (about 2,200)
  until the data is checked.
- **Open Graph:** every page sets title, description, URL, type, locale and a
  1200 × 630 image (the default `/og/privzeto.png` for now; pages pass their own
  `image` once per-page cards exist), plus a Twitter large-image card.
- Colours come from the export (`meta.fields`, `meta.roles`), so the site, the
  map and the analysis plots share one palette; blue and orange stay reserved
  for gender.
