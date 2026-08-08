"""AI 增值模块：笔记总结、跨书主题串联、读书问答、个性化推荐。

所有能力都走统一的 LLMEngine 抽象：
- offline：内置离线模板引擎，无需联网/Key，保证 demo 可跑
- openai：接入 OpenAI 兼容接口（设置 OPENAI_API_KEY 后自动启用）
"""
from .engine import get_engine, LLMEngine  # noqa: F401
from .summarize import summarize_note, summarize_reading  # noqa: F401
from .themes import link_themes  # noqa: F401
from .qa import ask_about_book  # noqa: F401
from .recommend import recommend_books  # noqa: F401
