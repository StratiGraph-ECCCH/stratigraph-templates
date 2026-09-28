# stratigraph-templates

**La scheda è un dato, non uno schema.**

In pyarchinit la scheda *è* lo schema: 619 colonne su 29 tabelle sono una
serializzazione dello standard ICCD, e aggiungere la scheda spagnola vorrebbe
dire aggiungere colonne. Misurato: `us_table` da sola ne ha 133, di cui 46
appartengono a un'altra scheda (la USM, che nell'ICCD è un modello a sé) e 13
esistono solo perché la riga non sa dire «questo valore, in questa lingua».

Qui una scheda è una **definizione dichiarativa, versionata, citabile**, che una
macchina legge per fare tre cose diverse:

* mostrare un **modulo** da compilare (telefono, tablet, desktop),
* stampare un **foglio A4 fronte-retro**,
* dire al **grafo** che cosa significa quello che è stato scritto.

Aggiungere una scheda costa **scrivere una definizione**, non scrivere
un'applicazione. La prova sta nei test: il diff del renderer fra prima e dopo
l'aggiunta del secondo standard è vuoto.

> **Questo repository contiene DATI e una implementazione di riferimento.
> Non contiene un'applicazione.** Nessun server, nessun login, nessun database.

## Com'è fatto

```
templates/<id>/template.yaml   le definizioni (la sostanza, il legame al grafo, il foglio)
vocabularies/schemes/          gli schemi di vocabolario, REFERENZIATI non incorporati
vocabularies/alignments/       gli allineamenti SKOS fra vocabolari nazionali
vocabularies/fixtures/         micro-schemi finti, per le prove
examples/                      dati di prova
registry/                      istantanea di ciò che s3Dgraphy dichiara — LA fonte di validate e build
dist/schede/                   le definizioni COMPILATE (JSON autosufficiente): ciò che un'app vendora
src/stratigraph_templates/     l'implementazione di riferimento (legge, valida, rende)
drafts/                        bozze estratte da normative XSD: proposte, non verità
tests/                         la suite, e le definizioni rotte che i cancelli devono prendere
docs/                          il referto della serata e le catture
```

Due definizioni ci sono già:

| definizione | che cos'è | campi |
|---|---|---|
| `iccd-us-2021` | ICCD, Unità Stratigrafica, modello per il rilevamento sul campo 2021 — ricostruita **dalla normativa** (CC BY-SA 4.0) | 59 |
| `es-ue-demo-2026` | una *ficha* dimostrativa, **inventata** e dichiarata tale, in spagnolo e italiano | 15 |

La specifica del formato è in **[SPEC.md](SPEC.md)**.

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'

