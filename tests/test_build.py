"""The compiled form (SPEC §9): what `build` hands to a program.

Four promises are pinned here, each measured on the real definitions:

* every definition in templates/ compiles; one without a version, or with a
  verdict still `undecided`, does not;
* the digest moves with the definition and ONLY with it;
* the recipe of the ICCD US is what its verdicts say — an `add_edge` per edge
  box, nothing for a `none` box, US/USN from POSITIVA/NEGATIVA — and every name
  in it exists in the datamodel its header cites;
* a golden file, so an unintended change of the compiler shows up as a diff.
"""

import copy
import json
import os
from pathlib import Path

import pytest
import yaml

from stratigraph_templates import registry as reg_mod
from stratigraph_templates.compile import (
    PublishedVersionChanged, build, compile_template, digest_of, dumps, summary, write_compiled,
)
from stratigraph_templates.loader import find_template, load_record, load_template
from stratigraph_templates.loader import TemplateSyntaxError
from stratigraph_templates.validate import ValidationError

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).resolve().parent / "golden"
ALL = sorted(d.name for d in (ROOT / "templates").iterdir() if (d / "template.yaml").is_file())
ICCD = "iccd-us-2021"


@pytest.fixture(scope="module")
def iccd(reg, vocab):
    return compile_template(find_template(ICCD), reg, vocab)


def _written(tmp_path, doc, name="t.yaml"):
    p = tmp_path / name
    p.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return load_template(p)


def _minimal_doc():
    return yaml.safe_load((Path(__file__).parent / "fixtures" / "minimal.yaml").read_text())


# ── every definition compiles; the unfinished ones do not ───────────────────

@pytest.mark.parametrize("tid", ALL)
def test_every_definition_in_templates_compiles(tid, reg, vocab):
    doc = compile_template(find_template(tid), reg, vocab)
    assert doc["header"]["id"] == tid
    assert doc["header"]["version"]
    assert doc["header"]["digest"].startswith("sha256:")
    assert set(doc["recipe"]["fields"]) == {f["id"] for f in doc["visual"]["fields"]}


def test_a_definition_without_a_version_does_not_compile(tmp_path, reg, vocab):
    doc = _minimal_doc()
    del doc["template"]["version"]
    with pytest.raises(ValidationError) as exc:
        compile_template(_written(tmp_path, doc), reg, vocab)
    assert "template.version" in str(exc.value)
    assert "version of the norm" in str(exc.value)


def test_a_version_that_is_not_semver_does_not_compile(tmp_path, reg, vocab):
    doc = _minimal_doc()
    doc["template"]["version"] = "2021"          # the norm's year is not our version
    with pytest.raises(ValidationError, match="not semver"):
        compile_template(_written(tmp_path, doc), reg, vocab)


def test_an_undecided_verdict_does_not_compile(tmp_path, reg, vocab):
    doc = _minimal_doc()
    doc["template"]["fields"][-1]["graph"] = {"verdict": "undecided"}
    with pytest.raises(ValidationError, match="undecided"):
        compile_template(_written(tmp_path, doc), reg, vocab)


def test_the_extracted_xsd_draft_does_not_compile(reg, vocab):
    """The real draft: 257 undecided verdicts, and no version."""
    t = load_template(ROOT / "drafts" / "draft-sas-300.yaml")
    with pytest.raises(ValidationError) as exc:
        compile_template(t, reg, vocab)
    text = str(exc.value)
    assert "template.version" in text and "undecided" in text


def test_build_writes_the_valid_ones_and_reports_the_rest(tmp_path, reg, vocab):
    doc = _minimal_doc()
    del doc["template"]["version"]
    broken = _written(tmp_path, doc)
    out = tmp_path / "dist"
    written, refused = build([find_template(ICCD), broken], reg, vocab, out)
    assert [w[0] for w in written] == [ICCD]
    assert [r[0] for r in refused] == ["minimal"]
    version = find_template(ICCD).version
    assert (out / ICCD / f"{version}.json").is_file()
    index = json.loads((out / "index.json").read_text())
    assert index["schede"][ICCD]["latest"] == version
    assert "minimal" not in index["schede"]


# ── the record says which definition AND which version it followed ─────────

