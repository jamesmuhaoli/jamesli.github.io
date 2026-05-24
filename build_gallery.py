#!/usr/bin/env python3
"""Regenerate the photo gallery in photography.html from the photography/ folder.

WORKFLOW
--------
1. Drop a new photo into  photography/  named like:  place_words_month_year[_counter].JPG
   examples:   sacramento_may_2026.JPG          -> "Sacramento - May 2026"
               san_diego_march_2026_2.JPG       -> "San Diego - March 2026"
               Wisconsin_capitol_April_2026.JPG -> "Wisconsin Capitol - April 2026"
2. Run:  python3 build_gallery.py
3. Commit & push:  git add -A && git commit -m "Add photos" && git push

The script only rewrites the block between the
<!-- BEGIN AUTO-GALLERY --> and <!-- END AUTO-GALLERY --> markers in
photography.html. Everything else (head, styles, nav, lightbox, scripts)
is left untouched.

If the auto-generated caption for a file isn't quite right, add an entry to
CAPTION_OVERRIDES below (key = filename without extension).
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHOTO_DIR = HERE / "photography"
HTML_FILE = HERE / "photography.html"

BEGIN = "<!-- BEGIN AUTO-GALLERY -->"
END = "<!-- END AUTO-GALLERY -->"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mov", ".mp4", ".webm"}

MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
MONTH_INDEX = {m: i + 1 for i, m in enumerate(MONTHS)}

# Captions the auto-formatter can't infer perfectly.
# Key = filename stem (no extension). Value = exact caption text.
CAPTION_OVERRIDES = {
    "chin_hills_april_2026": "Chino Hill - April 2026",
    "del_mar_blvd_Pasadena_April_2026": "Del Mar Blvd, Pasadena - April 2026",
    "mendota_lake_wisconsin_april_2026": "Mendota Lake, Wisconsin - April 2026",
    "mendota_lake_wisconsin_April_2026": "Mendota Lake, Wisconsin - April 2026",
}

DASH = "—"  # em dash used in the rendered captions


def parse_caption(stem):
    """Turn a filename stem into 'Place - Month Year'."""
    if stem in CAPTION_OVERRIDES:
        return CAPTION_OVERRIDES[stem].replace(" - ", f" {DASH} ")

    tokens = stem.split("_")
    # Strip a trailing numeric counter like _1, _2 (but not a 4-digit year).
    if len(tokens) > 1 and tokens[-1].isdigit() and len(tokens[-1]) <= 2:
        tokens = tokens[:-1]

    month = year = None
    place_tokens = tokens
    for i, tok in enumerate(tokens):
        if tok.lower() in MONTH_INDEX:
            month = tok.capitalize()
            if i + 1 < len(tokens) and re.fullmatch(r"\d{4}", tokens[i + 1]):
                year = tokens[i + 1]
            place_tokens = tokens[:i]
            break

    place = " ".join(t.capitalize() for t in place_tokens) if place_tokens else stem
    if month and year:
        return f"{place} {DASH} {month} {year}"
    if month:
        return f"{place} {DASH} {month}"
    return place


def date_key(stem):
    """Sort key: newest first by (year, month), then filename."""
    tokens = stem.split("_")
    y = m = 0
    for i, tok in enumerate(tokens):
        if tok.lower() in MONTH_INDEX:
            m = MONTH_INDEX[tok.lower()]
            if i + 1 < len(tokens) and re.fullmatch(r"\d{4}", tokens[i + 1]):
                y = int(tokens[i + 1])
            break
    return (-y, -m, stem.lower())


def main():
    if not PHOTO_DIR.is_dir():
        raise SystemExit(f"Photo folder not found: {PHOTO_DIR}")

    files = [p for p in PHOTO_DIR.iterdir()
             if p.is_file() and p.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS]
    files.sort(key=lambda p: date_key(p.stem))

    # Map of image stems (lowercased) -> path, for matching video posters.
    images_by_stem = {p.stem.lower(): p for p in files
                      if p.suffix.lower() in IMAGE_EXTS}

    blocks = []
    print(f"Found {len(files)} item(s) in {PHOTO_DIR.name}/:\n")
    for p in files:
        caption = parse_caption(p.stem)
        caption_e = html.escape(caption)
        rel = f"photography/{p.name}"
        print(f"  {p.name:45s} -> {caption}")

        if p.suffix.lower() in VIDEO_EXTS:
            poster = images_by_stem.get(p.stem.lower())
            poster_attr = f'\n                 poster="photography/{poster.name}"' if poster else ""
            block = f'''        <figure class="photo">
          <video controls preload="metadata" playsinline{poster_attr}>
            <source src="{rel}" type="video/quicktime">
            <source src="{rel}" type="video/mp4">
            Your browser does not support embedded video.
          </video>
          <figcaption class="caption">{caption_e} (video)</figcaption>
        </figure>'''
        else:
            alt = html.escape(caption.replace(f" {DASH} ", ", "))
            block = f'''        <figure class="photo">
          <img src="{rel}"
               alt="{alt}"
               loading="lazy"
               data-caption="{caption_e}">
          <figcaption class="caption">{caption_e}</figcaption>
        </figure>'''
        blocks.append(block)

    gallery = "\n\n".join(blocks)

    source = HTML_FILE.read_text(encoding="utf-8")
    if BEGIN not in source or END not in source:
        raise SystemExit(
            f"Markers not found in {HTML_FILE.name}. Expected:\n  {BEGIN}\n  {END}")

    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    replacement = f"{BEGIN}\n\n{gallery}\n\n        {END}"
    HTML_FILE.write_text(pattern.sub(replacement, source), encoding="utf-8")

    print(f"\nWrote {len(files)} item(s) into {HTML_FILE.name}.")


if __name__ == "__main__":
    main()
