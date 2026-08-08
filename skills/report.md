# report — 读书报告（延展能力）

把 `readdata` 的阅读统计组织成可视化报告（HTML + 图表），可选附加 AI 总结。

## 何时使用
- 用户说“生成我的月度/年度读书报告”“做个阅读复盘”“我今年读书数据可视化”

## 命令
```
readlens report --mode monthly [--ai] [--out <dir>]
readlens report --mode annually --ai
```
`--mode`: weekly | monthly | annually | overall；`--ai` 附加个性化阅读总结。

## 产物
- `report_<mode>.html` — 卡片式总览 + 图表 + 排行 + 偏好分析
- `charts/*.png` — 每日趋势、分类环形图、24 小时时段分布、读得最多的书

## 口径要点（沿用 readdata.md）
- 所有时长字段单位是**秒**，展示时转“x 小时 y 分钟”。
- 总时长优先用 `totalReadTime`；跨周期用「完整周期累加 + 边界日级 `dailyReadTimes` 修正」。
- `dayAverageReadTime` 是按自然日平均，不是按阅读天数；如需阅读日均用 `totalReadTime / readDays`。
- `preferTime` 从 6 点开始排列，绘图时需还原到自然小时顺序。

## 工作流
1. 调 `read_stat(mode)` 取统计。
2. `build_report()` 整理为报告字典。
3. 生成图表 → 渲染 HTML；若 `--ai`，调 `summarize_reading()` 生成总结段落插入报告。
