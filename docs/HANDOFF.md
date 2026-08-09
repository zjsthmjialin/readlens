# 交接文档 HANDOFF

> 给下一个会话（新对话窗口）快速接手用。读完这份 + `CLAUDE.md` 即可继续开发。

## 0. 一分钟上手
```bash
cd "ReadLens  260808"                      # 项目根目录
pip install -r requirements.txt
python examples/demo.py                     # 无需任何 Key，端到端跑通
python -m pytest tests/ -q                  # 期望：7 passed
python -m readlens.cli vault --out ./MyReadingVault \
       --manual examples/manual_collection.json   # 生成 Obsidian 知识库
```
用 Obsidian「打开文件夹作为仓库」选 `MyReadingVault`，装 Dataview 插件，打开「📖 首页」。

## 1. 这个项目是什么
见 `CLAUDE.md` 与 `docs/PROJECT_PLAN.md`。一句话：把读书数据 + 藏书做成
一个 Dataview 驱动的 Obsidian 个人读书/藏书知识库，附带导出/报告/AI 能力。

## 2. 已完成且验证过（v0.1.0）
- 五大能力全部实现：平台适配层、多格式导出、读书报告、AI 增值、Obsidian 知识库。
- 7 个单测通过；`examples/demo.py` 端到端产出：导出文件、HTML 报告 + 图表、示例 vault。
- 离线可跑（mock 平台 + offline AI 引擎），不需要 API Key。
- 示例产物已在 `examples/output/`（含一份完整生成的 `MyReadingVault/`）。

## 3. 文件地图（改哪里做什么）
| 想做的事 | 去改 |
|----------|------|
| 加一个新阅读平台 | `readlens/adapters/` 新建子类 + `adapters/__init__.py` 注册 |
| 改统一数据结构 | `readlens/models.py`（改完检查所有下游） |
| 调整知识库结构/仪表盘 | `readlens/vault/builder.py` + `vault/templates.py` |
| 改导出格式 | `readlens/export/{markdown,obsidian,notion}.py` |
| 改报告/图表 | `readlens/report/{generator,charts}.py` |
| 改 AI 能力/提示词 | `readlens/ai/{summarize,themes,qa,recommend}.py` |
| 加 CLI 子命令 | `readlens/cli.py` |
| 能力说明（给 Agent 读） | `skills/*.md` |

## 4. 建议的下一步（按优先级，来自 PROJECT_PLAN Phase 1）
已完成（v0.2.0，本次会话）：
1. ✅ **增量更新**：`vault/merge.py` 用标记注释包裹自动区，只替换自动区；frontmatter
   保护手填字段（rating/location/price/isbn/cover/owned 等）。默认开启，`--overwrite` 强制全量。
2. ✅ **封面图**：`cover` 非空时书籍笔记渲染 `![封面|150](URL)`。
3. ✅ **DataviewJS 统计页**：`04-仪表盘/可视化统计.md`（评分分布 / 分类占比 / 各年读完）。

待做：见 **`docs/FEATURES.md`**（功能总表，单一事实来源，含验收标准与优先级）。
建议首批：A1 PyPI 发布 → B1 购书清单 → A2 文档完善 → C1 豆瓣元数据增强。
部署形态决策见 `docs/DEPLOYMENT.md`（已定：GitHub + pip 分发）。

每项都遵循 `CLAUDE.md` 的开发顺序，并保持离线可跑 + 补测试。

## 5. 待确认的开放问题（可问用户）
- 知识库主力数据源：以微信读书导入为主，还是手动藏书为主？（影响增量更新策略）
- 是否需要真实接入微信读书 Key 联调 weread 适配器？（目前仅按文档实现，未联调）
- 是否要 vendored 原项目的平台 API 文档到 `docs/weread-api/` 备查？
- 知识库语言/命名偏好（当前中文目录名，如 `01-书籍`）。

## 6. 环境与密钥
- 复制 `config.example.yaml` → `config.yaml`；`.env.example` → `.env`。
- `WEREAD_API_KEY`：接真实微信读书数据用（`platform: weread`）。
- `OPENAI_API_KEY`：设了就自动启用真实 LLM，否则用离线引擎。
- **不要把 `config.yaml` / `.env` / 真实 Key 提交进版本库。**

## 7. 质量门槛（提交前必过）
```bash
python -m pytest tests/ -q      # 全绿
python examples/demo.py         # 无报错，产物正常
```

## 8. 已知限制
见 `docs/PROJECT_PLAN.md` 第 6 节（weread 未联调、离线 AI 为占位、vault 全量覆盖等）。
