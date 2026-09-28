# SPEC — che cos'è una definizione di scheda

Una **definizione** (in questo repository: un *template*) è un file dichiarativo,
versionato e citabile, che descrive una scheda di rilevamento archeologico in modo
che una macchina possa fare tre cose diverse con lo stesso dato:

1. mostrare un **modulo** da compilare,
2. stampare un **foglio A4 fronte-retro**,
3. dire al **grafo** che cosa significa ciò che è stato scritto.

Se queste tre cose vivono in tre posti diversi, si perde la coesione che rende la
scheda un dato; qui stanno in un file solo, e questa specifica dice come.

Chi legge questa pagina e guarda `templates/iccd-us-2021/template.yaml` deve
poter scrivere la scheda del proprio paese **senza chiedere niente a nessuno**.
Se serve leggere del codice, la specifica è sbagliata: apri una issue.

---

## 0 · Perché YAML

Due righe, come chiesto:

1. **I commenti sono parte del dato.** Una definizione registra dove la scheda e
   una tabella preesistente divergono, e perché una casella è stata letta così:
   JSON non ha commenti e quelle annotazioni finirebbero in un file a parte, cioè
   si perderebbero. YAML tiene commento e campo sulla stessa riga di sguardo.
2. **Si scrive a mano.** Testi lunghi (etichette normative di quaranta parole,
   note) stanno su più righe senza escape, e l'indentazione fa vedere la
   struttura a paragrafi che la scheda ha già sulla carta.

Il modello dei dati resta però **JSON-compatibile** (nessun tag YAML, nessuna
ancora, nessun tipo esotico): un consumatore che preferisce JSON converte con
`yaml.safe_load` + `json.dump` e non perde nulla tranne i commenti.

---

## 1 · Struttura di un file

```yaml
template:
  id: <slug>                  # = nome della cartella sotto templates/
  version: "1.0.0"            # la versione di QUESTA DEFINIZIONE (semver), §1.1
  standard: {...}             # chi lo pubblica, quale codice, quale versione della NORMA
  source_language: it         # la lingua della NORMA
  languages: [it, en]         # tutte le lingue in cui la scheda si può rendere
  identity: {...}             # la coppia identificativo umano / UID
  provenance: {...}           # la provenienza per campo
  vocabularies: [<scheme id>] # gli schemi di vocabolario a cui i campi rimandano
  paragraphs: [...]           # la SOSTANZA: come i campi si raggruppano
  fields: [...]               # la SOSTANZA + IL LEGAME AL GRAFO, campo per campo
  sheet: {...}                # IL FOGLIO: dove sta ogni casella
  notes: {...}                # libero: misure, provenienza della ricostruzione
```

### 1.1 · `standard`

| chiave | obbligo | significato |
|---|---|---|
| `authority` | sì | chi pubblica la norma (`ICCD`, `DAI`, …) |
| `code` | sì | il codice della scheda (`US`, `USM`, `SAS`) |
| `version` | sì | la versione della norma, come stringa (`"2021"`, `"3.00"`) |
| `kind` | sì | `field_model` (modello da campo) o `catalogue_record` (normativa di catalogo) |
| `title` | sì | titolo per lingua |
| `source` | no | da dove viene la ricostruzione |
| `license` | no | la licenza della NORMA (non del codice) |
| `attribution` | no | l'attribuzione da riportare |
| `invented` | no | `true` = definizione demo/inventata. La stampa porta il bollo `FIXTURE` |

#### `template.version` — la definizione ha una versione sua

`standard.version` è la versione della **norma** (`"2021"`, `"3.00"`). Non dice
niente della **definizione**: una correzione alla nostra lettura del modello ICCD
2021 — un verdetto rivisto, un'etichetta inglese migliore, una casella spostata —
non è una nuova norma, ed è comunque una definizione diversa. Quindi ogni
definizione porta, accanto a `id`, una versione propria:

| chiave | obbligo | significato |
|---|---|---|
| `version` | **sì** | semver `MAJOR.MINOR.PATCH` (con pre-release opzionale, `1.1.0-rc.1`) |

* **obbligatoria**: il validatore rifiuta una definizione senza, e una che
  scriva al suo posto l'anno della norma (`"2021"` non è semver). Una
  definizione senza versione non si compila (§9) e un record non la può citare;
