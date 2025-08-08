import json
import sys
import pathlib
import pytest
from unittest.mock import AsyncMock

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import azure.functions as func

from function_app import http_save_snippet, http_get_snippet


class DummyReq:
    def __init__(self, method: str, url: str, body: dict | None = None, route_params: dict | None = None):
        self.method = method
        self.url = url
        self._body = json.dumps(body or {}).encode()
        self.route_params = route_params or {}

    def get_json(self):
        return json.loads(self._body.decode())

    def get_body(self):
        return self._body


@pytest.mark.asyncio
async def test_http_save_snippet_valid(monkeypatch):
    from data import cosmos_ops

    async def fake_upsert(**kwargs):
        return {"id": kwargs["name"], "ok": True}

    monkeypatch.setattr(cosmos_ops, "upsert_document", AsyncMock(side_effect=fake_upsert))

    req = DummyReq("POST", "/api/snippets", {"name": "n1", "code": "print(1)"})
    embeddings = json.dumps({"response": {"data": [{"embedding": [0.1, 0.2]}]}})

    resp: func.HttpResponse = await http_save_snippet(req, embeddings)  # type: ignore
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_http_get_snippet_not_found(monkeypatch):
    from data import cosmos_ops

    async def fake_get(name):
        return None

    monkeypatch.setattr(cosmos_ops, "get_snippet_by_id", AsyncMock(side_effect=fake_get))

    req = DummyReq("GET", "/api/snippets/x", route_params={"name": "x"})
    resp: func.HttpResponse = await http_get_snippet(req)  # type: ignore
    assert resp.status_code == 404
