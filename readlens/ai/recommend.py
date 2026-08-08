"""个性化推荐：基于阅读偏好与笔记，给出下一步读什么的建议。"""
from __future__ import annotations

from typing import List

from ..models import Note, ReadStat
from .engine import LLMEngine

_SYS = "你是一位懂读者口味的荐书顾问，推荐要具体、说明理由、避免泛泛而谈。"


def recommend_books(stat: ReadStat, notes: List[Note], engine: LLMEngine,
                    n: int = 5) -> str:
    cats = "、".join(c.title for c in stat.prefer_category[:3])
    read = "、".join(sorted({nt.book.title for nt in notes}))
    authors = "、".join(a.name for a in stat.prefer_author[:3])
    user = (f"我最近读过：{read}。\n偏好分类：{cats}；偏好作者：{authors}。\n"
            f"请推荐 {n} 本我可能会喜欢、但不在上述已读列表里的书，"
            f"每本给出书名、作者和一句话推荐理由（结合我的阅读偏好）。")
    return engine.complete(_SYS, user)
