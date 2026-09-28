"""Il giro di chiusura (28 set 2026): il datamodel fa fede, e due qualia nuove.

* **ICCD 2.0.0** — la natura della formazione (`formazione_natura`) scriveva
  `formation_mode`, property_name mai registrata, con valori italiani; ora scrive la
  qualia `origin_type` del datamodel con le sue chiavi (`natural`/`artificial`), la
  stessa del DAI (`isNatural`). Le etichette del foglio restano NATURALE/ARTIFICIALE.
  È un verdetto cambiato: MAJOR (SPEC §1.1), e le versioni vecchie restano in `dist/`
  perché un record 1.0.2 si rilegge con la 1.0.2.
* **DAI 0.2.0** — `featureForm` e `featureBorders` non sono più bloccati (D7, D8):
  `vocabulary` sulle qualia `feature_shape` e `boundary_distinctness` (qualia
  1.6.2), con i valuelist DAI come vocabolario.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "schede"


@pytest.fixture(scope="module")
def iccd():
    return find_template("iccd-us-2021")


@pytest.fixture(scope="module")
def dai():
    return find_template("dai-idaifield-layer-2026")


def _field(t, fid):
    return next(f for f in t.fields if f.id == fid)


def test_iccd_la_natura_scrive_la_qualia_del_datamodel(iccd, reg):
    assert iccd.version == "2.0.0"
    f = _field(iccd, "formazione_natura")
    assert f.graph.verdict == "property" and f.graph.qualia == "origin_type"
    assert not f.graph.property_name
    assert [o.value for o in f.options] == ["natural", "artificial"]
    assert [o.labels["it"] for o in f.options] == ["NATURALE", "ARTIFICIALE"]
    assert "origin_type" in reg.qualia


def test_iccd_il_compilato_dice_qualia_registrata(iccd, reg, vocab):
    step = compile_template(iccd, reg, vocab)["recipe"]["fields"]["formazione_natura"]
    assert step["property"] == {"property_type": "origin_type", "registered_qualia": True}


def test_iccd_le_versioni_vecchie_restano_e_dicono_ancora_formation_mode():
    old = json.loads((DIST / "iccd-us-2021" / "1.0.2.json").read_text(encoding="utf-8"))
    prop = old["recipe"]["fields"]["formazione_natura"]["property"]
    assert prop == {"property_type": "formation_mode", "registered_qualia": False}
    index = json.loads((DIST / "index.json").read_text(encoding="utf-8"))["schede"]["iccd-us-2021"]
    assert index["latest"] == "2.0.0"
    assert {"1.0.0", "1.0.1", "1.0.2", "2.0.0"} <= set(index["versions"])


@pytest.mark.parametrize("fid,qualia,scheme", [
    ("featureForm", "feature_shape", "idai-field-feature-featureform-default"),
    ("featureBorders", "boundary_distinctness", "idai-field-feature-featureborders-default"),
])
def test_dai_forma_e_limiti_sono_vocabolario_sulle_qualia_nuove(dai, reg, fid, qualia, scheme):
    assert dai.version == "0.2.0"
    f = _field(dai, fid)
    assert f.graph.verdict == "vocabulary" and f.graph.qualia == qualia
    assert not f.graph.blocked_on
    assert f.vocabulary.scheme == scheme
    assert qualia in reg.qualia, "lo snapshot del registro deve venire da s3Dgraphy qualia >= 1.6.2"


def test_dai_restano_aperte_le_altre_domande(dai):
    blocked = {f.id for f in dai.fields if f.graph.blocked_on}
    assert len(blocked) == 12 and not blocked & {"featureForm", "featureBorders"}


# ── le due dipendenze fuori dal repository (README) ──────────────────────────

def test_senza_i_checkout_validate_lo_dice_in_una_riga(tmp_path, monkeypatch, vocab):
    monkeypatch.setenv("STRATIGRAPH_IDAI_FIELD", str(tmp_path / "manca"))
    monkeypatch.setenv("STRATIGRAPH_ICCD_STANDARDS", str(tmp_path / "manca-anche"))
    lines = vocab.missing_checkouts()
    assert len(lines) == 2
    idai, = [l for l in lines if "iDAI.field" in l]
    assert "4b5c1e2" in idai and "STRATIGRAPH_IDAI_FIELD" in idai and "github.com/dainst" in idai
    assert any("STRATIGRAPH_ICCD_STANDARDS" in l for l in lines)


def test_un_checkout_senza_il_commit_lo_dice(tmp_path, monkeypatch, vocab):
    import subprocess
    repo = tmp_path / "idai-field"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    monkeypatch.setenv("STRATIGRAPH_IDAI_FIELD", str(repo))
    line, = [l for l in vocab.missing_checkouts() if "iDAI.field" in l]
    assert "does not hold commit 4b5c1e2" in line and "fetch" in line


def test_validate_e_build_stampano_l_avviso_e_non_falliscono(tmp_path, monkeypatch, capsys):
    from stratigraph_templates import cli
    monkeypatch.setenv("STRATIGRAPH_IDAI_FIELD", str(tmp_path / "manca"))
    assert cli.main(["--snapshot", "validate", "dai-idaifield-layer-2026"]) == 0
    assert "no iDAI.field checkout at" in capsys.readouterr().out
