"""FastAPI 依赖注入：给每个请求提供一个 core.store.Store 实例。"""
from ..core.store import Store

_store_singleton = None


def get_store() -> Store:
    """复用同一个 Store 实例，避免每次请求都重新解析 LINKKEEP_HOME。"""
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = Store()
    return _store_singleton


def reset_store_singleton() -> None:
    """测试专用：强制下一次 get_store() 重新构建 Store（避免用例间共享单例状态）。"""
    global _store_singleton
    _store_singleton = None
