"""导出：把当前书签列表写到本地文件，供跨设备同步或备份。"""
import json
from pathlib import Path
from typing import List

from ..core.models import Bookmark


def export_to_json(bookmarks: List[Bookmark], out_path: str) -> str:
    """导出为 JSON 数组（与 Store 内部落盘格式一致，可被 importer 直接读回）。"""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [b.to_dict() for b in bookmarks]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def export_to_markdown(bookmarks: List[Bookmark], out_path: str) -> str:
    """导出为按标签分组的 Markdown 清单，便于人工浏览或粘进笔记工具。"""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    by_tag: dict = {}
    untagged = []
    for b in bookmarks:
        if not b.tags:
            untagged.append(b)
            continue
        for t in b.tags:
            by_tag.setdefault(t, []).append(b)

    lines = ["# linkkeep 书签导出\n"]
    for tag in sorted(by_tag):
        lines.append(f"## {tag}\n")
        for b in by_tag[tag]:
            lines.append(f"- [{b.title or b.url}]({b.url})")
        lines.append("")
    if untagged:
        lines.append("## (无标签)\n")
        for b in untagged:
            lines.append(f"- [{b.title or b.url}]({b.url})")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
