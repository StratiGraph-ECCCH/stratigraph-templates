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

⚠ Il redirect **`w3id.org/extendedmatrix` non è ancora registrato**: gli URI sono
stabili nell'intenzione ma non risolvibili. Va chiesto prima di pubblicare.

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
