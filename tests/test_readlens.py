"""基础单元测试，覆盖适配器 / 导出 / 报告 / AI 四层。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readlens.adapters import get_platform
from readlens.config import Config
from readlens import export as exp
from readlens.report.generator import build_report
from readlens import ai


def _plat():
    return get_platform(Config.load(None))


def test_search():
    hits = _plat().search("三体")
    assert any("三体" in b.title for b in hits)


def test_notebooks_and_notes():
    plat = _plat()
    nbs = plat.notebooks()
    assert len(nbs) >= 1
    note = plat.book_notes("b_santi")
    assert note.total_count == len(note.highlights) + len(note.thoughts) + note.bookmark_count
    assert note.highlights


def test_markdown_export(tmp_path):
    plat = _plat()
    note = plat.book_notes("b_santi")
    files = exp.export_markdown([note], str(tmp_path))
    assert files and os.path.exists(files[0])
    content = open(files[0], encoding="utf-8").read()
    assert "三体" in content and ">" in content  # 引用格式


def test_notion_blocks():
    note = _plat().book_notes("b_santi")
    blocks = exp.to_notion_blocks(note)
    assert blocks[0]["type"] == "heading_1"
    assert any(b["type"] == "quote" for b in blocks)


def test_report_build():
    stat = _plat().read_stat(mode="monthly")
    rep = build_report(stat)
    assert rep["read_days"] >= 1
    assert rep["read_longest"]
    assert "小时" in rep["total_read"] or "分钟" in rep["total_read"]


def test_vault_build(tmp_path):
    from readlens.vault import build_vault, VaultConfig
    from readlens.models import Book, Note
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    manual = [Note(book=Book(book_id="m1", title="百年孤独", author="马尔克斯",
                             category="文学", source="manual", owned="physical"))]
    out = str(tmp_path / "vault")
    counts = build_vault(notes, VaultConfig(out_dir=out),
                         stat=plat.read_stat("overall"), manual_books=manual)
    assert counts["books"] == len(notes) + 1
    # 首页与关键仪表盘存在
    assert os.path.exists(os.path.join(out, "📖 首页.md"))
    assert os.path.exists(os.path.join(out, "04-仪表盘", "藏书清单.md"))
    # 手动藏书笔记含正确 frontmatter
    bianian = open(os.path.join(out, "01-书籍", "百年孤独.md"), encoding="utf-8").read()
    assert "owned: physical" in bianian and "source: manual" in bianian
    # 导入书为电子书 + Dataview 查询存在
    santi = open(os.path.join(out, "01-书籍", "三体.md"), encoding="utf-8").read()
    assert "owned: digital" in santi and "status: 已读" in santi
    home = open(os.path.join(out, "📖 首页.md"), encoding="utf-8").read()
    assert "```dataview" in home and "#book" in home


def test_vault_incremental_preserves(tmp_path):
    """增量更新：保护用户手填 frontmatter 与手写尾部，同时刷新计数。"""
    import re
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = str(tmp_path / "vault")
    vc = VaultConfig(out_dir=out)
    build_vault(notes, vc, stat=plat.read_stat("overall"))

    bp = os.path.join(out, "01-书籍", "三体.md")
    txt = open(bp, encoding="utf-8").read()
    assert "<!-- readlens:auto:start -->" in txt and "## 我的笔记" in txt
    # 用户手填 + 手写
    txt = txt.replace('location: ""', 'location: "书房A-3"').replace("price: ", "price: 68")
    txt = re.sub(r"## 我的笔记.*", "## 我的笔记\n\n手写读后感勿删", txt, flags=re.S)
    open(bp, "w", encoding="utf-8").write(txt)

    build_vault(notes, vc, stat=plat.read_stat("overall"))  # 再次增量
    after = open(bp, encoding="utf-8").read()
    assert 'location: "书房A-3"' in after
    assert "price: 68" in after
    assert "手写读后感勿删" in after
    assert re.search(r"highlights: \d+", after)  # 计数仍在（已刷新）


def test_vault_overwrite_mode(tmp_path):
    """全量覆盖模式清除手写内容。"""
    import re
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = str(tmp_path / "vault")
    build_vault(notes, VaultConfig(out_dir=out))
    bp = os.path.join(out, "01-书籍", "三体.md")
    txt = re.sub(r"## 我的笔记.*", "## 我的笔记\n\n应被覆盖", open(bp, encoding="utf-8").read(), flags=re.S)
    open(bp, "w", encoding="utf-8").write(txt)
    build_vault(notes, VaultConfig(out_dir=out, incremental=False))
    assert "应被覆盖" not in open(bp, encoding="utf-8").read()


def test_vault_cover_and_viz(tmp_path):
    """封面图渲染 + DataviewJS 统计页存在。"""
    from readlens.vault import build_vault, VaultConfig
    from readlens.models import Book, Note
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    manual = [Note(book=Book(book_id="c1", title="带封面的书", author="作者X",
                             cover="https://img.example.com/c.jpg",
                             source="manual", owned="physical"))]
    out = str(tmp_path / "vault")
    build_vault(notes, VaultConfig(out_dir=out), manual_books=manual)
    cover_note = open(os.path.join(out, "01-书籍", "带封面的书.md"), encoding="utf-8").read()
    assert "![封面|150](https://img.example.com/c.jpg)" in cover_note
    viz = open(os.path.join(out, "04-仪表盘", "可视化统计.md"), encoding="utf-8").read()
    assert "```dataviewjs" in viz and "评分分布" in viz


def test_vault_author_topic_tail_preserved(tmp_path):
    """作者页「## 关于」与主题页「## 主题笔记」手写区在重生后保留。"""
    import re
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = str(tmp_path / "vault")
    vc = VaultConfig(out_dir=out)
    build_vault(notes, vc)
    ap = os.path.join(out, "02-作者", "刘慈欣.md")
    txt = re.sub(r"## 关于.*", "## 关于\n\n刘慈欣是我最爱的科幻作者", open(ap, encoding="utf-8").read(), flags=re.S)
    open(ap, "w", encoding="utf-8").write(txt)
    build_vault(notes, vc)
    assert "刘慈欣是我最爱的科幻作者" in open(ap, encoding="utf-8").read()


