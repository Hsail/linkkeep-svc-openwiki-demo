---
type: Reference
title: linkkeep-svc Domain Guide
description: Per-domain reference for key types, functions, and business rules.
resource: /linkkeep/core/models.py
tags: [reference, domains, business-rules]
---

# Domain Guide

This page is a per-domain reference for the key types, functions, and business rules in linkkeep-svc. Use it to quickly find where a behavior lives and why.

---

## Core Domain (`linkkeep/core/`)

The data foundation shared by all other domains. No dependencies on api, cli, or sync.

### `models.py` — Bookmark Dataclass

```python
@dataclass
class Bookmark:
    id: int
    url: str
    title: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

- **`to_dict()`**: Serializes to a plain dict via `dataclasses.asdict()`.
- **`from_dict(data)`**: Reconstructs from a dict. Missing `title`/`tags`/`created_at` get safe defaults; `id` and `url` are required (will raise `KeyError` if absent).
- **`matches_tag(tag)`**: Returns `True` if `tag` is in `self.tags`. Note: this is a **case-sensitive** check. The CLI and API apply normalization before calling this, but the method itself does not normalize.
- **`matches_any_tag(tags)`**: Returns `True` if any tag in the provided list is in `self.tags` (OR semantics). Like `matches_tag`, the check is **case-sensitive**. Added for future multi-tag filtering use cases; the current CLI and API only perform single-tag filtering.
- **`matches_all_tags(tags)`**: Returns `True` only if every tag in the provided list is in `self.tags` (AND semantics, complementing `matches_any_tag`). Like the other match methods, the check is **case-sensitive**. Added as a sentinel/idempotency helper for cross-run re-verification (km-9); not yet called by CLI or API.

### `store.py` — JSON File Persistence

| Method | Behavior |
|--------|----------|
| `Store(path=None)` | Resolves path from `LINKKEEP_HOME` env or `~/.linkkeep/bookmarks.json` |
| `_ensure()` | Creates parent dir + empty `[]` file if missing |
| `load()` | Reads JSON array, returns `List[Bookmark]` |
| `save(bookmarks)` | Writes `List[Bookmark]` as JSON (indent=2, ensure_ascii=False) |
| `next_id(bookmarks)` | `max(b.id) + 1`, or `1` if list is empty |
| `add(url, title, tags)` | Loads, creates `Bookmark` with next ID, appends, saves, returns it |
| `remove(bookmark_id)` | Loads, filters out by ID, saves. Returns `False` if ID not found |
| `count()` | `len(self.load())` — convenience wrapper |
| `clear()` | Saves an empty list `[]` to the JSON file, removing all bookmarks. Dangerous operation intended for test/reset scenarios. |

**Business rule — ID allocation**: IDs are assigned as `max(existing_ids) + 1`. If all bookmarks are deleted and new ones added, IDs do not reset to 1 — they continue from the historical max. Deleted IDs are not reused. `clear()` empties the store entirely (saves `[]`), which resets the ID counter back to 1 on the next `add()`.

### `tags.py` — Tag Normalization & Statistics

| Function | Behavior |
|----------|----------|
| `normalize_tag(tag)` | `tag.strip().lower()` — eliminates case/whitespace variants |
| `normalize_tags(tags)` | Normalizes each, deduplicates, preserves first-seen order |
| `tag_counts(bookmarks)` | Returns `Counter` of normalized tags across all bookmarks' tag lists |
| `top_tags(counts, n=5)` | Returns `counts.most_common(n)` — top N `(tag, count)` pairs |
| `rarest_tags(counts, n=5)` | Returns the N least-common `(tag, count)` pairs (reversed ascending). Helps find orphan or misspelled tags. Not yet exposed via CLI or API. |
| `tag_overlap(bookmarks, tag_a, tag_b)` | Counts bookmarks that have **both** `tag_a` and `tag_b` (AND semantics). Tags are normalized (case-insensitive) before comparison. Powers the CLI `tag-overlap` subcommand. |

**Business rule — tag normalization**: Tags are normalized to lowercase + stripped. `"Ref"`, `" ref "`, and `"REF"` all collapse to `"ref"`. However, `normalize_tag` is applied in `tag_counts()` and `top_tags()` but is **not** automatically applied when a bookmark is added via `Store.add()`. Tags are stored as-is in the JSON file. This means the stored format may contain un-normalized tags if added directly through `Store.add()` without pre-normalization.

---

## API Domain (`linkkeep/api/`)

FastAPI REST layer. Exposes core Store operations over HTTP.

### `app.py` — Application Assembly

- Creates `FastAPI(title="linkkeep-svc", version="0.2.0")`.
- Includes the router from `routes.py`.
- Adds a `/health` endpoint returning `{"status": "ok"}`.

### `deps.py` — Dependency Injection

- `get_store()` returns a module-level singleton `_store_singleton`.
- First call creates `Store()` (resolving `LINKKEEP_HOME` at that point).
- Subsequent calls return the same instance.
- `reset_store_singleton()` sets `_store_singleton` back to `None`, forcing the next `get_store()` call to rebuild the `Store`. Intended for test isolation so that test cases don't share singleton state.
- Tests currently override `deps._store_singleton` directly with a temp-directory `Store`; `reset_store_singleton()` is available as a cleaner alternative.

### `schemas.py` — Pydantic Models

| Model | Purpose | Fields |
|-------|---------|--------|
| `BookmarkIn` | POST request body | `url: str`, `title: str = ""`, `tags: List[str] = []` |
| `BookmarkOut` | Response shape | `id`, `url`, `title`, `tags`, `created_at` |
| `TagCount` | Tag stats response | `tag: str`, `count: int` |
| `BookmarkListOut` | List wrapper (unused) | `total: int`, `items: List[BookmarkOut]` |

**Note**: `BookmarkListOut` is defined but not yet used by any route. `GET /bookmarks` returns `List[BookmarkOut]` directly.

### `routes.py` — REST Endpoints

All routes are prefixed with `/bookmarks`.

| Method | Path | Handler | Behavior |
|--------|------|---------|----------|
| GET | `/bookmarks` | `list_bookmarks` | Optional `?tag=` filter via `Bookmark.matches_tag()` |
| POST | `/bookmarks` | `create_bookmark` | Calls `store.add()`, returns 201 with `BookmarkOut` |
| DELETE | `/bookmarks/{id}` | `delete_bookmark` | Returns 204 on success, 404 if ID not found |
| GET | `/bookmarks/tags` | `list_tag_counts` | Returns `List[TagCount]` sorted by count desc |

**Note**: The tag filter on `GET /bookmarks` uses `Bookmark.matches_tag()` which is case-sensitive. If a client passes `?tag=Ref` but bookmarks store `ref`, they won't match. Consider normalizing the query parameter in a future change.

---

## CLI Domain (`linkkeep/cli/`)

Argparse-based command-line interface. Entry point registered as `linkkeep` console script in `pyproject.toml`.

### `main.py` — Parser & Entry Point

- `build_parser()` creates subparsers for each subcommand, each with `set_defaults(func=handler)`.
- `main(argv=None)` parses args, creates `Store()`, calls `args.func(store, args)`.
- Registered as `linkkeep = "linkkeep.cli.main:main"` in `pyproject.toml`.

### `commands.py` — Subcommand Handlers

| Handler | Subcommand | Behavior |
|---------|------------|----------|
| `cmd_add` | `add <url> [--title] [--tag ...]` | Creates bookmark, prints `added #N: <url>` |
| `cmd_list` | `list [--tag]` | Prints `#id  url  [title]  (tag,tag)` per line |
| `cmd_remove` | `remove <id>` | Deletes by ID, prints confirmation or error |
| `cmd_count` | `count [--tag]` | Prints integer count, optionally filtered by tag |
| `cmd_export` | `export --format <json\|markdown> --out <path>` | Delegates to `sync.exporter` |
| `cmd_import` | `import <file>` | Delegates to `sync.importer`, prints `imported N new bookmarks` |
| `cmd_top_tags` | `top-tags [--n 5]` | Prints `tag\tcount` for top N tags |
| `cmd_tag_overlap` | `tag-overlap <tag_a> <tag_b>` | Prints count of bookmarks having both tags (AND, case-insensitive) |

