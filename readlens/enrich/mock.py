"""离线元数据源（mock）。

无网络时用的确定性数据，保证「离线可跑」硬约束与可测试性。
为示例书目预置了真实的出版信息；未知书目返回空字典（不臆造封面）。
"""
from __future__ import annotations

from typing import Dict

from .base import MetadataFetcher

# 预置的真实出版信息（按书名匹配；cover 留空——离线不臆造封面 URL）
_CANNED: Dict[str, Dict[str, str]] = {
    "三体": {"isbn": "9787536692930", "publisher": "重庆出版社", "pubdate": "2008"},
    "人类简史": {"isbn": "9787508647357", "publisher": "中信出版社", "pubdate": "2014"},
    "百年孤独": {"isbn": "9787544253994", "publisher": "南海出版公司", "pubdate": "2011"},
    "置身事内": {"isbn": "9787208171336", "publisher": "上海人民出版社", "pubdate": "2021"},
    "沙丘": {"isbn": "9787539966755", "publisher": "江苏凤凰文艺出版社", "pubdate": "2017"},
}


class MockFetcher(MetadataFetcher):
    """离线示例元数据源。"""

    def fetch(self, title: str, author: str = "") -> Dict[str, str]:
        return dict(_CANNED.get((title or "").strip(), {}))
