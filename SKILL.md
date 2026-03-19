---
name: wechat-mp-writer
description: "微信公众号文章全自动写作与发布。从信息搜集、AI配图规划、报刊级 HTML 排版、到草稿创建和发布的完整流程。适用于 AI 日报、财经周报、深度分析、新闻资讯类文章。内置多种模板，并提供本地渲染、校验、图片规划和发布流水线脚本。"
version: 1.1.0
author: 39Claw
license: MIT
compatibility:
  platforms:
    - openclaw
metadata:
  openclaw:
    emoji: "📝"
    requires:
      bins: ["python3"]
      skills: ["nanobanana-pro-fallback", "wechat-mp", "searxng"]
---

# 微信公众号文章全自动写作与发布

从素材归并到排版发布的一站式公众号文章制作技能。

## openClaw 路径约束

如果这个 skill 是从 OpenClaw 的 workspace skills 目录加载的，不要假设当前工作目录就是 skill 根目录。执行本仓库内置脚本、模板或参考文件时，优先先定位 `SKILL.md` 所在目录，再从该目录拼绝对路径访问 `scripts/`、`templates/`、`references/`。

人类用户的接入步骤见 `docs/openclaw.zh.md`。

## 快速入口

优先用仓库自带脚本，不要手工替换模板占位符：

```bash
# 渲染 HTML
python3 scripts/render_article.py article.json -o build/article.html --check

# 单独校验
python3 scripts/validate_article.py article.json --html build/article.html

# 规划封面图和正文配图
python3 scripts/plan_images.py article.json --write-article build/article.with-images.json

# 跑完整本地流水线
python3 scripts/run_pipeline.py article.json --output-dir build --dry-run
```

如果要接入外部技能完成配图生成、上传和发布，再追加脚本路径：

```bash
python3 scripts/run_pipeline.py article.json \
  --output-dir build \
  --nanobanana-script /abs/path/to/generate_image.py \
  --wechat-script /abs/path/to/wechat_mp.py \
  --create-draft \
  --publish
```

## 核心能力

1. **信息搜集**：`scripts/collect_sources.py` 归并本地文件、URL、原始文本
2. **AI配图规划**：`scripts/plan_images.py` 自动补封面图和正文图 prompt、caption、文件路径
3. **世界级排版**：`scripts/render_article.py` 渲染报刊级 HTML 模板
4. **硬约束校验**：`scripts/validate_article.py` 校验标题、摘要、图片 URL、正文大小
5. **自动发布**：`scripts/run_pipeline.py` 串联渲染、校验、上传封面、上传正文图、建草稿、发布

## 脚本清单

- `scripts/collect_sources.py`
  输入 source spec JSON，或直接通过命令行指定数据源，输出统一的 source bundle JSON。
- `scripts/plan_images.py`
  根据文章 JSON 自动规划封面图和正文图。
- `scripts/render_article.py`
  根据 `template` 和 `sections` 渲染 HTML。
- `scripts/validate_article.py`
  校验 JSON 和已渲染 HTML 是否符合微信限制。
- `scripts/run_pipeline.py`
  执行本地 dry-run，或串接外部图片生成/微信发布脚本。

## 输入格式

文章统一使用 JSON。最小结构：

```json
{
  "template": "daily-intelligence",
  "meta": {
    "title": "AI日报3.15｜亮点1·亮点2·亮点3",
    "digest": "摘要，128字以内",
    "author": "39Claw",
    "date": "2026-03-15"
  },
  "headline": {
    "title": "头条标题",
    "body": ["第一段", "第二段"],
    "source": "CNBC"
  },
  "sections": [
    {
      "en": "BRIEFING",
      "cn": "要闻",
      "blocks": [
        {
          "type": "card",
          "style": "highlight",
          "number": 1,
          "title": "卡片标题",
          "body": ["正文段落"],
          "source": "财联社"
        }
      ]
    }
  ],
  "conclusion": "适用于 deep-analysis 的结论段",
  "cta": "你最关注哪一点？欢迎留言。"
}
```

支持的 `template`：
- `daily-intelligence`
- `weekly-financial`
- `deep-analysis`
- `breaking-watch`
- `product-release`
- `industry-radar`
- `studio-brief`
- `neo-brutalism`

支持的 `block.type`：
- `card`
- `opinion`
- `week-ahead`
- `image`
- `quote`
- `takeaways`
- `paragraph`

