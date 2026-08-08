"""读书报告生成器：把 ReadStat 组织成月度/年度报告（数据 + 图表 + HTML）。"""
from __future__ import annotations

import os
from typing import Dict, Any, Optional

from ..models import ReadStat
from . import charts

_MODE_CN = {"weekly": "本周", "monthly": "月度", "annually": "年度", "overall": "全部"}


def _fmt_duration(seconds: int) -> str:
    h, m = seconds // 3600, (seconds % 3600) // 60
    if h and m:
        return f"{h} 小时 {m} 分钟"
    if h:
        return f"{h} 小时"
    return f"{m} 分钟"


def build_report(stat: ReadStat) -> Dict[str, Any]:
    """把统计数据整理成报告字典（供 HTML 渲染或 AI 二次加工）。"""
    period = _MODE_CN.get(stat.mode, stat.mode)
    compare_txt = None
    if stat.compare is not None:
        pct = round(stat.compare * 100)
        compare_txt = f"较上期{'增长' if pct >= 0 else '下降'} {abs(pct)}%"
    top_book = stat.read_longest[0]["title"] if stat.read_longest else "—"
    top_cat = stat.prefer_category[0].title if stat.prefer_category else "—"
    return {
        "period": period,
        "mode": stat.mode,
        "total_read": _fmt_duration(stat.total_read_time),
        "total_hours": stat.total_hours,
        "read_days": stat.read_days,
        "day_average": _fmt_duration(stat.day_average),
        "compare": compare_txt,
        "top_book": top_book,
        "top_category": top_cat,
        "read_longest": stat.read_longest,
        "prefer_category": [(c.title, _fmt_duration(c.reading_time)) for c in stat.prefer_category],
        "prefer_author": [(a.name, a.read_time) for a in stat.prefer_author],
        "read_stat": stat.read_stat,
    }


_HTML_TMPL = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>{period}阅读报告 · ReadLens</title>
<style>
 body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
   max-width:860px;margin:0 auto;padding:32px 20px;color:#1a1a1a;background:#fafafa;}}
 h1{{font-size:28px;}} h2{{margin-top:36px;border-left:4px solid {color};padding-left:10px;}}
 .cards{{display:flex;flex-wrap:wrap;gap:16px;margin:20px 0;}}
 .card{{flex:1;min-width:140px;background:#fff;border-radius:12px;padding:18px;
   box-shadow:0 1px 4px rgba(0,0,0,.06);}}
 .card .num{{font-size:26px;font-weight:700;color:{color};}}
 .card .lbl{{color:#888;font-size:13px;margin-top:4px;}}
 img{{max-width:100%;border-radius:10px;background:#fff;margin:8px 0;}}
 table{{width:100%;border-collapse:collapse;margin:10px 0;background:#fff;}}
 td,th{{padding:8px 12px;border-bottom:1px solid #eee;text-align:left;font-size:14px;}}
 .ai{{background:#fff;border-radius:12px;padding:18px 22px;border:1px solid #eee;
   line-height:1.7;white-space:pre-wrap;}}
 footer{{margin-top:40px;color:#aaa;font-size:12px;text-align:center;}}
</style></head><body>
<h1>📖 {period}阅读报告</h1>
<div class="cards">
 <div class="card"><div class="num">{total_hours}h</div><div class="lbl">总阅读时长</div></div>
 <div class="card"><div class="num">{read_days}</div><div class="lbl">阅读天数</div></div>
 <div class="card"><div class="num">{day_average}</div><div class="lbl">日均</div></div>
 <div class="card"><div class="num">{top_book}</div><div class="lbl">读得最多</div></div>
</div>
{compare_block}
{charts_block}
<h2>读书排行</h2>
{ranking_table}
<h2>偏好分析</h2>
{prefer_block}
{ai_block}
<footer>由 ReadLens 生成 · 脱胎于 Tencent/WeChatReading Skills</footer>
</body></html>
"""


def render_html_report(stat: ReadStat, out_dir: str,
                       ai_summary: Optional[str] = None,
                       color: str = "#07c160") -> str:
    """渲染 HTML 报告（含图表），返回 HTML 文件路径。"""
    os.makedirs(out_dir, exist_ok=True)
    rep = build_report(stat)
    chart_dir = os.path.join(out_dir, "charts")
    chart_paths = charts.generate_all(stat, chart_dir, color)

    charts_block = "<h2>数据可视化</h2>\n" + "\n".join(
        f'<img src="charts/{os.path.basename(p)}" alt="chart">' for p in chart_paths)

    ranking = "<table><tr><th>#</th><th>书名</th><th>作者</th><th>时长</th></tr>"
    for i, b in enumerate(rep["read_longest"], 1):
        ranking += (f"<tr><td>{i}</td><td>{b['title']}</td>"
                    f"<td>{b.get('author','')}</td><td>{_fmt_duration(b['read_time'])}</td></tr>")
    ranking += "</table>"

    prefer = "<table><tr><th>分类</th><th>时长</th></tr>"
    for name, dur in rep["prefer_category"]:
        prefer += f"<tr><td>{name}</td><td>{dur}</td></tr>"
    prefer += "</table>"
    if rep["prefer_author"]:
        prefer += "<p><b>偏好作者：</b>" + "、".join(
            f"{n}（{d}）" for n, d in rep["prefer_author"]) + "</p>"

    compare_block = f'<p style="color:{color};font-weight:600;">↗ {rep["compare"]}</p>' \
        if rep["compare"] else ""
    ai_block = f'<h2>🤖 AI 读书总结</h2><div class="ai">{ai_summary}</div>' \
        if ai_summary else ""

    html = _HTML_TMPL.format(
        period=rep["period"], color=color, total_hours=rep["total_hours"],
        read_days=rep["read_days"], day_average=rep["day_average"],
        top_book=rep["top_book"], compare_block=compare_block,
        charts_block=charts_block, ranking_table=ranking,
        prefer_block=prefer, ai_block=ai_block)

    path = os.path.join(out_dir, f"report_{stat.mode}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
