"""ReadLens 命令行入口。

用法示例（默认使用离线 mock 平台，无需 API Key）：
  readlens search 三体
  readlens shelf
  readlens export --format markdown --out ./export_output
  readlens report --mode monthly --ai
  readlens ai summarize --book b_santi
  readlens ai themes --topic 文明
  readlens ai ask --book b_santi --q "黑暗森林法则是什么？"
  readlens ai recommend
"""
from __future__ import annotations

import argparse
import os
import sys

from .config import Config
from .adapters import get_platform
from . import export as exp
from .report import render_html_report
from . import ai
from .models import Book, Note
from .vault import build_vault, VaultConfig


def _load_manual_books(path):
    """从 JSON 载入手动藏书，转成 Note 列表。

    JSON 为对象数组，字段对应 Book（book_id 可省略，用 title 生成）。
    """
    import json
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    out = []
    for i, r in enumerate(rows):
        b = Book(
            book_id=r.get("book_id") or f"manual_{i}",
            title=r.get("title", ""), author=r.get("author", ""),
            category=r.get("category", ""), publisher=r.get("publisher", ""),
            intro=r.get("intro", ""), rating=r.get("platform_rating"),
            finished=r.get("status") == "已读",
            progress=r.get("progress", 0),
            source=r.get("source", "manual"),
            owned=r.get("owned", "physical"),
        )
        out.append(Note(book=b))
    return out


def _load(args):
    cfg = Config.load(args.config)
    if args.platform:
        cfg.data["platform"] = args.platform
    return cfg, get_platform(cfg)


def cmd_search(args):
    _, plat = _load(args)
    for i, b in enumerate(plat.search(args.keyword, scope=args.scope), 1):
        rating = f" · {b.rating}分" if b.rating else ""
        print(f"{i}. 《{b.title}》 — {b.author}（{b.category}{rating}） [{b.book_id}]")


def cmd_shelf(args):
    _, plat = _load(args)
    for i, b in enumerate(plat.shelf(), 1):
        flag = "✅读完" if b.finished else (f"{b.progress}%" if b.progress else "在读")
        print(f"{i}. 《{b.title}》 — {b.author}  [{flag}]")


def cmd_notes(args):
    _, plat = _load(args)
    note = plat.book_notes(args.book)
    print(exp.to_markdown(note))


def cmd_export(args):
    cfg, plat = _load(args)
    if args.book:
        notes = [plat.book_notes(args.book)]
    else:
        notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    out = args.out or cfg["export"]["out_dir"]
    if args.format == "markdown":
        files = exp.export_markdown(notes, out, single_file=args.single)
    elif args.format == "obsidian":
        vault = args.out or cfg["export"].get("obsidian_vault") or out
        files = exp.export_obsidian(notes, vault)
    elif args.format == "notion":
        files = exp.export_notion_json(notes, out)
    else:
        print(f"未知格式：{args.format}", file=sys.stderr)
        return
    print(f"已导出 {len(files)} 个文件到 {out}：")
    for f in files:
        print("  -", f)


def cmd_report(args):
    cfg, plat = _load(args)
    stat = plat.read_stat(mode=args.mode)
    summary = None
    if args.ai:
        engine = ai.get_engine(cfg)
        summary = ai.summarize_reading(stat, engine).replace("\n", "<br>")
    out = args.out or cfg["report"]["out_dir"]
    path = render_html_report(stat, out, ai_summary=summary,
                              color=cfg["report"]["theme_color"])
    print("报告已生成：", path)


def cmd_vault(args):
    cfg, plat = _load(args)
    notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
    manual = _load_manual_books(args.manual)
    stat = None
    if not args.no_stat:
        try:
            stat = plat.read_stat(mode="overall")
        except Exception:
            stat = None
    vc = VaultConfig(out_dir=args.out, vault_name=args.name)
    counts = build_vault(notes, vc, stat=stat, manual_books=manual)
    print(f"知识库已生成到 {args.out}")
    print(f"  书籍 {counts['books']} · 作者 {counts['authors']} · "
          f"主题 {counts['topics']} · 仪表盘 {counts['dashboards']} · "
          f"其他 {counts['misc']}")
    print("用 Obsidian 打开该文件夹，并启用 Dataview 插件后打开「📖 首页」。")


def cmd_ai(args):
    cfg, plat = _load(args)
    engine = ai.get_engine(cfg)
    if args.ai_cmd == "summarize":
        print(ai.summarize_note(plat.book_notes(args.book), engine))
    elif args.ai_cmd == "themes":
        notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
        print(ai.link_themes(notes, engine, theme=args.topic or ""))
    elif args.ai_cmd == "ask":
        print(ai.ask_about_book(plat.book_notes(args.book), args.q, engine))
    elif args.ai_cmd == "recommend":
        notes = [plat.book_notes(n.book.book_id) for n in plat.notebooks()]
        print(ai.recommend_books(plat.read_stat(mode="overall"), notes, engine))


def build_parser():
    p = argparse.ArgumentParser(prog="readlens", description="ReadLens 阅读智能工具箱")
    p.add_argument("--config", default="config.yaml", help="配置文件路径")
    p.add_argument("--platform", choices=["mock", "weread"], help="覆盖平台适配器")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜索书籍")
    s.add_argument("keyword")
    s.add_argument("--scope", default="book")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("shelf", help="查看书架")
    s.set_defaults(func=cmd_shelf)

    s = sub.add_parser("notes", help="打印单本书笔记(markdown)")
    s.add_argument("--book", required=True)
    s.set_defaults(func=cmd_notes)

    s = sub.add_parser("export", help="导出笔记")
    s.add_argument("--format", default="markdown",
                   choices=["markdown", "obsidian", "notion"])
    s.add_argument("--book", help="只导出某本书，不指定则导出全部")
    s.add_argument("--out", help="输出目录")
    s.add_argument("--single", action="store_true", help="markdown 合并为单文件")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("report", help="生成读书报告")
    s.add_argument("--mode", default="monthly",
                   choices=["weekly", "monthly", "annually", "overall"])
    s.add_argument("--out", help="输出目录")
    s.add_argument("--ai", action="store_true", help="附加 AI 阅读总结")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("vault", help="生成 Obsidian 读书/藏书知识库")
    s.add_argument("--out", default="./MyReadingVault", help="vault 输出目录")
    s.add_argument("--name", default="我的读书藏书库", help="知识库名称")
    s.add_argument("--manual", help="手动藏书 JSON 文件路径")
    s.add_argument("--no-stat", action="store_true", help="不生成统计快照")
    s.set_defaults(func=cmd_vault)

    s = sub.add_parser("ai", help="AI 分析")
    ai_sub = s.add_subparsers(dest="ai_cmd", required=True)
    a = ai_sub.add_parser("summarize"); a.add_argument("--book", required=True)
    a = ai_sub.add_parser("themes"); a.add_argument("--topic", default="")
    a = ai_sub.add_parser("ask"); a.add_argument("--book", required=True); a.add_argument("--q", required=True)
    ai_sub.add_parser("recommend")
    s.set_defaults(func=cmd_ai)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
