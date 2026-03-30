# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kube-OVN documentation site — a bilingual (Chinese/English) MkDocs Material project with multi-version support via Mike. Deployed to GitHub Pages at `https://kubeovn.github.io/docs/`.

## Common Commands

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Local development server (http://localhost:8000)
mkdocs serve

# Build and validate (strict mode, used in CI)
mkdocs build -s

# Markdown linting (matches CI)
npx markdownlint-cli "**/*.md" --disable MD013 MD033 MD045 MD024 MD041 MD029 MD051 MD046 MD007 -r markdownlint-rule-search-replace@1.0.9

# Check for Chinese punctuation in English docs
python3 scripts/check-chinese-punctuation.py

# Auto-fix Chinese punctuation in English docs
python3 scripts/check-chinese-punctuation.py --fix

# Cherry-pick commits to release branches
./hack/cherry-pick.sh 'v1.14,v1.13'
```

## Internationalization (i18n)

- **Chinese (default):** `filename.md`
- **English:** `filename.en.md`
- Every document should have both Chinese and English versions side by side in the same directory.
- The i18n plugin (`mkdocs-static-i18n`) handles language switching. UI translations are defined in `mkdocs.yml` under `plugins.i18n.languages`.

## Document Conventions

These rules are enforced by CI linting:

### Punctuation

- Chinese docs: use Chinese punctuation (。，？！；：)
- English docs: use English punctuation only (CI runs `scripts/check-chinese-punctuation.py` to enforce this)
- **Mandatory spacing:** insert a space between Chinese characters and English/numbers (e.g., `安装 Kube-OVN` not `安装 Kube-OVN`). This is enforced by markdownlint search-replace rules in `.markdownlint.json`.

### Code Blocks

- Always specify language: ` ```yaml `, ` ```bash `, etc.
- Commands with output: prefix executed commands with `#` to distinguish from output
- Commands without output: no `#` prefix needed

### Links

- Internal links: use relative `.md` paths (e.g., `./prepare.md`)
- External links: add `{: target="_blank" }` attribute

### Formatting

- Separate logical blocks (headings, text, code) with exactly one blank line
- Sentences in Chinese docs end with `。`; example introductions use `：`

## Architecture

```text
docs/              # All documentation content
  advance/         # Advanced features
  guide/           # User guide
  kubevirt/        # KubeVirt integration
  ops/             # Operations & maintenance
  reference/       # Technical reference
  start/           # Getting started
  vpc/             # VPC networking
  static/          # Images and assets
overrides/         # MkDocs Material theme overrides (main.html, contact.md)
scripts/           # CI scripts (Chinese punctuation checker)
hack/              # Utility scripts (cherry-pick, gh-pages squash)
mkdocs.yml         # Main site configuration (nav, plugins, i18n, theme)
```

## CI Pipeline

PRs run two checks (`.github/workflows/lint.yml`):

1. **Markdown lint** — markdownlint-cli with custom search-replace rules for Chinese-English spacing
2. **Chinese punctuation check** — ensures `.en.md` files have no Chinese punctuation
3. **Build validation** — `mkdocs build -s` must succeed

Pushes to `main`/`master` deploy via Mike with version tags (`.github/workflows/ci.yml`).

## Version Management

- Each Kube-OVN release has a corresponding git branch (`v1.10` through `v1.15`, `master` for dev)
- Mike manages version deployment to `gh-pages`
- Release process documented in README.md — involves branch creation and Mike config changes in `mkdocs.yml`
- `hack/squash.sh` compresses `gh-pages` history to control repo size
