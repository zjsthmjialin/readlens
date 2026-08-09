# automation — 定时自动化（sync）

一条命令跑完「拉数据 → 增量更新知识库 → 生成周/月报 → 落统计快照」。

## 何时使用
- 用户说「每周自动更新我的读书库」「定时生成周报/月报」「让知识库自动同步」

## 命令
```
readlens sync --platform weread --out ./MyVault --report-mode weekly|monthly|annually|none \
              [--manual books.json] [--enrich] [--overwrite]
```
- 需要 `WEREAD_API_KEY`（接真实数据）；不加 `--platform weread` 则用离线 mock。
- 幂等：增量更新不覆盖手写内容；同周期报告覆盖同一文件。

## 产物
- 知识库照常更新（书籍/作者/主题/仪表盘/可视化）。
- `07-报告/{周报|月报}-{周期}.md`：时长/天数/对比/Top 书/偏好/AI 小结。
- `06-统计快照/history.json` + `趋势.md`：累积对比。

## 定时（本机）
见 [`docs/AUTOMATION.md`](../docs/AUTOMATION.md)：macOS launchd（推荐）或 Linux cron。
Key 只存 plist（chmod 600）或 `~/.readlens.env`，不进代码库。

## 设计
- `readlens/report/digest.py`：ReadStat → markdown 周期报告；`period_slug` 决定幂等文件名。
- `cli.cmd_sync`：串起 notebooks/book_notes → build_vault（增量+快照）→ digest 写入。