def test_vault_buylist(tmp_path):
    """购书清单页存在；priority 字段在书籍 frontmatter 中且增量更新保留。"""
    import re
    from readlens.vault import build_vault, VaultConfig
    from readlens.models import Book, Note
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    manual = [Note(book=Book(book_id="w1", title="想买的书", author="作者Y",
                             category="随笔", source="manual", owned="none"))]
    out = str(tmp_path / "vault")
    vc = VaultConfig(out_dir=out)
    build_vault(notes, vc, manual_books=manual)
    buy = open(os.path.join(out, "04-仪表盘", "购书清单.md"), encoding="utf-8").read()
    assert "购书清单" in buy and "owned" in buy
    bp = os.path.join(out, "01-书籍", "想买的书.md")
    txt = open(bp, encoding="utf-8").read()
    assert "priority:" in txt and "price_target:" in txt
    # 用户填 priority 后增量更新应保留
    txt = txt.replace("priority: ", "priority: 高").replace("price_target: ", "price_target: 45")
    open(bp, "w", encoding="utf-8").write(txt)
    build_vault(notes, vc, manual_books=manual)
    after = open(bp, encoding="utf-8").read()
    assert "priority: 高" in after and "price_target: 45" in after


def test_enrich_mock_only_fills_empty():
    """离线增强：补空缺字段，且不覆盖已有值。"""
    from readlens import enrich
    from readlens.models import Book
    f = enrich.get_fetcher("mock")
    b = Book(book_id="e1", title="三体", author="刘慈欣", publisher="已有出版社")
    filled = enrich.enrich_book(b, f)
    assert "isbn" in filled and b.isbn == "9787536692930"
    assert b.publisher == "已有出版社"      # 不覆盖已有
    assert "publisher" not in filled
    # 未知书目返回空、无改动
    b2 = Book(book_id="e2", title="不存在的书", author="无名")
    assert enrich.enrich_book(b2, f) == []


def test_enrich_vault_integration(tmp_path):
    """vault 增强后书籍 frontmatter 含补全的 isbn/pubdate。"""
    from readlens import enrich
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    enrich.enrich_notes(notes, enrich.get_fetcher("mock"))
    out = str(tmp_path / "vault")
    build_vault(notes, VaultConfig(out_dir=out))
    santi = open(os.path.join(out, "01-书籍", "三体.md"), encoding="utf-8").read()
    assert 'isbn: "9787536692930"' in santi and "pubdate: 2008" in santi


def test_enrich_douban_degrades(monkeypatch):
    """豆瓣源在网络/依赖异常时降级为返回空字典，绝不抛异常。"""
    import requests
    from readlens.enrich.douban import DoubanFetcher

    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(requests, "get", boom)
    assert DoubanFetcher().fetch("三体") == {}


