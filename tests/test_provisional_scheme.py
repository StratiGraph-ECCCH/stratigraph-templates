"""La norma dichiarata e il modulo nostro che risponde per lei (SPEC §3.2, §3.3).

I cinque campi a vocabolario della US ICCD 2021 citano schemi `declared`: l'ICCD
prescrive un termine controllato e non ha pubblicato lo SKOS dei modelli da
campo. Finché è così rispondono i moduli originati `em-us-*`. Questi test
dicono che il ponte regge, che non si può costruire storto, e che ogni
concetto dei cinque moduli ha una fonte.
"""
import json

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, SKOS

from stratigraph_templates.compile import compile_template
from stratigraph_templates.loader import find_template
from stratigraph_templates.registry import registry
from stratigraph_templates.vocab import REPO_ROOT, Vocabularies, VocabularyError

MODULES = ["definizione", "consistenza", "colore", "stato-conservazione", "affidabilita"]
LANGS = {"it", "en", "ro", "el", "es", "pl", "he", "de"}


@pytest.fixture(scope="module")
def vocabs():
    return Vocabularies.load()


# ── il ponte ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("m", MODULES)
def test_ogni_schema_iccd_us_e_dichiarato_e_ha_il_suo_provvisorio(vocabs, m):
    norm, ours = vocabs.schemes[f"iccd-us-{m}"], vocabs.schemes[f"em-us-{m}"]
    assert norm.status == "declared" and norm.provisional == ours.id
    assert ours.origin == "originated" and ours.status == "resolvable"
    assert vocabs.effective(norm.id) == ours.id


def test_un_concetto_si_risolve_attraverso_lo_schema_della_norma(vocabs):
    uri = "https://w3id.org/extendedmatrix/vocab/us-definizione/strato-di-crollo"
    r = vocabs.resolve("iccd-us-definizione", uri, "it")
    assert r.label == "strato di crollo"
    assert r.via == "provisional:em-us-definizione", "il tracciato dice DA DOVE viene la parola"


def _scheme(tmp_path, name, body):
    (tmp_path / f"{name}.yaml").write_text(body, encoding="utf-8")


def _ours(tmp_path, sid="em-x", origin="originated", status="resolvable"):
    (tmp_path / "x.ttl").write_text(
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
        "<https://example.org/x/a> a skos:Concept ; skos:prefLabel \"a\"@it .\n", encoding="utf-8")
    extra = ("  version: '0.1.0'\n  license: 'CC BY 4.0'\n" if origin == "originated" else "")
    _scheme(tmp_path, sid, f"scheme:\n  id: {sid}\n  authority: X\n  origin: {origin}\n"
            f"  status: {status}\n  labels: {{it: x}}\n  uri: 'https://example.org/x/'\n{extra}"
            f"  resolve: {{kind: skos_file, path: '{tmp_path / 'x.ttl'}'}}\n")


