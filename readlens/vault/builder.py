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
from .merge import (MARK_END, wrap_auto, merge_frontmatter, extract_user_tail)
from . import snapshot as S

# 目录名
DIR_BOOKS = "01-书籍"
DIR_AUTHORS = "02-作者"
DIR_TOPICS = "03-主题"
DIR_DASH = "04-仪表盘"
DIR_TPL = "00-模板"

# 各类笔记里「自动区之后」默认给用户的手写占位
TAIL_BOOK = "## 我的笔记\n\n> 这一区是你的手写笔记，重新生成知识库时不会被覆盖。\n"
TAIL_AUTHOR = "## 关于\n\n> 在此记录对这位作者的整体印象、写作风格、阅读顺序建议等。\n"
TAIL_TOPIC = "## 主题笔记\n\n> 记录这个主题下的核心概念、书与书之间的联系、延伸阅读方向。\n"


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
    incremental: bool = True   # True=合并保护手写内容/手填字段；False=全量覆盖
    snapshot: bool = True      # 是否记录统计快照并生成趋势页


def _render(fm_lines: List[str], auto_inner: str, user_tail: str) -> str:
    """组装一篇「frontmatter + 标记包裹的自动区 + 用户手写尾部」的笔记。"""
    parts = ["---", *fm_lines, "---", "",
             wrap_auto(auto_inner), "", user_tail.rstrip("\n")]
    return "\n".join(parts).rstrip() + "\n"


def _write_note(path: str, fm_lines: List[str], auto_inner: str,
                default_tail: str, incremental: bool) -> None:
    """写入笔记；incremental 时合并旧文件的手填字段与手写尾部。"""
    if incremental and os.path.exists(path):
        old = open(path, encoding="utf-8").read()
        fm_lines = merge_frontmatter(fm_lines, old)
        user_tail = extract_user_tail(old, default_tail)
    else:
        user_tail = default_tail
    with open(path, "w", encoding="utf-8") as f:
        f.write(_render(fm_lines, auto_inner, user_tail))


# --------------------------------------------------------------------------
# 单本书笔记
# --------------------------------------------------------------------------
def _book_note_parts(note: Note):
    """返回 (frontmatter 行列表, 自动区正文字符串)。"""
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
        "type: book",
        f'title: "{b.title}"',
        f'author: "{b.author}"',
        f'authors: ["[[{_slug(b.author)}]]"]' if b.author else "authors: []",
        f'category: "{b.category}"',
        f"tags: [{', '.join(tags)}]",
        f"status: {status}",
        f"rating: {prating if prating is not None else ''}",
        f"platform_rating: {b.rating if b.rating is not None else ''}",
        f'isbn: "{b.isbn}"',
        f'publisher: "{b.publisher}"',
        f'pubdate: {b.pubdate}',
        f'cover: {b.cover}',
        f"source: {b.source}",
        f"owned: {owned}",
        f'location: ""',
        f"price: ",
        f"priority: ",       # 购书优先级：高 | 中 | 低（用于购书清单排序）
        f"price_target: ",   # 心理价位（可选）
        f"progress: {b.progress if b.progress is not None else (100 if b.finished else 0)}",
        f"started: ",
        f"finished: {finished_date}",
        f"added: {added}",
        f"highlights: {len(note.highlights)}",
        f"thoughts: {len(note.thoughts)}",
    ]

    # 自动区正文
    body: List[str] = [f"# {b.title}", ""]
    if b.cover:
        body += [f"![封面|150]({b.cover})", ""]
    if b.intro:
        body += [f"> [!info] 简介", f"> {b.intro}", ""]
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

    return fm, "\n".join(body).rstrip() + "\n"


# --------------------------------------------------------------------------
# 作者中心页
# --------------------------------------------------------------------------
def _author_note_parts(author: str):
    fm = ["type: author", f'name: "{author}"', "tags: [author]"]
    inner = f"""# {author}

## 我库中的作品
```dataview
TABLE status AS 状态, rating AS 我的评分, file.link AS 书
FROM #book
WHERE contains(author, this.file.name)
SORT rating DESC
```"""
    return fm, inner


