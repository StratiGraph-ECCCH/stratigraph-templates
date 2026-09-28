# SPEC — what a recording-sheet definition is

A **definition** (in this repository: a *template*) is a declarative, versioned and
citable file that describes an archaeological recording sheet so that a machine can do
three different things with the same data:

1. show a **form** to fill in,
2. print a **double-sided A4 sheet**,
3. tell the **graph** the meaning of what has been written.

If these three things live in three different places, the cohesion that makes the
recording sheet data is lost; here they sit in a single file, and this specification says how.

Anyone who reads this page and looks at `templates/iccd-us-2021/template.yaml` must
be able to write their own country's recording sheet **without asking anyone anything**.
If you need to read code, the specification is wrong: open an issue.

---

## 0 · Why YAML

Two lines, as requested:

1. **Comments are part of the data.** A definition records where the recording sheet and
   a pre-existing table diverge, and why a box was read the way it was:
   JSON has no comments, and those annotations would end up in a separate file, that is,
   they would be lost. YAML keeps comment and field within the same glance.
2. **It is written by hand.** Long texts (forty-word labels from the standard,
   notes) sit on several lines without escaping, and indentation shows the
   paragraph structure the sheet already has on paper.

The data model nonetheless stays **JSON-compatible** (no YAML tags, no
anchors, no exotic types): a consumer who prefers JSON converts with
`yaml.safe_load` + `json.dump` and loses nothing except the comments.

---

## 1 · Structure of a file

```yaml
template:
  id: <slug>                  # = name of the folder under templates/
  version: "1.0.0"            # the version of THIS DEFINITION (semver), §1.1
  standard: {...}             # who publishes it, which code, which version of the STANDARD
  source_language: it         # the language of the STANDARD
  languages: [it, en]         # all the languages the sheet can be rendered in
  identity: {...}             # the human identifier / UID pair
  provenance: {...}           # per-field provenance
  vocabularies: [<scheme id>] # the vocabulary schemes the fields refer to
  paragraphs: [...]           # the SUBSTANCE: how fields are grouped
  fields: [...]               # the SUBSTANCE + THE GRAPH BINDING, field by field
  sheet: {...}                # THE SHEET: where every box sits — optional, §4.1
  notes: {...}                # free: measurements, provenance of the reconstruction
```

### 1.1 · `standard`

| key | required | meaning |
|---|---|---|
| `authority` | yes | who publishes the standard (`ICCD`, `DAI`, …) |
| `code` | yes | the code of the recording sheet (`US`, `USM`, `SAS`) |
| `version` | yes | the version of the standard, as a string (`"2021"`, `"3.00"`) |
| `kind` | yes | `field_model` (field model) or `catalogue_record` (catalogue standard) |
| `title` | yes | title per language |
| `source` | no | where the reconstruction comes from |
| `license` | no | the licence of the STANDARD (not of the code) |
| `attribution` | no | the attribution to be reproduced |
| `invented` | no | `true` = demo/invented definition. The print carries the `FIXTURE` stamp |

#### `template.version` — the definition has a version of its own

`standard.version` is the version of the **standard** (`"2021"`, `"3.00"`). It says
nothing about the **definition**: a correction to our reading of the ICCD 2021 model —
a revised verdict, a better English label, a moved box —
is not a new standard, and it is still a different definition. So every
definition carries, next to `id`, a version of its own:

| key | required | meaning |
|---|---|---|
| `version` | **yes** | semver `MAJOR.MINOR.PATCH` (with optional pre-release, `1.1.0-rc.1`) |

* **mandatory**: the validator rejects a definition without it, and one that
  writes the year of the standard in its place (`"2021"` is not semver). A
  definition without a version does not compile (§9) and a record cannot cite it;
* **how it is bumped**: MAJOR when a record compiled with the previous version
  would read differently (a changed verdict, a field removed or renamed,
  a changed type); MINOR when something is added without changing the meaning of
  what was there (a language, an optional field, an option); PATCH for what
  touches neither the data nor the graph (a note, a help text, a typo in a label);
* **a published version does not change**: `build` refuses to rewrite
  `dist/schede/<id>/<versione>.json` with different content (§9.4). If the
  digest changes, the number changes.

Invented demos sit below `1.0.0` (`0.x`): nobody cites them.

The `kind` distinction is not decorative: the ICCD publishes its **models for
field recording** as Word documents and its **catalogue standards** as
XSD, and a field tool targets the former. See §7.

### 1.2 · `identity` — identity is a PAIR

```yaml
identity:
  human_key:
    fields: [localita, area, us]        # which fields make up the human ID
    pattern: "US {us} — {area} ({localita})"
    unit_field: us                      # WHICH of the three IS the unit (see below)
  uid:
    policy: minted_by_creator           # the only allowed value
    opaque: true
    display: on_request
    derive_from_human_key: false        # must be false
  deduplication: by_human_key_in_context
```

#### `unit_field` — which field IS the unit, and why it must be DECLARED

`fields` says which boxes **make up** the name. It does not say which of them is
**the unit** and which are the **context** that disambiguates it, and those are two
different pieces of information: anyone who has to answer “which unit is this sheet about” needs
the second — the form that draws it, the adapter that hands it to a
graph, the validator of a compiled sheet.

**Mandatory when the key has more than one field.** With a single field there is
nothing to choose, deducing it is not guessing, and it can be omitted. With two or more,
a definition that stays silent cannot be served and the validator rejects it.

