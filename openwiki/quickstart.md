---
type: Project
title: linkkeep-svc Quickstart
description: Entry point for linkkeep-svc — a four-domain Python bookmark service. Install, CLI/REST usage, and the non-obvious storage and delegation behaviors that most affect safe changes.
tags: [linkkeep, bookmark-management, python, fastapi, cli]
verified:
  - by: openwiki/0.7.2
    at: 2026-10-26T14:47:50.406Z
sources:
  - id: openwiki-source-6d4b4e707b8d60b6ccfa3425
    resource: repo://.github/workflows/openwiki-update.yml
  - id: openwiki-source-38784abca709308d4f822ad5
    resource: repo://linkkeep/api/app.py
  - id: openwiki-source-01a7c89607c91e477e3d0204
    resource: repo://linkkeep/api/deps.py
  - id: openwiki-source-7f8d521aafaf274354bb67ba
    resource: repo://linkkeep/api/routes.py
  - id: openwiki-source-55669d908fc4066add253a2c
    resource: repo://linkkeep/cli/commands.py
  - id: openwiki-source-e466342d4d62ff6a08d8b1ce
    resource: repo://linkkeep/cli/main.py
  - id: openwiki-source-15f5c3c3f48f6c28d3523804
    resource: repo://linkkeep/core/models.py
  - id: openwiki-source-b953bc233bb1a125beed5f1a
    resource: repo://linkkeep/core/store.py
  - id: openwiki-source-c579e5324095b231df2eba7f
    resource: repo://linkkeep/core/tags.py
  - id: openwiki-source-25b341ad09159a35b9816d97
    resource: repo://linkkeep/sync/dedup.py
  - id: openwiki-source-b881e990318f9161a3f1e489
    resource: repo://linkkeep/sync/importer.py
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-11519246eac934485315b3cb
    resource: repo://tests/test_api.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
  - id: openwiki-source-64e6e88ec5734d86bc525361
    resource: repo://tests/test_sync.py
generated: { by: "openwiki/0.7.2", at: "2026-10-26T14:47:50.406Z" }
---

# linkkeep-svc — Quickstart

linkkeep-svc is a multi-domain **bookmark management service** written in Python (3.9+). It splits a simple bookmark workflow into four cleanly separated domains — core data models, a FastAPI REST API, a command-line interface, and a sync layer for import/export with deduplication.

## Four Domains at a Glance

| Domain | Location | Role |
|--------|----------|------|
| **core** | `linkkeep/core/` | Data foundation: `Bookmark` model, `Store` (JSON persistence), tag normalization & statistics |
| **api** | `linkkeep/api/` | REST interface via FastAPI: bookmark CRUD + tag overview endpoints |
| **cli** | `linkkeep/cli/` | Command-line entry: `add / list / remove / count / export / import / tag-overlap` |
| **sync** | `linkkeep/sync/` | Export (JSON/Markdown), import with URL-based dedup, dedup statistics |

All three interface domains (api, cli, sync) depend on **core** for the shared `Bookmark` dataclass and `Store` persistence layer. The CLI additionally depends on **sync**: its `export` and `import` subcommands delegate to `sync.exporter` and `sync.importer` rather than implementing file logic themselves. This is the only cross-interface edge; the dependency graph is otherwise acyclic.

→ For the dependency graph and design rationale, see [architecture.md](architecture.md).
→ For per-domain API reference and business rules, see [domain-guide.md](domain-guide.md).

## Install

```bash
pip install -e ".[dev]"
```

Runtime dependencies: `fastapi`, `pydantic`. Dev dependencies: `pytest`, `httpx`. The `linkkeep` console script is registered in `pyproject.toml` as `linkkeep = "linkkeep.cli.main:main"`.

## Usage

### CLI

```bash
linkkeep add https://example.com --title "Example" --tag ref --tag demo
linkkeep list
linkkeep list --tag ref
linkkeep count --tag ref
linkkeep tag-overlap ref demo
linkkeep export --format markdown --out backup.md
linkkeep import other-device-export.json
```

**Wired subcommands** (registered in `cli/main.py` `build_parser()`): `add`, `list`, `remove <id>`, `count`, `export`, `import`, `tag-overlap`.

> **README is stale on subcommands.** `README.md` documents only the original six (`add / list / remove / count / export / import`) and omits `tag-overlap`, which *is* wired and reachable. The `top-tags` handler (`cmd_top_tags`) exists in `cli/commands.py` but `build_parser()` registers **no `top-tags` subparser**, so it is unreachable from the `linkkeep` entry point — do not rely on `linkkeep top-tags` working.

### REST API