# --------------------------------------------------------------------------
# 主题 MOC
# --------------------------------------------------------------------------
def _topic_note_parts(topic: str):
    fm = ["type: topic", "tags: [topic, moc]"]
    inner = f"""# 🗂️ {topic}

按分类聚合的主题地图（MOC）。

```dataview
TABLE author AS 作者, status AS 状态, rating AS 评分, owned AS 拥有
FROM #book
WHERE category = this.file.name
SORT status ASC, rating DESC
```"""
    return fm, inner


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
        "购书清单.md": """# 🛒 购书清单（想读但还没入手）

> 汇总 `owned: none` 的书。在书籍笔记里填 `priority: 高/中/低` 即可按优先级排序；
> `price_target` 可记心理价位。需启用 Dataview 的 *JavaScript Queries*。

```dataviewjs
const order = { '高': 0, '中': 1, '低': 2 };
const rows = dv.pages('#book')
  .where(p => (p.owned ?? 'none') === 'none')
  .array()
  .sort((a, b) => {
    const pa = order[a.priority] ?? 9, pb = order[b.priority] ?? 9;
    if (pa !== pb) return pa - pb;
    return String(b.added ?? '').localeCompare(String(a.added ?? ''));
  });
if (rows.length === 0) {
  dv.paragraph('_目前没有 `owned: none` 的书。把想买的书 `owned` 设为 `none` 即可出现在这里。_');
} else {
  dv.table(['书', '作者', '分类', '优先级', '心理价位'],
    rows.map(p => [p.file.link, p.author, p.category,
      p.priority ?? '—', p.price_target ?? '—']));
}
```

## 高优先级速览
```dataview
LIST FROM #book
WHERE (owned = "none" OR owned = none) AND priority = "高"
SORT added DESC
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


def _viz_note_md() -> str:
    """DataviewJS 可视化统计页：评分分布 / 分类占比 / 按年阅读。

    纯前端渲染，需启用 Dataview 的 JavaScript Queries。全程容错，
    数据为空时给出友好提示而非报错。
    """
    return """# 📈 可视化统计

> 本页用 **DataviewJS** 渲染，需在 Dataview 设置中开启 *Enable JavaScript Queries*。
> 图表随笔记 frontmatter（rating / category / status / finished）实时变化。

