"""La scheda del DAI: dalla configurazione aperta di iDAI.field a una definizione.

Tre cose nuove, e ciascuna ha qui la sua prova:

* un ESTRATTORE che legge la configurazione di un'applicazione a un commit
  (`git show`, mai il working tree) e ne propone una bozza — i numeri misurati
  il 2026-10-26 sono scritti qui, e se la lettura cambia il test lo dice;
* uno SCHEMA risolvibile da un checkout esterno fissato a un commit
  (`resolve.kind: idai_field_valuelist`), come gli SKOS dell'ICCD da
  Standard-catalografici;
* una definizione SENZA FOGLIO: valida, compila (`sheet: null`), il modulo la
  mostra per paragrafi, la stampa la rifiuta e dice perché.

I test che leggono iDAI.field si saltano se il checkout non c'è, e lo dicono.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from stratigraph_templates import idai_extract as idai
from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template, parse_template
from stratigraph_templates.render import RenderError, sheet_html
from stratigraph_templates.validate import ValidationError, draft_undecided, validate_template

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "drafts" / "draft-idai-field-layer.yaml"
DIST = ROOT / "dist" / "schede" / "dai-idaifield-layer-2026" / "0.2.0.json"
COMMIT = "4b5c1e2c3c499d4bd125d0eda61cc6f5c94ffcd4"
DAI = "dai-idaifield-layer-2026"


@pytest.fixture(scope="module")
def src():
    try:
        return idai.Source.open(commit=COMMIT)
    except idai.IdaiFieldError as exc:
        pytest.skip(f"iDAI.field checkout not usable on this machine: {exc}")


@pytest.fixture(scope="module")
def dai():
    return find_template(DAI)


# ── 1 · l'estrattore, misurato ─────────────────────────────────────────────

def test_the_measured_numbers_of_the_layer_form(src):
    _, stats, form = idai.extract_idai_field(src, "Layer")
    assert stats["commit"] == COMMIT
    assert form.parent == "Feature"
    assert form.forms == ["Feature:default", "Layer:default"]
    assert stats["fields"] == 44
    assert stats["groups"] == 8
    assert stats["relations"] == 15
    assert stats["labels"] == {"de": 44, "en": 44}        # nessuna etichetta nostra
    assert stats["term_valuelists"] == 8
    assert stats["verdicts"] == {"identity": 1, "edge": 13, "none": 4, "undecided": 26}


def test_the_draft_on_disk_is_what_the_extractor_writes_today(src):
    """La bozza committata non è un file scritto a mano: rigenerarla dà gli
    stessi byte, perché si legge a un commit e non dal working tree."""
    draft, _, _ = idai.extract_idai_field(src, "Layer")
    assert DRAFT.read_text(encoding="utf-8") == draft


def test_a_project_configuration_goes_on_top(src):
    """Milet nasconde tre campi di Feature e ne aggiunge di suoi: la lettura
    di progetto li toglie e li aggiunge, e il form di base resta 44."""
    _, stats, form = idai.extract_idai_field(src, "Layer", project="Milet")
    names = {f.name for f in form.fields}
    assert {"color", "featureBorders", "description"}.isdisjoint(names)
    assert "layerInterpretation" in names
    assert stats["hidden"] >= 3


def test_the_relation_table_speaks_only_canonical_edges(reg):
    for name, (edge, direction) in idai._EDGES.items():
        assert edge in reg.edge_types, name
        assert not (reg.edges[edge].get("spelling_of")), name
        assert direction in ("outgoing", "incoming")


def test_merge_groups_is_the_port_of_idai_field():
    """mergeGroupsConfigurations: un gruppo figlio che nomina TUTTI i campi del
    padre ne ridà l'ordine; altrimenti accoda quelli che mancano."""
    parent = [{"name": "properties", "fields": ["a", "b"]}, {"name": "time", "fields": ["t"]}]
    assert idai.merge_groups(parent, [{"name": "properties", "fields": ["c"]}]) == [
        {"name": "properties", "fields": ["a", "b", "c"]}, {"name": "time", "fields": ["t"]}]
    assert idai.merge_groups(parent, [{"name": "properties", "fields": ["b", "c", "a"]}])[0] == {
        "name": "properties", "fields": ["b", "c", "a"]}
    assert idai.merge_groups(parent, [{"name": "dimension", "fields": ["d"]}])[-1] == {
        "name": "dimension", "fields": ["d"]}
    assert parent[0]["fields"] == ["a", "b"]              # il padre non si tocca