**Why it is not deduced.** Until 2026-09-23 a consumer took the LAST
field of the key, and on three definitions out of three it was right. Then the
fourth arrived:

```
iccd-us-2021      [localita, area, us]      → us          (the last)
es-ue-demo-2026   [yacimiento, contexto]    → contexto    (the last)
hu-rl-demo-2026   [retegszam, lelohely]     → retegszam   (the FIRST)
```

In Hungarian the determiner comes first: “Réteg 12 · Castel Fontenova”. With deduction,
a layer sheet would have been addressed **by the name of the site** — and
**nobody would have noticed**, because a human key with the wrong designator
raises nothing: it produces a label that looks right and a
comparison that misses its target. It is the kind of error you find two years later,
looking into why two excavations “have the same unit”.

**A regularity observed on three cases is not a rule.** The designator is
declared.



* the **human identifier** (`US 3014`, `Contexto 13`) is the one written
  on the bag and shouted across the trench. Which fields make it up **depends on the
  standard**, and that is why the definition declares it, not the code;
* the **UID** is opaque and is **minted by whoever creates the unit first**. It is not shown
  unless requested.

`derive_from_human_key: true` is **rejected by the validator**. Deduplication
across tools is done by recognising a human identifier already present in the
context, not by forcing two tools to compute the same function. (A
single tool may derive its own ids deterministically in order to find
its own nodes again on re-delivery: that is its own business, not a rule of the format.)

### 1.3 · `provenance` — per-field provenance

```yaml
provenance:
  per_field: true
  authors: [human, ai]
  states: [asserted, ai_drafted, human_validated]
  clock: s3dgraphy_crdt_field_clock
```

A field dictated in the trench and cleaned up by a model is written by an **AI
author** and **can be validated by a human**: in the data (`record.field_provenance`)
every field can carry `state`, `by`, `ts`, and the print marks it with a stamp
(`AI`, `AI✓`). The mechanism this rests on already exists: the per-field `Clock(ts, by)`
of the s3Dgraphy CRDT.

This is **not** the `aux_volatile` mechanism of the contract: that one answers the
question of *residence* (a piece of data that lives elsewhere), not that
of *authorship*.

### 1.4 · `paragraphs`

Every field belongs to **exactly one** paragraph (the validator checks it).
Paragraphs are the logical structure of the recording sheet — the one the form uses for
navigation and that the standard prints in bold.

### 1.5 · `fields` — the substance

```yaml
- id: copre
  labels: {it: "COPRE", en: "COVERS"}
  type: unit_ref_list
  required: false
  repeatable: true
  max_len: "0,25"           # as the ICCD writes it, if it writes it
  help: {it: "…"}
  vocabulary: {scheme: <id>, binding: "VC_…", level_expr: "$1"}
  options: [...]            # only for type: choice
  provenance: {enabled: true, authors: [human, ai]}
  graph: {...}              # see §2
  note: "…"                 # divergences and reasons, inside the data
```

**Labels are a dictionary per language, inside the definition.** There is
no generic translation file and there is no fallback: asking for a
language the definition does not declare is an error, not a degraded mode.
It is the error measured in the pyarchinit-mini generator (“Notifica” in place of
FLOTTAZIONE) and it cannot recur, by construction.

#### Allowed field types

| type | value in the data | notes |
|---|---|---|
| `identifier` | string | the human ID or a part of it |
| `text` | string | one line |
| `longtext` | string | several lines |
| `integer`, `decimal` | number | |
| `date` | `YYYY-MM-DD` | |
| `term` | `{concept: <uri>, label: <str>}` | **a concept**, not a string (§3) |
| `term_list` | list of the above | |
| `choice` | string = `options[].value` | mutually exclusive tick boxes |
| `checkbox` | boolean | a single box |
| `unit_ref_list` | list of unit ids | the relationship boxes (§2, verdict `edge`) |
| `record_ref_list` | list of sheet ids | references to other sheets (RA, TMA…) |
| `resource_ref_list` | list of names/references | plans, sections, photographs |
| `person_ref` | `{name, ref}` | a person |
| `actor_ref` | `{name, ref}` | an institution (§2, note on `blocked_on`) |
| `epoch_ref`, `activity_ref` | string or `{ref}` | period, phase, activity |
| `quantity_list` | list of `{qualia, label, value, unit}` | measurements, elevations, counts |

Checked rules: `term`/`term_list` **must** have a `vocabulary`;
`unit_ref_list` **must** have verdict `edge`; `choice` **must** have `options`
with labels in all declared languages.

### 1.6 · `recorded_in` — where that field is filled in

```yaml
- id: descrizione
  labels: {it: "DESCRIZIONE"}
  type: longtext
  recorded_in: trench       # trench | lab | unknown — absent = unknown
```

Three values and no fourth:

| value | it means |
|---|---|
| `trench` | filled in **during the act of excavation**, by whoever has their hands in the soil |
| `lab` | filled in **after that act** — laboratory, office, archive |
| `unknown` | **the definition has not said** — and this is the default |

**Why these names.** `recorded_in` names a **place and a moment**, not a
rank: `priority` or `level` would have said that a lab field counts
for less, and that is not true — it is written at another moment, often by another person.
And `lab` is the shorthand the discipline uses for “not while digging”: it is not
a statement about a room, and a catalogue number filled in at the office is
`lab` just like an analysis under the microscope.

