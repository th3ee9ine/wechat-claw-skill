#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from article_lib import ArticleError, load_json, render_article, validate_article


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a WeChat article JSON file into HTML.")
    parser.add_argument("input", help="Path to article JSON")
    parser.add_argument("-o", "--output", help="Write rendered HTML to this file")
    parser.add_argument("--check", action="store_true", help="Validate before writing output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        article = load_json(args.input)
        html_text = render_article(article)
        if args.check:
            validation = validate_article(article, html_text=html_text)
            if not validation.ok:
                for error in validation.errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            for warning in validation.warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
        if args.output:
            Path(args.output).write_text(html_text, encoding="utf-8")
        else:
            sys.stdout.write(html_text)
        return 0
    except (ArticleError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
