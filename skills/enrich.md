# enrich — 书目元数据增强

给缺字段的书补全 **isbn / cover / publisher / pubdate**，配合封面图与知识库更完整。

## 何时使用
- 用户说「补全 ISBN/封面/出版信息」「元数据增强」「书的封面缺了」

## 命令
```
readlens enrich [--source mock|douban] [--manual books.json]      # 预览会补什么（不落库）
readlens vault --enrich [--enrich-source mock|douban] --out ./MyVault   # 生成前顺带补全
```

## 来源
- `mock`（默认，**离线可跑**）：确定性预置数据，用于演示与测试。
- `douban`（在线，best-effort）：豆瓣 suggest 接口补 cover/pubdate；任何网络/解析错误都
  **降级为不补全**，绝不影响主流程。带本地缓存 `.readlens_cache/douban.json`。

## 设计要点（见 `readlens/enrich/`）
- 可插拔 `MetadataFetcher`（`base.py`）；`get_fetcher(source)` 选择实现。
- **只填空、不覆盖**：与 vault 增量更新「保护手填字段」一致——已有 isbn/publisher 不动。
- 豆瓣不抓 ISBN（详情页不稳定）；需要 ISBN 用离线预置或人工补。

## 扩展新来源
实现一个 `MetadataFetcher` 子类（如 Google Books），在 `get_fetcher` 注册即可，上层零改动。
