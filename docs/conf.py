# Configurazione Sphinx — stratigraph-templates
#
# Rispecchia docs/conf.py di s3Dgraphy (tema, MyST, intersphinx, badge di
# versione composto, LaTeX con XeLaTeX e DejaVu, generatore agganciato a
# builder-inited) e ne cambia i nomi. Due differenze sono volute:
#
# * le pagine non contengono testo proprio: README.md, SPEC.md e LICENSING.md
#   sono la fonte e vengono INCLUSI (docs/_tools/generate.py scrive gli
#   involucri in docs/_generated/, calcolando le righe dai titoli);
# * il generatore qui NON è best-effort: se non riesce, il build si ferma.
#   Senza di lui mancherebbero le pagine, non solo le cifre, e un sito che si
#   pubblica lo stesso con metà indice è peggio di un build rosso.

import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(HERE, '_tools'))

# -- Progetto ---------------------------------------------------------------
project = 'stratigraph-templates'
copyright = f'2026-{datetime.datetime.now().year}, Emanuel Demetrescu — CNR-ISPC'
author = 'Emanuel Demetrescu'


def _read_version():
    """La versione del pacchetto, mai scritta qui: dal pacchetto o da pyproject."""
    try:
        from importlib.metadata import version as _v
        return _v('stratigraph-templates')
    except Exception:
        pass
    with open(os.path.join(ROOT, 'pyproject.toml'), encoding='utf-8') as fh:
        m = re.search(r'^version\s*=\s*"([^"]+)"', fh.read(), re.MULTILINE)
    if not m:
        raise RuntimeError('versione non trovata in pyproject.toml')
    return m.group(1)


release = _read_version()
version = '.'.join(release.split('.')[:2])   # la linea (0.1), come lo slug su RTD

# Il badge si compone dalla versione risolta, come in s3Dgraphy.
_badge_version = release.replace('-', '--')
rst_prolog = """
.. |version_badge| image:: https://img.shields.io/badge/version-%s-blue.svg
   :alt: Version %s
""" % (_badge_version, release)
myst_substitutions = {'release': release}

# -- Estensioni -------------------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '_tools']
master_doc = 'index'
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
language = 'it'

# -- MyST -------------------------------------------------------------------
myst_enable_extensions = ['deflist', 'colon_fence', 'fieldlist', 'linkify', 'substitution']
myst_heading_anchors = 3
suppress_warnings = [
    # le sezioni incluse cominciano spesso da un titolo di livello 2
    'myst.header',
    # un blocco ```json di SPEC.md usa «...» come segnaposto: si evidenzia lo stesso
    'misc.highlighting_failure',
]

# -- HTML -------------------------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': False,     # l'archivio resta fuori dal menu
    'titles_only': False,
}
html_context = {
    'display_github': True,
    'github_user': 'StratiGraph-ECCCH',
    'github_repo': 'stratigraph-templates',
    'github_version': 'main',
    'conf_py_path': '/docs/',
}
html_last_updated_fmt = '%d %b %Y'

# -- LaTeX / PDF (come s3Dgraphy: il PDF è ciò che si deposita col DOI) -----
latex_engine = 'xelatex'
latex_use_xindy = False
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'figure_align': 'htbp',
    'fontpkg': r"""
\IfFontExistsTF{DejaVu Serif}
  {\setmainfont{DejaVu Serif}}
  {\IfFontExistsTF{FreeSerif}{\setmainfont{FreeSerif}}{}}
\IfFontExistsTF{DejaVu Sans}
  {\setsansfont{DejaVu Sans}}
  {\IfFontExistsTF{FreeSans}{\setsansfont{FreeSans}}{}}
\IfFontExistsTF{DejaVu Sans Mono}
  {\setmonofont{DejaVu Sans Mono}[Scale=MatchLowercase]}
  {\IfFontExistsTF{FreeMono}{\setmonofont{FreeMono}[Scale=MatchLowercase]}{}}
""",
    'preamble': r"""
\sloppy
""",
}
latex_documents = [
    ('index', 'stratigraph-templates.tex', 'stratigraph-templates',
     'Emanuel Demetrescu', 'manual'),
]
latex_show_urls = 'footnote'

# -- autodoc (in fondo al menu: il repository è dati, non un'applicazione) --
autodoc_default_options = {'members': True, 'member-order': 'bysource', 'undoc-members': False}
autodoc_mock_imports = ['weasyprint', 'rdflib']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# -- Link fra i file di radice ----------------------------------------------
# README, SPEC e LICENSING si citano fra loro come file ([SPEC.md](SPEC.md)),
# con percorsi relativi al file che li contiene, non alla pagina che li include.
# Prima che MyST risolva i link, questo passo li legge rispetto al file sorgente
# del nodo: i tre file di radice portano alla pagina che li include, ogni altro
# file del repository (templates/…, src/…) al file su GitHub.
_ROOT_DOCS = {'SPEC.md': '_generated/spec', 'LICENSING.md': '_generated/licensing',
              'README.md': '_generated/cose'}
_GITHUB = 'https://github.com/StratiGraph-ECCCH/stratigraph-templates/blob/main/'

from sphinx.transforms.post_transforms import SphinxPostTransform  # noqa: E402


class RepoLinks(SphinxPostTransform):
    default_priority = 8          # prima di MystReferenceResolver (9)

    def run(self, **kwargs):
        from docutils import nodes
        from sphinx import addnodes
        for node in list(self.document.findall(addnodes.pending_xref)):
            if node.get('reftype') != 'myst' or not node.source:
                continue
            # MyST ha già letto il link rispetto alla PAGINA e tolto il suffisso:
            # si torna al percorso scritto nel file e lo si rilegge dal file.
            target = node.get('reftarget') or ''
            if not os.path.isabs(target):
                target = os.path.relpath(target, os.path.dirname(node.get('refdoc', '')) or '.')
                target = os.path.join(os.path.dirname(node.source), target)
            path = next((os.path.normpath(target + sfx) for sfx in ('.md', '')
                         if os.path.isfile(os.path.normpath(target + sfx))), None)
            if path is None or not path.startswith(ROOT + os.sep):
                continue
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            if rel.startswith('docs/'):
                continue          # un documento del sito: lo risolve MyST
            if rel in _ROOT_DOCS:
                uri = self.app.builder.get_relative_uri(self.env.docname, _ROOT_DOCS[rel])
            else:
                uri = _GITHUB + rel
            ref = nodes.reference('', '', internal=rel in _ROOT_DOCS, refuri=uri)
            ref += node.children
            node.replace_self(ref)


def _generate(app):
    import generate
    generate.main()
    print('[stratigraph-templates] pagine generate in docs/_generated/')


# «Edit on GitHub» su una pagina generata porterebbe a un file che non è nel
# repository: lì il link punta al file di radice che la pagina include.
_SOURCE_OF = {'cose': 'README.md', 'specie': 'README.md', 'uso': 'README.md',
              'licenze-sintesi': 'README.md', 'licensing': 'LICENSING.md', 'spec': 'SPEC.md'}


def _page_context(app, pagename, templatename, context, doctree):
    if not pagename.startswith('_generated/'):
        return
    stem = pagename.split('/', 1)[1]
    src = _SOURCE_OF.get(stem) or ('SPEC.md' if stem.startswith('spec-') else None)
    if src is None:               # i cataloghi: non c'è un file da modificare
        context['display_github'] = False
        return
    context['meta'] = dict(context.get('meta') or {}, github_url=_GITHUB + src)


def setup(app):
    app.connect('builder-inited', _generate)
    app.connect('html-page-context', _page_context)
    app.add_post_transform(RepoLinks)
