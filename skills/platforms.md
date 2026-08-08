# platforms — 多平台适配（延展能力）

ReadLens 把「阅读平台」抽象成统一接口 `ReadingPlatform`。上层导出/报告/AI
只依赖统一模型，因此可以把同一套能力复刻到不同平台。

## 已内置
| 平台 | 适配器 | 说明 |
|------|--------|------|
| mock | `MockPlatform` | 离线示例数据，无需 Key，用于体验/开发/测试 |
| weread | `WeReadPlatform` | 微信读书，按 Tencent/WeChatReading 网关协议实现，需 `WEREAD_API_KEY` |

切换平台：改 `config.yaml` 的 `platform:` 或命令行 `--platform`。

## 复刻到新平台（如豆瓣读书 / Kindle / Readwise）
1. 在 `readlens/adapters/` 新建 `xxx.py`，继承 `ReadingPlatform`。
2. 实现必需方法：`search / book_info / shelf / notebooks / book_notes / read_stat`；
   可选实现 `popular_highlights` 和写入类 `add_to_shelf / create_thought`。
3. 关键工作是**字段映射**：把该平台原始返回映射到 `readlens.models` 的
   `Book / Highlight / Thought / Note / ReadStat`。`mock.py` 是最好的映射参照。
4. 在 `adapters/__init__.py` 的 `get_platform()` 里注册平台名。
5. 完成后，导出/报告/AI 全部能力自动可用，无需改动上层代码。

## 统一模型速览
- `Book(book_id, title, author, category, rating, finished, progress...)`
- `Highlight(text, chapter_title, chapter_idx, popular_count...)`
- `Thought(content, abstract, star, is_book_review...)`
- `Note(book, highlights[], thoughts[], bookmark_count)` — `total_count` 沿用原项目统计口径
- `ReadStat(total_read_time秒, read_days, prefer_category[], prefer_time[24], read_longest[]...)`
