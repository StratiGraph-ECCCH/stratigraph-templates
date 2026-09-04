# NIGHT — la scheda diventa un dato · referto

*Notte del 2026-09-04/05. Tutto ciò che segue è misurato sul disco di questa
macchina e riproducibile con i comandi citati. Il repository è nuovo:
`~/Documents/GitHub/stratigraph-templates`. Niente è stato committato.*

---

## 0 · L'esito in una riga

La tesi regge: **aggiungere uno standard costa scrivere una definizione**. Il
diff dell'implementazione fra prima e dopo l'aggiunta del secondo standard è
vuoto, e la prova sta in un test che lo tiene vuoto anche domani.

Restano tre cose che *non* si decidono di notte e che questo referto riporta
invece di risolvere: l'attore istituzionale, `CRMsci S13_Sample`, e la licenza
del codice.

---

## 1 · Il formato, e perché YAML (due righe)

**[SPEC.md](../SPEC.md)** — 404 righe: le tre facce, i diciassette tipi di
campo, i sette verdetti di legame al grafo, il foglio A4 fronte-retro,
l'identità a coppia, il riferimento a un vocabolario e la dichiarazione di un
allineamento.

Il formato è **YAML**, per due ragioni e nessuna estetica:

1. **i commenti sono parte del dato**: una definizione deve poter dire, sulla
   riga del campo, dove la scheda e la tabella divergono e perché — in JSON
   quelle note finirebbero in un file a parte, cioè si perderebbero;
2. **si scrive a mano**: etichette normative di quaranta parole e note lunghe
   stanno su più righe senza escape, e l'indentazione fa vedere la struttura a
   paragrafi che la scheda ha già sulla carta.

Il modello resta JSON-compatibile (nessun tag, nessuna ancora): chi preferisce
JSON converte e perde solo i commenti.

---

## 2 · La definizione ICCD US 2021, e il conto contro le 133 colonne

`templates/iccd-us-2021/template.yaml` — ricostruita dal `.doc` normativo
(CC BY-SA 4.0), non dai template di alcun software.

| | |
|---|---:|
| campi | **59** |
| paragrafi | 10 |
| obbligatori | 3 |
| ripetibili | 20 |
| con vocabolario | 5 |
| caselle-relazione (verdetto `edge`) | **13** |
| verdetti | `property` 18 · `node` 18 · `edge` 13 · `vocabulary` 5 · `none` 3 · `node_type` 1 · `identity` 1 |
| facciate | recto 14 righe · verso 11 righe |

Il confronto con `us_table` è misurato da `tools/compare_us_table.py`, che legge
le colonne da `pyarchinit-mini/pyarchinit_mini/models/us.py` e i campi dalla
definizione:

```
us_table: 133 colonne
  USM (scheda diversa, vocabolario CRMba)       46
  gemelle _en (lingua come colonna)             13
  malformate (verdetto E.D.)                     5   cont_per, doc_usv, modo_formazione, rapporti2, ref_n
  tecniche / identità                            4   id_us, node_uuid, unita_tipo, us
  layout                                         1   order_layer
  restano                                       64
```

**Delle 64 restanti, 52 hanno una casella sulla scheda e 12 no.** Le dodici, una
per una:

| colonna | perché non è sulla scheda US 2021 |
|---|---|
| `d_interpretativa` | la scheda ha **una** DEFINIZIONE, non due |
| `periodo_finale`, `fase_finale` | la scheda ha PERIODO e FASE, non una coppia iniziale/finale |
| `scavato` | non è una casella del modello 2021 |
| `metodo_di_scavo` | è della scheda **SAS** (saggio), non della US |
| `struttura` | non è una casella del modello 2021 |
| `tipo_documento` | la scheda distingue le voci (piante/prospetti/sezioni/foto), non il "tipo" |
| `file_path` | è un `ResourceNode`: il legame a un file in MinIO, non una casella di carta |
| `n_catalogo_generale`, `_interno`, `_internazionale` | numeri di catalogo: sono del **record di catalogo**, non del rilevamento |
| `ref_tm` | arco verso la scheda TMA: non una casella della US |

