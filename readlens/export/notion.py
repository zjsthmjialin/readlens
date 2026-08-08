"""Notion 导出：生成 Notion API 兼容的 blocks JSON。

不直接依赖 Notion SDK，输出标准 blocks 数组，可直接喂给
`notion-client` 的 `blocks.children.append`，或保存为 JSON 备用。
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import List, Dict, Any

from ..models import Note
from .markdown import _slug


def _rt(text: str) -> List[Dict[str, Any]]:
    """构造 Notion rich_text 数组。"""
    return [{"type": "text", "text": {"content": text[:2000]}}]


def to_notion_blocks(note: Note) -> List[Dict[str, Any]]:
    b = note.book
    blocks: List[Dict[str, Any]] = [
        {"object": "block", "type": "heading_1",
         "heading_1": {"rich_text": _rt(b.title)}},
        {"object": "block", "type": "paragraph",
         "paragraph": {"rich_text": _rt(
             f"作者：{b.author} ｜ 分类：{b.category} ｜ "
             f"划线 {len(note.highlights)} · 想法 {len(note.thoughts)}")}},
    ]
    by_chapter = defaultdict(list)
    for h in note.highlights:
        by_chapter[(h.chapter_idx, h.chapter_title or "未分章节")].append(h)
    for (_, ch_title), items in sorted(by_chapter.items()):
        blocks.append({"object": "block", "type": "heading_2",
                       "heading_2": {"rich_text": _rt(ch_title)}})
        for h in items:
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": _rt(h.text)}})
    thoughts = [t for t in note.thoughts]
    if thoughts:
        blocks.append({"object": "block", "type": "heading_2",
                       "heading_2": {"rich_text": _rt("想法与点评")}})
        for t in thoughts:
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": _rt(
                               ("★ " if t.is_book_review else "💡 ") + t.content)}})
    return blocks


def export_notion_json(notes: List[Note], out_dir: str) -> List[str]:
    """把每本书导出为一个 Notion blocks JSON 文件。"""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for n in notes:
        payload = {
            "page_title": n.book.title,
            "properties": {
                "作者": n.book.author,
                "分类": n.book.category,
                "划线数": len(n.highlights),
                "想法数": len(n.thoughts),
            },
            "children": to_notion_blocks(n),
        }
        path = os.path.join(out_dir, f"{_slug(n.book.title)}.notion.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        written.append(path)
    return written
