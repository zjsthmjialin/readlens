"""微信读书平台适配器。

按 Tencent/WeChatReading Skills 描述的网关协议实现：所有请求 POST 到网关，
body 里业务参数平铺在顶层，与 api_name / skill_version 同级；API Key 通过
Authorization 头注入。

注意：真实调用需要有效的 WEREAD_API_KEY；无 Key 时请使用 mock 适配器体验。
本适配器负责把 WeRead 原始回包映射为 readlens.models 的统一模型。
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from ..models import Book, Note, Highlight, Thought, ReadStat, CategoryPref, AuthorPref
from .base import ReadingPlatform

# ReadLens 的 scope 语义 -> WeRead scope 数值（见 search.md）
_SCOPE_MAP = {
    "all": 0, "book": 10, "webnovel": 16, "audio": 14,
    "author": 6, "fulltext": 12, "booklist": 13,
}


def _pubyear(publish_time) -> str:
    """把 /book/info 的 publishTime 归一为出版年份字符串（尽力而为）。"""
    if not publish_time:
        return ""
    s = str(publish_time)
    # 形如 "2008-01-01" / "2008年"
    import re
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        return m.group(0)
    # 可能是 Unix 时间戳
    try:
        from datetime import datetime
        return datetime.fromtimestamp(int(publish_time)).strftime("%Y")
    except Exception:
        return ""


class WeReadPlatform(ReadingPlatform):
    name = "weread"

    def __init__(self, base_url: str, api_key: Optional[str],
                 skill_version: str = "1.0.3", timeout: int = 20):
        if requests is None:
            raise RuntimeError("需要安装 requests 才能使用 WeRead 适配器")
        if not api_key:
            raise ValueError(
                "缺少 WEREAD_API_KEY。请设置环境变量或改用 platform: mock 体验。")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.skill_version = skill_version
        self.timeout = timeout

    # ---- 底层网关调用 ----
    def _call(self, api_name: str, **params) -> Dict[str, Any]:
        body = {"api_name": api_name, "skill_version": self.skill_version}
        # 业务参数平铺在顶层（与官方 SDK 一致：api_name/skill_version + 平铺参数）
        body.update({k: v for k, v in params.items() if v is not None})
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(self.base_url, json=body,
                             headers=headers, timeout=self.timeout)
        text = resp.text or ""
        if resp.status_code != 200:
            raise RuntimeError(
                f"微信读书网关 HTTP {resp.status_code}（api_name={api_name}）。"
                f"响应体前 300 字：{text[:300]!r}")
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(
                f"微信读书网关返回非 JSON（HTTP 200, api_name={api_name}）。"
                f"响应体前 300 字：{text[:300]!r}。"
                "常见原因：API Key 无效/过期/未正确设置，或网络被代理拦截。"
                "可先运行 `readlens weread-check` 单独验证鉴权。")
        # 官方约定：errcode 非 0 即业务错误
        if isinstance(data, dict) and data.get("errcode") not in (None, 0):
            raise RuntimeError(
                f"微信读书网关错误 errcode={data.get('errcode')}"
                f"，errmsg={data.get('errmsg')}（api_name={api_name}）")
        return data

    # ---- 搜索与书籍 ----
    def search(self, keyword: str, scope: str = "book", limit: int = 15) -> List[Book]:
        scope_val = _SCOPE_MAP.get(scope, 10)
        data = self._call("/store/search", keyword=keyword, scope=scope_val)
        books: List[Book] = []
        for group in data.get("results", []):
            for item in group.get("books", [])[:limit]:
                info = item.get("bookInfo", {})
                books.append(Book(
                    book_id=info.get("bookId", ""),
                    title=info.get("title", ""),
                    author=info.get("author", ""),
                    cover=info.get("cover", ""),
                    category=info.get("category", ""),
                    intro=info.get("intro", ""),
                    publisher=info.get("publisher", ""),
                    rating=item.get("newRating"),
                    reading_count=item.get("readingCount"),
                    source="weread", owned="digital",
                ))
        return books

    def book_info(self, book_id: str) -> Book:
        info = self._call("/book/info", bookId=book_id)
        return Book(
            book_id=book_id,
            title=info.get("title", ""),
            author=info.get("author", ""),
            cover=info.get("cover", ""),
            category=info.get("category", ""),
            intro=info.get("intro", ""),
            publisher=info.get("publisher", ""),
            isbn=info.get("isbn", ""),
            pubdate=_pubyear(info.get("publishTime")),
            rating=info.get("newRating"),
            source="weread", owned="digital",
        )

    def _progress(self, book_id: str):
        """返回 (progress:int|None, finished:bool)；失败则 (None, False)。"""
        try:
            b = self._call("/book/getprogress", bookId=book_id).get("book", {})
            p = b.get("progress")
            if p is None:
                return None, False
            return int(p), int(p) == 100
        except Exception:
            return None, False

    # ---- 书架 ----
    def shelf(self) -> List[Book]:
        data = self._call("/shelf/sync")
        out = []
        for b in data.get("books", []):
            out.append(Book(
                book_id=b.get("bookId", ""),
                title=b.get("title", ""),
                author=b.get("author", ""),
                cover=b.get("cover", ""),
                category=b.get("category", ""),
                finished=b.get("finishReading") == 1,   # 书架用 finishReading
                source="weread", owned="digital",
            ))
        return out

    # ---- 笔记 ----
    def notebooks(self) -> List[Note]:
        notes: List[Note] = []
        last_sort = None
        while True:
            data = self._call("/user/notebooks", count=20, lastSort=last_sort)
            for entry in data.get("books", []):
                b = entry.get("book", {})
                book = Book(
                    book_id=entry.get("bookId", ""),
                    title=b.get("title", ""),
                    author=b.get("author", ""),
                    cover=b.get("cover", ""),
                    progress=entry.get("readingProgress"),
                    finished=entry.get("markedStatus") == 1,
                    source="weread", owned="digital",
                )
                note = Note(book=book, bookmark_count=entry.get("bookmarkCount", 0))
                # 概览阶段用占位数量；完整内容需 book_notes 拉取
                note._preview_highlight_count = entry.get("noteCount", 0)  # type: ignore
                note._preview_review_count = entry.get("reviewCount", 0)   # type: ignore
                notes.append(note)
                last_sort = entry.get("sort")
            if data.get("hasMore") != 1:
                break
        return notes

    def book_notes(self, book_id: str) -> Note:
        book = self.book_info(book_id)
        # 补全阅读进度与读完状态（否则统一模型里会默认「想读」）
        prog, finished = self._progress(book_id)
        if prog is not None:
            book.progress = prog
        book.finished = finished
        note = Note(book=book)
        # 划线内容
        bm = self._call("/book/bookmarklist", bookId=book_id)
        chapters = {c.get("chapterUid"): c for c in bm.get("chapters", [])}
        for u in bm.get("updated", []):
            ch = chapters.get(u.get("chapterUid"), {})
            note.highlights.append(Highlight(
                highlight_id=u.get("bookmarkId", ""),
                book_id=book_id,
                text=u.get("markText", ""),
                chapter_title=ch.get("title", ""),
                chapter_idx=ch.get("chapterIdx", 0),
                create_time=u.get("createTime"),
                color=u.get("colorStyle"),
            ))
        # 想法 / 点评
        synckey = 0
        while True:
            rv = self._call("/review/list/mine", bookid=book_id, synckey=synckey)
            for r in rv.get("reviews", []):
                review = r.get("review", {})
                note.thoughts.append(Thought(
                    review_id=review.get("reviewId", ""),
                    book_id=book_id,
                    content=review.get("content", ""),
                    abstract=review.get("abstract", ""),
                    chapter_title=review.get("chapterName", ""),
                    star=review.get("star", -1),
                    is_book_review=bool(review.get("isFinish") is not None
                                        and not review.get("chapterName")),
                    create_time=review.get("createTime"),
                ))
            if rv.get("hasMore") != 1:
                break
            synckey = rv.get("synckey", 0)
        return note

    def popular_highlights(self, book_id: str) -> List[Highlight]:
        data = self._call("/book/bestbookmarks", bookId=book_id)
        chapters = {c.get("chapterUid"): c for c in data.get("chapters", [])}
        out = []
        for item in data.get("items", []):
            ch = chapters.get(item.get("chapterUid"), {})
            out.append(Highlight(
                highlight_id=item.get("bookmarkId", ""),
                book_id=book_id,
                text=item.get("markText", ""),
                chapter_title=ch.get("title", ""),
                popular_count=item.get("totalCount"),
            ))
        return out

    # ---- 阅读统计 ----
    def read_stat(self, mode: str = "monthly", base_time: int = 0) -> ReadStat:
        d = self._call("/readdata/detail", mode=mode, baseTime=base_time)
        stat = ReadStat(
            mode=mode,
            base_time=d.get("baseTime", 0),
            total_read_time=d.get("totalReadTime", 0),
            read_days=d.get("readDays", 0),
            day_average=d.get("dayAverageReadTime", 0),
            compare=d.get("compare"),
            prefer_time=d.get("preferTime", []),
            read_stat=d.get("readStat", []),
            daily_read_times={str(k): v for k, v in (d.get("dailyReadTimes") or {}).items()},
        )
        for r in d.get("readLongest", []):
            b = r.get("book") or r.get("albumInfo") or {}
            stat.read_longest.append({
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "read_time": r.get("readTime", 0),
            })
        for c in d.get("preferCategory", []):
            stat.prefer_category.append(CategoryPref(
                title=c.get("categoryTitle", ""),
                reading_time=c.get("readingTime", 0),
                reading_count=c.get("readingCount", 0),
                parent_title=c.get("parentCategoryTitle", ""),
            ))
        for a in d.get("preferAuthor", []):
            stat.prefer_author.append(AuthorPref(
                name=a.get("name", ""),
                count=a.get("count", 0),
                read_time=a.get("readTime", ""),
            ))
        return stat
