"""增量更新工具：保护用户手写内容与手填 frontmatter 字段。

设计契约：
- 自动生成区用标记注释包裹：`<!-- readlens:auto:start -->` / `<!-- readlens:auto:end -->`。
  重新生成 vault 时只替换标记之间的内容，标记之后的用户手写区（如
  `## 我的笔记` / `## 关于` / `## 主题笔记`）原样保留。
- frontmatter 分两类：
    * REFRESH（每次用平台最新值覆盖）：阅读状态与计数等「活」字段。
    * PRESERVE_IF_SET（存在非空值则保留用户手填）：评分/位置/价格等策展字段。
  用户额外加的自定义字段一律保留。
"""
from __future__ import annotations

import re
from collections import OrderedDict
from typing import List

MARK_START = "<!-- readlens:auto:start -->"
MARK_END = "<!-- readlens:auto:end -->"

# 每次重新导入都应刷新的「活」字段（阅读状态 / 计数 / 基本信息）
REFRESH = {
    "type", "title", "author", "authors",
    "platform_rating", "source", "progress", "status",
    "highlights", "thoughts",
}
# 存在非空值时保留用户手填的策展字段
PRESERVE_IF_SET = {
    "rating", "isbn", "publisher", "cover", "owned",
    "location", "price", "priority", "price_target",
    "started", "finished", "added",
    "category", "pubdate", "purchase_date", "purchase_from",
}

_EMPTY_TOKENS = {"", '""', "''", "[]", "~", "null"}


def _fm_key(line: str) -> str:
    return line.split(":", 1)[0].strip()


def _is_empty_fm_value(line: str) -> bool:
    """判断一条 frontmatter 行的值是否为空（无用户填写）。"""
    if ":" not in line:
        return True
    val = line.split(":", 1)[1].strip()
    return val in _EMPTY_TOKENS


def parse_frontmatter_lines(text: str) -> "OrderedDict[str, str]":
    """从文档解析出 frontmatter 的 key -> 整行原文（保留格式与引号）。

    只支持首个 `---...---` 块内的单行字段（本项目 schema 均为单行）。
    """
    out: "OrderedDict[str, str]" = OrderedDict()
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return out
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        out[_fm_key(line)] = line
    return out


def merge_frontmatter(new_lines: List[str], existing_text: str) -> List[str]:
    """把新生成的 frontmatter 行与已存在文档合并。

    - REFRESH 字段用新值；
    - PRESERVE_IF_SET 字段：旧文档有非空值则保留旧值；
    - 旧文档里我们不管理的自定义字段追加保留。
    """
    existing = parse_frontmatter_lines(existing_text)
    out: List[str] = []
    seen = set()
    for line in new_lines:
        key = _fm_key(line)
        seen.add(key)
        if (key in PRESERVE_IF_SET and key in existing
                and not _is_empty_fm_value(existing[key])):
            out.append(existing[key])
        else:
            out.append(line)
    for key, line in existing.items():
        if key not in seen:
            out.append(line)
    return out


def extract_user_tail(existing_text: str, default: str) -> str:
    """从已存在文档提取用户手写尾部（自动区之后的内容）。

    优先取 `<!-- readlens:auto:end -->` 之后的内容；否则退化为从
    某个用户标题（## 我的笔记 / ## 关于 / ## 主题笔记）开始；都没有则用 default。
    """
    idx = existing_text.find(MARK_END)
    if idx != -1:
        tail = existing_text[idx + len(MARK_END):].strip("\n")
        return (tail + "\n") if tail else default
    m = re.search(r"^## (?:我的笔记|关于|主题笔记).*", existing_text, re.M | re.S)
    if m:
        return existing_text[m.start():].rstrip() + "\n"
    return default


def wrap_auto(inner: str) -> str:
    """用标记注释包裹自动区内容。"""
    return f"{MARK_START}\n{inner.rstrip()}\n{MARK_END}"
