"""The in-memory shape of a sheet definition.

Three faces, one object: ``fields``/``paragraphs`` are the SUBSTANCE, every
field's ``graph`` is the BINDING, ``sheet`` is the SHEET.  Nothing here knows
about ICCD, Italian, or archaeology: that knowledge is in the YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional


class MissingLabel(KeyError):
    """A label was asked for in a language the definition does not declare.

    Raised — never silently substituted.  A sheet whose labels come from a
    generic dictionary prints 'Notifica' where the norm says 'FLOTTAZIONE';
    this exception is the reason that cannot happen here.
    """


FIELD_TYPES = (
    "identifier",
    "text",
    "longtext",
    "integer",
    "decimal",
    "date",
    "term",
    "term_list",
    "choice",
    "checkbox",
    "unit_ref_list",
    "record_ref_list",
    "resource_ref_list",
    "person_ref",
    "actor_ref",
    "epoch_ref",
    "activity_ref",
    "quantity_list",
)

#: The verdicts of the sieve: what a field MEANS for the graph.
GRAPH_VERDICTS = (
    "identity",   # part of the human identifier of the unit
    "property",   # a property (qualia) of a node that already exists
    "node_type",  # the discriminant that decides the node type
    "node",       # a node of its own, reached by an edge
    "edge",       # a relation towards another unit
    "vocabulary", # a controlled term (the CONCEPT lands in the graph)
    "none",       # presentation only: the sheet says it, the graph does not
)

EDGE_DIRECTIONS = ("outgoing", "incoming")


def label_of(labels: Dict[str, str], lang: str, what: str) -> str:
    """Resolve a label in ``lang`` or refuse.

    There is deliberately NO fallback to another language: rendering a sheet in
    a language its definition does not declare is an error, not a degraded mode.
    """
    if not isinstance(labels, dict) or lang not in labels or not str(labels.get(lang, "")).strip():
        raise MissingLabel(
            f"{what}: no label declared for language '{lang}' "
            f"(declared: {sorted(labels) if isinstance(labels, dict) else 'none'})"
        )
    return labels[lang]


@dataclass
class Standard:
    authority: str
    code: str
    version: str
    kind: str                    # field_model | catalogue_record
    title: Dict[str, str] = dc_field(default_factory=dict)
    source: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    invented: bool = False       # True = demo definition, not a real normative


@dataclass
class VocabularyRef:
    scheme: str
    binding: Optional[str] = None       # e.g. the ICCD binding_thesId
    level_expr: Optional[str] = None


@dataclass
class BlockedOn:
    """The sheet says it and the graph, today, cannot.

    Declared on purpose: a field whose honest binding would need a node type
    s3Dgraphy does not have is NOT quietly demoted to presentation — it carries
    what it would need and who was told.
    """
    needs: str
    reported: Optional[str] = None


@dataclass
class Option:
    value: str
    labels: Dict[str, str]

    def label(self, lang: str) -> str:
        return label_of(self.labels, lang, f"option '{self.value}'")


@dataclass
class GraphBinding:
    verdict: str
    node_type: Optional[str] = None
    node_types: Dict[str, str] = dc_field(default_factory=dict)  # term -> node_type
    edge_type: Optional[str] = None
    direction: Optional[str] = None
    qualia: Optional[str] = None
    property_name: Optional[str] = None
    attaches_to: str = "self"           # 'self' = the unit the sheet describes
    target: Optional[str] = None        # what the other end of an edge is
    blocked_on: Optional[BlockedOn] = None
    note: Optional[str] = None


@dataclass
class FieldProvenance:
    enabled: bool = True
    authors: List[str] = dc_field(default_factory=list)


@dataclass
class Field:
    id: str
    labels: Dict[str, str]
    type: str
    required: bool = False
    repeatable: bool = False
    max_len: Optional[str] = None
    help: Dict[str, str] = dc_field(default_factory=dict)
    vocabulary: Optional[VocabularyRef] = None
    options: List[Option] = dc_field(default_factory=list)
    graph: Optional[GraphBinding] = None
    provenance: Optional[FieldProvenance] = None
    note: Optional[str] = None          # divergence from a local tool, in the datum itself

    def label(self, lang: str) -> str:
        return label_of(self.labels, lang, f"field '{self.id}'")


@dataclass
class Paragraph:
    id: str
    labels: Dict[str, str]
    fields: List[str]

    def label(self, lang: str) -> str:
        return label_of(self.labels, lang, f"paragraph '{self.id}'")


@dataclass
class Cell:
    """One box on the paper. Either a field, a nested grid, or empty space."""
    field: Optional[str] = None
    block: Optional[str] = None            # id of a nested grid (for the label)
    block_labels: Dict[str, str] = dc_field(default_factory=dict)
    rows: List["Row"] = dc_field(default_factory=list)
    w: float = 100.0                       # percent of the content width
    label: str = "auto"                    # auto | none
    rotated: bool = False                  # vertical label, as on the ICCD sheet
    style: Optional[str] = None

    def block_label(self, lang: str) -> str:
        return label_of(self.block_labels, lang, f"block '{self.block}'")


@dataclass
class Row:
    h: float = 8.0                         # millimetres
    cells: List[Cell] = dc_field(default_factory=list)


@dataclass
class Side:
    id: str                                # recto | verso
    labels: Dict[str, str] = dc_field(default_factory=dict)
    rows: List[Row] = dc_field(default_factory=list)


@dataclass
class Sheet:
    page: str = "A4"
    margins_mm: Dict[str, float] = dc_field(default_factory=dict)
    sides: List[Side] = dc_field(default_factory=list)


@dataclass
class Identity:
    human_key: List[str] = dc_field(default_factory=list)
    pattern: str = ""
    uid_policy: str = "minted_by_creator"
    uid_opaque: bool = True
    uid_display: str = "on_request"
    uid_derive_from_human_key: bool = False
    deduplication: str = "by_human_key_in_context"


@dataclass
class Provenance:
    per_field: bool = True
    authors: List[str] = dc_field(default_factory=lambda: ["human", "ai"])
    states: List[str] = dc_field(default_factory=lambda: ["asserted", "ai_drafted", "human_validated"])
    clock: str = "s3dgraphy_crdt_field_clock"


@dataclass
class Template:
    id: str
    standard: Standard
    source_language: str
    languages: List[str]
    identity: Identity
    provenance: Provenance
    paragraphs: List[Paragraph]
    fields: List[Field]
    sheet: Sheet
    vocabularies: List[str] = dc_field(default_factory=list)
    graph_defaults: Dict[str, Any] = dc_field(default_factory=dict)
    notes: Dict[str, Any] = dc_field(default_factory=dict)
    path: Optional[str] = None

    def __post_init__(self) -> None:
        self._by_id = {f.id: f for f in self.fields}

    def field(self, fid: str) -> Field:
        try:
            return self._by_id[fid]
        except KeyError:
            raise KeyError(f"{self.id}: no field '{fid}' in this template") from None

    def has_field(self, fid: str) -> bool:
        return fid in self._by_id

    def title(self, lang: str) -> str:
        return label_of(self.standard.title, lang, f"template '{self.id}' title")

    def edges(self) -> List[Field]:
        return [f for f in self.fields if f.graph and f.graph.verdict == "edge"]


@dataclass
class Record:
    """Filled data for one unit — the other half of what a renderer needs."""
    template: str
    values: Dict[str, Any] = dc_field(default_factory=dict)
    field_provenance: Dict[str, Any] = dc_field(default_factory=dict)
    uid: Optional[str] = None
    path: Optional[str] = None
