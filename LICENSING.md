# Licences and attribution

This repository has **two layers** with different licences, and the distinction matters.

## 1 · The definitions (data)

`templates/`, and the measurement notes that accompany them.

The `iccd-us-2021` definition is reconstructed from the ICCD model
*“US — Unità Stratigrafica, modello per il rilevamento sul campo, 2021”* (US —
Stratigraphic Unit, field recording model, 2021), which ICCD publishes under a
**CC BY-SA 4.0** licence (declaration at the foot of the `.doc` file:
*“MiC - ICCD_licenza CC BY-SA 4.0”*).

As a consequence:

* the definition is **CC BY-SA 4.0**;
* the attribution is **MiC — Istituto Centrale per il Catalogo e la
  Documentazione (ICCD)**, and it lives in the data (`standard.attribution`), not only here;
* whoever modifies or redistributes it does so under the same terms.

**Why it matters.** Reconstructing the sheet from the STANDARD is explicitly permitted;
copying the templates of a GPL application (HTML forms, PDF generators) would be a
derivative work of that software, with all the constraints that follow. The road chosen
here is clean by construction, not by luck.

The `es-ue-demo-2026` definition is **invented** (`invented: true`, and the print carries
the `FIXTURE` stamp): it cites no real national standard.

## 1-bis · The vocabularies WE originate

`vocabularies/skos/`, declared with `origin: originated` in
`vocabularies/schemes/`.

They are a category of their own and must be kept distinct from other people's tools: here
we are not referencing an institution's work, we are doing it. So we answer for the
content, and the validator demands three things without which one of our own modules is
uncitable — `version`, `license`, `uri`.

The first is **`em-taph-weathering`**: Behrensmeyer 1978's six bone weathering stages,
**CC BY 4.0**, attribution StratiGraph WP3 — CNR-ISPC.

**Why it is lawful, and it is the same reason as for the ICCD sheet.** The six stages are a
published scientific fact and are not covered by copyright; Behrensmeyer's **prose** is.
The module's definitions are therefore **reworded, not transcribed**, and the source is
cited on every single concept as well as on the scheme. Reconstructing the scale from the
literature is permitted; copying its descriptions would be a derivative work of the paper.

**Why it exists.** It has been the *de facto* standard of taphonomy for half a century and
has never had an identifier: it exists only as a table inside a 1978 paper. Checked in
September 2026: Getty AAT has no `cut marks`, `gnawing`, `trampling`; PACTOLS and TAABA
have `tafonomia` with zero *narrower*. The discipline is named everywhere, its objects
nowhere.

Then the five modules of the US sheet — **`em-us-definizione`**,
**`em-us-consistenza`**, **`em-us-colore`**, **`em-us-stato-conservazione`**,
**`em-us-affidabilita`** — **CC BY 4.0**, like the first. The terms come from the
PyArchInit thesaurus and interface (GPL): they are single words or trade phrases
(“strato di crollo”, “friabile”), not a protected expression, and the source is cited on
every concept; the definitions are ours. They do not derive from the ICCD standard — the
US 2021 model lists no terms (measured on the `.doc`) — and for this reason they do not
inherit the CC BY-SA 4.0 that applies to `templates/`. The iDAI.field valuelists
(Apache-2.0) serve the alignments and the DAI sheet, and are not copied (see §1-quater).

⚠ The **`w3id.org/extendedmatrix` redirect is not yet registered**: the URIs are stable in
intent but not resolvable. It must be requested before publishing.

## 1-quater · A definition read from an application's configuration

`templates/dai-idaifield-layer-2026/`, `drafts/draft-idai-field-layer.yaml`,
`vocabularies/schemes/idai-field-*.yaml`.

The fourth kind: neither published standard, nor our own module, nor export. **The open
configuration of iDAI.field** (Field Desktop), the excavation documentation system of the
Deutsches Archäologisches Institut, which the DAI publishes on GitHub (`dainst/idai-field`)
under the **Apache-2.0** licence. Read at commit
`4b5c1e2c3c499d4bd125d0eda61cc6f5c94ffcd4` (2026-09-24).

**What comes in here.** The names of the fields and groups, their **de/en labels** (short,
the ones the DAI publishes in `Language.*.json`), the types and the references to the
valuelists, with the attribution in the data (`standard.attribution`,
`standard.license: Apache-2.0`) and the commit cited. The reading, the verdicts, the notes
and the questions are our work.

**What does NOT come in.** The **valuelist values**: the `idai-field-*` schemes declare
them and **resolve them from the checkout** at the commit (`resolve.kind:
idai_field_valuelist`), just as the ICCD SKOS are resolved from Standard-catalografici. An
app that vendors them (StratiField, `sync-schede.sh`) carries with it the scheme's
attribution and licence, as Apache-2.0 requires.

