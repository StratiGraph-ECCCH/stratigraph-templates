"""Dove si compila un campo — e soprattutto: che cosa vuol dire il silenzio.

Il marcatore risponde a due domande (SPEC §1.6). La prima è facile: *quali campi
mostro sul telefono?* La seconda è quella che decide la forma del default: *cosa
succede a un campo obbligatorio che non è da trincea?*

**IL CUORE DI QUESTO FILE È IL DEFAULT**, e la prova non è che il default valga
`unknown` — è che un consumatore, davanti a una definizione che tace, **non
possa concluderne niente**. Le due cose non sono la stessa: un default corretto
letto con `!= "lab"` fa comparire cinquantanove campi su una scheda telefono che
nessuno ha progettato.
"""

from __future__ import annotations

import pytest

from stratigraph_templates.loader import (TemplateSyntaxError, find_template,
                                          load_template)
from stratigraph_templates.model import (RECORDED_IN_LAB, RECORDED_IN_TRENCH,
                                         RECORDED_IN_UNKNOWN,
                                         RECORDED_IN_VALUES)


# ── 1 · IL DEFAULT CHE NON PROMETTE NIENTE, dimostrato sull'effetto ──────────

def test_a_definition_that_says_nothing_yields_no_trench_fields(fixture_template):
    """LA GUARDIA DI QUESTO CAPITOLO, verificata sull'EFFETTO.

    `minimal.yaml` non dichiara `recorded_in` da nessuna parte. Un consumatore
    che chiede il sottoinsieme da trincea deve ricevere **l'insieme vuoto** —
    non i tre campi, non «tutti tranne i lab».

    Prima si verifica che la definizione TACCIA davvero (altrimenti questo test
    misurerebbe un file che qualcuno ha marcato nel frattempo, e passerebbe per
    la ragione sbagliata), poi si verifica che il consumatore non ne ricavi
    nulla.
    """
    t = fixture_template("minimal")

    # il cancello: la definizione tace per davvero
    assert len(t.fields) == 3
    for f in t.fields:
        assert f.recorded_in == RECORDED_IN_UNKNOWN, (
            f"{f.id} porta un marcatore: questa prova non sta più misurando il "
            f"silenzio")

    # l'effetto: chi monta la scheda telefono non ottiene niente
    assert t.recorded_in(RECORDED_IN_TRENCH) == []
    assert [f.id for f in t.fields if f.recorded_in_trench] == []
    assert t.recorded_in_counts() == {RECORDED_IN_UNKNOWN: 3,
                                      RECORDED_IN_TRENCH: 0,
                                      RECORDED_IN_LAB: 0}


def test_that_the_check_above_can_actually_fire(fixture_template, tmp_path):
    """Una guardia che non può scattare riferisce l'assenza di ciò che non ha
    mai cercato. Tre prove, in questo ecosistema, sono state no-op.

    Quindi: la STESSA definizione con UN campo marcato, e il consumatore deve
    ricevere esattamente quell'uno. Se anche così tornasse vuoto, il test qui
    sopra passerebbe per un bug del selettore e non per il default.
    """
    import pathlib

    source = pathlib.Path("tests/fixtures/minimal.yaml").resolve()
    text = source.read_text(encoding="utf-8")

    # la sostituzione, e la prova che è entrata
    marked = text.replace('''    - id: nota
      labels: {it: "NOTA"}
      type: longtext''', '''    - id: nota
      labels: {it: "NOTA"}
      type: longtext
      recorded_in: trench''', 1)
    assert "recorded_in: trench" in marked, "la sostituzione non è entrata"
    assert marked != text

    target = tmp_path / "marked.yaml"
    target.write_text(marked, encoding="utf-8")
    t = load_template(target)

    assert [f.id for f in t.recorded_in(RECORDED_IN_TRENCH)] == ["nota"], (
        "con un campo marcato il selettore torna vuoto: allora il test del "
        "default non stava misurando il default")
    assert t.recorded_in_counts()[RECORDED_IN_UNKNOWN] == 2