def test_the_record_declares_the_version_it_followed(tmp_path):
    rec = load_record(ROOT / "examples" / "us-3014-demo.yaml")
    assert (rec.template, rec.template_version) == (ICCD, find_template(ICCD).version)
    p = tmp_path / "r.yaml"
    p.write_text("record:\n  template: x\n  values: {}\n")
    with pytest.raises(TemplateSyntaxError, match="template_version"):
        load_record(p)


# ── the digest ───────────────────────────────────────────────────────────────

def test_the_digest_does_not_change_when_recompiled_identical(iccd, reg, vocab):
    again = compile_template(find_template(ICCD), reg, vocab)
    assert again["header"]["digest"] == iccd["header"]["digest"]
    assert dumps(again) == dumps(iccd)
    assert digest_of(iccd) == iccd["header"]["digest"]


def test_the_digest_changes_when_the_definition_changes(tmp_path, iccd, reg, vocab):
    doc = yaml.safe_load((ROOT / "templates" / ICCD / "template.yaml").read_text())
    doc["template"]["fields"][0]["labels"]["en"] = "SU number"
    changed = compile_template(_written(tmp_path, doc), reg, vocab)
    assert changed["header"]["digest"] != iccd["header"]["digest"]


def test_the_datamodel_line_is_outside_the_digest(iccd):
    """Recompiled against a later datamodel that changes nothing in the recipe,
    the definition is the same definition."""
    moved = copy.deepcopy(iccd)
    moved["header"]["datamodel"]["connections"] = "9.9.9"
    moved["header"]["compiled_by"]["version"] = "9.9.9"
    assert digest_of(moved) == iccd["header"]["digest"]
    moved["recipe"]["fields"]["copre"]["steps"][0]["emit"]["edge_type"] = "is_after"
    assert digest_of(moved) != iccd["header"]["digest"]


def test_a_published_version_cannot_change_under_the_same_number(tmp_path, iccd):
    write_compiled(iccd, tmp_path)
    assert write_compiled(iccd, tmp_path)[1] == "unchanged"
    other = copy.deepcopy(iccd)
    other["header"]["digest"] = "sha256:" + "0" * 64
    with pytest.raises(PublishedVersionChanged, match="raise template.version"):
        write_compiled(other, tmp_path)


# ── the recipe of the ICCD US ───────────────────────────────────────────────

def _edge_fields(t):
    return [f for f in t.fields if f.graph.verdict == "edge"]


def test_one_add_edge_per_edge_box(iccd):
    t = find_template(ICCD)
    fields = iccd["recipe"]["fields"]
    edge_ids = [f.id for f in _edge_fields(t)]
    assert len(edge_ids) == 13
    for fid in edge_ids:
        ops = [s["emit"]["op"] for s in fields[fid]["steps"]]
        assert ops == ["add_edge"], fid
        assert fields[fid]["each"] is True


def test_the_us_3014_record_expands_to_the_fifteen_edges_the_audit_expected(iccd):
    """13 boxes, 15 relations: the audit counted the RECORD (copre and
    posteriore_a hold two units each), the recipe counts the BOXES."""
    rec = load_record(ROOT / "examples" / "us-3014-demo.yaml")
    fields = iccd["recipe"]["fields"]
    n = sum(len(rec.values.get(fid) or [])
            for fid, e in fields.items() if e["verdict"] == "edge")
    assert n == 15


def test_a_none_box_produces_no_operation(iccd):
    fields = iccd["recipe"]["fields"]
    nones = [fid for fid, e in fields.items() if e["verdict"] == "none"]
    assert sorted(nones) == ["campionature", "ente_responsabile", "ufficio_mic"]
    for fid in nones:
        assert fields[fid]["steps"] == []
        assert fields[fid]["blocked_on"]["needs"]


def test_positive_and_negative_decide_US_and_USN(iccd):
    unit = iccd["recipe"]["unit"]
    assert unit["node_type"]["decided_by"] == "formazione_segno"
    table = unit["node_type"]["table"]
    assert {k: v["node_type"] for k, v in table.items()} == {"positiva": "US", "negativa": "USN"}
    assert table["negativa"]["class"] == "NegativeStratigraphicUnit"
    assert iccd["recipe"]["fields"]["formazione_segno"]["table"] == table


def test_the_box_that_is_the_nodes_description_writes_the_nodes_description(iccd):
    """Audit B9: the verdict said `description` and the value landed in a data
    key named after the box. The recipe addresses the node's own field."""
    steps = iccd["recipe"]["fields"]["descrizione"]["steps"]
    assert [s["emit"] for s in steps] == [
        {"op": "update_field", "node_id": "$unit", "field": "description", "value": "$value"}]


