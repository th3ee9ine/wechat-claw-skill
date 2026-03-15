# OpenClaw Integration Guide

Overview: [../README.md](../README.md) | 中文总览: [README.zh.md](./README.zh.md) | 中文接入: [openclaw.zh.md](./openclaw.zh.md)

This repository already declares `openclaw` compatibility and can be used as an OpenClaw skill. The current `SKILL.md` declares these runtime requirements:

- `python3`
- `nanobanana-pro-fallback`
- `wechat-mp`
- `searxng`

## Recommended: install as a workspace skill

The OpenClaw README documents the workspace skill path as:

```text
~/.openclaw/workspace/skills/<skill>/SKILL.md
```

If you changed the workspace root in your OpenClaw config, replace `~/.openclaw/workspace` below with your actual path.

The simplest integration path is to place this repository under that directory.

### 1. Prepare the repo

```bash
git clone https://github.com/th3ee9ine/wechat-claw.git
cd wechat-claw
```

If you already maintain a local checkout, reuse that path.

### 2. Link it into the OpenClaw skills directory

Using a symlink keeps updates simple:

```bash
mkdir -p ~/.openclaw/workspace/skills
ln -sfn /abs/path/to/wechat-claw ~/.openclaw/workspace/skills/wechat-claw
```

If you want the folder name to match the skill name, this also works:

```bash
ln -sfn /abs/path/to/wechat-claw ~/.openclaw/workspace/skills/wechat-mp-writer
```

The important part is that the target directory directly contains `SKILL.md`.

### 3. Install companion skills if you need the full pipeline

This skill owns the article-writing and publishing pipeline, but the end-to-end workflow also depends on:

- `nanobanana-pro-fallback` for cover and inline image generation
- `wechat-mp` for uploads, draft creation, and publishing
- `searxng` for source lookup and retrieval

If you only need local HTML rendering, validation, and image planning, those skills are optional.

### 4. Reload OpenClaw

Reload or restart OpenClaw so it rescans `~/.openclaw/workspace/skills/`.

### 5. Typical prompts

Examples:

- “Use `wechat-mp-writer` to render this article JSON into WeChat HTML.”
- “Use `wechat-mp-writer` to plan cover and inline images, then output a publish-ready article JSON.”
- “Collect sources from these URLs and markdown files, then turn them into a WeChat article draft.”

## Runtime path rule

This is the main integration gotcha.

Inside OpenClaw, the current working directory is usually not the skill root. Do not assume `scripts/...` resolves correctly. Prefer absolute paths rooted at the installed skill directory:

```bash
SKILL_ROOT="$HOME/.openclaw/workspace/skills/wechat-claw"

python3 "$SKILL_ROOT/scripts/render_article.py" article.json -o build/article.html --check
python3 "$SKILL_ROOT/scripts/validate_article.py" article.json --html build/article.html
python3 "$SKILL_ROOT/scripts/plan_images.py" article.json --write-article build/article.with-images.json
```

If you linked the skill as `wechat-mp-writer`, point `SKILL_ROOT` there instead.

Recommended practice:

- keep source files and article JSON in your working project directory
- write outputs into `build/` or another work directory
- avoid writing generated artifacts back into the skill directory

## Full publishing pipeline

For the full pipeline, `run_pipeline.py` also needs explicit paths to the image-generation and WeChat helper scripts:

```bash
SKILL_ROOT="$HOME/.openclaw/workspace/skills/wechat-claw"

python3 "$SKILL_ROOT/scripts/run_pipeline.py" article.json \
  --output-dir build \
  --nanobanana-script /abs/path/to/generate_image.py \
  --wechat-script /abs/path/to/wechat_mp.py \
  --create-draft \
  --publish
```

`--nanobanana-script` and `--wechat-script` can point to:

- your own compatible wrappers
- absolute paths exposed by other skills
- a thin wrapper script you keep locally

## ClawHub

The OpenClaw README describes ClawHub as a minimal skill registry. If you want OpenClaw to discover and pull this skill through ClawHub, you can publish this repository as a skill package.

This repo already satisfies the basic packaging shape:

- `SKILL.md` is at the skill root
- `SKILL.md` declares `openclaw` compatibility
- scripts, templates, and references live alongside the skill root

## nix-openclaw native plugin mode

If you use `nix-openclaw` with `plugins = [{ source = ...; }]`, note that the documented plugin contract expects at least:

```text
flake.nix
skills/<skill>/SKILL.md
```

and `flake.nix` must export `openclawPlugin`.

This repository does not ship that Nix wrapper yet, so for now you should either:

- use the workspace-skill approach above
- add a thin plugin-wrapper repository that references this repo

## Troubleshooting

### `python3` is missing

Make sure the OpenClaw runtime environment has `python3` on `PATH`.

### The skill loads, but scripts fail with “No such file or directory”

That almost always means the command still uses a relative path like `scripts/render_article.py`. Switch to an absolute path under the installed skill root.

### HTML renders, but publish fails

This repository handles article structure, rendering, and pipeline orchestration. Actual uploads, draft creation, and publishing still depend on a `wechat-mp` compatible helper and valid WeChat permissions.

### I only want layout/rendering inside OpenClaw

That is fine. You only need:

- `scripts/validate_article.py`
- `scripts/plan_images.py`
- `scripts/render_article.py`

## References

- OpenClaw official README: <https://github.com/openclaw/openclaw/blob/main/README.md>
- nix-openclaw official README: <https://github.com/openclaw/nix-openclaw/blob/main/README.md>
