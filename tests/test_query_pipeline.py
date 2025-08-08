import os
import sys
import pathlib
import json
import pytest
from unittest.mock import AsyncMock

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from routes.query import _chat_complete, http_query
from agents.tools import vector_search as vs


@pytest.mark.asyncio
async def test_query_chat_mock(monkeypatch):
    os.environ["DISABLE_OPENAI"] = "1"
    text, usage = await _chat_complete("s", "u")
    assert "mock" in usage


@pytest.mark.asyncio
async def test_vector_search_error_bubble(monkeypatch):
    async def fake_vs(query, k, project_id):
        return json.dumps({"error": "boom"})

    monkeypatch.setattr(vs, "vector_search", AsyncMock(side_effect=fake_vs))

    class R:
        def __init__(self):
            self.route_params = {}
        def get_json(self):
            return {"question": "q", "projectId": "p"}
        def get_body(self):
            return b"{}"

    resp = await http_query(R())
    assert resp.status_code == 502
