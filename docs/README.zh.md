# wechat-claw

中文详细说明。Overview: [../README.md](../README.md) ｜ English: [README.en.md](./README.en.md)

微信公众号文章工具集，用于把结构化 JSON 内容渲染成公众号 HTML，并串联校验、配图规划、图片上传、草稿创建和发布流程。

### 项目简介

这个仓库当前聚焦在“文章生产链路”：

- 维护多套公众号文章模板
- 读取文章 JSON，渲染为 HTML
- 对标题、摘要、正文结构、图片链接等做校验
- 自动补齐默认元数据
- 自动规划封面图和正文配图 prompt / 本地文件名
- 调用外部脚本生成图片、上传图片、创建草稿、发布文章
- 采集本地文件、URL、原始文本并归一化为 source bundle

### 适用场景

- AI 日报 / 财经周报 / 深度分析 / 行业观察
- 产品发布说明
- 热点快讯追踪
- 需要“结构化写作 + 模板化渲染 + 自动发布”的公众号工作流

### 环境要求

- Python `3.10+`
- 当前脚本只依赖 Python 标准库
- 如果要走完整发布链路，需要你额外提供：
  - 一个图片生成脚本，兼容 `generate_image.py --prompt ... --filename ... --resolution 1K`
  - 一个公众号脚本，兼容 `wechat_mp.py upload-image|upload-content-image|draft-add|publish`

### openClaw 接入

仓库已经在 `SKILL.md` 中声明 `openclaw` 兼容，并带有依赖 skill 元数据。

- 本地接入教程：[`openclaw.zh.md`](./openclaw.zh.md)
- English guide: [`openclaw.en.md`](./openclaw.en.md)

### 支持模板

| 模板 ID | 用途 |
| --- | --- |
| `daily-intelligence` | AI 日报 / 资讯精选 |
| `weekly-financial` | 财经周报 / 宏观与市场回顾 |
| `deep-analysis` | 单主题深度分析 |
| `industry-radar` | 行业观察 / 赛道扫描 / 公司动态 |
| `product-release` | 产品发布 / 版本更新 |
| `breaking-watch` | 快讯追踪 / 热点拆解 |
| `studio-brief` | 极简编辑风 / 生活方式 / 品牌观察 |
| `neo-brutalism` | 粗边框高对比 / 强视觉冲击 / 海报感长文 |

模板文件位于 [`../templates/`](../templates)。

### 支持的正文 block 类型

| 类型 | 说明 | 关键字段 |
| --- | --- | --- |
| `card` | 标准新闻卡片 | `title`, `body`, `source`, `number` |
| `opinion` | 编辑观点卡片 | `title`, `body`, `source`, `number` |
| `week-ahead` | 下周前瞻日历块 | `title`, `days`, `source`, `number` |
| `image` | 正文内图片块 | `url`, `caption` |
| `quote` | 引述块 | `text`, `attribution` |
| `takeaways` | 结论清单 | `title`, `items` |
| `paragraph` | 普通段落块 | `text` 或 `body` |

此外还支持：

- `headline.image`：头条配图
- `section.image`：分区配图
- `meta.cover_image`：封面图元数据

### 文章 JSON 结构

最小可用结构如下：

```json
{
  "template": "daily-intelligence",
  "meta": {
    "title": "AI 日报测试",
    "digest": "这里是一段摘要",
    "date": "2026-03-15"
  },
  "headline": {
    "title": "头条标题",
    "body": [
      "第一段正文。",
      "第二段正文。"
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
          "title": "新闻标题",
          "body": "新闻正文",
          "source": "Example Source"
        }
      ]
    }
  ]
}
```

系统会自动补齐部分默认字段：

- `meta.date_cn`
- `meta.date_short`
- `meta.author`，默认值为 `39Claw`
- `meta.open_comment`，默认值为 `1`
- `meta.source_count`
- `meta.news_count`

### 校验规则

主要校验逻辑由 [`../scripts/article_lib.py`](../scripts/article_lib.py) 和 [`../scripts/validate_article.py`](../scripts/validate_article.py) 提供：

- `template` 必须存在于 `templates/*.html`
- `meta.title` 必填，且长度不超过 `32`
- `meta.digest` 必填，且长度不超过 `128`
- `headline.title` 必填
- `headline.body` 必须是非空字符串或字符串数组
- `sections` 必须是非空数组
- `card` / `opinion` block 必须有 `title`
- `week-ahead` block 必须有 `days`
- 如果渲染后的 HTML 仍含未解析占位符，会直接报错
- `thumb_media_id` 缺失会给 warning，因为创建草稿前仍需要上传封面

### 常用命令

#### 1. 采集数据源

```bash
python3 scripts/collect_sources.py \
  --source-file notes.txt \
  --source-url "Example::https://example.com" \
  --source-text "临时线索文本" \
  -o build/sources.json
```

#### 2. 渲染文章 HTML

```bash
python3 scripts/render_article.py article.json -o build/article.html --check
```

#### 3. 单独校验文章

```bash
python3 scripts/validate_article.py article.json --json
```

#### 4. 自动规划封面图和正文配图

```bash
python3 scripts/plan_images.py article.json \
  -o build/image-plan.json \
  --write-article build/article.planned.json \
  --output-dir build/images
```

#### 5. 运行本地完整流水线

只做本地渲染与校验：

```bash
python3 scripts/run_pipeline.py article.json --output-dir build --dry-run
```

带图片生成、上传、建草稿、发布：

```bash
python3 scripts/run_pipeline.py article.json \
  --output-dir build \
  --nanobanana-script /path/to/generate_image.py \
  --wechat-script /path/to/wechat_mp.py \
  --create-draft \
  --publish
```

### 推荐工作流

1. 用 `collect_sources.py` 收集原始材料
2. 手工或上游程序生成文章 JSON
3. 用 `validate_article.py` 先做结构校验
4. 用 `plan_images.py` 规划封面和正文配图
5. 用 `render_article.py` 产出 HTML
6. 用 `run_pipeline.py` 串联图片生成、上传、建草稿、发布

### 目录结构

```text
templates/              公众号 HTML 模板
scripts/article_lib.py  核心渲染与校验逻辑
scripts/render_article.py
scripts/validate_article.py
scripts/plan_images.py
scripts/run_pipeline.py
scripts/collect_sources.py
references/             写作、标题、图片提示词参考
```
