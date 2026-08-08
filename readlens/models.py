"""统一数据模型。

不同平台（微信读书、豆瓣、Kindle…）的原始字段差异很大，适配器负责把它们
归一化成这里的模型，上层的导出 / 报告 / AI 模块只依赖这套统一模型。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Book:
    """一本书的基本信息。"""
    book_id: str
    title: str
    author: str = ""
    cover: str = ""
    category: str = ""
    intro: str = ""
    publisher: str = ""
    rating: Optional[float] = None          # 0-100 归一化评分
    reading_count: Optional[int] = None     # 在读/读过人数
    finished: bool = False                   # 是否读完
    progress: Optional[int] = None           # 阅读进度百分比
    source: str = "manual"                   # 数据来源：weread|manual|douban|kindle
    owned: str = "none"                       # 拥有情况：physical|digital|none

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Highlight:
    """一条划线（高亮原文）。"""
    highlight_id: str
    book_id: str
    text: str
    chapter_title: str = ""
    chapter_idx: int = 0
    create_time: Optional[int] = None       # Unix 时间戳
    color: Optional[int] = None
    popular_count: Optional[int] = None      # 热门划线时的划线人数

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Thought:
    """一条个人想法 / 点评（对应后端 review）。"""
    review_id: str
    book_id: str
    content: str
    abstract: str = ""                       # 关联的划线原文（如有）
    chapter_title: str = ""
    star: int = -1                           # 0-5，-1 表示无评分
    is_book_review: bool = False             # 是否整本书评
    create_time: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Note:
    """单本书的完整笔记聚合（划线 + 想法）。"""
    book: Book
    highlights: List[Highlight] = field(default_factory=list)
    thoughts: List[Thought] = field(default_factory=list)
    bookmark_count: int = 0                  # 书签数量（仅统计，无内容）

    @property
    def total_count(self) -> int:
        # 与原项目统计口径一致：reviewCount + noteCount + bookmarkCount
        return len(self.highlights) + len(self.thoughts) + self.bookmark_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "book": self.book.to_dict(),
            "highlights": [h.to_dict() for h in self.highlights],
            "thoughts": [t.to_dict() for t in self.thoughts],
            "bookmark_count": self.bookmark_count,
            "total_count": self.total_count,
        }


@dataclass
class CategoryPref:
    """偏好分类。"""
    title: str
    reading_time: int = 0                     # 秒
    reading_count: int = 0
    parent_title: str = ""


@dataclass
class AuthorPref:
    name: str
    count: int = 0
    read_time: str = ""                       # 平台原始格式化字符串


@dataclass
class ReadStat:
    """一个统计周期内的阅读数据。"""
    mode: str = "monthly"                     # weekly | monthly | annually | overall
    base_time: int = 0
    total_read_time: int = 0                  # 秒
    read_days: int = 0
    day_average: int = 0                      # 秒
    compare: Optional[float] = None           # 与上期对比比例
    read_longest: List[Dict[str, Any]] = field(default_factory=list)  # {book, read_time}
    prefer_category: List[CategoryPref] = field(default_factory=list)
    prefer_author: List[AuthorPref] = field(default_factory=list)
    prefer_time: List[int] = field(default_factory=list)              # 24 段，秒
    read_stat: List[Dict[str, str]] = field(default_factory=list)     # 读过/读完/笔记...
    daily_read_times: Dict[str, int] = field(default_factory=dict)    # 日期戳 -> 秒

    @property
    def total_hours(self) -> float:
        return round(self.total_read_time / 3600, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_hours"] = self.total_hours
        return d
