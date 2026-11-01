# Review: names the enrichment resolved differently

During enrichment, the search model sometimes identified a person under a
different name. Typo fixes (Kocmu → Kocmut) should be applied as a rename
plus an alias. Fuller names (added middle name or second surname) are optional.
A different person means the enrichment data for that entity is wrong.

**Status 2026-11-01: applied** by `scripts/apply_name_decisions.py` (log in
`data/meta/name_decisions.csv`). Also merged seven hidden duplicates where the
resolved name already existed as its own entity (Prinčič, Steinbacher, Lili Prap,
Krošl, Slokar Kos, Šušnik, Emerik Bernard). Still open: `ida` vs `ida-weiss`
(the Iris 2023 winner may be a film title), `samo-strelec` vs `samo-m-strelec`,
`anja-bezlova` (Anja Završnik?).

| entity_id | name in data | resolved name | decision |
|---|---|---|---|
| `adrian-garcia-bogliano` | Adrian Garcia Bogliano | Adrián García Bogliano | **rename**: correct spelling; old one becomes alias |
| `aleksander-ostan` | Aleksander Ostan | Aleksander Saša Ostan | **alias**: keep name as printed in award sources; add resolved name as alias |
| `aleksandra-kocmu` | Aleksandra Kocmu | Aleksandra Kocmut | **rename**: correct spelling; old one becomes alias |
| `alenka-moder` | Alenka Moder | Alenka Moder Saje | **alias**: keep name as printed in award sources; add resolved name as alias |
| `alesh-maatko` | Alesh Maatko | Aleš Maatko | **alias**: keep name as printed in award sources; add resolved name as alias |
| `alessio-princic` | Alessio Princic | Aleš Prinčič | **alias** (default; not checked) |
| `alex-volasko` | Alex Volasko | Aleksander Volasko | **alias**: keep name as printed in award sources; add resolved name as alias |
| `alex-de-la-iglesia` | Alex de la Iglesia | Alejandro de la Iglesia Mendoza | **alias**: keep name as printed in award sources; add resolved name as alias |
| `alexander-gadjiev` | Alexander Gadjiev | Aleksander Gadžijev | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ales-blatnik` | Aleš Blatnik | Andrej Blatnik | **wrong-person**: enrichment is Andrej Blatnik's (b. 1963); Aleš Blatnik is a film juror; clear enrichment |
| `ales-vavpotic` | Aleš Vavpotič | Aleš Vaupotič | **rename**: correct spelling; old one becomes alias |
| `alma-causevic-klemencic-2` | Alma Čauševič Klemenčič | Alma Čaušević Klemenčič | **rename**: correct spelling; old one becomes alias |
| `alya` | Alya | Alja Omladič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ana-marij-kozlevcar` | Ana Marij Kozlevčar | Ana Marija Kozlevčar | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ana-stefanec` | Ana Štefanec | Ana Štefanec Knez | **alias**: keep name as printed in award sources; add resolved name as alias |
| `andrey-breznik` | Andrey Breznik | Andrej Breznik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `andriej-moskwin` | Andriej Moskwin | Andrej Moskwin | **alias**: keep name as printed in award sources; add resolved name as alias |
| `anja-bezlova` | Anja Bezlova | Anja Završnik | [check] Anja Završnik a married name, or a different person? default keep, no alias |
| `anja-planiscek` | Anja Planišček | Anja Planišček | **rename**: correct spelling; old one becomes alias |
| `anna-facchini` | Anna Facchini | Ana Facchini | **alias**: keep name as printed in award sources; add resolved name as alias |
| `anne-gavalda` | Anne Gavalda | Anna Gavalda | **rename**: correct spelling; old one becomes alias |
| `anton-demsar` | Anton Demšar | Anton Jernej Demšar | **alias**: keep name as printed in award sources; add resolved name as alias |
| `antony-gardner` | Antony Gardner | Anthony Gardner | **alias**: keep name as printed in award sources; add resolved name as alias |
| `arhitekturni-atelje-medprostor` | Arhitekturni Atelje Medprostor | Arhitekturni atelje Medprostor | **rename**: correct spelling; old one becomes alias |
| `asta-vrecko` | Asta Vrečko | Asta Vrečko | **rename**: correct spelling; old one becomes alias |
| `ati-soss` | Ati Soss | Karel Soss | **alias**: keep name as printed in award sources; add resolved name as alias |
| `balladero` | Balladero | Dominik Bagola | **alias**: keep name as printed in award sources; add resolved name as alias |
| `bina-stampe-zmavc` | Bina Štampe žmavc | Bina Štampe Žmavc | **rename**: correct spelling; old one becomes alias |
| `bine-rogelj` | Bine Rogelj | Albin Rogelj | **alias**: keep name as printed in award sources; add resolved name as alias |
| `bogdan` | Bogdan | Bogdan Borčić | **wrong-person**: MMS 2018 winner matched to painter Bogdan Borčić (b. 1926); clear enrichment |
| `bogdan-mesko` | Bogdan Meško | Kiar (Bogdan) Meško | **alias**: keep name as printed in award sources; add resolved name as alias |
| `bogo-leskovic` | Bogo Leskovic | Bogomir Leskovič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `bogo-sajovic` | Bogo Sajovic | Bogdan Sajovic | **alias**: keep name as printed in award sources; add resolved name as alias |
| `boris-sinigoj` | Boris Šinigoj | Boris Šinigoj (mlajši) | **alias**: keep name as printed in award sources; add resolved name as alias |
| `center-in-galerija-p74` | Center in galerija P74 | Tadej Pogačar | **institution**: resolved to a member (Tadej Pogačar); set entity_type, clear person data, no alias |
| `ciril-cvetko` | Ciril Cvetko | Ciril Gabrijel Cvetko | **alias**: keep name as printed in award sources; add resolved name as alias |
| `cristoph-huber` | Cristoph Huber | Christoph Huber | **rename**: correct spelling; old one becomes alias |
| `cro` | Cro | Luiza Crobath | **alias**: keep name as printed in award sources; add resolved name as alias |
| `celestin` | Célestin | Fran Celestin | **wrong-person**: Zlata hruška 2023 winner matched to 19th-c. writer Fran Celestin; clear enrichment |
| `damjan-levec-emperatrizz` | Damjan Levec - Emperatrizz | Damjan Levec | **keep**: absorbs `empera3zz`; alias Empera3zz, Damjan Levec |
| `darka-tancer-kajnih` | Darka Tancer Kajnih | Darka Tancer-Kajnih | **alias**: keep name as printed in award sources; add resolved name as alias |
| `david-verbucthe` | David VerbučThe | David Verbuč | **rename**: correct spelling; old one becomes alias |
| `davorina-lenko` | Davorina Lenko | Davorin Lenko | **rename** to Davorin Lenko, id `davorin-lenko` (confirmed by user); alias Davorina Lenko |
| `defonija` | Defonija | Miha Zadnikar | **group**: resolved to a member (Miha Zadnikar); set entity_type, clear person data, no alias |
| `delavska-godba-iz-trbovelj` | Delavska Godba Iz Trbovelj | Delavska godba iz Trbovelj | **rename**: correct spelling; old one becomes alias |
| `denis-zivcec` | Denis Živčec | Denis Bende Živčec | **alias**: keep name as printed in award sources; add resolved name as alias |
| `diskolektiv` | Diskolektiv | Gregor Kamnikar | **group**: resolved to a member (Gregor Kamnikar); set entity_type, clear person data, no alias |
| `dragan-jelicic` | Dragan Jelićić | Dragan Jeličić | **rename**: correct spelling; old one becomes alias |
| `dusan-velkavrh` | Dušan Velkavrh | Dušan Velkaverh | **rename**: correct spelling; old one becomes alias |
| `dzevad-karahsan` | Dževad Karahsan | Dževad Karahasan | **rename**: correct spelling; old one becomes alias |
| `edo-ravnikar-ml` | Edo Ravnikar Ml. | Edo Ravnikar ml. | **rename**: correct spelling; old one becomes alias |
| `elise-gravel` | Elise Gravel | Élise Gravel | **rename**: correct spelling; old one becomes alias |
| `emerik-bernard-b` | Emerik Bernard[b] | Emerik Bernard | **rename**: correct spelling; old one becomes alias |
| `empera3zz` | Empera3zz | Damjan Levec | **merge** into `damjan-levec-emperatrizz` (confirmed by user) |
| `filip-kumbatovic-kalan` | Filip Kumbatovič - Kalan | Filip Kumbatovič Kalan | **alias**: keep name as printed in award sources; add resolved name as alias |
| `godalni-kvartet-tartini` | Godalni Kvartet Tartini | Godalni kvartet Tartini | **rename**: correct spelling; old one becomes alias |
| `goran-lisica-fox` | Goran Lisica - Fox | Goran Lisica | **keep**: nickname form; alias the short name |
| `goran-strefanovski` | Goran Strefanovski | Goran Stefanovski | **rename**: correct spelling; old one becomes alias |
| `ida` | Ida | Ida Weiss | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ignacija-j-fridl` | Ignacija J. Fridl | Ignacija Fridl Jarc | **alias**: keep name as printed in award sources; add resolved name as alias |
| `igor-ruzic` | Igor Ružič | Igor Ružić | **alias**: č/ć or styling variant; both in use, keep the name as printed |
| `igor-skulj` | Igor Skulj | Igor Škulj | **rename**: correct spelling; old one becomes alias |
| `ina-shai` | Ina Shai | Martina Šraj | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ingrid-brus-kovac` | Ingrid Brus Kovač | Ingrid Kovač Brus | **alias**: keep name as printed in award sources; add resolved name as alias |
| `isaac-palma` | Isaac Palma | Isaac Leandro Palma | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ivan-marincek` | Ivan Marinček | Ivan Andrej Marinček | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ivan-stuhec` | Ivan Štuhec | Ivan Janez Štuhec | **alias**: keep name as printed in award sources; add resolved name as alias |
| `iztok-geister-plamen` | Iztok Geister - Plamen | Iztok Geister | **keep**: nickname form; alias the short name |
| `jan-podbreznik` | Jan Podbrežnik | Jan Franc Podbrežnik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `janez-boncina-benc` | Janez Bončina - Benč | Janez Bončina | **keep**: nickname form; alias the short name |
| `janez-petretic-ive` | Janez Petretič Ive | Janez Petretič | **keep**: nickname form; alias the short name |
| `janja-kolaric` | Janja Kolarič | Jana Kolarič | **alias** (Jana Kolarič); keep [medium confidence match] |
| `jedert-vodopivec` | Jedert Vodopivec | Jedert Vodopivec Tomažič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `jelka-ciglenicki` | Jelka Ciglenički | Jelka Ciglenečki | **rename**: correct spelling; old one becomes alias |
| `kaja-perat` | Kaja Perat | Katja Perat | **wrong-person**: source prints Kaja Perat (Borštnik 2015 jury, confirmed); enrichment copied from the poet Katja Perat; clear enrichment |
| `karl-markus-gauss` | Karl-Markus Gauss | Karl-Markus Gauß | **rename**: correct spelling; old one becomes alias |
| `karpo-godina` | Karpo Godina | Karpo Ačimović Godina | **alias**: keep name as printed in award sources; add resolved name as alias |
| `komorni-godalni-orkester-slovenske-filharmonije` | Komorni Godalni Orkester Slovenske Filharmonije | Komorni godalni orkester Slovenske filharmonije | **rename**: correct spelling; old one becomes alias |
| `komorni-zbor-ave` | Komorni Zbor Ave | Komorni zbor Ave | **rename**: correct spelling; old one becomes alias |
| `koni-steinbaher` | Koni Steinbaher | Konrad Steinbacher | **rename** to Koni Steinbacher (spelling); alias Konrad Steinbacher |
| `kristina-buozyte` | Kristina Buožyte | Kristina Buožytė | **rename**: correct spelling; old one becomes alias |
| `kristjan-lesnik-musek` | Kristjan Lešnik Musek | Kristijan Musek Lešnik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `kukla` | Kukla | Katarina Rešek | **alias**: keep name as printed in award sources; add resolved name as alias |
| `lenart-kucic` | Lenart Kučič | Lenart J. Kučić | **alias**: keep name as printed in award sources; add resolved name as alias |
| `lili-prap` | Lili Prap | Lilijana Praprotnik Zupančič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ljubljanska-drama` | Ljubljanska Drama | Slovensko narodno gledališče Drama Ljubljana | **alias**: keep name as printed in award sources; add resolved name as alias |
| `lojz-kraigher` | Lojz Kraigher | Alojz Kraigher | **alias**: keep name as printed in award sources; add resolved name as alias |
| `luka-zabric` | Luka Zabric | Luka Zabrič | **rename**: correct spelling; old one becomes alias |
| `luna-j-sribar` | LunA J. Šribar | Luna Jurančič Šribar | **rename** to Luna J. Šribar (case typo) |
| `mgl` | MGL | Mestno gledališče ljubljansko | **alias**: keep name as printed in award sources; add resolved name as alias |
| `maja-jancic` | Maja Jančič | Maja Bogataj Jančič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `majda-bozeglav` | Majda Božeglav | Majda Božeglav Japelj | **alias**: keep name as printed in award sources; add resolved name as alias |
| `maks-strmcnik` | Maks Strmčnik | Maksimiljan Strmčnik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `manica-j-ambrozic` | Manica J. Ambrožič | Manica Janežič Ambrožič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mara-partida-munoz` | Mara Partida Munoz | Mara Partida Muñoz | **rename**: correct spelling; old one becomes alias |
| `marcos-fink` | Marcos Fink | Marcos Teodoro Fink | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mare-bulc` | Mare Bulc | Marko Bulc | **rename** to Marko Bulc (confirmed by user: a man); keep enrichment |
| `maria-sako` | Maria Säkö | Maria Pauliina Säkö | **alias**: keep name as printed in award sources; add resolved name as alias |
| `marija-rapa-suklje` | Marija Rapa Šuklje | Marija Šuklje | **keep**: nickname form; alias the short name |
| `marijan-britovsek` | Marijan Britovšek | Marjan Britovšek | **alias**: keep name as printed in award sources; add resolved name as alias |
| `marina-milivojevic-madjarev` | Marina Milivojević-Madjarev | Marina Milivojević-Mađarev | **rename**: correct spelling; old one becomes alias |
| `marina-richter` | Marina Richter | Marina D. Richter | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mario-berdic` | Mario Berdič | Mario Berdič Codella | **alias**: keep name as printed in award sources; add resolved name as alias |
| `marjan-amalietti` | Marjan Amalietti | Marijan Amalietti | **alias**: keep name as printed in award sources; add resolved name as alias |
| `marko-dekleva` | Marko Dekleva | Marko Marjan Dekleva | **alias**: keep name as printed in award sources; add resolved name as alias |
| `marko-rupnik` | Marko Rupnik | Marko Ivan Rupnik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `martina` | Martina | Martina Batič | **wrong-person**: MMS 2024 winner matched to choir conductor Martina Batič; clear enrichment |
| `martina-ozbot` | Martina Ožbot | Martina Ožbot Currie | **alias**: keep name as printed in award sources; add resolved name as alias |
| `masayah` | Masayah | Mia Puhar Rodin | **alias**: keep name as printed in award sources; add resolved name as alias |
| `matej-kucina` | Matej Kučina | Matej Kučina | **rename**: correct spelling; old one becomes alias |
| `matevz-vidmar-celik` | Matevž Vidmar Čelik | Matevž Čelik Vidmar | **alias**: keep name as printed in award sources; add resolved name as alias |
| `matija-kozamernik-jojo` | Matija Kozamernik Jojo | Matija Kozamernik | **keep**: nickname form; alias the short name |
| `miha-gunzek` | Miha Gunzek | Mihael Gunzek | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mikko-roiha` | Mikko Roiha | Mikko Aleksi Roiha | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mile-de-gleria` | Mile De Gleria | Mile de Gleria | **rename**: correct spelling; old one becomes alias |
| `milica-maslo` | Milica Maslo | Milica Maslo Bezer | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mimi-inhof` | Mimi Inhof | Miran Inhof | **gender f** (confirmed by user); not Miran Inhof; no alias |
| `mini-teater-ljubljana` | Mini Teater Ljubljana | Robert Waltl | **institution**: resolved to a member (Robert Waltl); set entity_type, clear person data, no alias |
| `miran-gracer` | Miran Gracer | Miran Gracer mlajši | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mircea-cartarescu` | Mircea Cartarescu | Mircea Cărtărescu | **rename**: correct spelling; old one becomes alias |
| `miriam-kicinova` | Miriam Kičinova | Miriam Kičiňová | **rename**: correct spelling; old one becomes alias |
| `mirjam-bevc` | Mirjam Bevc | Mirjam Bevc Peressutti | **alias**: keep name as printed in award sources; add resolved name as alias |
| `miro-purivatra` | Miro Purivatra | Mirsad Purivatra | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mico-micovic` | Mičo Mičović | Miloslav Mićović | **alias**: keep name as printed in award sources; add resolved name as alias |
| `misa-cermak` | Miša Čermak | Milojka Miša Čermak | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mladen-djordjevic` | Mladen Djordjević | Mladen Đorđević | **rename**: correct spelling; old one becomes alias |
| `mladinski-pevski-zbor-iz-maribora` | Mladinski Pevski Zbor Iz Maribora | Mladinski pevski zbor iz Maribora | **rename**: correct spelling; old one becomes alias |
| `moises-romera` | Moisés Romera | Moisés Romera Pérez | **alias**: keep name as printed in award sources; add resolved name as alias |
| `mojmir-lasan` | Mojmir Lasan | Mojmir Lašan | **rename**: correct spelling; old one becomes alias |
| `narvika-bavcon` | Narvika Bavcon | Narvika Bovcon | **rename**: correct spelling; old one becomes alias |
| `natasa-prosenc` | Nataša Prosenc | Nataša Prosenc Stearns | **alias**: keep name as printed in award sources; add resolved name as alias |
| `nenad-zivkovic-neso` | Nenad Živković Nešo | Nenad Živković | **keep**: nickname form; alias the short name |
| `niko-jez` | Niko Jež | Nikolaj Jež | **alias**: keep name as printed in award sources; add resolved name as alias |
| `niko-r-kolar` | Niko R. Kolar | Niko Rudolf Kolar | **alias**: keep name as printed in award sources; add resolved name as alias |
| `ninnay` | Ninnay | Nina Bužanin Simčič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `nusa-jurkovic` | Nuša Jurkovič | Nuša Jurkovič | **rename**: correct spelling; old one becomes alias |
| `olga-tokarczuk` | Olga Tokarczuk | Olga Nawoja Tokarczuk | **alias**: keep name as printed in award sources; add resolved name as alias |
| `oto-bajde` | Oto Bajde | Oton Bajde | **alias**: keep name as printed in award sources; add resolved name as alias |
| `otto-tolnai` | Otto Tolnai | Ottó Tolnai | **rename**: correct spelling; old one becomes alias |
| `paula-caspao` | Paula Caspao | Paula Caspão | **rename**: correct spelling; old one becomes alias |
| `pavel-golia` | Pavel Golia | Pavel Metod Golia | **alias**: keep name as printed in award sources; add resolved name as alias |
| `pavle-merku` | Pavle Merkú | Pavle Merkù | **rename**: correct spelling; old one becomes alias |
| `petra-trampuz` | Petra Trampuž | Petra Trampuž Bocevska | **alias**: keep name as printed in award sources; add resolved name as alias |
| `polona-filipic` | Polona Filipič | Polona Filipič Gorenšek | **alias**: keep name as printed in award sources; add resolved name as alias |
| `peter-nadas` | Péter Nadas | Péter Nádas | **rename**: correct spelling; old one becomes alias |
| `raay` | Raay | Aleš Vovk | **alias**: keep name as printed in award sources; add resolved name as alias |
| `rade-krstic` | Rade Krstić | Rade Krstič | **alias**: č/ć or styling variant; both in use, keep the name as printed |
| `radio-smarje-pri-jelsah` | Radio Šmarje pri Jelšah | Jože Jakoš | **institution**: resolved to a member (Jože Jakoš); set entity_type, clear person data, no alias |
| `rastko-pecar` | Rastko Pečar | Rastko Pečar | **rename**: correct spelling; old one becomes alias |
| `raul-monge` | Raúl Monge | Raúl Monge | **rename**: correct spelling; old one becomes alias |
| `rene-maurin` | Rene Maurin | Rene Jože Maurin | **alias**: keep name as printed in award sources; add resolved name as alias |
| `roberto-magnifico` | Roberto Magnifico | Robert Pešut | **alias**: keep name as printed in award sources; add resolved name as alias |
| `rok-k-nagode` | Rok K. Nagode | Rok Kajzer Nagode | **alias**: keep name as printed in award sources; add resolved name as alias |
| `rudi-vavpotic` | Rudi Vavpotič | Rudi Vaupotič | **alias**: Vavpotič confirmed by user |
| `sng-ng` | SNG NG | Slovensko narodno gledališče Nova Gorica | **alias**: keep name as printed in award sources; add resolved name as alias |
| `sadar-vuga` | Sadar+Vuga | SADAR+VUGA | **alias**: č/ć or styling variant; both in use, keep the name as printed |
| `sam-orti` | Sam Orti | Sam Ortí | **rename**: correct spelling; old one becomes alias |
| `samo-m-strelec` | Samo M. Strelec | Samo Marija Strelec | **alias**: keep name as printed in award sources; add resolved name as alias |
| `samo-strelec` | Samo Strelec | Samo M. Strelec | **keep** separate [open]: unclear whether the Borštnik 2000 juror is Samo M. Strelec; no alias (would collide) |
| `sandi-krosl` | Sandi Krošl | Aleksander Krošl | **alias**: keep name as printed in award sources; add resolved name as alias |
| `sandra-basic` | Sandra Bašič | Sandra Bašič Hrvatin | **alias**: keep name as printed in award sources; add resolved name as alias |
| `sandra-krkoc` | Sandra Krkoč | Sandra Krkoč Lasič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `sasa-begovic` | Saša Begovič | Saša Begović | **alias**: č/ć or styling variant; both in use, keep the name as printed |
| `sasa-loncar` | Saša Lončar | Aleksandra Saša Lončar | **alias**: keep name as printed in award sources; add resolved name as alias |
| `sasa-machtig` | Saša Mächtig | Saša Janez Mächtig | **alias**: keep name as printed in award sources; add resolved name as alias |
| `simon-hudolin-salci` | Simon Hudolin Salči | Simon Hudolin | **keep**: nickname form; alias the short name |
| `srdjan-golubovic` | Srdjan Golubović | Srdan Golubović | **rename**: correct spelling; old one becomes alias |
| `stane-rozman` | Stane Rozman | Franc Rozman – Stane | **wrong-person**: matched to WWII general Franc Rozman – Stane; clear enrichment |
| `stanislava-chrobakova-repar` | Stanislava Chrobaková Repar | Stanislava Chrobáková Repar | **rename**: correct spelling; old one becomes alias |
| `steffy-stefica-graselli` | Steffy - Štefica Graselli | Štefica Graselli | **keep**: nickname form; alias the short name |
| `stephane-everaert` | Stephane Everaert | Stéphane Everaert | **rename**: correct spelling; old one becomes alias |
| `suncan-stone` | Sunčan Stone | Sunčan Patrick Stone | **alias**: keep name as printed in award sources; add resolved name as alias |
| `tadeja-krecic` | Tadeja Krečič | Tadeja Krečič Scholten | **alias**: keep name as printed in award sources; add resolved name as alias |
| `tallulah-h-schwab` | Tallulah H. Schwab | Tallulah Hazekamp Schwab | **alias**: keep name as printed in award sources; add resolved name as alias |
| `tjasa-koprivec` | Tjaša Koprivec | Tjaša Koprivec Vuga | **alias**: keep name as printed in award sources; add resolved name as alias |
| `tjasa-slokar` | Tjaša Slokar | Tjaša Slokar Kos | **alias**: keep name as printed in award sources; add resolved name as alias |
| `tomy-declerque` | Tomy Declerque | Tomy DeClerque | **rename**: correct spelling; old one becomes alias |
| `tugo-susnik` | Tugo Šušnik | Tugomir Šušnik | **alias**: keep name as printed in award sources; add resolved name as alias |
| `vasif-kortun` | Vasif Kortun | Vasıf Kortun | **rename**: correct spelling; old one becomes alias |
| `vaso-perovic` | Vaso Perovič | Vaso Perović | **alias**: č/ć or styling variant; both in use, keep the name as printed |
| `vid-sagadin` | Vid Sagadin | Vid Sagadin Žigon | **alias**: keep name as printed in award sources; add resolved name as alias |
| `vida-skerk` | Vida Skerk | Vida Škerk | **rename**: correct spelling; old one becomes alias |
| `viktorija-bencik` | Viktorija Bencik | Viktorija Bencik Emeršič | **alias**: keep name as printed in award sources; add resolved name as alias |
| `yvonna-kreuzmannova` | Yvonna Kreuzmannova | Yvonna Kreuzmannová | **rename**: correct spelling; old one becomes alias |
| `zavod-trajekt` | Zavod Trajekt | Matevž Čelik Vidmar | **institution**: resolved to a member (Matevž Čelik Vidmar); set entity_type, clear person data, no alias |
| `zlata-ognjanovic` | Zlata Ognjanović | Zlata Gašperšič Ognjanović | **alias**: keep name as printed in award sources; add resolved name as alias |
| `dr-dragica-haramija` | dr. Dragica Haramija | Dragica Haramija | done earlier (entity is `dragica-haramija`) |
| `skupina-kaverljag` | skupina Kaverljag | Aleš Sedmak | **group**: resolved to a member (Aleš Sedmak); set entity_type, clear person data, no alias |
| `skupina-nonument-nonument-group` | skupina Nonument / Nonument group | skupina Nonument | **rename** to skupina Nonument |
| `tandem-son-da` | tandem son:DA | Metka Golec | **group**: resolved to a member (Metka Golec); set entity_type, clear person data, no alias |
| `stefka-drolc` | Štefka Drolc | Štefanija Ana Drolc | **alias**: keep name as printed in award sources; add resolved name as alias |
| `zivko-marusic` | Živko Marušič | Živko Ira Marušič | **alias**: keep name as printed in award sources; add resolved name as alias |

## Diacritic variants

These names differ only in diacritics and are almost certainly the same person.
Pick the correct spelling; the other becomes an alias.

| entity_ids | spellings | correct spelling |
|---|---|---|
| `alma-causevic-klemencic`, `alma-causevic-klemencic-2` | Alma Čaušević Klemenčič / Alma Čauševič Klemenčič | **Alma Čaušević Klemenčič** (Bosnian -ević + Slovene -čič); merge `-2` into it |
| `bojan-labovic`, `bojan-labovic-2` | Bojan Labović / Bojan Labovič | **Bojan Labović** (confirmed by user); merge `-2` into it |
| `jaroslav-skrusny`, `jaroslav-skrusny-2` | Jaroslav Skrušny / Jaroslav Skrušný | **Jaroslav Skrušný** (Czech spelling); merge `jaroslav-skrusny` into `-2`, then rename id |