def test_uno_schema_resolvable_non_puo_avere_un_provvisorio(tmp_path):
    """Il primo dei due casi rossi del punto 3: uno schema che si risolve da sé
    con un sostituto avrebbe due risposte."""
    _ours(tmp_path)
    _scheme(tmp_path, "norm", "scheme:\n  id: norm\n  authority: N\n  status: resolvable\n"
            "  labels: {it: n}\n  provisional: em-x\n"
            f"  resolve: {{kind: skos_file, path: '{tmp_path / 'x.ttl'}'}}\n")
    with pytest.raises(VocabularyError, match="only a DECLARED scheme"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


def test_il_provvisorio_deve_esistere(tmp_path):
    _scheme(tmp_path, "norm", "scheme:\n  id: norm\n  authority: N\n  status: declared\n"
            "  labels: {it: n}\n  provisional: em-che-non-c-e\n")
    with pytest.raises(VocabularyError, match="no declaration"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


def test_il_provvisorio_deve_essere_originato(tmp_path):
    """Il secondo caso rosso: un sostituto che è di altri non è un nostro
    dovere di risposta."""
    _ours(tmp_path, sid="ext-x", origin="external")
    _scheme(tmp_path, "norm", "scheme:\n  id: norm\n  authority: N\n  status: declared\n"
            "  labels: {it: n}\n  provisional: ext-x\n")
    with pytest.raises(VocabularyError, match="originated"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


def test_il_provvisorio_deve_essere_risolvibile(tmp_path):
    _ours(tmp_path, status="declared")
    _scheme(tmp_path, "norm", "scheme:\n  id: norm\n  authority: N\n  status: declared\n"
            "  labels: {it: n}\n  provisional: em-x\n")
    with pytest.raises(VocabularyError, match="cannot be resolved"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


def test_unverified_languages_solo_su_un_modulo_nostro(tmp_path):
    _scheme(tmp_path, "ext", "scheme:\n  id: ext\n  authority: E\n  status: declared\n"
            "  labels: {it: e}\n  unverified_languages: [de]\n")
    with pytest.raises(VocabularyError, match="only a module we maintain"):
        Vocabularies.load(schemes_dir=tmp_path, alignments_dir=tmp_path)


# ── la forma compilata ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def compiled(vocabs):
    return compile_template(find_template("iccd-us-2021"), registry(check_live=False), vocabs)


def test_il_compilato_dice_il_provvisorio_sul_campo_sulla_ricetta_e_nella_testata(compiled):
    fields = {f["id"]: f for f in compiled["visual"]["fields"]}
    assert fields["definizione"]["vocabulary"] == {"scheme": "iccd-us-definizione",
                                                   "provisional": "em-us-definizione"}
    assert compiled["recipe"]["fields"]["colore"]["provisional"] == "em-us-colore"
    header = [v["id"] for v in compiled["header"]["vocabularies"]]
    for m in MODULES:
        i = header.index(f"iccd-us-{m}")
        assert header[i + 1] == f"em-us-{m}", "il provvisorio subito dopo lo schema che sostituisce"
    ours = next(v for v in compiled["header"]["vocabularies"] if v["id"] == "em-us-definizione")
    assert ours["provisional_for"] == "iccd-us-definizione"
    assert ours["version"] == "0.1.0" and ours["origin"] == "originated"


def test_la_definizione_ha_alzato_la_versione(compiled):
    # 1.0.2 = i concetti provvisori; 2.0.0 (natura → origin_type) li tiene tutti.
    assert compiled["header"]["version"] in ("1.0.2", "2.0.0")
    index = json.loads((REPO_ROOT / "dist/schede/index.json").read_text(encoding="utf-8"))
    assert {"1.0.0", "1.0.1", "1.0.2", "2.0.0"} <= set(index["schede"]["iccd-us-2021"]["versions"]), \
        "le versioni vecchie restano: un record 1.0.1 si rilegge con la 1.0.1"


# ── i cinque moduli ──────────────────────────────────────────────────────────

def _graph(vocabs, m):
    g = Graph()
    g.parse(str(vocabs.schemes[f"em-us-{m}"].skos_file()), format="turtle")
    return g


@pytest.mark.parametrize("m", MODULES)
def test_ogni_concetto_ha_una_fonte_e_tutte_le_lingue(vocabs, m):
    g = _graph(vocabs, m)
    concepts = set(g.subjects(None, SKOS.Concept))
    assert concepts
    without_source = {c for c in concepts if not list(g.objects(c, DCTERMS.source))}
    assert not without_source, f"un termine senza fonte non entra: {sorted(without_source)}"
    for c in concepts:
        langs = {o.language for o in g.objects(c, SKOS.prefLabel)}
        assert langs == LANGS, f"{c}: {langs ^ LANGS}"
        assert {o.language for o in g.objects(c, SKOS.definition)} >= {"it", "en"}
        for b in g.objects(c, SKOS.broader):
            assert b in concepts, f"{c} broader {b} fuori dal modulo"


@pytest.mark.parametrize("m", MODULES)
def test_le_lingue_in_bozza_sono_dichiarate(vocabs, m):
    s = vocabs.schemes[f"em-us-{m}"]
    assert set(s.unverified_languages) == LANGS - {"it"}
    assert s.version == "0.1.0" and s.license == "CC BY 4.0"
    assert s.uri == f"https://w3id.org/extendedmatrix/vocab/us-{m}/"


@pytest.mark.parametrize("m", MODULES)
def test_gli_allineamenti_puntano_a_concetti_che_esistono(vocabs, m):
    concepts = {str(c) for c in _graph(vocabs, m).subjects(None, SKOS.Concept)}
    ours = [a for a in vocabs.alignments if a.source_scheme == f"em-us-{m}"]
    assert ours, "ogni modulo ha almeno un allineamento proposto"
    for a in ours:
        assert a.source_concept in concepts, a.source_concept
        assert a.status == "proposed", "verified lo mette E.D."


def test_la_US_3014_trova_strato_di_crollo(vocabs):
    uri = URIRef("https://w3id.org/extendedmatrix/vocab/us-definizione/strato-di-crollo")
    g = _graph(vocabs, "definizione")
    assert (uri, SKOS.altLabel, None) in g, "«crollo» (tutorial PyArchInit) come altLabel"


def test_una_parola_fuori_lista_si_stampa_come_parola(vocabs):
    """`{label}` senza concetto è ciò che il widget scrive per un termine fuori
    lista: sul foglio va la parola, non la rappresentazione del dizionario."""
    from stratigraph_templates.render import VocabTrace, _term_label
    field = next(f for f in find_template("iccd-us-2021").fields if f.id == "colore")
    trace = VocabTrace()
    assert _term_label(field, {"label": "bruno chiaro (10YR 6/3)"}, "it", vocabs, trace) \
        == "bruno chiaro (10YR 6/3)"
    assert trace.rows[-1][3] == "uncontrolled_string"
