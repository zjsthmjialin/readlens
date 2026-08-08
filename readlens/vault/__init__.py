"""Obsidian 知识库（vault）生成器。

把统一模型的书籍/笔记 + 手动藏书组织成一个深度适配 Dataview 的
个人读书/藏书知识库：每本书一张笔记、作者中心页、主题 MOC、
Dataview 仪表盘、阅读时间线、愿望清单与模板。
"""
from .builder import build_vault, VaultConfig  # noqa: F401
