# Network map (for the website)

An interactive map of the award scene: who sits on juries together, who judged
whom, and around which awards. It is a picture for exploring, not a finding.
The tested results about the network are in `docs/findings.md` (§12, §20, §21).

```bash
uv sync --group network                               # gensim, umap-learn, adjustText
uv run python -m kulturne_nagrade.network_map         # ~80 s: graph, node2vec, UMAP, exports
uv run python -m kulturne_nagrade.network_map --plots # re-render the previews only
```

## The graph (`kulturne_nagrade.graph`)

| Node | id | attributes |
|---|---|---|
| person, group, institution, work | `entity_id` | `label`, `field`, `wins`, `sittings`, `first`, `last` |
| award | `award:<award_id>` | `label`, `genre`, `field`, `prestige` |

| Edge `kind` | direction | attributes |
|---|---|---|
| `co_jury` | person — person, stored once (u < v) | `sittings`, `weight` = Σ 1/(jury size − 1), `first`, `last`, `awards` |
| `judged` | juror → winner | `editions`, `weight` = Σ 1/number of jurors, `first`, `last`, `awards` |
| `role` | entity → award | `role` (winner / jury), `count`, `first`, `last` |

Seats are sittings, so a jury that awards several prizes at once ties its members
once. `field` is the display field (10 genres merged into 6, plus *splošno* for the
umbrella awards). For a person, it is the field of most of their wins at field
awards; jury seats decide only for people with no field wins, because jurors often
sit outside their own field (writers on the Jurčičeva nagrada's journalism jury).

Querying in Python:

```python
from kulturne_nagrade import graph
G = graph.load()                                   # results/network/graph.graphml, or rebuilt
graph.summary(G, "ignacija-j-fridl")               # record, top co-jurors, judged / judged by
graph.judged_by(G, "dusan-jovanovic")              # jurors of the editions they won
graph.judged(G, "matej-bogataj")                   # winners of the editions they judged
graph.connection(G, "svetlana-makarovic", "matej-bogataj")  # shortest chain of ties
```

## Layout

- **node2vec** on an undirected weighted version of the graph. Role edges weigh
  their count, and `co_jury` and `judged` edges their weights. Settings: 20 walks
  of length 40 per node, p = 1, q = 0.5 (walks that move outward bring out
  communities), skip-gram with dimension 64 and window 5. The walks are a seeded
  numba implementation, and word2vec runs with one worker, so the layout is
  reproducible.
- **UMAP** to 2D (cosine metric, 30 neighbours, `min_dist` 0.8, fixed random
  state), scaled to about −100…100. The settings were chosen from a grid: fewer
  neighbours break the map into islands, and a smaller `min_dist` piles people
  onto their award.
- **Field labels** sit at the densest spot of each field's people, not the
  median, which would fall between the two clusters of a split field
  (visual art and architecture).

Positions summarise who appears near whom in random walks. Distances are not
tested and should not be read as measurements. Awards with no shared people
(e.g. Mantuanijeva nagrada, Zlata piščal) sit apart as small islands.

## Files (`results/network/`)

| file | committed | contents |
|---|---|---|
| `graph.json` | yes | graphology JSON for sigma.js (5 MB, ~0.6 MB gzipped) |
| `nodes.csv` | yes | every node with its attributes and `x`, `y` |
| `embedding.npz` | yes | `ids`, `vectors` (node2vec, 64-d), for "who sits in a similar place" |
| `graph.graphml` | no | the full typed graph with positions (14 MB; regenerated) |
| `edges.csv` | no | every edge with its attributes (3 MB; regenerated) |

### `graph.json` for the site

Standard graphology serialisation (`graph.import(json)`), `type: mixed`,
`multi: true`.

- **Nodes:** `label`, `x`, `y`, `size`, `color` (by field), `kind`, `field`,
  `role` (winner / jury / both; people only), `landmark` (all awards and the 40
  most active people: label these at every zoom level). People also have `wins`,
  `sittings`, `first`, `last`, and `win_list` / `jury_list` as `[year, award]`
  pairs for the info panel. Awards also have `prestige` and `genre`.
- **Edges:** `co_jury` (`sittings`, `weight`) and `judged` (`editions`,
  `weight`) only. Role ties are already in the people's lists, and per-edge
  years and awards are in `edges.csv`. This keeps the file small.
- **Graph attributes:** `regions` (field label positions and colours), `fields`
  (field → colour) and `roles` (role → colour), for the legend and for
  switching between colouring by field and by role.

Suggested rendering: no edges by default (35,000 edges make a hairball); on hover
or click, show the node's own `co_jury` and `judged` edges and its record. The
field colours fall below 3:1 contrast on the light background (palette
validator), so keep the region labels and a legend visible.

## Standalone page

```bash
uv run python -m kulturne_nagrade.network_page   # -> results/network/zemljevid.html (5.5 MB)
```

One HTML file that opens from disk, offline. It inlines graphology 0.25.4,
sigma.js 2.4.0 (pinned, downloaded once to `.cache/vendor/`) and `graph.json`.
The template is `src/kulturne_nagrade/templates/network_page.html`. The file is
gitignored; rebuild it after `network_map`. It is also the reference for the
website's version:

- colour by field or by role (toggle); the legend hides or shows a group;
- landmarks: zoomed out, awards of prestige 4–5 and the 15 most active people
  are always labelled; zoomed in, all awards and the 40 landmarks are;
- hover shows a tooltip and the node's ties (violet = shared jury, green =
  juror and winner) and dims everyone else. An award highlights its people;
- click or search (Enter) flies to the node and opens its record: wins, juries,
  closest co-jurors, the jurors who awarded the person and the winners of the
  person's juries. Every name is a link;
- field names over the regions; light and dark themes; on a phone, the panel
  moves below the map.

## Previews

- `plots/network/zemljevid_mreze.png`: coloured by field, with field and award
  landmarks.
- `plots/network/zemljevid_vloge.png`: the same layout coloured by role (winners
  only, jurors only, both), with every award and the 40 most active people named.

## Legacy

`improved_awards_processor.py` in the legacy project had these problems:
- built the graph from raw rows, so shared juries counted once per prize;
- used hand-set weights (jury–winner 3.0, field hubs 4.0);
- included commission ties;
- ran node2vec with several workers and no seed;
- ran UMAP with 5 neighbours, which gave hundreds of islands;
- drew every label, in 8 colours for role combinations.

None of this is reused.
