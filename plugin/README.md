# ReadLens 阅镜 · Obsidian 原生仪表盘插件

读 `#book` 笔记的 frontmatter，**原生渲染**读书仪表盘——**无需 Dataview**。
Apple 风设计：毛玻璃卡片、系统色、数字/条形/描边动画、Hero 大标题。

配合 [ReadLens 阅镜](https://github.com/zjsthmjialin/readlens) 生成的知识库使用效果最佳：
```bash
readlens vault --dashboards plugin --out ./MyVault
```
这样生成的整库仪表盘都用本插件的 ```readlens``` 块渲染，彻底不依赖 Dataview。

## 安装（手动，三个文件）

1. 在你的库里建目录：`<你的库>/.obsidian/plugins/readlens/`
2. 把本目录的 **`main.js`、`manifest.json`、`styles.css`** 三个文件复制进去
3. Obsidian → 设置 → 社区插件 →（关闭受限模式）→ 刷新 → 启用「ReadLens 阅镜」

## 用法

在任意笔记里插入代码块：

```` ```readlens
view: home
``` ````

支持的 `view`：

| view | 说明 | 常用参数 |
|------|------|----------|
| `home` | 首页概览：Hero + KPI + 正在读/最近读完/想读 | — |
| `stats` | 统计：评分分布 / 分类圆环 / 阅读热力 | — |
| `list` | 通用书单表格 | `status` `owned` `priority` `rated` `finished` `sort` `order` `limit` `columns` `title` |
| `author` | 当前作者的书（按笔记名匹配 author） | `columns` |
| `topic` | 当前分类的书（按笔记名匹配 category） | `columns` |

`columns` 可选列：`book, author, status, progress, rating, platform, finished, category, owned, priority, location, price, source`。

示例：
```` ```readlens
view: list
title: 📕 在读
status: 在读
sort: progress
order: desc
columns: [book, author, progress]
``` ````

## 从源码构建

```bash
cd plugin
npm install
npm run build      # 产出 main.js
```

## 许可证
Apache-2.0
