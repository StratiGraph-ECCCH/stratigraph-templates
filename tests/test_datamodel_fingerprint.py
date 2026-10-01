"""The datamodel's fingerprint travels with every compiled sheet, and a stale
snapshot is refused by NAME.

s3Dgraphy computes one digest over the datamodel JSONs a consumer copies
(`api.datamodel_fingerprint`). The snapshot records it, the header of every
compiled sheet carries it beside the versions, and `validate` compares the
snapshot's with the working tree's: a divergence stops the command and says
which datamodel moved (`nodes 1.6.12 vs 1.6.17`), not only that something did.
"""

import copy
import json

import pytest

from stratigraph_templates import cli
from stratigraph_templates import registry as reg_mod
from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template

NAMES = ("nodes", "node_registry", "connections", "visual_rules", "qualia", "translations")


def _live_or_skip():
    try:
        return reg_mod.from_s3dgraphy()
    except reg_mod.RegistryUnavailable as exc:
        pytest.skip(f"no s3Dgraphy on this machine: {exc}")


def test_the_snapshot_records_the_fingerprint(reg):
    fp = reg.datamodel
    assert fp["digest"].startswith("sha256:") and len(fp["digest"]) == 71
    assert tuple(fp["versions"]) == NAMES
    assert fp["versions"]["nodes"] == reg.node_datamodel_version


def test_the_fingerprint_is_s3dgraphys_not_restated_here():
    live = _live_or_skip()
    from s3dgraphy import api
    assert live.datamodel["digest"] == api.datamodel_fingerprint()["digest"]


def test_a_compiled_sheet_carries_the_fingerprint(reg, vocab):
    doc = compile_template(find_template("iccd-us-2021"), reg, vocab)
    head = doc["header"]["datamodel"]
    assert head["digest"] == reg.datamodel["digest"]
    for name in NAMES:
        assert head[name] == reg.datamodel["versions"][name], name
    # the files the sheet was built from, each with its own digest (dev25)
    assert tuple(head["files"]) == reg_mod.DATAMODEL_READS
    for name in reg_mod.DATAMODEL_READS:
        assert head["files"][name] == {"digest": reg.datamodel["digests"][name],
                                       "version": reg.datamodel["versions"][name]}, name
    # the sheet's own digest is another thing, and the datamodel stays outside it
    assert doc["header"]["digest"] != head["digest"]


def test_the_committed_dist_carries_the_fingerprint_of_the_snapshot(reg):
    """The CURRENT version of every definition carries it. An older published
    version was compiled before the fingerprint existed and never changes
    (a published version is immutable): it has no digest, and a reader says so."""
    root = reg_mod.REPO_ROOT / "dist" / "schede"
    current = {d.name: find_template(d.name).version
               for d in (reg_mod.REPO_ROOT / "templates").iterdir()
               if (d / "template.yaml").is_file()}
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    checked = 0
    for tid, version in current.items():
        head = json.loads((root / tid / f"{version}.json").read_text(encoding="utf-8"))
        assert head["header"]["datamodel"]["digest"] == reg.datamodel["digest"], tid
        entry = index["schede"][tid]["versions"][version]
        assert entry["datamodel"]["digest"] == reg.datamodel["digest"], tid
        checked += 1
    assert checked == len(current) > 0


def _stale(snapshot: reg_mod.Registry, **versions) -> reg_mod.Registry:
    stale = copy.deepcopy(snapshot)
    stale.datamodel["versions"].update(versions)
    stale.datamodel["digest"] = "sha256:" + "0" * 64
    return stale


def test_an_old_snapshot_fails_validate_with_the_name_of_the_datamodel(monkeypatch, capsys):
    snap = reg_mod.from_snapshot()
    live = reg_mod.from_snapshot()
    old = _stale(snap, nodes="1.6.12")
    monkeypatch.setattr(reg_mod, "from_snapshot", lambda path=None: copy.deepcopy(old))
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: live)
    code = cli.main(["validate", "iccd-us-2021"])
    err = capsys.readouterr().err
    assert code != 0
    assert f"datamodel: nodes 1.6.12 vs {live.datamodel['versions']['nodes']}" in err


def test_same_versions_different_content_is_still_named(monkeypatch):
    live = reg_mod.from_snapshot()
    edited = copy.deepcopy(live)
    edited.datamodel["digests"]["qualia"] = "sha256:" + "1" * 64
    edited.datamodel["digest"] = "sha256:" + "1" * 64
    assert reg_mod.differences(edited, live) == [
        f"datamodel: qualia {live.datamodel['versions']['qualia']}: "
        "same version, different content"]


def _live_moved(name: str) -> reg_mod.Registry:
    """The working tree as it would be after a change to `name` alone: a new
    version, a new digest for that file, a new one digest."""
    live = reg_mod.from_snapshot()
    live.datamodel["versions"][name] = "9.9.9"
    live.datamodel["digests"][name] = "sha256:" + "9" * 64
    live.datamodel["digest"] = "sha256:" + "9" * 64
    return live


@pytest.mark.parametrize("name", ["visual_rules", "translations"])
def test_a_change_to_a_file_templates_does_not_read_does_not_stop_validate(
        monkeypatch, capsys, name):
    """D4 of the MICRO-DERIVA: templates reads four datamodel files, and the
    visual rules and the translations are not among them."""
    assert name not in reg_mod.DATAMODEL_READS
    snap, live = reg_mod.from_snapshot(), _live_moved(name)
    monkeypatch.setattr(reg_mod, "from_snapshot", lambda path=None: copy.deepcopy(snap))
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: copy.deepcopy(live))
    assert reg_mod.differences(snap, live) == []
    code = cli.main(["validate", "iccd-us-2021"])
    assert code == 0, capsys.readouterr().err


def test_a_change_to_the_node_datamodel_stops_validate_and_names_the_file(
        monkeypatch, capsys):
    snap, live = reg_mod.from_snapshot(), _live_moved("nodes")
    monkeypatch.setattr(reg_mod, "from_snapshot", lambda path=None: copy.deepcopy(snap))
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: copy.deepcopy(live))
    code = cli.main(["validate", "iccd-us-2021"])
    err = capsys.readouterr().err
    assert code != 0
    assert f"datamodel: nodes {snap.datamodel['versions']['nodes']} vs 9.9.9" in err


def test_the_snapshot_records_the_whole_fingerprint_and_compares_four():
    doc = json.loads(reg_mod.SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert tuple(doc["datamodel"]["versions"]) == NAMES and doc["datamodel"]["digest"]
    read = reg_mod.from_snapshot().content()["datamodel"]
    assert tuple(read["versions"]) == reg_mod.DATAMODEL_READS
    assert "digest" not in read


def test_a_format_3_snapshot_is_read_and_its_divergence_named(tmp_path, monkeypatch):
    doc = json.loads(reg_mod.SNAPSHOT_PATH.read_text(encoding="utf-8"))
    doc["snapshot_format"] = 3
    doc.pop("datamodel")
    doc["node_datamodel_version"] = "1.6.12"
    old = tmp_path / "s3dgraphy-snapshot.json"
    old.write_text(json.dumps(doc), encoding="utf-8")
    live = reg_mod.from_snapshot()
    monkeypatch.setattr(reg_mod, "SNAPSHOT_PATH", old)
    monkeypatch.setattr(reg_mod, "from_s3dgraphy", lambda: live)
    with pytest.raises(reg_mod.RegistryDivergence) as exc:
        reg_mod.registry()
    first = exc.value.differences[0]
    assert first == f"datamodel: nodes 1.6.12 vs {live.node_datamodel_version}"
