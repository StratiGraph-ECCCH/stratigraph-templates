"""La scheda dice dove scrive (ICCD US 2021 3.0.0, decisioni di E.D. del 17 nov
2026, MICRO-J §B; SPEC §2.4, §2.5, §5, §9.5).

Ogni casella che un lettore leggeva «indeciso» — due caselle sullo stesso
indirizzo — ha ora un discriminante dichiarato: il livello del luogo, la
sotto-epoca, le qualia accettate, l'atto a cui appartiene."""
import copy

import pytest

from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template
from stratigraph_templates.validate import ValidationError, validate_template


@pytest.fixture(scope="module")
def iccd():
    return find_template("iccd-us-2021")


@pytest.fixture(scope="module")
def recipe(iccd, reg, vocab):
    return compile_template(iccd, reg, vocab)["recipe"]


def test_le_caselle_di_contesto_si_distinguono_per_il_livello(recipe):
    seen = {}
    for fid in ("localita", "area", "saggio", "settore", "quadrato", "ambiente"):
        e = recipe["fields"][fid]
        assert e["node"]["class"] == "LocationNodeGroup"
        assert e["resolve"]["$node"]["find"]["data"] == e["where"]
        seen[(e["where"]["kind"], e["where"]["level"])] = fid
    assert len(seen) == 6, "two boxes with the same discriminant"
    assert seen[("functional", "ambiente")] == "ambiente"
    # IDENTIFICATIVO resta l'unica casella verso un'unità funzionale
    fu = [f for f, e in recipe["fields"].items()
          if (e.get("node") or {}).get("class") == "FunctionalUnitNodeGroup"]
    assert fu == ["identificativo_riferimento"]


def test_fase_e_la_sotto_epoca_di_periodo(recipe):
    periodo, fase = recipe["fields"]["periodo"], recipe["fields"]["fase"]
    assert periodo["yields_to"] == "fase" and fase["sub_epoch_of"] == "periodo"
    unit_edge = [s for s in periodo["steps"] if s["emit"]["op"] == "add_edge"][0]
    assert unit_edge["when"] == "empty:fase"
    ops = [(s["emit"]["op"], s["emit"].get("edge_type"), s["emit"].get("source")) for s in fase["steps"]]
    assert ("add_edge", "has_sub_epoch", "$field.periodo.node") in ops
    assert ("add_edge", "has_first_epoch", "$unit") in ops
    assert fase["after"] == ["periodo"]


def test_misure_e_quote_dicono_le_qualia_che_accettano(recipe, reg):
    misure = recipe["fields"]["misure"]["property"]["accepts"]
    assert {"height", "width", "depth", "diameter", "length", "thickness"} <= set(misure)
    quote = recipe["fields"]["quote"]["property"]["accepts"]
    assert not set(misure) & set(quote)
    assert set(misure) | set(quote) <= reg.qualia


def test_gli_atti_sono_definiti_con_autore_e_data(recipe):
    anchors = recipe["anchors"]
    assert {k: (a["defined"], a["where"]["act_kind"]) for k, a in anchors.items()} == {
        "excavation_activity": (True, "excavation"),
        "recording_act": (True, "recording"),
        "revision_act": (True, "revision")}
    assert anchors["excavation_activity"]["resolve"]["$anchor.excavation_activity"]["find"]["data"] \
        == {"act_kind": "excavation", "act_start": "$values.anno"}
    for fid, act in (("anno", "excavation_activity"), ("data_rilevamento", "recording_act"),
                     ("data_rielaborazione", "revision_act")):
        step = recipe["fields"][fid]["steps"][0]["emit"]
        assert step == {"op": "update_field", "node_id": f"$anchor.{act}",
                        "field": "data.act_start", "value": "$value"}
    for fid, act in (("responsabile_scientifico", "excavation_activity"),
                     ("responsabile_compilazione", "recording_act"),
                     ("responsabile_rielaborazione", "revision_act")):
        edge = [s["emit"] for s in recipe["fields"][fid]["steps"] if s["emit"]["op"] == "add_edge"][0]
        assert (edge["edge_type"], edge["source"]) == ("has_author", f"$anchor.{act}")
    assert recipe["open"] == []


def test_i_documenti_si_citano_per_nome_e_un_nome_non_si_crea(recipe):
    r = recipe["fields"]["piante"]["resolve"]["$node"]
    assert r["find"]["any"] == [{"name": "$item"}, {"url": "$item"}]
    assert "never by name" in r["when_missing"]
    assert recipe["fields"]["riferimenti_tabelle_materiali"]["resolve"]["$item"]["find"]["any"] == [{"name": "$item"}]


def test_lo_stato_del_record_sta_sull_unita(recipe):
    rs = recipe["unit"]["record_status"]
    assert rs["scheme"] == "em-record-status" and rs["values"] == ["from_field", "revised"]
    assert rs["steps"][0]["emit"]["field"] == "data.record_status"


def test_il_validatore_rifiuta_i_discriminanti_fuori_posto(iccd, reg, vocab):
    bad = copy.deepcopy(iccd)
    f = next(x for x in bad.fields if x.id == "descrizione")
    f.graph.where = {"level": "x"}
    m = next(x for x in bad.fields if x.id == "misure")
    m.graph.accepts = ["height", "not_a_quale"]
    p = next(x for x in bad.fields if x.id == "fase")
    p.graph.sub_epoch_of = "descrizione"
    with pytest.raises(ValidationError) as exc:
        validate_template(bad, reg, known_schemes=vocab.scheme_ids())
    text = str(exc.value)
    assert "graph.where" in text and "not_a_quale" in text and "sub_epoch_of" in text
