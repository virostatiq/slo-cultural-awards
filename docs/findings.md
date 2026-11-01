# Findings

Numbers come from `results/*.json` (run of 2026-11-01, after the duplicate-editions
and resolved-names reviews, the Zlata ptica relabelling to ceremony years, the
addition of Zlata strela and the removal of the commission data). The data covers
96 awards, 2,067 editions and 1949–2026, with jury lists for 64% of editions. Coverage is
dense from about 2000; before that, results rest on fewer awards. See
`docs/methods.md` for how each number was computed and `plots/<theme>/` for the
figures.

## Headline findings

### 1. Women are now the majority on juries, but not yet among winners
Women's share has risen steadily on juries and among winners. In 2016–2026,
women held **51%** of jury seats and won **43%** of awards. Juries
crossed parity around 2020 (52% in 2020–24). In the 1950s and 60s, women won
10–19% of awards and held almost no jury seats.
*Figure: `plots/gender/delez_zensk_skozi_cas.png`*

### 2. Juries with more women do not pick more women, once like is compared with like
Looked at naively, an all-female jury is **37 percentage points** more likely to
pick a woman than an all-male one. Within the same award and decade, the
effect drops to **+8 points** and is not significant (95% CI −4 to +20;
permutation p = 0.15; 3,087 winners, 73 awards). The naive gap exists because
women entered juries and winner lists over the same decades and in the same
fields. This overturns the legacy "homophily" result.
*Figure: `plots/gender/homofilija_zirij.png`*

### 3. Former jurors win more often than their peers, but only a little, and mostly at three awards
**187** winners had sat on the same award's jury before winning it. Comparable
peers (winners of other awards in the same field and year) would give **152**:
a premium of **1.23×** (p < 0.001), and 1.24× when peers are also age-matched.
Per award, after correcting for testing about 70 awards:
- **Desetnica**: 9 of its 25 winners had previously sat on its jury, against
  about 1–2 expected. This is the clearest case, and it survives age matching.
- **Nagrada Franceta Štiglica**: 10 against 3.5 expected. Weaker with age
  matching.
- **Prešernova nagrada**: 27 against 12 expected, but with age-matched peers
  it is 23 against 17.6, which is not significant. Most of the apparent
  premium is seniority: the people who sit on the Prešeren jury are the same
  generation that receives the lifetime award.

The legacy list of "insider" awards (Stritarjeva, Mira, Jenkova…) does not
survive a proper null.
*Figure: `plots/juries/nekdanji_ziranti_med_nagrajenci.png`*

### 4. "I award you, you award me" happens no more than chance
There are **117** pairs of people who each sat on a jury that awarded the
other. Random reshuffling of winners within the same field and year produces
**103** on average (p = 0.07). In a scene this small, mutual awarding is
largely unavoidable.
*Figure: `plots/juries/vzajemno_nagrajevanje.png`*

### 5. Women laureates are recruited to juries faster than men
Of people first awarded in 2000 or later, **19%** of women and **14%** of men
sat on a jury within ten years. Within the same field, women's rate is
**1.4×** that of men (Cox HR 1.38, 95% CI 1.09–1.75, p = 0.007). This is part
of why juries became majority-female before winner lists did.

The reverse path is rarer. Of 1,053 people first seated on a jury in 2000 or
later with no earlier win, **12%** of men and **16%** of women won an award
within ten years. Within the same field, the difference is not significant
(Cox HR 1.11, 95% CI 0.79–1.57, p = 0.54). Of the 142 who did win, **30%** won
first at an award whose jury they had sat on. Whether that is more than chance
is the insider question of §3.
*Figures: `plots/careers/nagrajenec_postane_ziranti.png`, `ziranti_postanejo_nagrajenci.png`*

### 6. Winners are getting older at the same award
Within the same award, the age at win rises **1.4 years per decade** (95% CI
0.6–2.1). Wikidata/VIAF ages alone give +4.3. The raw trend (+0.6, not
significant) understates this, because younger-skewing awards joined the data
over time. Juries have stayed at a median of about 50, so the jury–winner age
gap has shrunk from 6–10 years in 2000–2014 to 2–3 years now. That pooled gap
mixes awards, though. Within the same edition, the jury is on average only
**0.7 years** older than its winners (older in 54% of 1,188 editions with
sourced ages). Within the same award, that gap has not changed (−0.1 years per
decade, p = 0.76).
*Figures: `plots/age/trend_starosti.png`, `plots/age/starost_zirij_in_nagrajencev.png`*