**In an app's published image** (decided on 28 Sep 2026, Cowork for E.D.): the DAI labels
— those of the fields in the compiled sheet and those of the valuelists in the vendored
vocabularies — **may** live in the StratiField image on GHCR, **with** what Apache-2.0 §4
asks of whoever redistributes: next to every directory that contains them
(`schede/dai-idaifield-layer-2026/`, `vocabolari/`) `sync-schede.sh` writes
**`LICENSE-Apache-2.0.txt`** (the text the DAI itself distributes, read from the checkout
at the same commit `4b5c1e2`) and a **`NOTICE`** that says what belongs to the DAI, from
which commit, and that the labels are reproduced without changing their meaning. The DAI
has no `NOTICE` of its own at that commit (measured): there is nothing to propagate beyond
the attribution. Generated, never written by hand; the `attribution` field of every json
stays.

**Why it is lawful.** Apache-2.0 permits redistribution and derivation, asking for
attribution and that the licence of the reused part stay stated: both live in the data,
field by field of the header. The description (verdicts and notes) follows the rest of
`templates/`.

**Unlike the ICCD case:** the version stays **0.x** until the DAI (Benjamin)
has seen the reading and answered the questions in the report.

## 1-quinquies · The good-practice lists, which until now had no home

`vocabularies/schemes/` — section to be opened when the first list comes in.

The fifth kind, and the most common of all: the lists of controlled terms that are born
**by formalising a case study**, not from a standard and not from a system. “RTK geodesy,
UAV, scanner 3D” for the instrument, “sedimento, carbone” for the sample, “pulitura
meccanica, pulitura chimica” for the activity, “taglio, riempimento, muro, piano” for the
unit type. Those who do the work write them in a table, inside a report or a slide, and
there they stay: they are not citable, not alignable, and the next time someone rewrites
them slightly differently.

**They are none of the other four.** No authority like ICCD publishes them, so they are
not reconstructed from a standard. We do not originate them as we do the `em-*` modules,
so the authorship is not ours. They do not live in an export or in an application's
configuration: they live in a group's methodological work. They do, however, have
everything a definition in this repository needs — **an owner, a licence and a version**
— and so they fit well here.

**What comes in.** The vocabulary scheme with its concepts, the labels in the languages the
group works in, and the alignment to an external thesaurus where a hook exists (AAT first).
In the header, the group that produced it as `standard.attribution`, the licence it
chooses, and the version.

**Attribution is twofold, as for the DAI.** The list stays with the group that
built it, the reading and the alignment belong to whoever made them; whoever cites the list
cites both. Until the group confirms, the version stays **0.x**, which here means “not yet
citable”.

**Why it pays off for whoever writes it.** A list that lives here is validated against
what s3Dgraphy declares, comes out compiled in `dist/`, hooks onto a thesaurus and gets an
identifier that holds over time. A list that stays in a table in a document does none of
this, and ages with the document that contains it.

## 2 · The vocabularies (referenced, not embedded)

The ICCD terminology tools are SKOS/RDF under the **CC BY-SA 3.0 IT** licence
(`dc:license` in the files, `A33_CCBYSA30IT`), edited by M. L. Mancinelli, with
C. Veninata, M. T. Natale, M. Porena.

This repository **does not copy them**: `vocabularies/schemes/*.yaml` declares the scheme,
the licence, the attribution and *where the file lives* (by default the
`Standard-catalografici/` checkout, overridable with `$STRATIGRAPH_ICCD_STANDARDS`).
The files in `vocabularies/fixtures/` are **invented** micro-schemes for testing, and say so
in their README.

## 3 · The code (reference implementation)

`src/`, `tests/`.

**EUPL-1.2 — CONFIRMED by E. Demetrescu on 2026-09-24.** It is the licence designed for
the software of European projects, it is weak copyleft, and it has a compatibility list
that includes GPL-3.0 and CC BY-SA 4.0 for combined works.

The **official text** is in `./LICENSE`, 287 lines, taken from `joinup.ec.europa.eu` (the
Commission's site) and not rewritten from memory: an approximate licence is worse than no
licence, because it looks like a licence.

`pyproject.toml` declares `EUPL-1.2` and carries alongside it, in a comment, the breakdown
by part — because a Python package's metadata can express ONE licence and this repository
has three.

## 4 · Attribution of the measurements

The measurements cited in the definitions and in the report (133 columns of `us_table`,
32 mapping targets, 276 records of SAS 3.00, 473 mm height of the US model) were taken on
disk on 4-5 September 2026 and are reproducible with the commands in
`docs/2026-09-20-NIGHT-la-scheda-diventa-un-dato.md`.