def test_vault_snapshot_upsert(tmp_path):
    """快照按日期 upsert：同日重生不重复；趋势页与 history.json 生成。"""
    import json
    from readlens.vault import build_vault, VaultConfig
    from readlens.vault import snapshot as S
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = str(tmp_path / "vault")
    vc = VaultConfig(out_dir=out)
    stat = plat.read_stat("overall")
    build_vault(notes, vc, stat=stat)
    build_vault(notes, vc, stat=stat)      # 同日再来一次
    hist_path = os.path.join(out, S.DIR_SNAP, "history.json")
    history = json.load(open(hist_path, encoding="utf-8"))
    today = [h for h in history if h["date"]]
    # 同一天只应有一条
    assert len({h["date"] for h in history}) == len(history)
    assert len(history) == 1
    assert os.path.exists(os.path.join(out, S.DIR_SNAP, "趋势.md"))


def test_snapshot_compute_and_trend_delta():
    """compute_snapshot 计数正确；趋势页含与上期对比(±)。"""
    from readlens.vault import snapshot as S
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    s1 = S.compute_snapshot(notes, plat.read_stat("overall"), day="2026-01-01")
    assert s1["total"] == len(notes)
    assert s1["已读"] + s1["在读"] + s1["想读"] == len(notes)
    s2 = dict(s1); s2["date"] = "2026-02-01"; s2["已读"] = s1["已读"] + 2
    page = S.trend_page_md([s1, s2])
    assert "统计趋势" in page and "(+2)" in page   # 与上期对比出现


def test_quickstart_sample_manual():
    """内置示例藏书可被 --with-manual 纳入（离线，无外部文件）。"""
    from readlens.cli import _rows_to_notes
    from readlens.sampledata import SAMPLE_MANUAL
    notes = _rows_to_notes(SAMPLE_MANUAL)
    assert len(notes) == len(SAMPLE_MANUAL) >= 3
    titles = {n.book.title for n in notes}
    assert "沙丘" in titles
    assert any(n.book.owned == "none" for n in notes)   # 有待购书演示购书清单


def test_vault_heatmap_section(tmp_path):
    """可视化统计页含阅读热力（年×月）区块。"""
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = str(tmp_path / "vault")
    build_vault(notes, VaultConfig(out_dir=out))
    viz = open(os.path.join(out, "04-仪表盘", "可视化统计.md"), encoding="utf-8").read()
    assert "阅读热力" in viz and "grid" in viz


def test_weread_mapping_offline(monkeypatch):
    """用假网关校验 weread 适配器字段映射与官方文档一致（无需真实 Key）。"""
    from readlens.adapters.weread import WeReadPlatform

    canned = {
        "/store/search": {"results": [{"books": [
            {"bookInfo": {"bookId": "b1", "title": "三体", "author": "刘慈欣",
                          "category": "科幻"}, "newRating": 92, "readingCount": 100}]}]},
        "/shelf/sync": {"books": [{"bookId": "b1", "title": "三体", "author": "刘慈欣",
                                   "category": "科幻", "finishReading": 1}]},
        "/book/info": {"title": "三体", "author": "刘慈欣", "category": "科幻",
                       "publisher": "重庆出版社", "isbn": "9787536692930",
                       "publishTime": "2008-01-01", "newRating": 92},
        "/book/getprogress": {"book": {"progress": 100, "finishTime": 123}},
        "/book/bookmarklist": {"updated": [{"bookmarkId": "h1", "chapterUid": 1,
                               "markText": "黑暗森林", "createTime": 100}],
                               "chapters": [{"chapterUid": 1, "chapterIdx": 1,
                                             "title": "第一章"}]},
        "/review/list/mine": {"reviews": [{"review": {"reviewId": "r1", "content": "想法",
                              "abstract": "黑暗森林", "star": -1, "chapterName": "第一章"}}],
                              "hasMore": 0},
        "/readdata/detail": {"totalReadTime": 3600, "readDays": 10,
                             "dayAverageReadTime": 360,
                             "readLongest": [{"book": {"title": "三体", "author": "刘慈欣"},
                                              "readTime": 3600}],
                             "preferCategory": [{"categoryTitle": "科幻",
                                                 "readingTime": 3600, "readingCount": 1}]},
    }
    plat = WeReadPlatform(base_url="http://fake", api_key="wrk-test")
    monkeypatch.setattr(plat, "_call", lambda api_name, **kw: canned[api_name])

    # 搜索
    hits = plat.search("三体")
    assert hits and hits[0].title == "三体" and hits[0].source == "weread"
    # 书架：finished 来自 finishReading
    shelf = plat.shelf()
    assert shelf[0].finished is True and shelf[0].source == "weread"
    # 单本笔记：source/isbn/pubdate/进度/读完 + 划线/想法
    note = plat.book_notes("b1")
    assert note.book.source == "weread" and note.book.owned == "digital"
    assert note.book.isbn == "9787536692930" and note.book.pubdate == "2008"
    assert note.book.progress == 100 and note.book.finished is True
    assert note.highlights[0].chapter_title == "第一章"
    assert note.thoughts[0].abstract == "黑暗森林"
    # 阅读统计
    stat = plat.read_stat("overall")
    assert stat.total_hours == 1.0 and stat.read_days == 10
    assert stat.read_longest[0]["title"] == "三体"
    assert stat.prefer_category[0].title == "科幻"


