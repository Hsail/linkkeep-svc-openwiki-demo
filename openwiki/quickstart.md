# linkkeep-svc — OpenWiki Quickstart

linkkeep-svc is a multi-domain **bookmark management service** written in Python (3.9+). It organizes a simple bookmark workflow into four cleanly separated domains — core data models, a FastAPI REST API, a command-line interface, and a sync layer for import/export with deduplication.

The project was built as an OpenWiki Stage 2 documentation case study: a small but realistic service that exercises cross-domain dependencies, shared data models, and distinct interfaces over the same storage layer.

## Four Domains at a Glance

| Domain | Location | Role |
|--------|----------|------|
| **core** | `linkkeep/core/` | Data foundation: `Bookmark` model, `Store` (JSON persistence), tag normalization & statistics |
| **api** | `linkkeep/api/` | REST interface via FastAPI: CRUD + tag overview endpoints |
| **cli** | `linkkeep/cli/` | Command-line entry: `add / list / remove / count / export / import / top-tags` |
| **sync** | `linkkeep/sync/` | Export (JSON/Markdown), import with URL-based dedup, dedup statistics |

All three interface domains (api, cli, sync) depend on **core** for the shared `Bookmark` dataclass and `Store` persistence layer. The CLI additionally depends on **sync** for its `export` and `import` subcommands.

→ See [architecture.md](architecture.md) for the dependency graph and design rationale.
→ See [domain-guide.md](domain-guide.md) for per-domain API reference and business rules.

## Install

```bash
pip install -e ".[dev]"
```

Dependencies: `fastapi`, `pydantic` (runtime); `pytest`, `httpx` (dev).

## Usage

### CLI

```bash
linkkeep add https://example.com --title "示例站点" --tag ref --tag demo
linkkeep list
linkkeep list --tag ref
linkkeep count --tag ref
linkkeep top-tags --n 5
linkkeep export --format markdown --out backup.md
linkkeep import other-device-export.json
```

Subcommands: `add`, `list`, `remove <id>`, `count`, `export`, `import`, `top-tags`.

### REST API

```bash
uvicorn linkkeep.api.app:app --reload
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/bookmarks?tag=<tag>` | List bookmarks, optional tag filter |
| POST | `/bookmarks` | Create a bookmark (body: `{url, title, tags}`) |
| DELETE | `/bookmarks/{id}` | Delete by ID (404 if not found) |
| GET | `/bookmarks/tags` | Tag counts (bookmark count per tag) |

## Data Storage

Bookmarks are persisted as a JSON array at `~/.linkkeep/bookmarks.json` by default. Override the storage directory with the `LINKKEEP_HOME` environment variable:

```bash
LINKKEEP_HOME=/data/linkkeep linkkeep list
```

The `Store` class (`linkkeep/core/store.py`) handles load/save, auto-incrementing IDs, and directory/file creation. The API layer reuses a singleton `Store` instance per process via `linkkeep/api/deps.py`.

## Testing

```bash
pytest tests/ -v
```

Three test modules, one per interface domain:

- `tests/test_core.py` — Bookmark round-trip, Store add/load/remove/next_id, tag normalization & counts
- `tests/test_api.py` — FastAPI TestClient: health, create+list, 404 on delete, tag counts endpoint
- `tests/test_sync.py` — URL normalization, dedup logic, JSON/Markdown export, import merge with dedup

All tests use temp directories for isolation; no shared state.

## CI / OpenWiki Automation

`.github/workflows/openwiki-update.yml` runs a daily scheduled (08:00 UTC) OpenWiki documentation refresh. It installs OpenWiki via npm, runs `openwiki code --update --print`, and opens a pull request with regenerated docs. The workflow uses OpenRouter (GLM model) and requires `OPENROUTER_API_KEY`. It also optionally enables LangSmith tracing (`LANGSMITH_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_TRACING_V2`).

## Key Design Decisions

- **One shared data model**: `Bookmark` is a plain `@dataclass` (not a Pydantic model). The API layer wraps it in Pydantic `BookmarkIn`/`BookmarkOut` schemas for validation/serialization, keeping core free of web-framework dependencies.
- **JSON file as database**: No external database. `Store` reads/writes the entire bookmark list as a JSON array on every operation. Simple, portable, fine for the project's scope.
- **Tag normalization**: Tags are lowercased and stripped in `core/tags.py`. `"Ref"` and `"ref"` are treated as the same tag in counts and filtering.
- **URL-based dedup**: Import merges by normalized URL (trailing slash removed, lowercased). Existing bookmarks take priority; incoming duplicates are silently dropped.

## Backlog

- **`top-tags` CLI subcommand not in README**: The `top-tags` subcommand (added in the latest commit) is implemented in `cli/commands.py` and wired in `cli/main.py` but not documented in `README.md`. Reason: README is slightly stale relative to the latest commit.
- **`BookmarkListOut` schema unused**: `api/schemas.py` defines `BookmarkListOut` (wrapper with `total` + `items`) but `routes.py` returns a plain `List[BookmarkOut]`. Reason: schema prepared but endpoint not yet updated to use it.
- **`dedup_stats` not exposed via CLI or API**: `sync/dedup.py` provides `dedup_stats()` for pre-import preview, but no CLI/API surface calls it yet. Reason: utility added for future use.
- **`count_by_tag` in exporter vs `tag_counts` in core**: Two overlapping tag-counting functions exist (`sync/exporter.count_by_tag` and `core/tags.tag_counts`). Reason: exporter's version handles `_untagged` grouping differently and is local to export formatting.
- **`rarest_tags` not exposed via CLI or API**: `core/tags.rarest_tags()` returns the least-common tags to help find orphan/misspelled tags, but no CLI subcommand or API endpoint calls it yet. Reason: utility added for future use.
