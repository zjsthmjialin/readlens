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

### Phase 1 · 打磨知识库（近期，优先）
- [ ] 书籍笔记内嵌封面图（cover 字段落地为 Obsidian 图片/外链）
- [ ] DataviewJS 可视化统计页：年度阅读热力图、分类占比、评分分布
- [ ] 增量更新：重复运行 vault 时**合并**而非覆盖用户手写内容（保护 `## 主题笔记`、`## 关于` 等人写区块）
- [ ] 愿望清单 → 购书清单（owned=none 的书聚合，可标记优先级）

### Phase 2 · 数据更丰富
- [ ] 豆瓣适配器：补全 ISBN、封面、出版信息（作为 `douban` 平台或元数据增强）
- [ ] 微信读书写操作：`create_thought` / `add_to_shelf` 真实实现（接口已在 base 预留）
- [ ] 阅读统计快照存档：每次导入落一份带日期的统计，支持趋势对比

### Phase 3 · 分发与自动化
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
- `weread` 适配器未经真实 Key 联调（无 Key 环境）；字段映射基于原项目文档，接入真实数据后需校验。
- 离线 AI 引擎是抽取式占位，质量有限；接入 LLM 后显著提升。
- vault 目前是全量生成/覆盖，用户在生成文件里手写的内容会被下次生成覆盖（见 Phase 1 增量更新）。

## 7. 版本
- v0.1.0（当前）：五大能力 + 知识库，离线可跑。
- v0.2.0（计划）：Phase 1 完成 = 知识库可日常使用、封面 + DataviewJS + 增量更新。
