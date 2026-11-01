# Review: duplicate award-year rows

45 groups, 90 rows.

**Status 2026-11-01: applied** by `scripts/apply_edition_decisions.py` (log in
`data/meta/edition_decisions.csv`). Still open:
- NFKP 2024 and Trubarjevo 2025: kept as separate editions, categories unknown.
- Zlata ptica: **relabelled to the ceremony year (+1 for the whole series)**,
  2026-11-01. Every dated source has the ceremony in the spring after the year
  the awards are for: "prvič podeljena za leto 1975" (dobreknjige.si); Svetina's
  first award (our 1975) presented in 1976 (Delo); 2004 → 14. 4. 2005,
  2007 → May 2008 ("za leto 2007"), 2008 → 7. 5. 2009, 2009 → 10. 5. 2010,
  2011 → May 2012 (rtvslo); 2012 → 5. 6. 2013 (STA). The series now runs
  1976–2015; the last edition (Kolektivni projekt Zombie) is unverified. The
  pre-2000 editions list one winner a year and are certainly incomplete
  (Jožica Avbelj's 1979 award, for example, is missing).
- Editions with no winners: filled Grumova 1986, Lastovka 2018 (jury corrected),
  Kosobrin 2026 (unverified AI overview), Brenkova 2025, Najboljši esej 2026.
  Grumova 1997 kept as not awarded (the jury sat). Dropped as not held/awarded:
  Majski salon 2024, Slodnjak 2022, Trdinova 1990. **Left: Bernekerjeva 1996,
  Bert 2020, Bibič 2016** (a search claimed Bibič did not exist in 2016; our data
  has it from 2007, so that answer was rejected).

The legacy CSV has more than one row for these (award, year) pairs. The migration
kept every row as its own edition (`-2`, `-3` suffixes). For each group, decide:

- **keep**: they are real separate editions or categories (add `category` if known)
- **merge**: the same edition split across rows (combine the winners, dedupe the jury)
- **move**: a row belongs to a different year (give the correct year)
- **drop**: an erroneous duplicate

Lines refer to `data/zirije_plus_nagrajenci.csv` in the legacy project.

## Aškerčevo priznanje 2018  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `askercevo-priznanje-2018` | 1549 | Marija Čipić Rehar | Andrej Nared, Elizabeta Eržen Podlipnik, Ivan Fras, Aleksandra Pavšič Milost, Katja Zupanič |
| `askercevo-priznanje-2018-2` | 1550 | Dejan Zadravec | Andrej Nared, Elizabeta Eržen Podlipnik, Ivan Fras, Aleksandra Pavšič Milost, Katja Zupanič |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Aškerčevo priznanje 2022  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `askercevo-priznanje-2022` | 1544 | Danijela Juričić Čargo, Lilijana Žnidaršič Golec | Andrej Nared, Julijana Visočnik, Elizabeta Eržen Podlipnik, Mirjana Kontestabile Rovis, Aleksander Žižek |
| `askercevo-priznanje-2022-2` | 1545 | Mojca Horvat | Andrej Nared, Julijana Visočnik, Elizabeta Eržen Podlipnik, Mirjana Kontestabile Rovis, Aleksander Žižek |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Aškerčevo priznanje 2024  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `askercevo-priznanje-2024` | 1541 | Tadej Cankar, Mateja Jeraj, Matevž Košir, Tadeja Tominšek Čehulić, Polona Trobec Mlakar, Mojca Tušar, Tanja Žohar | Andrej Nared, Julijana Visočnik, Elizabeta Eržen Podlipnik, Mirjana Kontestabile Rovis, Aleksander Žižek |
| `askercevo-priznanje-2024-2` | 1542 | Bojan Himmelreich | Andrej Nared, Julijana Visočnik, Elizabeta Eržen Podlipnik, Mirjana Kontestabile Rovis, Aleksander Žižek |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Borštnikovo srečanje 2012  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `borstnikovo-srecanje-2012` | 213 | MGL, Jernej Lorenci, Nataša Barbara Gračner, Gregor Baković, Primož Pirnat, Matej Puc, Nika Rozman, Branko Hojnik, Branko Rožman, Belinda Radulović, Maja Cerar | Mark Brown, Jaša Drnovšek, Meta Hočevar, Arthur Sonnen, Zala Dobovšek |
| `borstnikovo-srecanje-2012-2` | 265 | Jernej Lorenci | Mark Brown, Zala Dobovšek, Jaša Drnovšek, Meta Hočevar, Arthur Sonnen |

Decision: **drop** `borstnikovo-srecanje-2012-2` [sure]: Lorenci is already in the full list.

## Desetnica 2025  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `desetnica-2025` | 337 | Andrej E. Skubic | Ivo Frbežar, Petra Kolmančič, Tone Peršak, Tomo Podstenšek, Robert Titan Felix |
| `desetnica-2025-2` | 338 | Mateja Gomboc | Marjana Moškrič, Tone Peršak, Tomo Podstenšek, Veronika Simoniti, Robert Titan Felix |

Decision: **move** `desetnica-2025-2` → `desetnica-2026` [sure]: confirmed by web search. 2025 = Andrej E. Skubic; 2026 = Mateja Gomboc (*Preveč zvezd*), jury Moškrič, Peršak, Podstenšek, Simoniti, Titan Felix.

## Gibanica 2013  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `gibanica-2013` | 1568 | Maja Delak | Zala Dobovšek, Iva Nerina Sibila, Anita Mathieu |
| `gibanica-2013-2` | 1569 | Mala Kline | Zala Dobovšek, Iva Nerina Sibila, Anita Mathieu |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Gibanica 2023  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `gibanica-2023` | 1563 | Irena Tomažin, Jule Flierl | Roberto Casarotto, Dries Douibi, Lea Loeb |
| `gibanica-2023-2` | 1564 | Beno Novak, Elvis Homan, Boštjan Simon | Roberto Casarotto, Dries Douibi, Lea Loeb |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Grumova nagrada 2014  (same jury, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `grumova-nagrada-2014` | 751 | Vinko Möderndorfer | Mateja Pezdirc Bartol, Tomaž Gubenšek, Vilma Štritof Čretnik, Klavdija Zupan, Igor Žunkovič |
| `grumova-nagrada-2014-2` | 755 | Vinko Möderndorfer | Mateja Pezdirc Bartol, Tomaž Gubenšek, Vilma Štritof Čretnik, Klavdija Zupan, Igor Žunkovič |

Decision: **drop** `grumova-nagrada-2014-2` [sure]: exact duplicate.

## Jenkova nagrada 2002  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2002` | 470 | Erika Vouk | — |
| `jenkova-nagrada-2002-2` | 488 | Erika Vouk | Dane Zajc, Milan Jesih, Vida Mokrin Pauer, Lidija Gačnik Gombač |

Decision: **merge** into `jenkova-nagrada-2002` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2003  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2003` | 471 | Brane Mozetič | — |
| `jenkova-nagrada-2003-2` | 487 | Brane Mozetič | Lidija Gačnik Gombač, Dane Zajc, Tone Peršak, Vida Mokrin Pauer |

Decision: **merge** into `jenkova-nagrada-2003` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2005  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2005` | 473 | Maja Vidmar | — |
| `jenkova-nagrada-2005-2` | 486 | Maja Vidmar | Lucija Stupica, Ciril Bergles, Matevž Kos, Marko Kravos |

Decision: **merge** into `jenkova-nagrada-2005` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2006  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2006` | 474 | Josip Osti, Miklavž Komelj | — |
| `jenkova-nagrada-2006-2` | 485 | Josip Osti | Majda Kne, Alojz Ihan, Lucija Stupica, Milan Jesih |

Decision: **merge** into `jenkova-nagrada-2006` [sure]: joint winners Josip Osti + Miklavž Komelj (confirmed by web search); take the jury from the `-2` row (Kne, Ihan, Stupica, Jesih), drop `-2`. The AI-overview search gave a different jury (Samo Rugelj, Iztok Osojnik, Peter Kuhar), which we do not trust; verify against a primary source before publishing.

## Jenkova nagrada 2007  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2007` | 475 | Tomaž Šalamun | — |
| `jenkova-nagrada-2007-2` | 484 | Tomaž Šalamun | Niko Grafenauer, Andrej Inkret, Matevž Kos, Milan Jesih, Miklavž Komelj |

Decision: **merge** into `jenkova-nagrada-2007` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2008  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2008` | 476 | Andrej Medved | — |
| `jenkova-nagrada-2008-2` | 483 | Andrej Medved | Niko Grafenauer, Andrej Inkret, Tomaž Šalamun, Aleš Šteger, Tomaž Toporišič |

Decision: **merge** into `jenkova-nagrada-2008` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2009  (different juries, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2009` | 477 | Aleš Debeljak | Niko Grafenauer |
| `jenkova-nagrada-2009-2` | 482 | Aleš Debeljak | Niko Grafenauer, Andrej Medved, Ifigenija Simonović, Aleš Šteger, Tomaž Toporišič |

Decision: **merge** into `jenkova-nagrada-2009` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jenkova nagrada 2010  (same jury, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jenkova-nagrada-2010` | 478 | Ivo Svetina | Niko Grafenauer, Aleš Debeljak, Andrej Medved, Ifigenija Simonović, Tomaž Toporišič |
| `jenkova-nagrada-2010-2` | 481 | Ivo Svetina | Niko Grafenauer, Aleš Debeljak, Andrej Medved, Ifigenija Simonović, Tomaž Toporišič |

Decision: **merge** into `jenkova-nagrada-2010` [sure]: same winner; take the jury from the `-2` row, drop `-2`.

## Jurčičeva nagrada 2012  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `jurciceva-nagrada-2012` | 193 | Darja Korez Korenčan, Matevž Tomšič, Ivan Štuhec | Janez Bernik, Drago Demšar, Niko Grafenauer, Drago Jančar, Janko Kos, Lojze Lebič, Primož Simoniti, Jože Snoj, Janez Pogačnik, Aleksander Zorn, Barbara Šubert, Veno Taufer, Evald Flisar, Barbara Korun, Vlado Žabot, Marjan Strojan, Jani Virk, Feri Lainšček, Igor Grdina, Peter Lah, Aleš Maver, Jožef Muhovič, Alenka Puhar, Brane Senegačnik |
| `jurciceva-nagrada-2012-2` | 194 | Vinko Vasle, Uroš Urbanija, Marko Crnkovič, Peter Rak | Janez Bernik, Drago Demšar, Niko Grafenauer, Drago Jančar, Janko Kos, Lojze Lebič, Primož Simoniti, Jože Snoj, Janez Pogačnik, Aleksander Zorn, Barbara Šubert, Veno Taufer, Evald Flisar, Barbara Korun, Vlado Žabot, Marjan Strojan, Jani Virk, Feri Lainšček, Igor Grdina, Peter Lah, Aleš Maver, Jožef Muhovič, Alenka Puhar, Brane Senegačnik |

Decision: **merge** [sure]: same jury, several winners in one year; combine winners, drop `-2`.

## Kresnik 2025  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `kresnik-2025` | 169 | Ana Schnabl | Igor Bratož, Seta Knop, Kristina Kočan, Tanja Petrič, Peter Svetina |
| `kresnik-2025-2` | 170 | Ajda Bračič | Igor Bratož, Kristina Kočan, Tanja Petrič, Seta Knop, Igor Žunkovič |

Decision: **swap juries + move** [sure]: confirmed by web search. `kresnik-2025` = Ana Schnabl + jury Bratož, Knop, Kočan, Petrič, Žunkovič. `kresnik-2026` = Ajda Bračič (*Kresničevje*) + jury Bratož, Knop, Kočan, Petrič, Svetina (Nina Gostiša was secretary, not a juror).

## Nagrada filmskih kritikov in publicistov 2024  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `nagrada-filmskih-kritikov-in-publicistov-2024` | 794 | Maja Doroteja Prelog | Maša Peče, Varja Močnik, Kristian Božak Kavčič |
| `nagrada-filmskih-kritikov-in-publicistov-2024-2` | 795 | Aleksandra Gačić, Zigi Omerzel, Ciril Oberstar | Polona Petek, Varja Močnik, Gaja Pöschl |

Decision: **keep** [check]: row 1 (Prelog, *Cent'anni*) = FIPRESCI award of the Društvo slovenskih filmskih publicistov at Festival slovenskega filma. Row 2 (Gačić, Omerzel, Oberstar; different jury) is probably the critics' award for film criticism: Gačić was nominated for criticism in 2024. Not confirmed; Omerzel and Oberstar not found. Source to check: dsfp.si, or the FSF 2024 award list.

## Sovretova nagrada 2002  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `sovretova-nagrada-2002` | 534 | Jaroslav Novak | Janko Moder, Jože Stabej, Branko Madžarevič, Niko Jež, Marko Marinčič |
| `sovretova-nagrada-2002-2` | 550 | Jaro Novak | — |

Decision: **merge** into `sovretova-nagrada-2002` [sure]: Jaro Novak = Jaroslav Novak (add alias); drop `-2`.

## Trubarjevo priznanje 2025  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `trubarjevo-priznanje-2025` | 1017 | Slovenski narodopisni inštitut Urban Jarnik, Matija Ogrin, Andrejka Žejn | Marijan Rupert, Urša Kocjan, Lucija Planinc |
| `trubarjevo-priznanje-2025-2` | 1018 | Kamra, Center za konserviranje in restavriranje | Urša Kocjan, Luka Vidmar, Urška Perenič |

Decision: **keep** [check]: no 2025 recipients found online. The NUK announces the Trubarjeva priznanja every year (gov.si news / nuk.uni-lj.si, late in the year). Two different commissions point to two years rather than two categories: possibly the 2024 and 2025 calls, or 2025 and 2026.

## Večernica 2002  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2002` | 395 | Marjana Moškrič | Slavko Pregl, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2002-2` | 1035 | Matjaž Pikalo | Igor Saksida, Marjana Kobe, Darja Lavrenčič Vrabec, Slavko Pregl, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2002-2` [sure]: duplicate of `vecernica-2001`, shifted one year (legacy block 1035–1057).

## Večernica 2003  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2003` | 396 | Slavko Pregl | Tone Partljič, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2003-2` | 1036 | Marjana Moškrič | Tone Partljič, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |

Decision: **drop** `vecernica-2003-2` [sure]: duplicate of `vecernica-2002`, shifted one year (legacy block 1035–1057). Jury of `vecernica-2003` confirmed by web search.

## Večernica 2004  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2004` | 397 | Igor Karlovšek | Tone Partljič, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2004-2` | 1037 | Slavko Pregl | Tone Partljič, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |

Decision: **drop** `vecernica-2004-2` [sure]: duplicate of `vecernica-2003`, shifted one year (legacy block 1035–1057).

## Večernica 2005  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2005` | 398 | Dušan Dim | Tone Partljič, Vida Medved Udovič, Ida Mlakar, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2005-2` | 1038 | Igor Karlovšek | Tone Partljič, Marjana Kobe, Darja Lavrenčič Vrabec, Darka Tancer Kajnih, Petra Vidali |

Decision: **drop** `vecernica-2005-2` [sure]: duplicate of `vecernica-2004`, shifted one year (legacy block 1035–1057).

## Večernica 2006  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2006` | 399 | Irena Velikonja, Majda Koren | Tone Partljič, Vida Medved Udovič, Ida Mlakar, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2006-2` | 1039 | Dušan Dim | Tone Partljič, Ida Mlakar, Darka Tancer Kajnih, Vida Medved Udovič, Petra Vidali |

Decision: **drop** `vecernica-2006-2` [sure]: duplicate of `vecernica-2005`, shifted one year (legacy block 1035–1057).

## Večernica 2007  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2007` | 400 | Ervin Fritz | Tone Partljič, Vida Medved Udovič, Ida Mlakar, Darka Tancer Kajnih, Petra Vidali |
| `vecernica-2007-2` | 1040 | Irena Velikonja, Majda Koren | Tone Partljič, Vida Medved Udovič, Ida Mlakar, Darka Tancer Kajnih, Petra Vidali |

Decision: **drop** `vecernica-2007-2` [sure]: duplicate of `vecernica-2006`, shifted one year (legacy block 1035–1057).

## Večernica 2008  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2008` | 401 | Janja Vidmar | Tone Partljič, Manca Perko, dr. Dragica Haramija, Ida Mlakar, Melita Forstnerič Hajnšek |
| `vecernica-2008-2` | 1041 | Ervin Fritz | Tone Partljič, Vida Medved Udovič, Ida Mlakar, Darka Tancer Kajnih, Petra Vidali |

Decision: **drop** `vecernica-2008-2` [sure]: duplicate of `vecernica-2007`, shifted one year (legacy block 1035–1057).

## Večernica 2009  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2009` | 402 | Bina Štampe žmavc | Vlado Žabot, dr. Dragica Haramija, Manca Perko, Ida Mlakar, Melita Forstnerič Hajnšek |
| `vecernica-2009-2` | 1042 | Janja Vidmar | Tone Partljič, Manca Perko, dr. Dragica Haramija, Ida Mlakar, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2009-2` [sure]: duplicate of `vecernica-2008`, shifted one year (legacy block 1035–1057).

## Večernica 2010  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2010` | 403 | Mate Dolenc | Vlado Žabot, dr. Dragica Haramija, Manca Perko, Ida Mlakar, Melita Forstnerič Hajnšek |
| `vecernica-2010-2` | 1043 | Bina Štampe žmavc | dr. Dragica Haramija, Darka Tancer Kajnih, Alenka Urh, Barbara Zorman, Klara Širovnik |

Decision: **drop** `vecernica-2010-2` [sure]: its winner duplicates 2009; its jury is unrelated. `vecernica-2010` jury confirmed by web search.

## Večernica 2011  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2011` | 404 | Dim Zupan | dr. Dragica Haramija, Aleš Debeljak, Kristina Picco, Manca Perko, Melita Forstnerič Hajnšek |
| `vecernica-2011-2` | 1044 | Mate Dolenc | Vlado Žabot, Ida Mlakar, Melita Forstnerič Hajnšek, Manca Perko, dr. Dragica Haramija |

Decision: **drop** `vecernica-2011-2` [sure]: duplicate of `vecernica-2010`, shifted one year (legacy block 1035–1057).

## Večernica 2012  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2012` | 405 | Peter Svetina | dr. Dragica Haramija, Aleš Debeljak, Kristina Picco, Maja Logar, Melita Forstnerič Hajnšek |
| `vecernica-2012-2` | 1045 | Dim Zupan | dr. Dragica Haramija, Aleš Debeljak, Kristina Picco, Manca Perko, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2012-2` [sure]: duplicate of `vecernica-2011`, shifted one year (legacy block 1035–1057).

## Večernica 2013  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2013` | 406 | Vinko Möderndorfer | dr. Dragica Haramija, Aleš Debeljak, Maja Logar, Kristina Picco, Melita Forstnerič Hajnšek |
| `vecernica-2013-2` | 1046 | Peter Svetina | dr. Dragica Haramija, Aleš Debeljak, Kristina Picco, Maja Logar, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2013-2` [sure]: duplicate of `vecernica-2012`, shifted one year (legacy block 1035–1057).

## Večernica 2014  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2014` | 407 | Vladimir P. Štefanec | Igor Saksida, Aleš Debeljak, Petra Vidali, Maja Logar, Tone Obadič |
| `vecernica-2014-2` | 1047 | Vinko Möderndorfer | dr. Dragica Haramija, Aleš Debeljak, Maja Logar, Kristina Picco, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2014-2` [sure]: duplicate of `vecernica-2013`, shifted one year (legacy block 1035–1057).

## Večernica 2015  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2015` | 408 | Peter Svetina | Igor Saksida, Erica Johnson Debeljak, Maja Logar, Petra Vidali, Tone Obadič |
| `vecernica-2015-2` | 1048 | Vladimir P. Štefanec | Igor Saksida, Aleš Debeljak, Petra Vidali, Maja Logar, Tone Obadič |

Decision: **drop** `vecernica-2015-2` [sure]: duplicate of `vecernica-2014`, shifted one year (legacy block 1035–1057).

## Večernica 2016  (same jury, identical winners (likely exact duplicate))

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2016` | 409 | Peter Svetina | Maja Logar, Erica Johnson Debeljak, Tone Obadič, Petra Vidali, Igor Saksida |
| `vecernica-2016-2` | 1049 | Peter Svetina | Igor Saksida, Erica Johnson Debeljak, Maja Logar, Petra Vidali, Tone Obadič |

Decision: **drop** `vecernica-2016-2` [sure]: exact duplicate.

## Večernica 2017  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2017` | 410 | Anja Štefan | Igor Saksida, dr. Dragica Haramija, Maja Logar, Petra Vidali, Kaja Bucik Vavpetič |
| `vecernica-2017-2` | 1050 | Peter Svetina | Maja Logar, Erica Johnson Debeljak, Tone Obadič, Petra Vidali, Igor Saksida |

Decision: **drop** `vecernica-2017-2` [sure]: duplicate of `vecernica-2016`, shifted one year (legacy block 1035–1057).

## Večernica 2018  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2018` | 411 | Andrej E. Skubic | Kaja Bucik Vavpetič, dr. Dragica Haramija, Darka Tancer Kajnih, Igor Saksida, Petra Vidali |
| `vecernica-2018-2` | 1051 | Anja Štefan | Igor Saksida, Maja Logar, Kaja Bucik Vavpetič, dr. Dragica Haramija, Petra Vidali |

Decision: **drop** `vecernica-2018-2` [sure]: duplicate of `vecernica-2017`, shifted one year (legacy block 1035–1057).

## Večernica 2019  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2019` | 412 | Andrej Rozman Roza | Igor Saksida, Darka Tancer Kajnih, Kaja Bucik Vavpetič, dr. Dragica Haramija, Petra Vidali |
| `vecernica-2019-2` | 1052 | Andrej E. Skubic | Kaja Bucik Vavpetič, dr. Dragica Haramija, Darka Tancer Kajnih, Igor Saksida, Petra Vidali |

Decision: **drop** `vecernica-2019-2` [sure]: duplicate of `vecernica-2018`, shifted one year (legacy block 1035–1057).

## Večernica 2020  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2020` | 413 | Sebastijan Pregelj | Melita Forstnerič Hajnšek, dr. Dragica Haramija, Darka Tancer Kajnih, Alenka Urh, Barbara Zorman |
| `vecernica-2020-2` | 1053 | Andrej Rozman Roza | Igor Saksida, Darka Tancer Kajnih, Kaja Bucik Vavpetič, dr. Dragica Haramija, Petra Vidali |

Decision: **drop** `vecernica-2020-2` [sure]: duplicate of `vecernica-2019`, shifted one year (legacy block 1035–1057).

## Večernica 2021  (same jury)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2021` | 414 | Maša Ogrizek | dr. Dragica Haramija, Barbara Zorman, Darka Tancer Kajnih, Alenka Urh, Melita Forstnerič Hajnšek |
| `vecernica-2021-2` | 1054 | Sebastijan Pregelj | Melita Forstnerič Hajnšek, dr. Dragica Haramija, Darka Tancer Kajnih, Alenka Urh, Barbara Zorman |

Decision: **drop** `vecernica-2021-2` [sure]: duplicate of `vecernica-2020`, shifted one year (legacy block 1035–1057).

## Večernica 2022  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2022` | 415 | Špela Frlic | dr. Dragica Haramija, Darka Tancer Kajnih, Alenka Urh, Barbara Zorman, Klara Širovnik |
| `vecernica-2022-2` | 1055 | Maša Ogrizek | dr. Dragica Haramija, Barbara Zorman, Darka Tancer Kajnih, Alenka Urh, Melita Forstnerič Hajnšek |

Decision: **drop** `vecernica-2022-2` [sure]: duplicate of `vecernica-2021`, shifted one year (legacy block 1035–1057).

## Večernica 2023  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2023` | 416 | Marjana Moškrič | dr. Dragica Haramija, Darka Tancer Kajnih, Norma Bale, Klara Širovnik, Lenart Zajc, Alenka Urh |
| `vecernica-2023-2` | 1056 | Špela Frlic | dr. Dragica Haramija, Darka Tancer Kajnih, Alenka Urh, Barbara Zorman, Klara Širovnik |

Decision: **drop** `vecernica-2023-2` [sure]: duplicate of `vecernica-2022`, shifted one year (legacy block 1035–1057).

## Večernica 2024  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `vecernica-2024` | 417 | Andrej E. Skubic | Darka Tancer Kajnih, Norma Bale, Klara Širovnik, Lenart Zajc, Alenka Urh |
| `vecernica-2024-2` | 1057 | Marjana Moškrič | dr. Dragica Haramija, Darka Tancer Kajnih, Norma Bale, Klara Širovnik, Lenart Zajc, Alenka Urh |

Decision: **drop** `vecernica-2024-2` [sure]: duplicate of `vecernica-2023`, shifted one year (legacy block 1035–1057).

## Zlata ptica 2012  (different juries)

| edition_id | legacy line | winners | jury |
|---|---|---|---|
| `zlata-ptica-2012` | 45 | Elvis Halilović, Maja Smrekar, Blaž Božič, Boštjan Čadež, Maja Delak, Luka Prinčič | Alenka Gregorič, Mare Bulc, Dejan Koban, Bor Pungerčič, Vuk Ćosić |
| `zlata-ptica-2012-2` | 48 | Socialni center Rog, Pekarna magdalenske mreže, Kino Udarnik, Kulturno umetniško društvo Mreža, Festival Sajeta | — |

Decision: **Zlata ptica series** [check: year convention]. Our data is labelled by the year the awards are *for*, and the ceremony is the following spring: `zlata-ptica-2008` = ceremony May 2009 (rtvslo), `-2011` = golden nests, ceremony May 2012 (rtvslo + web search), `-2012` = Halilović, Smrekar, Božič, Čadež, Delak, Prinčič, ceremony 5. 6. 2013 (STA). So `zlata-ptica-2013` (same winners, no jury) is a **duplicate → drop**. `zlata-ptica-2012-2` (Rog, Pekarna, Kino Udarnik, KUD Mreža, Sajeta) is not found in any source → **drop** unless a source turns up. Open: keep the "for year" labels, or relabel to the ceremony year like the other awards (+1 for the whole series)?

# Editions with no winners

These rows had an empty winners cell. Fill in the winners or drop the edition.

- `bernekerjeva-nagrada-1996`
- `bert-2020`
- `grumova-nagrada-1986`
- `grumova-nagrada-1997`
- `kosobrin-2026`
- `lastovka-2018`
- `majski-salon-2024`
- `nagrada-kristine-brenkove-2025`
- `nagrada-marka-slodnjaka-2022`
- `nagrada-poldeta-bibica-2016`
- `najboljsi-esej-2026`
- `trdinova-nagrada-1990`
