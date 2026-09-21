"""Uno schema ORIGINATO si comporta come gli altri, e in più risponde di sé.

Il modulo Behrensmeyer è il banco di prova della governance: se questi test
passano, la struttura regge per la tafonomia litica, per i lessici locali dei
partner e per qualunque cosa venga dopo.
"""
import pytest

from stratigraph_templates.vocab import Vocabularies, VocabularyError

SCHEME = "em-taph-weathering"
NS = "https://w3id.org/extendedmatrix/vocab/taph-weathering/"


@pytest.fixture(scope="module")
def vocabs():
    return Vocabularies.load()


def test_lo_schema_e_originato_e_si_dichiara(vocabs):
    s = vocabs.schemes[SCHEME]
    assert s.origin == "originated"
    assert s.status == "resolvable"
    # le tre cose senza cui un modulo nostro è incitabile
    assert s.version and s.license and s.uri


def test_i_sei_stadi_si_risolvono_in_due_lingue(vocabs):
    for n in range(6):
        concept = f"{NS}stage-{n}"
        for lang in ("en", "it"):
            r = vocabs.resolve(SCHEME, concept, lang)
            assert r.label, f"stage-{n} non ha etichetta in {lang}"
            assert r.via == "scheme", (
                f"stage-{n}/{lang} risolto via {r.via}: un modulo nostro deve "
                f"portare le proprie etichette, non prenderle in prestito"
            )
        assert str(n) in vocabs.resolve(SCHEME, concept, "en").label


def test_l_ancoraggio_ad_aat_e_broad_non_exact(vocabs):
    """AAT ha UN concetto di weathering, non gli stadi: exactMatch sarebbe falso."""
    ours = {f"{NS}stage-{n}" for n in range(6)}
    anchors = [a for a in vocabs.alignments if a.source_concept in ours]
    assert len(anchors) == 6
    assert {a.match for a in anchors} == {"broadMatch"}
    assert all(a.status == "proposed" for a in anchors), (
        "un allineamento non verificato da una persona resta 'proposed': "
        "è la distinzione che nella metodologia ARIADNE non esiste"
    )


def test_originato_senza_versione_e_rifiutato(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "scheme:\n"
        "  id: sg-bad\n"
        "  authority: StratiGraph\n"
        "  origin: originated\n"
        "  status: declared\n"
        "  labels: {en: 'x'}\n"
        "  license: 'CC BY 4.0'\n"
        "  uri: 'https://example.org/x/'\n",
        encoding="utf-8",
    )
    with pytest.raises(VocabularyError, match="version"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


def test_origin_ignoto_e_rifiutato(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "scheme:\n  id: sg-bad\n  authority: X\n  origin: nostro\n"
        "  status: declared\n  labels: {en: 'x'}\n",
        encoding="utf-8",
    )
    with pytest.raises(VocabularyError, match="origin"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)
