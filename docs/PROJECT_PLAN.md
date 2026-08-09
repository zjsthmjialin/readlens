# ReadLens 项目规划

## 1. 愿景
把分散在阅读平台里的读书数据（书目、划线、想法、统计）与个人藏书，沉淀为一个
**可导出、可分析、可持续生长的个人知识库**。最终形态是一个 Obsidian 仓库——
每本书是一张互相链接的笔记，配合 Dataview 成为「个人图书馆 + 读书大脑」。

脱胎于 [Tencent/WeChatReading](https://github.com/Tencent/WeChatReading) Skills，
但从「一组面向 Agent 的接口文档」升级为「可运行的工具 + 知识库生成器」。

## 2. 现状（v0.1.0）— 已完成
| 模块 | 状态 | 说明 |
|------|------|------|
| 平台适配层 | ✅ | `base` 抽象 + `mock`（离线示例）+ `weread`（网关协议）|
| 统一数据模型 | ✅ | Book / Highlight / Thought / Note / ReadStat |
| 多格式导出 | ✅ | Markdown / Obsidian / Notion(blocks JSON) |
| 读书报告 | ✅ | HTML 报告 + 4 张 matplotlib 图表 |
| AI 增值 | ✅ | 总结 / 跨书主题 / 问答 / 推荐，离线引擎 + OpenAI 可选 |
| Obsidian 知识库 | ✅ | 书籍笔记 / 作者页 / 主题 MOC / Dataview 仪表盘 / 时间线 / 模板 |
| CLI | ✅ | search / shelf / notes / export / report / ai / vault |
| 测试 | ✅ | 7 个单测通过，demo 端到端可跑 |

**硬性约束**：无 API Key 时用 mock + 离线 AI 引擎跑通全部流程。

## 3. 架构总览
```
阅读平台(微信读书/未来豆瓣等) ──适配器──▶ 统一模型 ──▶ 导出 / 报告 / AI / 知识库
                                   ▲
                      手动藏书(JSON/模板) ┘
```
分层解耦：新增平台或新增输出形态，互不影响。详见 `CLAUDE.md`「关键设计决策」。

## 4. 路线图

> 📋 **完整待做功能清单见 [`docs/FEATURES.md`](FEATURES.md)**（单一事实来源，含每项验收标准与优先级）。
> 下面按 Phase 概览；勾选状态与 FEATURES.md 保持一致。

### Phase 1 · 打磨知识库（近期，优先）
- [x] 书籍笔记内嵌封面图（cover 落地为 `![封面|150](URL)` 外链图片）
- [x] DataviewJS 可视化统计页：评分分布 / 分类占比 / 各年读完数量（`04-仪表盘/可视化统计.md`）
- [x] 增量更新：重复运行 vault 时**合并**而非覆盖（标记注释包裹自动区；frontmatter 保护手填字段）。见 `vault/merge.py`。
- [ ] 愿望清单 → 购书清单（owned=none 的书聚合，可标记优先级）

### Phase 2 · 数据更丰富
- [x] 豆瓣元数据增强：`readlens/enrich/`（mock 离线 + douban 在线降级），补 ISBN/封面/出版信息
- [ ] 微信读书写操作：`create_thought` / `add_to_shelf` 真实实现（接口已在 base 预留）
- [x] 阅读统计快照存档：每次导入落一份带日期快照（`06-统计快照/`）+ 趋势对比页

### Phase 3 · 分发与自动化
- [x] **pip 包分发**：`pip install readlens` + `readlens quickstart` 一键上手；
      pyproject 元数据/入口点 + GitHub Actions CI 就绪（v0.2.0，定位「分发给别人用」）。
- [ ] 打包成原项目那种 `npx skills add` 的 Skill 包形态
- [ ] 定时任务：周期性导入 + 生成周报/月报，推送到知识库
- [ ] 更多平台适配器：Kindle 标注、Readwise、微信收藏

## 5. Backlog（想法池，未排期）
- 划线全文检索（本地向量库）+ 跨书语义问答
- 读书笔记自动打标签（AI 主题标注）
- 与日历/日记联动的阅读打卡
- 多用户/多 vault 配置

## 6. 已知限制与技术债
- 原项目的平台侧 Skill 文档（search/book/shelf/notes/readdata/review/discover）未随本项目 vendored；weread 适配器按其口径用代码实现。若需可把原始 `.md` 收进 `docs/weread-api/` 备查。
- ~~`weread` 适配器未联调~~ → v0.4.0 已按官方 2026 skills 文档对齐并**用真实 Key 线上联调通过**。
- 离线 AI 引擎是抽取式占位，质量有限；接入 LLM 后显著提升。
- ~~vault 全量覆盖会丢手写内容~~ → 已在 v0.2.0 用增量合并解决（`--overwrite` 可强制全量）。

## 7. 版本
- v0.1.0：五大能力 + 知识库，离线可跑。
- v0.2.0：Phase 1 = 封面 + DataviewJS 可视化 + 增量更新；pip 分发 + CI + **已发布 PyPI**。
- v0.3.0（当前）：阅读热力日历 + 统计快照/趋势 + 示例藏书随包 + 元数据增强(豆瓣)。
