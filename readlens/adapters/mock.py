"""离线 Mock 适配器：内置示例数据，无需 API Key 即可跑通全流程。

也是复刻新平台时最好的参照实现——展示了如何把原始数据映射成统一模型。
"""
from __future__ import annotations

import time
from typing import List, Optional

from ..models import (Book, Note, Highlight, Thought, ReadStat,
                      CategoryPref, AuthorPref)
from .base import ReadingPlatform

_NOW = int(time.time())
_DAY = 86400


def _mk_book(bid, title, author, cat, rating, finished=False, progress=100):
    return Book(book_id=bid, title=title, author=author, category=cat,
                rating=rating, finished=finished, progress=progress,
                source="weread", owned="digital",
                intro=f"《{title}》是 {author} 的代表作之一。")


_BOOKS = [
    _mk_book("b_santi", "三体", "刘慈欣", "科幻", 92, True),
    _mk_book("b_sapiens", "人类简史", "尤瓦尔·赫拉利", "历史", 89, True),
    _mk_book("b_deepwork", "深度工作", "卡尔·纽波特", "自我提升", 85, True),
    _mk_book("b_thinking", "思考,快与慢", "丹尼尔·卡尼曼", "心理学", 88, False, 62),
    _mk_book("b_poor", "贫穷的本质", "班纳吉/迪弗洛", "经济学", 86, False, 40),
]

_NOTES = {
    "b_santi": Note(
        book=_BOOKS[0], bookmark_count=3,
        highlights=[
            Highlight("h1", "b_santi", "弱小和无知不是生存的障碍，傲慢才是。",
                      "第二部 黑暗森林", 12, _NOW - 30 * _DAY, popular_count=128340),
            Highlight("h2", "b_santi", "给岁月以文明，而不是给文明以岁月。",
                      "第三部 死神永生", 20, _NOW - 28 * _DAY, popular_count=98211),
            Highlight("h3", "b_santi", "在宇宙中，生存是文明的第一需要。",
                      "第二部 黑暗森林", 13, _NOW - 25 * _DAY, popular_count=76500),
        ],
        thoughts=[
            Thought("t1", "b_santi", "黑暗森林法则把囚徒困境放大到宇宙尺度，"
                    "读起来后背发凉。", abstract="在宇宙中，生存是文明的第一需要。",
                    chapter_title="第二部 黑暗森林", star=-1, create_time=_NOW - 25 * _DAY),
            Thought("t2", "b_santi", "整本书对'文明与时间'的取舍讨论非常震撼，五星。",
                    is_book_review=True, star=5, create_time=_NOW - 20 * _DAY),
        ]),
    "b_sapiens": Note(
        book=_BOOKS[1], bookmark_count=2,
        highlights=[
            Highlight("h4", "b_sapiens", "我们以为自己驯化了小麦，其实是小麦驯化了我们。",
                      "第二部 农业革命", 5, _NOW - 60 * _DAY, popular_count=54021),
            Highlight("h5", "b_sapiens", "金钱是有史以来最普遍也最有效的互信系统。",
                      "第三部 人类的融合统一", 9, _NOW - 58 * _DAY, popular_count=43120),
        ],
        thoughts=[
            Thought("t3", "b_sapiens", "'想象的共同体'这个概念可以解释货币、国家、公司。",
                    abstract="金钱是有史以来最普遍也最有效的互信系统。",
                    chapter_title="第三部 人类的融合统一", create_time=_NOW - 57 * _DAY),
        ]),
    "b_deepwork": Note(
        book=_BOOKS[2], bookmark_count=1,
        highlights=[
            Highlight("h6", "b_deepwork", "你对世界的体验，源自你所关注的事物。",
                      "第一部分 深度工作是有价值的", 2, _NOW - 15 * _DAY, popular_count=32100),
        ],
        thoughts=[
            Thought("t4", "b_deepwork", "决定把手机放到另一个房间，实测专注时长翻倍。",
                    create_time=_NOW - 14 * _DAY),
        ]),
    "b_thinking": Note(
        book=_BOOKS[3], bookmark_count=0,
        highlights=[
            Highlight("h7", "b_thinking", "系统1快而直觉，系统2慢而理性；我们高估了系统2。",
                      "第一部分 两个系统", 1, _NOW - 5 * _DAY, popular_count=21000),
        ],
        thoughts=[]),
    "b_poor": Note(book=_BOOKS[4], bookmark_count=0, highlights=[], thoughts=[]),
}


