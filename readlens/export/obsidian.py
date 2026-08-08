"""Obsidian 导出：Markdown + 双链、按作者/分类聚合的 MOC 索引页。"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import List

from ..models import Note
from .markdown import to_markdown, _slug


def export_obsidian(notes: List[Note], vault_dir: str,
                    subfolder: str = "ReadLens") -> List[str]:
    """写入 Obsidian vault，附带作者/分类双链与一个 MOC 索引。"""
    base = os.path.join(vault_dir, subfolder)
    os.makedirs(base, exist_ok=True)
    written = []

    for n in notes:
        b = n.book
        md = to_markdown(n, include_frontmatter=True)
        # 追加双链，方便在 Obsidian 里做关系图谱
        links = []
        if b.author:
            links.append(f"[[{b.author}]]")
        if b.category:
            links.append(f"[[{b.category}]]")
        if links:
            md += "\n\n---\n关联：" + " ".join(links) + "\n"
        path = os.path.join(base, f"{_slug(b.title)}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        written.append(path)

    # 生成 MOC（Map of Content）索引页
    by_cat = defaultdict(list)
    for n in notes:
        by_cat[n.book.category or "未分类"].append(n)
    moc = ["# 📚 ReadLens 阅读索引", ""]
    for cat, ns in sorted(by_cat.items()):
        moc.append(f"## {cat}")
        moc.append("")
        for n in ns:
            moc.append(f"- [[{_slug(n.book.title)}|{n.book.title}]] "
                       f"— {n.book.author}（{len(n.highlights)} 划线 / "
                       f"{len(n.thoughts)} 想法）")
        moc.append("")
    moc_path = os.path.join(base, "_ReadLens_MOC.md")
    with open(moc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(moc))
    written.append(moc_path)
    return written
