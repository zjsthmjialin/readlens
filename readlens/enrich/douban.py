"""豆瓣元数据源（在线，best-effort）。

用豆瓣的轻量 suggest 接口按书名查询，补全 cover / pubdate（年份）。
任何网络/解析错误都降级为返回空字典，绝不影响主流程。带本地 JSON 缓存。

注意：豆瓣接口无官方保障、可能限流/改动；本模块仅尽力而为，失败即降级到不补全。
ISBN 需要抓取详情页，稳定性差，这里不做（保持健壮）；如需 ISBN 建议用离线预置或人工补。
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional

from .base import MetadataFetcher

_SUGGEST = "https://book.douban.com/j/subject_suggest?q={q}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ReadLens/0.2)"}


class DoubanFetcher(MetadataFetcher):
    def __init__(self, cache_path: Optional[str] = None, timeout: float = 6.0):
        self.cache_path = cache_path
        self.timeout = timeout
        self._cache: Dict[str, Dict[str, str]] = {}
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        if not self.cache_path:
            return
        try:
            os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def fetch(self, title: str, author: str = "") -> Dict[str, str]:
        key = (title or "").strip()
        if not key:
            return {}
        if key in self._cache:
            return dict(self._cache[key])

        result: Dict[str, str] = {}
        try:
            import requests  # 延迟导入，缺依赖也不影响离线路径
            from urllib.parse import quote
            resp = requests.get(_SUGGEST.format(q=quote(key)),
                                headers=_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            items = resp.json()
            best = None
            for it in items:
                if it.get("type") == "b" and it.get("title"):
                    best = it
                    break
            if best:
                if best.get("pic"):
                    result["cover"] = best["pic"]
                # title 里常含年份，如「三体 (2008)」→ 抽出年份
                m = re.search(r"(19|20)\d{2}", best.get("year") or best.get("title") or "")
                if m:
                    result["pubdate"] = m.group(0)
        except Exception:
            result = {}   # 网络/依赖/解析任何问题都降级

        self._cache[key] = result
        self._save_cache()
        return dict(result)