### 7. Women win about three years younger than men at the same award
Within the same award and decade, women are **2.9 years** younger at their win
(95% CI 2.0–3.7). The raw medians are 43 and 46.

### 8. The Prešeren two-step takes two decades
**Two thirds** of Prešernova nagrada winners (since the sklad prizes began)
had first won a nagrada Prešernovega sklada. The median gap is **21 years**.
Going the other way, only about **15%** of sklad laureates reach the
Prešernova nagrada within 30 years.
*Figure: `plots/careers/presernov_sklad_do_nagrade.png`*

### 9. Juries rotate more than they used to, but a small group holds a large share of seats
The share of jury seats held by someone who sat on the same jury in the
previous three years fell from **74%** in the 1990s to **51%** in the 2020s.
At the same time, the busiest 10% of jurors in each period hold about **30%**
of seats, against about 20% in the 1970s–80s. **15%** of seats since 2010 go to
people who sit on at least one other jury that year; Mojca Pišek (2017) and
Matej Bogataj (2021) each sat on five.

The most active juror is **Andrej Blatnik**: 51 sittings across 7 awards,
1984–2026. Several of the most active jurors have no award in the data,
including Tone Peršak (45), Ignacija J. Fridl (34), Vesna Kondrič Horvat (34)
and Petra Vidali (28).
*Figures: `plots/power/`*

### 10. (Dropped) Commissioners on their own juries
This section relied on the commission member lists, which were dropped as
unreliable on 2026-11-01 (see `docs/methods.md`, "Commission data dropped").
The number is kept so later sections keep their references.

### 11. Nine in ten have a Ljubljana tie, but the awards do not add to the capital's pull
Since 2000, **91%** of winners and **90%** of jurors with a placeable Slovenian
tie have Ljubljana among their ties (birthplace, schooling or work; not
residence). Per head of population, Ljubljana has **4.2×** its share of winners
(95% CI 4.1–4.3). No region reaches parity: the best are Goriška (0.72×) and
Koroška (0.69×), and the central region outside Ljubljana is lowest (0.21×).
The share has stayed near 90% since the 1950s, and within the same award it
has not moved (+0.1 pp per decade, 95% CI −0.4 to +0.6).

The awards' own mechanics do not seem to add to this concentration:
- **Juries are no more Ljubljana-bound than the people they award.** Within the
  same edition, the difference is −0.1 pp (95% CI −2.3 to +2.0; 1,203 editions).
- **Juries from outside Ljubljana do not pick winners from outside Ljubljana.**
  The naive slope is +0.21; within the same award and decade it is −0.06
  (permutation p = 0.48; 1,596 winners, 35 awards).

So the concentration is a property of the cultural field, which trains and
works in Ljubljana (the national academies, theatres and publishers are
there), not something the juries add. The population comparison measures that
field, not jury bias.

Compared with winners of other awards in the same field and year:
- **More Ljubljana-bound** (q < 0.05): Borštnikovo srečanje (98% vs 91%
  expected, although it is held in Maribor), Prešernov sklad (94% vs 91%) and
  Vesna (96% vs 92%). Župančičeva nagrada (99%) is Ljubljana's municipal award,
  so that result is expected.
- **Less Ljubljana-bound**: the municipal awards of other towns (Bernekerjeva,
  Glazerjeva, Trdinova), MMS (Piran; 54% vs 70%), Gala ZIZ and the Grossmann
  festival awards in Ljutomer.
- **Home advantage of awards held outside Ljubljana.** Among national awards,
  only Tantadruj (Nova Gorica) clearly favours its own region: 57% of its
  winners have a Goriška tie, against 23% for peers (2.5×, q = 0.002). The
  Ljutomer festival awards show the same pattern on very few winners. The
  Borštnik, Kranj (Grumova, Šeligova) and Celje awards show no home
  advantage. The municipal awards, as their rules require, do (2.5–5.5×);
  they confirm that the method detects a real home bias.