## 模板

使用 `templates/` 目录下的模板：
- `templates/daily-intelligence.html` — AI日报模板
- `templates/weekly-financial.html` — 财经周报模板
- `templates/deep-analysis.html` — 深度分析模板
- `templates/breaking-watch.html` — 快讯追踪模板
- `templates/product-release.html` — 产品发布模板
- `templates/industry-radar.html` — 行业雷达模板
- `templates/studio-brief.html` — 极简生活方式 / 编辑风模板
- `templates/neo-brutalism.html` — Neo Brutalism 高对比模板

模板由脚本自动注入这些核心占位符：
- `{{HEADLINE_BODY}}`
- `{{HEADLINE_IMAGE}}`
- `{{BODY_SECTIONS}}`

## 完整流程

### 第一步：信息搜集

先确认用户是否已经指定数据源。

- 如果用户已经指定数据源：严格按用户给的文件、URL、原始文本或关键词处理
- 如果用户没有指定数据源：先提示用户指定数据源，不要默认抓取或自行猜测来源

先把素材归并成统一 bundle，再整理成 article JSON：

```bash
python3 scripts/collect_sources.py source-spec.json -o build/sources.json
```

也可以直接让用户指定数据源，不必先手写 spec 文件：

```bash
python3 scripts/collect_sources.py \
  --source-file "飞书导出::/path/to/daily.md" \
  --source-url "CNBC::https://www.cnbc.com/world/" \
  --source-text "补充备注::今天重点看模型价格战和 Agent 落地" \
  -o build/sources.json
```

推荐来源：
- 本地 markdown / txt
- 直接 URL
- 已整理好的原始文本

如果素材来自飞书，先导出或复制成文本文件，再交给 `collect_sources.py`。
如果用户没有提供任何 `source-spec.json` 或 `--source-*` 参数，脚本会直接报错并提示用户先指定数据源。

### 第二步：规划封面图和正文图

```bash
python3 scripts/plan_images.py article.json \
  --write-article build/article.with-images.json \
  --output-dir build/images
```

生成后的 JSON 会补上：
- `meta.cover_image`
- `headline.image`
- `section.image`

### 第三步：渲染 HTML

```bash
python3 scripts/render_article.py build/article.with-images.json \
  -o build/article.html \
  --check
```

### 第四步：发布前校验

```bash
python3 scripts/validate_article.py build/article.with-images.json --html build/article.html
```

### 第五步：建草稿与发布

```bash
python3 scripts/run_pipeline.py article.json \
  --output-dir build \
  --nanobanana-script /abs/path/to/generate_image.py \
  --wechat-script /abs/path/to/wechat_mp.py \
  --create-draft \
  --publish
```

如果返回 `48001`，通知用户改为手动去草稿箱发布。

## 排版核心规范

| 项目 | 设置 |
|------|------|
| 字体 | -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC' |
| 正文字号 | 14-15px |
| 正文颜色 | #555 或 #3f3f3f |
| 标题颜色 | #1a1a2e |
| 行高 | 1.9-2.0 |
| 强调数据 | `<strong style="color: #e94560;">数据</strong>` |

## 写作原则

参考 `references/writing-guide.md`：
- "说人话"，避免行业黑话
- 每条新闻精简到 2-3 句话，保留核心信息
- 关键数据用红色加粗突出
- 设计"留言诱因"，留言权重最高
- 结尾引导互动 + 引导关注

## 标题公式

参考 `references/title-formulas.md`：
- 关键词法：带核心关键词，利于搜索推荐
- 反差法：制造认知冲突
- 问号式：激发好奇心
- 数据法：用具体数字吸引眼球
- 禁止"震惊体"，会被判标题党限流

## 发布时段

- 最佳：17:00-23:00
- 通勤：8:00-9:00
- 午休：12:00-13:00
- 分享朋友圈最佳：21:00后

## 注意事项

- 标题严格 ≤ 32 字
- 摘要严格 ≤ 128 字
- 正文大小不超过 1MB
- 正文图片必须使用 upload-content-image 后得到的微信 CDN URL
- 封面图必须先 upload-image，再写入 `meta.thumb_media_id`
- 草稿发布后会从草稿箱移除
- 发布是异步的，需要用 publish-status 查询结果
- 流量周期：前 48 小时是巅峰，第 3 天明显衰减