* **come si alza**: MAJOR quando un record compilato con la versione precedente
  si leggerebbe diversamente (un verdetto cambiato, un campo tolto o rinominato,
  un tipo cambiato); MINOR quando si aggiunge senza cambiare il significato di
  ciò che c'era (una lingua, un campo facoltativo, un'opzione); PATCH per ciò che
  non tocca né i dati né il grafo (una nota, un aiuto, un refuso in un'etichetta);
* **una versione pubblicata non cambia**: `build` rifiuta di riscrivere
  `dist/schede/<id>/<versione>.json` con un contenuto diverso (§9.4). Se il
  digest cambia, cambia il numero.

Le demo inventate stanno sotto `1.0.0` (`0.x`): nessuno le cita.

La distinzione `kind` non è decorativa: l'ICCD pubblica i **modelli per il
rilevamento sul campo** come documenti Word e le **normative di catalogo** come
XSD, e un tool da campo bersaglia i primi. Vedi §7.

### 1.2 · `identity` — l'identità è una COPPIA

```yaml
identity:
  human_key:
    fields: [localita, area, us]        # quali campi compongono l'ID umano
    pattern: "US {us} — {area} ({localita})"
    unit_field: us                      # QUALE dei tre È l'unità (v. sotto)
  uid:
    policy: minted_by_creator           # unico valore ammesso
    opaque: true
    display: on_request
    derive_from_human_key: false        # deve essere false
  deduplication: by_human_key_in_context
```

#### `unit_field` — quale campo È l'unità, e perché va DICHIARATO

`fields` dice quali caselle **compongono** il nome. Non dice quale di esse sia
**l'unità** e quali il **contesto** che la disambigua, e sono due informazioni
diverse: chiunque debba rispondere a «di che unità è questa scheda» ha bisogno
della seconda — il modulo che la disegna, l'adattatore che la consegna a un
grafo, il validatore di una scheda compilata.

**Obbligatorio quando la chiave ha più di un campo.** Con un campo solo non c'è
niente da scegliere, dedurlo non è indovinare, e si può omettere. Con due o più,
una definizione che tace non è servibile e il validatore la rifiuta.

**Perché non si deduce.** Fino al 2026-09-23 un consumatore prendeva l'ULTIMO
campo della chiave, e su tre definizioni su tre era giusto. Poi è arrivata la
quarta:

```
iccd-us-2021      [localita, area, us]      → us          (l'ultimo)
es-ue-demo-2026   [yacimiento, contexto]    → contexto    (l'ultimo)
hu-rl-demo-2026   [retegszam, lelohely]     → retegszam   (il PRIMO)
```

In ungherese il determinante precede: «Réteg 12 · Castel Fontenova». Con la deduzione,
una scheda di strato sarebbe stata indirizzata **col nome del sito** — e
**nessuno se ne sarebbe accorto**, perché una chiave umana con il designatore
sbagliato non solleva niente: produce un'etichetta che sembra giusta e un
confronto che manca bersaglio. È il tipo di errore che si trova due anni dopo,
guardando perché due scavi «hanno la stessa unità».

**Una regolarità osservata su tre casi non è una regola.** Il designatore si
dichiara.



* l'**identificativo umano** (`US 3014`, `Contexto 13`) è quello che si scrive
  sulla busta e si urla in trincea. Quali campi lo compongono **dipende dallo
  standard**, e per questo lo dichiara la definizione, non il codice;
* l'**UID** è opaco e lo **conia chi crea l'unità per primo**. Non si mostra se
  non su richiesta.

`derive_from_human_key: true` è **rifiutato dal validatore**. La deduplicazione
fra strumenti si fa riconoscendo un identificativo umano già presente nel
contesto, non costringendo due strumenti a calcolare la stessa funzione. (Un
singolo strumento può derivare i propri id in modo deterministico per ritrovare
i propri nodi alla riconsegna: è un fatto suo, non una regola del formato.)

### 1.3 · `provenance` — la provenienza per campo

```yaml
provenance:
  per_field: true
  authors: [human, ai]
  states: [asserted, ai_drafted, human_validated]
  clock: s3dgraphy_crdt_field_clock
```

Un campo dettato in trincea e ripulito da un modello è scritto da un **autore
AI** e **può essere validato da un umano**: nei dati (`record.field_provenance`)
ogni campo può portare `state`, `by`, `ts`, e la stampa lo segna con un bollo
(`AI`, `AI✓`). Il meccanismo su cui questo si appoggia esiste già: `Clock(ts, by)`
per campo del CRDT di s3Dgraphy.

Questo **non** è il meccanismo `aux_volatile` del contratto: quello risponde alla
domanda della *residenza* (un dato che vive altrove), non a quella
dell'*autorialità*.

### 1.4 · `paragraphs`

Ogni campo appartiene a **esattamente un** paragrafo (il validatore lo verifica).
I paragrafi sono la struttura logica della scheda — quella che il modulo usa per
la navigazione e che la norma stampa in grassetto.

### 1.5 · `fields` — la sostanza

```yaml
- id: copre
  labels: {it: "COPRE", en: "COVERS"}
  type: unit_ref_list
  required: false
  repeatable: true
  max_len: "0,25"           # come lo scrive l'ICCD, se lo scrive
  help: {it: "…"}
  vocabulary: {scheme: <id>, binding: "VC_…", level_expr: "$1"}
  options: [...]            # solo per type: choice
  provenance: {enabled: true, authors: [human, ai]}
  graph: {...}              # vedi §2
  note: "…"                 # divergenze e ragioni, dentro il dato
```

**Le etichette sono un dizionario per lingua, dentro la definizione.** Non
esiste un file di traduzione generico e non esiste un fallback: chiedere una
lingua che la definizione non dichiara è un errore, non una modalità degradata.
È l'errore misurato nel generatore di pyarchinit-mini («Notifica» al posto di
FLOTTAZIONE) e non si ripete per costruzione.

#### Tipi di campo ammessi

| tipo | valore nei dati | note |
|---|---|---|
| `identifier` | stringa | l'ID umano o una sua parte |
| `text` | stringa | una riga |
| `longtext` | stringa | più righe |
| `integer`, `decimal` | numero | |
| `date` | `YYYY-MM-DD` | |
| `term` | `{concept: <uri>, label: <str>}` | **un concetto**, non una stringa (§3) |
| `term_list` | lista di quanto sopra | |
| `choice` | stringa = `options[].value` | caselle da barrare mutuamente esclusive |
| `checkbox` | booleano | una casella sola |
| `unit_ref_list` | lista di id di unità | le caselle dei rapporti (§2, verdetto `edge`) |
| `record_ref_list` | lista di id di schede | rimandi ad altre schede (RA, TMA…) |
| `resource_ref_list` | lista di nomi/riferimenti | piante, sezioni, fotografie |
| `person_ref` | `{name, ref}` | una persona |
| `actor_ref` | `{name, ref}` | un ente (§2, nota su `blocked_on`) |
| `epoch_ref`, `activity_ref` | stringa o `{ref}` | periodo, fase, attività |
| `quantity_list` | lista di `{qualia, label, value, unit}` | misure, quote, conteggi |

Regole verificate: `term`/`term_list` **devono** avere un `vocabulary`;
`unit_ref_list` **deve** avere verdetto `edge`; `choice` **deve** avere `options`
con etichette in tutte le lingue dichiarate.

### 1.6 · `recorded_in` — dove si compila quel campo

```yaml
- id: descrizione
  labels: {it: "DESCRIZIONE"}
  type: longtext
  recorded_in: trench       # trench | lab | unknown — assente = unknown
```

Tre valori e nessun quarto:

