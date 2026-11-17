"""The copy in vocabularies/ is the source, refreshed — never edited here.

MICRO-J (17 Nov 2026): em-media-role was born in this copy and had to go home
to ExtendedMatrix/vocabularies; from then on a test says when the two disagree.
Skipped when there is no sibling checkout of the source (CI of this repository
alone): the copy is then what was last synced."""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO.parent / "vocabularies"


def _sync():
    spec = importlib.util.spec_from_file_location("sync_vocabularies", REPO / "tools" / "sync_vocabularies.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_source_path_gets_the_prefix_of_the_copy_and_nothing_else_moves():
    sync = _sync()
    assert sync.copied('    path: "skos/media-role.ttl"') == '    path: "vocabularies/skos/media-role.ttl"'
    assert sync.copied("# alignments/, e `provisional`") == "# vocabularies/alignments/, e `provisional`"
    assert sync.copied("vocabularies/skos/x.ttl") == "vocabularies/skos/x.ttl"
    assert sync.copied("https://w3id.org/extendedmatrix/vocab/us-colore/") == \
        "https://w3id.org/extendedmatrix/vocab/us-colore/"


@pytest.mark.skipif(not (SOURCE / "schemes").is_dir(), reason="no sibling checkout of ExtendedMatrix/vocabularies")
def test_the_copy_is_the_source():
    diffs = _sync().differences(SOURCE)
    assert not diffs, "run tools/sync_vocabularies.py: " + ", ".join(diffs)
