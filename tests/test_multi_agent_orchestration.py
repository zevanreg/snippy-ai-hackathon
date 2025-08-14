import os
import sys
import pathlib
import json
import pytest
from unittest.mock import AsyncMock

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from functions.bp_multi_agent import (
    load_snippet_activity,
    code_review_agent_activity,
    documentation_agent_activity,
    testing_agent_activity,
)


@pytest.mark.asyncio
async def test_load_snippet_activity_not_found(monkeypatch):
    from data import cosmos_ops

    async def fake_get(name):
        return None

    monkeypatch.setattr(cosmos_ops, "get_snippet_by_id", AsyncMock(side_effect=fake_get))
    out = await load_snippet_activity({"name": "x"})
    assert out == {}


@pytest.mark.asyncio
async def test_review_docs_tests_flow_mock(monkeypatch):
    os.environ["DISABLE_OPENAI"] = "1"

    review = await code_review_agent_activity({
        "code": "def f():\n    print(1)",
        "correlationId": "c1"
    })
    assert review["summary"]
    assert any(i["type"] == "style" for i in review["issues"])  # prints detected

    docs = await documentation_agent_activity({
        "code": "def f():\n    print(1)",
        "review": review,
        "correlationId": "c1"
    })
    assert "Code Documentation" in docs["markdown"]
    assert "Issues found:" in docs["markdown"]

    tests = await testing_agent_activity({
        "code": "def f():\n    return 1",
        "review": {"issues": [{"severity": "medium"}]},
        "correlationId": "c1"
    })
    assert tests["count"] >= 1
    # includes perf test due to medium severity
    assert any(t["name"].startswith("test_") for t in tests["tests"]) 