| valore | vuol dire |
|---|---|
| `trench` | si compila **durante l'atto di scavo**, da chi ha le mani nella terra |
| `lab` | si compila **dopo quell'atto** — laboratorio, ufficio, archivio |
| `unknown` | **la definizione non l'ha detto** — e questo è il default |

**Perché questi nomi.** `recorded_in` nomina un **luogo e un momento**, non un
rango: `priority` o `level` avrebbero detto che un campo da laboratorio conta
meno, e non è vero — è scritto in un altro momento, spesso da un'altra persona.
E `lab` è l'abbreviazione che la disciplina usa per «non mentre si scava»: non è
un'affermazione su una stanza, e un numero di catalogo compilato in ufficio è
`lab` come un'analisi al microscopio.

**Il default è quello che non promette niente.** Un campo senza `recorded_in` è
`unknown`, e un consumatore **non può** concluderne che sia da trincea. Se il
formato tace, tace: chi monta una scheda telefono su `unknown` sta inventando
una decisione che nessuno ha preso. Per la stessa ragione un valore che non è
uno dei tre è un **errore** e non un ripiego silenzioso su `unknown`: una
definizione che intendeva `trench` e ha scritto `Trench` sparirebbe dalla
scheda telefono senza che niente, in nessun posto, dica perché.

#### Come si decide — il criterio, e da dove viene

Il criterio **non è un'opinione di chi scrive questo formato**. Ha due basi, e
ognuna è citabile riga per riga.

**Base A — le parole che una persona dice sul campo.** In
`stratigraph-chatbot/app/tools.py` i sette intenti del field assistant sono nati
dalla **scheda da campo di Elisa Dalla Longa**: un cartoncino in forex con i
comandi vocali a colori, un artefatto di accessibilità che fa anche da specifica
dei comandi. Il file lo dice così: *«i comandi che ci sono sopra SONO gli
intenti, nelle parole che una persona dice con le mani nella terra.»* Quindi:
**un campo che uno degli intenti nomina — come slot o dentro una frase
riconosciuta — è un campo da trincea**, e la giustificazione è il numero di riga.

**Base B — le parole dello standard stesso.** Alcune schede lo dicono da sole.
La US ICCD 2021 ha `RESPONSABILE COMPILAZIONE SUL CAMPO` e `DATA RILEVAMENTO
SUL CAMPO` e, poche righe sotto, `DATA RIELABORAZIONE` e `RESPONSABILE
RIELABORAZIONE`: **è lo standard che distingue il campo dalla rielaborazione,
nelle proprie etichette.** Dove una scheda fa quella distinzione, è la sua a
valere.

Tutto il resto è `unknown`, e va lasciato `unknown`. Una manciata di campi
incerti dichiarati vale più di cinquantanove decisi da chi non scava.

**Citare la base è obbligatorio quanto il marcatore.** Un criterio senza la sua
provenienza diventa arbitrio alla prima discussione, quindi la definizione porta
la giustificazione in `note` sul campo, o nella `notes` della scheda quando
riguarda l'insieme.

#### È PER STANDARD, e le due schede di questo repository lo dimostrano

Non esiste un elenco universale di «campi da campo», e il formato non deve
suggerire che ci sia. La scheda spagnola avrà un altro sottoinsieme, deciso da
chi la scrive.

Misurato sulle due definizioni qui dentro: **le dieci caselle dei rapporti della
US ICCD 2021 sono `unknown`** — nessuno dei sette intenti le nomina — mentre le
**cinque della `ficha ES demo` sono `trench`**, perché l'autore di quella scheda
(demo) lo ha deciso. Stesso concetto, marcatore diverso, **e la differenza è la
base, non il concetto**. Se le due schede finissero con lo stesso sottoinsieme,
il marcatore starebbe descrivendo il nostro pregiudizio invece che lo standard.

#### Le due domande a cui serve rispondere

**Quali campi mostro sul telefono?** `template.recorded_in("trench")`. Il filtro
sta nel modello e non nel consumatore, perché un consumatore che filtra da sé è
una seconda lettura della stessa dichiarazione.

**Cosa succede a un campo obbligatorio che non è da trincea?** Una scheda
compilata in trincea è **incompleta per costruzione**, e non è un errore: è il
mestiere. `required` e `recorded_in` sono **ortogonali** di proposito, e insieme
rendono la distinzione calcolabile per campo:

| `required` | `recorded_in` | valore assente vuol dire |
|---|---|---|
| `true` | `trench` | **manca qualcosa**: era compilabile sullo scavo |
| `true` | `lab` | **incompleta per costruzione**, se la scheda è ancora di campo |
| `true` | `unknown` | **non si può decidere** — ed è la risposta onesta |

La terza riga è il motivo per cui `unknown` deve essere il default e non un
sinonimo di `lab`: «non lo so» e «si compila dopo» portano un validatore a due
conclusioni diverse, e una delle due assolverebbe una scheda incompleta senza
averne il diritto.

**Quello che questo formato NON può dire, e va detto qui:** la definizione rende
la distinzione calcolabile **per campo**, ma per applicarla serve sapere se
*quella scheda compilata* è ancora di campo o già rielaborata — e quello è uno
stato del **record**, non della definizione. Oggi un record (§5) non lo dichiara.
Un validatore di schede compilate, quando esisterà, avrà bisogno di quella sola
dichiarazione in più; il resto ce l'ha già.

---

## 2 · Il legame al grafo — i verdetti

Ogni campo dichiara che cosa **significa**. I verdetti ammessi sono sette:

| verdetto | vuol dire | chiavi obbligatorie |
|---|---|---|
| `identity` | è (parte di) l'identificativo umano | il campo deve stare in `identity.human_key` |
| `property` | è una proprietà di un nodo che esiste | `qualia` **oppure** `property_name` |
| `node_type` | **decide** il tipo di nodo | `node_types: {termine: NodeType}` |
| `node` | è un nodo a sé, raggiunto da un arco | `node_type` **e** `edge_type` |
| `edge` | è una relazione verso un'altra unità | `edge_type` **e** `direction` |
| `vocabulary` | è un termine controllato | il campo deve avere `vocabulary`; `qualia` opzionale |
| `none` | presentazione pura: la scheda lo dice, il grafo no | — |

