"""周期报告摘要（Markdown）。

把一个统计周期的 ReadStat 渲染成一张适合放进 Obsidian 知识库的 markdown 报告，
供 `readlens sync` 定时生成周报/月报用。纯离线可跑；可选带入 AI 小结。
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..models import ReadStat

_MODE_LABEL = {"weekly": "周报", "monthly": "月报",
               "annually": "年报", "overall": "总报"}


def period_slug(mode: str, when: Optional[date] = None) -> str:
    """生成该周期的文件名片段，用于幂等命名（同周期覆盖同一文件）。"""
    when = when or date.today()
    if mode == "weekly":
        y, w, _ = when.isocalendar()
        return f"周报-{y}-W{w:02d}"
    if mode == "monthly":
        return f"月报-{when:%Y-%m}"
    if mode == "annually":
        return f"年报-{when:%Y}"
    return f"总报-{when:%Y%m%d}"


def _fmt_hms(seconds: int) -> str:
    seconds = int(seconds or 0)
    h, m = seconds // 3600, (seconds % 3600) // 60
    if h and m:
        return f"{h} 小时 {m} 分钟"
    if h:
        return f"{h} 小时"
    return f"{m} 分钟"


def render_digest_md(stat: ReadStat, mode: str,
                     ai_summary: Optional[str] = None,
                     when: Optional[date] = None) -> str:
    """渲染一份周期报告的 markdown。"""
    when = when or date.today()
    label = _MODE_LABEL.get(mode, "报告")
    lines = [
        f"# 📮 阅读{label}（{period_slug(mode, when).split('-', 1)[1]}）",
        "",
        f"> 由 ReadLens 于 {when.isoformat()} 自动生成。数据周期：{mode}。",
        "",
        "## 概览",
        f"- 阅读时长：**{_fmt_hms(stat.total_read_time)}**（{stat.total_hours} 小时）",
        f"- 阅读天数：**{stat.read_days}** 天",
        f"- 日均：{_fmt_hms(stat.day_average)}",
    ]
    if stat.compare is not None:
        arrow = "📈 增长" if stat.compare > 0 else ("📉 下降" if stat.compare < 0 else "持平")
        lines.append(f"- 与上期对比：{arrow} {abs(round(stat.compare * 100))}%")
    lines.append("")

    if stat.read_longest:
        lines += ["## 读得最多", ""]
        for i, b in enumerate(stat.read_longest[:5], 1):
            t = _fmt_hms(b.get("read_time", 0))
            author = f" — {b['author']}" if b.get("author") else ""
            lines.append(f"{i}. 《{b.get('title','')}》{author}（{t}）")
        lines.append("")

    if stat.prefer_category:
        cats = "、".join(c.title for c in stat.prefer_category[:5] if c.title)
        if cats:
            lines += [f"## 偏好分类", "", cats, ""]
    if stat.prefer_author:
        aus = "、".join(a.name for a in stat.prefer_author[:5] if a.name)
        if aus:
            lines += [f"## 偏好作者", "", aus, ""]

    if ai_summary:
        lines += ["## 小结", "", ai_summary.strip(), ""]

    return "\n".join(lines).rstrip() + "\n"
