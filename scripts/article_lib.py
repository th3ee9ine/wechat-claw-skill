#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
WECHAT_IMAGE_HOST_PATTERNS = (
    "mmbiz.qpic.cn",
    "mmbiz.qlogo.cn",
    "mmbiz.qlogo.cn",
    "wx.qlogo.cn",
    "mmbiz.qpic.cn",
)


class ArticleError(RuntimeError):
    pass


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def available_templates() -> set[str]:
    return {path.stem for path in TEMPLATES_DIR.glob("*.html")}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ArticleError("Article input must be a JSON object.")
    return data


def dump_json(path: str | Path, payload: Any) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize_text(value: Any, *, allow_html: bool = False) -> str:
    text = "" if value is None else str(value).strip()
    if not allow_html:
        return html.escape(text)
    return text


def normalize_paragraphs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in re.split(r"\n{2,}", value) if part.strip()]
        return parts or [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ArticleError(f"Expected string or list of strings, got: {type(value)!r}")


def to_int_string(value: Any, fallback: str) -> str:
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return fallback


def parse_iso_date(raw: str | None) -> date:
    if raw:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return date.today()


def ensure_meta_defaults(article: dict[str, Any]) -> dict[str, Any]:
    raw_meta = article.get("meta")
    meta = raw_meta if isinstance(raw_meta, dict) else dict(raw_meta or {})
    article["meta"] = meta
    parsed_date = parse_iso_date(meta.get("date"))
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    meta.setdefault("date", parsed_date.isoformat())
    meta.setdefault(
        "date_cn",
        f"{parsed_date.year} 年 {parsed_date.month} 月 {parsed_date.day} 日 · {weekdays[parsed_date.weekday()]}",
    )
    meta.setdefault("date_short", parsed_date.strftime("%Y.%m.%d"))
    meta.setdefault("author", "39Claw")
    meta.setdefault("open_comment", 1)
    meta.setdefault("source_count", count_sources(article))
    meta.setdefault("news_count", count_news_items(article))
    return meta


def count_sources(article: dict[str, Any]) -> int:
    sources: set[str] = set()
    headline = article.get("headline") or {}
    source = headline.get("source")
    if source:
        sources.add(str(source).strip())
    for section in article.get("sections") or []:
        for block in section.get("blocks") or []:
            source = block.get("source")
            if source:
                sources.add(str(source).strip())
    return len(sources)


def count_news_items(article: dict[str, Any]) -> int:
    count = 0
    for section in article.get("sections") or []:
        for block in section.get("blocks") or []:
            if block.get("type", "card") in {"card", "opinion", "week-ahead"}:
                count += 1
    return count


def read_template(template_name: str) -> str:
    template_path = TEMPLATES_DIR / f"{template_name}.html"
    if not template_path.exists():
        raise ArticleError(f"Template not found: {template_name}")
    return template_path.read_text(encoding="utf-8")


def is_studio_brief_template(template_name: str) -> bool:
    return template_name == "studio-brief"


def is_brutal_template(template_name: str) -> bool:
    return template_name == "neo-brutalism"


def render_image_block(image: dict[str, Any] | None, *, template_name: str = "") -> str:
    if not image:
        return ""
    url = normalize_text(image.get("url"))
    if not url:
        return ""
    caption = normalize_text(image.get("caption") or "配图", allow_html=False)
    if is_studio_brief_template(template_name):
        return (
            '<section style="background: #ffffff; padding: 8px 22px 24px; text-align: center;">'
            '<section style="background: #f6f2ea; border-radius: 14px; overflow: hidden; border: 1px solid rgba(23,22,20,0.07);">'
            f'<img src="{url}" style="width: 100%; display: block; margin: 0;" />'
            '<section style="padding: 10px 14px 12px;">'
            f'<p style="font-size: 11px; color: #7f766b; text-align: left; margin: 0; line-height: 1.6;">{caption} · AI 生成</p>'
            "</section></section></section>"
        )
    if is_brutal_template(template_name):
        return (
            '<section style="background: #fffdf7; padding: 10px 18px 0; text-align: center;">'
            '<section style="background: #ffffff; border: 4px solid #111111; box-shadow: 8px 8px 0 #7dff6b; overflow: hidden;">'
            f'<img src="{url}" style="width: 100%; display: block; margin: 0;" />'
            '<section style="padding: 10px 12px 12px; background: #7dff6b; border-top: 4px solid #111111;">'
            f'<p style="font-size: 11px; color: #111111; text-align: left; margin: 0; line-height: 1.55; font-weight: 900; letter-spacing: 0.3px;">{caption}</p>'
            "</section></section></section>"
        )
    return (
        '<section style="background: #ffffff; padding: 15px 20px; text-align: center;">'
        f'<img src="{url}" style="width: 100%; border-radius: 4px; margin: 0;" />'
        f'<p style="font-size: 11px; color: #999; text-align: center; margin: 5px 0 0; font-style: italic;">'
        f"{caption} | AI 生成"
        "</p></section>"
    )


def render_section_heading(section: dict[str, Any], *, template_name: str = "") -> str:
    section_en = normalize_text(section.get("en") or section.get("title_en") or "SECTION")
    section_cn = normalize_text(section.get("cn") or section.get("title") or "分区")
    if is_studio_brief_template(template_name):
        return (
            '<section style="background: #ffffff; padding: 26px 22px 10px;">'
            f'<p style="font-size: 11px; color: #887d70; letter-spacing: 3px; text-transform: uppercase; margin: 0 0 8px;">{section_en}</p>'
            f'<p style="font-size: 21px; font-weight: 700; color: #171614; line-height: 1.3; margin: 0;">{section_cn}</p>'
            "</section>"
        )
    if is_brutal_template(template_name):
        return (
            '<section style="background: #fffdf7; padding: 18px 18px 10px;">'
            '<section style="display: inline-block; padding: 10px 12px 8px; background: #00c2ff; border: 4px solid #111111; box-shadow: 6px 6px 0 #111111;">'
            f'<p style="font-size: 11px; color: #111111; letter-spacing: 2.6px; text-transform: uppercase; margin: 0 0 6px; font-weight: 900;">{section_en}</p>'
            f'<p style="font-size: 22px; font-weight: 900; color: #111111; line-height: 1.15; margin: 0;">{section_cn}</p>'
            "</section></section>"
        )
    return (
        '<section style="background: #f8f7f4; padding: 20px 20px 5px;">'
        '<p style="font-size: 10px; color: #e94560; letter-spacing: 5px; text-transform: uppercase; '
        f'margin: 0 0 15px; font-weight: 700;">{section_en} · {section_cn}</p>'
        "</section>"
    )


def render_body_paragraphs(value: Any, *, margin_bottom: str = "8px", template_name: str = "") -> str:
    paragraphs = normalize_paragraphs(value)
    if not paragraphs:
        return ""
    if is_studio_brief_template(template_name):
        font_size, text_color, line_height = "15px", "#332f2a", "1.95"
    elif is_brutal_template(template_name):
        font_size, text_color, line_height = "15px", "#111111", "1.82"
    else:
        font_size, text_color, line_height = "14px", "#555", "1.9"
    return "".join(
        f'<p style="font-size: {font_size}; color: {text_color}; line-height: {line_height}; margin: 0 0 {margin_bottom};">{normalize_text(paragraph, allow_html=True)}</p>'
        for paragraph in paragraphs
    )


def render_card_block(block: dict[str, Any], *, highlight: bool, template_name: str = "") -> str:
    number = html.escape(str(block.get("number") or "").zfill(2) if str(block.get("number") or "").isdigit() else str(block.get("number") or ""))
    number = number or "&nbsp;"
    color = "#e94560" if highlight else "#1a1a2e"
    title = normalize_text(block.get("title"))
    source = normalize_text(block.get("source") or "")
    body = render_body_paragraphs(block.get("body"), template_name=template_name)
    if is_studio_brief_template(template_name):
        number_bg = "#c96d44" if highlight else "#d9cfbf"
        number_fg = "#fffaf4" if highlight else "#3d372f"
        return (
            '<section style="background: #ffffff; padding: 0 22px 10px;">'
            '<section style="background: #fbf8f1; border: 1px solid rgba(23,22,20,0.08); border-radius: 16px; padding: 18px 18px 16px;">'
            '<section style="display: flex; align-items: flex-start;">'
            f'<section style="min-width: 34px; width: 34px; height: 34px; background: {number_bg}; color: {number_fg}; '
            'font-size: 12px; font-weight: 700; line-height: 34px; text-align: center; border-radius: 999px; '
            'margin-right: 14px; flex-shrink: 0; letter-spacing: 0.3px;">'
            f"{number}</section>"
            '<section style="flex: 1;">'
            f'<p style="font-size: 18px; font-weight: 700; color: #171614; margin: 0 0 10px; line-height: 1.4;">{title}</p>'
            f"{body}"
            f'<p style="font-size: 11px; color: #8b8175; margin: 10px 0 0; letter-spacing: 0.4px;">{source}</p>'
            "</section></section></section></section>"
        )
    if is_brutal_template(template_name):
        number_bg = "#ff5fa2" if highlight else "#ffffff"
        return (
            '<section style="background: #ffffff; padding: 0 18px 12px;">'
            '<section style="background: #ffffff; border: 4px solid #111111; box-shadow: 8px 8px 0 #111111; padding: 16px 14px 14px;">'
            '<section style="display: flex; align-items: flex-start;">'
            f'<section style="min-width: 38px; width: 38px; height: 38px; background: {number_bg}; color: #111111; '
            'font-size: 13px; font-weight: 900; line-height: 38px; text-align: center; margin-right: 12px; flex-shrink: 0; border: 3px solid #111111;">'
            f"{number}</section>"
            '<section style="flex: 1;">'
            f'<p style="font-size: 18px; font-weight: 900; color: #111111; margin: 0 0 10px; line-height: 1.28;">{title}</p>'
            f"{body}"
            f'<p style="font-size: 11px; color: #111111; margin: 10px 0 0; font-weight: 800; letter-spacing: 0.2px;">{source}</p>'
            "</section></section></section></section>"
        )
    return (
        '<section style="background: #ffffff; margin: 0 0 1px; padding: 20px;">'
        '<section style="display: flex; align-items: flex-start;">'
        f'<section style="min-width: 36px; width: 36px; height: 36px; background: {color}; color: #fff; '
        'font-size: 14px; font-weight: 900; line-height: 36px; text-align: center; border-radius: 4px; '
        f'margin-right: 14px; flex-shrink: 0;">{number}</section>'
        '<section style="flex: 1;">'
        f'<p style="font-size: 17px; font-weight: 800; color: #1a1a2e; margin: 0 0 8px; line-height: 1.4;">{title}</p>'
        f"{body}"
        f'<p style="font-size: 11px; color: #bbb; margin: 8px 0 0;">{source}</p>'
        "</section></section></section>"
    )


def render_opinion_block(block: dict[str, Any], *, template_name: str = "") -> str:
    opinion = dict(block)
    opinion["title"] = f"编辑观点：{block.get('title', '')}"
    opinion.setdefault("source", block.get("source") or "39Claw 编辑部")
    return render_card_block(opinion, highlight=True, template_name=template_name)


def render_week_ahead_block(block: dict[str, Any], *, template_name: str = "") -> str:
    number = normalize_text(block.get("number") or "")
    title = normalize_text(block.get("title") or "下周前瞻")
    source = normalize_text(block.get("source") or "")
    rows = []
    for row in block.get("days") or []:
        label = normalize_text(row.get("label") or "")
        events = normalize_text(row.get("events") or "", allow_html=True)
        if is_brutal_template(template_name):
            rows.append(
                '<p style="font-size: 14px; color: #111111; line-height: 1.78; margin: 0 0 6px; font-weight: 700;">'
                f'<strong style="color: #111111;">{label}</strong> // {events}</p>'
            )
        else:
            rows.append(
                '<p style="font-size: 14px; color: #555; line-height: 1.9; margin: 0 0 5px;">'
                f'🔴 <strong>{label}</strong>：{events}</p>'
            )
    rows_html = "".join(rows)
    if is_brutal_template(template_name):
        return (
            '<section style="background: #ffffff; padding: 0 18px 12px;">'
            '<section style="background: #ffffff; border: 4px solid #111111; box-shadow: 8px 8px 0 #00c2ff; padding: 16px 14px 14px;">'
            '<section style="display: flex; align-items: flex-start;">'
            f'<section style="min-width: 38px; width: 38px; height: 38px; background: #ffd84d; color: #111111; '
            'font-size: 13px; font-weight: 900; line-height: 38px; text-align: center; margin-right: 12px; flex-shrink: 0; border: 3px solid #111111;">'
            f"{number}</section>"
            '<section style="flex: 1;">'
            f'<p style="font-size: 18px; font-weight: 900; color: #111111; margin: 0 0 10px; line-height: 1.28;">{title}</p>'
            f"{rows_html}"
            f'<p style="font-size: 11px; color: #111111; margin: 10px 0 0; font-weight: 800;">{source}</p>'
            "</section></section></section></section>"
        )
    return (
        '<section style="background: #ffffff; margin: 0 0 1px; padding: 20px;">'
        '<section style="display: flex; align-items: flex-start;">'
        f'<section style="min-width: 36px; width: 36px; height: 36px; background: #e94560; color: #fff; '
        'font-size: 14px; font-weight: 900; line-height: 36px; text-align: center; border-radius: 4px; '
        f'margin-right: 14px; flex-shrink: 0;">{number}</section>'
        '<section style="flex: 1;">'
        f'<p style="font-size: 17px; font-weight: 800; color: #1a1a2e; margin: 0 0 8px; line-height: 1.4;">{title}</p>'
        f"{rows_html}"
        f'<p style="font-size: 11px; color: #bbb; margin: 8px 0 0;">{source}</p>'
        "</section></section></section>"
    )


def render_quote_block(block: dict[str, Any], *, template_name: str = "") -> str:
    text = normalize_text(block.get("text") or "", allow_html=True)
    attribution = normalize_text(block.get("attribution") or "")
    if is_brutal_template(template_name):
        return (
            '<section style="background: #ffffff; padding: 0 18px 12px;">'
            '<section style="background: #f5f5f5; border: 4px solid #111111; box-shadow: 8px 8px 0 #ffd84d; padding: 14px 14px 12px;">'
            f'<p style="font-size: 16px; color: #111111; line-height: 1.8; margin: 0 0 8px; font-weight: 800;">{text}</p>'
            f'<p style="font-size: 11px; color: #111111; margin: 0; font-weight: 800;">{attribution}</p>'
            "</section></section>"
        )
    return (
        '<section style="background: #ffffff; padding: 10px 20px 20px;">'
        '<section style="border-left: 3px solid #e94560; padding: 6px 0 6px 14px;">'
        f'<p style="font-size: 15px; color: #3f3f3f; line-height: 1.9; margin: 0 0 8px;">{text}</p>'
        f'<p style="font-size: 11px; color: #999; margin: 0;">{attribution}</p>'
        "</section></section>"
    )


def render_takeaways_block(block: dict[str, Any], *, template_name: str = "") -> str:
    title = normalize_text(block.get("title") or "核心结论")
    items = block.get("items") or []
    items_html = "".join(
        f'<li style="margin: 0 0 8px;">{normalize_text(item, allow_html=True)}</li>' for item in items
    )
    if is_brutal_template(template_name):
        return (
            '<section style="background: #ffffff; padding: 0 18px 12px;">'
            '<section style="background: #ffd84d; border: 4px solid #111111; box-shadow: 8px 8px 0 #111111; padding: 16px 14px 8px;">'
            f'<p style="font-size: 16px; font-weight: 900; color: #111111; margin: 0 0 12px;">{title}</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #111111; font-size: 15px; line-height: 1.82; font-weight: 800;">{items_html}</ul>'
            "</section></section>"
        )
    return (
        '<section style="background: #ffffff; padding: 20px;">'
        '<section style="background: #f8f7f4; border: 1px solid rgba(233,69,96,0.12); border-radius: 8px; padding: 18px 18px 10px;">'
        f'<p style="font-size: 16px; font-weight: 800; color: #1a1a2e; margin: 0 0 12px;">{title}</p>'
        f'<ul style="margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 1.9;">{items_html}</ul>'
        "</section></section>"
    )


def render_paragraph_block(block: dict[str, Any], *, template_name: str = "") -> str:
    body = render_body_paragraphs(block.get("text") or block.get("body"), margin_bottom="12px", template_name=template_name)
    if is_brutal_template(template_name):
        return f'<section style="background: #fffdf7; padding: 0 18px 8px;">{body}</section>'
    if is_studio_brief_template(template_name):
        return f'<section style="background: #ffffff; padding: 0 22px 8px;">{body}</section>'
    return f'<section style="background: #ffffff; padding: 0 20px 8px;">{body}</section>'


def render_block(block: dict[str, Any], *, template_name: str = "") -> str:
    block_type = block.get("type", "card")
    if block_type == "card":
        return render_card_block(block, highlight=block.get("style") == "highlight", template_name=template_name)
    if block_type == "opinion":
        return render_opinion_block(block, template_name=template_name)
    if block_type == "week-ahead":
        return render_week_ahead_block(block, template_name=template_name)
    if block_type == "image":
        return render_image_block(block, template_name=template_name)
    if block_type == "quote":
        return render_quote_block(block, template_name=template_name)
    if block_type == "takeaways":
        return render_takeaways_block(block, template_name=template_name)
    if block_type == "paragraph":
        return render_paragraph_block(block, template_name=template_name)
    raise ArticleError(f"Unsupported block type: {block_type}")


def render_sections(article: dict[str, Any], *, template_name: str = "") -> str:
    rendered: list[str] = []
    for section in article.get("sections") or []:
        rendered.append(render_section_heading(section, template_name=template_name))
        intro = section.get("intro")
        if intro:
            if is_studio_brief_template(template_name):
                rendered.append(
                    '<section style="background: #ffffff; padding: 0 22px 14px;">'
                    f'<p style="font-size: 15px; color: #5c554d; line-height: 1.9; margin: 0;">{normalize_text(intro, allow_html=True)}</p>'
                    "</section>"
                )
            elif is_brutal_template(template_name):
                rendered.append(
                    '<section style="background: #ffffff; padding: 0 18px 14px;">'
                    f'<p style="font-size: 15px; color: #111111; line-height: 1.82; margin: 0; font-weight: 700;">{normalize_text(intro, allow_html=True)}</p>'
                    "</section>"
                )
            else:
                rendered.append(
                    '<section style="background: #ffffff; padding: 0 20px 12px;">'
                    f'<p style="font-size: 14px; color: #666; line-height: 1.9; margin: 0;">{normalize_text(intro, allow_html=True)}</p>'
                    "</section>"
                )
        if section.get("image"):
            rendered.append(render_image_block(section.get("image"), template_name=template_name))
        for block in section.get("blocks") or []:
            rendered.append(render_block(block, template_name=template_name))
    return "".join(rendered)


def render_headline_body(article: dict[str, Any], *, template_name: str = "") -> str:
    paragraphs = normalize_paragraphs((article.get("headline") or {}).get("body"))
    if not paragraphs:
        return ""
    if is_studio_brief_template(template_name):
        return "".join(
            f'<p style="font-size: 16px; color: #2f2b27; line-height: 1.95; margin: 0 0 10px;">{normalize_text(paragraph, allow_html=True)}</p>'
            for paragraph in paragraphs
        )
    if is_brutal_template(template_name):
        return "".join(
            f'<p style="font-size: 16px; color: #111111; line-height: 1.82; margin: 0 0 10px; font-weight: 700;">{normalize_text(paragraph, allow_html=True)}</p>'
            for paragraph in paragraphs
        )
    return "".join(
        f'<p style="font-size: 15px; color: #3f3f3f; line-height: 2; margin: 0 0 8px;">{normalize_text(paragraph, allow_html=True)}</p>'
        for paragraph in paragraphs
    )


def apply_replacements(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def strip_html_comments(html_text: str) -> str:
    return re.sub(r"<!--.*?-->", "", html_text, flags=re.S)


def render_article(article: dict[str, Any]) -> str:
    meta = ensure_meta_defaults(article)
    template_name = str(article.get("template") or "").strip()
    template_text = strip_html_comments(read_template(template_name))
    headline = article.get("headline") or {}
    rendered = apply_replacements(
        template_text,
        {
            "DATE_CN": normalize_text(meta.get("date_cn")),
            "DATE_SHORT": normalize_text(meta.get("date_short")),
            "SOURCE_COUNT": normalize_text(meta.get("source_count")),
            "NEWS_COUNT": normalize_text(meta.get("news_count")),
            "TITLE": normalize_text(meta.get("title")),
            "SUBTITLE": normalize_text(meta.get("subtitle") or ""),
            "AUTHOR": normalize_text(meta.get("author")),
            "DIGEST": normalize_text(meta.get("digest") or "", allow_html=True),
            "HEADLINE_TITLE": normalize_text(headline.get("title")),
            "HEADLINE_BODY": render_headline_body(article, template_name=template_name),
            "HEADLINE_SOURCE": normalize_text(headline.get("source") or ""),
            "HEADLINE_IMAGE": render_image_block(headline.get("image"), template_name=template_name),
            "BODY_SECTIONS": render_sections(article, template_name=template_name),
            "CONCLUSION": normalize_text(article.get("conclusion") or "", allow_html=True),
            "CTA": normalize_text(article.get("cta") or "你最关注哪一点？欢迎留言讨论。", allow_html=True),
        },
    )
    return rendered


def find_content_images(article: dict[str, Any]) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    headline = article.get("headline") or {}
    if isinstance(headline.get("image"), dict):
        images.append(headline["image"])
    for section in article.get("sections") or []:
        if isinstance(section.get("image"), dict):
            images.append(section["image"])
        for block in section.get("blocks") or []:
            if block.get("type") == "image":
                images.append(block)
    return images


def is_wechat_image_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return any(pattern in host for pattern in WECHAT_IMAGE_HOST_PATTERNS)


def validate_article(article: dict[str, Any], *, html_text: str | None = None) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    template_name = str(article.get("template") or "").strip()
    templates = available_templates()
    if template_name not in templates:
        errors.append(f"template must be one of: {', '.join(sorted(templates))}")

    meta = ensure_meta_defaults(article)
    title = str(meta.get("title") or "").strip()
    digest = str(meta.get("digest") or "").strip()
    if not title:
        errors.append("meta.title is required")
    elif len(title) > 32:
        errors.append(f"meta.title must be <= 32 characters, got {len(title)}")

    if not digest:
        errors.append("meta.digest is required")
    elif len(digest) > 128:
        errors.append(f"meta.digest must be <= 128 characters, got {len(digest)}")

    if not str(meta.get("author") or "").strip():
        errors.append("meta.author is required")

    headline = article.get("headline") or {}
    if not str(headline.get("title") or "").strip():
        errors.append("headline.title is required")
    if not normalize_paragraphs(headline.get("body")):
        errors.append("headline.body is required")

    sections = article.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty array")
    else:
        for section_index, section in enumerate(sections, start=1):
            if not str(section.get("cn") or section.get("title") or "").strip():
                errors.append(f"sections[{section_index - 1}] is missing cn/title")
            blocks = section.get("blocks") or []
            if not blocks:
                warnings.append(f"sections[{section_index - 1}] has no blocks")
            for block_index, block in enumerate(blocks):
                block_type = block.get("type", "card")
                if block_type in {"card", "opinion"} and not str(block.get("title") or "").strip():
                    errors.append(f"sections[{section_index - 1}].blocks[{block_index}] is missing title")
                if block_type == "week-ahead" and not block.get("days"):
                    errors.append(f"sections[{section_index - 1}].blocks[{block_index}] needs days")
                if block_type == "image":
                    url = str(block.get("url") or "").strip()
                    if url and not is_wechat_image_url(url):
                        warnings.append(
                            f"sections[{section_index - 1}].blocks[{block_index}] image URL does not look like WeChat CDN"
                        )

    cover_media_id = str(meta.get("thumb_media_id") or meta.get("cover_media_id") or "").strip()
    if not cover_media_id:
        warnings.append("meta.thumb_media_id is missing; draft creation will need upload-image first")

    for image_index, image in enumerate(find_content_images(article)):
        url = str(image.get("url") or "").strip()
        if url and not is_wechat_image_url(url):
            warnings.append(f"content image #{image_index + 1} does not look like WeChat CDN: {url}")

    if html_text is not None:
        html_without_comments = strip_html_comments(html_text)
        if "{{" in html_without_comments or "}}" in html_without_comments:
            errors.append("rendered HTML still contains unresolved placeholders")
        html_size = len(html_text.encode("utf-8"))
        if html_size > 1024 * 1024:
            errors.append(f"rendered HTML exceeds 1MB limit: {html_size} bytes")

    return ValidationResult(errors=errors, warnings=warnings)
