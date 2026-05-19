#!/usr/bin/env python3
"""
Sync release notes from GitHub Releases into Hugo content/releases/.

For each published (non-draft, non-prerelease by default) GitHub Release, one
markdown file is written to content/releases/ with Hugo front matter.  The
release body is used as-is — it is expected to be Markdown.

Usage:
    # Uses GITHUB_TOKEN env var if available (required for private repos;
    # raises the rate-limit for public repos from 60 → 5 000 req/h)
    python3 scripts/sync-releases.py

    # Include pre-releases
    INCLUDE_PRERELEASES=1 python3 scripts/sync-releases.py

Environment variables:
    GITHUB_TOKEN        Personal access token or Actions token (optional for
                        public repos, but strongly recommended to avoid rate
                        limiting during CI).
    GITHUB_REPOSITORY   Override the repo slug (default: parsed from config.toml
                        or hardcoded fallback "finemcp/finemcp").
    INCLUDE_PRERELEASES Set to "1" to also sync pre-release entries.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR   = Path(__file__).parent
WEB_DIR      = SCRIPT_DIR.parent
CONFIG_FILE  = WEB_DIR / "config.toml"
RELEASES_DIR = WEB_DIR / "content" / "releases"

# Parse repo slug from config.toml so there is a single source of truth.
def _repo_from_config() -> str:
    try:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        m = re.search(r'githubURL\s*=\s*"https://github\.com/([^"]+)"', text)
        if m:
            return m.group(1).rstrip("/")
    except FileNotFoundError:
        pass
    return "finemcp/finemcp"

REPO             = os.environ.get("GITHUB_REPOSITORY") or _repo_from_config()
GITHUB_TOKEN     = os.environ.get("GITHUB_TOKEN", "")
INCLUDE_PRE      = os.environ.get("INCLUDE_PRERELEASES", "0").strip() == "1"
API_BASE         = "https://api.github.com"
PER_PAGE         = 100   # maximum allowed by GitHub API


# ---------------------------------------------------------------------------
# GitHub API helper
# ---------------------------------------------------------------------------

def _gh_get(path: str) -> list | dict:
    """Fetch a paginated or single GitHub API endpoint and return parsed JSON."""
    url = f"{API_BASE}{path}"
    results = []
    page = 1

    while True:
        paged_url = f"{url}?per_page={PER_PAGE}&page={page}"
        req = urllib.request.Request(paged_url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if GITHUB_TOKEN:
            req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            print(f"ERROR: GitHub API {paged_url} → HTTP {exc.code}: {exc.reason}",
                  file=sys.stderr)
            if exc.code == 401:
                print("  Hint: set GITHUB_TOKEN to a valid personal access token.",
                      file=sys.stderr)
            elif exc.code == 403:
                print("  Hint: rate limit exceeded — set GITHUB_TOKEN.",
                      file=sys.stderr)
            elif exc.code == 404:
                print(f"  Hint: repo '{REPO}' not found or not accessible.",
                      file=sys.stderr)
            sys.exit(1)

        if isinstance(data, list):
            results.extend(data)
            if len(data) < PER_PAGE:
                break   # last page
            page += 1
        else:
            return data  # single-object endpoints

    return results


# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

def _slug(tag: str) -> str:
    """'v1.2.3' → 'v1-2-3'  (safe filename, mirrors Hugo URL)"""
    return re.sub(r"[^a-zA-Z0-9]+", "-", tag).strip("-")


# ---------------------------------------------------------------------------
# Front-matter helpers
# ---------------------------------------------------------------------------

def _escape(s: str) -> str:
    return s.replace('"', '\\"')


def _build_front_matter(release: dict, weight: int) -> str:
    tag      = release["tag_name"]
    title    = release.get("name") or tag
    date_raw = release.get("published_at") or release.get("created_at") or ""
    date     = date_raw[:10]           # ISO 8601 date only
    url_path = f"/releases/{_slug(tag)}/"
    gh_url   = release.get("html_url", "")
    is_pre   = release.get("prerelease", False)

    lines = [
        "---",
        f'title: "{_escape(title)}"',
        f'date: {date}',
        f'weight: {weight}',
        f'url: "{url_path}"',
        f'github_url: "{gh_url}"',
    ]
    if is_pre:
        lines.append("prerelease: true")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main sync
# ---------------------------------------------------------------------------

def sync() -> None:
    print(f"Fetching releases for {REPO} …")
    all_releases: list[dict] = _gh_get(f"/repos/{REPO}/releases")

    # Filter out drafts; optionally keep pre-releases based on env flag.
    releases = [
        r for r in all_releases
        if not r.get("draft", False)
        and (INCLUDE_PRE or not r.get("prerelease", False))
    ]

    if not releases:
        print("No published releases found — nothing to write.", file=sys.stderr)
        return

    # Newest first (GitHub returns newest first already, but sort defensively).
    releases.sort(key=lambda r: r.get("published_at") or r.get("created_at") or "",
                  reverse=True)

    # Clear existing generated files (keep _index.md).
    for p in RELEASES_DIR.iterdir():
        if p.name != "_index.md" and p.suffix == ".md":
            p.unlink()

    for weight, release in enumerate(releases, start=1):
        tag  = release["tag_name"]
        slug = _slug(tag)
        body = (release.get("body") or "").strip()

        # If the release body is empty, insert a minimal placeholder so the
        # page still renders.
        if not body:
            body = f"_No release notes provided. See the [GitHub release]({release.get('html_url', '')})._"

        front_matter = _build_front_matter(release, weight)
        out_path = RELEASES_DIR / f"{slug}.md"

        out_path.write_text(front_matter + "\n" + body + "\n", encoding="utf-8")
        print(f"  {tag:20s} → releases/{slug}.md")

    print(f"\nSynced {len(releases)} release(s) from github.com/{REPO}.")


if __name__ == "__main__":
    sync()
