---
type: Architecture
title: linkkeep-svc Architecture
description: How the four domains (core, api, cli, sync) interact through a shared JSON-backed Store.
resource: /linkkeep/__init__.py
tags: [architecture, core, api, cli, sync]
---

# Architecture

## Overview

linkkeep-svc follows a **layered domain architecture** with four packages, each owning a distinct concern. Three interface domains (api, cli, sync) sit on top of a shared core domain that owns the data model and persistence.

```
                    ┌─────────────────────────────────────────┐
                    │              linkkeep.core               │
                    │  Bookmark (dataclass)  ·  Store (JSON)  │
                    │  tag normalize / counts / top_tags      │
                    └───────────────────┬─────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────┴────────┐    ┌──────────┴──────────┐    ┌────────┴────────┐
     │  linkkeep.api   │    │   linkkeep.cli      │    │  linkkeep.sync  │
     │  FastAPI REST   │    │   argparse CLI      │    │  export/import  │
     │  CRUD + tags    │    │   8 subcommands     │    │  dedup by URL   │
     └─────────────────┘    └──────────┬──────────┘    └─────────────────┘
                                       │
                                       └──────► (cli imports sync.exporter
                                                and sync.importer for its
                                                export / import subcommands)
```

## Dependency Rules

1. **core depends on nothing** within the project — only stdlib (`json`, `os`, `pathlib`, `dataclasses`, `datetime`, `collections`).
2. **api** depends on `core` (Store, tags) and external `fastapi`/`pydantic`.
3. **cli** depends on `core` (Store, tags, models) and `sync` (exporter, importer).
4. **sync** depends on `core` (Bookmark, Store) only.

This means `sync` does **not** depend on `cli` or `api`, and `api` does **not** depend on `cli` or `sync`. The dependency graph is acyclic.

## Shared Data Model

The `Bookmark` dataclass (`linkkeep/core/models.py`) is the single source of truth for what a bookmark is:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `id` | `int` | (required) | Auto-assigned by `Store.next_id()` |
| `url` | `str` | (required) | Normalized for dedup in `sync/dedup.py` |
| `title` | `str` | `""` | Optional human-readable title |
| `tags` | `List[str]` | `[]` | Normalized (lowercase, stripped) in `core/tags.py` |
| `created_at` | `str` | UTC ISO 8601 now | Set at construction, not updated |

The `to_dict()` / `from_dict()` methods provide JSON serialization. The API layer wraps this with Pydantic models (`BookmarkIn`, `BookmarkOut`, `TagCount`) for request validation and response shaping — but the canonical data shape lives in core.

## Persistence: Store

`Store` (`linkkeep/core/store.py`) is the single persistence abstraction. It:

- Resolves the data directory from `LINKKEEP_HOME` env var (defaults to `~/.linkkeep/`).
- Reads/writes `bookmarks.json` as a JSON array of bookmark dicts.
- Provides `add()`, `remove()`, `load()`, `save()`, `count()`, `next_id()`, `clear()`.
- Lazily creates the parent directory and an empty `[]` file if missing.

**Every operation is a full load → modify → save cycle.** There is no in-memory caching at the Store level. This is simple and safe for a single-process tool but means concurrent writers (e.g., CLI and API server simultaneously) could overwrite each other's changes.

## API Layer: Singleton Store

`linkkeep/api/deps.py` provides `get_store()` as a FastAPI dependency. It lazily initializes a module-level `_store_singleton` on first request, then reuses it for all subsequent requests. This avoids re-parsing `LINKKEEP_HOME` per request but still does a full file read/write per operation.

`reset_store_singleton()` clears the singleton, forcing the next `get_store()` call to rebuild the `Store`. It is intended for test isolation so that test cases don't share singleton state.

Tests override `deps._store_singleton` directly with a temp-directory `Store` for isolation; `reset_store_singleton()` is available as a cleaner alternative.

## CLI Layer: Subcommand Dispatch

`linkkeep/cli/main.py` builds an `argparse.ArgumentParser` with one subparser per subcommand. Each subparser sets `func` to a handler in `linkkeep/cli/commands.py`. At runtime, `main()` creates a `Store()` instance and calls `args.func(store, args)`. The CLI's `export` and `import` subcommands delegate to `sync.exporter` and `sync.importer` respectively.

## Sync Layer: Export / Import / Dedup

- **Export** (`sync/exporter.py`): Writes bookmarks to JSON (same format as Store's internal file) or grouped Markdown. The Markdown exporter groups by tag, sorts tags alphabetically, and places untagged bookmarks under a `(无标签)` section.
- **Import** (`sync/importer.py`): Reads a JSON file, validates each item has a `url` field, deduplicates against existing Store bookmarks by normalized URL, reassigns IDs starting from `Store.next_id()`, and saves the merged list.
- **Dedup** (`sync/dedup.py`): `normalize_url()` strips trailing slashes and lowercases. `dedup_by_url()` returns only incoming bookmarks whose URL is not already in the existing set (existing wins, no overwrite). `dedup_stats()` provides a pre-import preview count.

## Package Structure

```
linkkeep/
├── __init__.py          # Package docstring, __version__ = "0.2.0"
├── core/
│   ├── __init__.py
│   ├── models.py        # Bookmark dataclass
│   ├── store.py         # Store: JSON persistence, CRUD, ID allocation
│   └── tags.py          # normalize_tag, normalize_tags, tag_counts, top_tags, rarest_tags, tag_overlap
├── api/
│   ├── __init__.py
│   ├── app.py           # FastAPI app assembly + /health
│   ├── deps.py          # get_store() singleton, reset_store_singleton()
│   ├── routes.py        # /bookmarks CRUD + /bookmarks/tags
│   └── schemas.py       # BookmarkIn, BookmarkOut, TagCount, BookmarkListOut
├── cli/
│   ├── __init__.py
│   ├── commands.py      # cmd_add, cmd_list, cmd_remove, cmd_count,
│   │                    #   cmd_export, cmd_import, cmd_top_tags
│   └── main.py          # argparse parser + main() entry point
└── sync/
    ├── __init__.py
    ├── dedup.py          # normalize_url, dedup_by_url, dedup_stats
    ├── exporter.py       # export_to_json, export_to_markdown, count_by_tag
    └── importer.py       # import_from_json
```
