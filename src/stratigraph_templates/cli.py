"""Command line: definitions in, sheets out. No server, no session, no database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .loader import find_template, load_record, templates_dir
from .model import MissingLabel
from .registry import RegistryUnavailable, registry, write_snapshot
from .render import RenderError, VocabTrace, sheet_html, write_pdf
from .validate import ValidationError, blocked_fields, validate_template
from .vocab import Vocabularies, VocabularyError
from .xsd_extract import extract_xsd


def _all_template_ids() -> List[str]:
    return sorted(d.name for d in templates_dir().iterdir() if (d / "template.yaml").is_file())


def _vocab() -> Vocabularies:
    return Vocabularies.load()


def _validate_one(name: str, reg, vocab: Vocabularies, quiet: bool = False) -> int:
    t = find_template(name)
    try:
        validate_template(t, reg, known_schemes=vocab.scheme_ids())
    except ValidationError as exc:
        print(f"✗ {t.id}", file=sys.stderr)
        for p in exc.problems:
            print(f"    {p}", file=sys.stderr)
        return 1
    blocked = blocked_fields(t)
    if not quiet:
        print(
            f"✓ {t.id}: {len(t.fields)} fields, {len(t.paragraphs)} paragraphs, "
            f"{len(t.edges())} relation slots, {len(t.sheet.sides)} sides, "
            f"languages {t.languages}"
        )
        if blocked:
            print(f"  · {len(blocked)} field(s) declared BLOCKED on a datamodel decision: {blocked}")
            for fid in blocked:
                print(f"      {fid} needs: {t.field(fid).graph.blocked_on.needs}")
    return 0


def cmd_validate(args) -> int:
    reg = registry(prefer_snapshot=args.snapshot)
    print(reg.provenance())
    vocab = _vocab()
    names = args.templates or _all_template_ids()
    return max(_validate_one(n, reg, vocab) for n in names)


def cmd_info(args) -> int:
    t = find_template(args.template)
    voc = [f for f in t.fields if f.vocabulary]
    verdicts = {}
    for f in t.fields:
        v = f.graph.verdict if f.graph else "MISSING"
        verdicts[v] = verdicts.get(v, 0) + 1
    payload = {
        "template": t.id,
        "standard": f"{t.standard.authority} {t.standard.code} {t.standard.version}",
        "kind": t.standard.kind,
        "invented": t.standard.invented,
        "languages": t.languages,
        "fields": len(t.fields),
        "paragraphs": len(t.paragraphs),
        "required": sum(1 for f in t.fields if f.required),
        "repeatable": sum(1 for f in t.fields if f.repeatable),
        "with_vocabulary": len(voc),
        "relation_slots": len(t.edges()),
        "verdicts": dict(sorted(verdicts.items())),
        "blocked_on_decision": blocked_fields(t),
        "sides": {s.id: len(s.rows) for s in t.sheet.sides},
        "human_key": t.identity.human_key,
        "human_key_pattern": t.identity.pattern,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _record(args):
    return load_record(args.record) if args.record else None


def _explain(trace: VocabTrace) -> None:
    if not trace.rows:
        return
    print("controlled terms — how each label was resolved:", file=sys.stderr)
    for field_id, concept, label, via in trace.rows:
        print(f"    {field_id}: {label!r}  ← {via}  {concept}", file=sys.stderr)
    bad = trace.uncontrolled()
    if bad:
        print(
            f"    ! {len(bad)} value(s) written as a bare string in a controlled box: "
            f"{[b[0] for b in bad]}",
            file=sys.stderr,
        )


def cmd_print(args) -> int:
    reg = registry(prefer_snapshot=args.snapshot)
    vocab = _vocab()
    t = find_template(args.template)
    validate_template(t, reg, known_schemes=vocab.scheme_ids())
    trace = VocabTrace()
    out = args.out or f"out/{t.id}.pdf"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    pages = write_pdf(t, _record(args), out, lang=args.lang, vocab=vocab, trace=trace)
    sides = len(t.sheet.sides)
    print(f"{out} — {t.standard.authority} {t.standard.code} {t.standard.version}, "
          f"{sides} side(s) → {pages} page(s), language '{args.lang or t.source_language}'")
    if pages > sides:
        print(
            f"  ! {pages - sides} page(s) more than sides: some box had to grow to keep what was "
            f"written. Nothing was clipped; the geometry of this definition is too tight for these "
            f"data",
            file=sys.stderr,
        )
    if args.explain_vocab:
        _explain(trace)
    return 0


def cmd_form(args) -> int:
    reg = registry(prefer_snapshot=args.snapshot)
    vocab = _vocab()
    t = find_template(args.template)
    validate_template(t, reg, known_schemes=vocab.scheme_ids())
    trace = VocabTrace()
    out = args.out or f"out/{t.id}-form.html"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    doc = sheet_html(t, _record(args), lang=args.lang, mode="form", vocab=vocab, trace=trace)
    Path(out).write_text(doc, encoding="utf-8")
    print(f"{out} — form, language '{args.lang or t.source_language}'")
    if args.explain_vocab:
        _explain(trace)
    return 0


def cmd_extract_xsd(args) -> int:
    draft, stats = extract_xsd(Path(args.xsd), authority=args.authority, code=args.code,
                               version=args.version)
    out = Path(args.out) if args.out else Path(f"out/draft-{args.code.lower()}.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(draft, encoding="utf-8")
    print(f"{out} — proposal, not truth")
    for k, v in stats.items():
        print(f"    {k}: {v}")
    return 0


def cmd_registry_snapshot(args) -> int:
    reg = write_snapshot()
    print(reg.provenance())
    return 0


def cmd_vocab(args) -> int:
    vocab = _vocab()
    if args.concept is None:
        for sid, s in sorted(vocab.schemes.items()):
            marks = []
            if s.fixture:
                marks.append("FIXTURE")
            marks.append(s.status)
            print(f"{sid:28s} [{', '.join(marks)}] {s.authority} — {s.license or 'licence not stated'}")
        print(f"{len(vocab.alignments)} alignment(s) declared")
        return 0
    res = vocab.resolve(args.scheme, args.concept, args.lang)
    print(f"{res.label}  ← {res.via}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="stratigraph-templates", description=__doc__)
    ap.add_argument("--snapshot", action="store_true",
                    help="check graph bindings against the recorded registry snapshot instead of a "
                         "live s3Dgraphy")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate", help="check definitions (shape + graph bindings)")
    p.add_argument("templates", nargs="*")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("info", help="the numbers of one definition")
    p.add_argument("template")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("print", help="A4 recto/verso PDF from definition + data")
    p.add_argument("template")
    p.add_argument("--record")
    p.add_argument("--lang")
    p.add_argument("-o", "--out")
    p.add_argument("--explain-vocab", action="store_true")
    p.set_defaults(func=cmd_print)

    p = sub.add_parser("form", help="fillable HTML form from the same definition")
    p.add_argument("template")
    p.add_argument("--record")
    p.add_argument("--lang")
    p.add_argument("-o", "--out")
    p.add_argument("--explain-vocab", action="store_true")
    p.set_defaults(func=cmd_form)

    p = sub.add_parser("extract-xsd", help="propose a draft definition from an ICCD catalogue XSD")
    p.add_argument("xsd")
    p.add_argument("--authority", default="ICCD")
    p.add_argument("--code", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_extract_xsd)

    p = sub.add_parser("registry-snapshot", help="record what s3Dgraphy declares today")
    p.set_defaults(func=cmd_registry_snapshot)

    p = sub.add_parser("vocab", help="list schemes, or resolve a concept label")
    p.add_argument("--scheme")
    p.add_argument("--concept")
    p.add_argument("--lang", default="it")
    p.set_defaults(func=cmd_vocab)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, RenderError, VocabularyError, MissingLabel, RegistryUnavailable,
            FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
