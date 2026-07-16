"""linkkeep-svc：多域书签管理服务（core / api / cli / sync 四域）。

在 Stage 1 的极简 linkkeep（models/store/cli 三模块）基础上扩展为一个更贴近真实
工程的小型服务：core 负责数据模型与持久化、api 用 FastAPI 暴露 REST 接口、
cli 保留命令行入口、sync 负责导入导出与去重。四个域各自独立、通过 core 共享
同一份数据模型，用于 OpenWiki 文档生成案例的被文档化对象。
"""
__version__ = "0.2.0"
