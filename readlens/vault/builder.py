"""Obsidian 知识库生成器主逻辑。"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict

from ..models import Note, Book, ReadStat
from . import templates as T

# 目录名
DIR_BOOKS = "01-书籍"
DIR_AUTHORS = "02-作者"
DIR_TOPICS = "03-主题"
DIR_DASH = "04-仪表盘"
DIR_TPL = "00-模板"


def _slug(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|#\[\]]", "_", (text or "").strip())
    return text or "未命名"


def _ts_to_date(ts: Optional[int]) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _status_of(book: Book) -> str:
    if book.finished:
        return "已读"
    if book.progress and book.progress > 0:
        return "在读"
    return "想读"


def _personal_rating(note: Note) -> Optional[float]:
    """从整本书评的 star（0-5）取个人评分；没有则留空。"""
    for t in note.thoughts:
        if t.is_book_review and t.star and t.star > 0:
            return float(t.star)
    return None


@dataclass
class VaultConfig:
    out_dir: str = "./MyReadingVault"
    vault_name: str = "我的读书藏书库"
    overwrite: bool = True


# --------------------------------------------------------------------------
# 单本书笔记
# --------------------------------------------------------------------------
def _book_note_md(note: Note) -> str:
    b = note.book
    status = _status_of(b)
    prating = _personal_rating(note)
    added = date.today().isoformat()
    finished_date = ""
    if b.finished and note.thoughts:
        finished_date = _ts_to_date(max((t.create_time or 0) for t in note.thoughts))
    owned = b.owned if b.owned and b.owned != "none" else (
        "digital" if b.source == "weread" else "none")

    tags = ["book"]
    if b.category:
        tags.append(b.category)
    if owned == "physical":
        tags.append("藏书")

    fm = [
        "---",
        "type: book",
        f'title: "{b.title}"',
        f'author: "{b.author}"',
        f'authors: ["[[{_slug(b.author)}]]"]' if b.author else "authors: []",
        f'category: "{b.category}"',
        f"tags: [{', '.join(tags)}]",
        f"status: {status}",
        f"rating: {prating if prating is not None else ''}",
        f"platform_rating: {b.rating if b.rating is not None else ''}",
        f'isbn: ""',
        f'publisher: "{b.publisher}"',
        f'cover: {b.cover}',
        f"source: {b.source}",
        f"owned: {owned}",
        f'location: ""',
        f"price: ",
        f"progress: {b.progress if b.progress is not None else (100 if b.finished else 0)}",
        f"started: ",
        f"finished: {finished_date}",
        f"added: {added}",
        f"highlights: {len(note.highlights)}",
        f"thoughts: {len(note.thoughts)}",
        "---",
        "",
        f"# {b.title}",
        "",
    ]
    if b.intro:
        fm += [f"> [!info] 简介", f"> {b.intro}", ""]

    body: List[str] = []
    # 划线按章节标题分组，按章节首次出现的 idx 排序
    by_ch = defaultdict(list)
    ch_order: Dict[str, int] = {}
    for h in note.highlights:
        title = h.chapter_title or "未分章节"
        by_ch[title].append(h)
        ch_order.setdefault(title, h.chapter_idx)

    # 想法关联划线
    th_by_abs = defaultdict(list)
    book_reviews = []
    orphan_thoughts = []
    for t in note.thoughts:
        if t.is_book_review:
            book_reviews.append(t)
        elif t.abstract:
            th_by_abs[t.abstract].append(t)
        else:
            orphan_thoughts.append(t)

    if by_ch:
        body.append("## 划线")
        body.append("")
        for ch in sorted(by_ch, key=lambda t: ch_order[t]):
            items = by_ch[ch]
            body.append(f"### {ch}")
            body.append("")
            for h in items:
                hot = f"  `🔥{h.popular_count}人`" if h.popular_count else ""
                body.append(f"> {h.text}{hot}")
                for t in th_by_abs.get(h.text, []):
                    body.append("> ")
                    body.append(f"> 💡 *{t.content}*")
                body.append("")

    if orphan_thoughts:
        body += ["## 想法", ""]
        for t in orphan_thoughts:
            pre = f"（{t.chapter_title}）" if t.chapter_title else ""
            body.append(f"- 💡 {pre}{t.content}")
        body.append("")

    if book_reviews:
        body += ["## 书评", ""]
        for t in book_reviews:
            star = f"（{'★' * int(t.star)}）" if t.star and t.star > 0 else ""
            body.append(f"- {star}{t.content}")
        body.append("")

    # 关联区（双链）
    links = []
    if b.author:
        links.append(f"作者 [[{_slug(b.author)}]]")
    if b.category:
        links.append(f"主题 [[{b.category}]]")
    body += ["## 关联", "", " · ".join(links) if links else "—", ""]

    return "\n".join(fm + body).rstrip() + "\n"


# --------------------------------------------------------------------------
# 作者中心页
# --------------------------------------------------------------------------
def _author_note_md(author: str) -> str:
    return f"""---