Chiavi comuni: `attaches_to` (a che cosa si attacca, default `self` = l'unità
descritta dalla scheda), `target` (che cosa sta all'altro capo di un arco),
`note`, `blocked_on`.

### 2.1 · Il cancello: i nomi devono esistere

`node_type`, `edge_type` e `qualia` sono verificati contro **quello che
s3Dgraphy dichiara oggi** (datamodel dei nodi, datamodel delle connessioni, tipi
di qualia). Un nome che non esiste è un **errore**, non un avviso.

Non è pedanteria: è il modo in cui «non aggiungere tipi al datamodel» si fa
rispettare da sé. La crescita del datamodel è una decisione, non un effetto
collaterale di una definizione scritta di notte.

**La fonte è una sola: `registry/s3dgraphy-snapshot.json`.** È committato, quindi
è la stessa per chiunque; dichiara da dove è stato preso (commit di s3Dgraphy,
`git_dirty`, data) e con quali versioni (datamodel dei nodi, delle connessioni,
qualia, `em.ttl`). `validate` e `build` leggono **quello** — prima del
2026-10-18 `validate` leggeva il working tree di s3Dgraphy quando c'era e lo
snapshot quando no, e la stessa definizione era validata contro 1.6.19 su una
macchina e 1.6.13 su un'altra.

Il working tree di s3Dgraphy (`$STRATIGRAPH_S3DGRAPHY_SRC`, o il checkout accanto
a questo repository), quando c'è, serve a **una domanda sola**: lo snapshot è
ancora ciò che s3Dgraphy dichiara? Il confronto è sul **contenuto**, non sul
commit. Se divergono, il comando lo dice — con le differenze — e **si ferma**:
non sceglie da solo. Rigenerare (`registry-snapshot`) è la decisione, e il diff
di `registry/` ne è il documento. `--snapshot` salta il confronto, e la riga di
provenienza lo dichiara.

Oltre ai nomi, lo snapshot tiene ciò che serve per dire che cosa **produrre**
(§9): la grafia em.json di ogni classe (`DocumentNode` → `document`), il reverse
e la simmetria di ogni arco, i predicati RDF che l'esportatore di s3Dgraphy
emette per ciascuno (chiesti al suo codice, non riletti), i termini `em:`
dichiarati in `em.ttl`, e l'insieme chiuso delle operazioni CRDT. **Se lo
snapshot non c'è, non si valida niente**: non esiste una terza modalità in cui
ogni tipo va bene.

### 2.2 · `blocked_on` — quando la scheda dice più del grafo

```yaml
graph:
  verdict: none
  blocked_on:
    needs: "attore istituzionale (E39_Actor / E74_Group)"
    reported: "EM_design_setaccio-US §1 — decisione di E.D."
```

Un campo il cui legame onesto richiederebbe un tipo che s3Dgraphy non ha **non
viene silenziosamente degradato a presentazione**: porta scritto che cosa
servirebbe e a chi è stato riportato. Il verdetto deve essere `none` (finché la
decisione non c'è, il campo non atterra da nessuna parte) e `validate` li conta
e li stampa. Nella US 2021 sono tre: `ente_responsabile`, `ufficio_mic`
(l'attore istituzionale) e `campionature` (`CRMsci S13_Sample`).

### 2.3 · Gli archi hanno UNA direzione canonica

La scheda ha due caselle per la stessa relazione (`COPRE` e `COPERTO DA`); il
grafo ha un arco. Quindi:

```yaml
- id: copre        → {verdict: edge, edge_type: overlies, direction: outgoing}
- id: coperto_da   → {verdict: edge, edge_type: overlies, direction: incoming}
```

`direction: incoming` significa: l'arco canonico va **dall'unità citata a
questa**. `edge_type` deve essere una chiave del datamodel delle connessioni; i
nomi inversi (`is_overlain_by`) **non** sono tipi di arco e non si scrivono qui.

Misurato su s3Dgraphy 1.6.13: le dodici caselle della scheda US sono **sette
tipi di arco** per **due direzioni** — `equals`, `bonded_to`, `abuts`,
`overlies`, `cuts`, `fills` (tutti `AP11_has_physical_relation` con `type_tag`) e
`is_after` (`P120_occurs_before` / `AP28`).

---

## 3 · Il vocabolario, e l'allineamento fra paesi

Una definizione **riferisce** un thesaurus, non lo incorpora: un vocabolario ha
un ciclo di vita e una licenza propri. Gli schemi stanno in
`vocabularies/schemes/<id>.yaml`:

```yaml
scheme:
  id: iccd-ra-materia
  authority: ICCD
  labels: {it: "…", en: "…"}
  status: resolvable            # oppure: declared
  origin: external              # oppure: originated
  uri: "http://dati.beniculturali.it/vocabularies/…"
  license: "CC BY-SA 3.0 IT"
  attribution: "ICCD — MiC; …"
  binding_thes_id: "VC_MTC_RA"
  resolve:
    kind: external_skos_file    # oppure skos_file (dentro il repo)
    path: "strumenti-terminologici/…/….rdf"
```

* `declared` = la norma prescrive un vocabolario controllato, ma non esiste (o
  non è a portata) uno SKOS leggibile. È il caso dei modelli **da campo**
  dell'ICCD: gli strumenti terminologici in RDF coprono le schede di catalogo.
* `resolvable` = c'è un file SKOS. `skos_file` sta nel repository;
  `external_skos_file` sta sul disco, sotto `$STRATIGRAPH_ICCD_STANDARDS`
  (default `~/Documents/GitHub/Standard-catalografici`).

`status` e `origin` rispondono a due domande diverse e non vanno confusi.
`status` dice **posso risolverlo?**, `origin` dice **di chi è?**.

* `origin: external` (default) = è di altri. Lo dichiariamo, lo risolviamo dove
  sta, licenza e attribuzione sono loro, e un aggiornamento arriva da fuori.
* `origin: originated` = lo manteniamo noi. Porta un namespace proprio, una
  `version` propria e un dovere di citazione verso la fonte scientifica che
  riformula. Il validatore **pretende** `version`, `license` e `uri`: un modulo
  nostro senza una di quelle tre è incitabile, e un vocabolario incitabile non
  serve a nessuno. I file stanno in `vocabularies/skos/`, non in `fixtures/` —
  un modulo che scriviamo non è una prova.

Il primo modulo originato è `em-taph-weathering`: i sei stadi di alterazione
dell'osso di Behrensmeyer 1978, che sono lo standard *de facto* della tafonomia
da mezzo secolo e **non hanno mai avuto un identificatore**. I concetti sono un
fatto scientifico pubblicato; la prosa dell'autrice no, quindi le definizioni
sono **riformulate e non trascritte**, con la fonte su ogni concetto.

Dopo di lui, i cinque moduli della scheda US (`em-us-definizione`,
`em-us-consistenza`, `em-us-colore`, `em-us-stato-conservazione`,
`em-us-affidabilita`): l'ICCD prescrive un termine controllato per quelle caselle
e non ne ha pubblicato lo SKOS, quindi rispondono provvisoriamente per gli schemi
dichiarati `iccd-us-*` (§3.2). Stessa regola: un termine senza fonte non entra, e
la fonte è su ogni concetto (`dct:source`).

Il prefisso `em-` e il namespace `w3id.org/extendedmatrix` non sono un dettaglio
di naming. Un modulo `external` lo dichiariamo e basta, e se il progetto finisce
non succede niente a nessuno. Un modulo **originato** porta URI che altri
citeranno: se li appendiamo a StratiGraph, che ha una data di fine, nel 2029
sono orfani. Stanno quindi su Extended Matrix, che è l'ecosistema che sopravvive
al progetto; StratiGraph resta nell'`attribution`, che è il posto giusto per
dire dove e quando il modulo è nato. La pubblicazione è a
`extendedmatrix.org/vocab/<modulo>/`, con la sorgente qui: la copia pubblicata
porta in testa il commit da cui viene, perché due copie di un vocabolario
divergono e quella risolvibile che diventa vecchia è il guasto peggiore.

**Nel grafo finisce il CONCETTO** (l'URI SKOS), non l'etichetta: la risoluzione
etichetta-in-lingua avviene alla lettura. Se scrivi la stringa italiana nel
grafo, hai perso.

### 3.1 · L'allineamento

`vocabularies/alignments/*.yaml`:

```yaml
alignments:
  - source: {scheme: fx-ue-definicion-es, concept: "…/estrato"}
    match: exactMatch          # exactMatch | closeMatch | broadMatch | narrowMatch
    target: {scheme: fx-us-definizione-it, concept: "…/strato"}
    status: proposed           # proposed | verified
    by: "…"
    note: "…"
```

Ordine di risoluzione di un'etichetta: **schema proprio → schema provvisorio
(§3.2) → allineamento (`exactMatch` prima) → etichetta portata dal dato** (dichiarata come tale nel
tracciato `--explain-vocab`). Se nessuna delle tre strade dà una parola nella
lingua richiesta, il renderer **rifiuta**.

Questo campo esiste da subito, anche vuoto, per una ragione sola: un campo di
allineamento aggiunto fra un anno è un campo che nessuno riempirà.

### 3.2 · `provisional` — la norma dichiarata e chi risponde per lei

Uno schema `declared` dice che la norma prescrive un vocabolario che nessuno ha
pubblicato. Finché resta così, il widget scrive una parola senza concetto, e una
parola senza concetto non entra nel grafo (in s3Dgraphy `definition.rdf.label_only`
è `null`: nessuna tripla) e non si allinea a niente. Il rimedio non è cambiare lo
schema che il campo cita — **la norma è quella** — ma dire chi risponde per lei
nel frattempo:

```yaml
scheme:
  id: iccd-us-definizione
  status: declared
  provisional: em-us-definizione     # un modulo NOSTRO, finché l'ICCD non pubblica
```

* il campo continua a citare `iccd-us-definizione`; chi legge risolve con
  `em-us-definizione` (ordine: schema proprio → **provvisorio** → allineamento
  del provvisorio → etichetta portata dal dato; il tracciato dice
  `provisional:<id>`);
* la forma compilata (§9) lo scrive due volte, perché un consumatore non deve
  rileggere gli schemi: `vocabulary: {scheme, provisional}` sul campo e sulla voce
  della ricetta, e nella testata il provvisorio **subito dopo** lo schema che
  sostituisce (`provisional_for`), così chi vendora i vocabolari della testata
  vendora quello che risponde;
* **regole verificate** al caricamento degli schemi, e quindi da `validate` e da
  `build`: solo uno schema `declared` può avere `provisional` (uno `resolvable`
  risponde già da sé, e ne avrebbe due); il provvisorio deve esistere, essere
  `origin: originated` (è il nostro dovere di risposta, non quello di un terzo) e
  `resolvable`; un provvisorio non ha a sua volta un provvisorio;
* **il giorno che l'autorità pubblica**: `resolve:` sullo schema dichiarato, un
  allineamento `em-us-*` → `iccd-us-*` in `alignments/` (`exactMatch` dove lo è),
  e `provisional` si toglie. I concetti già scritti nei grafi restano validi: sono
  URI nostri, e l'allineamento li porta dall'altra parte.

### 3.3 · `unverified_languages` — operativi subito, corretti dopo

Un modulo originato serve in trincea in tutte le lingue dei partner prima che
qualcuno abbia potuto verificarle. La regola di E.D. per le traduzioni è
*operativi subito, correzione postuma dopo verifica*, e il formato la dice così:

```yaml
scheme:
  id: em-us-colore
  origin: originated
  unverified_languages: [en, ro, el, es, pl, he, de]   # etichette in bozza
```

* le etichette ci sono tutte (`skos:prefLabel` per lingua nel file SKOS) e si
  risolvono come le altre: una bozza è operativa;
* la lista dice quali lingue **nessuno che ne risponda** ha ancora verificato; la
  verifica di una lingua la toglie dalla lista, ed è un commit leggibile;
* solo un modulo `originated` la porta: uno schema esterno risponde delle proprie
  etichette.

**Perché per schema × lingua e non per etichetta.** s3Dgraphy marca la verifica
stringa per stringa (`validated_<lang>` in `datamodel_translations.json`), e lì
funziona perché ogni stringa è già un oggetto JSON. In SKOS un'etichetta è un
letterale: marcarla una per una vorrebbe dire reificarla (SKOS-XL), per moduli di
dieci o quaranta concetti che una persona rivede comunque una lingua alla volta.
Un meccanismo solo per tutta la suite: questo.

---

## 4 · Il foglio — A4 fronte-retro

Il foglio è una griglia di righe e celle, per facciata:

```yaml
sheet:
  page: A4
  margins_mm: {top: 10, right: 12, bottom: 10, left: 12}
  sides:
    - id: recto                 # recto | verso
      labels: {it: "fronte", en: "recto"}
      rows:
        - h: 15                 # altezza in MILLIMETRI
          cells:
            - {field: ufficio_mic, w: 53.4}    # larghezza in % della riga
            - {field: identificativo_riferimento, w: 46.6}
```

Una cella è una di tre cose:

* **un campo**: `{field: <id>, w: <%>, label: auto|none}`;
* **un blocco**: una griglia annidata, con o senza etichetta propria —
  `{block: <id>, block_labels: {...}, rotated: true, w: <%>, rows: [...]}`.
  `rotated: true` disegna l'etichetta in verticale su una striscia a sinistra,
  come fa la scheda ICCD per SEQUENZA FISICA e SEQUENZA STRATIGRAFICA. I blocchi
  si annidano, e questo dà la potenza dei `rowspan` senza avere i rowspan;
* **uno spazio**: `{w: <%>}` senza `field` né `rows`.

Regole verificate:

* la somma delle `w` di una riga non supera 100;
* ogni campo ha **esattamente una** casella (un campo in cui nessuno può
  scrivere non è un campo; due caselle per lo stesso campo sono un errore);
* le facciate si chiamano `recto` e `verso`, e non si ripetono;
* **l'altezza dichiarata di una facciata deve stare in una facciata A4** (297 mm
  meno i margini meno 9 mm di intestazione corrente);
* un'etichetta ruotata deve stare nell'altezza del suo blocco, altrimenti
  stamperebbe tagliata.

L'altezza di una riga è un **minimo di progetto**, non una ghigliottina: se un
dato è più alto della casella, la casella cresce e il comando dice quante pagine
è costato (`2 side(s) → 3 page(s)`). Non si taglia mai ciò che qualcuno ha
scritto.

---

## 5 · I dati

```yaml
record:
  template: iccd-us-2021
  template_version: "1.0.0"     # OBBLIGATORIO: quale versione della definizione ha seguito
  uid: "01J9Z7QK…"              # opaco
  values:
    us: "3014"
    copre: ["3018", "3020"]
    definizione: {concept: "…", label: "strato di crollo"}
    misure: [{qualia: thickness, label: "spessore max", value: "0,42", unit: "m"}]
  field_provenance:
    interpretazione: {state: human_validated, by: "ai:… · validato da …", ts: "…"}
```

Il file dei dati non è la scheda: dichiara solo quale definizione segue, **e in
quale versione** (`template` + `template_version`, la coppia che §9 usa per
archiviare la forma compilata). Senza la versione, rileggere un record vorrebbe
dire indovinare con quale ricetta è stato scritto. `print` e `form` rifiutano un
record di un'altra definizione e segnalano una versione diversa.

---

## 6 · Che cosa NON c'è, per scelta

Nessun server, nessuna autenticazione, nessuna sessione, nessun database.
Nessuna matrice di Harris (l'editor di grafo è EMStudio). Nessun GIS (è di
pyarchinit). Nessun record di catalogo ministeriale (è del Catalog, come
proiezione, più tardi). Nessun tipo nuovo in s3Dgraphy. Nessuna gestione di
asset (esistono già: SHA-256 + IIIF). Nessuna identità, coda offline o ingresso
in stanza (esistono già, provati nel field assistant).

---

## 7 · La bozza estratta da un XSD

`stratigraph-templates extract-xsd <file.xsd> --code SAS --version 3.00` legge
una normativa di catalogo ICCD e **propone** una definizione: struttura,
paragrafi, alias, obbligatorietà, ripetibilità, legami ai vocabolari.

Due cose non ci sono e non possono esserci:

* **il legame al grafo**: ogni campo esce con `verdict: undecided`, e il
  validatore **rifiuta** una definizione che porti ancora quel marcatore. Lo
  decide una persona;
* **il foglio**: un XSD non dice dove sta una casella. La bozza mette una riga
  per campo perché non si perda nulla, e lo dichiara.

## 8 · Un export documento-per-record (iDAI.field)

Il formato descrive una scheda, non un archivio, e i dati di un record sono un
dizionario piatto di `field_id → valore`. Un export documento-per-record — come
quello di `iDAI.field` / Field Desktop, che replica **a livello di documento**
mentre qui si replica a livello di **campo** — entra come una sequenza di
`record:`, uno per documento, purché il produttore dichiari a quale definizione
ciascun documento risponde. Ciò che *non* entra automaticamente è la loro
struttura di categorie configurabile: quella va scritta come una definizione
(che è precisamente il lavoro che questo formato rende possibile fare una volta e
non per ogni tool).

---

## 9 · La forma compilata — `stratigraph-templates build`

Una definizione in YAML è fatta per chi la scrive. Un programma che la usa —
StratiField che disegna il modulo e, a scheda compilata, **manda le operazioni
alla stanza** — ha bisogno di un'altra cosa: un file che prende e usa **senza
leggerla in tempo reale**, che non cambia sotto i piedi, e che dice contro quale
s3Dgraphy è stato verificato. `build` lo produce. È lo stesso patto del tema
(`sync-brand.sh`) e dei datamodel (`sync-datamodels.sh`): **qui si produce,
l'app vendora e committa la copia**.

```
dist/schede/index.json                   ogni definizione, ogni versione, digest, datamodel
dist/schede/<id>/<versione>.json         la definizione compilata
```

`dist/` è versionata nel repository, e un test verifica che corrisponda a ciò
che le definizioni compilano oggi: una definizione modificata senza `build`
lascerebbe alle app una copia vecchia che sembra ufficiale.

**Chi non compila.** `build` compila ciò che valida (§1–§4): una definizione
senza `version`, o con un verdetto `undecided` (la bozza di un XSD, §7), non
compila; le altre sì, e il comando esce con errore se anche una sola è stata
rifiutata.

### 9.1 · La testata

```json
"header": {
  "id": "iccd-us-2021",
  "version": "1.0.0",
  "standard": {"authority": "ICCD", "code": "US", "version": "2021", "kind": "field_model",
               "title": {...}, "license": "CC BY-SA 4.0", "invented": false, ...},
  "source_language": "it",
  "languages": ["it", "en"],
  "vocabularies": [{"id": "iccd-us-consistenza", "status": "declared", ...}, ...],
  "digest": "sha256:<64 hex>",
  "datamodel": {"nodes": "1.6.8", "connections": "1.6.19", "qualia": "1.6.1",
                "em_ttl": "1.6.2", "s3dgraphy": "1.6.0.dev20",
                "taken_from": {"git_commit": "8b91867…", "git_dirty": false},
                "snapshot": "registry/s3dgraphy-snapshot.json"},
  "compiled_by": {"name": "stratigraph-templates", "version": "0.1.0"}
}
```

`datamodel` è **letto dallo snapshot** (§2.1), che a sua volta l'ha letto dai file
di configurazione di s3Dgraphy: nessuna versione è scritta a mano.

**Il digest** è SHA-256 sul JSON canonico (chiavi ordinate, nessuno spazio) del
documento **senza** `digest`, `datamodel` e `compiled_by`. Quindi:

* ricompilare la stessa definizione dà lo stesso digest, byte per byte;
* cambiare la definizione — anche solo un'etichetta — cambia il digest;
* ricompilare contro un datamodel più recente **che non cambia la ricetta**
  lascia il digest com'è (la riga `datamodel` si aggiorna); un datamodel che la
  cambia — un arco rinominato, una grafia em.json diversa — cambia il digest,
  perché la ricetta è dentro.

### 9.2 · La metà visiva

Ciò che serve a un modulo e a un foglio, così com'è nella definizione:
`identity` (chiave umana, `pattern`, `unit_field` risolto, politica dell'UID),
`provenance`, `paragraphs`, `fields` (tipo, `required`, `repeatable`,
`recorded_in`, `max_len`, etichette **in tutte le lingue dichiarate**, `help`,
`options`, `vocabulary`, `note`, e il paragrafo di appartenenza), `sheet` com'è,
`notes`. Nessuna etichetta di ripiego: se una lingua è dichiarata, c'è.

### 9.3 · La metà ontologica — la ricetta

Per ogni campo, **che cosa produrre nel vocabolario delle cinque operazioni CRDT
di s3Dgraphy** — `add_node`, `update_field`, `remove_node`, `add_edge`,
`remove_edge` (`s3dgraphy/crdt.py:66`, `api.make_op`) — e **nessun valore**.
L'orchestratore è StratiGraph Server: chi entra in una stanza manda operazioni,
la stanza le applica con `em.apply_op` e le rilancia. Una ricetta che dicesse
«fai questo grafo» avrebbe bisogno di un applicatore accanto alla stanza, fuori
dall'orchestrazione; questa dice **quali operazioni mandare**.

Una voce ha dei **passi**; un passo `emit`-te un'operazione nella forma esatta
del filo (quella di `crdt.apply_op_to_section`), con **riferimenti** dove andrà
un valore:

| riferimento | che cos'è |
|---|---|
| `$unit` | l'unità che la scheda descrive |
| `$value`, `$value.<k>` | il valore del campo; una sua chiave (`$value.concept`, `$value.name`) |
| `$item`, `$item.<k>` | un elemento di un valore lista (la voce ha `each: true`: i passi si ripetono per elemento) |
| `$node` | il nodo che il passo trova o crea (vedi `resolve`) |
| `$prop` | la PropertyNode che il passo conia |
| `$field.<id>.prop` | la PropertyNode coniata dalla voce di un ALTRO campo (la voce ha `after: [<id>]`) |
| `$anchor.<nome>` | qualcosa che la definizione nomina e non definisce (vedi `open`) |

`when: created` su un passo = mandalo solo se `resolve` ha **creato** il nodo
invece di trovarlo. Gli **id li conia chi crea** (`identity.uid.policy`): la
ricetta non ne scrive mai uno. `name` e `description` di un nodo em.json sono
stringhe: chi sostituisce un valore numerico lo scrive come testo.

**L'unità** (`recipe.unit`) si trova per chiave umana nel contesto
(`identity.deduplication`) o si crea con un `add_node`; il suo `node_type` lo
decide il campo con verdetto `node_type`, se c'è. Si decide **alla creazione**:
`update_field` indirizza solo `name`, `description` e `data.*`
(`crdt.py:749`), quindi il tipo di un'unità esistente non si cambia con
un'operazione di questo vocabolario — e la ricetta lo dice.

**Verdetto per verdetto:**

| verdetto | passi |
|---|---|
| `identity` | nessuno: il campo compone il nome dell'unità (`names: $unit`, `designator`) |
| `none` | **nessuno**, dichiarato: `reason`, oppure `blocked_on` |
| `node_type` | nessuno: `decides: unit.node_type` + la tabella valore → `{class, node_type}` |
| `property`, nome nativo | `update_field {node_id: $unit, field: description, value: $value}` |
| `property`, **elemento del nodo** | `update_field {node_id: $unit, field: <em_json dell'elemento>, value: $value}` — oggi `definition` → `data.definition` (v. sotto) |
| `property`, altrimenti | `add_node` PropertyNode + `add_edge has_property` (v. sotto) |
| `vocabulary` | come `property`, con `property_type` = la qualia e **valore = il concetto** (`$value.concept`, §3) |
| `node` | `add_node` (`when: created`) del nodo trovato per nome/ref + `add_edge` nella direzione dichiarata |
| `edge` | un `add_edge` per elemento; `outgoing` = `$unit → $item`, `incoming` = `$item → $unit` |

**La proprietà: la forma che s3Dgraphy e EMStudio usano davvero**, non una
nuova:

```json
{"op": "add_node", "node": {"id": "$prop", "node_type": "property", "name": "texture",
                            "description": "$value.concept",
                            "data": {"property_type": "texture"}}}
{"op": "add_edge", "edge_type": "has_property", "source": "$unit", "target": "$prop"}
```

* PropertyNode con `name` = `data.property_type` = la qualia, appesa al soggetto
  con `has_property` **dal soggetto alla proprietà**: EMStudio
  `frontend/src/model.ts:924-938` e `frontend/src/em-data.ts:605-632`
  (`addQualiaClaim`), s3Dgraphy `importer/base_importer.py:666-713`
  (`_create_property`) e `importer/unified_xlsx_importer.py:612-639`
  (`_handle_qualia`);
* **il valore sta in `description`**: è la convenzione che EMStudio dichiara
  (`model.ts:924`, «A PropertyNode's VALUE lives in `description`») e che
  `_create_property` e `addQualiaClaim` seguono; `_handle_qualia` lo mette in
  `value` (sollevato in `data.value` da `emjson_exporter.py:60`). Le due grafie
  convivono oggi in s3Dgraphy; la ricetta segue quella dell'orchestrato;
* **le unità di misura** in `data.units` (`_handle_qualia`, `:632`);
* un `quantity_list` fa **una PropertyNode per riga**, con la qualia della riga
  (`$item.qualia`, e `defaults` se il campo ne dichiara una);
* `property_name: description` è il **campo del nodo** e diventa `update_field`
  su `description` (audit B9: finiva in `data.<id della casella>`);
* un `property_name` che il datamodel dei nodi dichiara come **elemento del
  nodo** (`properties.<nome>` con `kind: node_element`, oggi solo
  `StratigraphicNode.properties.definition`, nodi 1.6.9) **non** è una qualia:
  diventa un `update_field` sul posto em.json che il datamodel nomina
  (`data.definition`), con il valore **intero** (`$value` = `{concept, label}`),
  e la voce porta `element: {name, declared_on, value, rdf}`. Nome, posto e RDF
  vengono dallo snapshot (`node_elements`, formato 3), non da questo repository.
  Il compilatore rifiuta un tipo di campo che non scrive quel valore (un
  `concept` lo scrive solo un `term`) e un tipo di unità che non eredita
  l'elemento (decisione di E.D., 2026-10-21: la DEFINIZIONE della US è un
  elemento del nodo);
* un `property_name` che non è una qualia registrata diventa comunque una
  PropertyNode con quel `property_type` — è ciò che fa `_create_property` con i
  nomi di colonna — e la voce lo dichiara (`registered_qualia: false`).

**Un nodo raggiunto da un arco** si trova prima di crearsi: per nome
(`LocationNodeGroup`, `EpochNode`…), per `ref` e poi nome (`person_ref`,
`epoch_ref`), per **percorso** se è un riferimento a file (`resource_ref_list` →
DocumentNode con `data.url` = il riferimento, deduplicato per percorso come
`pyarchinit_importer._add_path_document`, `:797-808`). Un `longtext` è un
**contenuto**, non un nome: il nodo si conia e lo porta in `description`.

**Gli archi.** `edge_type` è la chiave del datamodel delle connessioni, cioè la
forma canonica; `edge` riporta ciò che s3Dgraphy dichiara di quell'arco —
`symmetric`, `reverse`, e l'RDF **che l'esportatore di s3Dgraphy emette**
(`exporter/rdf_exporter.py:199`, `:300`, `:332`: predicato, sottoproprietà AP11,
estensione, `subject: target` quando la mappatura inverte). `same_rdf_as` elenca
gli altri tipi d'arco che diventano **la stessa proprietà**: `bonded_to` ≡
`is_bonded_to` (`em:bondedTo`), `equals` ≡ `is_physically_equal_to`
(`em:physicallyEquals`, `em.ttl:528`, `:536`). Entrambi i nomi sono validi e la
definizione ICCD usa le forme che il datamodel chiama canoniche; il compilato lo
dice, così un consumatore non raddoppia le frecce.

**`open` — ciò che la definizione non decide, dichiarato.** La ricetta non
inventa: dove la definizione tace, lo scrive. Oggi, per la US ICCD:
`definizione` (verdetto `vocabulary` senza qualia né `property_name`: nessuna
operazione finché non lo dice), e tre `attaches_to` che nominano atti non
definiti (`excavation_activity`, `recording_act`, `revision_act` →
`$anchor.<nome>`, in `recipe.anchors`). Per le due demo, anche il tipo dell'unità
(nessun campo `node_type`). Il compilatore **rifiuta** invece ciò che è
incoerente: un `attaches_to: property:<x>` che nessun campo produce, un nome che
non ha grafia em.json, un arco deprecato o la cui proprietà RDF `em:` non è in
`em.ttl`, un'operazione fuori dalle cinque.

### 9.4 · Le versioni pubblicate non cambiano

`build` rifiuta di riscrivere `dist/schede/<id>/<versione>.json` se il nuovo
digest è diverso da quello già scritto: **alza `template.version`**. Lo stesso
digest riscrive il file (la riga `datamodel` può essersi aggiornata) e lo dice.
L'indice elenca ogni versione presente e la più recente (`latest`, ordine
semver): le versioni vecchie restano, perché un record compilato con una di
esse va riletto con quella.
