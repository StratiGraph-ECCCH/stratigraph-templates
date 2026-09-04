"""The A4 recto/verso invariant, measured on the produced PDF."""

import pytest

from stratigraph_templates.loader import find_template, load_record
from stratigraph_templates.render import write_pdf

weasyprint = pytest.importorskip("weasyprint")

A4_PT = (595.28, 841.89)


@pytest.mark.parametrize(
    "tid,record,lang",
    [
        ("iccd-us-2021", "examples/us-3014-cencelle.yaml", "it"),
        ("iccd-us-2021", "examples/us-3014-cencelle.yaml", "en"),
        ("es-ue-demo-2026", "examples/ue-13-tarraco-demo.yaml", "es"),
        ("es-ue-demo-2026", "examples/ue-13-tarraco-demo.yaml", "it"),
    ],
)
def test_one_page_per_declared_side(tid, record, lang, tmp_path, vocab):
    t = find_template(tid)
    out = tmp_path / f"{tid}-{lang}.pdf"
    pages = write_pdf(t, load_record(record), str(out), lang=lang, vocab=vocab)
    assert pages == len(t.sheet.sides), "a box had to grow: the geometry is too tight"
    assert out.stat().st_size > 5000


def test_the_page_really_is_a4(tmp_path, vocab):
    t = find_template("iccd-us-2021")
    out = tmp_path / "a4.pdf"
    write_pdf(t, load_record("examples/us-3014-cencelle.yaml"), str(out), lang="it", vocab=vocab)
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open(out)
    for page in doc:
        assert round(page.rect.width) == round(A4_PT[0])
        assert round(page.rect.height) == round(A4_PT[1])


def test_nothing_spills_outside_the_printable_area(vocab):
    """Every cell must stay inside the page box: a box wider than the paper is how
    the graphic-documentation row used to overwrite its neighbours."""
    from weasyprint import HTML

    from stratigraph_templates.render import sheet_html

    t = find_template("iccd-us-2021")
    rec = load_record("examples/us-3014-cencelle.yaml")
    doc = sheet_html(t, rec, lang="it", mode="print", vocab=vocab)
    pages = HTML(string=doc).render().pages

    def walk(box):
        for child in getattr(box, "all_children", lambda: [])():
            yield child
            yield from walk(child)

    for page in pages:
        box = page._page_box
        # child positions are absolute on the page, so the content edge has to
        # include the page margin
        limit = box.content_box_x() + box.width
        for cell in walk(box):
            el = getattr(cell, "element", None)
            if el is None or "cell" not in (el.get("class") or ""):
                continue
            # position_x is the border-box left, width the content width: allow the
            # padding and border of one cell as tolerance
            assert cell.position_x + cell.width < limit + 6, el.get("data-field") or el.get("class")


def _widest_cell_overflow(t, vocab):
    """How far past the printable area the widest cell reaches, in px."""
    from weasyprint import HTML

    from stratigraph_templates.render import sheet_html

    pages = HTML(string=sheet_html(t, None, mode="print", vocab=vocab)).render().pages

    def walk(box):
        for child in getattr(box, "all_children", lambda: [])():
            yield child
            yield from walk(child)

    worst = 0.0
    for page in pages:
        box = page._page_box
        limit = box.content_box_x() + box.width
        for cell in walk(box):
            el = getattr(cell, "element", None)
            if el is None or "cell" not in (el.get("class") or ""):
                continue
            worst = max(worst, cell.position_x + cell.width - limit)
    return worst


def test_a_row_of_four_equal_cells_inside_a_block_stays_on_the_page(fixture_template, vocab):
    """The shape the twelve boxes have: 25+25+25+25 inside a labelled block, with
    no width left over to absorb a mistake. This is the case that fires when the
    renderer resolves percentages against the wrong box or adds padding on top of
    them — measured at 19 px (5 mm) off the page before the fix."""
    t = fixture_template("tight-nested")
    assert _widest_cell_overflow(t, vocab) < 6
