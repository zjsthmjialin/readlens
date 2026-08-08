"""用 matplotlib 生成报告图表，输出 PNG 文件路径。"""
from __future__ import annotations

import os
from typing import List

import matplotlib
matplotlib.use("Agg")  # 无界面后端
import matplotlib.pyplot as plt
from matplotlib import font_manager

from ..models import ReadStat


def _setup_cjk_font():
    """尽量选一个可用的中文字体，避免图表中文乱码。"""
    candidates = ["PingFang SC", "Heiti SC", "Songti SC", "STHeiti",
                  "Microsoft YaHei", "SimHei", "WenQuanYi Zen Hei",
                  "Noto Sans CJK SC", "Noto Sans CJK JP", "Arial Unicode MS"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for c in candidates:
        if c in available:
            plt.rcParams["font.sans-serif"] = [c]
            break
    plt.rcParams["axes.unicode_minus"] = False


_setup_cjk_font()


def chart_daily_trend(stat: ReadStat, out_path: str, color: str = "#07c160") -> str:
    """每日阅读时长趋势（分钟）。"""
    items = sorted(stat.daily_read_times.items())
    if not items:
        return ""
    xs = list(range(len(items)))
    ys = [v / 60 for _, v in items]  # 分钟
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.fill_between(xs, ys, color=color, alpha=0.25)
    ax.plot(xs, ys, color=color, linewidth=2)
    ax.set_title("每日阅读时长趋势（分钟）")
    ax.set_xlabel("天")
    ax.set_ylabel("分钟")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def chart_category(stat: ReadStat, out_path: str, color: str = "#07c160") -> str:
    """偏好分类占比（环形图）。"""
    cats = stat.prefer_category
    if not cats:
        return ""
    labels = [c.title for c in cats]
    sizes = [c.reading_time for c in cats]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90,
           wedgeprops=dict(width=0.42), pctdistance=0.78)
    ax.set_title("阅读分类分布")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def chart_time_of_day(stat: ReadStat, out_path: str, color: str = "#07c160") -> str:
    """24 小时阅读时段分布。prefer_time 从 6 点开始（见 readdata.md）。"""
    pt = stat.prefer_time
    if not pt or len(pt) < 24:
        return ""
    hours = [(6 + i) % 24 for i in range(24)]
    order = sorted(range(24), key=lambda i: hours[i])
    labels = [f"{hours[i]:02d}" for i in order]
    values = [pt[i] / 60 for i in order]  # 分钟
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.bar(labels, values, color=color, alpha=0.85)
    ax.set_title("24 小时阅读时段分布（分钟）")
    ax.set_xlabel("小时")
    ax.set_ylabel("分钟")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def chart_top_books(stat: ReadStat, out_path: str, color: str = "#07c160") -> str:
    """读得最多的书（横向条形图，分钟）。"""
    books = stat.read_longest
    if not books:
        return ""
    books = list(reversed(books))
    labels = [b["title"] for b in books]
    values = [b["read_time"] / 60 for b in books]
    fig, ax = plt.subplots(figsize=(8, max(3, len(books) * 0.6)))
    ax.barh(labels, values, color=color, alpha=0.85)
    ax.set_title("读得最多的书（分钟）")
    ax.set_xlabel("分钟")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def generate_all(stat: ReadStat, out_dir: str, color: str = "#07c160") -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for fn, name in [
        (chart_daily_trend, "daily_trend.png"),
        (chart_category, "category.png"),
        (chart_time_of_day, "time_of_day.png"),
        (chart_top_books, "top_books.png"),
    ]:
        p = fn(stat, os.path.join(out_dir, name), color)
        if p:
            paths.append(p)
    return paths
