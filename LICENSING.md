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

**Proposta: EUPL-1.2** — è la licenza pensata per il software di progetti
europei, è copyleft debole e ha una lista di compatibilità che include GPL-3.0 e
CC BY-SA 4.0 per le opere combinate.

**Questa scelta è una proposta e va confermata da E. Demetrescu**: la decisione
di licenza di un repository nuovo non è un effetto collaterale della prima
notte di lavoro. Fino alla conferma, `pyproject.toml` dichiara `EUPL-1.2` e
questo paragrafo dice che è in attesa di conferma.

## 4 · Attribuzione delle misure

Le misure citate nelle definizioni e nel referto (133 colonne di `us_table`,
32 target di mapping, 276 record della SAS 3.00, 473 mm di altezza del modello
US) sono state prese sul disco il 4-5 settembre 2026 e sono riproducibili con i
comandi in `docs/2026-09-20-NIGHT-la-scheda-diventa-un-dato.md`.
