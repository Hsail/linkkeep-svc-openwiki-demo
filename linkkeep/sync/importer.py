"""导入：从一个 JSON 文件读回书签、去重后合并进当前 Store。"""
import json
from pathlib import Path

from ..core.models import Bookmark
from ..core.store import Store
from .dedup import dedup_by_url


def import_from_json(store: Store, in_path: str) -> int:
    """把 in_path 里的书签合并进 store，按 URL 去重，返回真正新增的条数。"""
    raw = json.loads(Path(in_path).read_text(encoding="utf-8"))
    for item in raw:
        if "url" not in item:
            raise ValueError(f"导入条目缺少必需字段 url：{item!r}")
    incoming = [Bookmark.from_dict(item) for item in raw]

    existing = store.load()
    fresh = dedup_by_url(existing, incoming)

    if not fresh:
        return 0

    next_id = store.next_id(existing)
    for i, b in enumerate(fresh):
        b.id = next_id + i

    store.save(existing + fresh)
    return len(fresh)
