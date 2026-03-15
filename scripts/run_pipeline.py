#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from article_lib import ArticleError, dump_json, ensure_meta_defaults, find_content_images, load_json, render_article, validate_article
from plan_images import attach_missing_image_plans


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def _parse_json_like(output: str) -> dict[str, Any]:
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}


def _extract_first(patterns: list[str], output: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None


def _generate_image(nanobanana_script: str, prompt: str, filename: str) -> str:
    return _run(["python3", nanobanana_script, "--prompt", prompt, "--filename", filename, "--resolution", "1K"])


def _upload_cover(wechat_script: str, filename: str) -> tuple[str | None, str]:
    output = _run(["python3", wechat_script, "upload-image", filename])
    payload = _parse_json_like(output)
    media_id = payload.get("media_id") or _extract_first([r"media_id['\": ]+([\w-]+)"], output)
    return media_id, output


def _upload_content_image(wechat_script: str, filename: str) -> tuple[str | None, str]:
    output = _run(["python3", wechat_script, "upload-content-image", filename])
    payload = _parse_json_like(output)
    url = payload.get("url") or _extract_first([r"(https?://\S+)"], output)
    return url, output


def _create_draft(wechat_script: str, article: dict[str, Any], html_text: str) -> tuple[str | None, str]:
    meta = article["meta"]
    cmd = [
        "python3",
        wechat_script,
        "draft-add",
        "--title",
        str(meta["title"]),
        "--content",
        html_text,
        "--thumb",
        str(meta["thumb_media_id"]),
        "--author",
        str(meta["author"]),
        "--digest",
        str(meta["digest"]),
        "--open-comment",
        str(meta.get("open_comment", 1)),
    ]
    output = _run(cmd)
    payload = _parse_json_like(output)
    draft_id = payload.get("media_id") or payload.get("draft_media_id") or _extract_first([r"media_id['\": ]+([\w-]+)"], output)
    return draft_id, output


def _publish_draft(wechat_script: str, draft_media_id: str) -> tuple[str | None, str]:
    output = _run(["python3", wechat_script, "publish", draft_media_id])
    payload = _parse_json_like(output)
    publish_id = payload.get("publish_id") or _extract_first([r"publish_id['\": ]+([\w-]+)"], output)
    return publish_id, output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local render/validate/publish pipeline for a WeChat article.")
    parser.add_argument("input", help="Path to article JSON")
    parser.add_argument("--output-dir", default="build", help="Directory for rendered files and planned images")
    parser.add_argument("--resolved-article", help="Write the resolved article JSON to this file")
    parser.add_argument("--skip-plan-images", action="store_true", help="Do not attach missing image prompts/paths")
    parser.add_argument("--max-content-images", type=int, default=3, help="Number of non-cover images to plan")
    parser.add_argument("--nanobanana-script", help="Path to generate_image.py for prompt-based image generation")
    parser.add_argument("--wechat-script", help="Path to wechat_mp.py for upload/draft/publish")
    parser.add_argument("--create-draft", action="store_true", help="Create a WeChat draft after render/validation")
    parser.add_argument("--publish", action="store_true", help="Publish immediately after draft creation")
    parser.add_argument("--dry-run", action="store_true", help="Only render and validate locally")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        article = load_json(args.input)
        if args.publish and not args.create_draft:
            raise ArticleError("--publish requires --create-draft in the current pipeline")
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not args.skip_plan_images:
            article = attach_missing_image_plans(article, output_dir=output_dir / "images", max_content_images=args.max_content_images)

        meta = ensure_meta_defaults(article)
        cover = dict(meta.get("cover_image") or {})
        if args.nanobanana_script and not args.dry_run and cover.get("prompt") and cover.get("local_path") and not Path(cover["local_path"]).exists():
            _generate_image(args.nanobanana_script, cover["prompt"], cover["local_path"])

        for image in find_content_images(article):
            if args.nanobanana_script and not args.dry_run and image.get("prompt") and image.get("local_path") and not Path(image["local_path"]).exists():
                _generate_image(args.nanobanana_script, image["prompt"], image["local_path"])

        if args.wechat_script and not args.dry_run:
            if cover.get("local_path") and not meta.get("thumb_media_id"):
                media_id, _ = _upload_cover(args.wechat_script, cover["local_path"])
                if media_id:
                    meta["thumb_media_id"] = media_id

            for image in find_content_images(article):
                if image.get("local_path") and not image.get("url"):
                    url, _ = _upload_content_image(args.wechat_script, image["local_path"])
                    if url:
                        image["url"] = url

        html_text = render_article(article)
        validation = validate_article(article, html_text=html_text)
        if not validation.ok:
            for error in validation.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            for warning in validation.warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
            return 1

        for warning in validation.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        html_path = output_dir / f"{Path(args.input).stem}.html"
        html_path.write_text(html_text, encoding="utf-8")

        resolved_path = Path(args.resolved_article) if args.resolved_article else output_dir / f"{Path(args.input).stem}.resolved.json"
        dump_json(resolved_path, article)

        draft_media_id = None
        publish_id = None
        if args.create_draft:
            if args.dry_run:
                print("WARNING: --create-draft ignored during dry-run", file=sys.stderr)
            elif not args.wechat_script:
                raise ArticleError("--wechat-script is required for --create-draft")
            elif not meta.get("thumb_media_id"):
                raise ArticleError("meta.thumb_media_id is missing; upload-image must finish before draft creation")
            else:
                draft_media_id, draft_output = _create_draft(args.wechat_script, article, html_text)
                print(draft_output, file=sys.stderr)
                if args.publish:
                    if not draft_media_id:
                        raise ArticleError("Failed to parse draft media_id from draft-add output")
                    publish_id, publish_output = _publish_draft(args.wechat_script, draft_media_id)
                    print(publish_output, file=sys.stderr)

        summary = {
            "html": str(html_path),
            "resolved_article": str(resolved_path),
            "draft_media_id": draft_media_id,
            "publish_id": publish_id,
            "cover_media_id": meta.get("thumb_media_id"),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (ArticleError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
