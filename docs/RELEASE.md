# 发布到 PyPI · 手把手命令清单（A1）

面向第一次发包的你：每一步都给出**要敲的命令 + 预期看到什么 + 出错怎么办**。
照着从上往下做即可。仓库地址已配置为 `https://github.com/zjsthmjialin/readlens`。

> 只有「上传」需要你的 PyPI 账号与 Token；构建和自检我都已在本项目验证过能通过。
> 建议**先发 TestPyPI 演练一遍**，确认无误再发正式 PyPI。

---

## 两条路：先选一条

- **路径 A · 自动发布（推荐，最省事）**：一次性网页配置后，以后发版你只需
  `git push` 一个标签，GitHub 自动构建并发到 PyPI，**你本地永远不碰 Token、不装工具**。
  见下方「路径 A」。仓库已内置 `.github/workflows/publish.yml`。
- **路径 B · 本地手动上传**：用 `twine` 从你电脑上传（步骤 0–8）。适合想完全手动掌控、
  或不想用 GitHub Actions 的情况。

无论哪条，都需要你先有 PyPI 账号（下方步骤 2）。**你的活儿本质只有三样**：注册账号、
（一次性）网页授权、敲 `git push` 或 `twine upload`——其余构建/校验都自动完成。

---

## 路径 A · 自动发布（Trusted Publishing）

**一次性配置（约 5 分钟，网页操作）**

1. 注册并登录 PyPI（见步骤 2），开启 2FA。
2. 打开 https://pypi.org/manage/account/publishing/ ，在「Add a new pending publisher」填：
   - PyPI Project Name：`readlens`
   - Owner：`zjsthmjialin`
   - Repository name：`readlens`
   - Workflow name：`publish.yml`
   - Environment name：`pypi`
   保存。（这一步让 PyPI「信任」你这个仓库的这个工作流，无需任何 Token。）
3. 在 GitHub 仓库建同名环境：仓库 → Settings → Environments → New environment → 命名 `pypi` → 保存。

**以后每次发版（你要做的全部）**
```bash
# 先把代码推上去（若还没推）
git push -u origin main
# 打标签并推送 —— 这一下就会触发自动构建 + 发布
git tag -a v0.2.0 -m "ReadLens v0.2.0"
git push origin v0.2.0
```
然后到仓库的 **Actions** 标签看「Publish to PyPI」跑绿即可。跑完 https://pypi.org/project/readlens/
就上线了。**全程你没碰 Token、没在本地构建。**

> 想先演练：把 publishing 配置和 workflow 指到 TestPyPI 也可以，需要时我帮你加一个测试版 workflow。

---

## 路径 B · 本地手动上传（备选）

下面 步骤 0–8 是完全手动的流程。若你已选路径 A，可跳过本节。

---

## 步骤 0 · 确认环境（约 1 分钟）

打开终端，进入项目目录（注意文件夹名里有两个空格，用引号包住）：
```bash
cd "ReadLens  260808"
```

确认 Python ≥ 3.9：
```bash
python --version        # 显示 Python 3.9.x 或更高即可（若提示找不到，试 python3 --version）
```
> 下文命令若你的系统用的是 `python3`/`pip3`，把 `python`/`pip` 相应替换即可。

---

## 步骤 1 · 安装打包工具（约 1 分钟）

```bash
pip install --upgrade build twine
```
**预期**：最后一行类似 `Successfully installed build-... twine-...`。
**出错**：若提示权限问题，加 `--user`：`pip install --user --upgrade build twine`。

---

## 步骤 2 · 注册账号 + 建 API Token（约 5 分钟，网页操作）

你需要**两个**账号（演练用 TestPyPI，正式用 PyPI），注册流程一样：

1. 注册正式 PyPI：https://pypi.org/account/register/
2. 注册 TestPyPI：https://test.pypi.org/account/register/
3. 两边都要**开启两步验证（2FA）**，否则不能建 Token（PyPI 现在强制）。
4. 建 API Token：
   - 正式：https://pypi.org/manage/account/token/ → Add API token → Scope 先选 "Entire account" → 创建
   - 测试：https://test.pypi.org/manage/account/token/ → 同上
5. **Token 只显示一次**，形如 `pypi-AgEIcHl...`，立刻复制保存好。

---

## 步骤 3 · 保存 Token 到 ~/.pypirc（约 2 分钟，一次性）

这样以后 `twine upload` 就不用每次手输了。在你的用户主目录建 `~/.pypirc`：

