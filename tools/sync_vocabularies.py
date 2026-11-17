#!/usr/bin/env python3
"""Refresh `vocabularies/` — the COPY — from its source, ExtendedMatrix/vocabularies.

Since 25 October 2026 the vocabularies live in their own repository; the copy
here stays so that nothing reading `vocabularies/schemes/*.yaml` breaks
(vocabularies/README.md). It is never edited by hand: this script rewrites it.

    python3 tools/sync_vocabularies.py                 # from the sibling checkout
    python3 tools/sync_vocabularies.py ../vocabularies
    python3 tools/sync_vocabularies.py --check         # exit 1 if the copy differs

What it copies: `schemes/`, `skos/`, `alignments/`, `fixtures/` — every file,
byte for byte, but for ONE rewrite: a path written relative to the source
repository (`path: "skos/…"`, `path: "fixtures/…"`, and the same folders named
in comments) gets the `vocabularies/` prefix this repository reads them under.
A file the source no longer has is removed from the copy. `README.md` at the
top of the copy is this repository's own and is left alone.

MICRO-J (17 Nov 2026): written when em-media-role, born here by mistake on
14 Nov, went home to the source and the copy had to follow.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COPY = REPO / "vocabularies"
FOLDERS = ("schemes", "skos", "alignments", "fixtures")
#: `skos/x.ttl` → `vocabularies/skos/x.ttl` where it is a path of the source
_PATH = re.compile(r'(?<![\w/.-])(' + "|".join(FOLDERS) + r')/')


def copied(text: str) -> str:
    """What a source file becomes in the copy."""
    return _PATH.sub(r"vocabularies/\1/", text)


def plan(source: Path) -> dict:
    """{relative path in the copy: content} for every file the copy must hold."""
    out = {}
    for folder in FOLDERS:
        for p in sorted((source / folder).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                rel = p.relative_to(source).as_posix()
                out[rel] = copied(p.read_text(encoding="utf-8"))
    return out


def differences(source: Path) -> list:
    want = plan(source)
    have = {p.relative_to(COPY).as_posix() for folder in FOLDERS
            for p in (COPY / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    diffs = [f"missing {r}" for r in sorted(set(want) - have)]
    diffs += [f"extra {r}" for r in sorted(have - set(want))]
    diffs += [f"differs {r}" for r in sorted(set(want) & have)
              if (COPY / r).read_text(encoding="utf-8") != want[r]]
    return diffs


def find_source(arg: str | None) -> Path:
    for cand in ([Path(arg)] if arg else []) + [REPO.parent / "vocabularies"]:
        if (cand / "schemes").is_dir() and (cand / "skos").is_dir():
            return cand.resolve()
    sys.exit("no ExtendedMatrix/vocabularies checkout (give its path)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", nargs="?")
    ap.add_argument("--check", action="store_true", help="only say whether the copy differs")
    a = ap.parse_args(argv)
    source = find_source(a.source)
    diffs = differences(source)
    if a.check:
        for d in diffs:
            print(" ", d)
        print(f"copy {'differs from' if diffs else 'is'} {source}" + (f" ({len(diffs)})" if diffs else ""))
        return 1 if diffs else 0
    want = plan(source)
    for folder in FOLDERS:
        for p in (COPY / folder).rglob("*"):
            if p.is_file() and p.relative_to(COPY).as_posix() not in want:
                p.unlink()
                print("  removed", p.relative_to(REPO))
    for rel, text in want.items():
        dst = COPY / rel
        if not dst.is_file() or dst.read_text(encoding="utf-8") != text:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")
            print("  wrote", dst.relative_to(REPO))
    print(f"copy refreshed from {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
