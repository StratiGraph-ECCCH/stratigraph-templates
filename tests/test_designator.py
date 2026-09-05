"""Il designatore — quale campo della chiave umana È l'unità.

La chiave umana dice quali campi COMPONGONO il nome; non dice quale dei tre sia
l'unità e quali il contesto che la disambigua. Sono due informazioni diverse, e
la seconda serve a chiunque debba rispondere a «di che unità è questa scheda».

**Fino al 2026-09-23 un consumatore prendeva l'ULTIMO campo**, ed era vero su
tre definizioni su tre. Una regolarità osservata su tre casi non è una regola:
`hu-rl-demo-2026` è il quarto caso, e lì il designatore è il PRIMO. Con la
vecchia deduzione una scheda di strato sarebbe stata indirizzata **col nome del
sito** — senza che niente sollevasse un errore.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from stratigraph_templates.loader import load_template                # noqa: E402
from stratigraph_templates.registry import registry                   # noqa: E402
from stratigraph_templates.validate import (ValidationError,           # noqa: E402
                                            validate_template)

TEMPLATES = pathlib.Path(__file__).resolve().parents[1] / "templates"


def a_sheet(**identity):
    key = {"fields": ["sito", "numero"], "pattern": "US {numero} · {sito}"}
    key.update(identity)
    return {"template": {
        "id": "prova", "source_language": "it", "languages": ["it"],
        "standard": {"authority": "TEST", "code": "P", "version": "1",
                     "kind": "field_model", "invented": True,
                     "title": {"it": "Prova"}},
        "identity": {"human_key": key,
                     "uid": {"policy": "minted_by_creator"}},
        "paragraphs": [{"id": "tutto", "labels": {"it": "Tutto"},
                        "fields": ["sito", "numero"]}],
        "fields": [
            {"id": "sito", "labels": {"it": "SITO"}, "type": "text",
             "graph": {"verdict": "none"}},
            {"id": "numero", "labels": {"it": "NUMERO"}, "type": "identifier",
             "graph": {"verdict": "identity"}},
        ],
        "sheet": {"page": "A4",
                  "margins_mm": {"top": 12, "right": 12, "bottom": 12, "left": 12},
                  "sides": [{"id": "recto", "labels": {"it": "fronte"},
                             "rows": [{"h": 10, "cells": [
                                 {"field": "sito", "w": 50},
                                 {"field": "numero", "w": 50}]}]}]}}}


def written(tmp_path, doc):
    where = tmp_path / "prova.yaml"
    where.write_text(yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")
    return load_template(where)


def problems_of(template):
    try:
        validate_template(template, registry())
    except ValidationError as failed:
        return str(failed)
    return ""


# ── 1 · LA GUARDIA, dimostrata su un caso che la fa scattare ────────────────

def test_a_composite_key_without_a_designator_is_refused(tmp_path):
    """Due campi e nessuna dichiarazione: rifiutata, e la frase dice perché."""
    said = problems_of(written(tmp_path, a_sheet()))
    assert "unit_field" in said
    assert "composite" in said or "human_key has 2 fields" in said


def test_the_same_sheet_WITH_the_designator_is_valid(tmp_path):
    """Il controllo che rende la prova sopra una misura e non una coincidenza:
    cambia UNA riga e la scheda passa."""
    assert problems_of(written(tmp_path, a_sheet(unit_field="numero"))) == ""


def test_a_designator_that_is_not_in_the_key_is_refused(tmp_path):
    said = problems_of(written(tmp_path, a_sheet(unit_field="colore")))
    assert "colore" in said and "human_key.fields" in said


def test_a_single_field_key_needs_no_declaration(tmp_path):
    """Con un campo solo non c'è niente da scegliere, quindi dedurlo non è
    indovinare — ed è l'unico caso in cui la deduzione resta lecita."""
    doc = a_sheet(fields=["numero"], pattern="US {numero}")
    doc["template"]["paragraphs"][0]["fields"] = ["numero"]
    doc["template"]["fields"] = [doc["template"]["fields"][1]]
    doc["template"]["sheet"]["sides"][0]["rows"][0]["cells"] = [
        {"field": "numero", "w": 100}]
    t = written(tmp_path, doc)
    assert problems_of(t) == ""
    assert t.identity.unit_field_of() == "numero"


def test_a_key_with_no_declaration_resolves_to_NOTHING_rather_than_a_guess(
        tmp_path):
    """L'EFFETTO della regola, non solo il rifiuto del validatore.

    `unit_field_of()` su una chiave composta non dichiarata torna vuoto: non
    l'ultimo, non il primo. Un consumatore che chiede riceve «non lo so», che è
    la sola risposta onesta — e la vecchia deduzione è sparita dal codice
    invece che essere stata messa a riposo.
    """
    t = written(tmp_path, a_sheet())
    assert t.identity.human_key == ["sito", "numero"]
    assert t.identity.unit_field_of() == "", (
        "una chiave composta non dichiarata ha prodotto un designatore: la "
        "deduzione è ancora nel codice")


def test_the_old_deduction_is_gone_from_the_source():
    """«L'ultimo campo» non deve sopravvivere come fallback: se resta come
    fallback, resta come baco — e un baco silenzioso, perché produce
    un'etichetta plausibile."""
    import inspect

    from stratigraph_templates import model

    source = inspect.getsource(model.Identity)
    assert "human_key[-1]" not in source
    assert "[-1]" not in source.split("def unit_field_of")[1]


# ── 2 · LE TRE SCHEDE VERE, e la forma diversa che ne conferma il senso ────

def test_the_three_shipped_sheets_declare_their_designator():
    for folder in sorted(TEMPLATES.iterdir()):
        t = load_template(folder / "template.yaml")
        assert t.identity.unit_field_of(), t.id
        assert t.identity.unit_field_of() in t.identity.human_key, t.id


def test_the_designator_is_NOT_always_the_last_field():
    """LA CONFERMA CHE VALEVA LA PENA.

    Se un giorno tutte le schede tornassero ad avere il designatore in fondo,
    questo test diventa rosso — e allora la dichiarazione esplicita sembrerà
    inutile. Non lo è: è il caso che si scopre alla quarta scheda.
    """
    where = {}
    for folder in sorted(TEMPLATES.iterdir()):
        t = load_template(folder / "template.yaml")
        key = t.identity.human_key
        where[t.id] = (key.index(t.identity.unit_field_of()), len(key))

    ultimo = [tid for tid, (i, n) in where.items() if i == n - 1]
    non_ultimo = [tid for tid, (i, n) in where.items() if i != n - 1]
    assert non_ultimo, (
        f"tutte le schede hanno il designatore in fondo ({where}): la "
        f"regolarità che ha ingannato un consumatore per tre definizioni è "
        f"tornata, e non c'è più un caso che la smentisca")
    assert ultimo, where
