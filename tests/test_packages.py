"""The sheets of a community package (MICRO-PL11, row W8 of the extensions plan).

Pinned on em-profiles' example package (copied into a temporary folder: the
compiler writes inside the package), read by s3Dgraphy:

* the registry of a package's sheet is the snapshot of the core + the
  package's overlay, and the snapshot is not touched;
* the package's carried vocabularies are schemes `<prefix>:<slug>`, resolved
  from the package's own .ttl;
* the compiled form lands where the manifest says, names the packages in its
  header (outside the digest), and `forms[].digest` is stamped so that
  s3Dgraphy's validator passes; a published version does not change;
* `verify_compiled` says each way a compiled form can be wrong.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

from stratigraph_templates.compile import FORMAT, compile_template, digest_of, dumps
from stratigraph_templates.loader import load_template
from stratigraph_templates.validate import validate_template

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT.parent / "em-profiles" / "examples"
SRC = ROOT.parent / "s3Dgraphy" / "src"

pk = pytest.importorskip("stratigraph_templates.packages")
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
pytest.importorskip("s3dgraphy.profiles")
if not (EXAMPLES / "esempio-statuaria" / "profile.json").is_file():
    pytest.skip("em-profiles is not checked out beside this repository", allow_module_level=True)

FORM = "stat-scheda-superficie"


@pytest.fixture
def pkg_dir(tmp_path):
    out = tmp_path / "esempio-statuaria"
    shutil.copytree(EXAMPLES / "esempio-statuaria", out)
    return out


@pytest.fixture
def mixed_dir(tmp_path):
    out = tmp_path / "esempio-statuaria-misto"
    shutil.copytree(EXAMPLES / "esempio-statuaria-misto", out)
    return out


def _compiled(d: Path) -> Path:
    return d / "forms" / FORM / "0.1.0.json"


def _manifest(d: Path) -> dict:
    return json.loads((d / "profile.json").read_text(encoding="utf-8"))


def _s3d_validate(d: Path):
    from s3dgraphy import profiles
    return profiles.validate(d)


# ── the overlay ──────────────────────────────────────────────────────────────

def test_the_overlay_is_the_core_plus_the_package_and_the_snapshot_is_untouched(pkg_dir, reg):
    p = pk.open_community_package(pkg_dir)
    before = set(reg.qualia)
    oreg = pk.registry_with(reg, [p])
    assert set(reg.qualia) == before and not reg.packages      # a copy
    added = set(oreg.qualia) - before
    assert added == {"stat:larghezza_biorbitale", "stat:altezza_facciale", "stat:indice_facciale",
                     "stat:area_integrazione", "stat:lavorazione", "stat:fase_di_superficie"}
    assert oreg.packages == [{"name": "esempio-statuaria", "prefix": "stat", "version": "0.1.0",
                              "iri": "https://w3id.org/extendedmatrix/profile/esempio-statuaria"}]
    assert "+ community packages: esempio-statuaria 0.1.0 (6 qualia of theirs)" in oreg.provenance()
    # the core is not redefined: its names and versions are the snapshot's
    assert before <= set(oreg.qualia)
    assert (oreg.node_types, oreg.edge_types, oreg.versions_line()) == (reg.node_types, reg.edge_types,
                                                                         reg.versions_line())


def test_the_carried_vocabularies_are_schemes_of_the_package(pkg_dir, vocab):
    p = pk.open_community_package(pkg_dir)
    assert sorted(p.schemes) == ["stat:fase-superficie", "stat:lavorazione", "stat:punti-volto"]
    s = p.schemes["stat:fase-superficie"]
    assert (s.origin, s.status, s.version) == ("originated", "resolvable", "0.1.0")
    assert s.uri.endswith("/vocab/fase-superficie/") and s.skos_file() == pkg_dir / "vocab" / "fase-superficie.ttl"
    v = pk.vocabularies_with(vocab, [p])
    assert set(vocab.schemes) < set(v.schemes) and "stat:fase-superficie" not in vocab.schemes
    pytest.importorskip("rdflib")
    doc = pk.scheme_file(v, "stat:fase-superficie", ["it", "en"])
    labels = {c["concept"].rsplit("/", 1)[-1]: c["labels"] for c in doc["concepts"]}
    assert labels["integrazione"] == {"it": "integrazione di restauro", "en": "restoration infill"}
    assert doc["unverified_languages"] == ["en"]


def test_without_the_package_the_sheet_says_where_its_qualia_come_from(pkg_dir, reg, vocab):
    t = load_template(pkg_dir / "forms" / FORM / "template.yaml")
    probs = validate_template(t, reg, known_schemes=vocab.scheme_ids(), strict=False)
    text = "\n".join(map(str, probs))
    assert "community package's (prefix 'stat')" in text and "package-build" in text


def test_a_quale_the_package_does_not_declare_is_named_with_the_package(pkg_dir, reg, vocab):
    src = pkg_dir / "forms" / FORM / "template.yaml"
    src.write_text(src.read_text(encoding="utf-8").replace("stat:indice_facciale", "stat:indice_inventato"),
                   encoding="utf-8")
    p = pk.open_community_package(pkg_dir)
    t = load_template(src)
    probs = validate_template(t, pk.registry_with(reg, [p]),
                              known_schemes=pk.vocabularies_with(vocab, [p]).scheme_ids(), strict=False)
    assert any("'stat:indice_inventato' is not declared by the package esempio-statuaria 0.1.0" in str(x)
               for x in probs)


# ── compiling ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("which", ["pkg_dir", "mixed_dir"])
def test_compiled_where_the_manifest_says_and_stamped(which, request, reg, vocab):
    d = request.getfixturevalue(which)
    data = d / "data" if which == "mixed_dir" else d
    out = _compiled(data)
    out.unlink()
    m = _manifest(data)
    m["forms"][0]["digest"] = "sha256:" + "0" * 64
    (data / "profile.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert not _s3d_validate(d).ok
    p, results, oreg = pk.build_package(d, reg, vocab)
    [r] = results
    assert not r.error, r.error
    assert r.path == out and r.what.startswith("written") and "stamped" in r.what
    doc = json.loads(out.read_text(encoding="utf-8"))
    head = doc["header"]
    assert doc["format"] == FORMAT and head["id"] == FORM and head["version"] == "0.1.0"
    assert head["packages"][0]["name"] == "esempio-statuaria"
    assert [v["id"] for v in head["vocabularies"]] == ["stat:fase-superficie", "stat:lavorazione"]
    assert doc["recipe"]["fields"]["larghezza"]["property"]["property_type"] == "stat:larghezza_biorbitale"
    assert doc["recipe"]["fields"]["fase"]["scheme"] == "stat:fase-superficie"
    assert head["digest"] == digest_of(doc) == r.digest
    raw = out.read_bytes()
    assert r.file_digest == "sha256:" + hashlib.sha256(raw).hexdigest() == _manifest(data)["forms"][0]["digest"]
    assert _s3d_validate(d).ok
    assert pk.verify_compiled(doc, _manifest(data)["forms"][0], raw, out.name) == []


def test_the_packages_are_outside_the_digest(pkg_dir, reg, vocab):
    p = pk.open_community_package(pkg_dir)
    t = load_template(pkg_dir / "forms" / FORM / "template.yaml")
    doc = compile_template(t, pk.registry_with(reg, [p]), pk.vocabularies_with(vocab, [p]))
    other = json.loads(json.dumps(doc))
    other["header"]["packages"][0]["version"] = "0.1.1"
    assert digest_of(other) == doc["header"]["digest"]


def test_a_second_build_changes_nothing_and_check_writes_nothing(pkg_dir, reg, vocab):
    _, [first], _ = pk.build_package(pkg_dir, reg, vocab)
    before = (_compiled(pkg_dir).read_bytes(), (pkg_dir / "profile.json").read_bytes())
    _, [again], _ = pk.build_package(pkg_dir, reg, vocab)
    assert again.what == "unchanged" and again.stamped
    _compiled(pkg_dir).unlink()
    _, [checked], _ = pk.build_package(pkg_dir, reg, vocab, write=False)
    assert checked.what == "would be written" and not _compiled(pkg_dir).exists()
    assert (pkg_dir / "profile.json").read_bytes() == before[1]


def test_a_published_version_does_not_change(pkg_dir, reg, vocab):
    pk.build_package(pkg_dir, reg, vocab)
    src = pkg_dir / "forms" / FORM / "template.yaml"
    src.write_text(src.read_text(encoding="utf-8").replace('"INDICE FACCIALE"', '"INDICE DEL VOLTO"'),
                   encoding="utf-8")
    _, [r], _ = pk.build_package(pkg_dir, reg, vocab)
    assert "A published version does not change" in r.error
    # the version raised, but the manifest still names 0.1.0.json
    src.write_text(src.read_text(encoding="utf-8").replace('version: "0.1.0"', 'version: "0.2.0"', 1),
                   encoding="utf-8")
    _, [r], _ = pk.build_package(pkg_dir, reg, vocab)
    assert "name the compiled file 0.2.0.json in the manifest" in r.error


def test_a_package_that_does_not_validate_is_not_compiled(pkg_dir, reg, vocab):
    m = _manifest(pkg_dir)
    m["prefix"] = "Stat!"
    (pkg_dir / "profile.json").write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(pk.PackageError, match="does not validate"):
        pk.build_package(pkg_dir, reg, vocab)


def test_the_command_line(pkg_dir, capsys):
    from stratigraph_templates.cli import main
    _compiled(pkg_dir).unlink()
    m = _manifest(pkg_dir)
    m["forms"][0]["digest"] = "sha256:" + "0" * 64
    (pkg_dir / "profile.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert main(["package-build", str(pkg_dir), "--check"]) == 0
    out = capsys.readouterr().out
    assert "+ community packages: esempio-statuaria 0.1.0" in out and "would be written" in out
    assert "(--check: not stamped)" in out and not _compiled(pkg_dir).exists()
    assert main(["package-build", str(pkg_dir)]) == 0
    assert _compiled(pkg_dir).is_file() and _s3d_validate(pkg_dir).ok
    assert main(["package-build", str(pkg_dir / "nothing")]) == 2


# ── verifying (what a reader does) ───────────────────────────────────────────

def test_verify_names_each_way_a_compiled_form_is_wrong(pkg_dir, reg, vocab):
    pk.build_package(pkg_dir, reg, vocab)
    out = _compiled(pkg_dir)
    form = _manifest(pkg_dir)["forms"][0]
    raw = out.read_bytes()
    doc = json.loads(raw)

    def codes(d, f=form, r=None, name=out.name):
        return [x["code"] for x in pk.verify_compiled(d, f, r if r is not None else dumps(d).encode(), name)]

    assert codes(doc, r=raw) == []
    edited = json.loads(raw)
    edited["visual"]["fields"][0]["labels"]["it"] = "US (modificata)"
    assert codes(edited) == ["file_digest", "content_digest"]
    assert codes(edited, f={"id": FORM}) == ["content_digest"]          # no digest in the manifest
    assert codes({"id": FORM, "fields": []}) == ["file_digest", "not_compiled"]
    assert codes(doc, f={"id": "other"}, r=raw) == ["id"]
    assert codes(doc, r=raw, name="0.2.0.json") == ["version"]
    said = pk.verify_compiled(edited, {"id": FORM})[0]
    assert "edited after compiling" in said["en"] and "modificato dopo la compilazione" in said["it"]
