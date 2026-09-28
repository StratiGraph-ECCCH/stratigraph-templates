# Sphinx configuration — stratigraph-templates
#
# Mirrors s3Dgraphy's docs/conf.py (theme, MyST, intersphinx, composed version
# badge, LaTeX with XeLaTeX and DejaVu, generator hooked on builder-inited) with
# the names changed. Three differences are deliberate:
#
# * the pages carry no text of their own: README.md, SPEC.md and LICENSING.md
#   are the source and are INCLUDED (docs/_tools/generate.py writes the
#   wrappers into docs/pages/, computing the lines from the headings);
# * the generator is NOT best-effort here: if it fails, the build stops.
#   Without it whole pages would be missing, not just figures, and a site that
#   publishes anyway with half an index is worse than a red build;
# * two languages. English is the source; Italian is a gettext translation in
#   docs/locale/it/LC_MESSAGES/, paragraph by paragraph. On Read the Docs the
#   Italian project is a translation of the English one and the build language
#   comes from READTHEDOCS_LANGUAGE. A paragraph changed in English and not yet
#   in the catalogue shows in English on the Italian site: stale, never wrong.
#   `sphinx-build -b gettext` + `sphinx-intl update -l it` refresh the catalogue.

import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(HERE, '_tools'))

# -- Project ----------------------------------------------------------------
project = 'stratigraph-templates'
copyright = f'2026-{datetime.datetime.now().year}, Emanuel Demetrescu — CNR-ISPC'
author = 'Emanuel Demetrescu'


def _read_version():
    """The package version, never typed here: from the package or pyproject."""
    try:
        from importlib.metadata import version as _v
        return _v('stratigraph-templates')
    except Exception:
        pass
    with open(os.path.join(ROOT, 'pyproject.toml'), encoding='utf-8') as fh:
        m = re.search(r'^version\s*=\s*"([^"]+)"', fh.read(), re.MULTILINE)
    if not m:
        raise RuntimeError('version not found in pyproject.toml')
    return m.group(1)


release = _read_version()
version = '.'.join(release.split('.')[:2])   # the line (0.1)

# The badge is composed from the resolved version, as in s3Dgraphy.
_badge_version = release.replace('-', '--')
rst_prolog = """
.. |version_badge| image:: https://img.shields.io/badge/version-%s-blue.svg
   :alt: Version %s
""" % (_badge_version, release)
myst_substitutions = {'release': release}

# -- Extensions -------------------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '_tools', 'locale']
master_doc = 'index'
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}

# -- Languages --------------------------------------------------------------
language = os.environ.get('READTHEDOCS_LANGUAGE', os.environ.get('DOCS_LANGUAGE', 'en')).split('-')[0]
locale_dirs = ['locale/']
gettext_compact = False                     # one catalogue per page
gettext_uuid = False
gettext_location = False                    # line numbers would churn the catalogue
# Code blocks are translated too (their comments are prose). They are EXTRACTED by
# the gettext builder (language en), but not translated by Sphinx's own Locale
# transform, which re-parses the msgstr as markup and, under MyST, turns a code
# block into a stray "::". LiteralBlocksI18n below puts them back verbatim.
gettext_additional_targets = ['literal-block'] if language == 'en' else []

# -- MyST -------------------------------------------------------------------
myst_enable_extensions = ['deflist', 'colon_fence', 'fieldlist', 'linkify', 'substitution']
myst_heading_anchors = 3
suppress_warnings = [
    # included sections often start with a level-2 heading
    'myst.header',
    # a ```json block in SPEC.md uses «...» as a placeholder: highlighted anyway
    'misc.highlighting_failure',
]

# -- HTML -------------------------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': False,     # the archive stays out of the menu
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

# -- LaTeX / PDF (as in s3Dgraphy: the PDF is what gets deposited with the DOI)
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

# -- autodoc (last in the menu: the repository is data, not an application) -
autodoc_default_options = {'members': True, 'member-order': 'bysource', 'undoc-members': False}
autodoc_mock_imports = ['weasyprint', 'rdflib']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# -- Links between the root files -------------------------------------------
# README, SPEC and LICENSING cite each other as files ([SPEC.md](SPEC.md)), with
# paths relative to the file that contains them, not to the page that includes
# it. Before MyST resolves the links, this pass re-reads them from the node's
# source file: the three root files lead to the page that includes them, any
# other file of the repository (templates/…, src/…) to the file on GitHub.
_ROOT_DOCS = {'SPEC.md': 'pages/spec', 'LICENSING.md': 'pages/licensing',
              'README.md': 'pages/what-it-is'}