```bash
cat > ~/.pypirc <<'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
  username = __token__
  password = 把这里换成你的正式PyPI-Token(pypi-开头)

[testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = 把这里换成你的TestPyPI-Token(pypi-开头)
EOF
chmod 600 ~/.pypirc      # 只让自己可读，保护 Token
```
> `username` 就是字面量 `__token__`（不是你的用户名）；`password` 才是 Token。
> 不想存文件也行——跳过本步，上传时按提示手输：用户名填 `__token__`，密码粘贴 Token。

---

## 步骤 4 · 确认包名 `readlens` 没被占用（约 1 分钟）

浏览器打开 https://pypi.org/project/readlens/ ：
- 显示 **404 / 页面不存在** → 名字可用，继续。
- 显示已有别人的项目 → 需要改名。编辑 `pyproject.toml` 的 `name`（如 `readlens-kb`
  或 `readlens-cn`），同时把 README 里的 `pip install readlens` 一并改掉，再继续。

---

## 步骤 5 · 构建发行包（约 1 分钟）

```bash
rm -rf dist build *.egg-info      # 清掉旧产物
python -m build                   # 生成 dist/*.whl 和 dist/*.tar.gz
```
**预期**：结尾出现 `Successfully built readlens-0.2.0.tar.gz and readlens-0.2.0-py3-none-any.whl`，
且 `ls dist/` 能看到这两个文件。

自检元数据（README 能否在 PyPI 正常渲染等）：
```bash
twine check dist/*
```
**预期**：两行都是 `PASSED`。

---

## 步骤 6 · 先发 TestPyPI 演练（约 3 分钟）

上传到测试站：
```bash
twine upload --repository testpypi dist/*
```
**预期**：进度条跑完，末尾给出 `https://test.pypi.org/project/readlens/0.2.0/` 链接。

到一个干净环境验证能装能跑（用临时虚拟环境，避免污染系统）：
```bash
python -m venv /tmp/rl-test
source /tmp/rl-test/bin/activate         # Windows: \tmp\rl-test\Scripts\activate
pip install -i https://test.pypi.org/simple/ readlens
readlens --version                        # 期望输出 readlens 0.2.0
readlens quickstart                       # 期望生成 ./ReadLensDemo
deactivate
```
> TestPyPI 不镜像正式依赖，装依赖时偶尔会报找不到包；只要 `readlens` 本体装上、
> `--version` 正常即算演练通过（依赖会在正式 PyPI 正常解析）。

---

## 步骤 7 · 正式发布到 PyPI（约 1 分钟）

```bash
twine upload dist/*
```
**预期**：给出 `https://pypi.org/project/readlens/0.2.0/`。

全世界验证（任意干净环境）：
```bash
pip install readlens
readlens --version        # readlens 0.2.0
readlens quickstart
```
🎉 到这里就真正做到「别人 `pip install readlens` 即用」了。

---

## 步骤 8 · 打 Git 标签 + GitHub Release（约 3 分钟）

```bash
git tag -a v0.2.0 -m "ReadLens v0.2.0：封面 + 可视化 + 增量更新 + 购书清单 + 元数据增强 + pip 分发"
git push origin v0.2.0
```
然后到 https://github.com/zjsthmjialin/readlens/releases/new ：选择 tag `v0.2.0`，
标题填 `ReadLens v0.2.0`，正文可摘录 `docs/FEATURES.md` 的「已完成」部分，附一张知识库截图，
Publish。

---

## 常见错误速查

| 报错 | 原因 | 解决 |
|------|------|------|
| `403 Invalid or non-existent authentication` | Token 错/用户名没写 `__token__` | 检查 `~/.pypirc`：username 必须是 `__token__`，password 是 `pypi-...` |
| `400 File already exists` | 该版本已上传过，PyPI 不允许覆盖 | 升版本号：改 `pyproject.toml` 的 `version` 与 `readlens/__init__.py` 的 `__version__`（如 0.2.1），重跑步骤 5、7 |
| `The name 'readlens' isn't allowed / already in use` | 包名被占 | 见步骤 4 改名 |
| `twine check` 报 README 渲染问题 | 描述格式问题 | 一般能 PASSED；若失败按提示修 README |
| 找不到 `twine` 命令 | 脚本目录不在 PATH | 用 `python -m twine upload ...` 代替 `twine ...` |

---

## 以后每次发新版本（三步）
1. 改版本号：`pyproject.toml` 的 `version` 和 `readlens/__init__.py` 的 `__version__`（两处一致）。
2. `python -m pytest tests/ -q` 全绿 + `readlens quickstart` 冒烟。
3. 重跑步骤 5 → 7 → 8。

## 进阶（可选）：自动发布
可加一个 GitHub Actions 工作流，push `v*` 标签时用
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) 自动发布，
免手动 `twine upload`、也无需在本地存 Token。需要我就帮你加这个 workflow。