def test_unknown_is_not_a_synonym_for_lab(fixture_template):
    """La riga di tabella che rende `unknown` necessario (SPEC §1.6).

    «non lo so» e «si compila dopo» portano un validatore a due conclusioni
    diverse, e confonderle assolverebbe una scheda incompleta senza averne il
    diritto. Quindi i due valori non collassano, nemmeno nel conteggio.
    """
    t = fixture_template("minimal")
    assert t.recorded_in(RECORDED_IN_LAB) == []
    assert len(t.recorded_in(RECORDED_IN_UNKNOWN)) == 3
    assert RECORDED_IN_UNKNOWN != RECORDED_IN_LAB


def test_the_default_is_the_first_admissible_value():
    """Non estetica: `unknown` è il default E il primo dell'elenco, così chi
    legge l'elenco vede per primo il valore che non afferma niente."""
    assert RECORDED_IN_VALUES[0] == RECORDED_IN_UNKNOWN
    assert set(RECORDED_IN_VALUES) == {RECORDED_IN_UNKNOWN, RECORDED_IN_TRENCH,
                                       RECORDED_IN_LAB}
    assert len(RECORDED_IN_VALUES) == 3, "un quarto valore vuole una riga in SPEC §1.6"


# ── 2 · un valore sbagliato è un errore, non un ripiego ─────────────────────

@pytest.mark.parametrize("bad", ["Trench", "field", "trincea", "lab ", "", None, True])
def test_a_value_that_is_not_one_of_the_three_is_refused(tmp_path, bad):
    """Il ripiego silenzioso su `unknown` sarebbe la trappola peggiore.

    Una definizione che intendeva `trench` e ha scritto `Trench` sparirebbe
    dalla scheda telefono, e il suo autore non avrebbe modo di distinguerlo da
    un campo lasciato indeciso di proposito.
    """
    import pathlib

    text = pathlib.Path("tests/fixtures/minimal.yaml").read_text(encoding="utf-8")
    broken = text.replace('''      type: longtext''',
                          f'''      type: longtext
      recorded_in: {bad!r}'''.replace("'", '"') if isinstance(bad, str)
                          else f'''      type: longtext
      recorded_in: {bad}''', 1)
    assert "recorded_in:" in broken, "la sostituzione non è entrata"

    target = tmp_path / "broken.yaml"
    target.write_text(broken, encoding="utf-8")
    with pytest.raises(TemplateSyntaxError) as refusal:
        load_template(target)
    said = str(refusal.value)
    assert "recorded_in" in said
    assert "unknown" in said, "il rifiuto deve dire qual è il default"


def test_asking_the_selector_for_a_place_that_does_not_exist_refuses(
        fixture_template):
    t = fixture_template("minimal")
    with pytest.raises(ValueError) as refusal:
        t.recorded_in("laboratorio")
    assert "laboratorio" in str(refusal.value)


# ── 3 · le due definizioni vere, e i loro conteggi ──────────────────────────

def test_the_iccd_sheet_carries_the_three_counts():
    """Misurato il 2026-09-22. Se questi numeri cambiano, è perché qualcuno ha
    marcato altri campi — e allora deve aver citato la riga che lo giustifica."""
    t = find_template("iccd-us-2021")
    assert t.recorded_in_counts() == {RECORDED_IN_UNKNOWN: 48,
                                      RECORDED_IN_TRENCH: 8,
                                      RECORDED_IN_LAB: 3}
    assert len(t.fields) == 59


def test_every_marked_iccd_field_carries_its_justification():
    """Un criterio senza la sua provenienza diventa arbitrio alla prima
    discussione (SPEC §1.6). Quindi la giustificazione sta NEL DATO.

    Il commento YAML non arriva al modello — è il prezzo dichiarato in SPEC §0
    — quindi la si cerca nel testo del file, sulle righe del campo marcato.
    """
    import pathlib
    import re

    text = pathlib.Path(find_template("iccd-us-2021").path).read_text(encoding="utf-8")
    lines = text.split("\n")
    marked = [i for i, line in enumerate(lines) if "recorded_in:" in line]
    assert len(marked) == 11, f"marcati {len(marked)}, attesi 11"

    for i in marked:
        following = lines[i + 1].strip()
        assert following.startswith("#"), (
            f"riga {i + 1}: un marcatore senza la riga di giustificazione sotto")
        assert re.search(r"Base [AB]|Strutturale", following), (
            f"riga {i + 1}: la giustificazione non cita una base: {following[:80]}")


