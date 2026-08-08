"""AI 笔记总结与阅读总结。"""
from __future__ import annotations

from typing import List

from ..models import Note, ReadStat
from .engine import LLMEngine

_SYS = "你是一位善于提炼的阅读助手，输出简洁、有洞察、可直接使用的中文总结。"


def summarize_note(note: Note, engine: LLMEngine) -> str:
    """总结单本书的笔记，提炼核心观点。"""
    b = note.book
    material = [f"书名：{b.title}；作者：{b.author}；分类：{b.category}", "划线原文："]
    material += [f"- {h.text}" for h in note.highlights]
    if note.thoughts:
        material.append("我的想法：")
        material += [f"- {t.content}" for t in note.thoughts]
    user = ("请基于以下读书划线和想法，提炼这本书的 3-5 个核心观点，"
            "并用一句话概括我从中获得的最大启发。\n\n" + "\n".join(material))
    return engine.complete(_SYS, user)


def summarize_reading(stat: ReadStat, engine: LLMEngine) -> str:
    """基于阅读统计生成一段个性化阅读总结（用于报告）。"""
    cats = "、".join(c.title for c in stat.prefer_category[:3])
    books = "、".join(b["title"] for b in stat.read_longest[:3])
    user = (f"这是我的{stat.mode}阅读数据：总时长约 {stat.total_hours} 小时，"
            f"阅读 {stat.read_days} 天，最常读的书是 {books}，"
            f"偏好分类是 {cats}。请写一段 120 字以内、温暖而有洞察的阅读总结，"
            f"点评我的阅读偏好并给一句鼓励。")
    return engine.complete(_SYS, user)