**The default is the one that promises nothing.** A field without `recorded_in` is
`unknown`, and a consumer **cannot** conclude from it that it is a trench field. If the
format is silent, it is silent: whoever builds a phone sheet on `unknown` is inventing
a decision nobody took. For the same reason a value that is not
one of the three is an **error** and not a silent fallback to `unknown`: a
definition that meant `trench` and wrote `Trench` would vanish from the
phone sheet without anything, anywhere, saying why.

#### How it is decided — the criterion, and where it comes from

The criterion **is not an opinion of whoever writes this format**. It has two bases, and
each one is citable line by line.

**Basis A — the words a person says in the field.** In
`stratigraph-chatbot/app/tools.py` the seven intents of the field assistant were born
from **Elisa Dalla Longa's field sheet**: a forex card with the
voice commands in colour, an accessibility artefact that doubles as the specification
of the commands. The file puts it like this: *“the commands on it ARE the
intents, in the words a person says with their hands in the soil.”* So:
**a field that one of the intents names — as a slot or inside a recognised
phrase — is a trench field**, and the justification is the line number.

**Basis B — the words of the standard itself.** Some recording sheets say it themselves.
The ICCD 2021 US has `RESPONSABILE COMPILAZIONE SUL CAMPO` and `DATA RILEVAMENTO
SUL CAMPO` and, a few lines below, `DATA RIELABORAZIONE` and `RESPONSABILE
RIELABORAZIONE`: **it is the standard that distinguishes the field from the reworking,
in its own labels.** Where a recording sheet makes that distinction, its own is the one that
holds.

Everything else is `unknown`, and must be left `unknown`. A handful of
uncertain fields, declared, is worth more than fifty-nine decided by someone who does not dig.

**Citing the basis is as mandatory as the marker.** A criterion without its
provenance turns into arbitrariness at the first argument, so the definition carries
the justification in `note` on the field, or in the sheet's `notes` when it
concerns the whole.

#### It is PER STANDARD, and the two recording sheets in this repository prove it

There is no universal list of “field fields”, and the format must not
suggest there is. The Spanish recording sheet will have a different subset, decided by
whoever writes it.

Measured on the two definitions in here: **the ten relationship boxes of the
ICCD 2021 US are `unknown`** — none of the seven intents names them — while the
**five of the `ficha ES demo` are `trench`**, because the author of that (demo)
sheet decided so. Same concept, different marker, **and the difference is the
basis, not the concept**. If the two sheets ended up with the same subset,
the marker would be describing our prejudice instead of the standard.

#### The two questions it needs to answer

**Which fields do I show on the phone?** `template.recorded_in("trench")`. The filter
lives in the model and not in the consumer, because a consumer that filters on its own is
a second reading of the same declaration.

**What happens to a mandatory field that is not a trench field?** A sheet
compiled in the trench is **incomplete by construction**, and that is not an error: it is the
craft. `required` and `recorded_in` are **orthogonal** on purpose, and together
they make the distinction computable per field:

| `required` | `recorded_in` | an absent value means |
|---|---|---|
| `true` | `trench` | **something is missing**: it could have been filled in on the excavation |
| `true` | `lab` | **incomplete by construction**, if the sheet is still a field one |
| `true` | `unknown` | **it cannot be decided** — and that is the honest answer |

The third row is the reason why `unknown` must be the default and not a
synonym of `lab`: “I don't know” and “it is filled in later” lead a validator to two
different conclusions, and one of the two would absolve an incomplete sheet without
having the right to.

**What this format CANNOT say, and must be said here:** the definition makes
the distinction computable **per field**, but applying it requires knowing whether
*that compiled sheet* is still a field sheet or already reworked — and that is a
state of the **record**, not of the definition. Today a record (§5) does not declare it.
A validator of compiled sheets, when it exists, will need that one extra
declaration; it already has the rest.

---

## 2 · The graph binding — the verdicts

Every field declares what it **means**. There are seven admissible verdicts:

| verdict | meaning | mandatory keys |
|---|---|---|
| `identity` | it is (part of) the human identifier | the field must be in `identity.human_key` |
| `property` | it is a property of a node that exists | `qualia` **or** `property_name` |
| `node_type` | it **decides** the node type | `node_types: {termine: NodeType}` |
| `node` | it is a node in its own right, reached by an edge | `node_type` **and** `edge_type` |
| `edge` | it is a relation towards another unit | `edge_type` **and** `direction` |
| `vocabulary` | it is a controlled term | the field must have `vocabulary`; `qualia` optional |
| `none` | pure presentation: the sheet says it, the graph does not | — |

Common keys: `attaches_to` (what it attaches to, default `self` = the unit
described by the recording sheet), `target` (what sits at the other end of an edge),
`note`, `blocked_on`.

### 2.1 · The gate: the names must exist

`node_type`, `edge_type` and `qualia` are checked against **what s3Dgraphy
declares today** (node datamodel, connections datamodel, qualia types). A name
that does not exist is an **error**, not a warning.

This is not pedantry: it is how “do not add types to the datamodel” enforces
itself. Growing the datamodel is a decision, not a side effect of a definition
written at night.