class MockPlatform(ReadingPlatform):
    name = "mock"

    def search(self, keyword: str, scope: str = "book", limit: int = 15) -> List[Book]:
        kw = keyword.lower()
        hits = [b for b in _BOOKS if kw in b.title.lower() or kw in b.author.lower()]
        return (hits or _BOOKS)[:limit]

    def book_info(self, book_id: str) -> Book:
        for b in _BOOKS:
            if b.book_id == book_id:
                return b
        raise KeyError(f"未找到书籍 {book_id}")

    def shelf(self) -> List[Book]:
        return list(_BOOKS)

    def notebooks(self) -> List[Note]:
        return [n for n in _NOTES.values() if n.total_count > 0]

    def book_notes(self, book_id: str) -> Note:
        if book_id not in _NOTES:
            raise KeyError(f"《{book_id}》没有笔记")
        return _NOTES[book_id]

    def popular_highlights(self, book_id: str) -> List[Highlight]:
        note = _NOTES.get(book_id)
        if not note:
            return []
        return sorted(note.highlights, key=lambda h: h.popular_count or 0, reverse=True)

    def read_stat(self, mode: str = "monthly", base_time: int = 0) -> ReadStat:
        # 一份贴近真实结构的示例统计
        scale = {"weekly": 0.25, "monthly": 1, "annually": 11, "overall": 40}.get(mode, 1)
        total = int(48000 * scale)  # 秒
        days = int(22 * min(scale, 1) if scale <= 1 else 250 * (scale / 11))
        daily = {}
        for i in range(30):
            daily[str(_NOW - i * _DAY)] = int(1600 * (0.5 + (i % 5) / 5))
        return ReadStat(
            mode=mode, base_time=base_time or _NOW, total_read_time=total,
            read_days=max(days, 1), day_average=int(total / max(days, 1)),
            compare=0.18 if mode in ("weekly", "monthly") else None,
            daily_read_times=daily if mode in ("monthly", "annually") else {},
            read_longest=[
                {"title": "三体", "author": "刘慈欣", "read_time": int(total * 0.34)},
                {"title": "人类简史", "author": "尤瓦尔·赫拉利", "read_time": int(total * 0.26)},
                {"title": "深度工作", "author": "卡尔·纽波特", "read_time": int(total * 0.18)},
                {"title": "思考,快与慢", "author": "丹尼尔·卡尼曼", "read_time": int(total * 0.14)},
                {"title": "贫穷的本质", "author": "班纳吉/迪弗洛", "read_time": int(total * 0.08)},
            ],
            prefer_category=[
                CategoryPref("科幻", int(total * 0.34), 1, "文学"),
                CategoryPref("历史", int(total * 0.26), 1, "人文社科"),
                CategoryPref("自我提升", int(total * 0.18), 1, "个人成长"),
                CategoryPref("心理学", int(total * 0.14), 1, "人文社科"),
                CategoryPref("经济学", int(total * 0.08), 1, "人文社科"),
            ],
            prefer_author=[
                AuthorPref("刘慈欣", 1, "4小时32分钟"),
                AuthorPref("尤瓦尔·赫拉利", 1, "3小时28分钟"),
            ],
            # 24 段，从 6 点开始（与 readdata.md 口径一致）；夜间偏多
            prefer_time=[int(t) for t in (
                200, 300, 400, 500, 600, 700, 900, 1100, 1300, 1200, 1000, 800,
                700, 600, 900, 1400, 2100, 2600, 2400, 1800, 1200, 800, 500, 300)],
            read_stat=[
                {"stat": "读过", "counts": "5本"},
                {"stat": "读完", "counts": "3本"},
                {"stat": "阅读", "counts": f"{max(days,1)}天"},
                {"stat": "笔记", "counts": "13条"},
            ],
        )
