"""The renderer refuses rather than improvising, and the same definition feeds
both outputs."""

import re

import pytest

from stratigraph_templates.loader import find_template, load_record
from stratigraph_templates.model import MissingLabel
from stratigraph_templates.render import RenderError, VocabTrace, sheet_html

TWELVE = [
    "uguale_a", "si_lega_a", "gli_si_appoggia", "si_appoggia_a", "coperto_da", "copre",
    "tagliato_da", "taglia", "riempito_da", "riempie", "posteriore_a", "anteriore_a",
]


@pytest.fixture(scope="module")
def us():
    return find_template("iccd-us-2021")


@pytest.fixture(scope="module")
def us_record():
    return load_record("examples/us-3014-cencelle.yaml")


def _box(html, field):
    """The rendered content of one field's box."""
    m = re.search(rf'<div class="cell[^"]*" style="[^"]*" data-field="{field}">(.*?)</div>\s*(?=<div|</div>)',
                  html, re.S)
    return m.group(1) if m else ""


def test_the_twelve_boxes_are_twelve_slots(us):
    slots = {f.id: (f.graph.edge_type, f.graph.direction) for f in us.edges()}
    for fid in TWELVE:
        assert fid in slots, fid
    # twelve boxes, seven edge types, two directions: no invented edge names
    assert len({slots[f][0] for f in TWELVE}) == 7
    assert {slots[f][1] for f in TWELVE} == {"outgoing", "incoming"}


def test_the_twelve_boxes_print_full(us, us_record, vocab):
    html = sheet_html(us, us_record, lang="it", mode="print", vocab=vocab)
    filled = {f: _box(html, f) for f in TWELVE}
    # every box with data in the record shows it, in its own box
    assert "3021" in filled["uguale_a"]
    assert "3011" in filled["si_lega_a"]
    assert "3007" in filled["gli_si_appoggia"]
    assert "3011" in filled["si_appoggia_a"]
    assert "3009" in filled["coperto_da"]
    assert "3018, 3020" in filled["copre"]
    assert "3005" in filled["tagliato_da"]
    assert "3022" in filled["taglia"]
    assert "3018, 3019" in filled["posteriore_a"]
    assert "3009" in filled["anteriore_a"]
    # and the two empty ones are empty boxes, not missing boxes
    for empty in ("riempito_da", "riempie"):
        assert 'class="v refs"' in filled[empty]


def test_a_blob_of_relations_does_not_leak_into_the_boxes(us, us_record, vocab):
    """The pyarchinit failure mode: rapporti as one string. Here a single blob in
    one slot stays in that slot and the others stay empty — the format has no way
    to express 'all twelve at once', which is the point."""
    us_record.values["copre"] = "Copre: 3018; Coperto da: 3009"
    html = sheet_html(us, us_record, lang="it", mode="print", vocab=vocab)
    assert "Coperto da: 3009" in _box(html, "copre")
    assert "3009" not in _box(html, "tagliato_da")


def test_missing_label_refuses_instead_of_guessing(fixture_template, vocab):
    t = fixture_template("broken-missing-label")
    with pytest.raises(MissingLabel) as exc:
        sheet_html(t, None, lang="it", mode="print", vocab=vocab)
    assert "copre" in str(exc.value)
    assert "'it'" in str(exc.value)


def test_an_undeclared_language_refuses(us, vocab):
    with pytest.raises(RenderError) as exc:
        sheet_html(us, None, lang="fr", mode="print", vocab=vocab)
    assert "does not declare language 'fr'" in str(exc.value)


def test_print_and_form_come_from_the_same_definition(us, us_record, vocab):
    printed = sheet_html(us, us_record, lang="it", mode="print", vocab=vocab)
    form = sheet_html(us, us_record, lang="it", mode="form", vocab=vocab)
    printed_fields = set(re.findall(r'data-field="([^"]+)"', printed))
    form_fields = set(re.findall(r'data-field="([^"]+)"', form))
    assert printed_fields == form_fields == {f.id for f in us.fields}


def test_provenance_per_field_shows_on_the_sheet(us, us_record, vocab):
    html = sheet_html(us, us_record, lang="it", mode="print", vocab=vocab)
    assert "AI✓" in _box(html, "interpretazione")   # AI draft validated by a human
    assert ">AI<" in _box(html, "descrizione")      # AI draft, not yet validated
    assert "prov" not in _box(html, "osservazioni")  # nobody claimed it, nothing invented


def test_the_record_must_match_the_template(us, vocab):
    other = load_record("examples/ue-13-tarraco-demo.yaml")
    with pytest.raises(RenderError):
        sheet_html(us, other, lang="it", mode="print", vocab=vocab)


def test_the_human_key_has_the_shape_each_standard_declares():
    us = find_template("iccd-us-2021")
    es = find_template("es-ue-demo-2026")
    assert us.identity.human_key == ["localita", "area", "us"]
    assert es.identity.human_key == ["yacimiento", "contexto"]   # no area at all


def test_second_standard_renders_with_no_special_case(vocab):
    es = find_template("es-ue-demo-2026")
    rec = load_record("examples/ue-13-tarraco-demo.yaml")
    for lang in ("es", "it"):
        for mode in ("print", "form"):
            html = sheet_html(es, rec, lang=lang, mode=mode, vocab=vocab)
            assert "18, 20" in html          # the relation slots carry through
            assert "FIXTURE" in html         # and it says it is invented


def test_no_standard_is_named_in_the_implementation():
    """If the renderer had to know about ICCD, the second standard would have
    needed code. It does not, and this test is what keeps it that way."""
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "stratigraph_templates"
    forbidden = ("iccd-us-2021", "es-ue-demo-2026", "definizione", "uguale_a", "yacimiento")
    for py in src.glob("*.py"):
        if py.name == "xsd_extract.py":
            continue  # the extractor is ABOUT the ICCD XSD dialect, by definition
        text = py.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{py.name} mentions {token!r}"
