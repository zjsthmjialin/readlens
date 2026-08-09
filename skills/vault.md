# vault — Obsidian 读书/藏书知识库（延展能力）

把导入的书籍笔记 + 手动藏书，生成一个深度适配 Dataview 的个人知识库。

## 何时使用
- 用户说“做一个读书知识库 / 藏书库”“导出成 Obsidian 仓库”“管理我的书”

## 命令
```
readlens vault --out ./MyReadingVault [--name 我的书库] \
               [--manual examples/manual_collection.json] [--no-stat] [--overwrite]
```
- 默认**增量合并**：重复生成不会覆盖用户手写内容与手填字段。
- `--overwrite`：全量覆盖（放弃保护，重建全部文件）。

## 增量更新（默认开启）
自动生成区用标记注释包裹：`<!-- readlens:auto:start -->` / `<!-- readlens:auto:end -->`。
重生时**只替换标记之间**的内容，标记之后的手写区原样保留：
- 书籍笔记：`## 我的笔记`
- 作者页：`## 关于`
- 主题页：`## 主题笔记`

frontmatter 分两类（见 `vault/merge.py`）：
- **REFRESH**（每次刷新）：status / progress / highlights / thoughts / platform_rating / title / author / source。
- **PRESERVE_IF_SET**（有非空值则保留手填）：rating / isbn / publisher / cover / owned / location / price / started / finished / category 等。
- 用户额外加的自定义字段一律保留。

## 封面图
`cover` 字段非空时，书籍笔记自动区顶部渲染 `![封面|150](URL)`（Obsidian 外链图片）。

## 可视化统计页
`04-仪表盘/可视化统计.md` 用 **DataviewJS** 渲染评分分布 / 分类占比 / 各年读完数量；
需在 Dataview 设置里开启 *Enable JavaScript Queries*。

## 购书清单
`04-仪表盘/购书清单.md` 聚合 `owned: none` 的书。在书籍笔记里填 `priority: 高/中/低`
按优先级排序，`price_target` 记心理价位。这两个字段属于 PRESERVE_IF_SET，增量更新时保留。

## 阅读热力
可视化统计页含「阅读热力（年×月）」网格，按 `finished` 月份统计，方块深浅 + 数字表数量。

## 统计快照与趋势
每次生成 vault 落一份带日期快照到 `06-统计快照/history.json`（按日期 upsert、持久累积），
并生成 `趋势.md` 展示历次与「与上期对比(±)」。`readlens vault --no-snapshot` 可关闭。
见 `readlens/vault/snapshot.py`。

## 生成的 vault 结构
```
MyReadingVault/
├── 📖 首页.md            总览仪表盘（在读/已读/想读/藏书速览）
├── 01-书籍/              每本书一张笔记（含 Dataview frontmatter）
├── 02-作者/              作者中心页（自动汇总该作者的书）
├── 03-主题/             主题 MOC（按分类聚合）
├── 04-仪表盘/           在读/已读/想读/评分排行/藏书清单/阅读统计/可视化统计
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
