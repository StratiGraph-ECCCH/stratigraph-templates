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
then refreshed from it. The cards there differ from these in two ways only:
their `resolve.path` is relative to that repository (`skos/…` instead of
`vocabularies/skos/…`), and the modules we originate also carry `lifecycle`
and `curators`.

Publishing to the site is done from there too (`tools/publish_vocab.py` in
that repository); the old script in `tools/` here refuses to run, so that it
cannot republish a stale copy under the old provenance.
