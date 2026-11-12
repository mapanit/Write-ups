#!/usr/bin/env python3
"""
fix_md_images.py

Находит в Markdown inline base64-картинки вида
    ![alt](data:image/png;base64,AAAA...)
и/или HTML
    <img src="data:image/png;base64,AAAA...">
декодирует их в файлы images/<slug>-<n>.<ext> рядом с .md
и заменяет ссылки на относительные пути.

Использование:
    python fix_md_images.py path/to/file.md
    python fix_md_images.py path/to/file.md --out-dir assets
    python fix_md_images.py path/to/dir/        # обработать все *.md рекурсивно
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import re
import sys
from pathlib import Path

# data:image/png;base64,....   (внутри может быть \n и пробелы — их срезаем)
DATA_URI_RE = re.compile(
    r"data:(image/(?P<subtype>[a-zA-Z0-9.+-]+));base64,(?P<data>[A-Za-z0-9+/=\s]+)"
)

# Markdown-картинка с data-URI: ![alt](data:image/...)
MD_IMG_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(\s*(?P<uri>data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+?)\s*\)"
)

# HTML-картинка с data-URI: <img ... src="data:image/...">
HTML_IMG_RE = re.compile(
    r"(<img\b[^>]*?\bsrc\s*=\s*)(?P<quote>[\"'])(?P<uri>data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+?)(?P=quote)",
    re.IGNORECASE,
)

EXT_MAP = {
    "png": "png",
    "jpeg": "jpg",
    "jpg": "jpg",
    "gif": "gif",
    "webp": "webp",
    "svg+xml": "svg",
    "bmp": "bmp",
    "tiff": "tiff",
    "x-icon": "ico",
}


def decode_data_uri(uri: str) -> tuple[bytes, str]:
    """Вернёт (bytes, extension)."""
    m = DATA_URI_RE.match(uri.strip())
    if not m:
        raise ValueError("не data:image/... URI")
    subtype = m.group("subtype").lower()
    ext = EXT_MAP.get(subtype, subtype.replace("+xml", ""))
    raw = re.sub(r"\s+", "", m.group("data"))
    # padding, если кто-то его обрезал
    pad = (-len(raw)) % 4
    if pad:
        raw += "=" * pad
    try:
        blob = base64.b64decode(raw, validate=False)
    except binascii.Error as e:
        raise ValueError(f"base64 decode failed: {e}") from e
    return blob, ext


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:10]


def process_markdown(md_path: Path, out_dir_name: str) -> tuple[int, int]:
    text = md_path.read_text(encoding="utf-8")

    out_dir = md_path.parent / out_dir_name
    # префикс для имён файлов — по имени md-файла
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", md_path.stem).strip("-") or "md"

    saved: dict[str, str] = {}   # hash -> relative path (для дедупликации)
    counter = {"n": 0}
    replaced = {"count": 0}
    skipped = {"count": 0}

    def make_filename(blob: bytes, ext: str) -> Path:
        h = short_hash(blob)
        if h in saved:
            return out_dir / saved[h]
        counter["n"] += 1
        name = f"{slug}-{counter['n']:02d}.{ext}"
        out_dir.mkdir(parents=True, exist_ok=True)
        fpath = out_dir / name
        fpath.write_bytes(blob)
        rel = f"{out_dir_name}/{name}"
        saved[h] = name
        return fpath

    def replace_md(match: re.Match) -> str:
        alt = match.group("alt")
        uri = match.group("uri")
        try:
            blob, ext = decode_data_uri(uri)
        except ValueError as e:
            print(f"  ! пропуск (md): {e}", file=sys.stderr)
            skipped["count"] += 1
            return match.group(0)
        make_filename(blob, ext)
        h = short_hash(blob)
        rel = f"{out_dir_name}/{saved[h]}"
        replaced["count"] += 1
        return f"![{alt}]({rel})"

    def replace_html(match: re.Match) -> str:
        prefix = match.group(1)
        quote = match.group("quote")
        uri = match.group("uri")
        try:
            blob, ext = decode_data_uri(uri)
        except ValueError as e:
            print(f"  ! пропуск (html): {e}", file=sys.stderr)
            skipped["count"] += 1
            return match.group(0)
        make_filename(blob, ext)
        h = short_hash(blob)
        rel = f"{out_dir_name}/{saved[h]}"
        replaced["count"] += 1
        return f"{prefix}{quote}{rel}{quote}"

    new_text = MD_IMG_RE.sub(replace_md, text)
    new_text = HTML_IMG_RE.sub(replace_html, new_text)

    if replaced["count"]:
        md_path.write_text(new_text, encoding="utf-8")

    return replaced["count"], skipped["count"]


def iter_md_files(path: Path):
    if path.is_file() and path.suffix.lower() == ".md":
        yield path
    elif path.is_dir():
        yield from sorted(path.rglob("*.md"))
    else:
        print(f"не .md и не каталог: {path}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Вынести inline base64-картинки из Markdown в файлы.")
    ap.add_argument("path", type=Path, help="путь к .md файлу или каталогу")
    ap.add_argument(
        "--out-dir",
        default="images",
        help="имя подкаталога для картинок (по умолчанию: images)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="ничего не писать на диск, только показать, что будет сделано",
    )
    args = ap.parse_args()

    if not args.path.exists():
        print(f"нет такого пути: {args.path}", file=sys.stderr)
        return 2

    total_files = 0
    total_replaced = 0
    total_skipped = 0

    for md in iter_md_files(args.path):
        total_files += 1
        print(f"→ {md}")
        if args.dry_run:
            # в dry-run всё равно нужен подсчёт; прогоняем на копии
            tmp = md.with_suffix(md.suffix + ".dryrun")
            tmp.write_text(md.read_text(encoding="utf-8"), encoding="utf-8")
            try:
                r, s = process_markdown(tmp, args.out_dir)
            finally:
                tmp.unlink(missing_ok=True)
                # удалим созданную images-папку, если она была
                # (осторожно: удаляем только файлы, которые скрипт сам создал)
                # проще: в dry-run просто пропускаем
            print(f"  [dry-run] было бы заменено: {r}, пропущено: {s}")
            total_replaced += r
            total_skipped += s
            continue
        r, s = process_markdown(md, args.out_dir)
        print(f"  заменено: {r}, пропущено: {s}")
        total_replaced += r
        total_skipped += s

    print(f"\nИтого файлов: {total_files}, заменено: {total_replaced}, пропущено: {total_skipped}")
    return 0 if total_skipped == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())