# wechat-claw

English detailed documentation. Overview: [../README.md](../README.md) | 中文: [README.zh.md](./README.zh.md)

`wechat-claw` is a toolkit for turning structured JSON articles into WeChat-ready HTML, with validation, image planning, upload, draft creation, and publishing helpers.

### Overview

This repository focuses on a structured WeChat article workflow:

- maintain multiple WeChat article templates
- render article JSON into HTML
- validate metadata, content structure, and image URLs
- fill sensible default metadata automatically
- plan cover and inline image prompts / filenames
- call external scripts for image generation, upload, draft creation, and publishing
- normalize local files, URLs, or raw text into a source bundle

### Typical use cases

- AI daily briefings
- weekly financial reviews
- deep-dive analysis pieces
- industry radar / company updates
- product release posts
- breaking news explainers

### Requirements

- Python `3.10+`
- standard-library only for the current scripts
- for the full publishing pipeline you need:
  - an image generator script compatible with `generate_image.py --prompt ... --filename ... --resolution 1K`
  - a WeChat helper script compatible with `wechat_mp.py upload-image|upload-content-image|draft-add|publish`

### OpenClaw integration

The repo already declares `openclaw` compatibility in `SKILL.md` and includes dependency metadata for companion skills.

- 中文接入: [`openclaw.zh.md`](./openclaw.zh.md)
- English guide: [`openclaw.en.md`](./openclaw.en.md)

### Supported templates

| Template ID | Purpose |
| --- | --- |
| `daily-intelligence` | AI daily briefing |
| `weekly-financial` | weekly macro / market review |
| `deep-analysis` | long-form single-topic analysis |
| `industry-radar` | industry scan / company updates |
| `product-release` | release notes / launch posts |
| `breaking-watch` | breaking-news tracking |
| `studio-brief` | minimal editorial / lifestyle / brand-observation posts |
| `neo-brutalism` | bold brutalist / poster-like / high-contrast long-form posts |

Template files live in [`../templates/`](../templates).

### Supported content block types

| Type | Purpose | Key fields |
| --- | --- | --- |
| `card` | standard news card | `title`, `body`, `source`, `number` |
| `opinion` | editorial opinion card | `title`, `body`, `source`, `number` |
| `week-ahead` | calendar / week-ahead block | `title`, `days`, `source`, `number` |
| `image` | inline image block | `url`, `caption` |
| `quote` | quote block | `text`, `attribution` |
| `takeaways` | bullet takeaways | `title`, `items` |
| `paragraph` | plain text paragraphs | `text` or `body` |

Additional image slots are also supported:

- `headline.image`
- `section.image`
- `meta.cover_image`

### Article JSON shape

The minimal valid article shape is:

```json
{
  "template": "daily-intelligence",
  "meta": {
    "title": "AI Daily Test",
    "digest": "Short article digest",
    "date": "2026-03-15"
  },
  "headline": {
    "title": "Headline title",
    "body": [
      "First paragraph.",
      "Second paragraph."
    ],
    "source": "Example Source"
  },
  "sections": [
    {
      "cn": "要闻",
      "en": "BRIEFING",
      "blocks": [
        {
          "type": "card",
          "number": "01",
          "title": "Story title",
          "body": "Story body",
          "source": "Example Source"
        }
      ]
    }
  ]
}
```

The system auto-fills several defaults:

- `meta.date_cn`
- `meta.date_short`
- `meta.author`, default `39Claw`
- `meta.open_comment`, default `1`
- `meta.source_count`
- `meta.news_count`

### Validation rules

Key validation behavior from [`../scripts/article_lib.py`](../scripts/article_lib.py) and [`../scripts/validate_article.py`](../scripts/validate_article.py):

- `template` must match an existing file in `templates/*.html`
- `meta.title` is required and must be `<= 32` chars
- `meta.digest` is required and must be `<= 128` chars
- `headline.title` is required
- `headline.body` must be a non-empty string or string array
- `sections` must be a non-empty array
- `card` / `opinion` blocks require `title`
- `week-ahead` blocks require `days`
- rendered HTML fails validation if unresolved placeholders remain
- missing `thumb_media_id` is reported as a warning because cover upload is still required before draft creation

### Common commands

Collect source materials:

```bash
python3 scripts/collect_sources.py \
  --source-file notes.txt \
  --source-url "Example::https://example.com" \
  --source-text "temporary clue text" \
  -o build/sources.json
```

Render HTML:

```bash
python3 scripts/render_article.py article.json -o build/article.html --check
```

Validate an article:

```bash
python3 scripts/validate_article.py article.json --json
```

Plan cover and inline images:

```bash
python3 scripts/plan_images.py article.json \
  -o build/image-plan.json \
  --write-article build/article.planned.json \
  --output-dir build/images
```

Run the full local pipeline:

```bash
python3 scripts/run_pipeline.py article.json --output-dir build --dry-run
```

Run with image generation, upload, draft creation, and publish:

```bash
python3 scripts/run_pipeline.py article.json \
  --output-dir build \
  --nanobanana-script /path/to/generate_image.py \
  --wechat-script /path/to/wechat_mp.py \
  --create-draft \
  --publish
```

### Recommended workflow

1. Collect source materials with `collect_sources.py`
2. Produce article JSON manually or from an upstream generator
3. Run `validate_article.py`
4. Run `plan_images.py`
5. Render HTML with `render_article.py`
6. Use `run_pipeline.py` for generation, upload, drafting, and publishing

### Repository layout

```text
templates/              WeChat HTML templates
scripts/article_lib.py  Core rendering and validation logic
scripts/render_article.py
scripts/validate_article.py
scripts/plan_images.py
scripts/run_pipeline.py
scripts/collect_sources.py
references/             Writing, title, and image prompt references
```