**E al contrario: 21 campi della scheda non hanno una colonna propria in
`us_table`.** Dodici sono le caselle dei rapporti (in tabella un blob
`rapporti`, più `rapporti2`); quattro sono piante/prospetti/sezioni/fotografie
(in tabella un `documentazione` unico); `formazione_segno` è la coppia
POSITIVA/NEGATIVA che decide il tipo di nodo; `modo_formazione` è la riga
discorsiva che la tabella ha come colonna malformata; poi
`identificativo_riferimento`, `dati_quantitativi`, `responsabile_rielaborazione`.

Le cinque colonne malformate non entrano. Una nota: `modo_formazione` sulla
scheda **esiste** come riga discorsiva accanto alle caselle naturale/artificiale
— in `us_table` era un duplicato di `formazione`, sul foglio è una casella vera.
La scheda vince, e la definizione lo dice in `note`.

---

## 3 · La stampa — le dodici caselle sono PIENE

```
$ stratigraph-templates print iccd-us-2021 --record examples/us-3014-cencelle.yaml --lang it -o out/us-3014-it.pdf
out/us-3014-it.pdf — ICCD US 2021, 2 side(s) → 2 page(s), language 'it'
```

Due facciate dichiarate, due pagine prodotte. I dati sono la stessa US ricca del
referto di pyarchinit-mini (Cencelle, strato di crollo), coi rapporti
**strutturati** invece che in un blob:

