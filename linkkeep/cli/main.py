"""命令行入口：解析子命令并驱动 Store / sync 模块完成增删查改与导入导出。"""
import argparse
from typing import List

from ..core.store import Store
from . import commands as c


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="linkkeep", description="linkkeep-svc 命令行入口")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增一条书签")
    p_add.add_argument("url")
    p_add.add_argument("--title", default="")
    p_add.add_argument("--tag", action="append", help="可重复，添加多个标签")
    p_add.set_defaults(func=c.cmd_add)

    p_list = sub.add_parser("list", help="列出书签，可按标签过滤")
    p_list.add_argument("--tag", default=None)
    p_list.set_defaults(func=c.cmd_list)

    p_remove = sub.add_parser("remove", help="按 ID 删除书签")
    p_remove.add_argument("id", type=int)
    p_remove.set_defaults(func=c.cmd_remove)

    p_count = sub.add_parser("count", help="统计书签数量，可按标签过滤")
    p_count.add_argument("--tag", default=None)
    p_count.set_defaults(func=c.cmd_count)

    p_export = sub.add_parser("export", help="导出全部书签到本地文件（json/markdown）")
    p_export.add_argument("--format", choices=["json", "markdown"], default="json")
    p_export.add_argument("--out", required=True)
    p_export.set_defaults(func=c.cmd_export)

    p_import = sub.add_parser("import", help="从 json 文件导入书签，按 url 去重")
    p_import.add_argument("file")
    p_import.set_defaults(func=c.cmd_import)

    p_overlap = sub.add_parser("tag-overlap", help="统计同时带有两个标签的书签数量")
    p_overlap.add_argument("tag_a")
    p_overlap.add_argument("tag_b")
    p_overlap.set_defaults(func=c.cmd_tag_overlap)

    return parser


def main(argv: List[str] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store()
    args.func(store, args)


if __name__ == "__main__":
    main()
