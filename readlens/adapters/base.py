"""平台适配层抽象基类。

这是 ReadLens 相对原项目最关键的延展点：把「阅读平台」抽象成统一接口，
上层导出 / 报告 / AI 模块都只依赖这套接口。要复刻到新平台（豆瓣读书、
Kindle、微信收藏、Readwise 等），只需实现一个新的 ReadingPlatform 子类，
把该平台的原始数据映射到 readlens.models 里的统一模型即可。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import Book, Note, ReadStat, Highlight


class ReadingPlatform(ABC):
    """一个阅读平台的统一能力接口。"""

    name: str = "base"

    # ---- 搜索与书籍 ----
    @abstractmethod
    def search(self, keyword: str, scope: str = "book", limit: int = 15) -> List[Book]:
        """搜索书籍。scope: book|all|audio|author|fulltext 等（各平台自行映射）。"""

    @abstractmethod
    def book_info(self, book_id: str) -> Book:
        """获取单本书详情。"""

    # ---- 书架 ----
    @abstractmethod
    def shelf(self) -> List[Book]:
        """获取书架书目。"""

    # ---- 笔记 ----
    @abstractmethod
    def notebooks(self) -> List[Note]:
        """获取所有有笔记的书（概览，可能不含完整内容）。"""

    @abstractmethod
    def book_notes(self, book_id: str) -> Note:
        """获取单本书的完整笔记（划线 + 想法）。"""

    def popular_highlights(self, book_id: str) -> List[Highlight]:
        """热门划线。默认未实现，平台可选覆盖。"""
        return []

    # ---- 阅读统计 ----
    @abstractmethod
    def read_stat(self, mode: str = "monthly", base_time: int = 0) -> ReadStat:
        """获取阅读统计。mode: weekly|monthly|annually|overall。"""

    # ---- 可选的写入能力（原项目未提供，此处作为延展接口） ----
    def add_to_shelf(self, book_id: str) -> bool:
        raise NotImplementedError(f"{self.name} 暂不支持加入书架写操作")

    def create_thought(self, book_id: str, content: str,
                       abstract: str = "") -> Optional[str]:
        raise NotImplementedError(f"{self.name} 暂不支持写入想法")
