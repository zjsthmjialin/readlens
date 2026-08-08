"""读书问答：基于某本书的笔记内容回答问题（RAG 雏形）。"""
from __future__ import annotations

import re
from typing import List

from ..models import Note
from .engine import LLMEngine

_SYS = ("你是一位读书助手，只根据用户提供的划线和想法回答问题；"
        "若材料不足以回答，请明确说明。")


def _retrieve(note: Note, question: str, k: int = 6) -> List[str]:
    """极简检索：按问题与划线的字符重叠打分，取 top-k。"""
    q = set(re.sub(r"[^一-龥A-Za-z]", "", question))
    scored = []
    for h in note.highlights:
        text = h.text
        score = len(q & set(re.sub(r"[^一-龥A-Za-z]", "", text)))
        scored.append((score, text))
    for t in note.thoughts:
        score = len(q & set(re.sub(r"[^一-龥A-Za-z]", "", t.content)))
        scored.append((score, "（想法）" + t.content))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for s, t in scored[:k] if s > 0] or [t for _, t in scored[:k]]


def ask_about_book(note: Note, question: str, engine: LLMEngine) -> str:
    context = _retrieve(note, question)
    user = (f"书名：《{note.book.title}》\n相关划线/想法：\n"
            + "\n".join(f"- {c}" for c in context)
            + f"\n\n问题：{question}\n请基于以上材料作答。")
    return engine.complete(_SYS, user)
