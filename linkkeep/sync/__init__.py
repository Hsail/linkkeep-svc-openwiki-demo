"""sync 域：书签的导出、导入与去重，用于跨设备同步 linkkeep-svc 数据。

这是 Step 10 A/B 消费实验的提问落点——"本项目的书签同步逻辑在哪个模块、
遵循什么模式"——答案应精确指向本域的 exporter / importer / dedup 三个文件。
"""