**Note**: The `top-tags` and `tag-overlap` subcommands are not documented in `README.md`.

---

## Sync Domain (`linkkeep/sync/`)

Export, import, and deduplication for cross-device bookmark synchronization.

### `dedup.py` — URL-Based Deduplication

| Function | Behavior |
|----------|----------|
| `normalize_url(url)` | Strips whitespace, removes trailing `/`, lowercases entire URL |
| `dedup_by_url(existing, incoming)` | Returns only incoming bookmarks whose normalized URL is not in existing. Existing wins — no overwrite. Also deduplicates within the incoming batch itself. |
| `dedup_stats(existing, incoming)` | Returns `{"incoming": N, "fresh": M, "dropped": N-M}` for pre-import preview |

**Business rule — dedup strategy**: When the same URL exists in both existing and incoming data, the **existing** bookmark is kept and the incoming one is **silently dropped** (no merge of fields like title or tags). This is a "existing wins" strategy, not a "last write wins" strategy.

**Note on `normalize_url`**: It lowercases the entire URL, including path and query string. This means `https://Example.com/Path` and `https://example.com/Path` are treated as duplicates, but `https://example.com/path` and `https://example.com/Path` are **not** (path case differs). This is a simplistic normalization — it does not handle URL-encoded characters, default ports, or www-prefix differences.

### `exporter.py` — Export

| Function | Behavior |
|----------|----------|
| `count_by_tag(bookmarks)` | Returns `Dict[str, int]`; untagged bookmarks counted under `"_untagged"` |
| `export_to_json(bookmarks, out_path)` | Writes JSON array (same format as Store's internal file). Creates parent dirs. |
| `export_to_markdown(bookmarks, out_path)` | Writes grouped Markdown: `## <tag>` sections sorted alphabetically, untagged under `## (无标签)` |

**Note**: `count_by_tag` in the exporter and `tag_counts` in core both count tags per bookmark but differ: `count_by_tag` groups untagged bookmarks into `"_untagged"` and does not normalize tags; `tag_counts` normalizes tags and ignores untagged bookmarks entirely.

### `importer.py` — Import & Merge

`import_from_json(store, in_path) -> int`:

1. Reads JSON array from `in_path`.
2. Validates every item has a `url` field (raises `ValueError` if missing).
3. Converts to `List[Bookmark]` via `Bookmark.from_dict()`.
4. Loads existing bookmarks from `store`.
5. Calls `dedup_by_url()` to find fresh (non-duplicate) bookmarks.
6. Reassigns IDs: `store.next_id(existing) + index` for each fresh bookmark.
7. Saves `existing + fresh` as the merged list.
8. Returns count of newly added bookmarks.

**Business rule — ID reassignment on import**: Incoming bookmarks' original IDs are discarded. Fresh bookmarks get new sequential IDs continuing from the existing max. This prevents ID collisions when merging data from another device.
 new sequential IDs continuing from the existing max. This prevents ID collisions when merging data from another device.
