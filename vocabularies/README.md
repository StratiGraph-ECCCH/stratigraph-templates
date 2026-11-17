# COPY — the source of these vocabularies is now ExtendedMatrix/vocabularies

**Source of truth:** <https://github.com/ExtendedMatrix/vocabularies>
(from 25 October 2026). The modules are served, as before, at
`https://w3id.org/extendedmatrix/vocab/<module>/`.

This folder was split out with its history into that repository (the last
commit here that touched it is `14e5f3a`). The files stay so that nothing
reading them breaks: the renderer, the validator and the tests of this
repository resolve `vocabularies/schemes/*.yaml` and the paths written in
them, relative to this repository.

**Do not edit them here.** A change to a module, a card or an alignment is a
pull request to ExtendedMatrix/vocabularies, reviewed there; this copy is
then refreshed from it with

```
python3 tools/sync_vocabularies.py [path of the vocabularies checkout]
python3 tools/sync_vocabularies.py --check     # does the copy match the source?
```

which copies `schemes/`, `skos/`, `alignments/`, `fixtures/` byte for byte with
one rewrite: a path relative to that repository (`skos/…`) gets the
`vocabularies/` prefix it is read under here. Since 17 November 2026 the cards
are otherwise identical (they carry `lifecycle` and `curators` here too), and
`tests/test_vocabularies_copy.py` fails when the copy and a sibling checkout of
the source disagree. (em-media-role was born in this copy on 14 November by
mistake; it went home to the source on the 17th, and this script was written
then.)

Publishing to the site is done from there too (`tools/publish_vocab.py` in
that repository); the old script in `tools/` here refuses to run, so that it
cannot republish a stale copy under the old provenance.
