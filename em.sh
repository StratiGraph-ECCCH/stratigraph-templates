#!/usr/bin/env bash
# stratigraph-templates — one entry point, the same ergonomics as EMtools' and
# EMStudio's `em.sh`. Every command calls what the repository already has: the
# CLI (`stratigraph_templates.cli`), `pytest`, `pip`. Nothing here compiles,
# validates or snapshots by itself.
#
# WHY `python -m` AND NOT `.venv/bin/stratigraph-templates`: the console script
# is a file pip writes, with the interpreter's path baked into its first line.
# It goes missing (a venv created without the install step) and goes stale (a
# Homebrew upgrade that moves the interpreter); `python -m
# stratigraph_templates.cli` only needs the package to be importable, which is
# what an editable install guarantees. So every command below runs
# `.venv/bin/python -m stratigraph_templates.cli …`, and `setup` still checks
# that the script exists, for whoever types the long form from the README.
#
# Start with:  ./em.sh help
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
CLI=("$PY" -m stratigraph_templates.cli)
S3D_SRC="${STRATIGRAPH_S3DGRAPHY_SRC:-$ROOT/../s3Dgraphy/src}"

log()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m⚠  %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

need_venv() {
  [[ -x "$PY" ]] || die "no .venv here (or it lost its interpreter). Run: ./em.sh setup"
  "$PY" -c 'import stratigraph_templates' 2>/dev/null \
    || die "the .venv cannot import stratigraph_templates. Run: ./em.sh setup"
}

# ── help ──────────────────────────────────────────────────────────────────────

help_overview() {
  cat <<'EOF'
stratigraph-templates — ./em.sh <command> [args]

Recording sheets are DATA; this repository compiles them against a SNAPSHOT of
s3Dgraphy's datamodel. These commands wrap the CLI, pytest and pip that the
repository already uses. Nothing here commits or pushes.

  setup                 Create or repair .venv (python >= 3.11, pip install -e '.[dev]').
                          ./em.sh setup
  snapshot              Re-take registry/s3dgraphy-snapshot.json from s3Dgraphy; show the diff.
                          ./em.sh snapshot
  validate [ids…]       Check the definitions (shape + graph bindings).
                          ./em.sh validate iccd-us-2021
  build [ids…]          Compile to dist/schede/<id>/<version>.json + index.json.
                          ./em.sh build
  after-bump            snapshot → validate → build, stop at the first error,
                        list the schede whose compiled output changed.
                          ./em.sh after-bump
  info <id>             The numbers of one definition.
                          ./em.sh info iccd-us-2021
  print <id> [args…]    A4 PDF (passes the arguments to the CLI).
                          ./em.sh print iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.pdf
  form <id> [args…]     Fillable HTML form (passes the arguments to the CLI).
                          ./em.sh form iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.html
  vocab [args…]         List schemes, or resolve a concept label.
                          ./em.sh vocab --scheme fx-ue-definicion-es
  cli [args…]           Any other CLI subcommand, as is.
                          ./em.sh cli extract-xsd <file.xsd> --code SAS --version 3.00
  test [pytest args…]   Run the test suite.
                          ./em.sh test -q
  status                Snapshot vs the s3Dgraphy next door: versions, fingerprint, files that differ.
                          ./em.sh status
  help [command]        This list, or the long help of one command.
                          ./em.sh help after-bump

The usual day after a datamodel change in s3Dgraphy:
    ./em.sh status        # does the snapshot still match?
    ./em.sh after-bump    # if not: re-snapshot, validate, build
    git diff registry/ dist/   # review, then commit by hand
EOF
}

