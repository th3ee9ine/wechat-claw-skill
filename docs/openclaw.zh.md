# openClaw 接入教程

Overview: [../README.md](../README.md) ｜ 中文总览: [README.zh.md](./README.zh.md) ｜ English: [openclaw.en.md](./openclaw.en.md)

这个仓库已经包含 `openclaw` 兼容声明，可以直接作为 OpenClaw skill 使用。当前 `SKILL.md` 中声明的依赖如下：

- `python3`
- `nanobanana-pro-fallback`
- `wechat-mp`
- `searxng`

## 推荐方式：作为 workspace skill 直接接入

OpenClaw 官方 README 约定 workspace 技能目录为：

```text
~/.openclaw/workspace/skills/<skill>/SKILL.md
```

如果你在 OpenClaw 配置里改过 workspace 根目录，把下面所有 `~/.openclaw/workspace` 替换成你的实际路径。

最直接的接入方式就是把本仓库放到这个目录下。

### 1. 准备仓库

```bash
git clone https://github.com/th3ee9ine/wechat-claw.git
cd wechat-claw
```

如果你已经在本地维护这个仓库，直接复用现有路径即可。

### 2. 挂到 OpenClaw skills 目录

推荐用软链，更新仓库时不需要重复复制：

```bash
mkdir -p ~/.openclaw/workspace/skills
ln -sfn /abs/path/to/wechat-claw ~/.openclaw/workspace/skills/wechat-claw
```

如果你更喜欢目录名和 skill 名保持一致，也可以链接成：

```bash
ln -sfn /abs/path/to/wechat-claw ~/.openclaw/workspace/skills/wechat-mp-writer
```

两种目录名都可以，关键是目标目录里要直接包含 `SKILL.md`。

### 3. 补齐依赖

这个 skill 只负责“公众号文章结构化写作与发布流水线”，完整跑通还需要这些配套 skill：

- `nanobanana-pro-fallback`：生成封面图和正文配图
- `wechat-mp`：上传图片、创建草稿、发布文章
- `searxng`：做资料检索或补充来源

如果只是本地渲染 HTML、校验 JSON、规划图片 prompt，这三个依赖不是强制的。

### 4. 重启或重新加载 OpenClaw

让 OpenClaw 重新扫描 `~/.openclaw/workspace/skills/`，然后就可以在对话里直接调用这个 skill。

### 5. 典型调用方式

可以直接对 agent 说：

- “使用 `wechat-mp-writer` skill，把这个 article JSON 渲染成公众号 HTML。”
- “用 `wechat-mp-writer` 先规划封面图和正文图，再输出可发布的 article JSON。”
- “先根据这些 URL 和 markdown 文件收集 sources，再整理成公众号文章。”

## 运行时路径规则

这是接入 OpenClaw 时最容易踩坑的一点。

OpenClaw 的当前工作目录通常不是 skill 根目录，所以执行本仓库脚本时，不要默认用相对路径。优先使用 skill 目录的绝对路径，例如：

```bash
SKILL_ROOT="$HOME/.openclaw/workspace/skills/wechat-claw"

python3 "$SKILL_ROOT/scripts/render_article.py" article.json -o build/article.html --check
python3 "$SKILL_ROOT/scripts/validate_article.py" article.json --html build/article.html
python3 "$SKILL_ROOT/scripts/plan_images.py" article.json --write-article build/article.with-images.json
```

如果你把 skill 链接成了 `wechat-mp-writer`，把上面的 `SKILL_ROOT` 改成对应目录即可。

建议：

- 输入文章 JSON、素材文件放在你的当前项目目录
- 输出文件写到当前项目的 `build/` 或其他工作目录
- 不要把生成物回写到 skill 目录本身

## 完整发布链路怎么接

如果要跑完整流水线，`run_pipeline.py` 需要额外知道图片生成脚本和公众号脚本的位置：

```bash
SKILL_ROOT="$HOME/.openclaw/workspace/skills/wechat-claw"

python3 "$SKILL_ROOT/scripts/run_pipeline.py" article.json \
  --output-dir build \
  --nanobanana-script /abs/path/to/generate_image.py \
  --wechat-script /abs/path/to/wechat_mp.py \
  --create-draft \
  --publish
```

这里的 `--nanobanana-script` 和 `--wechat-script` 可以指向：

- 你自己维护的兼容脚本
- 其他 skill 暴露出来的脚本绝对路径
- 包一层 thin wrapper 之后的统一入口

## ClawHub 接入

OpenClaw 官方 README 里把 ClawHub 定义为“minimal skill registry”。如果你想让 agent 后续通过 ClawHub 自动发现和拉取这个 skill，可以把当前仓库作为 skill 包发布到 ClawHub。

当前仓库已经具备这些前置条件：

- skill 根目录直接包含 `SKILL.md`
- `SKILL.md` 已声明 `openclaw` 兼容平台
- 资源、模板、脚本都跟 skill 根目录放在同一层级

## nix-openclaw 原生插件模式

如果你使用的是 `nix-openclaw` 的 `plugins = [{ source = ...; }]` 机制，要注意官方插件契约要求仓库至少包含：

```text
flake.nix
skills/<skill>/SKILL.md
```

并且 `flake.nix` 需要导出 `openclawPlugin`。

当前仓库还没有内置这层 Nix 包装，所以要走原生插件模式时，建议二选一：

- 先用上面的 workspace skill 方式接入
- 再额外做一个很薄的 plugin wrapper 仓库，把本仓库作为资源引用进去

## 常见问题

### 找不到 `python3`

确认 OpenClaw 运行环境里 `python3` 在 `PATH` 上。

### 能看到 skill，但脚本执行报 “No such file or directory”

基本都是因为命令是在别的工作目录里执行的，仍然写成了 `scripts/render_article.py` 这种相对路径。改成 skill 根目录的绝对路径即可。

### 能渲染 HTML，但发布失败

本仓库只负责文章结构、模板渲染和发布流水线编排。真正的图片上传、草稿创建、发布依赖 `wechat-mp` 兼容脚本和公众号权限。

### 只想在 OpenClaw 里用排版，不想接发布

完全可以。只跑下面三个脚本就够了：

- `scripts/validate_article.py`
- `scripts/plan_images.py`
- `scripts/render_article.py`

## 参考

- OpenClaw 官方仓库 README：<https://github.com/openclaw/openclaw/blob/main/README.md>
- nix-openclaw 官方仓库 README：<https://github.com/openclaw/nix-openclaw/blob/main/README.md>