_GITHUB = 'https://github.com/StratiGraph-ECCCH/stratigraph-templates/blob/main/'

from sphinx.transforms.post_transforms import SphinxPostTransform  # noqa: E402


class RepoLinks(SphinxPostTransform):
    default_priority = 8          # before MystReferenceResolver (9)

    def run(self, **kwargs):
        from docutils import nodes
        from sphinx import addnodes
        for node in list(self.document.findall(addnodes.pending_xref)):
            if node.get('reftype') != 'myst':
                continue
            # MyST 4 reads the link against the PAGE and drops the suffix
            # ('pages/SPEC'); MyST 5 leaves the path as written in the file
            # ('SPEC.md'). Either way it is re-read from the FILE.
            raw = node.get('reftarget') or ''
            here = os.path.dirname(node.source or self.env.doc2path(self.env.docname))
            cands = [raw if os.path.isabs(raw) else os.path.join(here, raw)]
            if not os.path.isabs(raw):
                back = os.path.relpath(raw, os.path.dirname(node.get('refdoc', '')) or '.')
                cands.append(os.path.join(here, back))
                # a paragraph translated through gettext no longer knows the file it
                # came from (its source is the page), so a root-file name goes to the
                # root file FIRST — on a case-insensitive disk 'pages/LICENSING.md'
                # would otherwise match the generated page 'pages/licensing.md'
                for name in (os.path.basename(raw), os.path.basename(raw) + '.md'):
                    if name in _ROOT_DOCS:
                        cands.insert(0, os.path.join(ROOT, name))
            path = next((os.path.normpath(c + sfx) for c in cands for sfx in ('', '.md')
                         if os.path.isfile(os.path.normpath(c + sfx))), None)
            if path is None or not path.startswith(ROOT + os.sep):
                continue
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            if rel.startswith('docs/'):
                continue          # a page of the site: MyST resolves it
            if rel in _ROOT_DOCS:
                uri = self.app.builder.get_relative_uri(self.env.docname, _ROOT_DOCS[rel])
            else:
                uri = _GITHUB + rel
            ref = nodes.reference('', '', internal=rel in _ROOT_DOCS, refuri=uri)
            ref += node.children
            node.replace_self(ref)


# "Edit on GitHub" on a generated page would lead to a file that is not in the
# repository: there the link points to the root file the page includes.
_SOURCE_OF = {'what-it-is': 'README.md', 'kinds': 'README.md', 'usage': 'README.md',
              'licences-summary': 'README.md', 'licensing': 'LICENSING.md', 'spec': 'SPEC.md'}


def _page_context(app, pagename, templatename, context, doctree):
    if not pagename.startswith('pages/'):
        return
    stem = pagename.split('/', 1)[1]
    src = _SOURCE_OF.get(stem) or ('SPEC.md' if stem.startswith('spec-') else None)
    if src is None:               # the catalogues: there is no file to edit
        context['display_github'] = False
        return
    context['meta'] = dict(context.get('meta') or {}, github_url=_GITHUB + src)


from sphinx.transforms import SphinxTransform  # noqa: E402


class LiteralBlocksI18n(SphinxTransform):
    """Translate code blocks from the catalogue, verbatim, never re-parsed."""
    default_priority = 21         # right after sphinx.transforms.i18n.Locale (20)

    def apply(self, **kwargs):
        if self.config.language == 'en':
            return
        from docutils import nodes
        from sphinx.locale import init as init_locale
        from sphinx.util.i18n import docname_to_domain
        dirs = [os.path.join(self.env.srcdir, d) for d in self.config.locale_dirs]
        domain = docname_to_domain(self.env.docname, self.config.gettext_compact)
        catalog, found = init_locale(dirs, self.config.language, domain)
        if not found:
            return
        for node in self.document.findall(nodes.literal_block):
            src = node.rawsource or node.astext()
            dst = catalog.gettext(src)
            if dst and dst != src:
                node[:] = [nodes.Text(dst)]
                node.rawsource = dst


def _generate(app):
    import generate
    generate.main(app.config.language)
    print(f'[stratigraph-templates] pages generated in docs/pages/ ({app.config.language})')


def setup(app):
    app.connect('builder-inited', _generate)
    app.connect('html-page-context', _page_context)
    app.add_post_transform(RepoLinks)
    app.add_transform(LiteralBlocksI18n)