type: author
name: "{author}"
tags: [author]
---

# {author}

## 我库中的作品
```dataview
TABLE status AS 状态, rating AS 我的评分, file.link AS 书
FROM #book
WHERE contains(author, this.file.name)
SORT rating DESC
```

## 关于
> 在此记录对这位作者的整体印象、写作风格、阅读顺序建议等。
"""


# --------------------------------------------------------------------------
# 主题 MOC
# --------------------------------------------------------------------------
def _topic_note_md(topic: str) -> str:
    return f"""---
type: topic
tags: [topic, moc]
---

# 🗂️ {topic}

按分类聚合的主题地图（MOC）。

```dataview
TABLE author AS 作者, status AS 状态, rating AS 评分, owned AS 拥有
FROM #book
WHERE category = this.file.name
SORT status ASC, rating DESC
```

## 主题笔记
> 记录这个主题下的核心概念、书与书之间的联系、延伸阅读方向。
"""


# --------------------------------------------------------------------------
# 仪表盘
# --------------------------------------------------------------------------
def _dashboard_files() -> Dict[str, str]:
    return {
        "在读.md": """# 📕 在读
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, (progress + "%") AS 进度, started AS 开始
FROM #book
WHERE status = "在读"
SORT progress DESC
```
""",
        "想读(愿望清单).md": """# 🌱 想读 / 愿望清单
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, category AS 分类, owned AS 拥有情况
FROM #book
WHERE status = "想读"
SORT added DESC
```

> 拥有情况为 `none` 的是还没入手、可以考虑购买的书。
""",
        "已读.md": """# ✅ 已读
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, rating AS 评分, finished AS 读完于
FROM #book
WHERE status = "已读"
SORT finished DESC
```
""",
        "评分排行.md": """# ⭐ 评分排行
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, rating AS 我的评分, platform_rating AS 平台评分
FROM #book
WHERE rating
SORT rating DESC
```
""",
        "藏书清单.md": """# 📦 藏书清单（拥有的实体/电子书）
## 纸质藏书
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, location AS 位置, price AS 价格
FROM #book
WHERE owned = "physical"
SORT location ASC
```
## 电子书
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, source AS 来源
FROM #book
WHERE owned = "digital"
SORT author ASC
```
""",
    }


def _stats_note_md(stat: Optional[ReadStat]) -> str:
    head = """# 📊 阅读统计

## 藏书概览（实时）
```dataview
TABLE WITHOUT ID
  length(rows) AS 数量
FROM #book
GROUP BY status AS 状态
```

```dataview
TABLE WITHOUT ID length(rows) AS 数量
FROM #book
GROUP BY owned AS 拥有情况
```

## 各分类藏书数
```dataview
TABLE WITHOUT ID length(rows) AS 数量
FROM #book
WHERE category
GROUP BY category AS 分类
SORT length(rows) DESC
```
"""
    if stat is None:
        return head
    hrs = stat.total_hours
    top = "、".join(b["title"] for b in stat.read_longest[:3])
    cats = "、".join(c.title for c in stat.prefer_category[:3])
    extra = f"""
## 来自阅读平台的统计（{stat.mode}）
- 总阅读时长：约 **{hrs} 小时**
- 阅读天数：**{stat.read_days}** 天
- 读得最多：{top}
- 偏好分类：{cats}

> 该模块由 ReadLens 从阅读平台数据快照生成，重新导入可刷新。
"""
    return head + extra


# --------------------------------------------------------------------------
# 首页 & 时间线
# --------------------------------------------------------------------------
def _home_md(vault_name: str) -> str:
    return f"""# 📖 {vault_name} · 首页

