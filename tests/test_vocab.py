"""What lands in the graph is the concept; the label is resolved at reading time,
and an alignment between national vocabularies is the only reason two countries
end up looking at the same thing."""

import pytest

from stratigraph_templates.loader import find_template, load_record
from stratigraph_templates.render import VocabTrace, sheet_html
from stratigraph_templates.vocab import VocabularyError

ES = "https://example.invalid/fixture/ue-definicion-es/estrato"
IT = "https://example.invalid/fixture/us-definizione-it/strato"


def test_own_scheme_first(vocab):
    r = vocab.resolve("fx-ue-definicion-es", ES, "es")
    assert (r.label, r.via) == ("estrato", "scheme")


def test_alignment_supplies_the_other_language(vocab):
    r = vocab.resolve("fx-ue-definicion-es", ES, "it")
    assert r.label == "strato"
    assert r.via.startswith("alignment:exactMatch")


def test_alignment_works_in_both_directions(vocab):
    r = vocab.resolve("fx-us-definizione-it", IT, "es")
    assert r.label == "estrato"
    assert "exactMatch" in r.via


def test_exact_match_is_preferred_over_close_match(vocab):
    # 'derrumbe' is only closeMatch to 'crollo': it still resolves, and says so
    r = vocab.resolve(
        "fx-ue-definicion-es",
        "https://example.invalid/fixture/ue-definicion-es/derrumbe",
        "it",
    )
    assert r.label == "strato di crollo"
    assert "closeMatch" in r.via


def test_no_label_and_no_alignment_refuses(vocab):
    with pytest.raises(VocabularyError) as exc:
        vocab.resolve("fx-ue-definicion-es", ES, "de")
    assert "no alignment supplies one" in str(exc.value) or "no label in 'de'" in str(exc.value)


def test_a_real_iccd_skos_scheme_is_read_where_it_lives(vocab):
    """The ICCD thesauri are referenced, not incorporated: this reads the actual
    RDF from the Standard-catalografici checkout."""
    concepts = vocab.concepts("iccd-ra-materia")
    if not concepts:
        pytest.skip("Standard-catalografici not present on this machine")
    assert len(concepts) > 1000
    some = next(iter(concepts.values()))
    assert "it" in some


def test_declared_schemes_carry_licence_and_attribution(vocab):
    for sid, s in vocab.schemes.items():
        if s.authority == "ICCD":
            assert s.license, sid
            assert s.attribution, sid


def test_the_sheet_shows_the_aligned_label(vocab):
    """The proof that matters: the Spanish concept prints its Italian label on the
    Italian rendering of the Spanish sheet, and the trace says how."""
    t = find_template("es-ue-demo-2026")
    rec = load_record("examples/ue-13-tarraco-demo.yaml")
    trace = VocabTrace()
    html = sheet_html(t, rec, lang="it", mode="print", vocab=vocab, trace=trace)
    assert ">strato<" in html
    assert any(row[3].startswith("alignment:exactMatch") for row in trace.rows)


def test_a_bare_string_in_a_controlled_box_is_recorded_as_such(vocab):
    t = find_template("es-ue-demo-2026")
    rec = load_record("examples/ue-13-tarraco-demo.yaml")
    rec.values["definicion"] = "estrato escrito a mano"
    trace = VocabTrace()
    sheet_html(t, rec, lang="es", mode="print", vocab=vocab, trace=trace)
    assert [r[0] for r in trace.uncontrolled()] == ["definicion"]
