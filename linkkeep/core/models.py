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
