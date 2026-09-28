# Licenze e attribuzione

Questo repository ha **due strati** con licenze diverse, e la distinzione conta.

## 1 · Le definizioni (dati)

`templates/`, e le note di misura che le accompagnano.

La definizione `iccd-us-2021` è ricostruita dal modello ICCD
*«US — Unità Stratigrafica, modello per il rilevamento sul campo, 2021»*, che
l'ICCD pubblica con licenza **CC BY-SA 4.0** (dichiarazione in calce al file
`.doc`: *«MiC - ICCD_licenza CC BY-SA 4.0»*).

Di conseguenza:

* la definizione è **CC BY-SA 4.0**;
* l'attribuzione è **MiC — Istituto Centrale per il Catalogo e la
  Documentazione (ICCD)**, e sta nel dato (`standard.attribution`), non solo qui;
* chi la modifica o la ridistribuisce lo fa alla stessa condizione.

**Perché conta.** Ricostruire la scheda dalla NORMA è esplicitamente permesso;
ricopiare i template di un'applicazione GPL (form HTML, generatori PDF) sarebbe
un'opera derivata di quel software, con tutti i vincoli che ne seguono. La
strada scelta qui è pulita per costruzione, non per fortuna.

La definizione `es-ue-demo-2026` è **inventata** (`invented: true`, e la stampa
porta il bollo `FIXTURE`): non cita nessuna normativa nazionale reale.

## 1-bis · I vocabolari che ORIGINIAMO noi

`vocabularies/skos/`, dichiarati con `origin: originated` in
`vocabularies/schemes/`.

Sono una categoria a sé e vanno tenuti distinti dagli strumenti altrui: qui non
stiamo referenziando il lavoro di un ente, lo stiamo facendo. Quindi rispondiamo
noi del contenuto, e il validatore pretende tre cose senza le quali un modulo
nostro è incitabile — `version`, `license`, `uri`.

Il primo è **`em-taph-weathering`**: i sei stadi di alterazione dell'osso di
Behrensmeyer 1978, **CC BY 4.0**, attribuzione StratiGraph WP3 — CNR-ISPC.

**Perché è lecito, ed è la stessa ragione della scheda ICCD.** I sei stadi sono
un fatto scientifico pubblicato e non sono coperti da copyright; la **prosa** di
Behrensmeyer sì. Le definizioni del modulo sono perciò **riformulate e non
trascritte**, e la fonte è citata su ogni singolo concetto oltre che sullo
scheme. Ricostruire la scala dalla letteratura è permesso; ricopiarne le
descrizioni sarebbe un'opera derivata dell'articolo.

**Perché esiste.** È lo standard *de facto* della tafonomia da mezzo secolo e non
ha mai avuto un identificatore: esiste solo come tabella dentro un articolo del
1978. Verificato a settembre 2026: Getty AAT non ha `cut marks`, `gnawing`,
`trampling`; PACTOLS e TAABA hanno `tafonomia` con zero *narrower*. La disciplina
è nominata ovunque, i suoi oggetti da nessuna parte.

Poi i cinque moduli della scheda US — **`em-us-definizione`**,
**`em-us-consistenza`**, **`em-us-colore`**, **`em-us-stato-conservazione`**,
**`em-us-affidabilita`** — **CC BY 4.0**, come il primo. I termini vengono dal
thesaurus e dall'interfaccia di PyArchInit (GPL): sono parole singole o sintagmi
del mestiere («strato di crollo», «friabile»), non un'espressione protetta, e la
fonte è citata su ogni concetto; le definizioni sono nostre. Non derivano dalla
norma ICCD — il modello US 2021 non elenca termini (misurato sul `.doc`) — e per
questo non ereditano la CC BY-SA 4.0 che vale per `templates/`. I valuelist di
iDAI.field (Apache-2.0) servono agli allineamenti e alla scheda DAI, e non sono
copiati (v. §1-quater).

⚠ Il redirect **`w3id.org/extendedmatrix` non è ancora registrato**: gli URI sono
stabili nell'intenzione ma non risolvibili. Va chiesto prima di pubblicare.

## 1-quater · Una definizione letta dalla configurazione di un'applicazione

`templates/dai-idaifield-layer-2026/`, `drafts/draft-idai-field-layer.yaml`,
`vocabularies/schemes/idai-field-*.yaml`.

La quarta specie: né norma pubblicata, né modulo nostro, né export. **La
configurazione aperta di iDAI.field** (Field Desktop), il sistema di
documentazione di scavo del Deutsches Archäologisches Institut, che il DAI
pubblica su GitHub (`dainst/idai-field`) con licenza **Apache-2.0**. Letta al
commit `4b5c1e2c3c499d4bd125d0eda61cc6f5c94ffcd4` (2026-09-24).

**Che cosa entra qui.** I nomi dei campi e dei gruppi, le loro **etichette
de/en** (brevi, quelle che il DAI pubblica in `Language.*.json`), i tipi e i
riferimenti ai valuelist, con l'attribuzione nel dato (`standard.attribution`,
`standard.license: Apache-2.0`) e il commit citato. La lettura, i verdetti, le
note e le domande sono lavoro nostro.

**Che cosa NON entra.** I **valori dei valuelist**: gli schemi `idai-field-*`
li dichiarano e li **risolvono dal checkout** al commit (`resolve.kind:
idai_field_valuelist`), come gli SKOS dell'ICCD si risolvono da
Standard-catalografici. Un'app che li vendora (StratiField, `sync-schede.sh`)
porta con sé l'attribuzione e la licenza dello schema, che Apache-2.0 chiede.

