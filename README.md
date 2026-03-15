# wechat-claw

项目总览。Detailed docs:

- 中文文档: [docs/README.zh.md](./docs/README.zh.md)
- English documentation: [docs/README.en.md](./docs/README.en.md)
- OpenClaw 接入: [docs/openclaw.zh.md](./docs/openclaw.zh.md)
- OpenClaw integration: [docs/openclaw.en.md](./docs/openclaw.en.md)

微信公众号文章工具集，用于把结构化 JSON 内容渲染成公众号 HTML，并串联校验、配图规划、图片上传、草稿创建和发布流程。  
`wechat-claw` is a toolkit for turning structured JSON articles into WeChat-ready HTML, with validation, image planning, upload, draft creation, and publishing helpers.

## Overview

当前仓库聚焦结构化的公众号文章生产与发布链路：

- Multi-template WeChat article rendering from JSON
- Article validation for metadata, structure, and unresolved placeholders
- Automatic cover/body image planning
- Optional pipeline hooks for image generation, upload, draft creation, and publish
- Source collection from files, URLs, and raw text

## Templates

Supported templates:

- `daily-intelligence`
- `weekly-financial`
- `deep-analysis`
- `industry-radar`
- `product-release`
- `breaking-watch`

Template files live in [`templates/`](./templates).

## Scripts

Core entry points:

- [`scripts/collect_sources.py`](./scripts/collect_sources.py)
- [`scripts/render_article.py`](./scripts/render_article.py)
- [`scripts/validate_article.py`](./scripts/validate_article.py)
- [`scripts/plan_images.py`](./scripts/plan_images.py)
- [`scripts/run_pipeline.py`](./scripts/run_pipeline.py)

## Docs

Choose one of the detailed guides:

- 中文: [docs/README.zh.md](./docs/README.zh.md)
- English: [docs/README.en.md](./docs/README.en.md)
- OpenClaw 接入: [docs/openclaw.zh.md](./docs/openclaw.zh.md)
- OpenClaw integration: [docs/openclaw.en.md](./docs/openclaw.en.md)

## Repository Layout

```text
docs/                   中文 / English 详细文档
templates/              公众号 HTML 模板
scripts/article_lib.py  核心渲染与校验逻辑
scripts/render_article.py
scripts/validate_article.py
scripts/plan_images.py
scripts/run_pipeline.py
scripts/collect_sources.py
references/             写作、标题、图片提示词参考
```

## Star History

<a href="https://www.star-history.com/?repos=th3ee9ine%2Fwechat-claw&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=th3ee9ine/wechat-claw&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=th3ee9ine/wechat-claw&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=th3ee9ine/wechat-claw&type=date&legend=top-left" />
 </picture>
</a>
