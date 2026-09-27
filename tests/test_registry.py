"""What s3Dgraphy declares is READ, and when it cannot be read nothing is checked."""

import json

import pytest

from stratigraph_templates import registry as reg_mod


def test_registry_reads_the_datamodels(reg):
    # the numbers that the whole format leans on
    assert len(reg.node_types) > 40
    assert {"US", "USN", "TSU", "EpochNode", "AuthorNode", "LocationNodeGroup"} <= reg.node_types
    assert {"overlies", "cuts", "fills", "abuts", "equals", "bonded_to", "is_after"} <= reg.edge_types
    assert {"elevation", "color", "certainty_level"} <= reg.qualia
    assert reg.node_datamodel_version and reg.connections_version


def test_the_relations_the_iccd_sheet_needs_all_exist(reg):
    # the twelve boxes are twelve (edge_type, direction) pairs over SEVEN edge types
    needed = {"equals", "bonded_to", "abuts", "overlies", "cuts", "fills", "is_after"}
    assert needed <= reg.edge_types


def test_ap13_is_not_in_the_datamodel(reg):
    """Measured, and worth keeping measured: s3Dgraphy maps every contact relation
    to AP11 with a type_tag, and has no AP13_has_stratigraphic_relation at all."""
    assert "has_stratigraphic_relation" not in reg.edge_types
    assert "covers" not in reg.edge_types  # it is called 'overlies'


def test_no_permissive_third_mode(monkeypatch, tmp_path):
    """If neither s3Dgraphy nor a snapshot can be read, the answer is an error —
    never 'accept every node type'."""
    monkeypatch.setattr(reg_mod, "_config_dir_from_import", lambda: None)
    monkeypatch.setattr(reg_mod, "SNAPSHOT_PATH", tmp_path / "nope.json")
    with pytest.raises(reg_mod.RegistryUnavailable):
        reg_mod.registry()


def test_snapshot_round_trip(tmp_path):
    live = reg_mod.from_s3dgraphy()
    path = tmp_path / "snap.json"
    reg_mod.write_snapshot(path)
    back = reg_mod.from_snapshot(path)
    assert back.node_types == live.node_types
    assert back.edge_types == live.edge_types
    assert "snapshot" in back.provenance()


# ── one source (audit B8): the snapshot, checked against the working tree ───

def _live_or_skip():
    try:
        return reg_mod.from_s3dgraphy()
    except reg_mod.RegistryUnavailable as exc:
        pytest.skip(f"no s3Dgraphy on this machine: {exc}")


def test_the_snapshot_is_the_source_even_when_the_working_tree_is_here():
    _live_or_skip()
    reg = reg_mod.registry()
    assert reg.source.startswith("snapshot ")
    assert "agrees with the snapshot" in reg.live_check


def test_the_committed_snapshot_is_what_s3dgraphy_declares_today():
    """The alarm B8 lacked. RED here means s3Dgraphy moved: regenerate the
    snapshot (`registry-snapshot`), read the diff of registry/, rebuild dist/."""
    live = _live_or_skip()
    assert reg_mod.differences(reg_mod.from_snapshot(), live) == []


def test_a_divergence_stops_and_does_not_choose(monkeypatch):
    snap = reg_mod.from_snapshot()
    ahead = reg_mod.from_snapshot()
    ahead.connections_version = "9.9.9"
    ahead.edge_types = set(ahead.edge_types) | {"a_new_relation"}
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: ahead)
    with pytest.raises(reg_mod.RegistryDivergence) as exc:
        reg_mod.registry()
    text = str(exc.value)
    assert "will not choose" in text
    assert "a_new_relation" in text and "9.9.9" in text
    # --snapshot: the working tree is not consulted, and the line says so
    reg = reg_mod.registry(check_live=False)
    assert reg.connections_version == snap.connections_version
    assert "not consulted" in reg.provenance()


def test_a_commit_that_changes_nothing_declared_is_not_a_divergence(monkeypatch):
    other = reg_mod.from_snapshot()
    other.taken_from = {"git_commit": "f" * 40, "git_dirty": True}
    other.source = "elsewhere"
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: other)
    assert reg_mod.registry().source.startswith("snapshot ")


def test_the_snapshot_records_where_and_which_versions():
    doc = json.loads(reg_mod.SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert doc["snapshot_format"] == reg_mod.SNAPSHOT_FORMAT
    assert doc["taken_from"]["git_commit"] and doc["taken_on"]
    assert not doc["taken_from"]["config_dir"].startswith("/Users/")   # any machine
    for key in ("node_datamodel_version", "connections_version", "qualia_version",
                "em_ttl_version", "operations", "node_classes", "edges", "node_elements"):
        assert doc[key], key


def test_the_node_elements_are_read_from_the_node_datamodel(reg):
    """`definition` is declared ONCE on StratigraphicNode (node datamodel 1.6.9)
    and every stratigraphic class inherits it; an object that is not
    `kind: node_element` (FunctionalUnitNodeGroup.geometry_type_ref) is not one."""
    assert set(reg.node_elements) == {"definition"}
    rule = reg.node_elements["definition"]
    assert (rule["declared_on"], rule["em_json"], rule["value"]) == (
        "StratigraphicNode", "data.definition", "concept")
    assert {"StratigraphicUnit", "NegativeStratigraphicUnit",
            "SpecialFindUnit"} <= set(rule["applies_to"])
    assert "LocationNodeGroup" not in rule["applies_to"]


def test_the_older_spellings_say_which_name_they_spell(reg):
    spelt = {k: e["spelling_of"] for k, e in reg.edges.items() if e.get("spelling_of")}
    assert spelt == {"is_bonded_to": "bonded_to", "is_physically_equal_to": "equals"}
