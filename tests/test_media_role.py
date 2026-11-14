"""Il ruolo nel gruppo (em-media-role): un modulo originato, estendibile dal
progetto (E.D., 14 nov 2026, MICRO-B-DOCUMENTI-MEDIA §1)."""
import pytest

from stratigraph_templates.vocab import Vocabularies

SCHEME = "em-media-role"
NS = "https://w3id.org/extendedmatrix/vocab/media-role/"
BASE = ["photogrammetry", "frontispiece", "detail", "vector_drawing", "raster_drawing",
        "model_3d", "orthophoto", "archival_documentation"]


@pytest.fixture(scope="module")
def vocabs():
    return Vocabularies.load()


def test_lo_schema_e_originato_ed_estendibile_dal_progetto(vocabs):
    s = vocabs.schemes[SCHEME]
    assert (s.origin, s.status, s.extensible) == ("originated", "resolvable", "project")
    assert s.version and s.license and s.uri == NS


def test_gli_otto_ruoli_si_risolvono_in_italiano_e_in_inglese(vocabs):
    concepts = vocabs.concepts(SCHEME)
    assert sorted(concepts) == sorted(NS + c for c in BASE)
    assert vocabs.resolve(SCHEME, NS + "frontispiece", "it").label == "frontespizio"
    assert vocabs.resolve(SCHEME, NS + "orthophoto", "en").label == "orthophoto"
    for c in BASE:
        for lang in ("it", "en"):
            assert vocabs.resolve(SCHEME, NS + c, lang).via == "scheme"
