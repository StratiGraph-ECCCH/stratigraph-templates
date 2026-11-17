# ICCD US 2021 — the versions of this definition

The version of the DEFINITION (SPEC §1.1), not of the standard (`standard.version`
stays «2021»). Old versions stay in `dist/schede/iccd-us-2021/`: a record
compiled with one of them is read back with that one (SPEC §9.4).

## 4.0.0 — 17 November 2026 · the definition is the property

Correction of E.D. on 17 November 2026 (MICRO-K-DEFINIZIONE-E-PASSI §A), which
withdraws the reading of MICRO-J §C. MAJOR: a record 3.0.0 would read
differently — DEFINIZIONE and INTERPRETAZIONE land elsewhere.

- **DEFINIZIONE** is the immediate explanation of what the unit is
  («fondazione in opera cementizia»): type `text`, the VALUE of the PropertyNode
  `definition` (as in the EM GraphML templates, 99 in TempluMare v10), with its
  chain. It was the term of the node element `data.definition` (1.0.1–3.0.0),
  now deprecated in s3Dgraphy (nodes 1.6.48). A term of iccd-us-definizione
  (em-us-definizione provisionally) MAY classify it on the same PropertyNode
  (`concept_scheme`, `data.concept`): one thing, labelled (SPEC §2.6).
- **INTERPRETAZIONE** is the DESCRIPTION of that same PropertyNode
  (`attaches_to: property:definition`, `property_name: description`): an
  `update_field` on the node DEFINIZIONE mints, after it. It was a PropertyNode
  `interpretation` of its own (1.0.0–3.0.0), still read back.
- **DESCRIZIONE** does not change: the unit's own description.
- Recipe numbers unchanged (`add_node` 36, `add_edge` 50, `update_field` 5,
  open 0): DEFINIZIONE now mints, INTERPRETAZIONE now updates.

**For StratiField** (not touched): its executor must resolve
`$field.definizione.prop` for INTERPRETAZIONE (the PropertyNode DEFINIZIONE
minted, or the unit's existing `definition`) and refuse INTERPRETAZIONE without
a definition; its reader (`values_from_graph`) reads DEFINIZIONE from the value
of the PropertyNode `definition` (the element `data.definition` only when there
is none), INTERPRETAZIONE from its description when it differs from the value,
else from an old PropertyNode `interpretation`.

## 3.0.0 — 17 November 2026 · the sheet says where it writes

Decided by E.D. on 17 November 2026 (MICRO-J-SCHEDA-SPEC-VOCABOLARI §B), on the
seven proposals that EMStudio's «Scheda» left after reading TempluMare v10
(MICRO-G-SCHEDE §11). MAJOR: a record 2.0.1 would read differently — verdicts
changed (AMBIENTE), boxes now land where they landed nowhere (ANNO, the dates),
the responsibles hang on the acts and not on the unit.

- **MISURE** declares the qualia it accepts (`accepts`): the ten dimensional
  qualia of the datamodel (height, width, depth, diameter, length, thickness,
  weight, volume, area, circumference). **QUOTE** declares the eight elevation
  qualia. A PropertyNode `height` is MISURE's without a sign. (SPEC §2.4)
- **FASE is the sub-epoch of PERIODO** (`sub_epoch_of: periodo`): PERIODO reads
  the parent epoch, FASE the child (`has_sub_epoch`). With FASE written the unit
  has_first_epoch the phase; the period is reached through has_sub_epoch.
- **The context boxes** are told apart by the place type the datamodel already
  has, LocationNodeGroup `kind` + `level` (`where`): LOCALITÀ
  `{toponym, sito}`, AREA / SAGGIO / SETTORE / QUADRATO `{study, <level>}`.
  **AMBIENTE** moves from FunctionalUnitNodeGroup (`is_in_functional_unit`) to
  a LocationNodeGroup `{functional, ambiente}` (`is_in_location`): a room is a
  place that answers «where» — the datamodel's own words for kind functional,
  and pyArchInit's `ambient` — while IDENTIFICATIVO keeps the Functional Unit
  alone. The level names are the module em-place-level.
- **The acts are defined** (`anchors`, SPEC §2.5): excavation (ANNO,
  RESPONSABILE SCIENTIFICO), field recording (DATA RILEVAMENTO, RESPONSABILE
  COMPILAZIONE), revision (DATA RIELABORAZIONE, RESPONSABILE RIELABORAZIONE).
  Each is an ActivityNodeGroup with `data.act_kind` (em-documentation-act),
  `data.act_start` and `has_author`; the unit is_in_activity of it. ANNO and the
  two dates are `act_start` of their act (they were `campaign_year`,
  `field_recording_date`, `revision_date` on anchors nobody defined, and landed
  nowhere); the three responsibles are authors of the act, not of the unit.
  The excavation act is shared by the units of one year.
- **Documents and finds are cited by name** (`find`): PIANTE, PROSPETTI,
  SEZIONI, FOTOGRAFIE `[name, url]` — a D.nn is found, never created by the
  sheet; a path still creates its document; RIFERIMENTI TABELLE MATERIALI
  `[name]`.
- **The record status** lands on the unit (`record_status`, SPEC §5):
  `data.record_status` = from_field | revised (em-record-status).
- The vocabularies list names em-place-level, em-documentation-act and
  em-record-status, so a reader vendors their labels.
- Nothing changes in the visual half: same boxes, labels, sheet.

## 2.0.1 — 1 October 2026

The definition does not change by a line; the compiled form does: the RDF
extension of an edge carries its guard (`riferimenti_tabelle_materiali`, AP21i
only into a US). PATCH.

## 2.0.0 — 28 September 2026

The nature of the formation (`formazione_natura`) passes from the unregistered
property name `formation_mode` to the datamodel's qualia `origin_type`
[natural, artificial]. MAJOR.

## 1.0.2 — 27 September 2026

The five vocabulary boxes CARRY CONCEPTS: the iccd-us-* schemes stay the norm,
only declared, and the em-us-* modules answer for them provisionally (SPEC §3.2).
PATCH.

## 1.0.1 — 21 October 2026

DEFINIZIONE becomes the node element `definition` (it was `vocabulary` without
a qualia: a required box that entered the graph by no door).

## 1.0.0 — 17 October 2026

The reading measured by the audit (a4b5365), the first a program compiles and
consumes.
