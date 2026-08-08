# vault — Obsidian 读书/藏书知识库（延展能力）

把导入的书籍笔记 + 手动藏书，生成一个深度适配 Dataview 的个人知识库。

## 何时使用
- 用户说“做一个读书知识库 / 藏书库”“导出成 Obsidian 仓库”“管理我的书”

## 命令
```
readlens vault --out ./MyReadingVault [--name 我的书库] \
               [--manual examples/manual_collection.json] [--no-stat]
```

## 生成的 vault 结构
```
MyReadingVault/
├── 📖 首页.md            总览仪表盘（在读/已读/想读/藏书速览）
├── 01-书籍/              每本书一张笔记（含 Dataview frontmatter）
├── 02-作者/              作者中心页（自动汇总该作者的书）
├── 03-主题/             主题 MOC（按分类聚合）
├── 04-仪表盘/           在读/已读/想读/评分排行/藏书清单/阅读统计
├── 05-阅读时间线.md
├── 00-模板/            书籍模板 + 藏书模板
└── README.md
```

## frontmatter 规范（Dataview 依赖）
| 字段 | 取值 | 说明 |
|------|------|------|
| type | book / author / topic | 笔记类型 |
| status | 想读/在读/已读/弃读 | 阅读状态 |
| rating | 0-5 | 个人评分（半星可用 4.5） |
| platform_rating | 0-100 | 平台评分 |
| owned | physical/digital/none | 拥有情况 |
| source | weread/manual/douban/kindle | 数据来源 |
| location | 文本 | 纸质藏书位置 |

## 两类内容共存
- **微信读书导入**：`source: weread`，默认 `owned: digital`，带划线/想法。
- **手动藏书**：通过 `--manual <json>` 传入，或在 Obsidian 里用 `00-模板/藏书模板` 新建；
  默认 `source: manual`、`owned: physical`，可填位置/价格/购入渠道。

## 工作流
1. 从平台拉全部有笔记的书 → `book_notes()`。
2. 载入手动藏书 JSON（可选）→ 合并入库。
3. 生成书籍笔记、作者页、主题 MOC、仪表盘、时间线、首页、模板。
4. 提示用户用 Obsidian 打开并启用 Dataview。
