"""An edge's RDF extension travels WITH its guard (connections 1.6.34).

`has_documentation` goes out as P70i_is_documented_in always, and as
em:derivedFromDocument only from a USD (`mapping.extension_when.source_node_class`
= DocumentaryStratigraphicUnit, SeriesOfDocumentaryStratigraphicUnit): the domain
of em:derivedFromDocument is the documentary unit. A recipe that kept the
extension without the guard would tell whoever executes it to write the
predicate on a US. Pinned here:

* the snapshot records the guard, read from s3Dgraphy's exporter;
* a definition whose unit is decided and outside the guard (ICCD US: US/USN)
  carries no extension;
* one whose unit is decided and inside it (a USD sheet) carries it, unguarded;
* one that does not decide the unit, or decides it per record across the guard
  (ICCD US for `is_part_of` → AP21i, whose target must be a US and may be a
  USN), carries the extension WITH `extension_when`.
"""

import copy
from pathlib import Path

import pytest
import yaml

from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template, load_template

DERIVED = "https://w3id.org/em/ontology#derivedFromDocument"
AP21I = "http://www.cidoc-crm.org/extensions/crmarchaeo/AP21i_is_contained_in"
USD_CLASSES = ["DocumentaryStratigraphicUnit", "SeriesOfDocumentaryStratigraphicUnit"]
DOC_FIELDS = ("piante", "prospetti", "sezioni", "fotografie")


def _minimal():
    return yaml.safe_load((Path(__file__).parent / "fixtures" / "minimal.yaml").read_text())


def _with_documentation(node_types=None):
    """The minimal definition plus a photo box (has_documentation to a document)
    and, if given, a field that decides the unit's node type."""
    doc = _minimal()
    t = doc["template"]
    t["fields"].append({
        "id": "foto", "labels": {"it": "FOTO"}, "type": "resource_ref_list", "repeatable": True,
        "graph": {"verdict": "node", "node_type": "DocumentNode", "edge_type": "has_documentation",
                  "direction": "outgoing", "target": "DocumentNode"}})
    t["paragraphs"][0]["fields"].append("foto")
    cells = t["sheet"]["sides"][1]["rows"][0]["cells"]
    cells[0]["w"] = 50
    cells.append({"field": "foto", "w": 50})
    if node_types:
        t["fields"].append({
            "id": "tipo", "labels": {"it": "TIPO"}, "type": "choice",
            "options": [{"value": k, "labels": {"it": k}} for k in node_types],
            "graph": {"verdict": "node_type", "node_types": node_types}})
        t["paragraphs"][0]["fields"].append("tipo")
        t["sheet"]["sides"][0]["rows"][0]["cells"] = [
            {"field": "numero", "w": 30}, {"field": "copre", "w": 50}, {"field": "tipo", "w": 20}]
    return doc


def _compiled(tmp_path, doc, reg, vocab):
    p = tmp_path / "t.yaml"
    p.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return compile_template(load_template(p), reg, vocab)


def test_the_snapshot_records_the_guard(reg):
    rdf = reg.edges["has_documentation"]["rdf"]
    assert rdf["extension"] == DERIVED
    assert rdf["extension_when"] == {"source_node_class": USD_CLASSES}
    assert reg.edges["is_part_of"]["rdf"]["extension_when"] == {
        "target_node_class": ["StratigraphicUnit"]}
    # an unconditional extension records no guard
    assert reg.edges["has_author"]["rdf"]["extension"] and \
        reg.edges["has_author"]["rdf"]["extension_when"] is None


def test_iccd_us_writes_no_derived_from_document(reg, vocab):
    doc = compile_template(find_template("iccd-us-2021"), reg, vocab)
    for fid in DOC_FIELDS:
        rdf = doc["recipe"]["fields"][fid]["edge"]["rdf"]
        assert "extension" not in rdf and "extension_when" not in rdf, (fid, rdf)
        assert rdf["predicate"].endswith("P70i_is_documented_in")


def test_iccd_us_carries_ap21i_with_its_guard(reg, vocab):
    """The unit is US or USN by POSITIVA/NEGATIVA; AP21i ranges over A2, which
    is the US alone — so the recipe cannot decide, and says on what."""
    doc = compile_template(find_template("iccd-us-2021"), reg, vocab)
    rdf = doc["recipe"]["fields"]["riferimenti_tabelle_materiali"]["edge"]["rdf"]
    assert rdf["extension"] == AP21I
    assert rdf["extension_when"] == {"target_node_class": ["StratigraphicUnit"]}


def test_a_usd_sheet_carries_derived_from_document(tmp_path, reg, vocab):
    doc = _compiled(tmp_path, _with_documentation({"documentaria": "USD"}), reg, vocab)
    rdf = doc["recipe"]["fields"]["foto"]["edge"]["rdf"]
    assert rdf["extension"] == DERIVED
    assert "extension_when" not in rdf


def test_a_us_sheet_does_not(tmp_path, reg, vocab):
    doc = _compiled(tmp_path, _with_documentation({"positiva": "US"}), reg, vocab)
    assert "extension" not in doc["recipe"]["fields"]["foto"]["edge"]["rdf"]


@pytest.mark.parametrize("node_types", [None, {"positiva": "US", "documentaria": "USD"}],
                         ids=["type-open", "type-per-record"])
def test_an_undecided_unit_carries_the_extension_with_the_guard(tmp_path, reg, vocab, node_types):
    doc = _compiled(tmp_path, _with_documentation(node_types), reg, vocab)
    rdf = doc["recipe"]["fields"]["foto"]["edge"]["rdf"]
    assert rdf["extension"] == DERIVED
    assert rdf["extension_when"] == {"source_node_class": USD_CLASSES}


def test_the_guard_does_not_leak_into_the_snapshot_entry(tmp_path, reg, vocab):
    """`_guarded` works on a copy: compiling a US sheet must not strip the
    extension from the registry every later compilation reads."""
    before = copy.deepcopy(reg.edges["has_documentation"])
    _compiled(tmp_path, _with_documentation({"positiva": "US"}), reg, vocab)
    assert reg.edges["has_documentation"] == before