def test_no_checkout_is_said_not_guessed(tmp_path, monkeypatch):
    monkeypatch.setenv(idai.IDAI_FIELD_ENV, str(tmp_path / "nowhere"))
    with pytest.raises(idai.IdaiFieldError, match="no iDAI.field checkout"):
        idai.Source.open()


# ── 2 · la bozza: verde da bozza, rifiutata da definizione ─────────────────

def test_the_draft_passes_every_check_but_the_undecided(reg, vocab):
    t = parse_template(yaml.safe_load(DRAFT.read_text(encoding="utf-8")))
    assert t.sheet is None
    assert validate_template(t, reg, known_schemes=vocab.scheme_ids(), draft=True) == []
    assert len(draft_undecided(t)) == 26
    with pytest.raises(ValidationError) as exc:
        validate_template(t, reg, known_schemes=vocab.scheme_ids())
    problems = [str(p) for p in exc.value.problems]
    assert len(problems) == 26 and all("undecided" in p for p in problems), problems


# ── 3 · gli schemi DAI si risolvono dal checkout, al commit ────────────────

def test_every_dai_scheme_resolves_from_the_pinned_commit(src, vocab, dai):
    for sid in dai.vocabularies:
        s = vocab.schemes[sid]
        assert (s.origin, s.status, s.license) == ("external", "resolvable", "Apache-2.0"), sid
        assert s.resolve["commit"] == COMMIT, sid
        concepts = vocab.concepts(sid)
        values = src.json(idai.VALUELISTS)[s.resolve["valuelist"]]["values"]
        assert len(concepts) == len(values), sid
        assert all(c.get("de") for c in concepts.values()), sid   # il tedesco è la chiave


def test_the_alignments_point_at_values_that_exist(src, vocab):
    """Ogni localizzatore iDAI di un allineamento è un valore del suo valuelist
    al commit fissato — letto, non ricordato."""
    targets = [a for a in vocab.alignments if a.target_scheme.startswith("idai-field-")]
    assert len(targets) == 24
    for a in targets:
        assert a.target_concept in vocab.concepts(a.target_scheme), a.target_concept
        assert a.status == "proposed"


def test_the_lens_reads_across_in_both_directions(src, vocab):
    """ICCD ↔ DAI sullo stesso concetto: la parola dell'altra parte arriva
    dall'allineamento."""
    planier = idai.value_locator(COMMIT, "Layer-layerClassification-default", "Planierschicht")
    said = vocab.resolve("idai-field-layer-layerclassification-default", planier, "de")
    assert said.label == "Planierschicht"
    locker = idai.value_locator(COMMIT, "Layer-consistency-default", "locker")
    assert vocab.resolve("idai-field-layer-consistency-default", locker, "it").label == "sciolto"


def test_a_missing_checkout_is_a_vocabulary_error_that_names_the_variable(tmp_path, monkeypatch):
    from stratigraph_templates.vocab import Vocabularies, VocabularyError

    monkeypatch.setenv(idai.IDAI_FIELD_ENV, str(tmp_path / "nowhere"))
    fresh = Vocabularies.load()
    with pytest.raises(VocabularyError, match=idai.IDAI_FIELD_ENV):
        fresh.concepts("idai-field-colors-default-1")


# ── 4 · la definizione ──────────────────────────────────────────────────────

def test_the_definition_has_no_sheet_and_validates(reg, vocab, dai):
    assert dai.sheet is None and dai.sides == []
    validate_template(dai, reg, known_schemes=vocab.scheme_ids())
    assert (dai.version, dai.source_language, dai.languages) == ("0.2.0", "de", ["de", "en"])
    assert len(dai.fields) == 44