| casella | stampato |
|---|---|
| UGUALE A | 3021 |
| SI LEGA A | 3011 |
| GLI SI APPOGGIA | 3007 |
| SI APPOGGIA A | 3011 |
| COPERTO DA | 3009 |
| COPRE | 3018, 3020 |
| TAGLIATO DA | 3005 |
| TAGLIA | 3022 |
| RIEMPITO DA | *(vuota: il dato non c'è)* |
| RIEMPIE | *(vuota: il dato non c'è)* |
| POSTERIORE A | 3018, 3019 |
| ANTERIORE A | 3009 |

Il test `test_the_twelve_boxes_print_full` verifica ognuna **nella propria
casella**, e `test_a_blob_of_relations_does_not_leak_into_the_boxes` verifica il
contrario: se qualcuno infila il vecchio blob `"Copre: 3018; Coperto da: 3009"`
in una casella, resta in quella casella e non si spande nelle altre. Il formato
non ha modo di esprimere «tutte e dodici insieme», ed è il punto.

Piene anche COMPONENTI ORGANICI/INORGANICI, MISURE (sei misure), QUOTE (tre),
ELEMENTI DATANTI, DATI QUANTITATIVI, CAMPIONATURE — cioè tutto quello che nel
referto §8 usciva vuoto.

**Una scoperta di geometria, che corregge il documento di design.** Ricostruendo
la griglia del `.doc` (righe, `rowspan`, larghezze: `tools`-non-serve, il calcolo
è in questo referto) risulta che le due etichette verticali coprono **sei righe
ciascuna** e che le colonne misurano `29.9 + 134.7 + 158.1 | 26.6 + 154.8 = 504`.
Cioè: sotto **SEQUENZA FISICA** stanno **dieci** caselle (uguale a, si lega a,
gli si appoggia, si appoggia a, coperto da, copre, tagliato da, taglia, riempito
da, riempie) e sotto **SEQUENZA STRATIGRAFICA** stanno **due** (posteriore a,
anteriore a). Il design (§4) leggeva «sequenza fisica = uguale a · si lega a».
**La geometria dice altro, e l'ontologia le dà ragione**: le dieci relazioni di
contatto sono tutte `AP11_has_physical_relation` (con `type_tag`), mentre
posteriore/anteriore sono ordinamento temporale (`P120_occurs_before` / `AP28`).
La definizione segue la geometria.

**Una seconda cosa misurata, e in disaccordo col design.** `AP13_has_stratigraphic_relation`
**non esiste** nel datamodel di s3Dgraphy 1.6.13: `grep` dà dieci occorrenze di
`AP11` e zero di `AP13`; `covers` non è un tipo di arco (si chiama `overlies`).
Le dodici caselle sono quindi **sette tipi di arco per due direzioni**, non
dodici tipi. Il test `test_ap13_is_not_in_the_datamodel` tiene la misura in
vista, perché se un giorno AP13 entra nel datamodel questa nota va riscritta.

Altezza totale del modello Word: **473 mm** contro 277 mm di altezza utile per
facciata A4. Il fronte-retro non è una preferenza: è aritmetica.

---

## 4 · Le etichette — dimostrato rompendolo

Nessuna etichetta viene da un dizionario generico: stanno nella definizione, per
lingua. Non c'è fallback fra lingue, per scelta.

`tests/fixtures/broken-missing-label.yaml` è la definizione minima con
l'etichetta italiana di `COPRE` **togliata via**. Due prove:

```
$ pytest tests/test_render.py::test_missing_label_refuses_instead_of_guessing
MissingLabel: field 'copre': no label declared for language 'it' (declared: [])
```

Il renderer **rifiuta**. E il validatore la prende prima:

```
field 'copre': no label for declared language 'it'. Labels live in the
definition, never in a generic dictionary: add labels.it or drop 'it' from
template.languages
```

Terza prova, sullo stesso principio: chiedere una lingua che la definizione non
dichiara non è una modalità degradata ma un errore —
`template 'iccd-us-2021' does not declare language 'fr' (declared: ['it', 'en'])`.

---

## 5 · Il modulo — tre soglie, tre catture

Stesso file di definizione, `mode="form"`:

| soglia | cattura | che cosa fa |
|---|---|---|
| telefono (390 px) | `docs/img/form-us-phone.png` | una colonna, le righe smettono di essere righe, campi da 40 px, intestazione appiccicata in alto, etichette di blocco orizzontali |
| tablet (834 px) | `docs/img/form-us-tablet.png` | **una facciata per volta**, con due bottoni fronte/retro |
| desktop 16:9 (1600×900) | `docs/img/form-us-desktop.png` | **due pagine affiancate** più la navigazione per paragrafi |

Una cattura in più: `docs/img/form-ue-demo-tablet.png`, la ficha spagnola sul
tablet — stesso codice, altra lingua, altri paragrafi.

**Il telefono si usa con una mano? A metà, e vale dirlo.** I campi sono alti
40 px e larghi tutto lo schermo, il pollice ci arriva; i radio button sono da
22 px. Ma i due bottoni fronte/retro stanno **in cima** allo schermo, e su un
telefono da 6,7 pollici la cima non è terreno del pollice. Un secondo difetto
onesto: la scheda ICCD ha 59 campi e in trincea, coi guanti sporchi, non se ne
compilano 59 — la scheda semplificata per il mobile è una **decisione di
dominio** (quali campi si riempiono davvero), non una media query, e questo
formato non la prende al posto di nessuno. Il modo di dichiararla c'è già
(un'altra definizione, con gli stessi id di campo).

Un difetto trovato e corretto durante la serata: al primo tentativo il tablet
apriva mostrando **entrambe** le facciate, perché la logica dei bottoni girava
solo al click. Un tablet che apre con due facciate ha smesso di essere «una
facciata per volta», quindi la logica ora gira anche al caricamento e al
cambio di soglia.

---

## 6 · Il secondo standard — e il diff è vuoto

`templates/es-ue-demo-2026/template.yaml`: 15 campi, spagnolo sorgente più
italiano, un paragrafo che l'ICCD **non ha** (GEORREFERENCIACIÓN: coordinate +
EPSG, dove la US 2021 ha solo le QUOTE), e una chiave umana di **forma diversa**
— `[yacimiento, contexto]`, senza area, contro `[localita, area, us]`.

È **inventata e lo dichiara** (`invented: true`): la stampa porta il bollo rosso
`FIXTURE` accanto al codice. Non avevamo la normativa spagnola vera, e citarne
una che non abbiamo letto sarebbe stato peggio.

Il diff dell'implementazione fra prima e dopo:

```
$ diff -ru /tmp/src-before-copy src && echo "(vuoto)"
(vuoto)
$ diff /tmp/src-before.sha /tmp/src-after.sha && echo "checksum identici"
checksum identici
```

Nove file Python, checksum identici. E perché resti vero domani:
`test_no_standard_is_named_in_the_implementation` cerca in `src/` i nomi dei due
standard e cinque nomi di campo (`iccd-us-2021`, `es-ue-demo-2026`,
`definizione`, `uguale_a`, `yacimiento`) e fallisce se ne trova uno.
L'unica eccezione dichiarata è `xsd_extract.py`, che *è* un lettore del dialetto
XSD dell'ICCD per definizione.

Stampata in due lingue: `out/ue-13-es.pdf`, `out/ue-13-it.pdf`.

---

## 7 · Il validatore — tre rotture, tre messaggi (e una quarta)

Sei definizioni rotte stanno in `tests/fixtures/`, ognuna con il suo cancello.

**1. Etichetta mancante** (`broken-missing-label`):

```
field 'copre': no label for declared language 'it'. Labels live in the
definition, never in a generic dictionary: add labels.it or drop 'it' from
template.languages
```

**2. Geometria** (`broken-geometry`) — due errori in un file:

```
sheet[recto].row[0]: cell widths add up to 125% of the line, which does not fit
on the page (cells: ['numero', 'copre'])
sheet[recto]: the declared rows are 280 mm tall but only 264 mm fit on a A4 side
(margins 12/12 mm plus 9 mm of running head): move fields to another side
```

**3. Un tipo di nodo che s3Dgraphy non ha** (`broken-unknown-node-type`):

```
field 'nota': graph node type 'InstitutionalActorNode' is not declared by
s3Dgraphy (node datamodel 1.6.4). Adding a node type is a decision, not a side
effect. Near: []
```

È un **errore**, non un avviso: `validate` esce con stato ≠ 0 e la definizione
non si usa.

E le altre tre, perché ognuna ha un suo motivo:

**4. UID derivato dalla chiave naturale** (`broken-uid-derived`):

```
template.identity: uid.derive_from_human_key: true is refused here. The UID is
minted by whoever creates the unit first; de-duplication between tools happens
by spotting a human identifier already in the context, not by making two tools
compute the same function. (A single tool may derive its own ids to find them
again on return; that is its own business, not a rule of this format.)
```

**5. Etichetta verticale in un blocco troppo basso** (`broken-rotated-label`):

```
sheet[verso].row[0].cell[0] block 'gruppo': the rotated label 'SEQUENZA
STRATIGRAFICA' (it) needs about 22 mm of height and the block is 10 mm: it would
print clipped. Raise the row or drop 'rotated'
```

Questo cancello non l'avevo previsto: l'ho scritto **dopo** aver visto la prima
stampa uscire con «QUENZA FISI» al posto di «SEQUENZA FISICA».

**6. Un campo senza paragrafo e senza casella** (`broken-orphan-field`):

```
field 'orfano': belongs to no paragraph
field 'orfano': has no box on the sheet: a field nobody can write into is not a field
```

**E la bozza estratta dall'XSD**: 257 campi con `verdict: undecided`, e il
validatore li rifiuta tutti e 257 (`test_the_draft_is_a_proposal_the_validator_refuses`).
Una bozza non può essere confusa con una definizione decisa.

### La regola di casa: i cancelli devono mordere

Ogni guardia è dimostrata su un caso che la fa scattare, e l'ho verificato
rompendo il codice, non sostituendo una stringa. Due note su questo, perché una
mi ha corretto:

* il cancello sul foglio (`test_nothing_spills_outside_the_printable_area` più
  la fixture `tight-nested`: quattro caselle da 25% dentro un blocco etichettato,
  senza un millimetro da regalare) **non mordeva** quando ho provato a
  reintrodurre il primo sospetto (`flex-basis` in percentuale). Misurato:
  overflow 0,00 px in entrambi i casi — quella modifica **non era** la causa, e
  ho corretto il commento nel codice che diceva il contrario. Rimettendo invece
  il difetto vero (la striscia dell'etichetta come *flex sibling*, che faceva
  risolvere le percentuali annidate contro la scatola sbagliata) il cancello
  scatta: **15,1 px = 4 mm fuori pagina**, su `componenti_organici` e sulla
  fixture. Ora morde;
* `test_no_permissive_third_mode` è nato rosso per una ragione vera: la funzione
  `from_snapshot` aveva il percorso come **valore di default**, valutato
  all'import, e il caso «non si può leggere niente» riusciva silenziosamente. È
  stato corretto nel codice, non nel test.

---

## 8 · L'estrattore XSD su SAS 3.00

```
$ stratigraph-templates extract-xsd '…/ICCD_normativa_SAS_3.00_102019.xsd' --code SAS --version 3.00
drafts/draft-sas-300.yaml — proposal, not truth
    records: 276                     ← riferimento: 276 ✓
    paragraphs: 19                   ← riferimento: 19 ✓
    structured_fields: 46
    simple_fields: 211               ← 46 + 211 = 257 campi
    records_with_alias: 276          ← riferimento: 276 su 276 ✓
    fields_with_vocabulary: 50       ← riferimento: 86 ✗ (vedi sotto)
    mandatory_fields: 30
    mandatory_paragraphs: 8          ← 30 + 8 = 38 ✓
    repeatable_fields: 41
    repeatable_paragraphs: 3         ← 41 + 3 = 44 ✓
    undecided_bindings: 257
```

Due differenze, e sono interessanti entrambe.

**Obbligatori e ripetibili tornano solo separando i paragrafi dai campi.**
`38` e `44` sono i numeri giusti *se* si contano anche i **paragrafi**: nell'XSD
un paragrafo può essere obbligatorio (8 lo sono) e ripetibile (3 lo sono). Il
mio conteggio li tiene distinti perché mettere insieme paragrafi e campi è
esattamente il modo in cui due conteggi onesti dello stesso file escono
diversi — e infatti il riferimento e il mio primo conteggio differivano di 8 e 3.
(Il `44` include anche il `maxOccurs="unbounded"` su `<xs:element ref="scheda">`?
No: quello è il 45° e non ha `id`, quindi non è un record della normativa.)

**I vocabolari sono 50, non 86, e la differenza non è un errore di conteggio: è
una definizione diversa di «campo con vocabolario».** Misurato con `grep` sullo
XSD: `binding_thesId` compare **50** volte, `linking_sourceType` (il rimando a
un authority file: AUT, BIB, DSC…) **51** volte, e le due insiemi si
sovrappongono su 7 elementi → unione **94**. Nessun `xs:enumeration` in tutto il
file. Quindi: `50` = i legami a un *thesaurus/vocabolario controllato*;
`94` = i legami a *qualunque* risorsa esterna controllata, authority file
compresi; `86` non è nessuno dei due, e viene da una sessione precedente il cui
metodo non è registrato. Il numero che questo repository produce è **50**, il
metodo è nel codice (`_own_fixed(el, "binding_thesId")`), e chi vuole gli 86 deve
dire quale insieme intende.

La bozza esce con **257 legami `undecided`** e il foglio dichiarato non-impaginato
(una riga per campo). Serve alle schede di catalogo e all'onboarding di una
normativa nuova; il legame al grafo lo decide una persona.

---

## 9 · L'allineamento fra vocabolari

**Dove si dichiara**: `vocabularies/alignments/*.yaml` — coppie
`source`/`target` con `match` (`exactMatch`, `closeMatch`, `broadMatch`,
`narrowMatch`), `status` (`proposed` | `verified`), `by`, `note`. Oggi contiene
cinque righe **finte** e dichiarate tali.

**L'esempio che il renderer usa davvero.** Nel dato della ficha spagnola il
valore di `definicion` è un **concetto**, non una parola:

```yaml
definicion:
  concept: "https://example.invalid/fixture/ue-definicion-es/estrato"
```

Stampando in spagnolo e in italiano, dallo stesso dato:

```
$ … print es-ue-demo-2026 --lang es --explain-vocab
    definicion: 'estrato'  ← scheme
$ … print es-ue-demo-2026 --lang it --explain-vocab
    definicion: 'strato'   ← alignment:exactMatch:fx-us-definizione-it
```

Nessuno ha scritto «strato» nel dato spagnolo: l'ha trovato l'allineamento. È il
caso in miniatura della ragione per cui questo tool può essere europeo invece che
italiano installato due volte.

Una nota di precisione che tengo perché è il punto: `derrumbe` è allineato a
`crollo` con **`closeMatch`**, non `exactMatch`, e il renderer lo dice
(`via=alignment:closeMatch`). «Estrato de derrumbe» e «strato di crollo» si
somigliano ma le due tradizioni di scavo li ritagliano diversamente, e un
formato che non sapesse dire la differenza fra i due gradi di corrispondenza
sarebbe un formato che invita a mentire.

**E i vocabolari veri sono referenziati, non copiati**: `iccd-ra-materia` punta
al file SKOS dell'ICCD dove sta (checkout `Standard-catalografici/`,
CC BY-SA 3.0 IT); il risolutore ne legge **2135 concetti** reali
(`test_a_real_iccd_skos_scheme_is_read_where_it_lives`). Per i cinque
vocabolari della scheda US da campo lo stato è `declared`: l'ICCD pubblica gli
strumenti terminologici in RDF per le schede di **catalogo**, non per i modelli
da campo, quindi il legame è dichiarato e il file non esiste — il giorno in cui
esce, si aggiunge `resolve:` e nient'altro.

---

## 10 · La suite, e lo stato del repository

```
$ .venv/bin/python -m pytest -q
45 passed in 6.5s
```

| file | che cosa tiene fermo |
|---|---|
| `test_registry.py` (5) | il registro si legge da s3Dgraphy; AP13 non c'è; nessuna terza modalità permissiva; l'istantanea è fedele |
| `test_validate.py` (10) | le sei rotture, la bozza `undecided`, i campi bloccati dichiarati |
| `test_render.py` (11) | le dodici caselle; il blob che non si spande; le etichette che rifiutano; stampa e modulo dalla stessa definizione; nessuno standard nominato nel codice |
| `test_vocab.py` (9) | concetto in due lingue, allineamento nei due sensi, exactMatch prima di closeMatch, SKOS ICCD vero |
| `test_xsd_extract.py` (3) | i numeri della SAS 3.00 e i 257 `undecided` |
| `test_print.py` (7) | una pagina per facciata dichiarata, A4 vero, niente fuori dalla pagina |

`git status --porcelain`: **il repository non è ancora un repository git** — il
`git init` è di E.D., come da consegna. Alberatura:

```
LICENSING.md  README.md  SPEC.md  pyproject.toml  .gitignore
docs/{questo referto, img/×4, us-3014-recto-verso-{it,en}.pdf, ue-13-demo-it.pdf}
drafts/draft-sas-300.yaml
examples/{us-3014-cencelle.yaml, ue-13-tarraco-demo.yaml}
registry/s3dgraphy-snapshot.json
src/stratigraph_templates/{__init__,model,loader,validate,registry,vocab,render,xsd_extract,cli}.py
templates/{iccd-us-2021,es-ue-demo-2026}/template.yaml
tests/{conftest,test_registry,test_validate,test_render,test_vocab,test_xsd_extract,test_print}.py
tests/fixtures/×8
tools/compare_us_table.py
vocabularies/{schemes/×8, alignments/×1, fixtures/×3}
out/  .venv/  *.egg-info/   ← ignorati
```

---

## 11 · Dove mi sono fermato, come chiesto

Tre cose che non ho deciso.

**1. L'attore istituzionale.** `ente_responsabile` e `ufficio_mic` sono enti, e
fra i 32 target ci sono solo `Author (human)` e `AI Author`. Non ho aggiunto
niente a s3Dgraphy. Ho invece aggiunto al formato un modo di **dirlo nel dato**:

```yaml
graph:
  verdict: none
  blocked_on:
    needs: "attore istituzionale (E39_Actor / E74_Group)"
    reported: "EM_design_setaccio-US §1 — decisione di E.D."
```

Il campo si compila e si stampa, e non entra nel grafo. `validate` li conta e li
stampa a ogni esecuzione, così la cosa non si dimentica. Sono tre in tutto: i
due enti e **`campionature`** (`CRMsci S13_Sample`: un campione di terreno non è
un Special Find — la voce «da decidere» del setaccio).

**2. La licenza del codice.** Le definizioni sono CC BY-SA 4.0 perché derivano
dalla norma ICCD, e i thesauri sono CC BY-SA 3.0 IT referenziati: questo strato
non è una scelta, è una conseguenza, e sta scritto in
[LICENSING.md](../LICENSING.md) e nel dato (`standard.attribution`). Per il
**codice** ho messo una **proposta**, EUPL-1.2 (progetto europeo, copyleft
debole, lista di compatibilità che include GPL-3.0 e CC BY-SA 4.0), dichiarata
come proposta in attesa di conferma. La licenza di un repository nuovo non è un
effetto collaterale della prima notte.

**3. Le due uscite chiedono la stessa cosa?** Sì, verificato: l'insieme dei
campi resi in stampa e nel modulo è lo stesso insieme (`test_print_and_form_come_from_the_same_definition`),
e non ho dovuto aggiungere un secondo file né una chiave «solo per la stampa».
Una differenza di **medium**, non di dato, l'ho gestita nel renderer e la
dichiaro: l'etichetta di un blocco è una striscia verticale sulla carta (dove lo
spazio non c'è) e un'intestazione orizzontale nel modulo (dove c'è). Stesso
`block_labels`, due rese.

### Il DAI, e la risposta strutturale

Un export **documento-per-record** come quello di `iDAI.field` entra: i dati di
un record sono un dizionario piatto `field_id → valore`, e una collezione di
documenti è una sequenza di `record:`, ognuno che dichiara a quale definizione
risponde. Quello che **non** entra automaticamente è la loro struttura di
categorie configurabile: quella va scritta **come una definizione** — cioè
esattamente il lavoro che questo formato permette di fare una volta invece che
per ogni strumento. Detto in una frase utile alla conversazione con Benjamin
Ducke: *noi non chiediamo al loro tool di cambiare modello; chiediamo che il
loro modello di scheda sia scrivibile come dato, e per la parte
documento-per-record lo è già.*

---

## 12 · Il seguito che questa notte ha guadagnato

* **USM 2021**: il `.doc` gemello è sullo stesso disco. Non chiede un nodo:
  chiede **CRMba** (leganti, paramenti, tecniche murarie, moduli), cioè
  un'ontologia intera. Con questo formato la definizione si scrive comunque, e
  i campi murari escono `blocked_on: CRMba` — la scheda si compila e si stampa
  mentre la decisione ontologica matura. È il caso d'uso che giustifica
  `blocked_on` meglio di quanto lo giustifichino i due enti.
* **La scheda semplificata per il mobile**: un'altra definizione con gli stessi
  id di campo, e una decisione di dominio da prendere in trincea, non qui.
* **`iccd-us-affidabilita` e i cinque schemi `declared`**: se all'ICCD esistono
  le liste dei termini (anche in PDF), diventano SKOS in mezza giornata e i
  cinque schemi passano a `resolvable` senza toccare la definizione.
* **La SAS da campo** (`SAS_modello per rilevamento sul campo_lug23.doc`): è un
  modello da campo, non la normativa XSD di catalogo, ed è il prossimo candidato
  naturale — insieme alla domanda che il setaccio ha già posto: quanto della
  scheda SAS è `metodo_di_scavo` che la US non ha.
