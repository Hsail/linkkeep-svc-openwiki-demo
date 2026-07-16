"""书签持久化：把 Bookmark 列表读写到本地 JSON 文件。"""
import json
import os
from pathlib import Path
from typing import List

from .models import Bookmark


def _home() -> Path:
    root = os.environ.get("LINKKEEP_HOME", str(Path.home() / ".linkkeep"))
    return Path(root)


class Store:
    """基于 JSON 文件的书签仓库，负责加载、保存与自增 ID 分配。

    api / cli / sync 三个域都通过这一个 Store 读写同一份数据，
    是 linkkeep-svc 四域共享的唯一数据地基。
    """

    def __init__(self, path: Path = None) -> None:
        self.path = path or (_home() / "bookmarks.json")

    def _ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> List[Bookmark]:
        self._ensure()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [Bookmark.from_dict(item) for item in raw]

    def save(self, bookmarks: List[Bookmark]) -> None:
        self._ensure()
        data = [b.to_dict() for b in bookmarks]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def next_id(self, bookmarks: List[Bookmark]) -> int:
        return (max((b.id for b in bookmarks), default=0)) + 1

    def add(self, url: str, title: str = "", tags: List[str] = None) -> Bookmark:
        bookmarks = self.load()
        bm = Bookmark(id=self.next_id(bookmarks), url=url, title=title, tags=tags or [])
        bookmarks.append(bm)
        self.save(bookmarks)
        return bm

    def remove(self, bookmark_id: int) -> bool:
        bookmarks = self.load()
        kept = [b for b in bookmarks if b.id != bookmark_id]
        if len(kept) == len(bookmarks):
            return False
        self.save(kept)
        return True
