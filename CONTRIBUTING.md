# 贡献指南

欢迎为 ReadLens 贡献代码、文档或新平台适配器。

## 本地开发

```bash
git clone https://github.com/zjsthmjialin/readlens.git
cd readlens
pip install -e ".[dev]"        # 装上开发依赖（含 pytest）
python examples/demo.py         # 无需 Key，端到端跑通
python -m pytest tests/ -q      # 期望全绿
```

## 硬性约束

- **离线可跑**：没有 API Key 时必须能用 `mock` 平台 + `offline` AI 引擎跑通全部流程。
  新功能都要保留离线路径。
- **统一模型优先**：平台数据先归一化到 `readlens/models.py`；上层（export/report/ai/vault）
  只依赖统一模型，不直接碰平台原始字段。
- **中文优先**：面向用户的文案、文档、注释用中文。

## 开发顺序（新增能力）

先写/改统一模型 → 适配器 → 上层功能 → CLI 子命令 → `skills/*.md` → 补 `tests/`。

## 提交前质量门槛

```bash
python -m pytest tests/ -q      # 全绿
python examples/demo.py         # 无报错，产物正常
```

## 新增一个阅读平台

继承 `readlens/adapters/base.ReadingPlatform`，把该平台原始字段映射到统一模型，
再在 `adapters/__init__.get_platform` 注册即可，上层零改动。`adapters/mock.py` 是最佳映射参照。

## 发布（维护者）

见 [`docs/RELEASE.md`](docs/RELEASE.md)。已配置 Trusted Publishing：改版本号 → 推 `v*` 标签
→ GitHub Actions 自动构建并发布到 PyPI。

## 更多约定

见 [`CLAUDE.md`](CLAUDE.md)（项目约定）与 [`docs/`](docs/)（规划 / 功能总表 / 交接）。
