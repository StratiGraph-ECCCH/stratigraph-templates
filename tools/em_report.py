"""The reports `em.sh` and `em.bat` print — one implementation for both shells.

    python tools/em_report.py provenance   # where registry/s3dgraphy-snapshot.json came from
    python tools/em_report.py status [S3D_SRC]
                                           # snapshot vs the s3Dgraphy next door, on what we read
    python tools/em_report.py changed      # compiled schede that differ from the last commit, and how

Reads only; writes nothing. Exit codes: `status` 1 when the datamodel differs on
the files this repository reads, 2 when s3Dgraphy cannot be read.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "registry" / "s3dgraphy-snapshot.json"


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def provenance() -> int:
    d = _snapshot()
    t = d.get("taken_from") or {}
    c = (t.get("git_commit") or "?")[:7]
    print(f"  taken from s3Dgraphy {c} ({'DIRTY' if t.get('git_dirty') else 'clean'})"
          f" · s3dgraphy {d.get('s3dgraphy_version')} · on {d.get('taken_on')}")
    v = (d.get("datamodel") or {}).get("versions") or {}
    print("  " + " · ".join(f"{k} {v[k]}" for k in v) + f" · em.ttl {d.get('em_ttl_version')}")
    return 0


def status(s3d_src: str) -> int:
    sys.path.insert(0, s3d_src)
    sys.path.insert(0, str(ROOT / "src"))
    from stratigraph_templates.registry import DATAMODEL_READS
    try:
        import s3dgraphy
        from s3dgraphy.datamodel import datamodel_fingerprint, fingerprint_differences
    except Exception as exc:  # absent, or a s3dgraphy older than the fingerprint
        print(f"  cannot read s3Dgraphy's fingerprint ({exc.__class__.__name__}: {exc})")
        return 2
    live = datamodel_fingerprint()
    expected = _snapshot().get("datamodel") or {}
    print(f"  s3dgraphy  {s3dgraphy.__version__}  datamodel {live['digest']}")
    print(f"  snapshot             datamodel {expected.get('digest') or '— (format < 4)'}")
    for n in DATAMODEL_READS:
        a = (expected.get("digests") or {}).get(n)
        b = (live.get("digests") or {}).get(n)
        va = (expected.get("versions") or {}).get(n) or "—"
        vb = live["versions"].get(n) or "—"
        print(f"    {'=' if a == b else '≠'} {n:<14} snapshot {va:<8} s3Dgraphy {vb}")
    diffs = fingerprint_differences(expected, live, DATAMODEL_READS)
    if diffs:
        print("  datamodel DIFFERS on what this repository reads:")
        for d in diffs:
            print("    " + d)
        print("  → ./em.sh after-bump")
        return 1
    print("  datamodel aligned on " + ", ".join(DATAMODEL_READS)
          + " (the snapshot's em.ttl terms are compared by validate)")
    return 0


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True).stdout


def changed() -> int:
    paths = [line[3:] for line in _git("status", "--porcelain", "--", "dist/schede").splitlines()
             if line[3:].endswith(".json") and not line[3:].endswith("index.json")]
    if not paths:
        print("  none — dist/schede is what was committed")
    for p in sorted(paths):
        new = json.loads((ROOT / p).read_text(encoding="utf-8")).get("header") or {}
        old_raw = _git("show", f"HEAD:{p}")
        sid, ver = new.get("id"), new.get("version")
        if not old_raw:
            print(f"  {sid} {ver}  NEW version")
            continue
        old = json.loads(old_raw).get("header") or {}
        if old.get("digest") != new.get("digest"):
            print(f"  {sid} {ver}  DEFINITION digest changed — a published version must not: "
                  "raise template.version")
            continue
        od, nd = old.get("datamodel") or {}, new.get("datamodel") or {}
        moved = [k for k in ("nodes", "node_registry", "connections", "visual_rules", "qualia",
                             "translations", "em_ttl", "digest") if od.get(k) != nd.get(k)]
        if moved:
            print(f"  {sid} {ver}  datamodel "
                  + ", ".join(f"{k} {od.get(k)} → {nd.get(k)}" for k in moved)
                  + "  (same definition digest)")
            continue
        prov = []
        if od.get("s3dgraphy") != nd.get("s3dgraphy"):
            prov.append(f"s3dgraphy {od.get('s3dgraphy')} → {nd.get('s3dgraphy')}")
        ot, nt = od.get("taken_from") or {}, nd.get("taken_from") or {}
        if ot != nt:
            prov.append(f"taken_from {str(ot.get('git_commit', '?'))[:7]}"
                        f" → {str(nt.get('git_commit', '?'))[:7]}")
        print(f"  {sid} {ver}  provenance only: " + (", ".join(prov) or "header bytes")
              + "  (same digest, same datamodel)")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "provenance":
        return provenance()
    if cmd == "status":
        src = argv[1] if len(argv) > 1 else os.environ.get(
            "STRATIGRAPH_S3DGRAPHY_SRC", str(ROOT.parent / "s3Dgraphy" / "src"))
        return status(src)
    if cmd == "changed":
        return changed()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
