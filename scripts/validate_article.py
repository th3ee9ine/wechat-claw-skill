#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from article_lib import ArticleError, load_json, render_article, validate_article


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate article JSON and optional rendered HTML.")
    parser.add_argument("input", help="Path to article JSON")
    parser.add_argument("--html", help="Path to existing rendered HTML. If omitted, HTML is rendered in-memory.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        article = load_json(args.input)
        html_text = Path(args.html).read_text(encoding="utf-8") if args.html else render_article(article)
        validation = validate_article(article, html_text=html_text)
        payload = {"ok": validation.ok, "errors": validation.errors, "warnings": validation.warnings}
        if args.json:
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            if validation.errors:
                for error in validation.errors:
                    print(f"ERROR: {error}")
            if validation.warnings:
                for warning in validation.warnings:
                    print(f"WARNING: {warning}")
            if validation.ok:
                print("OK: article passed validation")
        return 0 if validation.ok else 1
    except (ArticleError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
