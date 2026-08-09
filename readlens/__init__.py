"""ReadLens 阅镜 — 阅读智能工具箱。

在 Tencent/WeChatReading Skills 的基础上延展：
- 平台适配层（可复刻到不同阅读平台）
- 多格式笔记导出（Markdown / Obsidian / Notion）
- 读书报告与可视化
- AI 增值分析（总结 / 主题串联 / 问答 / 推荐）
"""

__version__ = "0.6.0"

from .models import Book, Highlight, Thought, Note, ReadStat, CategoryPref  # noqa: F401
from .adapters import get_platform  # noqa: F401
