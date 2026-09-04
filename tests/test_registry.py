"""What s3Dgraphy declares is READ, and when it cannot be read nothing is checked."""

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
