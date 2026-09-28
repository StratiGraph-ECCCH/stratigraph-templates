"""Pagine generate della documentazione: niente di qui si scrive a mano.

Due famiglie, entrambe rigenerate a ogni build (``builder-inited``):

1. **Le pagine-involucro.** ``README.md``, ``SPEC.md`` e ``LICENSING.md`` sono
   la documentazione e restano la fonte. Qui non se ne copia una riga: per ogni
   pagina si scrive una direttiva ``include`` con le righe di inizio e fine
   calcolate *dai titoli del file stesso*. Se una sezione cambia nome o si
   sposta, al build successivo l'involucro la segue; se sparisce, il build si
   ferma e lo dice.

2. **I cataloghi.** Definizioni, vocabolari, stato dello snapshot: ogni cifra
   viene dal pacchetto (gli stessi calcoli di ``stratigraph-templates info`` e
   ``vocab``) o da ``registry/s3dgraphy-snapshot.json``, mai da una tabella
   scritta.

Si lancia anche a mano: ``python docs/_tools/generate.py``.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
ROOT = DOCS.parent
OUT = DOCS / "_generated"
sys.path.insert(0, str(ROOT / "src"))

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BANNER = "<!-- GENERATO da docs/_tools/generate.py — non modificare: si rigenera a ogni build -->\n\n"


# ─── 1 · involucri: include per sezione, righe calcolate dai titoli ──────────

def _headings(path: Path):
    """[(indice di riga 0-based, livello, testo)], ignorando i blocchi di codice."""
    out, fence = [], False
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def _trim(path: Path, start: int, end: int) -> int:
    """Arretra la fine oltre le righe vuote e il separatore ``---`` che chiude la
    sezione nel file: in una pagina a sé un separatore finale non è ammesso."""
    lines = path.read_text(encoding="utf-8").splitlines()
    while end > start + 1 and lines[end - 1].strip() in ("", "---"):
        end -= 1
    return end


def section(path: Path, prefix: str | None):
    """Righe [start, end) della sezione il cui titolo comincia con ``prefix``.

    La sezione finisce al titolo successivo di livello uguale o superiore.
    ``prefix=None`` è il preambolo: dall'inizio del file al primo titolo di
    livello 2. Un titolo che non si trova è un errore, non una pagina vuota.
    """
    hs = _headings(path)
    n = len(path.read_text(encoding="utf-8").splitlines())
    if prefix is None:
        end = next((i for i, lvl, _ in hs if lvl == 2), n)
        return 0, _trim(path, 0, end)
    for k, (i, lvl, text) in enumerate(hs):
        if text.startswith(prefix):
            end = next((j for j, l2, _ in hs[k + 1:] if l2 <= lvl), n)
            return i, _trim(path, i, end)
    raise LookupError(f"{path.name}: nessun titolo comincia con {prefix!r}")


def include(src: str, span=None) -> str:
    rel = Path("..", "..", src).as_posix()          # da docs/_generated/ alla radice
    opts = [":relative-images:"]
    if span is not None:
        opts = [f":start-line: {span[0]}", f":end-line: {span[1]}"] + opts
    return "```{include} " + rel + "\n" + "\n".join(opts) + "\n```\n"


def page(name: str, body: str) -> None:
    (OUT / f"{name}.md").write_text(BANNER + body, encoding="utf-8")


def spec_sections():
    """Le sezioni di livello 2 di SPEC.md, nell'ordine in cui stanno: [(n, titolo)]."""
    out = []
    for _, lvl, text in _headings(ROOT / "SPEC.md"):
        m = re.match(r"^(\d+)\s*·", text)
        if lvl == 2 and m:
            out.append((m.group(1), text))
    return out


def wrappers() -> list[str]:
    readme, spec = ROOT / "README.md", ROOT / "SPEC.md"
    # 1 · che cos'è — il README senza le parti che hanno una pagina loro
    page("cose", "".join(include("README.md", section(readme, p)) + "\n" for p in (
        None, "Com'è fatto", "Il legame con s3Dgraphy", "La forma compilata")))
    # 2 · le cinque specie
    page("specie", include("README.md", section(readme, "Le cinque specie")))
    # 3 · la specifica, per le sue sezioni
    secs = spec_sections()
    toc = "\n".join(f"spec-{n}" for n, _ in secs)
    page("spec", include("SPEC.md", section(spec, None))
         + "\n```{toctree}\n:maxdepth: 2\n\n" + toc + "\n```\n")
    for n, title in secs:
        page(f"spec-{n}", include("SPEC.md", section(spec, title)))
    # 4 · l'uso — gli esempi del README, poi l'aiuto vero di ogni comando
    #     (i titoli generati stanno UN livello sotto «## Uso», che è il titolo della pagina)
    page("uso", include("README.md", section(readme, "Uso")) + "\n" + cli_reference())
    # 6 · licenze — la sintesi del README, poi LICENSING.md per esteso
    page("licenze-sintesi", include("README.md", section(readme, "Licenze")))
    page("licensing", include("LICENSING.md"))
    return [f"spec-{n}" for n, _ in secs]


# ─── 2 · i cataloghi ─────────────────────────────────────────────────────────

