"""Every guard is shown on a case that makes it fire."""

import pytest

from stratigraph_templates.loader import find_template
from stratigraph_templates.validate import ValidationError, blocked_fields, validate_template


def _problems(t, reg, vocab):
    return [str(p) for p in validate_template(t, reg, known_schemes=vocab.scheme_ids(), strict=False)]


def test_minimal_is_valid(fixture_template, reg, vocab):
    assert _problems(fixture_template("minimal"), reg, vocab) == []


def test_shipped_definitions_are_valid(reg, vocab):
    for tid in ("iccd-us-2021", "es-ue-demo-2026"):
        assert _problems(find_template(tid), reg, vocab) == [], tid


def test_missing_label_is_named_with_field_and_language(fixture_template, reg, vocab):
    problems = _problems(fixture_template("broken-missing-label"), reg, vocab)
    assert any("field 'copre'" in p and "'it'" in p for p in problems), problems


def test_unknown_node_type_is_an_error_not_a_warning(fixture_template, reg, vocab):
    t = fixture_template("broken-unknown-node-type")
    problems = _problems(t, reg, vocab)
    assert any("InstitutionalActorNode" in p and "not declared by s3Dgraphy" in p for p in problems)
    with pytest.raises(ValidationError):
        validate_template(t, reg, known_schemes=vocab.scheme_ids())


def test_geometry_that_does_not_fit_the_page(fixture_template, reg, vocab):
    problems = _problems(fixture_template("broken-geometry"), reg, vocab)
    assert any("widths add up" in p for p in problems), problems
    assert any("fit on a A4 side" in p for p in problems), problems


def test_uid_may_not_be_derived_from_the_human_key(fixture_template, reg, vocab):
    problems = _problems(fixture_template("broken-uid-derived"), reg, vocab)
    assert any("derive_from_human_key" in p for p in problems), problems


def test_a_rotated_label_must_fit_its_block(fixture_template, reg, vocab):
    problems = _problems(fixture_template("broken-rotated-label"), reg, vocab)
    assert any("would print clipped" in p for p in problems), problems


def test_a_field_needs_a_paragraph_and_a_box(fixture_template, reg, vocab):
    problems = _problems(fixture_template("broken-orphan-field"), reg, vocab)
    assert any("field 'orfano'" in p and "no paragraph" in p for p in problems), problems
    assert any("field 'orfano'" in p and "no box on the sheet" in p for p in problems), problems


def test_undecided_binding_is_refused(fixture_template, reg, vocab, tmp_path):
    """The marker an extracted draft carries cannot pass for a decision."""
    import yaml

    from stratigraph_templates.loader import parse_template

    doc = yaml.safe_load(open("tests/fixtures/minimal.yaml", encoding="utf-8"))
    doc["template"]["fields"][2]["graph"] = {"verdict": "undecided"}
    t = parse_template(doc)
    problems = _problems(t, reg, vocab)
    assert any("undecided" in p and "person must decide" in p for p in problems), problems


def test_blocked_fields_are_declared_not_hidden(reg, vocab):
    t = find_template("iccd-us-2021")
    blocked = blocked_fields(t)
    assert set(blocked) == {"ente_responsabile", "ufficio_mic", "campionature"}
    for fid in blocked:
        assert t.field(fid).graph.blocked_on.needs  # says what it would need
        assert t.field(fid).graph.verdict == "none"  # and lands nowhere meanwhile
