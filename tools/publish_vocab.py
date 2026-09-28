#!/usr/bin/env python3
"""Publish originated SKOS modules to the Extended Matrix site.

    python3 tools/publish_vocab.py <path to ExtendedMatrix-site> [module ...]

For every ORIGINATED, RESOLVABLE scheme (vocabularies/schemes/*.yaml with
origin: originated and resolve.kind: skos_file) it writes, under
<site>/public/vocab/<module>/:

  <module>.ttl   the source TTL, byte for byte, behind a header naming this
                 repository and the commit that last touched the source
  index.html     a human page: concepts, labels, definitions, sources,
                 proposed alignments, and the languages nobody has verified

and regenerates <site>/public/vocab/index.html from the modules present.

The source of truth stays HERE. The published copy says so in its first
lines: two copies drift silently, and when the resolvable one is the old one
nobody notices. Whoever changes a TTL republishes with this script.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

import yaml
from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS

REPO = Path(__file__).resolve().parents[1]
SCHEMES = REPO / "vocabularies" / "schemes"
ALIGN = REPO / "vocabularies" / "alignments"
SRC_URL = "https://github.com/StratiGraph-ECCCH/stratigraph-templates"
LANG_NAMES = {"it": "Italiano", "en": "English", "ro": "Română", "el": "Ελληνικά",
              "es": "Español", "pl": "Polski", "he": "עברית", "de": "Deutsch", "fr": "Français"}
RTL = {"he", "ar"}

CSS = """:root{--bg:#fdfcfa;--fg:#1c1a17;--muted:#6b645c;--line:#e2ddd5;--accent:#8a5a2b;--code:#f3efe9;--warn:#8a3b2b}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#16150f;--fg:#ece7de;--muted:#9c948a;--line:#332f28;--accent:#d7a76a;--code:#221f19;--warn:#e0957f}}
:root[data-theme="dark"]{--bg:#16150f;--fg:#ece7de;--muted:#9c948a;--line:#332f28;--accent:#d7a76a;--code:#221f19;--warn:#e0957f}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);margin:0;padding:0 16px;font:16px/1.65 Georgia,'Iowan Old Style',serif}
main{max-width:44rem;margin:0 auto;padding:3rem 0 5rem}
h1{font-size:1.9rem;line-height:1.2;margin:0 0 .3rem}
.sub{color:var(--muted);margin:0 0 2rem;font-style:italic}
h2{font-size:1.15rem;margin:2.6rem 0 .8rem;padding-bottom:.3rem;border-bottom:1px solid var(--line)}
article{margin:0 0 1.9rem}
h3{font-size:1.02rem;margin:0 0 .25rem;font-weight:600}
.n{display:inline-block;min-width:1.5rem;color:var(--accent);font-weight:700}
.uri code{font-size:.76rem;color:var(--muted);background:none;padding:0;word-break:break-all}
article p{margin:.3rem 0}
.it,.src{color:var(--muted);font-size:.93rem}
.src{font-size:.82rem}
.labels{color:var(--muted);font-size:.86rem}
.note{border-left:3px solid var(--warn);padding:.2rem 0 .2rem .8rem;color:var(--muted);font-size:.93rem}
code{background:var(--code);padding:.1rem .3rem;border-radius:3px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85em;word-break:break-all}
a{color:var(--accent)}
p{margin:.5rem 0}
.meta{color:var(--muted);font-size:.9rem}
dl{margin:0} dt{font-weight:600;margin-top:.7rem;font-size:.92rem}
dd{margin:.1rem 0 0;color:var(--muted);font-size:.92rem}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.86rem}"""


def e(s) -> str:
    return html.escape(str(s), quote=True)


def commit_of(path: Path) -> str:
    out = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%h", "--", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return out or "uncommitted"


def dirty(path: Path) -> bool:
    out = subprocess.run(["git", "--no-optional-locks", "-C", str(REPO), "status", "--porcelain", "--", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return bool(out)


def module_name(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def load_schemes():
    out = []
    for f in sorted(SCHEMES.glob("*.yaml")):
        s = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("scheme", {})
        r = s.get("resolve") or {}
        if s.get("origin") == "originated" and r.get("kind") == "skos_file" and s.get("uri"):
            out.append(s)
    return out


def load_alignments():
    rows = []
    for f in sorted(ALIGN.glob("*.yaml")):
        rows += (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("alignments", []) or []
    return rows


def lit(g, s, p, lang):
    for o in g.objects(s, p):
        if getattr(o, "language", None) == lang:
            return str(o)
    return None


def build_module(site: Path, s: dict, aligns: list) -> dict:
    name = module_name(s["uri"])
    src = REPO / s["resolve"]["path"]
    ttl = src.read_text(encoding="utf-8")
    commit = commit_of(src)
    if dirty(src):
        raise SystemExit(f"{src} has uncommitted changes: commit it first, so the header can name the commit")
    g = Graph().parse(data=ttl, format="turtle")
    scheme = URIRef(s["uri"])
    # Order: skos:notation when present, otherwise the order of the source file
    # (ordinal scales are written in order; alphabetical would scramble them).
    order = {}
    for c in set(g.subjects(SKOS.inScheme, scheme)):
        local = str(c)[len(s["uri"]):]
        m = re.search(r"(?:em:" + re.escape(local) + r"|<" + re.escape(str(c)) + r">)\s+a\s+skos:Concept", ttl)
        pos = m.start() if m else 10**9
        order[c] = pos
    concepts = sorted(order, key=lambda c: (str(next(g.objects(c, SKOS.notation), "")).zfill(6), order[c]))
    langs = sorted({o.language for c in concepts for o in g.objects(c, SKOS.prefLabel) if o.language},
                   key=lambda l: (l not in ("en", "it"), l))
    unverified = s.get("unverified_languages") or []
    title_en = s["labels"].get("en") or s["labels"].get("it")
    title_it = s["labels"].get("it")
    outdir = site / "public" / "vocab" / name
    outdir.mkdir(parents=True, exist_ok=True)

    header = (f"# PUBLISHED COPY — served at https://extendedmatrix.org/vocab/{name}/\n"
              f"# and resolved through {s['uri']}\n#\n"
              f"# The source of truth is stratigraph-templates, at\n#   {s['resolve']['path']}\n"
              f"# generated from commit {commit} by tools/publish_vocab.py. Do not edit this file here:\n"
              f"# edit it there and republish, or the two drift apart silently and the resolvable one is wrong.\n#\n")
    (outdir / f"{name}.ttl").write_text(header + ttl, encoding="utf-8")

    mine = [a for a in aligns if a.get("source", {}).get("scheme") == s["id"]]
    by_concept = {}
    for a in mine:
        by_concept.setdefault(a["source"]["concept"], []).append(a)

    arts = []
    for i, c in enumerate(concepts):
        frag = str(c)[len(s["uri"]):] or str(c)
        notation = next(g.objects(c, SKOS.notation), None)
        en = lit(g, c, SKOS.prefLabel, "en") or frag
        it = lit(g, c, SKOS.prefLabel, "it")
        den = lit(g, c, SKOS.definition, "en")
        dit = lit(g, c, SKOS.definition, "it")
        srcs = [str(o) for o in g.objects(c, DCTERMS.source)]
        others = [(l, lit(g, c, SKOS.prefLabel, l)) for l in langs if l not in ("en", "it")]
        others = [(l, v) for l, v in others if v]
        n = e(notation) if notation is not None else str(i + 1)
        star = "*" if "en" in unverified else ""
        a = [f'      <article id="{e(frag)}">',
             f'        <h3><span class="n">{n}</span> {e(en)}{star}</h3>',
             f'        <p class="uri"><code>{e(c)}</code></p>']
        if den:
            a.append(f"        <p>{e(den)}</p>")
        if it or dit:
            a.append(f'        <p lang="it" class="it"><strong>{e(it or "")}</strong>{" — " + e(dit) if dit else ""}</p>')
        if others:
            a.append('        <p class="labels">' + " · ".join(
                f'<span lang="{l}"{" dir=rtl" if l in RTL else ""}>{e(v)}</span> <small>({l}{"*" if l in unverified else ""})</small>'
                for l, v in others) + "</p>")
        for sv in srcs:
            a.append(f'        <p class="src">Source: {e(sv)}</p>')
        for al in by_concept.get(str(c), []):
            a.append(f'        <p class="src">{e(al.get("status", "proposed")).capitalize()} '
                     f'<code>skos:{e(al["match"])}</code> → <code>{e(al["target"]["concept"])}</code> '
                     f'({e(al["target"]["scheme"])})</p>')
        a.append("      </article>")
        arts.append("\n".join(a))

    n_ver = sum(1 for a in mine if a.get("status") == "verified")
    unv_note = ""
    if unverified:
        unv_note = (f'  <p class="note">Only the labels in the source language come from the sources. '
                    f'Labels marked with * ({", ".join(e(l) for l in unverified)}) were drafted with the module and '
                    f'nobody has verified them yet: usable now, to be corrected after review.</p>\n')
    desc = str(next(g.objects(scheme, DCTERMS.description), "") or title_en)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title_en)}</title>
<meta name="description" content="{e(desc)}">
<link rel="alternate" type="text/turtle" href="{e(name)}.ttl">
<style>
{CSS}
</style>
</head>
<body>
<main>
  <h1>{e(title_en)}</h1>
  <p class="sub">{e(title_it) + " — " if title_it and title_it != title_en else ""}an Extended Matrix vocabulary module.</p>

  <p>{e(desc)}</p>
{unv_note}
  <h2>Concepts</h2>
{chr(10).join(arts)}

  <h2>Using it</h2>
  <dl>
    <dt>Namespace</dt>
    <dd><code>{e(s['uri'])}</code></dd>
    <dt>Serialisation</dt>
    <dd><a href="{e(name)}.ttl">{e(name)}.ttl</a> (SKOS, Turtle) — {len(concepts)} concepts; labels in {", ".join(LANG_NAMES.get(l, l) for l in langs)}</dd>
    <dt>Version</dt>
    <dd>{e(s.get('version', ''))}</dd>
    <dt>Licence</dt>
    <dd>{e(s.get('license', ''))}</dd>
    <dt>Attribution</dt>
    <dd>{e(s.get('attribution', ''))}</dd>
    <dt>Published from</dt>
    <dd><a href="{SRC_URL}">stratigraph-templates</a>, <code>{e(s['resolve']['path'])}</code>, commit <code>{e(commit)}</code></dd>
  </dl>

  <h2>Alignments</h2>
  <p>{len(mine)} alignment{"s" if len(mine) != 1 else ""} declared, {n_ver} verified. Every alignment
  not marked verified is a proposal: it says what we think, marked as ours, until someone with standing
  in the target vocabulary confirms or rejects it. A match nobody has checked is never served as though it had been.</p>

  <footer>
    Part of the <a href="https://extendedmatrix.org">Extended Matrix</a> ecosystem.
    Source of truth: <a href="{SRC_URL}">stratigraph-templates</a>. <a href="../">All modules</a>.
  </footer>
</main>
</body>
</html>
"""
    (outdir / "index.html").write_text(page, encoding="utf-8")
    return {"name": name, "title": title_en, "version": s.get("version", ""), "license": s.get("license", ""),
            "uri": s["uri"], "n": len(concepts), "desc": desc, "commit": commit}


INDEX_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vocabulary modules</title>
<meta name="description" content="SKOS vocabulary modules originated and maintained in the Extended Matrix ecosystem.">
<style>
""" + CSS + """
</style>
</head>
<body>
<main>
  <h1>Vocabulary modules</h1>
  <p class="sub">Small controlled vocabularies the Extended Matrix ecosystem originates and maintains.</p>

  <p>These are modules, not a thesaurus. Each one exists because something we
  need to record has no identifier anywhere &mdash; checked, not assumed &mdash; and each
  is kept small enough that one person can be answerable for it. Where a term
  already lives in Getty, PeriodO or a national standard, we point at theirs
  instead of restating it: declaring beats copying, and a vocabulary nobody
  else maintains is a vocabulary that rots.</p>

  <p>Some modules stand in, provisionally, for a list that a national standard
  prescribes but has not yet published in machine-readable form. On the day the
  issuing institution publishes its own, an alignment is added and the institution's
  terms take precedence.</p>

  <p>Alignments to external vocabularies are published as proposals and marked
  as such until someone with standing in the target vocabulary confirms them. A
  match nobody has checked is never served as though it had been.</p>
"""
INDEX_TAIL = """
  <footer>
    Part of the <a href="/">Extended Matrix</a> ecosystem.
    Sources on <a href="https://github.com/StratiGraph-ECCCH/stratigraph-templates">GitHub</a>.
  </footer>
</main>
</body>
</html>
"""


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    site = Path(argv[0]).expanduser()
    wanted = set(argv[1:])
    aligns = load_alignments()
    built = []
    for s in load_schemes():
        name = module_name(s["uri"])
        if wanted and name not in wanted:
            continue
        built.append(build_module(site, s, aligns))
        print(f"published {name} ({built[-1]['n']} concepts, commit {built[-1]['commit']})")
    # the index lists every module present on the site, built now or before
    mods = {}
    for s in load_schemes():
        name = module_name(s["uri"])
        if (site / "public" / "vocab" / name / "index.html").exists():
            g = Graph().parse(REPO / s["resolve"]["path"], format="turtle")
            n = len(set(g.subjects(SKOS.inScheme, URIRef(s["uri"]))))
            mods[name] = (s, n)
    parts = []
    for name in sorted(mods):
        s, n = mods[name]
        parts.append(f"""
  <h2>{e(name)}</h2>
  <p><a href="{e(name)}/">{e(s['labels'].get('en') or s['labels'].get('it'))}</a> &mdash; {n} concepts.
  Version {e(s.get('version', ''))}, {e(s.get('license', ''))}.</p>
  <p class="meta"><code>{e(s['uri'])}</code></p>""")
    (site / "public" / "vocab" / "index.html").write_text(INDEX_HEAD + "".join(parts) + "\n" + INDEX_TAIL, encoding="utf-8")
    print(f"index: {len(mods)} modules")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
