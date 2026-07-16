"""书签数据模型。"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List


@dataclass
class Bookmark:
    """单条书签：一个 URL 加上标题、若干标签与创建时间。"""

    id: int
    url: str
    title: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(
            id=data["id"],
            url=data["url"],
            title=data.get("title", ""),
            tags=list(data.get("tags", [])),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    def matches_tag(self, tag: str) -> bool:
        return tag in self.tags

    def matches_any_tag(self, tags: List[str]) -> bool:
        """任一标签命中即返回 True，供未来"多标签筛选"用例复用（当前 CLI/API 只做单标签过滤）。"""
        return any(t in self.tags for t in tags)

    def matches_all_tags(self, tags: List[str]) -> bool:
        """km-9 复核用改动：全部标签都命中才返回 True（AND 语义，对照 matches_any_tag 的 OR 语义）。"""
        return all(t in self.tags for t in tags)
