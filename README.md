# linkkeep-svc

一个多域的书签管理服务（Python），在 Stage 1 极简版 `linkkeep` 的基础上扩展而来，
用于 OpenWiki Stage 2 案例 1 的文档生成实操——一个真实感够强、能触发「小仓库避免薄页
合并」与「多域 Backlog」教学观测点的被文档化对象。

## 四个域

- **`linkkeep/core/`**：数据地基。`Bookmark` 数据类 + `Store`（JSON 本地持久化）+ 标签规范化/统计工具。
- **`linkkeep/api/`**：REST 接口层，基于 FastAPI。`GET/POST /bookmarks`、`DELETE /bookmarks/{id}`、`GET /bookmarks/tags`。
- **`linkkeep/cli/`**：命令行入口。`add / list / remove / count / export / import` 六个子命令。
- **`linkkeep/sync/`**：导入导出与去重，负责跨设备同步书签数据（导出 json/markdown、按 URL 去重合并导入）。

## 安装

```bash
pip install -e ".[dev]"
```

## 用法

```bash
# CLI
linkkeep add https://example.com --title "示例站点" --tag ref --tag demo
linkkeep list
linkkeep count --tag ref
linkkeep export --format markdown --out backup.md
linkkeep import other-device-export.json

# API（另开一个终端）
uvicorn linkkeep.api.app:app --reload
curl http://127.0.0.1:8000/bookmarks
```

数据默认存在 `~/.linkkeep/bookmarks.json`，可用环境变量 `LINKKEEP_HOME` 覆盖。

## 测试

```bash
pytest tests/ -v
```
