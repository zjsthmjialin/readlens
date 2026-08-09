# 更新日志 Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.5.0] - 2026-08-09
### 新增（D1 定时自动化）
- **`readlens sync`**：一条命令完成「拉数据 → 增量更新知识库 → 生成周/月报写入 `07-报告/` → 落统计快照」，幂等可重复跑。
- **周期报告摘要** `readlens/report/digest.py`：把 ReadStat 渲染成 Obsidian 原生 markdown 周报/月报（时长/天数/对比/Top 书/偏好/AI 小结），同周期覆盖同一文件。
- **`docs/AUTOMATION.md`**：macOS launchd + Linux cron 定时方案，含 Key 安全与幂等说明。

## [0.4.0] - 2026-08-09
### 修正（weread 适配器按官方 2026 规格对齐）
- 网关地址改为官方 `https://i.weread.qq.com/api/agent/gateway`（原默认误指取 Key 页面）。
- `/book/info` 补充映射 `isbn` / `publishTime`→`pubdate`；weread 书正确标记 `source=weread, owned=digital`。
- `book_notes` 增调 `/book/getprogress` 回填阅读进度与读完状态（否则统一模型误判为「想读」）。
- 书架读完状态改用官方字段 `finishReading`（原误用 `markedStatus`）。
- 修复 `config.py` 默认网关（原代码默认仍指向取 Key 页面，导致返回 HTML 而非 JSON）。
- `_call` 增强诊断：非 JSON / 非 200 / errcode 非 0 时给出清晰错误；新增 `readlens weread-check` 鉴权诊断命令。
- 新增离线映射测试：用假网关按官方文档字段结构校验 search/shelf/book_notes/read_stat。
> ✅ 已用真实 Key 线上联调通过：search / shelf / notebooks / book_notes / getprogress / readdata / vault 全链路。

## [0.3.1] - 2026-08-09
### 变更
- 确定中文名为 **阅镜**（ReadLens：阅=read，镜=lens），替换旧中文名「读透」。
### 文档
- README「效果预览」改用真实资产：知识库首页结构示意 SVG + `readlens report` 真实图表。
- 新增 `CHANGELOG.md`、`CONTRIBUTING.md`，提升开源可用性。

## [0.3.0] - 2026-08-09
### 新增
- **阅读热力日历**：可视化统计页新增按 `finished` 月份的「年×月」热力网格（DataviewJS）。
- **统计快照与趋势**：每次生成 vault 落一份带日期快照到 `06-统计快照/history.json`
  （按日期 upsert 累积），并生成 `趋势.md` 展示历次「与上期对比(±)」；`vault --no-snapshot` 可关。
- **示例藏书随包**：内置 `readlens/sampledata.py`；`readlens quickstart --with-manual`
  无需外部文件即可演示手动藏书入库与购书清单。
### 变更
- `Book` 模型新增 `isbn` / `pubdate` 字段。

## [0.2.0] - 2026-08-09
### 新增
- **vault 增量更新**：自动区用标记注释包裹，重复生成只刷新自动区；frontmatter 保护
  手填字段（rating/location/price/isbn/cover/owned/priority…）。`vault --overwrite` 可全量。
- **书籍笔记内嵌封面图**（`cover` → `![封面|150](URL)`）。
- **DataviewJS 可视化统计页**：评分分布 / 分类占比 / 各年读完。
- **购书清单**：聚合 `owned: none`，按 `priority` 排序、`price_target` 记心理价位。
- **豆瓣元数据增强**：可插拔 `readlens/enrich/`（mock 离线 + douban 在线降级），
  `readlens enrich` 预览、`readlens vault --enrich` 落库；只填空不覆盖。
- **一键上手**：`readlens quickstart` 用内置离线数据生成演示知识库，无需 Key。
- **分发**：`pyproject.toml` 打包、`readlens` 入口点、`--version`；GitHub Actions CI +
  Trusted Publishing 自动发布；发布到 PyPI。

## [0.1.0]
### 新增
- 五大能力：平台适配层 / 多格式导出（Markdown·Obsidian·Notion）/ 读书报告（HTML+图表）/
  AI 增值（总结·主题·问答·推荐，离线可跑）/ Obsidian 知识库生成。
- CLI：search / shelf / notes / export / report / ai / vault。离线 mock 平台 + 离线 AI 引擎。