def _run_cli(*argv: str) -> str:
    from stratigraph_templates.cli import main
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            main(list(argv))
        except SystemExit:
            pass
    return buf.getvalue()


def cli_reference() -> str:
    from stratigraph_templates import cli
    text = _run_cli("--help")
    cmds = re.search(r"\{([a-z,-]+)\}", text).group(1).split(",")
    out = ["### I comandi, dall'aiuto della CLI\n",
           f"`stratigraph-templates` ha {len(cmds)} comandi. Il testo qui sotto è "
           "l'uscita di `--help`, presa dal codice al momento del build.\n",
           "```text\n" + text.rstrip() + "\n```\n"]
    for c in cmds:
        out.append(f"#### `{c}`\n\n```text\n" + _run_cli(c, "--help").rstrip() + "\n```\n")
    return "\n".join(out)


def _md_table(head, rows) -> str:
    esc = lambda v: str(v if v is not None else "—").replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(esc(v) for v in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def catalog_definitions() -> None:
    from stratigraph_templates.cli import _all_template_ids
    from stratigraph_templates.loader import find_template
    rows = []
    for tid in _all_template_ids():
        info = json.loads(_run_cli("info", tid))          # lo stesso calcolo del comando
        t = find_template(tid)
        s = t.standard
        title = s.title.get(t.source_language) or next(iter(s.title.values()), "")
        rows.append([f"`{tid}`", title, info["standard"], t.version,
                     "sì" if s.invented else "no", info["fields"],
                     ", ".join(info["languages"]), s.license, s.attribution])
    page("catalogo-definizioni",
         "# Catalogo delle definizioni\n\n"
         f"{len(rows)} definizioni in `templates/`. Ogni riga viene da "
         "`stratigraph-templates info <id>` e dalla testata `standard` della "
         "definizione, letti al momento del build.\n\n"
         + _md_table(["definizione", "titolo", "norma", "versione della definizione",
                      "inventata", "campi", "lingue", "licenza", "attribuzione"], rows))


def catalog_vocabularies() -> None:
    from stratigraph_templates.cli import _all_template_ids
    from stratigraph_templates.loader import find_template
    from stratigraph_templates.vocab import Vocabularies
    v = Vocabularies.load()
    used = {}
    for tid in _all_template_ids():
        for f in find_template(tid).fields:
            if f.vocabulary:
                used.setdefault(f.vocabulary.scheme, set()).add(tid)
    rows = []
    for sid, s in sorted(v.schemes.items()):
        al = [a for a in v.alignments if sid in (a.source_scheme, a.target_scheme)]
        others = sorted({a.target_scheme if a.source_scheme == sid else a.source_scheme for a in al})
        status = s.status + (" · FIXTURE" if s.fixture else "") + \
            (f" · provvisorio → `{s.provisional}`" if s.provisional else "")
        rows.append([f"`{sid}`", s.authority, s.origin, status, s.binding_thes_id,
                     f"{len(al)} ({', '.join(others)})" if al else "0",
                     ", ".join(f"`{t}`" for t in sorted(used.get(sid, ()))) or "—",
                     s.license])
    page("catalogo-vocabolari",
         "# Catalogo dei vocabolari\n\n"
         f"{len(rows)} schemi in `vocabularies/schemes/`, {len(v.alignments)} allineamenti "
         "dichiarati in `vocabularies/alignments/`. Letti dal pacchetto "
         "(`Vocabularies.load()`, lo stesso di `stratigraph-templates vocab`) al "
         "momento del build.\n\n"
         + _md_table(["schema", "autorità", "origine", "stato", "binding",
                      "allineamenti (con)", "usato da", "licenza"], rows))


def catalog_snapshot() -> None:
    d = json.loads((ROOT / "registry" / "s3dgraphy-snapshot.json").read_text(encoding="utf-8"))
    tf = d.get("taken_from", {})
    meta = [
        ["preso il", d.get("taken_on")],
        ["commit di s3Dgraphy", f"`{tf.get('git_commit')}`" + (" (albero sporco)" if tf.get("git_dirty") else "")],
        ["cartella letta", f"`{tf.get('config_dir')}`"],
        ["versione di s3Dgraphy", d.get("s3dgraphy_version")],
        ["datamodel dei nodi", d.get("node_datamodel_version")],
        ["datamodel delle connessioni", d.get("connections_version")],
        ["qualia", d.get("qualia_version")],
        ["em.ttl", d.get("em_ttl_version")],
        ["formato dello snapshot", d.get("snapshot_format")],
    ]
    counts = [[f"`{k}`", len(v)] for k, v in d.items() if isinstance(v, (list, dict)) and k != "taken_from"]
    page("stato-snapshot",
         "# Stato dello snapshot di s3Dgraphy\n\n"
         "`registry/s3dgraphy-snapshot.json` è la fonte di `validate` e `build`, ed è "
         "la cosa che invecchia per prima. Tutto qui sotto è letto dal file al "
         "momento del build.\n\n"
         + _md_table(["", "valore"], meta) + "\n## Che cosa contiene\n\n"
         + _md_table(["sezione", "voci"], counts))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    wrappers()
    catalog_definitions()
    catalog_vocabularies()
    catalog_snapshot()


if __name__ == "__main__":
    main()
