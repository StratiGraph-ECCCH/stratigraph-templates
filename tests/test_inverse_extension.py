"""An edge's INVERSE extension travels with its guard, as the extension does.

`is_part_of` restates itself from the other side (connections 1.6.33,
`mapping.inverse_extension`): a special find (SF) that is part of a virtual
reassembled find (VSF) says that the VSF is reconstructed FROM it,
`<VSF> em:reconstructsFrom <SF>` — guarded on the logical ends, source
SpecialFindUnit and target VirtualSpecialFindUnit. Pinned here:

* the snapshot records the inverse and its guard, read from s3Dgraphy's exporter;
* a sheet whose unit is an SF and whose box creates a VSF carries the inverse,
  unguarded;
* one whose unit is an SF and whose box names a unit the creator finds carries
  it WITH `inverse_extension_when` (the target is undecided);
* one whose unit is a US carries no inverse (the ICCD US among them);
* the registry is not mutated by the compilation.
"""

import copy
from pathlib import Path

import yaml

from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template, load_template

RECONSTRUCTS = "https://w3id.org/em/ontology#reconstructsFrom"


def _sheet(unit, target):
    """The minimal definition, with the unit's type decided (`unit`) and a box
    `ricomposto_in` (is_part_of, outgoing): a node of class `target` the box
    creates, or — `target=None` — a unit the creator finds."""
    doc = yaml.safe_load((Path(__file__).parent / "fixtures" / "minimal.yaml").read_text())
    t = doc["template"]
    if target:
        box = {"type": "text", "graph": {
            "verdict": "node", "node_type": target, "edge_type": "is_part_of",
            "direction": "outgoing", "target": target}}
    else:
        box = {"type": "unit_ref_list", "repeatable": True, "graph": {
            "verdict": "edge", "edge_type": "is_part_of", "direction": "outgoing",
            "target": "stratigraphic_unit"}}
    t["fields"].append({"id": "ricomposto_in", "labels": {"it": "RICOMPOSTO IN"}, **box})
    t["fields"].append({"id": "tipo", "labels": {"it": "TIPO"}, "type": "choice",
                        "options": [{"value": k, "labels": {"it": k}} for k in unit],
                        "graph": {"verdict": "node_type", "node_types": unit}})
    t["paragraphs"][0]["fields"] += ["ricomposto_in", "tipo"]
    t["sheet"]["sides"][0]["rows"][0]["cells"] = [
        {"field": "numero", "w": 30}, {"field": "copre", "w": 30},
        {"field": "ricomposto_in", "w": 20}, {"field": "tipo", "w": 20}]
    return doc


def _rdf(tmp_path, doc, reg, vocab):
    p = tmp_path / "t.yaml"
    p.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    out = compile_template(load_template(p), reg, vocab)
    return out["recipe"]["fields"]["ricomposto_in"]["edge"]["rdf"]


def test_the_snapshot_records_the_inverse_and_its_guard(reg):
    rdf = reg.edges["is_part_of"]["rdf"]
    assert rdf["inverse_extension"] == RECONSTRUCTS
    assert rdf["inverse_extension_when"] == {
        "source_node_class": ["SpecialFindUnit"],
        "target_node_class": ["VirtualSpecialFindUnit"]}
    assert reg.edges["overlies"]["rdf"]["inverse_extension"] is None


def test_an_sf_sheet_creating_a_vsf_carries_the_inverse(tmp_path, reg, vocab):
    rdf = _rdf(tmp_path, _sheet({"reperto": "SF"}, "VSF"), reg, vocab)
    assert rdf["inverse_extension"] == RECONSTRUCTS
    assert "inverse_extension_when" not in rdf


def test_an_sf_sheet_naming_a_found_unit_carries_it_with_the_guard(tmp_path, reg, vocab):
    rdf = _rdf(tmp_path, _sheet({"reperto": "SF"}, None), reg, vocab)
    assert rdf["inverse_extension"] == RECONSTRUCTS
    assert rdf["inverse_extension_when"] == {"target_node_class": ["VirtualSpecialFindUnit"]}


def test_a_us_sheet_carries_no_inverse(tmp_path, reg, vocab):
    rdf = _rdf(tmp_path, _sheet({"positiva": "US"}, None), reg, vocab)
    assert "inverse_extension" not in rdf and "inverse_extension_when" not in rdf
    iccd = compile_template(find_template("iccd-us-2021"), reg, vocab)
    for fid, entry in iccd["recipe"]["fields"].items():
        assert "inverse_extension" not in ((entry.get("edge") or {}).get("rdf") or {}), fid


def test_the_inverse_guard_does_not_leak_into_the_snapshot_entry(tmp_path, reg, vocab):
    before = copy.deepcopy(reg.edges["is_part_of"])
    _rdf(tmp_path, _sheet({"positiva": "US"}, None), reg, vocab)
    assert reg.edges["is_part_of"] == before