**Nell'immagine pubblicata di un'app** (deciso il 28 set 2026, Cowork per E.D.):
le etichette DAI — quelle dei campi nella scheda compilata e quelle dei valuelist
nei vocabolari vendorati — **possono** stare nell'immagine di StratiField su
GHCR, **con** ciò che Apache-2.0 §4 chiede a chi ridistribuisce: accanto a ogni
directory che le contiene (`schede/dai-idaifield-layer-2026/`, `vocabolari/`)
`sync-schede.sh` scrive **`LICENSE-Apache-2.0.txt`** (il testo che il DAI stesso
distribuisce, letto dal checkout allo stesso commit `4b5c1e2`) e un **`NOTICE`**
che dice che cosa è del DAI, da quale commit, e che le etichette sono riprodotte
senza cambiarne il senso. Il DAI non ha un proprio `NOTICE` a quel commit
(misurato): non c'è niente da propagare oltre all'attribuzione. Generati, mai
scritti a mano; il campo `attribution` di ogni json resta.

**Perché è lecito.** Apache-2.0 permette di ridistribuire e derivare,
chiedendo attribuzione e che la licenza della parte ripresa resti detta:
entrambe stanno nel dato, campo per campo della testata. La descrizione
(verdetti e note) segue il resto di `templates/`.

**Come la IAA, e non come l'ICCD:** la versione resta **0.x** finché il DAI
(Benjamin) non ha visto la lettura e risposto alle domande del referto.

## 1-quinquies · Le liste di buona pratica, che finora non avevano casa

`vocabularies/schemes/` — sezione da aprire quando la prima lista entra.

La quinta specie, e la più comune di tutte: le liste di termini controllati che
nascono **formalizzando un caso studio**, non da una norma e non da un sistema.
«RTK geodesy, UAV, scanner 3D» per lo strumento, «sedimento, carbone» per il
campione, «pulitura meccanica, pulitura chimica» per l'attività, «taglio,
riempimento, muro, piano» per il tipo di unità. Chi lavora le scrive in una
tabella, dentro una relazione o una slide, e lì restano: non sono citabili, non
sono allineabili, e la volta dopo qualcuno le riscrive leggermente diverse.

**Non sono nessuna delle altre quattro.** Non le pubblica un'autorità come
l'ICCD, quindi non si ricostruiscono da una norma. Non le originiamo noi come i
moduli `em-*`, quindi la paternità non è nostra. Non stanno in un export né
nella configurazione di un'applicazione: stanno nel lavoro metodologico di un
gruppo. Hanno però tutto quello che serve a una definizione di questo
repository — **un proprietario, una licenza e una versione** — e quindi qui ci
stanno bene.

**Che cosa entra.** Lo schema di vocabolario con i suoi concetti, le etichette
nelle lingue in cui il gruppo lavora, e l'allineamento a un thesaurus esterno
dove un aggancio esiste (AAT in testa). Nella testata il gruppo che la ha
prodotta come `standard.attribution`, la licenza che sceglie, e la versione.

**L'attribuzione è doppia, come per la IAA e per il DAI.** La lista resta del
gruppo che la ha costruita, la lettura e l'allineamento sono di chi li ha fatti;
chi cita la lista cita entrambi. Finché il gruppo non conferma, la versione
resta **0.x**, che qui significa «non ancora citabile».

**Perché conviene a chi la scrive.** Una lista che sta qui viene validata contro
quello che s3Dgraphy dichiara, esce compilata in `dist/`, si aggancia a un
thesaurus e prende un identificativo che regge nel tempo. Una lista che resta in
una tabella di un documento non fa niente di tutto questo, e invecchia con il
documento che la contiene.

## 2 · I vocabolari (referenziati, non incorporati)

Gli strumenti terminologici dell'ICCD sono SKOS/RDF con licenza
**CC BY-SA 3.0 IT** (`dc:license` nei file, `A33_CCBYSA30IT`), a cura di
M. L. Mancinelli, con C. Veninata, M. T. Natale, M. Porena.

Questo repository **non li copia**: `vocabularies/schemes/*.yaml` dichiara lo
schema, la licenza, l'attribuzione e *dove sta il file* (per default il checkout
`Standard-catalografici/`, ridefinibile con `$STRATIGRAPH_ICCD_STANDARDS`).
I file in `vocabularies/fixtures/` sono micro-schemi **inventati** per le prove e
lo dichiarano nel loro README.

## 3 · Il codice (implementazione di riferimento)

`src/`, `tests/`.

**EUPL-1.2 — CONFERMATA da E. Demetrescu il 2026-09-24.** È la licenza pensata
per il software di progetti europei, è copyleft debole e ha una lista di
compatibilità che include GPL-3.0 e CC BY-SA 4.0 per le opere combinate.

Il **testo ufficiale** sta in `./LICENSE`, 287 righe, preso da
`joinup.ec.europa.eu` (il sito della Commissione) e non riscritto a memoria: una
licenza approssimata è peggio di una licenza assente, perché sembra una licenza.

`pyproject.toml` dichiara `EUPL-1.2` e porta accanto, in un commento, la
ripartizione per parti — perché i metadati di un pacchetto Python sanno
esprimere UNA licenza e questo repository ne ha tre.

## 4 · Attribuzione delle misure

Le misure citate nelle definizioni e nel referto (133 colonne di `us_table`,
32 target di mapping, 276 record della SAS 3.00, 473 mm di altezza del modello
US) sono state prese sul disco il 4-5 settembre 2026 e sono riproducibili con i
comandi in `docs/2026-09-20-NIGHT-la-scheda-diventa-un-dato.md`.
