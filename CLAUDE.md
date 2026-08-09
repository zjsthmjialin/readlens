# CLAUDE.md — ReadLens 项目约定

> 本文件供 AI 会话（Claude Code / Cowork）自动加载，快速理解项目并保持一致风格。
> 新会话请先读本文件，再读 `docs/HANDOFF.md`（当前状态）与 `docs/PROJECT_PLAN.md`（规划）。

## 项目一句话
ReadLens（阅镜）是一个「阅读智能工具箱」，脱胎于 Tencent/WeChatReading Skills，
把个人读书数据（微信读书导入 + 手动藏书）沉淀为可导出、可分析、可生长的知识库；
核心交付形态是一个深度适配 Dataview 的 **Obsidian 读书/藏书知识库**。

## 技术栈与约束
- 语言：Python ≥ 3.9，标准库优先；第三方依赖只用 `requests / pyyaml / jinja2 / matplotlib`，AI 可选 `openai`。
- **离线可跑**：没有 API Key 时必须能用 `mock` 平台 + `offline` AI 引擎跑通全部流程。这是硬性约束，新功能都要保留离线路径。
- 所有平台数据先归一化到 `readlens/models.py` 的统一模型，上层（export/report/ai/vault）只依赖统一模型，不直接碰平台原始字段。
- 中文优先：面向用户的文案、文档、注释用中文。

## 目录约定
```
readlens/
├── models.py         统一数据模型（Book/Highlight/Thought/Note/ReadStat）
├── config.py         配置加载（yaml + 环境变量）
├── adapters/         平台适配层：base(抽象) / weread / mock / __init__(工厂)
├── export/           markdown / obsidian / notion 导出
├── report/           charts(matplotlib) / generator(HTML 报告)
├── ai/               engine(抽象+offline+openai) / summarize / themes / qa / recommend
├── vault/            Obsidian 知识库生成器：builder / templates
└── cli.py            命令行入口（argparse）
skills/               面向 Agent 的能力说明文档（export/report/ai/platforms/vault）
examples/             demo.py + manual_collection.json + output/(示例产物)
tests/                pytest 单元测试
docs/                 PROJECT_PLAN / HANDOFF
```

## 关键设计决策
1. **适配器模式**：新增平台 = 继承 `adapters/base.ReadingPlatform` + 字段映射，再在 `adapters/__init__.get_platform` 注册；上层零改动。`mock.py` 是最佳映射参照。
2. **AI 引擎抽象**：`ai/engine.py` 提供 `OfflineEngine`（抽取式，占位）与 `OpenAIEngine`；`get_engine()` 按是否有 `OPENAI_API_KEY` 自动选择。
3. **vault frontmatter 是契约**：Dataview 查询依赖字段名/取值（status/rating/owned/source/category/tags）。改字段要同步改 `vault/builder.py` 里的仪表盘查询与 `skills/vault.md`。
4. **统计口径沿用原项目**：阅读时长单位是**秒**；笔记数 = 划线 + 想法 + 书签；书签只计数不导出内容。见 `docs` 与原始 readdata/notes 口径。

## 编码规范
- 每个模块顶部写中文 docstring 说明用途。
- 新增能力：先写/改统一模型 → 适配器 → 上层功能 → CLI 子命令 → skills/*.md → tests。
- 提交前跑 `python -m pytest tests/ -q` 和 `python examples/demo.py`，两者都要绿。

## 运行速查
```bash
pip install -r requirements.txt
python examples/demo.py                                   # 离线跑通五大能力
python -m readlens.cli vault --out ./MyReadingVault \
       --manual examples/manual_collection.json           # 生成知识库
python -m pytest tests/ -q
```

## 当前状态（截至交接）
v0.1.0：平台适配层 / 多格式导出 / 读书报告 / AI 增值 / Obsidian 知识库五大能力均已实现并通过 7 个单测。详见 `docs/HANDOFF.md`。
