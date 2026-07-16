"""API 请求/响应模型（Pydantic）。"""
from typing import List, Optional

from pydantic import BaseModel, Field


class BookmarkIn(BaseModel):
    """POST /bookmarks 的请求体。"""

    url: str
    title: str = ""
    tags: List[str] = Field(default_factory=list)


class BookmarkOut(BaseModel):
    """书签对外返回的形状，与 core.models.Bookmark 字段一一对应。"""

    id: int
    url: str
    title: str
    tags: List[str]
    created_at: str


class TagCount(BaseModel):
    tag: str
    count: int


class BookmarkListOut(BaseModel):
    """列表接口的包裹形状：带上 total，避免客户端只靠数组长度猜总数。"""

    total: int
    items: List[BookmarkOut]