> 个人读书 / 藏书知识库。需启用 **Dataview** 插件。

## 正在读
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, (progress + "%") AS 进度
FROM #book
WHERE status = "在读"
SORT progress DESC
```

## 最近读完
```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, rating AS 评分, finished AS 读完于
FROM #book
WHERE status = "已读"
SORT finished DESC
LIMIT 5
```

## 想读（愿望清单）Top
```dataview
LIST FROM #book
WHERE status = "想读"
SORT added DESC
LIMIT 8
```

## 快捷入口
- [[在读]] · [[已读]] · [[想读(愿望清单)]]
- [[评分排行]] · [[藏书清单]] · [[阅读统计]]
- [[05-阅读时间线|📅 阅读时间线]]

## 藏书速览
```dataview
TABLE WITHOUT ID length(rows) AS 数量
FROM #book
GROUP BY status AS 状态
```
"""


def _timeline_md() -> str:
    return """# 📅 阅读时间线

按读完时间倒序排列。

```dataview
TABLE WITHOUT ID file.link AS 书, author AS 作者, rating AS 评分
FROM #book
WHERE finished
SORT finished DESC
```

## 在读中
```dataview
LIST FROM #book WHERE status = "在读"
```
"""


# --------------------------------------------------------------------------
# 主入口
# --------------------------------------------------------------------------
def build_vault(notes: List[Note], config: VaultConfig,
                stat: Optional[ReadStat] = None,
                manual_books: Optional[List[Note]] = None) -> Dict[str, int]:
    """生成完整 Obsidian 知识库。

    notes: 从平台导入的书籍笔记
    manual_books: 手动录入的藏书笔记（可选，与 notes 合并入库）
    stat: 阅读统计（可选，用于统计页快照）
    返回各类文件计数。
    """
    all_notes = list(notes) + list(manual_books or [])
    root = config.out_dir
    counts = {"books": 0, "authors": 0, "topics": 0, "dashboards": 0, "misc": 0}

    for d in (DIR_BOOKS, DIR_AUTHORS, DIR_TOPICS, DIR_DASH, DIR_TPL):
        os.makedirs(os.path.join(root, d), exist_ok=True)

    authors, topics = set(), set()

    # 书籍笔记
    for note in all_notes:
        b = note.book
        path = os.path.join(root, DIR_BOOKS, f"{_slug(b.title)}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_book_note_md(note))
        counts["books"] += 1
        if b.author:
            authors.add(b.author)
        if b.category:
            topics.add(b.category)

    # 作者中心页
    for a in sorted(authors):
        with open(os.path.join(root, DIR_AUTHORS, f"{_slug(a)}.md"), "w",
                  encoding="utf-8") as f:
            f.write(_author_note_md(a))
        counts["authors"] += 1

    # 主题 MOC
    for tp in sorted(topics):
        with open(os.path.join(root, DIR_TOPICS, f"{_slug(tp)}.md"), "w",
                  encoding="utf-8") as f:
            f.write(_topic_note_md(tp))
        counts["topics"] += 1

    # 仪表盘
    dash = _dashboard_files()
    dash["阅读统计.md"] = _stats_note_md(stat)
    for name, content in dash.items():
        with open(os.path.join(root, DIR_DASH, name), "w", encoding="utf-8") as f:
            f.write(content)
        counts["dashboards"] += 1

    # 模板
    with open(os.path.join(root, DIR_TPL, "书籍模板.md"), "w", encoding="utf-8") as f:
        f.write(T.BOOK_TEMPLATE)
    with open(os.path.join(root, DIR_TPL, "藏书模板.md"), "w", encoding="utf-8") as f:
        f.write(T.MANUAL_COLLECTION_TEMPLATE)

    # 首页 / 时间线 / README
    with open(os.path.join(root, "📖 首页.md"), "w", encoding="utf-8") as f:
        f.write(_home_md(config.vault_name))
    with open(os.path.join(root, "05-阅读时间线.md"), "w", encoding="utf-8") as f:
        f.write(_timeline_md())
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as f:
        f.write(T.VAULT_README)
    counts["misc"] += 5

    return counts
