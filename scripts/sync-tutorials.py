#!/usr/bin/env python3
"""
Sync tutorial content from finemcp/finemcp/examples/ into Hugo content/learn/.

Each numbered directory (NN-name/) in ../../finemcp/examples/ becomes a tutorial page.
The README.md is copied with injected Hugo front matter.

Usage:
    python3 scripts/sync-tutorials.py
"""
import os
import re
import shutil
import sys

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "finemcp", "examples")
TUTORIALS_DIR = os.path.join(os.path.dirname(__file__), "..", "content", "learn")

# Map folder name (after stripping NN-) to human-readable title override.
# If not here, the title is taken from the first # heading in the README.
TITLE_OVERRIDES = {}

def slugify(name):
    """Strip numeric prefix and return slug: '01-server' -> 'server'"""
    return re.sub(r"^\d+-", "", name)

def extract_title(readme_text, fallback):
    """Pull the first # Heading from the README, strip the 'NN — ' prefix pattern."""
    m = re.search(r"^#\s+(.+)$", readme_text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        # Strip leading "NN — " or "NN - "
        title = re.sub(r"^\d+\s*[—\-]\s*", "", title)
        return title
    return fallback

def extract_description(readme_text):
    """Pull the first non-heading, non-empty paragraph after the title."""
    lines = readme_text.splitlines()
    past_title = False
    for line in lines:
        if line.startswith("# "):
            past_title = True
            continue
        if past_title and line.strip() and not line.startswith("#"):
            # Remove markdown formatting for description
            desc = re.sub(r"`([^`]+)`", r"\1", line.strip())
            desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)
            return desc[:160]
    return ""

def strip_title_line(readme_text):
    """Remove the first # heading line since Hugo renders the title itself."""
    return re.sub(r"^#[^\n]+\n?", "", readme_text, count=1)

def sync():
    if not os.path.isdir(EXAMPLES_DIR):
        print(f"ERROR: examples dir not found: {EXAMPLES_DIR}", file=sys.stderr)
        sys.exit(1)

    # Collect all NN-name directories that have a README.md
    dirs = sorted([
        d for d in os.listdir(EXAMPLES_DIR)
        if re.match(r"^\d+-.+$", d) and
           os.path.isfile(os.path.join(EXAMPLES_DIR, d, "README.md"))
    ])

    if not dirs:
        print("No numbered example directories found.", file=sys.stderr)
        sys.exit(1)

    # Clear existing generated tutorials (keep _index.md)
    for entry in os.listdir(TUTORIALS_DIR):
        path = os.path.join(TUTORIALS_DIR, entry)
        if entry != "_index.md" and os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    for weight, dirname in enumerate(dirs, start=1):
        readme_path = os.path.join(EXAMPLES_DIR, dirname, "README.md")
        slug = slugify(dirname)
        url = f"/learn/{slug}/"

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        title = TITLE_OVERRIDES.get(slug) or extract_title(content, slug.replace("-", " ").title())
        description = extract_description(content)
        body = strip_title_line(content)

        front_matter = f"""---
title: "{title}"
description: "{description}"
weight: {weight}
url: "{url}"
tutorial_number: {weight}
source_dir: "{dirname}"
---
"""
        out_path = os.path.join(TUTORIALS_DIR, f"{slug}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(front_matter)
            f.write(body)

        print(f"  {dirname:25s} -> learn/{slug}.md  ({url})")

    print(f"\nSynced {len(dirs)} tutorials.")

if __name__ == "__main__":
    sync()
