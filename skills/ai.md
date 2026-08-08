# ai — AI 增值分析（延展能力）

在读取到的笔记与统计之上叠加 LLM 能力。所有能力走统一 `LLMEngine`：
未配置 `OPENAI_API_KEY` 时用内置**离线模板引擎**（抽取式摘要），配置后自动切换真实 LLM。

## 何时使用
- “帮我总结这本书的笔记”→ summarize
- “这几本书有什么共通主题”→ themes
- “根据我这本书的划线，回答 xxx”→ ask
- “根据我的阅读偏好推荐几本书”→ recommend

## 命令
```
readlens ai summarize --book <bookId>
readlens ai themes [--topic 文明]
readlens ai ask --book <bookId> --q "问题"
readlens ai recommend
```

## 能力说明
| 子命令 | 输入 | 输出 |
|--------|------|------|
| summarize | 单本书划线+想法 | 3-5 个核心观点 + 一句最大启发 |
| themes | 多本书划线 | 2-3 条跨书主题联系 + 延伸思考问题 |
| ask | 某书笔记 + 问题 | 基于笔记的问答（内置极简检索，只用笔记材料作答） |
| recommend | 偏好分类/作者 + 已读 | N 本荐书，含理由，排除已读 |

## 注意
- 离线引擎输出会标注“【离线摘要引擎输出】”，用于占位演示；接入 LLM 后质量显著提升。
- `ask` 只依据用户自己的划线/想法作答，材料不足会明确说明——避免编造。