help_setup() {
  cat <<'EOF'
./em.sh setup

WHAT IT DOES
  Creates .venv if it is missing, or repairs it if its interpreter is gone or
  older than 3.11 (pyproject: requires-python >= 3.11). Then:
      .venv/bin/python -m pip install -e '.[dev]'
  ([dev] = pytest, weasyprint, rdflib). Finally it checks that the console
  script .venv/bin/stratigraph-templates exists and that
  `python -m stratigraph_templates.cli --help` runs.

  The interpreter, in order: $PYTHON if you set it, else the newest of
  python3.14 / 3.13 / 3.12 / 3.11 on PATH, else python3 if it is >= 3.11.
  A .venv that already works is kept and only re-installed into.

WHAT IT DOES NOT DO
  It does not install s3Dgraphy (the snapshot reads ../s3Dgraphy/src from
  source), WeasyPrint's system libraries (macOS: brew install pango), nor the
  two vocabulary checkouts beside this repo (see the README). No git.

WHEN
  After cloning; after a Homebrew Python upgrade; whenever a command says
  "Run: ./em.sh setup".

EXAMPLE
  $ ./em.sh setup
  ▸ using /opt/homebrew/bin/python3.14 (Python 3.14.7)
  ▸ pip install -e '.[dev]'
  ✓ .venv ready: .venv/bin/stratigraph-templates present, the CLI answers

IF IT FAILS
  "no Python >= 3.11 found" → install one (brew install python@3.13) or run
  PYTHON=/path/to/python3.13 ./em.sh setup.  A pip error → read it; offline,
  pip cannot resolve PyYAML/pytest. A .venv that will not repair →
  rm -rf .venv && ./em.sh setup.
EOF
}

help_snapshot() {
  cat <<'EOF'
./em.sh snapshot

WHAT IT DOES
  Runs `stratigraph-templates registry-snapshot`: records what s3Dgraphy
  declares TODAY (node/connections/qualia datamodels, node registry, em.ttl
  terms, CRDT operations, the datamodel fingerprint) into
  registry/s3dgraphy-snapshot.json. s3Dgraphy is read from
  $STRATIGRAPH_S3DGRAPHY_SRC, else ../s3Dgraphy/src.
  It prints where the snapshot came from (s3Dgraphy commit, dirty flag,
  s3dgraphy version) and `git diff --stat` + the version lines of registry/,
  because re-taking the snapshot is a DECISION: every sheet compiled after it
  is compiled against it.

WHAT IT DOES NOT DO
  It does not validate, build or commit. It does not touch s3Dgraphy.

WHEN
  After a datamodel change in s3Dgraphy that the sheets should follow
  (`./em.sh status` says the snapshot differs, or `validate` exits 2).

EXAMPLE
  $ ./em.sh snapshot
  ▸ registry-snapshot from /Users/you/Documents/GitHub/s3Dgraphy/src
    taken from s3Dgraphy 42ea27c (clean) · s3dgraphy 1.6.0.dev25
    registry/s3dgraphy-snapshot.json | 12 ++++++------

IF IT FAILS
  "RegistryUnavailable" → s3Dgraphy is not where it is looked for: set
  STRATIGRAPH_S3DGRAPHY_SRC=/path/to/s3Dgraphy/src. An ImportError inside
  s3dgraphy → that checkout is broken; run its tests (s3Dgraphy: ./em.sh test).
  To undo a snapshot you did not want: git checkout -- registry/ (by hand).
EOF
}

help_validate() {
  cat <<'EOF'
./em.sh validate [template-id …] [--draft]

WHAT IT DOES
  `stratigraph-templates validate`: checks every definition (or the ones named)
  for shape and graph bindings, against the snapshot — and first compares the
  snapshot with the s3Dgraphy working tree.

WHAT IT DOES NOT DO
  It writes nothing.

WHEN
  After editing a definition under templates/, or after `snapshot`.

EXAMPLE
  $ ./em.sh validate iccd-us-2021
  iccd-us-2021 1.2.0 … ok

IF IT FAILS
  Exit 2 with "RegistryDivergence" and lines like `datamodel: nodes 1.6.18 vs
  1.6.19` → s3Dgraphy moved: ./em.sh after-bump (or ./em.sh snapshot, then
  validate). Exit 1 with errors about a field → fix the definition it names.
  To compile against the snapshot WITHOUT comparing it, use the CLI directly:
  ./em.sh cli --snapshot validate.
EOF
}

