---
type: Project
title: linkkeep-svc Quickstart
description: Multi-domain bookmark management service in Python. Entry point for OpenWiki documentation covering install, CLI + REST API usage, storage, testing, CI, and a task-routing map.
resource: /README.md
tags: [linkkeep, bookmark-management, python, fastapi, cli]
verified:
  - by: openwiki/0.7.3
    at: 2026-11-02T17:44:06.992Z
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
  - id: openwiki-source-b953bc233bb1a125beed5f1a
    resource: repo://linkkeep/core/store.py
  - id: openwiki-source-25b341ad09159a35b9816d97
    resource: repo://linkkeep/sync/dedup.py
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
generated: { by: "openwiki/0.7.3", at: "2026-11-02T17:44:06.992Z" }
---

# linkkeep-svc — OpenWiki Quickstart

linkkeep-svc is a multi-domain **bookmark management service** written in Python (3.9+). It organizes a simple bookmark workflow into four cleanly separated domains — core data models, a FastAPI REST API, a command-line interface, and a sync layer for import/export with deduplication.

The project was built as an OpenWiki Stage 2 documentation case study: a small but realistic service that exercises cross-domain dependencies, shared data models, and distinct interfaces over the same storage layer.

## Four Domains at a Glance

| Domain | Location | Role |
|--------|----------|------|
| **core** | `linkkeep/core/` | Data foundation: `Bookmark` model, `Store` (JSON persistence), tag normalization & statistics |
| **api** | `linkkeep/api/` | REST interface via FastAPI: CRUD + tag overview endpoints |
| **cli** | `linkkeep/cli/` | Command-line entry: `add / list / remove / count / export / import / tag-overlap` |
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
linkkeep tag-overlap ref demo
linkkeep export --format markdown --out backup.md
linkkeep import other-device-export.json
```

`linkkeep/cli/main.py` registers **7 subcommands**: `add`, `list`, `remove <id>`, `count`, `export`, `import`, `tag-overlap`. Each subparser maps to a handler in `cli/commands.py`; `main()` creates one `Store()` and dispatches. A `cmd_top_tags` handler is defined in `commands.py` but **not wired** to a subparser, so `top-tags` is currently unreachable from the CLI (see [Backlog](#backlog)). `README.md` documents only 6 subcommands (`add / list / remove / count / export / import`) and omits `tag-overlap` — it is slightly stale relative to the implemented CLI.

### REST API

```bash
uvicorn linkkeep.api.app:app --reload
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/bookmarks?tag=<tag>` | List bookmarks, optional tag filter |
| POST | `/bookmarks` | Create a bookmark (body: `{url, title, tags}`), 201 |
| DELETE | `/bookmarks/{id}` | Delete by ID (204, or 404 if not found) |
| GET | `/bookmarks/tags` | Tag counts (bookmark count per tag), sorted by frequency |

Routes are defined in `linkkeep/api/routes.py` under the `/bookmarks` prefix; `GET /health` is added directly in `linkkeep/api/app.py`. The `?tag=` filter and CLI `list`/`count --tag` both call `Bookmark.matches_tag()`, which is **case-sensitive** — `?tag=Ref` will not match a bookmark stored with `ref` (see [domain-guide.md](domain-guide.md)).

## Data Storage

Bookmarks are persisted as a JSON array at `~/.linkkeep/bookmarks.json` by default. Override the storage directory with the `LINKKEEP_HOME` environment variable:

```bash
LINKKEEP_HOME=/data/linkkeep linkkeep list
```

The `Store` class (`linkkeep/core/store.py`) handles load/save, auto-incrementing IDs, and directory/file creation. Every operation is a full load → modify → save cycle (no caching). The API layer reuses a singleton `Store` instance per process via `linkkeep/api/deps.py` (`get_store()`), which caches the `Store` object — not the data — so each request still reads/writes the file.

## Testing

```bash
pytest tests/ -v
```

Three test modules, one per interface domain, each using temp directories for isolation (no shared state):

- `tests/test_core.py` — Bookmark round-trip, Store add/load/remove/next_id, tag normalization & counts
- `tests/test_api.py` — FastAPI TestClient: health, create+list, 404 on delete, tag counts endpoint
- `tests/test_sync.py` — URL normalization, dedup logic, JSON/Markdown export, import merge with dedup

API tests override `deps._store_singleton` with a temp-directory `Store`; `reset_store_singleton()` is available as a cleaner alternative.

## CI / OpenWiki Automation

`.github/workflows/openwiki-update.yml` runs an OpenWiki documentation refresh on a **weekly schedule** (cron `0 8 * * 1` = Monday 08:00 UTC), plus `workflow_dispatch` for manual runs. It installs OpenWiki via npm, runs `openwiki code --update --print`, and opens a pull request with regenerated docs.

Key configuration details:

- **Checkout and PR creation use `secrets.GH_PAT_WITH_WORKFLOW_SCOPE`** (a PAT with `workflows` scope), not the default `GITHUB_TOKEN`. This is required because OpenWiki's `writeCodeModeWorkflow()` unconditionally rewrites the workflow file on each run, and `GITHUB_TOKEN` lacks the `workflows` permission needed to commit changes under `.github/workflows/`.
- **Provider**: OpenRouter with `OPENROUTER_API_KEY` and `OPENWIKI_MODEL_ID: z-ai/glm-5.2`.
- **LangSmith tracing variables are deliberately omitted** from the workflow env (the official template ships `LANGSMITH_API_KEY` / `LANGCHAIN_PROJECT` / `LANGCHAIN_TRACING_V2`); omitting them leaves LangSmith tracing disabled, which does not affect the main flow.
- **`add-paths`** includes `openwiki`, `AGENTS.md`, `CLAUDE.md` but **intentionally excludes the workflow file itself**. Although `writeCodeModeWorkflow()` still dirties the workflow file in the runner workspace, excluding it from `add-paths` prevents `create-pull-request` from including that hunk in the PR (so the PR does not revert the CI fix). The runner is ephemeral, so the local overwrite has no lasting effect.

## Key Design Decisions

- **One shared data model**: `Bookmark` is a plain `@dataclass` (not a Pydantic model). The API layer wraps it in Pydantic `BookmarkIn`/`BookmarkOut` schemas for validation/serialization, keeping core free of web-framework dependencies.
- **JSON file as database**: No external database. `Store` reads/writes the entire bookmark list as a JSON array on every operation. Simple, portable, fine for the project's scope — but concurrent writers (CLI + API server) could overwrite each other since there is no locking.
- **Tag normalization**: Tags are lowercased and stripped in `core/tags.py` (`normalize_tag`). Normalization is applied at statistics time (`tag_counts`, `tag_overlap`), **not** at storage time — tags are persisted verbatim, so mixed-case variants like `"Ref"` and `"ref"` are stored as distinct entries even though statistics collapse them. The single-tag query path (`matches_tag`) is likewise un-normalized.
- **URL-based dedup**: Import merges by normalized URL (trailing slash removed, lowercased). Existing bookmarks take priority; incoming duplicates are silently dropped. This is "existing wins", not "last write wins".

## Backlog

Maintained in parallel with [domain-guide.md](domain-guide.md); see that page for full details.

- **`top-tags` subcommand not wired**: `cmd_top_tags` is defined in `cli/commands.py` but no `top-tags` subparser is registered in `main.py`, so it is unreachable from the CLI. `README.md` also omits `tag-overlap` (documents only 6 of the 7 registered subcommands).
- **`BookmarkListOut` schema unused**: `api/schemas.py` defines `BookmarkListOut` (wrapper with `total` + `items`) but `routes.py` returns a plain `List[BookmarkOut]`.
- **`dedup_stats` not exposed via CLI or API**: `sync/dedup.py` provides `dedup_stats()` for pre-import preview, but no CLI/API surface calls it yet.
- **`count_by_tag` vs `tag_counts`**: Two overlapping tag-counting functions exist (`sync/exporter.count_by_tag` and `core/tags.tag_counts`). `count_by_tag` groups untagged bookmarks under `_untagged` and does not normalize tags; it is not called by any export function, CLI, or API.
- **`rarest_tags` not exposed via CLI or API**: `core/tags.rarest_tags()` returns the least-common tags to help find orphan/misspelled tags, but no CLI subcommand or API endpoint calls it yet.
- **`matches_any_tag` / `matches_all_tags` unused**: `Bookmark` defines OR/AND multi-tag matchers, but neither is called by CLI or API (the CLI uses `core.tags.tag_overlap` for AND semantics).
- **ID reuse on delete**: `next_id` is `max(existing)+1` with no high-water mark, so deleting the highest-ID bookmark causes that ID to be reused by the next `add()`.
- **Tag normalization gap**: Tags are stored verbatim (not normalized at add/create time), producing mixed-case duplicates in the JSON file even though statistics collapse case variants.

## Task-Routing Map

| If you need… | Go to |
|--------------|-------|
| The cross-domain dependency graph, acyclic import rules, and how the four layers assemble | [architecture.md](architecture.md) |
| Persistence semantics: full load→modify→save cycle, ID allocation, `next_id` reuse, `Store` lifecycle | [architecture.md](architecture.md) |
| Per-layer assembly: FastAPI app/router/singleton `Store`, argparse subcommand dispatch, sync export/import flow | [architecture.md](architecture.md) |
| Per-domain API reference for key types, functions, and signatures (`Bookmark`, `Store`, `tags.*`, routes, schemas) | [domain-guide.md](domain-guide.md) |
| Business rules and non-obvious behaviors: tag normalization gap, case-sensitive `matches_tag`, dedup existing-wins, ID reassignment on import | [domain-guide.md](domain-guide.md) |
| Backlog of unused/unwired surfaces (`top-tags`, `BookmarkListOut`, `dedup_stats`, `rarest_tags`, `count_by_tag`) | [domain-guide.md](domain-guide.md) |
| Install, CLI/REST usage, storage config, testing, CI/OpenWiki automation | this page |
