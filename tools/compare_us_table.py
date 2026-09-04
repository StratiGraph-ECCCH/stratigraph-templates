#!/usr/bin/env python3
"""Confronta la definizione ICCD US 2021 con le 133 colonne di `us_table`.

Non deduce: legge i due lati. Le colonne vengono da
`pyarchinit-mini/pyarchinit_mini/models/us.py` (o dal percorso passato come
argomento), i campi dalla definizione in questo repository.

    python3 tools/compare_us_table.py [percorso/us.py]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stratigraph_templates.loader import find_template  # noqa: E402

DEFAULT_US_PY = (
    Path.home() / "Documents/GitHub/pyarchinit-mini/pyarchinit_mini/models/us.py"
)

# Le 46 colonne della scheda USM fuse in `us_table` (modello ICCD a sé, e
# vocabolario CRMba: non è questa scheda).
USM = {
    "funz_statica", "lavorazione", "spess_giunti", "letti_posa", "alt_mod", "un_ed_riass",
    "reimp", "posa_opera", "quota_min_usm", "quota_max_usm", "cons_legante", "col_legante",
    "aggreg_legante", "con_text_mat", "col_materiale", "inclusi_materiali_usm",
    "lunghezza_usm", "altezza_usm", "spessore_usm", "tecnica_muraria_usm", "modulo_usm",
    "campioni_malta_usm", "campioni_mattone_usm", "campioni_pietra_usm",
    "provenienza_materiali_usm", "criteri_distinzione_usm", "uso_primario_usm",
    "tipologia_opera", "sezione_muraria", "superficie_analizzata", "orientamento",
    "materiali_lat", "lavorazione_lat", "consistenza_lat", "forma_lat", "colore_lat",
    "impasto_lat", "forma_p", "colore_p", "taglio_p", "posa_opera_p", "inerti_usm",
    "tipo_legante_usm", "rifinitura_usm", "materiale_p", "consistenza_p",
}

# Colonne malformate (verdetto di E.D.: da non portarsi dietro).
MALFORMED = {"cont_per", "ref_n", "rapporti2", "doc_usv", "modo_formazione"}

# Tecniche / identità: non sono dati della scheda.
TECHNICAL = {"id_us", "us", "unita_tipo", "node_uuid"}

# Ordinamento di visualizzazione: uno slot, non un'affermazione.
LAYOUT = {"order_layer"}

#: colonna → campo della definizione (o None = la scheda non ha questa casella)
MAP = {
    "sito": "localita",
    "area": "area",
    "d_stratigrafica": "definizione",
    "d_interpretativa": None,       # la scheda ha una sola DEFINIZIONE
    "descrizione": "descrizione",
    "interpretazione": "interpretazione",
    "periodo_iniziale": "periodo",
    "fase_iniziale": "fase",
    "periodo_finale": None,         # la scheda non ha periodo/fase FINALE
    "fase_finale": None,
    "scavato": None,                # non è sul modello da campo 2021
    "attivita": "attivita",
    "anno_scavo": "anno",
    "metodo_di_scavo": None,        # sta sulla scheda SAS, non sulla US
    "data_schedatura": "data_rilevamento",
    "schedatore": "responsabile_compilazione",
    "formazione": "formazione_natura",
    "stato_di_conservazione": "stato_conservazione",
    "colore": "colore",
    "consistenza": "consistenza",
    "struttura": None,              # non è una casella del modello 2021
    "inclusi": "componenti_inorganici",
    "campioni": "campionature",
    "rapporti": "__DODICI__",       # un blob contro dodici caselle
    "documentazione": "__QUATTRO__",  # un campo contro piante/prospetti/sezioni/fotografie
    "tipo_documento": None,
    "file_path": None,              # ResourceNode: legame a un file, non una casella
    "settore": "settore",
    "quad_par": "quadrato",
    "ambient": "ambiente",
    "saggio": "saggio",
    "elem_datanti": "elementi_datanti",
    "n_catalogo_generale": None,    # numeri di catalogo: non sul modello da campo
    "n_catalogo_interno": None,
    "n_catalogo_internazionale": None,
    "soprintendenza": "ufficio_mic",
    "quota_relativa": "quote",
    "quota_abs": "quote",
    "ref_tm": None,                 # arco verso la scheda TMA: non una casella US
    "ref_ra": "riferimenti_tabelle_materiali",
    "posizione": "posizione",
    "criteri_distinzione": "criteri_distinzione",
    "componenti_organici": "componenti_organici",
    "componenti_inorganici": "componenti_inorganici",
    "lunghezza_max": "misure",
    "altezza_max": "misure",
    "altezza_min": "misure",
    "profondita_max": "misure",
    "profondita_min": "misure",
    "larghezza_media": "misure",
    "quota_max_abs": "quote",
    "quota_max_rel": "quote",
    "quota_min_abs": "quote",
    "quota_min_rel": "quote",
    "osservazioni": "osservazioni",
    "datazione": "datazione",
    "flottazione": "flottazione",
    "setacciatura": "setacciatura",
    "affidabilita": "affidabilita",
    "direttore_us": "responsabile_scientifico",
    "responsabile_us": "responsabile_compilazione",
    "cod_ente_schedatore": "ente_responsabile",
    "data_rilevazione": "data_rilevamento",
    "data_rielaborazione": "data_rielaborazione",
}


def columns(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^\s*(\w+)\s*=\s*Column\(", text, re.M)


def main() -> int:
    us_py = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_US_PY
    if not us_py.is_file():
        print(f"non trovo {us_py}", file=sys.stderr)
        return 2
    cols = columns(us_py)
    t = find_template("iccd-us-2021")

    twins = [c for c in cols if c.endswith("_en")]
    usm = [c for c in cols if c in USM]
    malformed = [c for c in cols if c in MALFORMED]
    technical = [c for c in cols if c in TECHNICAL]
    layout = [c for c in cols if c in LAYOUT]
    rest = [
        c for c in cols
        if c not in USM and c not in MALFORMED and c not in TECHNICAL
        and c not in LAYOUT and not c.endswith("_en")
    ]

    unmapped = [c for c in rest if c not in MAP]
    not_on_sheet = [c for c in rest if MAP.get(c, "?") is None]
    mapped = [c for c in rest if MAP.get(c)]

    used = {MAP[c] for c in mapped if MAP[c] and not MAP[c].startswith("__")}
    # la colonna `us` sta nel secchio "tecniche/identità" perché in tabella è la
    # chiave, ma sulla scheda la casella US esiste: il campo non è un'aggiunta
    used.add("us")
    only_in_definition = [f.id for f in t.fields if f.id not in used]

    print(f"us_table: {len(cols)} colonne")
    print(f"  USM (scheda diversa, vocabolario CRMba)      {len(usm):3d}")
    print(f"  gemelle _en (lingua come colonna)            {len(twins):3d}")
    print(f"  malformate (verdetto E.D.)                   {len(malformed):3d}  {sorted(malformed)}")
    print(f"  tecniche / identità                          {len(technical):3d}  {sorted(technical)}")
    print(f"  layout                                       {len(layout):3d}  {sorted(layout)}")
    print(f"  restano                                      {len(rest):3d}")
    print()
    print(f"delle {len(rest)}: {len(mapped)} hanno una casella sulla scheda, "
          f"{len(not_on_sheet)} no")
    for c in not_on_sheet:
        print(f"    – {c}")
    if unmapped:
        print(f"  !! non classificate: {unmapped}")
    print()
    print(f"definizione iccd-us-2021: {len(t.fields)} campi")
    print(f"  con vocabolario   {sum(1 for f in t.fields if f.vocabulary):3d}")
    print(f"  obbligatori       {sum(1 for f in t.fields if f.required):3d}")
    print(f"  ripetibili        {sum(1 for f in t.fields if f.repeatable):3d}")
    print(f"  archi (relazioni) {len(t.edges()):3d}")
    print()
    print(f"campi della scheda che in us_table NON hanno una colonna propria "
          f"({len(only_in_definition)}):")
    for fid in only_in_definition:
        print(f"    + {fid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
