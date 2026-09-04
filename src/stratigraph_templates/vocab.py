"""Vocabularies are referenced, never incorporated — and they are aligned.

Two decisions live here.

1. A definition *refers* to a thesaurus (a SKOS scheme with its own life cycle
   and its own licence), so this repository holds scheme DECLARATIONS, not
   terms.  A scheme may be ``declared`` (the standard prescribes a controlled
   vocabulary, but no machine-readable scheme is published) or ``resolvable``
   (a SKOS file can be read, in the repo or on the machine).
2. What lands in the graph is the CONCEPT, and the label is resolved at reading
   time in the requested language.  When the concept has no label in that
   language, an ALIGNMENT (``skos:exactMatch`` / ``closeMatch``) to another
   national vocabulary can supply one — which is the only reason an Italian and
   a Spanish excavator can end up looking at the same thing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMES_DIR = REPO_ROOT / "vocabularies" / "schemes"
ALIGNMENTS_DIR = REPO_ROOT / "vocabularies" / "alignments"

#: where the ICCD standards checkout lives on this machine (not in this repo)
ICCD_STANDARDS_ENV = "STRATIGRAPH_ICCD_STANDARDS"
ICCD_STANDARDS_DEFAULT = Path.home() / "Documents" / "GitHub" / "Standard-catalografici"

MATCH_KINDS = ("exactMatch", "closeMatch", "broadMatch", "narrowMatch")


class VocabularyError(ValueError):
    pass


@dataclass
class Scheme:
    id: str
    authority: str
    labels: Dict[str, str]
    status: str                       # declared | resolvable
    uri: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    binding_thes_id: Optional[str] = None
    fixture: bool = False
    resolve: Dict[str, str] = dc_field(default_factory=dict)
    note: Optional[str] = None
    path: Optional[str] = None

    def skos_file(self) -> Optional[Path]:
        kind = self.resolve.get("kind")
        if kind == "skos_file":
            return REPO_ROOT / self.resolve["path"]
        if kind == "external_skos_file":
            root = Path(os.environ.get(ICCD_STANDARDS_ENV, str(ICCD_STANDARDS_DEFAULT)))
            return root / self.resolve["path"]
        return None


@dataclass
class Alignment:
    source_scheme: str
    source_concept: str
    match: str
    target_scheme: str
    target_concept: str
    status: str = "proposed"          # proposed | verified
    by: Optional[str] = None
    note: Optional[str] = None


@dataclass
class Resolution:
    label: str
    lang: str
    via: str                          # scheme | alignment:<match> | record_label

    def __str__(self) -> str:
        return f"{self.label} [{self.lang} via {self.via}]"


def _read_skos(path: Path) -> Dict[str, Dict[str, str]]:
    """concept URI -> {lang: prefLabel}.  Uses rdflib when available."""
    try:
        from rdflib import Graph
        from rdflib.namespace import SKOS
    except Exception as exc:  # pragma: no cover - rdflib is an optional extra
        raise VocabularyError(f"cannot read {path.name}: rdflib is not installed ({exc})") from exc
    g = Graph()
    fmt = "turtle" if path.suffix in (".ttl", ".turtle") else "xml"
    g.parse(str(path), format=fmt)
    out: Dict[str, Dict[str, str]] = {}
    for s, _, o in g.triples((None, SKOS.prefLabel, None)):
        out.setdefault(str(s), {})[str(o.language or "")] = str(o)
    return out


class Vocabularies:
    def __init__(self, schemes: Dict[str, Scheme], alignments: List[Alignment]):
        self.schemes = schemes
        self.alignments = alignments
        self._concepts: Dict[str, Dict[str, Dict[str, str]]] = {}

    # -- loading -------------------------------------------------------------
    @classmethod
    def load(cls, schemes_dir: Path = SCHEMES_DIR, alignments_dir: Path = ALIGNMENTS_DIR) -> "Vocabularies":
        schemes: Dict[str, Scheme] = {}
        for p in sorted(schemes_dir.glob("*.yaml")):
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            s = doc.get("scheme")
            if not isinstance(s, dict) or "id" not in s:
                raise VocabularyError(f"{p.name}: a scheme file needs a 'scheme:' mapping with an id")
            if s.get("status") not in ("declared", "resolvable"):
                raise VocabularyError(
                    f"{p.name}: scheme '{s['id']}' status must be 'declared' or 'resolvable', "
                    f"got {s.get('status')!r}"
                )
            schemes[s["id"]] = Scheme(
                id=s["id"],
                authority=s.get("authority", "?"),
                labels=s.get("labels") or {},
                status=s["status"],
                uri=s.get("uri"),
                license=s.get("license"),
                attribution=s.get("attribution"),
                binding_thes_id=s.get("binding_thes_id"),
                fixture=bool(s.get("fixture", False)),
                resolve=s.get("resolve") or {},
                note=s.get("note"),
                path=str(p),
            )
        alignments: List[Alignment] = []
        for p in sorted(alignments_dir.glob("*.yaml")):
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for i, a in enumerate(doc.get("alignments") or []):
                where = f"{p.name}.alignments[{i}]"
                match = a.get("match")
                if match not in MATCH_KINDS:
                    raise VocabularyError(f"{where}: match must be one of {list(MATCH_KINDS)}, got {match!r}")
                for side in ("source", "target"):
                    if not isinstance(a.get(side), dict) or "scheme" not in a[side] or "concept" not in a[side]:
                        raise VocabularyError(f"{where}: '{side}' needs 'scheme' and 'concept'")
                    if a[side]["scheme"] not in schemes:
                        raise VocabularyError(
                            f"{where}: {side} scheme '{a[side]['scheme']}' has no declaration in "
                            f"{schemes_dir.name}/ (known: {sorted(schemes)})"
                        )
                alignments.append(
                    Alignment(
                        source_scheme=a["source"]["scheme"],
                        source_concept=a["source"]["concept"],
                        match=match,
                        target_scheme=a["target"]["scheme"],
                        target_concept=a["target"]["concept"],
                        status=a.get("status", "proposed"),
                        by=a.get("by"),
                        note=a.get("note"),
                    )
                )
        return cls(schemes, alignments)

    # -- resolution ----------------------------------------------------------
    def concepts(self, scheme_id: str) -> Dict[str, Dict[str, str]]:
        if scheme_id in self._concepts:
            return self._concepts[scheme_id]
        scheme = self.schemes.get(scheme_id)
        if scheme is None:
            raise VocabularyError(f"unknown vocabulary scheme '{scheme_id}'")
        path = scheme.skos_file()
        if scheme.status != "resolvable" or path is None:
            self._concepts[scheme_id] = {}
            return {}
        if not path.is_file():
            raise VocabularyError(
                f"scheme '{scheme_id}' is declared resolvable but its SKOS file is missing: {path}. "
                f"Set ${ICCD_STANDARDS_ENV} if the standards checkout lives elsewhere"
            )
        self._concepts[scheme_id] = _read_skos(path)
        return self._concepts[scheme_id]

    def _aligned(self, scheme_id: str, concept: str) -> List[Tuple[str, str, str]]:
        """(match, other_scheme, other_concept) for both directions."""
        out = []
        for a in self.alignments:
            if a.source_scheme == scheme_id and a.source_concept == concept:
                out.append((a.match, a.target_scheme, a.target_concept))
            elif a.target_scheme == scheme_id and a.target_concept == concept:
                out.append((a.match, a.source_scheme, a.source_concept))
        # exactMatch first: it is the only one that means "the same concept"
        return sorted(out, key=lambda x: MATCH_KINDS.index(x[0]))

    def resolve(
        self,
        scheme_id: str,
        concept: str,
        lang: str,
        record_label: Optional[str] = None,
    ) -> Resolution:
        """Label for a concept in ``lang``: own scheme, then alignments, then the
        label the record carried (declared as such)."""
        own = self.concepts(scheme_id).get(concept, {})
        if own.get(lang):
            return Resolution(own[lang], lang, "scheme")
        for match, other_scheme, other_concept in self._aligned(scheme_id, concept):
            other = self.concepts(other_scheme).get(other_concept, {})
            if other.get(lang):
                return Resolution(other[lang], lang, f"alignment:{match}:{other_scheme}")
        if record_label:
            return Resolution(record_label, lang, "record_label")
        raise VocabularyError(
            f"no label in '{lang}' for concept {concept} of scheme '{scheme_id}', and no alignment "
            f"supplies one. Declare an alignment in vocabularies/alignments/ or carry a label in the record"
        )

    def scheme_ids(self) -> set:
        return set(self.schemes)
