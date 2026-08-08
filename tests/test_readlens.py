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
