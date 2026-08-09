"""书目元数据增强。

用一个可插拔的 `MetadataFetcher` 给缺字段的书补全 isbn / cover / publisher / pubdate。
**只填空、不覆盖**已有值——与 vault 增量更新「保护手填字段」的理念一致。

来源：
- `mock`（默认，离线可跑）：确定性预置数据。
- `douban`（在线，best-effort）：豆瓣 suggest，失败即降级。
"""
from __future__ import annotations

from typing import List

from ..models import Book, Note
from .base import MetadataFetcher
from .mock import MockFetcher

# 会被增强填充的字段（仅当 book 上对应值为空时）
_FIELDS = ("isbn", "cover", "publisher", "pubdate")


def get_fetcher(source: str = "mock", cache_path: str = None) -> MetadataFetcher:
    """按来源名返回一个元数据获取器。未知/离线一律回落到 mock。"""
    if source == "douban":
        from .douban import DoubanFetcher
        return DoubanFetcher(cache_path=cache_path)
    return MockFetcher()


def enrich_book(book: Book, fetcher: MetadataFetcher) -> List[str]:
    """给单本书补全缺失字段，返回被填充的字段名列表。"""
    missing = [f for f in _FIELDS if not (getattr(book, f, "") or "").strip()]
    if not missing:
        return []
    data = fetcher.fetch(book.title, book.author) or {}
    filled = []
    for f in missing:
        val = (data.get(f) or "").strip()
        if val:
            setattr(book, f, val)
            filled.append(f)
    return filled


def enrich_notes(notes: List[Note], fetcher: MetadataFetcher) -> dict:
    """批量增强，返回统计：{'books_touched', 'fields_filled'}。"""
    books_touched, fields_filled = 0, 0
    for n in notes:
        filled = enrich_book(n.book, fetcher)
        if filled:
            books_touched += 1
            fields_filled += len(filled)
    return {"books_touched": books_touched, "fields_filled": fields_filled}


__all__ = ["MetadataFetcher", "MockFetcher", "get_fetcher",
           "enrich_book", "enrich_notes"]