# ── DEFINIZIONE: an element of the node, not a qualia (E.D., 2026-10-21) ──────

@pytest.mark.parametrize("tid,fid", [(ICCD, "definizione"), ("es-ue-demo-2026", "definicion")])
def test_the_definition_is_the_units_own_element_written_by_update_field(tid, fid, reg, vocab):
    """One `update_field` on the em.json place the node datamodel declares, with
    the WHOLE term ({concept, label}): no PropertyNode, no has_property."""
    entry = compile_template(find_template(tid), reg, vocab)["recipe"]["fields"][fid]
    rule = reg.node_elements["definition"]
    assert [s["emit"] for s in entry["steps"]] == [
        {"op": "update_field", "node_id": "$unit", "field": rule["em_json"], "value": "$value"}]
    assert rule["em_json"] == "data.definition"          # read from s3Dgraphy, not typed
    assert entry["element"]["declared_on"] == "StratigraphicNode"
    assert entry["element"]["rdf"]["with_concept"] == "crm:P2_has_type"
    assert "resolve" not in entry and "property" not in entry


def test_the_unit_types_the_sheet_decides_inherit_the_element(iccd, reg):
    classes = {v["class"] for v in iccd["recipe"]["unit"]["node_type"]["table"].values()}
    assert classes == {"StratigraphicUnit", "NegativeStratigraphicUnit"}
    assert classes <= set(reg.node_elements["definition"]["applies_to"])


def test_an_element_written_by_the_wrong_field_type_does_not_compile(tmp_path, reg, vocab):
    doc = yaml.safe_load((ROOT / "templates" / ICCD / "template.yaml").read_text())
    f = next(x for x in doc["template"]["fields"] if x["id"] == "definizione")
    f["type"] = "text"
    f.pop("vocabulary")
    from stratigraph_templates.compile import CompileError
    with pytest.raises(CompileError, match="holds a 'concept' value"):
        compile_template(_written(tmp_path, doc), reg, vocab)


def test_an_older_spelling_of_an_edge_does_not_compile(tmp_path, reg, vocab):
    """`is_bonded_to` is read (spelling_of: bonded_to) and never written."""
    doc = yaml.safe_load((ROOT / "templates" / ICCD / "template.yaml").read_text())
    f = next(x for x in doc["template"]["fields"] if x["id"] == "si_lega_a")
    f["graph"]["edge_type"] = "is_bonded_to"
    from stratigraph_templates.compile import CompileError
    with pytest.raises(CompileError, match="older spelling of 'bonded_to'"):
        compile_template(_written(tmp_path, doc), reg, vocab)


def test_the_canonical_edge_names_its_spellings(iccd):
    f = iccd["recipe"]["fields"]
    assert f["si_lega_a"]["edge"]["spellings"] == ["is_bonded_to"]
    assert f["uguale_a"]["edge"]["spellings"] == ["is_physically_equal_to"]
    assert "spellings" not in f["copre"]["edge"]


def test_a_property_is_a_property_node_hung_by_has_property(iccd):
    entry = iccd["recipe"]["fields"]["consistenza"]
    add_node, add_edge = (s["emit"] for s in entry["steps"])
    assert add_node["node"]["node_type"] == "property"
    assert add_node["node"]["data"] == {"property_type": "texture"}
    assert add_node["node"]["description"] == "$value.concept"   # the CONCEPT (SPEC §3)
    assert add_edge == {"op": "add_edge", "edge_type": "has_property",
                        "source": "$unit", "target": "$prop"}


def test_the_reverse_box_is_the_same_edge_read_from_the_other_end(iccd):
    f = iccd["recipe"]["fields"]
    assert f["copre"]["steps"][0]["emit"] == {
        "op": "add_edge", "edge_type": "overlies", "source": "$unit", "target": "$item"}
    assert f["coperto_da"]["steps"][0]["emit"] == {
        "op": "add_edge", "edge_type": "overlies", "source": "$item", "target": "$unit"}


def test_the_aliases_that_are_one_rdf_property_are_declared(iccd):
    """`bonded_to` / `is_bonded_to` and `equals` / `is_physically_equal_to` are
    both valid and em.ttl maps each pair on one property. The definition is in
    order; the compiled form says the pair is one, so a consumer can too."""
    f = iccd["recipe"]["fields"]
    assert f["si_lega_a"]["edge"]["same_rdf_as"] == ["is_bonded_to"]
    assert f["si_lega_a"]["edge"]["rdf"]["subproperty"].endswith("#bondedTo")
    assert f["uguale_a"]["edge"]["same_rdf_as"] == ["is_physically_equal_to"]


