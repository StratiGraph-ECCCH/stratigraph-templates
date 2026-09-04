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
registry/                      istantanea di ciò che s3Dgraphy dichiara
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
.venv/bin/stratigraph-templates info iccd-us-2021
.venv/bin/stratigraph-templates print iccd-us-2021 --record examples/us-3014-cencelle.yaml --lang it -o out/us.pdf
.venv/bin/stratigraph-templates form  iccd-us-2021 --record examples/us-3014-cencelle.yaml --lang it -o out/us.html
.venv/bin/stratigraph-templates vocab --scheme fx-ue-definicion-es --concept 'https://example.invalid/fixture/ue-definicion-es/estrato' --lang it
.venv/bin/stratigraph-templates extract-xsd '<…>/ICCD_normativa_SAS_3.00_102019.xsd' --code SAS --version 3.00
.venv/bin/python -m pytest
```

La stampa richiede WeasyPrint (`pip install '.[print]'`; su macOS serve anche
`brew install pango`). La risoluzione dei vocabolari richiede `rdflib`.

## Il legame con s3Dgraphy

Ogni definizione dichiara, campo per campo, che cosa significa per il grafo. I
nomi di tipo di nodo, tipo di arco e qualia sono verificati contro **quello che
s3Dgraphy dichiara oggi**: un nome che non esiste è un errore, non un avviso — è
così che «non aggiungere tipi al datamodel» si fa rispettare da sé invece che a
parole.

Se s3Dgraphy non è leggibile si usa `registry/s3dgraphy-snapshot.json`, che dice
da dove è stato preso. Se non si può leggere nessuno dei due **non si valida
niente**: non esiste una terza modalità permissiva.

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