help_build() {
  cat <<'EOF'
./em.sh build [template-id …] [-o DIR]

WHAT IT DOES
  `stratigraph-templates build`: compiles definitions to
  dist/schede/<id>/<version>.json and dist/schede/index.json — header (with the
  datamodel fingerprint) + recipe (the five CRDT operations).

WHAT IT DOES NOT DO
  It does not commit dist/, and it never rewrites a published version with a
  different definition digest: that raises PublishedVersionChanged.

WHEN
  After validate passes; after a snapshot (a datamodel-only change rewrites the
  current sheets' header.datamodel, same digest).

EXAMPLE
  $ ./em.sh build
  wrote dist/schede/iccd-us-2021/1.2.0.json …

IF IT FAILS
  PublishedVersionChanged → you changed what a published version compiles to:
  raise template.version in the definition and build again. Then refresh the
  golden file: STRATIGRAPH_UPDATE_GOLDEN=1 ./em.sh test tests/test_build.py::test_golden_iccd
EOF
}

help_after_bump() {
  cat <<'EOF'
./em.sh after-bump

WHAT IT DOES
  The stratigraph-templates part of the datamodel chain
  (s3Dgraphy docs/DATAMODEL_PROPAGATION.md, step 11), in order:
      1. snapshot   (registry-snapshot, prints provenance and diff)
      2. validate
      3. build
  It stops at the first step that fails. At the end it lists every compiled
  scheda that differs from the last commit, and how: a NEW version, a changed
  DEFINITION digest (must not happen to a published version), a changed
  datamodel (versions / fingerprint), or provenance only (the s3dgraphy version
  and commit the snapshot was taken from). Then `git status --short` of
  registry/ and dist/.

WHAT IT DOES NOT DO
  It does not commit, push or run the tests (./em.sh test does). It does not
  raise a template.version for you, and it does not refresh the golden file
  tests/golden/iccd-us-2021.json. Since bdb09e4 the golden file leaves out
  header.datamodel and header.compiled_by, so a snapshot alone does not move it:
  it moves with a recipe change, and then STRATIGRAPH_UPDATE_GOLDEN=1 refreshes
  it (./em.sh help build).

WHEN
  After s3Dgraphy's datamodel changed — typically right after a dev release
  (s3Dgraphy: ./em.sh propagate runs this for you).

EXAMPLE
  $ ./em.sh after-bump
  ▸ 1/3 snapshot … ▸ 2/3 validate … ▸ 3/3 build …
  schede whose compiled output changed (against the last commit):
    iccd-us-2021 2.0.0  provenance only: s3dgraphy 1.6.0.dev24 → 1.6.0.dev25,
                        taken_from 066ba2f → 42ea27c  (same digest, same datamodel)
   M dist/schede/iccd-us-2021/2.0.0.json
   M registry/s3dgraphy-snapshot.json
  (measured on 2026-10-01, s3Dgraphy dev25. After a real datamodel change the
  line reads e.g. «datamodel nodes 1.6.18 → 1.6.19, digest sha256:… → sha256:…».)

IF IT FAILS
  It says which step. A validate error after a snapshot means the datamodel
  removed or renamed something a definition uses: fix the definition. A build
  PublishedVersionChanged: see ./em.sh help build. Review, then commit by hand.
EOF
}

help_info()  { echo "./em.sh info <template-id>"; echo; echo "  Passes to \`stratigraph-templates info\`: the numbers of one definition (fields,"; echo "  bindings, vocabularies). Writes nothing. Example: ./em.sh info iccd-us-2021"; echo "  If it fails: an unknown id lists nothing — see templates/ for the ids."; }
help_print() { cat <<'EOF'
./em.sh print <template-id> [--record FILE] [--lang LL] [-o OUT.pdf] [--explain-vocab]

  Passes to `stratigraph-templates print`: an A4 recto/verso PDF from the
  definition and (optionally) a record. Writes only the -o file.
  Needs WeasyPrint (installed by setup) and its system libraries
  (macOS: brew install pango). Labels of external vocabularies need the
  checkouts beside this repo (README, «The two dependencies outside…»).
  Example:
    ./em.sh print iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.pdf
  If it fails with "cannot load library 'libgobject…'": brew install pango.
EOF
}
help_form() { cat <<'EOF'
./em.sh form <template-id> [--record FILE] [--lang LL] [-o OUT.html]

  Passes to `stratigraph-templates form`: a fillable HTML form from the same
  definition. Writes only the -o file.
  Example:
    ./em.sh form iccd-us-2021 --record examples/us-3014-demo.yaml --lang it -o out/us.html
EOF
}
help_vocab() { cat <<'EOF'
./em.sh vocab [--scheme ID] [--concept IRI] [--lang LL]

  Passes to `stratigraph-templates vocab`: with no argument lists the schemes;
  with --scheme/--concept resolves a label (needs rdflib, installed by setup,
  and for ICCD/iDAI schemes the checkouts beside this repo). Writes nothing.
  Example:
    ./em.sh vocab --scheme fx-ue-definicion-es --concept 'https://example.invalid/fixture/ue-definicion-es/estrato' --lang it
EOF
}
help_cli() { echo "./em.sh cli <anything>"; echo; echo "  Runs .venv/bin/python -m stratigraph_templates.cli <anything>, unchanged:"; echo "  extract-xsd, extract-idai-field, --snapshot, --help. Example: ./em.sh cli --help"; }

help_test() {
  cat <<'EOF'
./em.sh test [pytest args…]

WHAT IT DOES
  .venv/bin/python -m pytest [args] — the whole suite by default (testpaths =
  tests). Extra arguments go to pytest as they are.

WHAT IT DOES NOT DO
  It does not snapshot or build first. Several tests compare the COMMITTED
  snapshot and dist/ with what s3Dgraphy declares today, so after a datamodel
  change they fail until ./em.sh after-bump has run.

EXAMPLE
  $ ./em.sh test -q
  200 passed in 9.81s

IF IT FAILS
  test_the_committed_snapshot_is_what_s3dgraphy_declares_today, or many errors
  at setup of the `reg` fixture → ./em.sh after-bump. test_golden_iccd after a
  recipe change → STRATIGRAPH_UPDATE_GOLDEN=1 ./em.sh test tests/test_build.py::test_golden_iccd
EOF
}

help_status() {
  cat <<'EOF'
./em.sh status

WHAT IT DOES
  Compares registry/s3dgraphy-snapshot.json with the s3Dgraphy next door
  ($STRATIGRAPH_S3DGRAPHY_SRC or ../s3Dgraphy/src), on the four datamodel files
  this repository READS (nodes, node_registry, connections, qualia — the
  visual rules and translations are none of a sheet's business):
    · s3dgraphy version and commit the snapshot was taken from;
    · the fingerprint of each, per file, via s3dgraphy.datamodel
      (api.datamodel_fingerprint / datamodel_differences);
    · each difference named (`nodes 1.6.18 vs 1.6.19`);
    · `git status --short` of registry/ and dist/.

WHAT IT DOES NOT DO
  It writes nothing and runs no compile.

EXAMPLE
  $ ./em.sh status
  snapshot   s3dgraphy 1.6.0.dev25 · taken from 066ba2f (clean)
  s3Dgraphy  1.6.0.dev25 · ../s3Dgraphy (42ea27c)
  datamodel  aligned on nodes, node_registry, connections, qualia

IF IT SAYS "differs"
  ./em.sh after-bump.  If s3Dgraphy is not found: set STRATIGRAPH_S3DGRAPHY_SRC.
EOF
}

do_help() {
  local c="${1:-}"
  case "$c" in
    "") help_overview ;;
    setup|snapshot|validate|build|info|print|form|vocab|cli|test|status) "help_$c" ;;
    after-bump) help_after_bump ;;
    *) die "no command '$c'. ./em.sh help lists them." ;;
  esac
}

