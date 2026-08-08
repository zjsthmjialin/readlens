"""Markdown 导出：按章节分组划线与想法，引用格式标注原文。"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import List

from ..models import Note


def _slug(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]", "_", text).strip()
    return text or "untitled"


def to_markdown(note: Note, include_frontmatter: bool = True) -> str:
    b = note.book
    lines: List[str] = []
    if include_frontmatter:
        lines += [
            "---",
            f"title: \"{b.title}\"",
            f"author: \"{b.author}\"",
            f"category: \"{b.category}\"",
            f"book_id: \"{b.book_id}\"",
            f"finished: {str(b.finished).lower()}",
            f"highlights: {len(note.highlights)}",
            f"thoughts: {len(note.thoughts)}",
            "tags: [reading, readlens]",
            "---",
            "",
        ]
    lines.append(f"# {b.title}")
    lines.append("")
    meta = f"**作者**：{b.author}"
    if b.category:
        meta += f" ｜ **分类**：{b.category}"
    if b.rating:
        meta += f" ｜ **评分**：{b.rating}"
    lines.append(meta)
    lines.append("")
    lines.append(f"> 划线 {len(note.highlights)} 条 · 想法 {len(note.thoughts)} 条 · "
                 f"书签 {note.bookmark_count} 个（共 {note.total_count} 条笔记）")
    lines.append("")

    # 关联想法到划线（按 abstract 匹配）
    thoughts_by_abs = defaultdict(list)
    book_reviews = []
    for t in note.thoughts:
        if t.is_book_review:
            book_reviews.append(t)
        elif t.abstract:
            thoughts_by_abs[t.abstract].append(t)
        else:
            thoughts_by_abs[""].append(t)

    # 按章节标题分组划线，按首次出现顺序排列
    by_chapter = defaultdict(list)
    ch_order = {}
    for h in note.highlights:
        title = h.chapter_title or "未分章节"
        by_chapter[title].append(h)
        ch_order.setdefault(title, h.chapter_idx)

    for ch_title in sorted(by_chapter, key=lambda t: ch_order[t]):
        items = by_chapter[ch_title]
        lines.append(f"## {ch_title}")
        lines.append("")
        for h in items:
            lines.append(f"> {h.text}")
            for t in thoughts_by_abs.get(h.text, []):
                lines.append(f"> ")
                lines.append(f"> 💡 *{t.content}*")
            lines.append("")

    # 无法关联到划线的独立想法
    orphan = thoughts_by_abs.get("", [])
    if orphan:
        lines.append("## 独立想法")
        lines.append("")
        for t in orphan:
            prefix = f"（{t.chapter_title}）" if t.chapter_title else ""
            lines.append(f"- 💡 {prefix}{t.content}")
        lines.append("")

    if book_reviews:
        lines.append("## 整本书评")
        lines.append("")
        for t in book_reviews:
            star = f"（{t.star}★）" if t.star and t.star > 0 else ""
            lines.append(f"- {star}{t.content}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def export_markdown(notes: List[Note], out_dir: str,
                    single_file: bool = False) -> List[str]:
    """导出为 Markdown 文件，返回生成的文件路径列表。"""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    if single_file:
        path = os.path.join(out_dir, "reading_notes.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(to_markdown(n) for n in notes))
        written.append(path)
    else:
        for n in notes:
            fname = f"{_slug(n.book.title)}.md"
            path = os.path.join(out_dir, fname)
            with open(path, "w", encoding="utf-8") as f:
                f.write(to_markdown(n))
            written.append(path)
    return written
