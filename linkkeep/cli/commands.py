"""子命令处理函数：add / list / remove / count / export / import / top-tags。"""
import argparse
from typing import List

from ..core.models import Bookmark
from ..core.store import Store
from ..core.tags import tag_counts, top_tags
from ..sync.exporter import export_to_json, export_to_markdown
from ..sync.importer import import_from_json


def cmd_add(store: Store, args: argparse.Namespace) -> None:
    bm = store.add(url=args.url, title=args.title or "", tags=args.tag or [])
    print(f"added #{bm.id}: {bm.url}")


def cmd_list(store: Store, args: argparse.Namespace) -> None:
    bookmarks: List[Bookmark] = store.load()
    if args.tag:
        bookmarks = [b for b in bookmarks if b.matches_tag(args.tag)]
    if not bookmarks:
        print("(no bookmarks)")
        return
    for b in bookmarks:
        tags = ",".join(b.tags)
        print(f"#{b.id}  {b.url}  [{b.title}]  ({tags})")


def cmd_remove(store: Store, args: argparse.Namespace) -> None:
    ok = store.remove(args.id)
    if not ok:
        print(f"no bookmark with id {args.id}")
        return
    print(f"removed #{args.id}")


def cmd_count(store: Store, args: argparse.Namespace) -> None:
    bookmarks = store.load()
    if args.tag:
        bookmarks = [b for b in bookmarks if b.matches_tag(args.tag)]
    print(len(bookmarks))


def cmd_export(store: Store, args: argparse.Namespace) -> None:
    bookmarks = store.load()
    if args.format == "markdown":
        path = export_to_markdown(bookmarks, args.out)
    else:
        path = export_to_json(bookmarks, args.out)
    print(f"exported {len(bookmarks)} bookmarks -> {path}")


def cmd_import(store: Store, args: argparse.Namespace) -> None:
    added = import_from_json(store, args.file)
    print(f"imported {added} new bookmarks (duplicates skipped)")


def cmd_top_tags(store: Store, args: argparse.Namespace) -> None:
    bookmarks = store.load()
    for tag, count in top_tags(tag_counts(bookmarks), n=args.n):
        print(f"{tag}\t{count}")
