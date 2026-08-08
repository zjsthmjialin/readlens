"""端到端演示：无需 API Key，使用离线 mock 数据跑通四大能力。

运行： python examples/demo.py
产物在 examples/output/ 下。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readlens.config import Config
from readlens.adapters import get_platform
from readlens import export as exp
from readlens.report import render_html_report
from readlens import ai
from readlens.vault import build_vault, VaultConfig
from readlens.models import Book, Note

OUT = os.path.join(os.path.dirname(__file__), "output")


def main():
    cfg = Config.load(None)          # 默认 platform=mock
    plat = get_platform(cfg)
    engine = ai.get_engine(cfg)      # 默认离线引擎

    print("=" * 60)
    print("1) 搜索：三体")
    for b in plat.search("三体"):
        print(f"   《{b.title}》 — {b.author}  [{b.book_id}]")

    print("\n2) 导出全部笔记")
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    md = exp.export_markdown(notes, os.path.join(OUT, "markdown"))
    nj = exp.export_notion_json(notes, os.path.join(OUT, "notion"))
    ob = exp.export_obsidian(notes, os.path.join(OUT, "obsidian_vault"))
    print(f"   markdown {len(md)} 个 · notion {len(nj)} 个 · obsidian {len(ob)} 个")

    print("\n3) 生成月度报告（含图表 + AI 总结）")
    stat = plat.read_stat(mode="monthly")
    summary = ai.summarize_reading(stat, engine).replace("\n", "<br>")
    report = render_html_report(stat, os.path.join(OUT, "report"),
                               ai_summary=summary)
    print("   ->", report)

    print("\n4) AI 分析")
    santi = plat.book_notes("b_santi")
    print("   [单书总结]")
    print(_indent(ai.summarize_note(santi, engine)))
    print("   [跨书主题串联 · 主题=文明]")
    print(_indent(ai.link_themes(notes, engine, theme="文明")))
    print("   [读书问答]")
    print(_indent(ai.ask_about_book(santi, "黑暗森林法则说的是什么？", engine)))
    print("   [推荐]")
    print(_indent(ai.recommend_books(stat, notes, engine)))

    print("\n5) 生成 Obsidian 读书/藏书知识库")
    manual = _manual_books()   # 手动录入的藏书，与微信读书导入内容共存
    counts = build_vault(
        notes, VaultConfig(out_dir=os.path.join(OUT, "MyReadingVault")),
        stat=plat.read_stat(mode="overall"), manual_books=manual)
    print(f"   书籍 {counts['books']} · 作者 {counts['authors']} · "
          f"主题 {counts['topics']} · 仪表盘 {counts['dashboards']}")
    print("   -> ", os.path.join(OUT, "MyReadingVault"))

    print("\n完成 ✅ 产物见：", OUT)


def _manual_books():
    """两本手动录入的藏书示例。"""
    return [
        Note(book=Book(book_id="m1", title="百年孤独", author="加西亚·马尔克斯",
                       category="文学", publisher="南海出版公司", rating=95,
                       source="manual", owned="physical")),
        Note(book=Book(book_id="m2", title="置身事内", author="兰小欢",
                       category="经济学", rating=91, finished=True,
                       source="manual", owned="physical")),
    ]


def _indent(text, pad="      "):
    return "\n".join(pad + line for line in text.splitlines())


if __name__ == "__main__":
    main()