def test_digest_and_slug():
    """周期报告摘要渲染 + 幂等命名。"""
    from datetime import date
    from readlens.report import render_digest_md, period_slug
    stat = _plat().read_stat("weekly")
    md = render_digest_md(stat, "weekly", ai_summary="这是小结")
    assert "阅读周报" in md and "阅读时长" in md and "这是小结" in md
    assert period_slug("monthly", date(2026, 8, 9)) == "月报-2026-08"
    assert period_slug("weekly", date(2026, 8, 9)).startswith("周报-2026-W")


def test_report_modes_resolve():
    """--report-mode 归一：单/多/all/none。"""
    from readlens.cli import _resolve_report_modes
    assert _resolve_report_modes("weekly") == ["weekly"]
    assert _resolve_report_modes(["all"]) == ["weekly", "monthly", "annually"]
    assert _resolve_report_modes(["none", "weekly"]) == []
    assert _resolve_report_modes(["monthly", "monthly", "weekly"]) == ["monthly", "weekly"]


def test_sync_command(tmp_path):
    """sync 一条命令：生成知识库 + 一次生成周/月/年三种报告写入 07-报告。"""
    import argparse
    from readlens.cli import cmd_sync
    out = str(tmp_path / "v")
    args = argparse.Namespace(config=None, platform="mock", out=out,
                              name="测试库", manual=None,
                              report_mode=["weekly", "monthly", "annually"],
                              overwrite=False, enrich=False, enrich_source="mock")
    cmd_sync(args)
    assert os.path.exists(os.path.join(out, "📖 首页.md"))
    reports = os.listdir(os.path.join(out, "07-报告"))
    assert any(r.startswith("周报-") for r in reports)
    assert any(r.startswith("月报-") for r in reports)
    assert any(r.startswith("年报-") for r in reports)
    # 幂等：再跑一次不新增重复文件
    cmd_sync(args)
    assert len(os.listdir(os.path.join(out, "07-报告"))) == len(reports)


def test_vault_obsidian_config(tmp_path):
    """预置 .obsidian：默认写入且开启 JS 查询；不覆盖已有；可关。"""
    import json
    from readlens.vault import build_vault, VaultConfig
    plat = _plat()
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]

    out = str(tmp_path / "v")
    build_vault(notes, VaultConfig(out_dir=out))
    cp = os.path.join(out, ".obsidian", "community-plugins.json")
    dv = os.path.join(out, ".obsidian", "plugins", "dataview", "data.json")
    assert "dataview" in json.load(open(cp, encoding="utf-8"))
    assert json.load(open(dv, encoding="utf-8"))["enableDataviewJs"] is True

    # 不覆盖用户已有配置
    open(cp, "w", encoding="utf-8").write('["myplugin"]')
    build_vault(notes, VaultConfig(out_dir=out))
    assert "myplugin" in open(cp, encoding="utf-8").read()

    # 可关闭
    out2 = str(tmp_path / "v2")
    build_vault(notes, VaultConfig(out_dir=out2, obsidian_config=False))
    assert not os.path.exists(os.path.join(out2, ".obsidian"))


def test_ai_offline():
    plat = _plat()
    engine = ai.get_engine(Config.load(None))
    note = plat.book_notes("b_santi")
    assert ai.summarize_note(note, engine)
    assert ai.ask_about_book(note, "黑暗森林", engine)
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    assert ai.link_themes(notes, engine, "文明")
    assert ai.recommend_books(plat.read_stat("overall"), notes, engine)


if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])