**The path into juries is the exception.** Of people first awarded in 2000 or
later (who had not judged before), 19% of those with a Ljubljana tie sat on a
jury within 10 years, against 10% of those without one (Kaplan–Meier). Within
the same field and richness stratum, the Ljubljana-tied reach a jury **1.8×**
as fast (Cox, 95% CI 1.2–2.8); 1.7× within the same first award (CI 1.0–2.8)
and 1.7× without the municipal awards (CI 1.1–2.7). Only 212 people are in the
outside group, so the size is uncertain, but the direction holds in every check.

**Caveat.** The places come from LLM enrichment and list ties, not residence.
How detailed a biography is changes the strict measures. Of winners with a
single recorded tie, 85% have Ljubljana as that tie; anyone with two or more
ties is by definition not "Ljubljana only". Every comparison is therefore made
within strata of the number of ties.
*Figures: `plots/geography/zastopanost_regij.png`, `zemljevid_zastopanosti.png`,
`ljubljana_skozi_cas.png`, `nagrade_proti_podrocju.png`, `domaca_prednost.png`,
`regionalna_homofilija.png`, `pot_v_zirijo.png`*

### 12. Juries are reappointed in the same line-up, but there are no groups moving between awards
**2,551** pairs of people sat together on at least three juries. If juries in
the same field and 5-year period were assembled at random (each person keeping
their number of sittings), there would be about **795** (3.2×). Even when people
are only reshuffled among the juries of the *same* award, it is still **1.36×**
(p = 0.003). Awards tend to reappoint the same jury: the top pairs are the
Vilenica jury (Peršak, Taufer, Kondrič Horvat and Blatnik sat together 31–34
times).

There is no sign of groups that move between awards together. **243** pairs
sat together on the juries of two or more different awards. Given each
person's own award memberships, chance gives **246** (p = 0.66); for three or
more awards it is 10 against 12. The pairs that travel the most are members of
the DSR board, which our sources list as the jury of several DSR film awards.
That is one body, not a faction.

Communities in the co-jury network (Louvain, modularity 0.75) follow the
fields: on average 66% of a community's members share one main field. The
communities are more distinct than random juries of the same field and period
would produce (0.65), because of the reappointed line-ups above.

**Brokers.** Andrej Blatnik and Ignacija J. Fridl are the most central jurors
(the most shortest paths between other jurors run through them). Fridl,
Aleš Šteger, Miha Hočevar and Varja Močnik are much more central than random
juries that keep their fields and number of sittings would make them. For
Blatnik, Bogataj and Zgonik, centrality is about what their spread across
fields predicts.
*Figures: `plots/network/ponavljajoce_dvojice.png`, `skupnosti_in_podrocja.png`,
`povezovalci.png`*

### 13. Independence did not interrupt careers in the award field
The legacy analysis reported that only 27% of pre-1991 winners won again after
1991. On its own, that number cannot be read: careers end anyway, and few awards
are recorded on both sides of 1991. Applying the same measure at placebo breaks
gives a baseline. For each break, it takes people active in the 10 years
before it (only awards recorded on both sides) and counts how many were active
again in the next 10.
- **Winners:** 29% continued across 1991, against 30% across 1971 and 25%
  across 1981. Later breaks are higher (40–42%), but they also have more
  recorded awards to reappear in.
- **Within the same award**, continuation across 1991 does not differ from any
  placebo break (differences between −0.4 and +4.6 points, all p > 0.2;
  32 awards).
- **Jurors:** 43% continued across 1991, against 45–62% at the other breaks.
  The intervals overlap (n = 86).

The share of new faces among each year's winners and jurors fell steadily from
the 1970s to the late 1980s. It dipped in the early 1990s and rose again in
the late 1990s, as new awards entered the data.
*Figures: `plots/transition/nadaljevanje_karier.png`, `novi_obrazi.png`*