def test_decided_and_blocked_are_counted(dai):
    blocked = [f.id for f in dai.fields if f.graph.blocked_on]
    assert len(blocked) == 12            # 0.2.0: D7, D8 decisi (qualia 1.6.2)
    assert len(dai.fields) - len(blocked) == 32
    for f in dai.fields:
        if f.graph.blocked_on:
            assert "Benjamin (DAI)" in f.graph.blocked_on.reported, f.id


def test_the_definition_keeps_every_edge_the_draft_proposed(dai):
    draft = parse_template(yaml.safe_load(DRAFT.read_text(encoding="utf-8")))
    for f in draft.fields:
        if f.graph.verdict == "edge":
            mine = dai.field(f.id).graph
            assert (mine.verdict, mine.edge_type, mine.direction) == \
                   ("edge", f.graph.edge_type, f.graph.direction), f.id
    assert dai.field("borders").graph.edge_type == "generic_connection"


def test_the_graph_words_it_shares_with_the_iccd_sheet(dai):
    """La lente funziona dove le due schede scrivono la STESSA cosa: stesso
    elemento del nodo, stesse qualia, stessi archi."""
    iccd = find_template("iccd-us-2021")
    g = {f.id: f.graph for f in dai.fields}
    i = {f.id: f.graph for f in iccd.fields}
    assert g["layerClassification"].property_name == i["definizione"].property_name == "definition"
    assert g["consistency"].qualia == i["consistenza"].qualia == "texture"
    assert g["color"].qualia == i["colore"].qualia == "color"
    assert g["description"].property_name == i["descrizione"].property_name == "description"
    edges_dai = {(x.edge_type, x.direction) for x in g.values() if x.verdict == "edge"}
    edges_iccd = {(x.edge_type, x.direction) for x in i.values() if x.verdict == "edge"}
    assert edges_iccd - {("is_part_of", "incoming")} <= edges_dai


def test_it_compiles_with_a_null_sheet(reg, vocab, dai):
    doc = compile_template(dai, reg, vocab)
    assert "sheet" in doc["visual"] and doc["visual"]["sheet"] is None
    assert doc["recipe"]["open"] == []
    assert doc["recipe"]["unit"]["node_type"]["decided_by"] == "category"
    entry = doc["recipe"]["fields"]["layerClassification"]
    assert entry["element"]["name"] == "definition"
    assert entry["steps"][0]["emit"]["field"] == "data.definition"
    published = json.loads(DIST.read_text(encoding="utf-8"))
    assert published["header"]["digest"] == doc["header"]["digest"]


def test_the_form_shows_every_field_and_the_print_refuses(dai, vocab):
    for lang in dai.languages:
        html = sheet_html(dai, None, lang=lang, mode="form", vocab=vocab)
        for f in dai.fields:
            assert f'data-field="{f.id}"' in html or f'name="{f.id}"' in html, (lang, f.id)
    with pytest.raises(RenderError, match="declares no sheet"):
        sheet_html(dai, None, lang="de", mode="print", vocab=vocab)


# ── 5 · il foglio assente è assente, non vuoto ─────────────────────────────

def _minimal(**extra):
    doc = {"template": {
        "id": "x", "version": "0.1.0",
        "standard": {"authority": "X", "code": "X", "version": "1", "kind": "field_model",
                     "title": {"en": "X"}},
        "source_language": "en", "languages": ["en"],
        "identity": {"human_key": {"fields": ["n"], "pattern": "{n}"},
                     "uid": {"policy": "minted_by_creator"}},
        "paragraphs": [{"id": "p", "labels": {"en": "P"}, "fields": ["n"]}],
        "fields": [{"id": "n", "labels": {"en": "N"}, "type": "identifier",
                    "graph": {"verdict": "identity"}}],
    }}
    doc["template"].update(extra)
    return parse_template(doc)


def test_no_sheet_key_means_no_sheet(reg):
    t = _minimal()
    assert t.sheet is None
    assert validate_template(t, reg, strict=False) == []


def test_a_declared_sheet_still_has_to_place_every_field(reg):
    t = _minimal(sheet={"page": "A4", "sides": [{"id": "recto", "labels": {"en": "f"}, "rows": []}]})
    problems = [str(p) for p in validate_template(t, reg, strict=False)]
    assert any("no box on the sheet" in p for p in problems), problems
