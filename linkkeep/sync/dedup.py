"""去重：按 URL 判定重复书签，供 importer 在合并两份数据时使用。"""
from typing import List

from ..core.models import Bookmark


def normalize_url(url: str) -> str:
    """去掉末尾斜杠、统一小写 scheme+host，避免同一地址因大小写/斜杠被判成两条。"""
    u = url.strip()
    if u.endswith("/"):
        u = u[:-1]
    return u.lower()


def dedup_by_url(existing: List[Bookmark], incoming: List[Bookmark]) -> List[Bookmark]:
    """从 incoming 里筛出 existing 尚未收录的书签（按标准化 URL 判重）。

    合并策略：existing 优先，incoming 中与 existing 重复的条目被丢弃、不覆盖。
    """
    existing_urls = {normalize_url(b.url) for b in existing}
    fresh = []
    seen_in_batch = set()
    for b in incoming:
        key = normalize_url(b.url)
        if key in existing_urls or key in seen_in_batch:
            continue
        seen_in_batch.add(key)
        fresh.append(b)
    return fresh


def dedup_stats(existing: List[Bookmark], incoming: List[Bookmark]) -> dict:
    """导入前预览：incoming 里有多少条会被判重丢弃、多少条会真正新增。"""
    fresh = dedup_by_url(existing, incoming)
    return {"incoming": len(incoming), "fresh": len(fresh), "dropped": len(incoming) - len(fresh)}