**There is one source only: `registry/s3dgraphy-snapshot.json`.** It is committed, so
it is the same for everyone; it declares where it was taken from (s3Dgraphy commit,
`git_dirty`, date) and with which versions (node datamodel, connections datamodel,
qualia, `em.ttl`). `validate` and `build` read **that** — before
2026-10-18 `validate` read the s3Dgraphy working tree when there was one and the
snapshot when there was not, and the same definition was validated against 1.6.19 on one
machine and 1.6.13 on another.

The s3Dgraphy working tree (`$STRATIGRAPH_S3DGRAPHY_SRC`, or the checkout next
to this repository), when present, serves **one question only**: is the snapshot
still what s3Dgraphy declares? The comparison is on **content**, not on the
commit. If they diverge, the command says so — with the differences — and **stops**:
it does not choose on its own. Regenerating (`registry-snapshot`) is the decision, and the diff
of `registry/` is its record. `--snapshot` skips the comparison, and the provenance
line declares it.

Beyond the names, the snapshot holds what is needed to say what to **produce**
(§9): the em.json spelling of every class (`DocumentNode` → `document`), the reverse
and the symmetry of every edge, the RDF predicates that the s3Dgraphy exporter
emits for each (asked of its code, not re-read), the `em:` terms
declared in `em.ttl`, and the closed set of CRDT operations. **If the
snapshot is missing, nothing is validated**: there is no third mode in which
every type is fine.

### 2.2 · `blocked_on` — when the sheet says more than the graph

```yaml
graph:
  verdict: none
  blocked_on:
    needs: "attore istituzionale (E39_Actor / E74_Group)"
    reported: "EM_design_setaccio-US §1 — decisione di E.D."
```

A field whose honest binding would require a type that s3Dgraphy lacks **is not
silently downgraded to presentation**: it carries in writing what would be
needed and to whom it was reported. The verdict must be `none` (until the
decision exists, the field lands nowhere) and `validate` counts them
and prints them. In the US 2021 there are three: `ente_responsabile`, `ufficio_mic`
(the institutional actor) and `campionature` (`CRMsci S13_Sample`).

**The missing decision may belong to whoever owns the standard**, not to the
datamodel: the vocabulary of locus types that only the IAA can provide
(`dai-idaifield-layer-2026`, fourteen fields). The form is the same — `none`
plus `blocked_on`, with the question in `needs` and the addressee in `reported` —
and it is the form **that compiles** of a verdict not yet decided: `undecided`
remains the draft marker (§7), which no definition carries.

### 2.3 · Edges have ONE canonical direction

The recording sheet has two boxes for the same relation (`COPRE` and `COPERTO DA`); the
graph has one edge. So:

```yaml
- id: copre        → {verdict: edge, edge_type: overlies, direction: outgoing}
- id: coperto_da   → {verdict: edge, edge_type: overlies, direction: incoming}
```

`direction: incoming` means: the canonical edge runs **from the cited unit to
this one**. `edge_type` must be a key of the connections datamodel; the
inverse names (`is_overlain_by`) are **not** edge types and are not written here.

Measured on s3Dgraphy 1.6.13: the twelve boxes of the US sheet are **seven
edge types** times **two directions** — `equals`, `bonded_to`, `abuts`,
`overlies`, `cuts`, `fills` (all `AP11_has_physical_relation` with `type_tag`) and
`is_after` (`P120_occurs_before` / `AP28`).

---

## 3 · The vocabulary, and alignment across countries

A definition **references** a thesaurus, it does not embed it: a vocabulary has
its own life cycle and its own licence. The schemes live in
`vocabularies/schemes/<id>.yaml`:

```yaml
scheme:
  id: iccd-ra-materia
  authority: ICCD
  labels: {it: "…", en: "…"}
  status: resolvable            # or: declared
  origin: external              # or: originated
  uri: "http://dati.beniculturali.it/vocabularies/…"
  license: "CC BY-SA 3.0 IT"
  attribution: "ICCD — MiC; …"
  binding_thes_id: "VC_MTC_RA"
  resolve:
    kind: external_skos_file    # or skos_file (inside the repo)
    path: "strumenti-terminologici/…/….rdf"
```

* `declared` = the standard prescribes a controlled vocabulary, but no readable SKOS
  exists (or is within reach). This is the case of the ICCD **field** models:
  the terminological tools in RDF cover the catalogue sheets.
* `resolvable` = there is a SKOS file. `skos_file` lives in the repository;
  `external_skos_file` lives on disk, under `$STRATIGRAPH_ICCD_STANDARDS`
  (default `~/Documents/GitHub/Standard-catalografici`).
* `resolvable` with `resolve.kind: idai_field_valuelist` = **an iDAI.field
  valuelist**, read from a checkout of `dainst/idai-field`
  (`$STRATIGRAPH_IDAI_FIELD`, default `~/Documents/GitHub/idai-field`) **at the
  commit the scheme names** (`resolve.commit`, `git show`, never the working
  tree), with `resolve.valuelist`. The labels are those of the DAI's
  `Language.default|projects.<lingua>.json`. iDAI.field does not coin URIs
  for values: the concepts are **locators we build ourselves**
  (`…/Valuelists.json#<valuelist>/<valore>`, the value percent-encoded), and the
  scheme declares it. One scheme per valuelist (`idai-field-<valuelist>`), so
  a widget offers the values of the box and not the other nine hundred.

`status` and `origin` answer two different questions and must not be confused.
`status` says **can I resolve it?**, `origin` says **whose is it?**.

