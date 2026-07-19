"""core 域测试：模型与持久化。"""
import tempfile
from pathlib import Path

from linkkeep.core.models import Bookmark
from linkkeep.core.store import Store
from linkkeep.core.tags import normalize_tag, tag_counts, tag_overlap


def _tmp_store() -> Store:
    d = tempfile.mkdtemp()
    return Store(path=Path(d) / "bookmarks.json")


def test_bookmark_round_trip():
    bm = Bookmark(id=1, url="https://example.com", title="Example", tags=["ref"])
    d = bm.to_dict()
    bm2 = Bookmark.from_dict(d)
    assert bm2.url == bm.url
    assert bm2.tags == ["ref"]


def test_store_add_and_load():
    store = _tmp_store()
    bm = store.add(url="https://a.com", title="A", tags=["x"])
    assert bm.id == 1
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].url == "https://a.com"


def test_store_next_id_increments():
    store = _tmp_store()
    store.add(url="https://a.com")
    store.add(url="https://b.com")
    bookmarks = store.load()
    assert store.next_id(bookmarks) == 3


def test_store_remove():
    store = _tmp_store()
    bm = store.add(url="https://a.com")
    assert store.remove(bm.id) is True
    assert store.remove(999) is False
    assert store.load() == []


def test_normalize_tag():
    assert normalize_tag("  Ref  ") == "ref"


def test_tag_counts():
    bookmarks = [
        Bookmark(id=1, url="https://a.com", tags=["Ref", "demo"]),
        Bookmark(id=2, url="https://b.com", tags=["ref"]),
    ]
    counts = tag_counts(bookmarks)
    assert counts["ref"] == 2
    assert counts["demo"] == 1


def test_tag_overlap():
    """km-11 案例3 真实代码改动：验证 tag_overlap 大小写不敏感、AND 语义。"""
    bookmarks = [
        Bookmark(id=1, url="https://a.com", tags=["Ref", "demo"]),
        Bookmark(id=2, url="https://b.com", tags=["ref"]),
        Bookmark(id=3, url="https://c.com", tags=["demo"]),
    ]
    assert tag_overlap(bookmarks, "ref", "Demo") == 1
    assert tag_overlap(bookmarks, "ref", "ref") == 2
    assert tag_overlap(bookmarks, "nope", "demo") == 0
