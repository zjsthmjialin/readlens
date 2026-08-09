"""元数据获取器抽象。

不同来源（豆瓣、离线 mock、未来 Google Books 等）实现同一接口，返回
一个可能包含 isbn/cover/publisher/pubdate 的字典（缺项省略）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class MetadataFetcher(ABC):
    """按书名/作者查询书目元数据。"""

    @abstractmethod
    def fetch(self, title: str, author: str = "") -> Dict[str, str]:
        """返回元数据字典，可能含：isbn / cover / publisher / pubdate。

        查询失败或无结果时应返回空字典 `{}`，绝不抛异常（保证增量流程健壮）。
        """
        raise NotImplementedError