* `origin: external` (default) = it belongs to others. We declare it, we resolve it where
  it lives, licence and attribution are theirs, and an update comes from outside.
* `origin: originated` = we maintain it. It carries its own namespace, its own
  `version` and a duty of citation towards the scientific source it
  reformulates. The validator **demands** `version`, `license` and `uri`: one of our own
  modules without one of those three is uncitable, and an uncitable vocabulary is
  of no use to anyone. The files live in `vocabularies/skos/`, not in `fixtures/` —
  a module we write is not a test.

The first originated module is `em-taph-weathering`: the six bone weathering stages
of Behrensmeyer 1978, which have been the *de facto* standard of taphonomy
for half a century and **have never had an identifier**. The concepts are a
published scientific fact; the author's prose is not, so the definitions
are **reformulated, not transcribed**, with the source on every concept.

After it, the five modules of the US sheet (`em-us-definizione`,
`em-us-consistenza`, `em-us-colore`, `em-us-stato-conservazione`,
`em-us-affidabilita`): the ICCD prescribes a controlled term for those boxes
and has not published its SKOS, so they answer provisionally for the
declared schemes `iccd-us-*` (§3.2). Same rule: a term without a source does not get in, and
the source is on every concept (`dct:source`).

The `em-` prefix and the `w3id.org/extendedmatrix` namespace are not a naming
detail. An `external` module we simply declare, and if the project ends
nothing happens to anyone. An **originated** module carries URIs that others
will cite: if we hang them on StratiGraph, which has an end date, in 2029
they are orphans. So they live on Extended Matrix, the ecosystem that outlives
the project; StratiGraph stays in the `attribution`, which is the right place to
say where and when the module was born. Publication is at
`extendedmatrix.org/vocab/<modulo>/`, with the source here: the published copy
carries at its head the commit it comes from, because two copies of a vocabulary
diverge, and the resolvable one going stale is the worst failure.

**What ends up in the graph is the CONCEPT** (the SKOS URI), not the label: resolving
the label in a language happens at read time. If you write the Italian string into the
graph, you have lost.

### 3.1 · The alignment

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

Resolution order for a label: **own scheme → provisional scheme
(§3.2) → alignment (`exactMatch` first) → label carried by the data** (declared as such in the
`--explain-vocab` trace). If none of the three routes yields a word in the
requested language, the renderer **refuses**.

This field exists from day one, even empty, for one reason only: an alignment
field added a year from now is a field nobody will fill.

### 3.2 · `provisional` — the declared standard and who answers for it

A `declared` scheme says that the standard prescribes a vocabulary that nobody has
published. As long as it stays that way, the widget writes a word without a concept, and a
word without a concept does not enter the graph (in s3Dgraphy `definition.rdf.label_only`
is `null`: no triple) and aligns to nothing. The remedy is not to change the
scheme the field cites — **that is the standard** — but to say who answers for it
in the meantime:

```yaml
scheme:
  id: iccd-us-definizione
  status: declared
  provisional: em-us-definizione     # one of OUR modules, until the ICCD publishes
```

* the field keeps citing `iccd-us-definizione`; the reader resolves with
  `em-us-definizione` (order: own scheme → **provisional** → alignment
  of the provisional → label carried by the data; the trace says
  `provisional:<id>`);
* the compiled form (§9) writes it twice, because a consumer should not have to
  re-read the schemes: `vocabulary: {scheme, provisional}` on the field and on the
  recipe entry, and in the header the provisional **right after** the scheme it
  replaces (`provisional_for`), so whoever vendors the header vocabularies
  vendors the one that answers;
