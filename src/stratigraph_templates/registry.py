"""What s3Dgraphy actually declares — read, never guessed.

A graph binding may only name a node type, an edge type or a qualia that
s3Dgraphy has *today*.  This module is the single place that knows them, and it
refuses to answer when it cannot read them: a permissive fallback would turn
"do not add node types" from a rule into a wish.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = REPO_ROOT / "registry" / "s3dgraphy-snapshot.json"

#: Where to look for a source checkout of s3Dgraphy, in order.
_CANDIDATE_SRC = (
    os.environ.get("STRATIGRAPH_S3DGRAPHY_SRC"),
    str(REPO_ROOT.parent / "s3Dgraphy" / "src"),
)


class RegistryUnavailable(RuntimeError):
    """Neither s3Dgraphy nor a snapshot could be read."""


@dataclass
class Registry:
    node_types: Set[str] = dc_field(default_factory=set)
    edge_types: Set[str] = dc_field(default_factory=set)
    qualia: Set[str] = dc_field(default_factory=set)
    mapping_targets: Dict[str, str] = dc_field(default_factory=dict)  # em_type -> cidoc class
    node_datamodel_version: str = ""
    connections_version: str = ""
    qualia_version: str = ""
    source: str = ""

    # -- provenance line, printed by every command that validates -------------
    def provenance(self) -> str:
        return (
            f"s3Dgraphy registry: nodes {self.node_datamodel_version} · "
            f"connections {self.connections_version} · qualia {self.qualia_version} "
            f"({len(self.node_types)} node types, {len(self.edge_types)} edge types, "
            f"{len(self.qualia)} qualia, {len(self.mapping_targets)} mapping targets) "
            f"[source: {self.source}]"
        )

    def to_json(self) -> Dict:
        return {
            "source": self.source,
            "node_datamodel_version": self.node_datamodel_version,
            "connections_version": self.connections_version,
            "qualia_version": self.qualia_version,
            "node_types": sorted(self.node_types),
            "edge_types": sorted(self.edge_types),
            "qualia": sorted(self.qualia),
            "mapping_targets": dict(sorted(self.mapping_targets.items())),
        }


def _config_dir_from_import() -> Optional[Path]:
    """Import s3dgraphy (installed, or from a sibling checkout) and locate its JSON_config."""
    for cand in _CANDIDATE_SRC:
        if cand and Path(cand).is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
    try:
        import s3dgraphy  # noqa: WPS433
    except Exception:
        return None
    cfg = Path(s3dgraphy.__file__).resolve().parent / "JSON_config"
    return cfg if cfg.is_dir() else None


def _collect_node_types(node_datamodel: Dict) -> Set[str]:
    out: Set[str] = set()
    for section, entries in node_datamodel.items():
        if not isinstance(entries, dict) or section == "referenced_ontology_versions":
            continue
        for name, body in entries.items():
            if name.startswith("_"):
                continue
            out.add(name)
            if isinstance(body, dict):
                subs = body.get("subtypes")
                if isinstance(subs, dict):
                    out.update(k for k in subs if not k.startswith("_"))
    return out


def _collect_qualia(qualia_doc: Dict) -> Set[str]:
    out: Set[str] = set()
    for cat in qualia_doc.get("qualia_categories", []):
        for sub in (cat.get("subcategories") or {}).values():
            for q in sub.get("qualia", []):
                if isinstance(q, dict) and q.get("id"):
                    out.add(q["id"])
    return out


def from_s3dgraphy() -> Registry:
    cfg = _config_dir_from_import()
    if cfg is None:
        raise RegistryUnavailable("s3dgraphy is not importable")
    nodes = json.loads((cfg / "s3Dgraphy_node_datamodel.json").read_text(encoding="utf-8"))
    conns = json.loads((cfg / "s3Dgraphy_connections_datamodel.json").read_text(encoding="utf-8"))
    qual = json.loads((cfg / "em_qualia_types.json").read_text(encoding="utf-8"))

    targets: Dict[str, str] = {}
    try:
        from s3dgraphy.mappings.authoring import target_groups

        for group in target_groups():
            for t in group.get("targets", []):
                targets[t["em_type"]] = t.get("cidoc", "")
    except Exception:  # the curated catalogue is a bonus, not a precondition
        targets = {}

    return Registry(
        node_types=_collect_node_types(nodes),
        edge_types={k for k in conns.get("edge_types", {}) if not k.startswith("_")},
        qualia=_collect_qualia(qual),
        mapping_targets=targets,
        node_datamodel_version=str(nodes.get("s3Dgraphy_data_model_version", "?")),
        connections_version=str(conns.get("s3Dgraphy_connections_model_version", "?")),
        qualia_version=str((qual.get("metadata") or {}).get("version", "?")),
        source=f"s3dgraphy at {cfg}",
    )


def from_snapshot(path: Optional[Path] = None) -> Registry:
    # resolved at call time on purpose: a default argument would freeze the path
    # at import and make the "nothing readable" case silently succeed
    path = path or SNAPSHOT_PATH
    if not path.is_file():
        raise RegistryUnavailable(f"no registry snapshot at {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    return Registry(
        node_types=set(doc["node_types"]),
        edge_types=set(doc["edge_types"]),
        qualia=set(doc["qualia"]),
        mapping_targets=dict(doc.get("mapping_targets", {})),
        node_datamodel_version=doc.get("node_datamodel_version", "?"),
        connections_version=doc.get("connections_version", "?"),
        qualia_version=doc.get("qualia_version", "?"),
        source=f"snapshot {path.name} (taken from {doc.get('source', '?')})",
    )


def registry(prefer_snapshot: bool = False) -> Registry:
    """The live registry if s3Dgraphy can be read, else the recorded snapshot.

    Raises RegistryUnavailable when neither exists — there is no third mode in
    which every node type is accepted.
    """
    order = (from_snapshot, from_s3dgraphy) if prefer_snapshot else (from_s3dgraphy, from_snapshot)
    errors: List[str] = []
    for fn in order:
        try:
            return fn()
        except RegistryUnavailable as exc:
            errors.append(str(exc))
    raise RegistryUnavailable(
        "cannot read what s3Dgraphy declares, so no graph binding can be checked: "
        + "; ".join(errors)
    )


def write_snapshot(path: Optional[Path] = None) -> Registry:
    path = path or SNAPSHOT_PATH
    reg = from_s3dgraphy()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg.to_json(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return reg