### 14. New juries do not favour newcomers
Within the same award and decade, an entirely new jury (no member on that
award's jury in the previous 3 years) is +4 points more likely than an
unchanged one to pick a first-time winner. This is not significant
(permutation p = 0.17; 1,716 winners since 2005, 66 awards). The legacy
correlation did not compare like with like. (The commission-tier results that
used to open this section were dropped with the commission data.)
*Figure: `plots/pipeline/nove_zirije_novi_obrazi.png`*

### 15. Dossier: Ignacija J. Fridl (Minister of Culture)
Fridl has **34 jury sittings on 9 awards** (1997–2019) and no awards won.
Among the 129 people with at least 10 sittings, Fridl ranks 5th by sittings and
by voting power, 2nd by distinct awards, and 1st or 2nd by network centrality
(sampled betweenness; Fridl and Andrej Blatnik swap places between runs). Fridl's largest shares of an award's
jury power are at Fabula (9%, first of 21 jurors) and Rožančeva nagrada (9%,
second of 27). Winners picked by Fridl's panels did not go on to juries more
often than other winners of the same awards and years (24% vs 18%; the
intervals overlap). They were not picked differently by gender either (28% vs
35% women, p = 0.24). The full dossier, with co-juror ties relevant to office,
is in `docs/dossier-ignacija-j-fridl.md`.

### 16. Jury seats are more concentrated than awards, and there is no visible "climb" to the top awards
Since 2000, the busiest 10% of jurors hold **40%** of jury seats (Gini 0.50).
The most-awarded 10% of winners hold **30%** of wins (Gini 0.30), and **72%**
of winners won only once. Recognition is spread more widely than the power to
grant it.

The legacy "climb" (years of lesser awards and jury work before the crown)
does not show in the data. Of people whose first prestige-5 award came in 2005
or later, only **20%** had any earlier award in the data and **10%** an earlier
jury seat. That is no more than for a first tier-4 award (18%, 14%) or a first
tier-3 award (31%, 21%). Within the same field and year, the crowned are
**less** likely than tier-3 winners to have judged before (−12 points,
p = 0.003). The crown does not change what follows either: about 22% sit on a
jury and 34% win again within 10 years, the same as after a tier-4 award. A
caveat is that lesser awards in some fields are missing from the data, so part
of the "no record" group did have a record we cannot see.
*Figures: `plots/crown/koncentracija.png`, `pred_kronanjem.png`, `po_kronanju.png`*

### 17. Fields stay separate; long careers are made on juries, not on winner lists
Since 2000, only **13%** of winners have awards in more than one field. If wins
were spread at random (keeping each field's wins and each person's number of
wins), it would be 26%. Literature and poetry share winners at **2.2×**
chance, and poetry and the umbrella awards (Prešeren, Župančič, Ježek) at
1.7×. Every other pair of fields shares fewer than chance. Film and theatre,
for example, share 52 winners against 100 expected.

The longest runs of consecutive years on juries come from standing juries:
**Tone Peršak, 41 years** (1986–2026, mostly Vilenica), Andrej Blatnik 36,
Vesna Kondrič Horvat 34. The longest run of consecutive years *winning* is 7
(Peter Musevski). 11% of jurors have a jury run of 5 years or more, but only 1%
of winners have a 3-year winning run. 4% of winner-years since 2000 include
two or more different awards. The maximum is four (Leo Černic, 2023, all film
awards for the same work).
**Juries mostly draw on their own field.** Since 2000, **65%** of seats on
field juries are held by people with no earlier field award in the data. Of the
rest, **19%** sit on a jury outside their home field (the field of most of
their earlier wins; poetry counted as literature; umbrella juries excluded).
Journalism juries are the exception: 58% of their awarded jurors come from
elsewhere, mostly writers (45%). Literature juries draw 10% from outside and
architecture juries none. Within the same award, the outside share is
*falling*, by 7 points per decade (95% CI −13 to −1, p = 0.015).
*Figures: `plots/mobility/prehajanje_podrocij.png`, `nizi_v_zirijah.png`,
`ziranti_iz_drugih_podrocij.png`*

### 18. The Prešernova nagrada often comes near the end of a life
Of Prešernova nagrada laureates since 1970, **20%** died within 5 years of the
award and **37%** within 10 (Kaplan–Meier; median age at the award 65). The
figures are 15% within 5 years for Meškova nagrada and 11% for Badjurova. For
most awards they are under 5%. These are lower bounds: a death year missing
from the enrichment counts as alive.
*Figure: `plots/age/pozne_nagrade.png`*

### 19. Overview: who wins and who judges most often
The data holds **4,993 wins by 2,868 people** (plus 157 groups, institutions and
works) and **6,080 jury seats held by 1,751 people**, counted in sittings.
**68%** of winners won once, while only **40%** of jurors sat once (median 2
sittings). **716 people** have done both: a quarter of winners and two fifths of
jurors.

- **Most wins:** Dušan Jovanović (20 wins at 10 awards, 1979–2009), then Boris
  Cavazza and Vinko Möderndorfer (14 each), Janez Burger and Damijan Stepančič
  (13), and Svetlana Makarovič, Drago Jančar, Zvonko Čoh and Jernej Lorenci (12).
  Theatre, film and children's illustration dominate, because those awards give many
  prizes a year.
- **Most jury sittings:** Andrej Blatnik (51), Veno Taufer (47), Tone Peršak
  (45), Matej Bogataj (42), and Ignacija J. Fridl and Vesna Kondrič Horvat
  (34 each). Of these, only Taufer has more than two wins of their own.
- **By decade**, the leading winner went from France Mihelič and Marlenka
  Stupica (4 in the 1950s) to Dušan Jovanović (7 in both the 1980s and 1990s),
  Peter Musevski (8 in the 2000s), Vinko Möderndorfer (10 in the 2010s) and
  Damijan Stepančič (7 so far in the 2020s). The leading juror went from Samo
  Hubad (1950s) to Andrej Blatnik (1980s, 1990s with Taufer, 2010s), Ignacija
  J. Fridl (21 in the 2000s) and Matej Bogataj (17 so far in the 2020s).
- **By year:** nobody has won more than four times in one year (Leo Černic,
  2023, all for the same film). In most years since 2000 the top winner has two
  wins, often shared with several others. The year's busiest juror usually has
  3 sittings; Mojca Pišek (2017) and Matej Bogataj (2021) had five.
- **Widest awards:** Prešernov sklad (608 different winners), Plečnikova
  nagrada (227), Vesna (226) and the Prešernova nagrada (220).

These are raw counts. Coverage grows after 2000, so all-time lists favour
recent careers and awards with many prizes a year. The full tables (top 25,
every year, every decade) are in `results/overview.json`.
*Figures: `plots/overview/najpogostejsi_nagrajenci.png`, `vodilni_po_letih.png`;
the top-jurors chart is `plots/power/najbolj_zasedeni_ziranti.png`*

### 20. No juror's panels "produce" future jurors, and juries of one award rarely lead to another
**Kingmakers.** For each of the 64 jurors with at least 10 sittings, the
winners their panels picked (wins up to 2016, people with no earlier seat) were
compared with winners of the same award within ±5 years whom they did not pick.
Across the 2,793 panel winners, **397** sat on a jury within ten years, against
**384** expected. **No juror** differs from expectation after correcting for 64
tests. The largest deviations are Milček Komelj (15 against 8.0, p = 0.02) and
Alenka Bole Vrabec (1 against 6.7, p = 0.01); neither survives correction
(q = 0.50). Ignacija J. Fridl: 13 against 9.6 (p = 0.30). The legacy
"kingmaker" ranking had no comparison group and so mostly ranked jurors by
how many winners they had picked.

**From one award's jury to another award.** Extending §3 to pairs of awards:
of 2,375 award pairs, **4** show more winners who earlier sat on the other
award's jury than peers of the same field and year would. All are small and
within one field: Borštnikov prstan jury → Bert (5 against 0.4), Kritiško sito
→ Stritarjeva nagrada (6 against 0.6), Grumova nagrada → Nagrada Vladimirja
Kralja (4 against 0.3) and Zlata ptica → Rožančeva nagrada (3 against 0.1).
Jury seats are counted in sittings, and wins by someone who had also sat on the
winning award's own jury are left to §3.
*Figures: `plots/influence/kraljevi_ustvarjalci.png`, `iz_zirije_v_drugo_nagrado.png`*

### 21. Many awards come back to their own past winners; awards do not share juror pools
**Repeat winners.** Among the winners of the same field and year, people who
had already won an award win it again more often than chance: **565** repeat
wins against **451** expected (1.25×, p < 0.001). This holds at **19 awards**
after correction. The strongest are the Grumova nagrada (24 against 3), Kresnik
(10 against 1), Desetnica (7 against 1), Dnevnikova nagrada (10 against 2),
Levstikova nagrada (59 against 25) and Borštnikovo srečanje (59 against 28).
The **Prešernov sklad** is the opposite: it almost never goes to a past
laureate (12 against 110 expected). Its laureates go on to the Prešernova
nagrada instead (§8).

**Shared juror pools.** 595 award pairs share at least one juror, but **none**
shares more than random juries of the same field and period would (after
correction). In total, 1,413 people sat on the juries of two awards, against
8,165 under random juries: jurors stay with one award. The strongest
candidates are small film-award pairs (butnskala and najsvetlejša zvezda
Oriona; the film critics' award and Nagrada Nike Bohinc) and Bert and Kosobrin,
whose juries are both the DSR board: one body, not a network.

**Older awards do not keep more stable juries.** Since 1990, 62% of jury seats
at awards younger than 10 years are repeat seats, against 55–57% at older
awards. Compared within the same period, the difference is −0.6 points per
10 years of award age (p = 0.58).
*Figures: `plots/awards/ponovni_nagrajenci_po_nagradah.png`, `skupni_ziranti_nagrad.png`,
`stabilnost_zirij_in_starost_nagrade.png`*

### 22. Ties to former Yugoslavia thinned out steadily, not at independence
Among winners with any recorded place, 36% of those awarded in the 1950s had a
tie (birth, schooling or work) elsewhere in former Yugoslavia, against 10% in
the 2020s. Older biographies list more places, so the raw drop overstates the
change. Within the same award and at the same number of listed places, the
share falls by **2.2 pp per decade** (95% CI 1.5–2.9). On top of that trend
there is no extra drop at 1991 (−3.9 pp, CI −11 to +3), nor at the placebo
breaks 1981 and 2001. Ties to the rest of the world (Trieste, Vienna, Paris,
Berlin, New York) stay at about a third of winners; within award the trend is
+1.1 pp per decade (CI −0.5 to +2.8), so no clear change.

The legacy plot read the before/after-1991 comparison as a shift "from the
Yugoslav axis to the west". The decline is generational and predates 1991; the
western share did not grow.
*Figure: `plots/geography/vezi_s_tujino.png`*

## Smaller results
- **Prestige and gender.** Since 2010, women won 37% of top-prestige awards,
  against 44–46% of tier 3–4 awards. The gap is not significant once
  clustering by award is accounted for (−3 pp after cohort and field controls,
  p = 0.23).
- **Youngest and oldest awards.** By median winner age, the youngest are the
  Nagrada za najboljši literarni prvenec (29), Nagrada skupine OHO (31) and
  Zlata ptica (31). The oldest are Bert (78), Zlatnik poezije (73.5) and
  Odličje Marije Vere (68).
- **Winning again.** A first win at a tier-4 award is followed by another win
  within 10 years for 34% of people. The figures are 29% for tier 5 and 18%
  for tiers 2–3.
- **Juror and winner in the same edition.** This happens in 11 cases (Vesna
  1999 and 2015, Desetnica 2009, Zlata strela 2026 and others; for Zlata strela
  2026 both aplavz.art reports name Nataša Živković as juror and laureate). These need verifying: they may be
  data errors, or a juror's work winning a different category.

## Corrections to legacy numbers
- **Jury seats were overcounted by 20%.** Shared juries (Prešeren, ZDUS, DSKP)
  were counted once per prize. The legacy figure of "35 seats across 10
  awards" for I. J. Fridl is 34 sittings across 9 awards.
- **Network-based "significance" results were significant by construction.**
  This applied to insider awards, rich-club, and homophily without controls.
  The rebuilt tests above replace them. The legacy null swapped edges of the
  one-mode projection, which breaks the cliques every jury creates. The
  rebuilt null shuffles people between juries instead.
- **"Ljubljana ×4.4"** (legacy) is ×4.2 after the reviews and place fixes. It
  measures the cultural field, not the juries (see §11).