```dataviewjs
try {
  const pages = dv.pages('#book');
  const bar = (n, max, w = 24) => {
    const len = max > 0 ? Math.round((n / max) * w) : 0;
    return '█'.repeat(len) + '░'.repeat(w - len);
  };

  // —— 评分分布（1–5 星）——
  dv.header(2, '⭐ 我的评分分布');
  const rated = pages.where(p => p.rating != null && p.rating !== '');
  if (rated.length === 0) {
    dv.paragraph('_还没有打分的书。在书籍笔记里填 `rating: 4.5` 即可统计。_');
  } else {
    const buckets = {};
    for (let s = 1; s <= 5; s++) buckets[s] = 0;
    for (const p of rated) {
      const s = Math.round(Number(p.rating));
      if (s >= 1 && s <= 5) buckets[s]++;
    }
    const rmax = Math.max(...Object.values(buckets));
    dv.table(['评分', '数量', ''],
      [5, 4, 3, 2, 1].map(s =>
        ['★'.repeat(s), buckets[s], bar(buckets[s], rmax)]));
  }

  // —— 分类占比 ——
  dv.header(2, '🗂️ 分类占比');
  const byCat = {};
  for (const p of pages) {
    const c = (p.category && String(p.category).trim()) || '未分类';
    byCat[c] = (byCat[c] || 0) + 1;
  }
  const catRows = Object.entries(byCat).sort((a, b) => b[1] - a[1]);
  if (catRows.length === 0) {
    dv.paragraph('_暂无书籍。_');
  } else {
    const total = catRows.reduce((s, [, n]) => s + n, 0);
    const cmax = catRows[0][1];
    dv.table(['分类', '数量', '占比', ''],
      catRows.map(([c, n]) =>
        [c, n, (100 * n / total).toFixed(0) + '%', bar(n, cmax)]));
  }

  // —— 按年阅读（已读）——
  dv.header(2, '📅 各年读完数量');
  const byYear = {};
  for (const p of pages) {
    const f = p.finished;
    if (!f) continue;
    const y = (f.year != null) ? f.year : String(f).slice(0, 4);
    if (!y || String(y).length < 4) continue;
    byYear[y] = (byYear[y] || 0) + 1;
  }
  const yrs = Object.keys(byYear).sort();
  if (yrs.length === 0) {
    dv.paragraph('_还没有带 `finished` 日期的已读书。_');
  } else {
    const ymax = Math.max(...Object.values(byYear));
    dv.table(['年份', '读完', ''],
      yrs.map(y => [y, byYear[y], bar(byYear[y], ymax)]));
  }

  // —— 阅读热力（年 × 月）——
  dv.header(2, '🔥 阅读热力（按读完月份）');
  const grid = {};   // year -> [12] 每月读完数
  for (const p of pages) {
    const f = p.finished;
    if (!f) continue;
    let y, mo;
    if (f.year != null && f.month != null) { y = f.year; mo = f.month; }
    else {
      const s = String(f);
      const mm = s.match(/^(\d{4})-(\d{2})/);
      if (!mm) continue;
      y = +mm[1]; mo = +mm[2];
    }
    if (!grid[y]) grid[y] = new Array(12).fill(0);
    if (mo >= 1 && mo <= 12) grid[y][mo - 1]++;
  }
  const gyears = Object.keys(grid).sort();
  if (gyears.length === 0) {
    dv.paragraph('_暂无可用于热力图的读完日期。_');
  } else {
    let hmax = 1;
    for (const y of gyears) hmax = Math.max(hmax, ...grid[y]);
    // 用 5 档方块表示热度：无=░，其余按比例 ▁▂▃█
    const blocks = ['·', '▂', '▄', '▆', '█'];
    const heat = n => n === 0 ? blocks[0]
      : blocks[Math.min(4, 1 + Math.floor((n - 1) / Math.max(1, hmax) * 3))];
    const months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
    dv.table(['年', ...months, '合计'],
      gyears.map(y => {
        const row = grid[y];
        const cells = row.map(n => n === 0 ? heat(0) : `${heat(n)}${n}`);
        return [y, ...cells, row.reduce((a, b) => a + b, 0)];
      }));
    dv.paragraph('_方块越满代表当月读完越多；数字为当月读完本数。_');
  }
} catch (e) {
  dv.paragraph('⚠️ 渲染失败：' + e.message +
    '（请确认已启用 Dataview 的 JavaScript Queries）');
}
```
"""


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
- [[在读]] · [[已读]] · [[想读(愿望清单)]] · [[购书清单]]
- [[评分排行]] · [[藏书清单]] · [[阅读统计]] · [[可视化统计]]
- [[05-阅读时间线|📅 阅读时间线]] · [[趋势|📈 统计趋势]]

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
    inc = config.incremental
    counts = {"books": 0, "authors": 0, "topics": 0, "dashboards": 0, "misc": 0}

    for d in (DIR_BOOKS, DIR_AUTHORS, DIR_TOPICS, DIR_DASH, DIR_TPL):
        os.makedirs(os.path.join(root, d), exist_ok=True)

    authors, topics = set(), set()

    # 书籍笔记（增量：保护手填 frontmatter 字段 + 手写尾部）
    for note in all_notes:
        b = note.book
        path = os.path.join(root, DIR_BOOKS, f"{_slug(b.title)}.md")
        fm, inner = _book_note_parts(note)
        _write_note(path, fm, inner, TAIL_BOOK, inc)
        counts["books"] += 1
        if b.author:
            authors.add(b.author)
        if b.category:
            topics.add(b.category)

    # 作者中心页（增量：保护「## 关于」手写区）
    for a in sorted(authors):
        fm, inner = _author_note_parts(a)
        _write_note(os.path.join(root, DIR_AUTHORS, f"{_slug(a)}.md"),
                    fm, inner, TAIL_AUTHOR, inc)
        counts["authors"] += 1

    # 主题 MOC（增量：保护「## 主题笔记」手写区）
    for tp in sorted(topics):
        fm, inner = _topic_note_parts(tp)
        _write_note(os.path.join(root, DIR_TOPICS, f"{_slug(tp)}.md"),
                    fm, inner, TAIL_TOPIC, inc)
        counts["topics"] += 1

    # 仪表盘（纯自动，全量覆盖）
    dash = _dashboard_files()
    dash["阅读统计.md"] = _stats_note_md(stat)
    dash["可视化统计.md"] = _viz_note_md()
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

    # 统计快照 + 趋势页（按日期 upsert，累积对比）
    if config.snapshot:
        snap = S.compute_snapshot(all_notes, stat)
        history = S.record_snapshot(root, snap)
        with open(os.path.join(root, S.DIR_SNAP, "趋势.md"), "w",
                  encoding="utf-8") as f:
            f.write(S.trend_page_md(history))
        counts["misc"] += 1

    return counts
