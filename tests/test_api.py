"""api 域测试：用 FastAPI TestClient 打 REST 接口。"""
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from linkkeep.api import app as app_module
from linkkeep.api import deps
from linkkeep.core.store import Store


def _client_with_tmp_store() -> TestClient:
    d = tempfile.mkdtemp()
    deps._store_singleton = Store(path=Path(d) / "bookmarks.json")
    return TestClient(app_module.app)


def test_health():
    client = _client_with_tmp_store()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_list_bookmark():
    client = _client_with_tmp_store()
    resp = client.post("/bookmarks", json={"url": "https://example.com", "title": "示例", "tags": ["ref"]})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1

    resp2 = client.get("/bookmarks")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


def test_delete_bookmark_404():
    client = _client_with_tmp_store()
    resp = client.delete("/bookmarks/999")
    assert resp.status_code == 404


def test_tag_counts_endpoint():
    client = _client_with_tmp_store()
    client.post("/bookmarks", json={"url": "https://a.com", "tags": ["ref"]})
    client.post("/bookmarks", json={"url": "https://b.com", "tags": ["ref", "demo"]})
    resp = client.get("/bookmarks/tags")
    assert resp.status_code == 200
    counts = {row["tag"]: row["count"] for row in resp.json()}
    assert counts["ref"] == 2
    assert counts["demo"] == 1
