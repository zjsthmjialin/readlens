# export — 笔记导出（延展能力）

把统一模型的笔记导出为 Markdown / Obsidian / Notion 三种格式。原项目只提供
「读取笔记内容」，本能力在其上增加「结构化落地」。

## 何时使用
- 用户说“导出我的笔记 / 划线”“同步到 Obsidian / Notion”“把三体的笔记存成 md”
- 用户想把读书笔记搬到第三方笔记系统做二次整理

## 命令
```
readlens export --format markdown [--book <bookId>] [--out <dir>] [--single]
readlens export --format obsidian --out <vault_dir>
readlens export --format notion  --out <dir>
```

## 格式说明
| 格式 | 产物 | 特点 |
|------|------|------|
| markdown | 每本书一个 `.md`，或 `--single` 合并 | YAML frontmatter + 按章节分组，划线用 `>` 引用，想法关联到对应划线 |
| obsidian | vault 内 `.md` + `_ReadLens_MOC.md` 索引 | 追加 `[[作者]]`/`[[分类]]` 双链，可做关系图谱 |
| notion | 每本书一个 `.notion.json` | 标准 Notion blocks，可直接喂 `blocks.children.append` |

## 工作流
1. 若给定 `bookId`/书名 → 只导出该书；否则遍历 `notebooks()` 导出全部。
2. 划线按 `chapter_idx` 排序、按章节标题分组。
3. 想法通过 `abstract`（关联划线原文）挂到对应划线下；无法关联的单独成节；整本书评单列。
4. 书签只体现数量，不导出内容（沿用原项目口径）。
