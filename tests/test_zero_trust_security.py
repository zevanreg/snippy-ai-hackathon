import sys
import pathlib
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import azure.functions as func
from routes.query import http_rbac_check


class DummyReq:
    def __init__(self):
        self.route_params = {}
    def get_json(self):
        return {}


@pytest.mark.asyncio
async def test_rbac_check_denied(monkeypatch):
    from data import cosmos_ops

    async def bad_get_container():
        raise Exception("Forbidden")

    monkeypatch.setattr(cosmos_ops, "get_container", AsyncMock(side_effect=bad_get_container))

    req = DummyReq()
    resp: func.HttpResponse = await http_rbac_check(req)  # type: ignore
    assert resp.status_code == 403
    body = json.loads(resp.get_body())
    assert body["ok"] is False


@pytest.mark.asyncio
async def test_rbac_check_ok(monkeypatch):
    from data import cosmos_ops

    class DummyContainer:
        container_link = "link"

    async def good_get_container():
        return DummyContainer()

    monkeypatch.setattr(cosmos_ops, "get_container", AsyncMock(side_effect=good_get_container))

    req = DummyReq()
    resp: func.HttpResponse = await http_rbac_check(req)  # type: ignore
    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["ok"] is True