```bash
uvicorn linkkeep.api.app:app --reload
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status": "ok"}`) |
| GET | `/bookmarks?tag=<tag>` | List bookmarks, optional tag filter (case-sensitive) |
| POST | `/bookmarks` | Create a bookmark (body: `{url, title, tags}`), returns `201` |
| DELETE | `/bookmarks/{id}` | Delete by ID — `204` on success, `404` if not found |
| GET | `/bookmarks/tags` | Tag counts (bookmark count per tag, sorted by count desc) |

## Data Storage

Bookmarks are persisted as a JSON array at `~/.linkkeep/bookmarks.json` by default. Override the storage directory with the `LINKKEEP_HOME` environment variable:

```bash
LINKKEEP_HOME=/data/linkkeep linkkeep list
```

Two storage behaviors most affect safe changes:

- **JSON file as database, no in-memory cache.** `Store` (`linkkeep/core/store.py`) is the single persistence abstraction shared by all three interface domains. **Every mutating operation is a full load → modify → save cycle** — `add()` loads all bookmarks, appends one, and writes the whole list back; `remove()` loads, filters, and writes back. There is no locking, so concurrent writers (e.g. the API server and a CLI invocation at once) can overwrite each other's changes.
- **API holds a singleton Store.** `linkkeep/api/deps.py` lazily initializes a module-level `_store_singleton` on the first request and reuses that same `Store` instance for all subsequent requests. The singleton caches the `Store` *object* (its resolved path), **not** the bookmark data — each operation still reads/writes the JSON file. `reset_store_singleton()` exists for test isolation.

## Testing

```bash
pytest tests/ -v
```

Three test modules, one per interface domain:

- `tests/test_core.py` — Bookmark round-trip, Store add/load/remove/next_id, tag normalization & counts.
- `tests/test_api.py` — FastAPI `TestClient`: health, create+list, 404 on delete, tag counts endpoint.
- `tests/test_sync.py` — URL normalization, dedup logic, JSON/Markdown export, import merge with dedup.

All tests use temp directories for isolation and share no state. The API tests override `deps._store_singleton` directly with a temp-directory `Store` (see `tests/test_api.py` `_client_with_tmp_store`) rather than calling `reset_store_singleton()`.

## CI / OpenWiki Automation

`.github/workflows/openwiki-update.yml` runs a **weekly** scheduled OpenWiki documentation refresh at **08:00 UTC every Monday** (`cron: "0 8 * * 1"`), plus a `workflow_dispatch` manual trigger. It installs OpenWiki via npm, runs `openwiki code --update --print`, and opens a pull request with the regenerated docs. The run requires:

- `OPENROUTER_API_KEY` — inference provider key (model `z-ai/glm-5.2` via the `openrouter` provider).
- A PAT with **workflow scope** (`secrets.GH_PAT_WITH_WORKFLOW_SCOPE`) — used for both checkout and the PR step, because the default `GITHUB_TOKEN` cannot commit changes to files under `.github/workflows/`.

## Key Design Decisions

- **Plain dataclass, not Pydantic, in core.** `Bookmark` (`linkkeep/core/models.py`) is a plain `@dataclass`. The API layer wraps it in Pydantic schemas (`BookmarkIn`/`BookmarkOut`) for validation/serialization, keeping core free of web-framework dependencies.
- **JSON file as database.** No external database; `Store` reads/writes the entire bookmark list as a JSON array on every operation. Simple and portable, but not concurrency-safe.
- **Tag normalization: lowercase + strip.** `normalize_tag` (`linkkeep/core/tags.py`) lowercases and strips tags, and it is applied inside `tag_counts`/`top_tags`/`tag_overlap`. It is **not** applied inside `Store.add`, so tags are stored as-is — the persisted file may contain un-normalized tags. Note the CLI `list --tag` / `count --tag` and API `?tag=` filters call the case-sensitive `Bookmark.matches_tag` directly and do not normalize the query, so the filter surfaces are case-sensitive while the tag-overview surfaces are not.
- **URL-based dedup with existing-wins.** Import (`sync/importer.import_from_json`) merges by normalized URL (trailing slash removed, lowercased). Existing bookmarks take priority; incoming duplicates are silently dropped with no field merge. Fresh bookmarks get **reassigned sequential IDs** (their imported IDs are discarded), continuing from the existing max.

## Where to Go Next

By task:

- **Understanding the layered architecture, dependency rules, and persistence invariants** → [architecture.md](architecture.md)
- **Looking up a specific type, function, endpoint, or business rule** (ID allocation, tag normalization timing, case-sensitive vs case-insensitive matching, URL normalization limits, existing-wins dedup) → [domain-guide.md](domain-guide.md)
