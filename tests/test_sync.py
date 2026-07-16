"""sync 域测试：导出、导入、去重。"""
import json
import tempfile
from pathlib import Path

from linkkeep.core.models import Bookmark
from linkkeep.core.store import Store
from linkkeep.sync.dedup import dedup_by_url, normalize_url
from linkkeep.sync.exporter import export_to_json, export_to_markdown
from linkkeep.sync.importer import import_from_json


def test_normalize_url_strips_slash_and_lowercases():
    assert normalize_url("HTTPS://Example.com/") == "https://example.com"


def test_dedup_by_url_skips_existing():
    existing = [Bookmark(id=1, url="https://a.com")]
    incoming = [Bookmark(id=2, url="https://a.com"), Bookmark(id=3, url="https://b.com")]
    fresh = dedup_by_url(existing, incoming)
    assert len(fresh) == 1
    assert fresh[0].url == "https://b.com"


def test_export_to_json_round_trip():
    bookmarks = [Bookmark(id=1, url="https://a.com", title="A", tags=["ref"])]
    d = tempfile.mkdtemp()
    out = export_to_json(bookmarks, str(Path(d) / "export.json"))
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    assert data[0]["url"] == "https://a.com"


def test_export_to_markdown_groups_by_tag():
    bookmarks = [
        Bookmark(id=1, url="https://a.com", title="A", tags=["ref"]),
        Bookmark(id=2, url="https://b.com", title="B", tags=[]),
    ]
    d = tempfile.mkdtemp()
    out = export_to_markdown(bookmarks, str(Path(d) / "export.md"))
    text = Path(out).read_text(encoding="utf-8")
    assert "## ref" in text
    assert "## (无标签)" in text


def test_import_from_json_dedup_and_merge():
    d = tempfile.mkdtemp()
    store = Store(path=Path(d) / "bookmarks.json")
    store.add(url="https://a.com", title="A")

    import_file = Path(d) / "incoming.json"
    import_file.write_text(json.dumps([
        {"id": 99, "url": "https://a.com", "title": "dup"},
        {"id": 100, "url": "https://c.com", "title": "C"},
    ]), encoding="utf-8")

    added = import_from_json(store, str(import_file))
    assert added == 1
    urls = {b.url for b in store.load()}
    assert urls == {"https://a.com", "https://c.com"}
