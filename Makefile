.PHONY: help dev build clean sync-tutorials sync-releases post

HUGO        := hugo
HUGO_ARGS   := --logLevel warn
BUILD_ARGS  := --minify --logLevel warn

# Paths to the main finemcp repo (sibling of this repo).
# Docs:     ../../finemcp/docs/
# Examples: ../../finemcp/examples/
FINEMCP_REPO := ../finemcp

# Default target
help:
	@echo ""
	@echo "  make dev              Start local dev server (localhost:1313)"
	@echo "  make build            Build site into public/"
	@echo "  make clean            Remove public/ and Hugo cache"
	@echo "  make sync-tutorials   Sync example READMEs from $(FINEMCP_REPO)/examples/"
	@echo "  make sync-releases    Fetch release notes from GitHub into content/releases/"
	@echo "  make post TITLE='...' Create a new draft blog post"
	@echo ""
	@echo "  Docs source:     $(FINEMCP_REPO)/docs/"
	@echo "  Examples source: $(FINEMCP_REPO)/examples/"
	@echo ""

## Start dev server with live reload (syncs tutorials first)
dev: sync-tutorials
	$(HUGO) serve $(HUGO_ARGS)

## Sync example READMEs from finemcp/finemcp/examples/ into content/tutorials/
sync-tutorials:
	python3 scripts/sync-tutorials.py

## Fetch release notes from GitHub Releases into content/releases/
## Set GITHUB_TOKEN to avoid rate limits: GITHUB_TOKEN=ghp_xxx make sync-releases
sync-releases:
	python3 scripts/sync-releases.py

## Build production site into public/
build: clean sync-tutorials sync-releases
	$(HUGO) $(BUILD_ARGS)

## Remove generated output and build lock
clean:
	rm -rf public/ resources/_gen/ .hugo_build.lock

## Create a new draft blog post: make post TITLE="My Post Title"
post:
ifndef TITLE
	$(error TITLE is required — usage: make post TITLE="My Post Title")
endif
	$(HUGO) new content/blog/$(shell echo "$(TITLE)" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g').md
