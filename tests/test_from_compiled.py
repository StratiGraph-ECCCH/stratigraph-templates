"""A reader that vendors the COMPILED form prints the same sheet as the YAML.

EMStudio (MICRO-G-SCHEDE, 2026-11-17) vendors `dist/schede/<id>/<version>.json`
and asks its bridge to print with this package's renderer: the template it hands
over is rebuilt from the compiled visual half (`template_from_compiled`). The
sheet must come out byte for byte as the one the definition itself draws —
otherwise the bridge would be a second renderer of the standard."""

import json
from pathlib import Path

import pytest

from stratigraph_templates.loader import (TemplateSyntaxError, find_template, load_record,
                                          template_from_compiled)
from stratigraph_templates.render import RenderError, sheet_html

DIST = Path(__file__).resolve().parents[1] / "dist" / "schede"


def _latest():
    index = json.loads((DIST / "index.json").read_text(encoding="utf-8"))
    out = []
    for tid, entry in sorted((index.get("schede") or index.get("definitions") or {}).items()):
        latest = entry.get("latest") if isinstance(entry, dict) else None
        if latest and (DIST / tid / f"{latest}.json").is_file():
            out.append((tid, latest))
    return out


LATEST = _latest()


def test_the_index_names_the_latest_of_each_definition():
    assert ("iccd-us-2021", find_template("iccd-us-2021").version) in LATEST


@pytest.mark.parametrize("tid,version", LATEST)
def test_the_compiled_form_draws_what_the_definition_draws(tid, version):
    doc = json.loads((DIST / tid / f"{version}.json").read_text(encoding="utf-8"))
    rebuilt = template_from_compiled(doc)
    source = find_template(tid)
    assert (rebuilt.id, rebuilt.version) == (source.id, source.version)
    for lang in source.languages:
        assert sheet_html(rebuilt, lang=lang, mode="form") == sheet_html(source, lang=lang, mode="form")
        if source.sheet is None:
            with pytest.raises(RenderError):
                sheet_html(rebuilt, lang=lang, mode="print")
        else:
            assert sheet_html(rebuilt, lang=lang, mode="print") == sheet_html(source, lang=lang, mode="print")


def test_with_a_record_too():
    doc = json.loads((DIST / "iccd-us-2021" / f"{find_template('iccd-us-2021').version}.json")
                     .read_text(encoding="utf-8"))
    rec = load_record("examples/us-3014-demo.yaml")
    a = sheet_html(template_from_compiled(doc), rec, lang="it", mode="print")
    b = sheet_html(find_template("iccd-us-2021"), rec, lang="it", mode="print")
    assert a == b and "3018, 3020" in a


def test_not_a_compiled_definition_is_said():
    with pytest.raises(TemplateSyntaxError):
        template_from_compiled({"template": {}})
