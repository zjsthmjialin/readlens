# 定时自动化（D1）· 让知识库自动生长

`readlens sync` 一条命令跑完整个流程：拉微信读书 → **增量更新**知识库 → 生成周/月报写进
`07-报告/` → 落统计快照。把它交给系统定时器，知识库就能定期自动更新。

> **为什么在本机跑？** 你的知识库在自己电脑上、Obsidian 要读它，云端摸不到本地文件，
> 所以定时任务要跑在你的 Mac（或你自己的服务器）上。

## 先手动验证一次

```bash
cd "/Users/jinsongmini/Projects/ReadLens  260808"
export WEREAD_API_KEY=wrk-你的key
python3 -m readlens.cli sync --platform weread --out ./MyVault --report-mode weekly
```
看到「知识库已更新 …」「已生成 weekly 报告 …」即成功。确认无误后再设定时。

## 方式 A · macOS launchd（推荐，开机常驻）

1. 新建 `~/Library/LaunchAgents/com.readlens.sync.plist`，内容如下
   （把 key、路径按需替换；每周一 08:00 跑一次周报）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.readlens.sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>-m</string><string>readlens.cli</string>
    <string>sync</string>
    <string>--platform</string><string>weread</string>
    <string>--out</string><string>/Users/jinsongmini/Projects/ReadLens  260808/MyVault</string>
    <string>--report-mode</string><string>weekly</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>WEREAD_API_KEY</key><string>wrk-你的key</string>
    <key>PYTHONPATH</key><string>/Users/jinsongmini/Projects/ReadLens  260808</string>
  </dict>
  <key>WorkingDirectory</key><string>/Users/jinsongmini/Projects/ReadLens  260808</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key><string>/tmp/readlens-sync.log</string>
  <key>StandardErrorPath</key><string>/tmp/readlens-sync.err</string>
</dict>
</plist>
```

2. 保护并加载：
```bash
chmod 600 ~/Library/LaunchAgents/com.readlens.sync.plist   # 里面有 key，只让自己读
launchctl load ~/Library/LaunchAgents/com.readlens.sync.plist
launchctl start com.readlens.sync                          # 立即跑一次验证
cat /tmp/readlens-sync.log                                 # 看输出
```

3. 常用管理：
```bash
launchctl unload ~/Library/LaunchAgents/com.readlens.sync.plist   # 停用
launchctl list | grep readlens                                    # 查看是否已注册
```

> 月报：把 `--report-mode weekly` 改成 `monthly`，`StartCalendarInterval` 改成
> `<key>Day</key><integer>1</integer>`（每月 1 号）。可以同时建两个 plist（周报+月报），Label 不同即可。

## 方式 B · cron（Linux / 也可用于 mac）

把 key 放进一个只读文件（不要写进 crontab 明文）：
```bash
echo 'export WEREAD_API_KEY=wrk-你的key' > ~/.readlens.env && chmod 600 ~/.readlens.env
crontab -e
```
加一行（每周一 08:00）：
```
0 8 * * 1 cd "/Users/jinsongmini/Projects/ReadLens  260808" && . ~/.readlens.env && /usr/bin/python3 -m readlens.cli sync --platform weread --out ./MyVault --report-mode weekly >> /tmp/readlens-sync.log 2>&1
```

## 安全与幂等

- **Key 安全**：只存在 plist（chmod 600）或 `~/.readlens.env`（chmod 600），不进代码库。
- **幂等**：`sync` 用增量更新，重复跑不会覆盖你的手写笔记/手填字段；同一周期的报告覆盖同一个文件（不会堆重复）。
- **看历史趋势**：每次 `sync` 会在 `06-统计快照/` 追加当日快照，`趋势.md` 自动对比。
- **Obsidian 刷新**：文件变化后，Dataview 会在你打开/切换笔记时自动更新，无需额外操作。

## 常见问题

- `ModuleNotFoundError: readlens` → `PYTHONPATH`/`WorkingDirectory` 要指到仓库根目录（含 `readlens/` 的那层）。
- 依赖缺失 → 先 `pip3 install requests pyyaml jinja2 matplotlib`。
- 想先不接 key 试跑 → 去掉 `--platform weread`，默认用离线 mock 数据。
