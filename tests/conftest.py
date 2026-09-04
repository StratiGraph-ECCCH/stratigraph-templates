import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from stratigraph_templates.loader import load_template  # noqa: E402
from stratigraph_templates.registry import registry  # noqa: E402
from stratigraph_templates.vocab import Vocabularies  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def reg():
    return registry()


@pytest.fixture(scope="session")
def vocab():
    return Vocabularies.load()


@pytest.fixture
def fixture_template():
    def _load(name):
        return load_template(FIXTURES / f"{name}.yaml")

    return _load