# ── setup ─────────────────────────────────────────────────────────────────────

py_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; }

pick_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    py_ok "$PYTHON" || die "\$PYTHON=$PYTHON is not a Python >= 3.11"
    printf '%s' "$PYTHON"; return
  fi
  local c p
  for c in python3.14 python3.13 python3.12 python3.11 python3; do
    p="$(command -v "$c" 2>/dev/null || true)"
    [[ -n "$p" ]] && py_ok "$p" && { printf '%s' "$p"; return; }
  done
  die "no Python >= 3.11 found (pyproject: requires-python >= 3.11). Install one, or PYTHON=/path ./em.sh setup"
}

do_setup() {
  if [[ -x "$PY" ]] && py_ok "$PY"; then
    log "keeping .venv ($("$PY" --version 2>&1))"
  else
    [[ -d "$VENV" ]] && warn ".venv is broken (interpreter missing or < 3.11): recreating it"
    local base; base="$(pick_python)"
    log "using $base ($("$base" --version 2>&1))"
    rm -rf "$VENV"
    "$base" -m venv "$VENV"
  fi
  log "pip install -e '.[dev]'"
  "$PY" -m pip install --quiet --upgrade pip
  (cd "$ROOT" && "$PY" -m pip install --quiet -e '.[dev]')
  "${CLI[@]}" --help >/dev/null || die "the CLI does not answer after the install"
  if [[ -x "$VENV/bin/stratigraph-templates" ]]; then
    ok ".venv ready: .venv/bin/stratigraph-templates present, the CLI answers"
  else
    warn ".venv/bin/stratigraph-templates is still missing — every ./em.sh command works anyway (python -m)"
  fi
}

