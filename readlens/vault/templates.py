"""静态模板与 Dataview 仪表盘文本。

集中放置模板字符串，builder.py 引用。所有 Dataview 代码块使用 `#book` 标签
和规范化 frontmatter 字段，保证查询可用。
"""

# ---- 新建书籍 / 藏书模板（供 Templater / QuickAdd 使用） ----

BOOK_TEMPLATE = """---
type: book
title: "{{title}}"
author: ""
authors: []          # 形如 ["[[作者名]]"]，用于关系图谱
category: ""
tags: [book]
status: 想读          # 想读 | 在读 | 已读 | 弃读
rating:              # 个人评分 0-5（半星可用 4.5）
platform_rating:     # 平台评分 0-100（导入时填充）
isbn: ""
publisher: ""
pubdate:             # 出版年份
cover:               # 封面图 URL 或本地路径
source: manual       # weread | manual | douban | kindle
owned: none          # physical(纸质) | digital(电子) | none(未拥有)
location: ""         # 纸质藏书位置，如「书房A-3」
price:               # 购入价格
priority:            # 购书优先级：高 | 中 | 低（owned=none 时用于购书清单排序）
price_target:        # 心理价位（可选）
progress: 0          # 阅读进度 %
started:             # 开始阅读 YYYY-MM-DD
finished:            # 读完 YYYY-MM-DD
added: {{date}}       # 收录进库日期
highlights: 0
thoughts: 0
---

# {{title}}

> [!info] 一句话简介
>

## 划线

## 想法 / 书评

## 关联
- 作者：
- 主题：
"""

MANUAL_COLLECTION_TEMPLATE = """---
type: book
title: "{{title}}"
author: ""
authors: []
category: ""
tags: [book, 藏书]
status: 想读
rating:
isbn: ""
publisher: ""
pubdate:
cover:
source: manual
owned: physical      # 手动藏书默认纸质
location: ""         # 例如「客厅书架-2层」
price:
purchase_date:       # 购入日期 YYYY-MM-DD
purchase_from:       # 购入渠道，如「当当」「二手书店」
added: {{date}}
highlights: 0
thoughts: 0
---

# {{title}}

> 手动录入的藏书。填写作者、分类、位置等信息后，会自动出现在各仪表盘中。

## 划线

## 想法 / 书评

## 关联
- 作者：
- 主题：
"""

# ---- README（vault 使用说明） ----

VAULT_README = """# 📚 我的读书 / 藏书知识库

由 [ReadLens](https://github.com/) 生成，脱胎于 Tencent/WeChatReading。
这是一个深度适配 **Dataview** 的个人读书与藏书知识库。

## 打开方式
1. 用 Obsidian 「打开文件夹作为仓库」选择本目录。
2. 安装社区插件 **Dataview**（设置 → 社区插件 → 浏览 → 搜 Dataview → 安装）。
   本库已**预配置** Dataview 设置（JavaScript Queries 已开启、安装后自动启用），
   所以你只需装一下、无需再做任何设置。
3. 打开 `📖 首页.md` 查看总览仪表盘。

（可选）安装 **Templater** / **QuickAdd**，把 `00-模板/` 里的模板绑定为快捷命令，
一键新建书籍或藏书笔记。

## 目录结构
- `📖 首页.md` — 总览仪表盘（在读 / 想读 / 最近读完 / 统计）
- `01-书籍/` — 每本书一张笔记（微信读书导入 + 手动录入共存）
- `02-作者/` — 作者中心页，自动汇总该作者的书
- `03-主题/` — 主题 MOC，按分类聚合
- `04-仪表盘/` — 在读 / 想读(愿望清单) / 已读 / 评分排行 / 藏书清单 / 阅读统计
- `05-阅读时间线.md` — 按时间排列的阅读轨迹
- `00-模板/` — 新建书籍 / 藏书模板

## frontmatter 字段约定
| 字段 | 含义 | 取值 |
|------|------|------|
| status | 阅读状态 | 想读 / 在读 / 已读 / 弃读 |
| rating | 个人评分 | 0-5（可半星） |
| owned | 拥有情况 | physical / digital / none |
| source | 数据来源 | weread / manual / douban / kindle |
| location | 纸质藏书位置 | 自由文本 |

改任意字段后，Dataview 仪表盘会自动更新——这就是知识库「活」起来的地方。
"""