* **rules checked** when the schemes are loaded, and therefore by `validate` and by
  `build`: only a `declared` scheme can have `provisional` (a `resolvable` one
  already answers for itself, and would have two); the provisional must exist, be
  `origin: originated` (it is our duty to answer, not a third party's) and
  `resolvable`; a provisional does not in turn have a provisional;
* **the day the authority publishes**: `resolve:` on the declared scheme, an
  `em-us-*` → `iccd-us-*` alignment in `alignments/` (`exactMatch` where it is one),
  and `provisional` is removed. The concepts already written into graphs stay valid: they are
  our URIs, and the alignment carries them to the other side.

### 3.3 · `unverified_languages` — operational now, corrected later

An originated module is needed in the trench in all the partners' languages before
anyone has been able to verify them. E.D.'s rule for translations is
*operational now, corrected afterwards once verified*, and the format states it like this:

```yaml
scheme:
  id: em-us-colore
  origin: originated
  unverified_languages: [en, ro, el, es, pl, he, de]   # draft labels
```

* the labels are all there (`skos:prefLabel` per language in the SKOS file) and
  resolve like the others: a draft is operational;
* the list says which languages **nobody who answers for them** has verified yet; verifying
  a language removes it from the list, and that is a readable commit;
* only an `originated` module carries it: an external scheme answers for its own
  labels.

**Why per scheme × language and not per label.** s3Dgraphy marks verification
string by string (`validated_<lang>` in `datamodel_translations.json`), and there it
works because every string is already a JSON object. In SKOS a label is a
literal: marking them one by one would mean reifying them (SKOS-XL), for modules of
ten or forty concepts that a person reviews one language at a time anyway.
One mechanism for the whole suite: this one.

---

## 4 · The sheet — double-sided A4

The sheet is a grid of rows and cells, per side:

```yaml
sheet:
  page: A4
  margins_mm: {top: 10, right: 12, bottom: 10, left: 12}
  sides:
    - id: recto                 # recto | verso
      labels: {it: "fronte", en: "recto"}
      rows:
        - h: 15                 # height in MILLIMETRES
          cells:
            - {field: ufficio_mic, w: 53.4}    # width as % of the row
            - {field: identificativo_riferimento, w: 46.6}
```

A cell is one of three things:

* **a field**: `{field: <id>, w: <%>, label: auto|none}`;
* **a block**: a nested grid, with or without a label of its own —
  `{block: <id>, block_labels: {...}, rotated: true, w: <%>, rows: [...]}`.
  `rotated: true` draws the label vertically on a strip to the left, as the ICCD
  recording sheet does for SEQUENZA FISICA and SEQUENZA STRATIGRAFICA. Blocks nest,
  and that gives the power of `rowspan` without having rowspans;
* **a spacer**: `{w: <%>}` with neither `field` nor `rows`.

Rules checked:

* the sum of the `w` in a row does not exceed 100;
* every field has **exactly one** box (a field nobody can write in is not a field;
  two boxes for the same field are an error);
* the sides are called `recto` and `verso`, and do not repeat;
* **the declared height of a side must fit on one A4 side** (297 mm minus the
  margins minus 9 mm of running header);
* a rotated label must fit within the height of its block, or it would print cut
  off.

The height of a row is a **design minimum**, not a guillotine: if a value is taller
than its box, the box grows and the command says how many pages it cost
(`2 side(s) → 3 page(s)`). What someone has written is never cut.

### 4.1 · The sheet that is not there

A standard that lives in a database with a form — iDAI.field — **has no paper
model**, and drawing one would mean inventing it: it would look like the standard.
So `sheet` is **optional**, and its absence is stated by leaving the key out:

* no `sheet:` key = no sheet (`Template.sheet` is `None`, the compiled output writes
  `"sheet": null`, StratiField shows the Fields and says so with `view.sheet.none`).
  There is no empty sheet: a `sheet:` key that is present is a sheet, with its rules,
  and it must place every field;
* without a sheet the validator does not count boxes — there are none — and the
  paragraphs remain the structure the form uses;
* `form` draws a fluid page, one block per paragraph; **`print` refuses**
  (`declares no sheet: there is no paper model to print`).

Whoever has a real sheet declares it; whoever builds one for convenience — like the
IAA-DANA definition, which says so in its comment — declares it too, and takes
responsibility for its geometry.

---

## 5 · The data

```yaml
record:
  template: iccd-us-2021
  template_version: "1.0.0"     # REQUIRED: which version of the definition it followed
  uid: "01J9Z7QK…"              # opaque
  values:
    us: "3014"
    copre: ["3018", "3020"]
    definizione: {concept: "…", label: "strato di crollo"}
    misure: [{qualia: thickness, label: "spessore max", value: "0,42", unit: "m"}]
  field_provenance:
    interpretazione: {state: human_validated, by: "ai:… · validato da …", ts: "…"}
```

The data file is not the recording sheet: it only declares which definition it
follows, **and in which version** (`template` + `template_version`, the pair that §9
uses to archive the compiled form). Without the version, rereading a record would
mean guessing which recipe it was written with. `print` and `form` refuse a record
of another definition and flag a different version.

---

## 6 · What is NOT there, by choice

No server, no authentication, no session, no database. No Harris matrix (the graph
editor is EMStudio). No GIS (that belongs to pyarchinit). No ministerial catalogue
record (that belongs to the Catalog, as a projection, later). No new type in
s3Dgraphy. No asset management (it already exists: SHA-256 + IIIF). No identity,
offline queue or room entry (they already exist, proven in the field assistant).

---

## 7 · The draft extracted from an XSD

`stratigraph-templates extract-xsd <file.xsd> --code SAS --version 3.00` reads an
ICCD catalogue standard and **proposes** a definition: structure, paragraphs,
aliases, obligation, repeatability, bindings to vocabularies.

Two things are missing and cannot be there:

* **the graph binding**: every field comes out with `verdict: undecided`, and the
  validator **refuses** a definition that still carries that marker. A person
  decides it;
* **the sheet**: an XSD does not say where a box goes. The draft puts one row per
  field so that nothing is lost, and declares it.

`stratigraph-templates validate --draft <bozza>` runs **all** the checks and counts
the `undecided` instead of refusing them: a draft is green when the only thing it
lacks is a person's judgement.

### 7.1 · The draft extracted from iDAI.field

`stratigraph-templates extract-idai-field Layer [--project Milet] [--commit
<sha>] [--schemes-out vocabularies/schemes]` reads the open configuration of
iDAI.field (DAI, Apache-2.0) **at a commit** of a local checkout:
`Library/Categories.json` and `Forms.json` (the category's form **merged with its
parent's** the way iDAI.field merges it, `mergeGroupsConfigurations`), the labels
from `Core/` and `Library/Language.<lingua>.json` and, if requested, the project
configuration on top (`Config-<P>.json`: hidden fields, custom fields, redefined
valuelists). The core fields and relations are read from
`built-in-configuration.ts` and `relation.ts`, not remembered.

Compared with the XSD it knows **more**, and proposes more: the identifier
(`identity`), the relations that have ONE canonical edge in s3Dgraphy (a table, in
the code, cited), the relations iDAI.field derives on its own, and the geometry
(`none`). Everything else comes out `undecided`. **No sheet**: the draft has no
`sheet` (§4.1). The valuelists become resolvable `external` schemes (§3), one per
valuelist, written with `--schemes-out` if they are not there.

## 8 · A document-per-record export (iDAI.field)

The format describes a recording sheet, not an archive, and the data of a record are
a flat dictionary of `field_id → valore`. A document-per-record export — like the one
from `iDAI.field` / Field Desktop, which replicates **at document level** while here
replication happens at **field** level — comes in as a sequence of `record:`, one per
document, provided the producer declares which definition each document answers to.
What does *not* come in automatically is their configurable category structure: that
has to be written as a definition (which is precisely the work this format makes it
possible to do once and not for every tool). Since 2026-10-26 the first one exists —
`dai-idaifield-layer-2026`, the `Layer` category — and the draft it grows from can be
extracted (§7.1).

---

## 9 · The compiled form — `stratigraph-templates build`

A definition in YAML is made for whoever writes it. A program that uses it —
StratiField drawing the form and, once the sheet is compiled, **sending the
operations to the room** — needs something else: a file it takes and uses **without
reading the definition at run time**, that does not change under its feet, and that
says which s3Dgraphy it was checked against. `build` produces it. It is the same pact
as the theme (`sync-brand.sh`) and the datamodels (`sync-datamodels.sh`): **it is
produced here, the app vendors and commits the copy**.

```
dist/schede/index.json                   every definition, every version, digest, datamodel
dist/schede/<id>/<versione>.json         the compiled definition
```

`dist/` is versioned in the repository, and a test checks that it matches what the
definitions compile to today: a definition modified without `build` would leave the
apps an old copy that looks official.

**What does not compile.** `build` compiles what validates (§1–§4): a definition
without `version`, or with an `undecided` verdict (the draft from an XSD, §7), does
not compile; the others do, and the command exits with an error if even one was
refused.

### 9.1 · The header

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

`datamodel` is **read from the snapshot** (§2.1), which in turn read it from the
s3Dgraphy configuration files: no version is written by hand.

**The digest** is SHA-256 over the canonical JSON (sorted keys, no whitespace) of the
document **without** `digest`, `datamodel` and `compiled_by`. So:

* recompiling the same definition gives the same digest, byte for byte;
* changing the definition — even just one label — changes the digest;
* recompiling against a newer datamodel **that does not change the recipe** leaves
  the digest as it is (the `datamodel` line is updated); a datamodel that does change
  it — a renamed edge, a different em.json spelling — changes the digest, because the
  recipe is inside.

### 9.2 · The visual half

What a form and a sheet need, exactly as it is in the definition: `identity` (human
key, `pattern`, resolved `unit_field`, UID policy), `provenance`, `paragraphs`,
`fields` (type, `required`, `repeatable`, `recorded_in`, `max_len`, labels **in every
declared language**, `help`, `options`, `vocabulary`, `note`, and the paragraph it
belongs to), `sheet` as it is, `notes`. No fallback labels: if a language is
declared, it is there.

### 9.3 · The ontological half — the recipe

For each field, **what to produce in the vocabulary of the five s3Dgraphy CRDT
operations** — `add_node`, `update_field`, `remove_node`, `add_edge`, `remove_edge`
(`s3dgraphy/crdt.py:66`, `api.make_op`) — and **no values**. The orchestrator is
StratiGraph Server: whoever enters a room sends operations, the room applies them
with `em.apply_op` and relays them. A recipe that said “build this graph” would need
an applier next to the room, outside the orchestration; this one says **which
operations to send**.

An entry has **steps**; a step `emit`s an operation in the exact wire form (that of
`crdt.apply_op_to_section`), with **references** where a value will go:

| reference | what it is |
|---|---|
| `$unit` | the unit the recording sheet describes |
| `$value`, `$value.<k>` | the value of the field; one of its keys (`$value.concept`, `$value.name`) |
| `$item`, `$item.<k>` | an element of a list value (the entry has `each: true`: the steps repeat per element) |
| `$node` | the node the step finds or creates (see `resolve`) |
| `$prop` | the PropertyNode the step mints |
| `$field.<id>.prop` | the PropertyNode minted by the entry of ANOTHER field (the entry has `after: [<id>]`) |
| `$anchor.<nome>` | something the definition names and does not define (see `open`) |

`when: created` on a step = send it only if `resolve` **created** the node instead of
finding it. **Ids are minted by whoever creates** (`identity.uid.policy`): the recipe
never writes one. `name` and `description` of an em.json node are strings: whoever
substitutes a numeric value writes it as text.

**The unit** (`recipe.unit`) is found by human key in the context
(`identity.deduplication`) or created with an `add_node`; its `node_type` is decided
by the field with verdict `node_type`, if there is one. It is decided **at creation**:
`update_field` addresses only `name`, `description` and `data.*` (`crdt.py:749`), so
the type of an existing unit cannot be changed with an operation of this vocabulary —
and the recipe says so.

**Verdict by verdict:**

| verdict | steps |
|---|---|
| `identity` | none: the field composes the unit's name (`names: $unit`, `designator`) |
| `none` | **none**, declared: `reason`, or `blocked_on` |
| `node_type` | none: `decides: unit.node_type` + the value table → `{class, node_type}` |
| `property`, native name | `update_field {node_id: $unit, field: description, value: $value}` |
| `property`, **node element** | `update_field {node_id: $unit, field: <em_json dell'elemento>, value: $value}` — today `definition` → `data.definition` (see below) |
| `property`, otherwise | `add_node` PropertyNode + `add_edge has_property` (see below) |
| `vocabulary` | like `property`, with `property_type` = the qualia and **value = the concept** (`$value.concept`, §3) |
| `node` | `add_node` (`when: created`) of the node found by name/ref + `add_edge` in the declared direction |
| `edge` | one `add_edge` per element; `outgoing` = `$unit → $item`, `incoming` = `$item → $unit` |

**The property: the form s3Dgraphy and EMStudio actually use**, not a new one:

```json
{"op": "add_node", "node": {"id": "$prop", "node_type": "property", "name": "texture",
                            "description": "$value.concept",
                            "data": {"property_type": "texture"}}}
{"op": "add_edge", "edge_type": "has_property", "source": "$unit", "target": "$prop"}
```

* PropertyNode with `name` = `data.property_type` = the qualia, attached to the
  subject with `has_property` **from the subject to the property**: EMStudio
  `frontend/src/model.ts:924-938` and `frontend/src/em-data.ts:605-632`
  (`addQualiaClaim`), s3Dgraphy `importer/base_importer.py:666-713`
  (`_create_property`) and `importer/unified_xlsx_importer.py:612-639`
  (`_handle_qualia`);
* **the value lives in `description`**: this is the convention EMStudio declares
  (`model.ts:924`, “A PropertyNode's VALUE lives in `description`”) and that
  `_create_property` and `addQualiaClaim` follow; `_handle_qualia` puts it in `value`
  (lifted into `data.value` by `emjson_exporter.py:60`). The two spellings coexist in
  s3Dgraphy today; the recipe follows the orchestrated one;
* **units of measure** in `data.units` (`_handle_qualia`, `:632`);
* a `quantity_list` makes **one PropertyNode per row**, with the row's qualia
  (`$item.qualia`, and `defaults` if the field declares one);
* `property_name: description` is the **node's field** and becomes `update_field` on
  `description` (audit B9: it used to end up in `data.<id della casella>`);
* a `property_name` that the node datamodel declares as a **node element**
  (`properties.<nome>` with `kind: node_element`, today only
  `StratigraphicNode.properties.definition`, nodes 1.6.9) is **not** a qualia: it
  becomes an `update_field` on the em.json location the datamodel names
  (`data.definition`), with the **whole** value (`$value` = `{concept, label}`), and
  the entry carries `element: {name, declared_on, value, rdf}`. Name, location and
  RDF come from the snapshot (`node_elements`, format 3), not from this repository.
  The compiler refuses a field type that does not write that value (a `concept` is
  written only by a `term`) and a unit type that does not inherit the element
  (decision by E.D., 2026-10-21: the DEFINITION of the US is a node element);
* a `property_name` that is not a registered qualia still becomes a PropertyNode
  with that `property_type` — it is what `_create_property` does with column
  names — and the entry declares it (`registered_qualia: false`).

**A node reached by an edge** is looked up before it is created: by name
(`LocationNodeGroup`, `EpochNode`…), by `ref` and then name (`person_ref`,
`epoch_ref`), by **path** if it is a file reference (`resource_ref_list` →
DocumentNode with `data.url` = the reference, deduplicated by path like
`pyarchinit_importer._add_path_document`, `:797-808`). A `longtext` is **content**,
not a name: the node is minted and carries it in `description`.

**The edges.** `edge_type` is the key of the connections datamodel, that is, the
canonical form; `edge` reports what s3Dgraphy declares about that edge —
`symmetric`, `reverse`, and the RDF **that the s3Dgraphy exporter emits**
(`exporter/rdf_exporter.py:199`, `:300`, `:332`: predicate, AP11 subproperty,
extension, `subject: target` when the mapping inverts). `same_rdf_as` lists the other
edge types that become **the same property**: `bonded_to` ≡ `is_bonded_to`
(`em:bondedTo`), `equals` ≡ `is_physically_equal_to` (`em:physicallyEquals`,
`em.ttl:528`, `:536`). Both names are valid and the ICCD definition uses the forms
the datamodel calls canonical; the compiled output says so, so a consumer does not
double the arrows.

**`open` — what the definition does not decide, declared.** The recipe does not
invent: where the definition is silent, it writes that down. Today, for the ICCD US:
`definizione` (verdict `vocabulary` with neither qualia nor `property_name`: no
operation until it says so), and three `attaches_to` that name undefined acts
(`excavation_activity`, `recording_act`, `revision_act` → `$anchor.<nome>`, in
`recipe.anchors`). For the two demos, the unit type too (no `node_type` field). The
compiler instead **refuses** what is inconsistent: an `attaches_to: property:<x>`
that no field produces, a name with no em.json spelling, an edge that is deprecated or
whose `em:` RDF property is not in `em.ttl`, an operation outside the five.

### 9.4 · Published versions do not change

`build` refuses to rewrite `dist/schede/<id>/<versione>.json` if the new digest
differs from the one already written: **bump `template.version`**. The same digest
rewrites the file (the `datamodel` line may have been updated) and says so. The index
lists every version present and the latest (`latest`, semver order): old versions
stay, because a record compiled with one of them must be reread with that one.
