#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


MISSING_SOURCE_MESSAGE = (
    "No data sources specified. 请先指定至少一个数据源。"
    "可用方式：提供 source-spec.json，或使用 --source-file、--source-url、--source-text、--stdin-text。"
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        self.chunks.append(text)


def load_spec(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Source spec must be a JSON object.")
    return data


def _parse_labeled_value(raw: str) -> tuple[str | None, str]:
    value = str(raw).strip()
    if not value:
        raise ValueError("Source value cannot be empty.")
    if "::" in value:
        label, payload = value.split("::", 1)
        label = label.strip() or None
        payload = payload.strip()
        if not payload:
            raise ValueError("Source value cannot be empty after label:: prefix.")
        return label, payload
    return None, value


def _build_cli_sources(args: argparse.Namespace) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []

    for raw in args.source_file:
        label, path = _parse_labeled_value(raw)
        entry = {"type": "file", "path": path}
        if label:
            entry["label"] = label
        sources.append(entry)

    for raw in args.source_url:
        label, url = _parse_labeled_value(raw)
        entry = {"type": "url", "url": url}
        if label:
            entry["label"] = label
        sources.append(entry)

    for raw in args.source_text:
        label, text = _parse_labeled_value(raw)
        entry = {"type": "text", "text": text}
        if label:
            entry["label"] = label
            entry["title"] = label
        sources.append(entry)

    if args.stdin_text:
        text = sys.stdin.read().strip()
        if not text:
            raise ValueError("--stdin-text was set, but stdin is empty.")
        sources.append({"type": "text", "label": args.stdin_label or "stdin", "title": args.stdin_label or "stdin", "text": text})

    return sources


def resolve_spec(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_spec(args.spec) if args.spec else {}
    if not isinstance(spec.get("sources") or [], list):
        raise ValueError("Source spec field 'sources' must be an array.")

    sources = list(spec.get("sources") or [])
    sources.extend(_build_cli_sources(args))
    if not sources:
        raise ValueError(MISSING_SOURCE_MESSAGE)

    spec["sources"] = sources
    return spec


def fetch_url(url: str, timeout: int, max_chars: int) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        body = response.read().decode("utf-8", errors="ignore")
    if content_type == "text/plain":
        text = " ".join(body.split())
        title = ""
    else:
        parser = TextExtractor()
        parser.feed(re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", body))
        title = parser.title
        text = " ".join(parser.chunks)
    return {"title": title, "content": text[:max_chars], "content_type": content_type}


def read_file(path: str | Path, max_chars: int) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    return {"title": Path(path).name, "content": text[:max_chars], "content_type": "text/plain"}


def collect(spec: dict[str, Any], timeout: int, max_chars: int) -> dict[str, Any]:
    items = []
    for entry in spec.get("sources") or []:
        entry_type = entry.get("type")
        label = entry.get("label") or entry.get("title") or entry.get("path") or entry.get("url") or entry_type
        try:
            if entry_type == "file":
                payload = read_file(entry["path"], max_chars)
                payload.update({"type": "file", "label": label, "path": entry["path"]})
            elif entry_type == "text":
                text = str(entry.get("text") or "")
                payload = {
                    "type": "text",
                    "label": label,
                    "title": entry.get("title") or label,
                    "content": text[:max_chars],
                    "content_type": "text/plain",
                }
            elif entry_type == "url":
                payload = fetch_url(entry["url"], timeout, max_chars)
                payload.update({"type": "url", "label": label, "url": entry["url"]})
            else:
                payload = {"type": entry_type or "unknown", "label": label, "error": f"Unsupported source type: {entry_type}"}
        except Exception as exc:
            payload = {"type": entry_type or "unknown", "label": label, "error": str(exc)}

        content = payload.get("content", "")
        payload["excerpt"] = content[: min(240, len(content))]
        payload["ok"] = "error" not in payload
        items.append(payload)

    ok_count = sum(1 for item in items if item.get("ok"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "ok_count": ok_count,
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect local files, URLs, or raw text into a normalized source bundle.")
    parser.add_argument("spec", nargs="?", help="Optional path to source spec JSON")
    parser.add_argument(
        "--source-file",
        action="append",
        default=[],
        help="Add a file source. Format: /path/to/file or 标签::/path/to/file",
    )
    parser.add_argument(
        "--source-url",
        action="append",
        default=[],
        help="Add a URL source. Format: https://... or 标签::https://...",
    )
    parser.add_argument(
        "--source-text",
        action="append",
        default=[],
        help="Add a raw text source. Format: 文本内容 or 标签::文本内容",
    )
    parser.add_argument("--stdin-text", action="store_true", help="Read one text source from stdin")
    parser.add_argument("--stdin-label", help="Label/title used together with --stdin-text")
    parser.add_argument("-o", "--output", help="Write collected bundle JSON to this file")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout in seconds for URL fetches")
    parser.add_argument("--max-chars", type=int, default=4000, help="Maximum characters stored per source")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = collect(resolve_spec(args), timeout=args.timeout, max_chars=args.max_chars)
        output = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0 if payload["ok_count"] else 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
