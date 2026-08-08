# 读透 ReadLens · 阅读智能工具箱

ReadLens 脱胎于 [Tencent/WeChatReading](https://github.com/Tencent/WeChatReading) Skills，
在其「搜书 / 书架 / 笔记 / 阅读统计」读取能力之上，做了四层延展：

1. **平台适配层** — 把「阅读平台」抽象成统一接口，可复刻到微信读书之外的平台
2. **多格式导出** — 笔记一键导出为 Markdown / Obsidian / Notion
3. **读书报告** — 月度/年度报告，自动生成图表可视化
4. **AI 增值** — 笔记总结、跨书主题串联、读书问答、个性化推荐
5. **📚 Obsidian 知识库** — 把读书笔记 + 手动藏书生成一个深度适配 Dataview 的
   个人读书/藏书知识库（每本书一张笔记、作者中心页、主题 MOC、仪表盘、时间线）

## 📚 生成 Obsidian 读书/藏书知识库（推荐用法）

```bash
readlens vault --out ./MyReadingVault --manual examples/manual_collection.json
```

生成的知识库结构（用 Obsidian 打开该文件夹，启用 **Dataview** 插件即可）：

```
MyReadingVault/
├── 📖 首页.md           总览仪表盘（在读 / 已读 / 想读 / 藏书速览）
├── 01-书籍/             每本书一张笔记（微信读书导入 + 手动录入共存）
├── 02-作者/            作者中心页（Dataview 自动汇总）
├── 03-主题/           主题 MOC（按分类聚合）
├── 04-仪表盘/         在读 / 已读 / 想读(愿望清单) / 评分排行 / 藏书清单 / 阅读统计
├── 05-阅读时间线.md
├── 00-模板/          书籍模板 + 藏书模板（配合 Templater/QuickAdd）
└── README.md
```

- **微信读书导入**：`source: weread`，默认电子书，带划线/想法/热门划线。
- **手动藏书**：`--manual <json>` 传入，或在 Obsidian 里用模板新建；可填纸质位置、
  价格、购入渠道。两类内容共存，仪表盘统一呈现。
- frontmatter 字段规范化（status/rating/owned/source…），改任意字段仪表盘实时更新。
  详见 [`skills/vault.md`](skills/vault.md)。

> 开箱即用：内置离线 `mock` 数据 + 离线 AI 引擎，**无需 API Key** 就能跑通全部流程。

## 与原项目的关系

| | Tencent/WeChatReading | ReadLens（本项目） |
|---|---|---|
| 形态 | 面向 Agent 的 Skill `.md` 文档 | 可运行 Python 项目 + 延展 Skill 文档 |
| 平台 | 仅微信读书 | 适配层，微信读书 + mock，可扩展 |
| 笔记 | 读取内容 | 读取 + 多格式导出（含双链/Notion blocks） |
| 统计 | 返回数据 | 数据 + 图表 + HTML 报告 |
| AI | 交由外部 Agent | 内置总结/主题/问答/推荐（离线可跑，可接 LLM） |
| 写操作 | 无 | 预留 `add_to_shelf` / `create_thought` 接口 |

## 快速开始

```bash
pip install -r requirements.txt          # 或 pip install -e .
python examples/demo.py                   # 无需 Key，一键跑通四大能力
```

CLI（默认离线 mock 平台）：

```bash
readlens search 三体
readlens shelf
readlens export --format markdown --out ./export_output
readlens export --format obsidian --out ./my_vault
readlens report --mode monthly --ai
readlens ai summarize --book b_santi
readlens ai themes --topic 文明
readlens ai ask --book b_santi --q "黑暗森林法则是什么？"
readlens ai recommend
```

## 接入真实数据

1. 复制配置：`cp config.example.yaml config.yaml`，把 `platform` 改为 `weread`
2. 设置微信读书 Key（从 https://weread.qq.com/r/weread-skills 获取）：
   ```bash
   export WEREAD_API_KEY=wrk-xxxxxxxx
   ```
3. （可选）接入 LLM 提升 AI 质量：
   ```bash
   export OPENAI_API_KEY=sk-xxxxxxxx      # 设置后 AI 自动从离线引擎切换到真实 LLM
   ```

## 目录结构

```
readlens/
├── adapters/        平台适配层（base 抽象 + weread + mock）
│   ├── base.py      ReadingPlatform 统一接口
│   ├── weread.py    微信读书适配器（网关协议）
│   └── mock.py      离线示例数据（复刻新平台的参照）
├── models.py        统一数据模型 Book/Highlight/Thought/Note/ReadStat
├── export/          markdown / obsidian / notion 导出
├── report/          报告生成器 + matplotlib 图表
├── ai/              engine 抽象 + summarize/themes/qa/recommend
├── vault/           Obsidian 知识库生成器（builder + 模板）
└── cli.py           命令行入口
skills/              面向 Agent 的延展 Skill 文档（export/report/ai/platforms）
examples/demo.py     端到端演示
tests/               单元测试
```

## 复刻到新平台

实现一个 `ReadingPlatform` 子类，把该平台原始字段映射到统一模型即可，
上层导出/报告/AI 自动复用。详见 [`skills/platforms.md`](skills/platforms.md)。

## 许可证

Apache-2.0 — 参考并延展自 Tencent/WeChatReading（Apache-2.0）。