def test_the_demo_sheet_was_marked_too():
    t = find_template("es-ue-demo-2026")
    counts = t.recorded_in_counts()
    assert counts[RECORDED_IN_TRENCH] == 14
    assert counts[RECORDED_IN_LAB] == 1
    assert counts[RECORDED_IN_UNKNOWN] == 0


# ── 4 · È PER STANDARD, e questo è il test che lo tiene vero ────────────────

def test_the_two_sheets_do_not_agree_on_the_same_concepts():
    """SE LE DUE SCHEDE FINISCONO CON LO STESSO SOTTOINSIEME, il marcatore sta
    descrivendo il nostro pregiudizio invece che lo standard.

    Le coppie sono accostate a mano perché le due schede non condividono gli id
    dei campi — che è esattamente il motivo per cui il marcatore è per standard.
    Misurato: 7 delle 13 coppie hanno un marcatore diverso.
    """
    us = find_template("iccd-us-2021")
    ue = find_template("es-ue-demo-2026")
    pairs = [("us", "contexto"), ("localita", "yacimiento"),
             ("definizione", "definicion"), ("descrizione", "descripcion"),
             ("interpretazione", "interpretacion"), ("uguale_a", "igual_a"),
             ("copre", "cubre"), ("coperto_da", "cubierto_por"),
             ("taglia", "corta"), ("tagliato_da", "cortado_por"),
             ("quote", "cota"),
             ("responsabile_compilazione", "responsable"),
             ("data_rilevamento", "fecha")]

    disagree = [(a, b) for a, b in pairs
                if us.field(a).recorded_in != ue.field(b).recorded_in]
    assert len(disagree) == 7, (
        f"{len(disagree)} coppie in disaccordo su 13 — se scende a zero il "
        f"marcatore ha smesso di essere per standard: {disagree}")

    # e le due divergenze che portano più significato, nominate
    assert us.field("definizione").recorded_in == RECORDED_IN_UNKNOWN
    assert ue.field("definicion").recorded_in == RECORDED_IN_TRENCH
    assert all(us.field(f).recorded_in == RECORDED_IN_UNKNOWN
               for f in ("copre", "coperto_da", "taglia", "tagliato_da"))
    assert all(ue.field(f).recorded_in == RECORDED_IN_TRENCH
               for f in ("cubre", "cubierto_por", "corta", "cortado_por"))


# ── 5 · `required` e `recorded_in` sono ortogonali ─────────────────────────

def test_required_and_recorded_in_are_independent():
    """La tabella di SPEC §1.6, sui dati veri.

    È la coppia che rende esprimibile «incompleta perché siamo ancora sullo
    scavo» contro «incompleta perché manca qualcosa» — e il caso che conta
    esiste davvero nella US ICCD: DEFINIZIONE è obbligatoria e il suo
    `recorded_in` è `unknown`, quindi la risposta onesta di un validatore è
    «non si può decidere».
    """
    t = find_template("iccd-us-2021")
    required = [f for f in t.fields if f.required]
    assert {f.id for f in required} == {"us", "localita", "definizione"}

    by_stage = {f.id: f.recorded_in for f in required}
    assert by_stage["us"] == RECORDED_IN_TRENCH
    assert by_stage["localita"] == RECORDED_IN_TRENCH
    assert by_stage["definizione"] == RECORDED_IN_UNKNOWN, (
        "il caso interessante è sparito: senza un obbligatorio `unknown` la "
        "terza riga della tabella di SPEC §1.6 non ha più un esempio")

    # e l'indipendenza nell'altro senso: dei marcati, non tutti sono obbligatori
    trench = t.recorded_in(RECORDED_IN_TRENCH)
    assert any(not f.required for f in trench)
    assert any(f.required for f in trench)


def test_a_lab_field_is_not_ranked_below_a_trench_one():
    """Il vincolo 3 del prompt, reso verificabile: nessun ordinamento.

    Se qualcuno introducesse `priority` o `level` accanto a questo marcatore,
    questo test è il posto dove la cosa va discussa.
    """
    from stratigraph_templates import model

    assert not hasattr(model.Field, "priority")
    assert not hasattr(model.Field, "level")
    source = __import__("pathlib").Path(model.__file__).read_text(encoding="utf-8")
    for word in ("priority", "level"):
        assert f"{word}:" not in source and f"{word} =" not in source, (
            f"'{word}' è comparso accanto a recorded_in: il marcatore è un "
            f"luogo e un momento, non un rango")
