"""LA TESI DEL REPOSITORY, come regressione: tre schede, zero righe di codice.

*Aggiungere uno standard costa scrivere una definizione.* Con due schede era una
tesi con un esempio; con tre è una tesi con un controesempio possibile, e questo
file è ciò che la tiene vera quando qualcuno aggiunge un campo condizionale al
renderer.

**Perché un test e non un referto.** La scheda ungherese è nata la notte del
2026-09-23 proprio per provare questo, è comparsa nel browser con il diff
dell'implementazione vuoto, e poi è stata cancellata: della prova sono rimasti
un commento e un documento. *Una prova che vive in un documento non è una
prova: è un ricordo.*
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from stratigraph_templates.loader import load_template                # noqa: E402
from stratigraph_templates.registry import registry                   # noqa: E402
from stratigraph_templates.validate import validate_template          # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SRC = ROOT / "src" / "stratigraph_templates"

#: Le tre schede, e la RAGIONE per cui ciascuna è diversa dalle altre. Se una
#: sparisce, questo elenco fa fallire il test invece di lasciare che la copertura
#: si assottigli in silenzio — che è esattamente com'è sparita la terza.
SHIPPED = {
    "iccd-us-2021":    "la norma vera, ricostruita dal .doc ICCD",
    "es-ue-demo-2026": "un'altra lingua sorgente e un paragrafo che l'ICCD non ha",
    "hu-rl-demo-2026": "una terza lingua, e il designatore che NON è l'ultimo",
}


def sheets():
    return {p.name: load_template(p / "template.yaml")
            for p in sorted(TEMPLATES.iterdir()) if p.is_dir()}


# ── 1 · tre, e non due ──────────────────────────────────────────────────────

def test_three_standards_are_shipped():
    found = sheets()
    assert set(found) == set(SHIPPED), (
        f"le schede spedite sono {sorted(found)}; attese {sorted(SHIPPED)}. "
        f"Una scheda tolta è una dimensione di copertura che sparisce senza "
        f"che niente lo dica.")


def test_every_shipped_standard_validates():
    reg = registry()
    for name, sheet in sheets().items():
        validate_template(sheet, reg)          # solleva se non va


# ── 2 · e sono DIVERSE, che è l'unica ragione per averne tre ───────────────

def test_the_three_speak_three_source_languages():
    assert {s.source_language for s in sheets().values()} == {"it", "es", "hu"}


def test_the_three_have_three_shapes_of_human_key():
    """Stessa domanda, tre risposte diverse: due campi, tre campi, e il
    designatore in due posizioni."""
    shapes = {}
    for name, sheet in sheets().items():
        key = sheet.identity.human_key
        shapes[name] = (len(key), key.index(sheet.identity.unit_field_of()))
    assert len(set(shapes.values())) == 3, shapes


def test_the_three_give_three_different_trench_subsets():
    """Se coincidessero, il marcatore `recorded_in` starebbe descrivendo il
    nostro pregiudizio invece dello standard."""
    counts = {n: s.recorded_in_counts() for n, s in sheets().items()}
    trench = {n: c["trench"] for n, c in counts.items()}
    assert len(set(trench.values())) == 3, counts


# ── 3 · E L'IMPLEMENTAZIONE NON LE NOMINA ──────────────────────────────────

def test_the_implementation_names_none_of_the_three():
    """Il cancello di `test_render.py`, allargato a tutto ciò che le tre schede
    chiamano per nome: id di scheda, di campo, di paragrafo.

    Sorveglia TRE schede adesso, non due — che è il senso di averne aggiunta
    una: la superficie che il codice potrebbe imparare per sbaglio è più larga.
    """
    import re

    names = set()
    for sheet in sheets().values():
        names.add(sheet.id)
        names.update(f.id for f in sheet.fields)
        names.update(p.id for p in sheet.paragraphs)

    guilty = {}
    for py in sorted(SRC.glob("*.py")):
        if py.name == "xsd_extract.py":
            continue      # è ABOUT il dialetto XSD dell'ICCD, per definizione
        code = py.read_text(encoding="utf-8")
        hits = sorted(n for n in names
                      if len(n) > 3 and re.search(rf"\b{re.escape(n)}\b", code))
        if hits:
            guilty[py.name] = hits
    assert not guilty, (
        f"l'implementazione nomina qualcosa delle schede: {guilty}. "
        f"Aggiungere uno standard deve costare una definizione, non una riga "
        f"di codice.")


def test_that_the_name_detector_actually_detects(tmp_path):
    """Una guardia che non morde dà lo stesso verde di una che funziona."""
    import re

    names = {"retegszam", "yacimiento"}
    guilty = tmp_path / "guilty.py"
    guilty.write_text("def f(x):\n    return x['retegszam']\n", encoding="utf-8")
    innocent = tmp_path / "innocent.py"
    innocent.write_text("def f(x):\n    return x[KEY]\n", encoding="utf-8")

    def hits(path):
        code = path.read_text(encoding="utf-8")
        return [n for n in names if re.search(rf"\b{re.escape(n)}\b", code)]

    assert hits(guilty) == ["retegszam"]
    assert hits(innocent) == []


# ── 4 · e la terza si STAMPA come le altre, senza una riga nuova ───────────

def test_the_third_sheet_prints_like_the_other_two(tmp_path):
    """La prova che il renderer non ha imparato niente di nuovo per lei."""
    from stratigraph_templates.render import write_pdf

    sheet = sheets()["hu-rl-demo-2026"]
    for lang in sheet.languages:
        out = tmp_path / f"hu-{lang}.pdf"
        pages = write_pdf(sheet, None, str(out), lang=lang)
        assert out.is_file() and out.stat().st_size > 1000, lang
        assert pages >= 1
