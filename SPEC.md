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
  standard: {...}             # chi lo pubblica, quale codice, quale versione
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

La distinzione `kind` non è decorativa: l'ICCD pubblica i **modelli per il
rilevamento sul campo** come documenti Word e le **normative di catalogo** come
XSD, e un tool da campo bersaglia i primi. Vedi §7.

### 1.2 · `identity` — l'identità è una COPPIA

```yaml
identity:
  human_key:
    fields: [localita, area, us]        # quali campi compongono l'ID umano
    pattern: "US {us} — {area} ({localita})"
  uid:
    policy: minted_by_creator           # unico valore ammesso
    opaque: true
    display: on_request
    derive_from_human_key: false        # deve essere false
  deduplication: by_human_key_in_context
```

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

Il registro viene letto da un s3Dgraphy importabile (installato, o
`$STRATIGRAPH_S3DGRAPHY_SRC`, o il checkout accanto a questo repository);
in mancanza, da `registry/s3dgraphy-snapshot.json`, che dichiara da dove è stato
preso. **Se non si può leggere nessuno dei due, non si valida niente**: non
esiste una terza modalità in cui ogni tipo va bene.

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
* `resolvable` = c'è un file SKOS. `skos_file` sta nel repository (solo
  *fixture*); `external_skos_file` sta sul disco, sotto
  `$STRATIGRAPH_ICCD_STANDARDS` (default `~/Documents/GitHub/Standard-catalografici`).

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

Ordine di risoluzione di un'etichetta: **schema proprio → allineamento
(`exactMatch` prima) → etichetta portata dal dato** (dichiarata come tale nel
tracciato `--explain-vocab`). Se nessuna delle tre strade dà una parola nella
lingua richiesta, il renderer **rifiuta**.

Questo campo esiste da subito, anche vuoto, per una ragione sola: un campo di
allineamento aggiunto fra un anno è un campo che nessuno riempirà.

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
  uid: "01J9Z7QK…"              # opaco
  values:
    us: "3014"
    copre: ["3018", "3020"]
    definizione: {concept: "…", label: "strato di crollo"}
    misure: [{qualia: thickness, label: "spessore max", value: "0,42", unit: "m"}]
  field_provenance:
    interpretazione: {state: human_validated, by: "ai:… · validato da …", ts: "…"}
```

Il file dei dati non è la scheda: dichiara solo quale definizione segue.

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
