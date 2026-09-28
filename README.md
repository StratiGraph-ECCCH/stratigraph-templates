# stratigraph-templates

**Archaeological recording sheets, written down as data: one definition per national
sheet, which the StratiGraph applications read to show the form, print the sheet and
write the knowledge graph.**

Part of **StratiGraph — Knowledge Graphs for Stratigraphy**, a Horizon Europe project
(grant agreement [101232855](https://cordis.europa.eu/project/id/101232855), 2025–2029)
coordinated by CNR-ISPC. Documentation:
[docs.extendedmatrix.org/projects/stratigraph-templates](https://docs.extendedmatrix.org/projects/stratigraph-templates/)
(English, with an Italian translation).

## Why it exists

Every excavation records its stratigraphic units on a sheet, and every country — often
every institution — has its own. Italy fills in the ICCD model for the Stratigraphic Unit,
Spain a *ficha de unidad estratigráfica*, the Israel Antiquities Authority records loci in
its DANA system, the German Archaeological Institute works in iDAI.field. The boxes look
alike and are not the same: they are named and grouped differently, they are filled with
different controlled terms, and some exist on one sheet only.

StratiGraph brings excavations from these countries into one knowledge graph. For that,
someone has to say, box by box, what each field of each sheet means for the graph: which
unit, which relation, which property, which vocabulary. This repository is where that is
written down, once per sheet, in a form that people and programs can both read.

The usual way goes the other direction: the sheet becomes the database schema, one column
per box, and a second national sheet means new columns, new code and a migration. Here
**the recording sheet is data, not a schema**: a **declarative, versioned, citable
definition**, which a machine reads to do three different things:

* show a **form** to fill in (phone, tablet, desktop),
* print a **double-sided A4 sheet**,
* tell the **graph** what whatever was written means.

Adding a sheet costs **writing a definition**, not writing an application. The proof is in
the tests: the renderer diff between before and after adding the second standard is empty.

> **This repository contains DATA and a reference implementation.
> It does not contain an application.** No server, no login, no database.

## Where it sits in StratiGraph

The definitions are written here and used elsewhere in the project's software:

* **s3Dgraphy**, the graph library of the Extended Matrix, declares the node types, edge
  types and qualia; every binding in a definition is checked against what it declares
  (see *The binding to s3Dgraphy* below);
* **StratiField**, the field recording application, takes the compiled definitions to draw
  the form and the sheet, and sends what is recorded to **StratiGraph Server**, which
  applies it to the shared graph;
* the other applications of the suite read the same graph, whichever national sheet a unit
  was recorded on.

The work belongs to StratiGraph's work package on the data model and the knowledge graph
(WP3), and is reported in its deliverables D3.1 and D3.2.

## How it is laid out

```
templates/<id>/template.yaml   the definitions (the substance, the graph binding, the sheet)
vocabularies/schemes/          the vocabulary schemes, REFERENCED not embedded
vocabularies/alignments/       the SKOS alignments between national vocabularies
vocabularies/fixtures/         fake micro-schemes, for testing
examples/                      test data
registry/                      snapshot of what s3Dgraphy declares — THE source for validate and build
dist/schede/                   the COMPILED definitions (self-contained JSON): what an app vendors
src/stratigraph_templates/     the reference implementation (reads, validates, renders)
drafts/                        drafts extracted from XSD standards: proposals, not truth
tests/                         the suite, and the broken definitions the gates must catch
docs/                          the documentation site, plus dated working notes and screenshots
```

The definitions in `templates/` today — with their fields, languages and licences — are
listed in the
[catalogue of definitions](https://docs.extendedmatrix.org/projects/stratigraph-templates/en/latest/pages/catalogue-definitions.html),
which is generated from the repository at every build of the documentation.

The format specification is in **[SPEC.md](SPEC.md)**.

## Usage

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'

.venv/bin/stratigraph-templates validate
.venv/bin/stratigraph-templates build                 # → dist/schede/<id>/<versione>.json + index.json
.venv/bin/stratigraph-templates registry-snapshot     # only when s3Dgraphy has changed: it is a decision
.venv/bin/stratigraph-templates info iccd-us-2021
.venv/bin/stratigraph-templates print iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.pdf
.venv/bin/stratigraph-templates form  iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.html
.venv/bin/stratigraph-templates vocab --scheme fx-ue-definicion-es --concept 'https://example.invalid/fixture/ue-definicion-es/estrato' --lang it
.venv/bin/stratigraph-templates extract-xsd '<…>/ICCD_normativa_SAS_3.00_102019.xsd' --code SAS --version 3.00
.venv/bin/python -m pytest
```

Printing requires WeasyPrint (`pip install '.[print]'`; on macOS you also need
`brew install pango`). Resolving vocabularies requires `rdflib`.

### The two dependencies outside the repository

Two vocabularies belonging to others **are not copied here**: they are read where they
live, from a checkout next to this repository. They are needed to resolve concept
**labels** (`vocab`, `form`/`print` with the words, the tests that read them) and for
`extract-idai-field`; **`validate` and `build` do not need them** (the compiled output
names the schemes, it does not copy their words), but if they are missing they say so in
one line.

| checkout | where (default) | variable | commit | what it is for |
|---|---|---|---|---|
| [ICCD-MiBACT/Standard-catalografici](https://github.com/ICCD-MiBACT/Standard-catalografici) | `~/Documents/GitHub/Standard-catalografici` | `$STRATIGRAPH_ICCD_STANDARDS` | any (the working tree is read; measured on `c1de8c3`, 2026-03-26) | the SKOS/RDF of the ICCD terminology tools (`resolve.kind: external_skos_file`) and the XSDs for `extract-xsd` |
| [dainst/idai-field](https://github.com/dainst/idai-field) | `~/Documents/GitHub/idai-field` | `$STRATIGRAPH_IDAI_FIELD` | **must contain `4b5c1e2`** (2026-09-24): read with `git show <commit>:…`, never the working tree | the DAI valuelists of the `idai-field-*` schemes (`resolve.kind: idai_field_valuelist`) and `extract-idai-field` |

```bash
cd ~/Documents/GitHub
git clone https://github.com/ICCD-MiBACT/Standard-catalografici.git
# the configuration is enough, not the application (23 MB instead of the whole repository):
git clone --filter=blob:none --sparse https://github.com/dainst/idai-field.git
git -C idai-field sparse-checkout set core/config core/src/configuration core/src/model/configuration
git -C idai-field cat-file -e 4b5c1e2c3c499d4bd125d0eda61cc6f5c94ffcd4^{commit} && echo ok
```

## The five kinds of definition

A definition that comes in here comes from somewhere, and where it comes from decides how
it is cited and under what licence it is redistributed. There are five kinds, and
[LICENSING.md](LICENSING.md) deals with them one by one.

| kind | where it comes from | example |
|---|---|---|
| published standard | reconstructed from an authority's standard | `iccd-us-2021` |
| our own module | we originate it, for the EM language | the `em-*` schemes |
| export | read from the data, because no public document exists | *to be opened* |
| application configuration | read from the open code of an excavation system | `dai-idaifield-layer-2026` |
| **good practice** | born by formalising a case study: no authority publishes it, we do not originate it, it does not live in a system | *to be opened* |

The last is the most common, and until now it had no home: the term lists a group writes
while formalising its own work — types of instrument, of sample, of activity, of unit —
and that stay inside a table in a report, not citable and not alignable. They have an
owner, a licence and a version, which is all this repository asks for. Attribution is
twofold, as for the DAI: the list stays with the group that built it, the
reading and the alignment belong to whoever made them.

## The binding to s3Dgraphy

Every definition declares, field by field, what it means for the graph. Node type, edge
type and qualia names are checked against **what s3Dgraphy declares today**: a name that
does not exist is an error, not a warning — that is how “do not add types to the
datamodel” enforces itself instead of relying on words.

There is **one source only**: `registry/s3dgraphy-snapshot.json`, committed, which states
which s3Dgraphy commit and which datamodel versions it was taken from. If the s3Dgraphy
checkout is on this machine, `validate` and `build` compare it with the snapshot and,
**if they diverge, they say so and stop**: they do not choose on their own. Regenerating
the snapshot (`registry-snapshot`) is the decision, and the diff of `registry/` is its
record. Without a snapshot **nothing is validated**: there is no third, permissive mode.

## The compiled form — how a definition reaches a program

For every valid definition, `build` writes a self-contained JSON in
`dist/schede/<id>/<versione>.json` (plus an `index.json`): a header with the definition
version, the digest and the s3Dgraphy datamodel it was validated against; a **visual
half** (fields, labels in every language, sheet); a **recipe** that says, field by field,
which of s3Dgraphy's five CRDT operations to produce — without values. The orchestrator
is StratiGraph Server: whoever fills in the sheet sends those operations to the room. The
same pact as `sync-brand.sh` and `sync-datamodels.sh`: **this is where it is produced; the
app vendors and commits the copy**. A published version does not change: different content
under the same number is rejected. SPEC §9.

## Licences — two layers, and why this road is clean

* **The definitions** carry the licence of where they come from. Those reconstructed from
  the ICCD standards, published under **CC BY-SA 4.0** (declared at the foot of the field
  models), are distributed under the same terms and carry the attribution to MiC — ICCD in
  `standard.attribution`; the other kinds are treated one by one in
  [LICENSING.md](LICENSING.md). The ICCD thesauri are **CC BY-SA 3.0 IT** and are
  **referenced**, not copied.
* **The code** of the reference implementation: **EUPL-1.2** (a European project,
  compatible with share-alike), confirmed on 2026-09-24.

This is not bureaucracy: reconstructing the sheet **from the standard** is explicitly
permitted, while copying the templates of GPL software would not be.
