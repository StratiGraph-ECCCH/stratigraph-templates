"""The extractor lifts what the XSD really says, and marks what it cannot know."""

import os
from pathlib import Path

import pytest

from stratigraph_templates.loader import parse_template
from stratigraph_templates.validate import validate_template, ValidationError
from stratigraph_templates.xsd_extract import extract_xsd

SAS = (
    Path(os.environ.get("STRATIGRAPH_ICCD_STANDARDS", Path.home() / "Documents/GitHub/Standard-catalografici"))
    / "schede-di-catalogo/beni archeologici/SAS 3.00/ICCD_normativa_SAS_3.00_102019.xsd"
)


@pytest.fixture(scope="module")
def sas():
    if not SAS.is_file():
        pytest.skip("SAS 3.00 XSD not present on this machine")
    return extract_xsd(SAS, code="SAS", version="3.00")


def test_the_measured_numbers(sas):
    _, stats = sas
    assert stats["records"] == 276
    assert stats["paragraphs"] == 19
    assert stats["simple_fields"] + stats["structured_fields"] == 257
    assert stats["records_with_alias"] == 276
    assert stats["mandatory_fields"] + stats["mandatory_paragraphs"] == 38
    assert stats["repeatable_fields"] + stats["repeatable_paragraphs"] == 44
    assert stats["fields_with_vocabulary"] == 50


def test_every_binding_comes_out_undecided(sas):
    _, stats = sas
    assert stats["undecided_bindings"] == 257


def test_the_draft_is_a_proposal_the_validator_refuses(sas, reg, vocab):
    draft, _ = sas
    import yaml

    t = parse_template(yaml.safe_load(draft))
    with pytest.raises(ValidationError) as exc:
        validate_template(t, reg, known_schemes=vocab.scheme_ids())
    reasons = [str(p) for p in exc.value.problems]
    assert sum("undecided" in r for r in reasons) > 200
