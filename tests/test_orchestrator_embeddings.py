import os
import sys
import pathlib
import pytest
from unittest.mock import AsyncMock

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from functions.bp_embeddings import embed_chunk_activity, persist_snippet_activity


@pytest.mark.asyncio
async def test_embed_chunk_activity_mocked(monkeypatch):
    os.environ["DISABLE_OPENAI"] = "1"
    out = await embed_chunk_activity({"text": "hello"})
    assert out == [0.0, 1.0, 0.0]


@pytest.mark.asyncio
async def test_persist_snippet_activity_success(monkeypatch):
    from data import cosmos_ops

    async def fake_upsert(name, project_id, code, embedding):
        return {"id": name}

    monkeypatch.setattr(cosmos_ops, "upsert_document", AsyncMock(side_effect=fake_upsert))

    res = await persist_snippet_activity({"name": "n", "projectId": "p", "code": "x", "embedding": [1.0]})
    assert res["ok"] is True
