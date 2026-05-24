# finemcp/finemcp.dev

Source for [finemcp.dev](https://finemcp.dev) — the Hugo static site for the FineMCP project.

Built with Hugo `0.157.0+extended`. Deployed to GitHub Pages on every push to `main`.

---

## How it works

This repo is the **website only**. Docs and examples live in the main Go repo ([finemcp/finemcp](https://github.com/finemcp/finemcp)) and are pulled in at build time:

| Content | Source |
|---|---|
| `/docs/` | `finemcp/finemcp/docs/` (Hugo mount) |
| `/learn/` | `finemcp/finemcp/examples/*/README.md` (sync script) |
| `/blog/` | `content/blog/` in this repo |
| `/releases/` | GitHub Releases API (sync script) |

---

## Local development

### Prerequisites

- [Hugo](https://gohugo.io/installation/) `0.157.0+extended`
- Python 3 (for sync scripts)
- Both repos cloned side-by-side (see below)

### Directory layout

The website expects `finemcp/finemcp` to be checked out **one level up** (as a sibling), matching the layout used in CI:

```
workspace/
├── finemcp/    ← github.com/finemcp/finemcp  (docs + examples live here)
└── web/        ← github.com/finemcp/finemcp.dev  (this repo)
```

### Setup

```bash
# Clone both repos side-by-side
git clone https://github.com/finemcp/finemcp.git path/to/workspace/finemcp
git clone https://github.com/finemcp/finemcp.dev.git path/to/workspace/web

cd path/to/workspace/web

# Sync tutorial content from finemcp/examples/ into content/learn/
make sync-tutorials

# Start the dev server
make dev
# → http://localhost:1313
```

### Available commands

```
make dev              Start local dev server with live reload
make build            Build production site into public/
make clean            Remove public/ and Hugo cache
make sync-tutorials   Pull tutorial content from ../../finemcp/examples/
make sync-releases    Fetch release notes from GitHub into content/releases/
make post TITLE='...' Create a new draft blog post
```

---

## Adding content

### Blog post

```bash
make post TITLE="My Post Title"
# Creates content/blog/my-post-title.md — edit, then set draft: false
```

### Docs

Edit markdown files directly in `finemcp/finemcp/docs/`. Hugo mounts that directory at `/docs/` automatically — no sync step needed.

### Tutorials

Tutorials are generated from the `README.md` of each numbered example directory in `finemcp/finemcp/examples/`. Edit the README there, then run `make sync-tutorials`.

---

## Repo structure

```
web/
├── config.toml                  # site config, Hugo mounts, params
├── content/                     # blog posts, releases (generated), learn (generated)
├── layouts/                     # Hugo templates
│   ├── index.html               # landing page
│   ├── blog/                    # blog list + single post
│   ├── docs/                    # docs single page
│   ├── docsroot/                # /docs/ index
│   ├── learn/                   # learn list + single page
│   ├── releases/                # changelog list + single page
│   ├── shortcodes/              # callout, card, cards
│   └── partials/                # header, footer, docs-sidebar
├── static/
│   ├── css/main.css             # single stylesheet
│   └── images/finemcp-logo.png  # logo
├── scripts/
│   ├── sync-tutorials.py        # generates content/learn/ from finemcp/examples/
│   ├── sync-releases.py         # generates content/releases/ from GitHub API
│   └── check_links.py           # crawl localhost:1313 and report broken links
├── .github/
│   └── workflows/deploy.yml     # CI: build + deploy to GitHub Pages
├── Makefile
└── README.md
```

---

## CI / Deployment

The deploy workflow (`.github/workflows/deploy.yml`) checks out both repos side-by-side, mirroring local development:

```
runner workspace/
├── finemcp/    ← finemcp/finemcp checkout
└── web/        ← this repo checkout
```

This means `../finemcp/` resolves identically in both local and CI environments — no path overrides needed.

**Trigger:** push to `main` or manual `workflow_dispatch`.

**Required GitHub repo settings (one-time):**
- Settings → Pages → Source → **GitHub Actions**

