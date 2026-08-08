"""跨书主题串联：找出多本书之间共通的主题与观点连接。"""
from __future__ import annotations

from typing import List

from ..models import Note
from .engine import LLMEngine

_SYS = "你是一位博学的读书顾问，擅长在不同书籍之间发现主题联系和思想脉络。"


def link_themes(notes: List[Note], engine: LLMEngine, theme: str = "") -> str:
    """从多本书的划线中，串联出共通主题与跨书洞察。"""
    material = []
    for n in notes:
        picks = n.highlights[:3]
        if not picks:
            continue
        material.append(f"《{n.book.title}》（{n.book.author}）：")
        material += [f"  - {h.text}" for h in picks]
    focus = f"围绕「{theme}」这个主题，" if theme else ""
    user = (f"{focus}请在下面这些书的划线之间找出 2-3 条跨书的共通主题或思想联系，"
            f"每条说明它们如何相互呼应或补充，并给出一个值得进一步思考的问题。\n\n"
            + "\n".join(material))
    return engine.complete(_SYS, user)