.venv/bin/stratigraph-templates validate
.venv/bin/stratigraph-templates build                 # → dist/schede/<id>/<versione>.json + index.json
.venv/bin/stratigraph-templates registry-snapshot     # solo quando s3Dgraphy è cambiato: è una decisione
.venv/bin/stratigraph-templates info iccd-us-2021
.venv/bin/stratigraph-templates print iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.pdf
.venv/bin/stratigraph-templates form  iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.html
.venv/bin/stratigraph-templates vocab --scheme fx-ue-definicion-es --concept 'https://example.invalid/fixture/ue-definicion-es/estrato' --lang it
.venv/bin/stratigraph-templates extract-xsd '<…>/ICCD_normativa_SAS_3.00_102019.xsd' --code SAS --version 3.00
.venv/bin/python -m pytest
```

La stampa richiede WeasyPrint (`pip install '.[print]'`; su macOS serve anche
`brew install pango`). La risoluzione dei vocabolari richiede `rdflib`.

### Le due dipendenze fuori dal repository

Due vocabolari altrui **non sono copiati qui**: si leggono dove vivono, da un
checkout accanto a questo repository. Servono a risolvere le **etichette** dei
concetti (`vocab`, `form`/`print` con le parole, i test che le leggono) e a
`extract-idai-field`; **`validate` e `build` non ne hanno bisogno** (il compilato
nomina gli schemi, non ne copia le parole), ma se mancano lo dicono in una riga.

| checkout | dove (default) | variabile | commit | a che cosa serve |
|---|---|---|---|---|
| [ICCD-MiBACT/Standard-catalografici](https://github.com/ICCD-MiBACT/Standard-catalografici) | `~/Documents/GitHub/Standard-catalografici` | `$STRATIGRAPH_ICCD_STANDARDS` | qualunque (letto il working tree; misurato su `c1de8c3`, 2026-03-26) | gli SKOS/RDF degli strumenti terminologici ICCD (`resolve.kind: external_skos_file`) e le XSD per `extract-xsd` |
| [dainst/idai-field](https://github.com/dainst/idai-field) | `~/Documents/GitHub/idai-field` | `$STRATIGRAPH_IDAI_FIELD` | **deve contenere `4b5c1e2`** (2026-09-24): si legge con `git show <commit>:…`, mai il working tree | i valuelist DAI degli schemi `idai-field-*` (`resolve.kind: idai_field_valuelist`) e `extract-idai-field` |

```bash
cd ~/Documents/GitHub
git clone https://github.com/ICCD-MiBACT/Standard-catalografici.git
# basta la configurazione, non l'applicazione (23 MB invece dell'intero repository):
git clone --filter=blob:none --sparse https://github.com/dainst/idai-field.git
git -C idai-field sparse-checkout set core/config core/src/configuration core/src/model/configuration
git -C idai-field cat-file -e 4b5c1e2c3c499d4bd125d0eda61cc6f5c94ffcd4^{commit} && echo ok
```

## Le cinque specie di definizione

Una definizione che entra qui viene da qualche parte, e da dove viene decide
come si cita e con che licenza si ridistribuisce. Le specie sono cinque, e
[LICENSING.md](LICENSING.md) le tratta una per una.

| specie | da dove viene | esempio |
|---|---|---|
| norma pubblicata | ricostruita dalla normativa di un'autorità | `iccd-us-2021` |
| modulo nostro | lo originiamo noi, per il linguaggio EM | gli schemi `em-*` |
| configurazione di un'applicazione | letta dal codice aperto di un sistema di scavo | `dai-idaifield-layer-2026` |
| **buona pratica** | nasce formalizzando un caso studio: non la pubblica un'autorità, non la originiamo noi, non sta in un sistema | *da aprire* |

L'ultima è la più comune e finora non aveva una casa: le liste di termini che un
gruppo scrive mentre formalizza il proprio lavoro — tipi di strumento, di
campione, di attività, di unità — e che restano dentro una tabella di una
relazione, non citabili e non allineabili. Hanno un proprietario, una licenza e
una versione, che è tutto ciò che questo repository chiede. L'attribuzione è
doppia come per la IAA e per il DAI: la lista resta del gruppo che l'ha
costruita, la lettura e l'allineamento sono di chi li ha fatti.

## Il legame con s3Dgraphy

Ogni definizione dichiara, campo per campo, che cosa significa per il grafo. I
nomi di tipo di nodo, tipo di arco e qualia sono verificati contro **quello che
s3Dgraphy dichiara oggi**: un nome che non esiste è un errore, non un avviso — è
così che «non aggiungere tipi al datamodel» si fa rispettare da sé invece che a
parole.

La fonte è **una sola**: `registry/s3dgraphy-snapshot.json`, committato, che
dice da quale commit di s3Dgraphy e con quali versioni dei datamodel è stato
preso. Se il checkout di s3Dgraphy è su questa macchina, `validate` e `build` lo
confrontano con lo snapshot e, **se divergono, lo dicono e si fermano**: non
scelgono da soli. Rigenerare lo snapshot (`registry-snapshot`) è la decisione,
e il diff di `registry/` ne è il documento. Senza snapshot **non si valida
niente**: non esiste una terza modalità permissiva.

## La forma compilata — come una definizione arriva a un programma

`build` scrive, per ogni definizione valida, un JSON autosufficiente in
`dist/schede/<id>/<versione>.json` (più un `index.json`): testata con versione
della definizione, digest e datamodel di s3Dgraphy contro cui è stata validata;
una **metà visiva** (campi, etichette in tutte le lingue, foglio); una **ricetta**
che dice, campo per campo, quali delle cinque operazioni CRDT di s3Dgraphy
produrre — senza valori. L'orchestratore è StratiGraph Server: chi compila la
scheda manda quelle operazioni alla stanza. Lo stesso patto di `sync-brand.sh` e
`sync-datamodels.sh`: **qui si produce, l'app vendora e committa la copia**.
Una versione pubblicata non cambia: un contenuto diverso sotto lo stesso numero
è rifiutato. SPEC §9.

## Licenze — due strati, e la ragione per cui questa strada è pulita

* **Le definizioni** derivano dalle normative ICCD, pubblicate **CC BY-SA 4.0**
  (dichiarato in calce ai modelli da campo): sono distribuite alla stessa
  condizione e portano l'attribuzione al MiC — ICCD in `standard.attribution`.
  I thesauri ICCD sono **CC BY-SA 3.0 IT** e sono **referenziati**, non copiati.
* **Il codice** dell'implementazione di riferimento: proposta **EUPL-1.2**
  (progetto europeo, compatibile con la condivisione allo stesso modo) —
  **da confermare**, vedi [LICENSING.md](LICENSING.md).

Non è burocrazia: ricostruire la scheda **dalla norma** è esplicitamente
permesso, mentre ricopiare i template di un software GPL non lo sarebbe.
