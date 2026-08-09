"""阅读统计快照与趋势。

每次生成 vault 时落一份带日期的统计快照到 `06-统计快照/history.json`
（按日期 upsert，持久累积、不被覆盖），并据此生成一张趋势页 `趋势.md`
（静态渲染，含与上期对比）。让「知识库随时间可对比」。
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Dict, List, Optional

from ..models import Note, ReadStat

DIR_SNAP = "06-统计快照"


def _status(b) -> str:
    if b.finished:
        return "已读"
    if b.progress and b.progress > 0:
        return "在读"
    return "想读"


def _owned(b) -> str:
    if b.owned and b.owned != "none":
        return b.owned
    return "digital" if b.source == "weread" else "none"


def compute_snapshot(notes: List[Note], stat: Optional[ReadStat],
                     day: Optional[str] = None) -> Dict:
    """从书籍笔记 + 阅读统计计算一份快照字典。"""
    day = day or date.today().isoformat()
    snap = {
        "date": day, "total": len(notes),
        "已读": 0, "在读": 0, "想读": 0,
        "owned_physical": 0, "owned_digital": 0, "owned_none": 0,
        "avg_rating": None, "total_hours": None, "read_days": None,
    }
    ratings = []
    for n in notes:
        b = n.book
        snap[_status(b)] += 1
        o = _owned(b)
        snap["owned_" + o] = snap.get("owned_" + o, 0) + 1
        for t in n.thoughts:
            if getattr(t, "is_book_review", False) and t.star and t.star > 0:
                ratings.append(float(t.star))
                break
    if ratings:
        snap["avg_rating"] = round(sum(ratings) / len(ratings), 2)
    if stat is not None:
        snap["total_hours"] = stat.total_hours
        snap["read_days"] = stat.read_days
    return snap


def record_snapshot(vault_dir: str, snap: Dict) -> List[Dict]:
    """把快照按日期 upsert 进 history.json，返回完整历史（按日期升序）。"""
    d = os.path.join(vault_dir, DIR_SNAP)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "history.json")
    history: List[Dict] = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history = [h for h in history if h.get("date") != snap["date"]]
    history.append(snap)
    history.sort(key=lambda h: h.get("date", ""))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)
    return history


def _delta(cur, prev) -> str:
    if cur is None or prev is None:
        return ""
    d = round(cur - prev, 2)
    if d > 0:
        return f" (+{d})"
    if d < 0:
        return f" ({d})"
    return " (±0)"


def trend_page_md(history: List[Dict]) -> str:
    """据历史快照渲染趋势页（静态表格，最新在上，含与上期对比）。"""
    head = "# 📈 统计趋势\n\n> 每次生成知识库自动落一份当日快照，累计对比。数据源：`06-统计快照/history.json`。\n\n"
    if not history:
        return head + "_还没有快照。重新运行 `readlens vault` 即可记录第一份。_\n"
    rows = list(reversed(history))          # 最新在上
    prev_by_date = {h["date"]: history[i - 1] if i > 0 else None
                    for i, h in enumerate(history)}
    lines = ["| 日期 | 总数 | 已读 | 在读 | 想读 | 待购(none) | 平均分 | 阅读时长(h) |",
             "|------|------|------|------|------|-----------|--------|-------------|"]
    for h in rows:
        prev = prev_by_date.get(h["date"])
        def cell(key):
            v = h.get(key)
            p = prev.get(key) if prev else None
            base = "—" if v is None else v
            return f"{base}{_delta(v, p) if isinstance(v, (int, float)) else ''}"
        lines.append(
            f"| {h['date']} | {h.get('total','—')} | {cell('已读')} | {cell('在读')} | "
            f"{cell('想读')} | {h.get('owned_none','—')} | "
            f"{'—' if h.get('avg_rating') is None else h['avg_rating']} | "
            f"{'—' if h.get('total_hours') is None else h['total_hours']} |")
    return head + "\n".join(lines) + "\n"
