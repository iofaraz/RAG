import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph import schema  # noqa: E402


@pytest.fixture(scope="session")
def csv_path():
    p = Path(os.getenv("GRAPH_TEST_CSV", schema.DEFAULT_CSV))
    if not p.exists():
        pytest.skip(f"CSV not found: {p} (set GRAPH_TEST_CSV)")
    return p


@pytest.fixture(scope="session")
def df(csv_path):
    from graph.graph_builder import load_foods
    return load_foods(csv_path)
