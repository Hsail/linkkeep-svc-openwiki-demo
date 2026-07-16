"""标签规范化与统计工具，被 api（校验入参）与 cli（list --tag 过滤）复用。"""
from collections import Counter
from typing import Iterable, List

from .models import Bookmark


def normalize_tag(tag: str) -> str:
    """标签统一小写、去首尾空白，避免 "Ref" 与 "ref" 被当成两个标签。"""
    return tag.strip().lower()


def normalize_tags(tags: Iterable[str]) -> List[str]:
    seen = []
    for t in tags:
        nt = normalize_tag(t)
        if nt and nt not in seen:
            seen.append(nt)
    return seen


def tag_counts(bookmarks: Iterable[Bookmark]) -> Counter:
    """统计每个标签下有多少条书签，供 cli/api 的标签概览使用。"""
    counter: Counter = Counter()
    for b in bookmarks:
        for t in b.tags:
            counter[normalize_tag(t)] += 1
    return counter


def top_tags(counts: Counter, n: int = 5) -> List[tuple]:
    """从 tag_counts 结果里取出现次数最高的前 n 个标签，供 CLI 概览命令使用。"""
    return counts.most_common(n)


def rarest_tags(counts: Counter, n: int = 5) -> List[tuple]:
    """取出现次数最少的前 n 个标签，供排查"可能打错字的孤儿标签"用。"""
    return counts.most_common()[-n:][::-1] if counts else []