# ── the chain ─────────────────────────────────────────────────────────────────

REPORT=("$PY" "$ROOT/tools/em_report.py")

snapshot_provenance() { "${REPORT[@]}" provenance; }

do_snapshot() {
  need_venv
  log "registry-snapshot from $S3D_SRC"
  [[ -d "$S3D_SRC" ]] || warn "$S3D_SRC does not exist: the CLI will look for an installed s3dgraphy"
  (cd "$ROOT" && STRATIGRAPH_S3DGRAPHY_SRC="$S3D_SRC" "${CLI[@]}" registry-snapshot) || return 1
  snapshot_provenance
  if git -C "$ROOT" diff --quiet -- registry/; then
    ok "registry/ unchanged: the snapshot already said this"
  else
    git -C "$ROOT" --no-pager diff --stat -- registry/
    git -C "$ROOT" --no-pager diff -U0 -- registry/ | grep -E '^[-+] *"(snapshot_format|node_datamodel_version|connections_version|qualia_version|em_ttl_version|s3dgraphy_version|git_commit)"' || true
    warn "the snapshot changed: review the diff above (git diff registry/) before you commit"
  fi
}

do_after_bump() {
  need_venv
  log "1/3 snapshot";  do_snapshot   || die "stopped at 1/3 snapshot"
  log "2/3 validate";  (cd "$ROOT" && "${CLI[@]}" validate) || die "stopped at 2/3 validate (nothing built)"
  log "3/3 build";     (cd "$ROOT" && "${CLI[@]}" build)    || die "stopped at 3/3 build"
  echo
  echo "schede whose compiled output changed (against the last commit):"
  "${REPORT[@]}" changed
  echo
  git -C "$ROOT" status --short -- registry/ dist/ || true
  ok "after-bump done — nothing committed. Review: git diff registry/ dist/"
  echo "  next: ./em.sh test. The golden file (tests/golden/iccd-us-2021.json) has no provenance:"
  echo "  only a changed RECIPE moves it, and a published version's recipe must not change."
}

# ── status ────────────────────────────────────────────────────────────────────

do_status() {
  need_venv
  echo "snapshot   registry/s3dgraphy-snapshot.json"
  snapshot_provenance
  local s3d_root; s3d_root="$(cd "$S3D_SRC/.." 2>/dev/null && pwd || true)"
  if [[ -n "$s3d_root" ]] && git -C "$s3d_root" rev-parse --git-dir >/dev/null 2>&1; then
    echo "s3Dgraphy  $s3d_root ($(git -C "$s3d_root" rev-parse --short HEAD), $(git -C "$s3d_root" branch --show-current))"
  fi
  local rc=0
  "${REPORT[@]}" status "$S3D_SRC" || rc=$?
  echo "git        $(git -C "$ROOT" status --short -- registry/ dist/ | wc -l | tr -d ' ') changed file(s) under registry/ dist/"
  return $rc
}

# ── dispatch ──────────────────────────────────────────────────────────────────

cmd="${1:-help}"; shift || true
case "$cmd" in
  help|-h|--help) do_help "${1:-}" ;;
  setup)      do_setup ;;
  snapshot)   do_snapshot ;;
  validate)   need_venv; cd "$ROOT"; "${CLI[@]}" validate "$@" ;;
  build)      need_venv; cd "$ROOT"; "${CLI[@]}" build "$@" ;;
  after-bump) do_after_bump ;;
  info|print|form|vocab)
              need_venv; cd "$ROOT"; "${CLI[@]}" "$cmd" "$@" ;;
  cli)        need_venv; cd "$ROOT"; "${CLI[@]}" "$@" ;;
  test)       need_venv; cd "$ROOT"; "$PY" -m pytest "$@" ;;
  status)     do_status ;;
  *)          echo "unknown command '$cmd'" >&2; echo >&2; help_overview >&2; exit 2 ;;
esac
