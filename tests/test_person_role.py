"""Il ruolo di una persona in un atto (em-person-role): un modulo originato,
piccolo, solo per ciò che il tipo dell'atto non dice (E.D., 27 nov 2026,
MICRO-RUOLI-PERSONE). La fonte è ExtendedMatrix/vocabularies; qui la copia."""
import pytest

from stratigraph_templates.vocab import Vocabularies

SCHEME = "em-person-role"
NS = "https://w3id.org/extendedmatrix/vocab/person-role/"


@pytest.fixture(scope="module")
def vocabs():
    return Vocabularies.load()


def test_lo_schema_e_originato_e_si_dichiara(vocabs):
    s = vocabs.schemes[SCHEME]
    assert (s.origin, s.status) == ("originated", "resolvable")
    assert s.version and s.license and s.uri == NS
    assert s.extensible is None


def test_un_solo_ruolo_quello_che_un_atto_non_dice(vocabs):
    assert sorted(vocabs.concepts(SCHEME)) == [NS + "sector_supervisor"]
    assert vocabs.resolve(SCHEME, NS + "sector_supervisor", "it").label == "responsabile di settore"
    assert vocabs.resolve(SCHEME, NS + "sector_supervisor", "en").label == "sector supervisor"
    for lang in ("it", "en"):
        assert vocabs.resolve(SCHEME, NS + "sector_supervisor", lang).via == "scheme"


def test_gli_atti_non_sono_ruoli(vocabs):
    """Il compilatore, il direttore, chi rielabora: li dice il tipo dell'atto
    (em-documentation-act), e qui non stanno."""
    acts = {c.rsplit("/", 1)[-1] for c in vocabs.concepts("em-documentation-act")}
    roles = {c.rsplit("/", 1)[-1] for c in vocabs.concepts(SCHEME)}
    assert acts == {"excavation", "recording", "revision"}
    assert not acts & roles


def test_le_corrispondenze_sono_proposte_e_mai_esatte(vocabs):
    rows = [a for a in vocabs.alignments if a.source_scheme == SCHEME]
    assert {(a.target_scheme, a.match) for a in rows} == {
        ("datacite-contributor-type", "closeMatch"),
        ("marc-relators", "broadMatch"),
    }
    assert all(a.status == "proposed" for a in rows)
    assert {vocabs.schemes[a.target_scheme].status for a in rows} == {"declared"}