def test_what_the_definition_leaves_open_is_declared_not_decided(iccd):
    open_ = {(o["field"], o["what"].split(":")[0]) for o in iccd["recipe"]["open"]}
    # DEFINIZIONE was open until 1.0.1: it is now the node element `definition`
    assert not any(f == "definizione" for f, _ in open_)
    assert set(iccd["recipe"]["anchors"]) == {"excavation_activity", "recording_act",
                                              "revision_act"}


def test_the_numbers(iccd):
    assert summary(iccd) == {
        "fields": 59,
        "verdicts": {"edge": 13, "identity": 1, "node": 18, "node_type": 1, "none": 3,
                     "property": 19, "vocabulary": 4},
        "steps": {"add_edge": 52, "add_node": 39, "update_field": 2},
        "open": 3,
    }


# ── the names come from s3Dgraphy, and the header says which s3Dgraphy ─────

def _names(doc):
    nodes, classes, edges, ops = set(), set(), set(), set()

    def walk(x):
        if isinstance(x, dict):
            if "op" in x:
                ops.add(x["op"])
                if x.get("edge_type"):
                    edges.add(x["edge_type"])
                nt = (x.get("node") or {}).get("node_type")
                if nt and not nt.startswith("$"):
                    nodes.add(nt)
            if "class" in x and "node_type" in x:
                classes.add(x["class"])
                nodes.add(x["node_type"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(doc["recipe"])
    return nodes, classes, edges, ops


@pytest.mark.parametrize("tid", ALL)
def test_every_name_in_the_recipe_exists_in_the_datamodel_of_the_header(tid, reg, vocab):
    doc = compile_template(find_template(tid), reg, vocab)
    snap = reg_mod.from_snapshot()
    head = doc["header"]["datamodel"]
    assert (head["nodes"], head["connections"], head["qualia"]) == (
        snap.node_datamodel_version, snap.connections_version, snap.qualia_version)
    nodes, classes, edges, ops = _names(doc)
    assert nodes and edges
    assert nodes <= set(snap.node_classes.values()), nodes - set(snap.node_classes.values())
    assert classes <= set(snap.node_classes), classes - set(snap.node_classes)
    assert edges <= set(snap.edges), edges - set(snap.edges)
    assert ops <= set(snap.operations) == {"add_node", "update_field", "remove_node",
                                           "add_edge", "remove_edge"}


# ── the golden file, and the committed dist/ ─────────────────────────────────

#: Header keys that say what the sheet was COMPILED WITH, not what it is: the
#: datamodel it was checked against (s3Dgraphy version, commit, fingerprint) and
#: the compiler's version. The golden leaves them out, so it moves when the
#: compiled sheet does and not after every snapshot; `header.digest` stays, and
#: `test_the_committed_dist_is_what_the_definitions_compile_to` pins the whole file.
GOLDEN_PROVENANCE = ("datamodel", "compiled_by")


def _without_provenance(doc):
    out = dict(doc)
    out["header"] = {k: v for k, v in doc["header"].items() if k not in GOLDEN_PROVENANCE}
    return out


def test_golden_iccd(iccd):
    """The compiled ICCD US, byte for byte, without its provenance. If this
    fails and the change is intended, regenerate with STRATIGRAPH_UPDATE_GOLDEN=1
    and read the diff."""
    path = GOLDEN / f"{ICCD}.json"
    body = dumps(_without_provenance(iccd))
    if os.environ.get("STRATIGRAPH_UPDATE_GOLDEN"):
        path.parent.mkdir(exist_ok=True)
        path.write_text(body, encoding="utf-8")
    assert body == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("tid", ALL)
def test_the_committed_dist_is_what_the_definitions_compile_to(tid, reg, vocab):
    """`dist/` is vendored by apps: a definition edited without `build` would
    leave them a stale copy that still looks official."""
    doc = compile_template(find_template(tid), reg, vocab)
    path = ROOT / "dist" / "schede" / tid / f"{doc['header']['version']}.json"
    assert path.is_file(), f"run `stratigraph-templates build` ({path} is missing)"
    assert path.read_text(encoding="utf-8") == dumps(doc)
