#!/usr/bin/env python3
"""Copy generated daily Markdown into a separate folder in an Obsidian vault."""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "<!-- Managed by ai-daily. Put personal notes in a separate note. -->\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--date", help="Only copy this issue (YYYY-MM-DD).")
    args = parser.parse_args()
    vault = args.vault.expanduser().resolve()
    if not (vault / ".obsidian").is_dir():
        parser.error("--vault must point to an existing Obsidian vault")
    if args.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error("--date must use YYYY-MM-DD")
    source = ROOT / "dist" / "markdown"
    files = sorted(source.glob((args.date + '*' if args.date else '*') + ".md"))
    if not files:
        parser.error("No generated Markdown found; build the website first")
    target = vault / "AI前沿日报"
    if target.is_symlink():
        parser.error("The daily folder must not be a symlink")
    target.mkdir(exist_ok=True)
    updated = 0
    for path in files:
        if path.is_symlink() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+)*\.md", path.name):
            parser.error("Unexpected Markdown source")
        dest = target / path.name
        content = MARKER + path.read_text(encoding="utf-8")
        if dest.is_symlink():
            parser.error(f"Refusing symlink: {dest.name}")
        if dest.exists():
            previous = dest.read_text(encoding="utf-8")
            if previous == content:
                continue
            if not previous.startswith(MARKER):
                parser.error(f"Refusing to overwrite a personal note: {dest.name}")
        temporary = dest.with_suffix(".md.tmp")
        if temporary.exists():
            parser.error(f"Temporary file already exists: {temporary.name}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(content)
        temporary.replace(dest)
        updated += 1
    print(f"Synced {updated} issues into {target}")


if __name__ == "__main__":
    main()
