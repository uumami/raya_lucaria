---
title: "Architecture"
summary: "Pipeline, directories, data flow, and build system"
---

# Architecture

## Three-Stage Pipeline

Glintstone uses a three-stage build pipeline:

1. **Python preprocessing** -- Reads Markdown frontmatter, builds hierarchy tree, aggregates tasks, writes JSON data files
2. **Eleventy (11ty)** -- Static site generator that reads Markdown + JSON data + Nunjucks templates to produce HTML
3. **Post-processing** -- Tailwind CSS generation, esbuild JS bundling, static asset copying, Pagefind search indexing

## Directory Structure

```
course-repo/
├── clase/                    # Course content (Eleventy input)
├── glintstone/               # Framework (git submodule)
│   ├── src/
│   │   ├── preprocessing/    # Python package
│   │   │   ├── cli.py        # CLI entry point
│   │   │   ├── config.py     # Config loader
│   │   │   ├── extract_metadata.py
│   │   │   ├── generate_hierarchy.py
│   │   │   ├── aggregate_tasks.py
│   │   │   ├── validate_content.py
│   │   │   └── schemas/config.py
│   │   └── eleventy/         # Eleventy project
│   │       ├── .eleventy.js  # Thin orchestrator (~60 lines)
│   │       ├── lib/          # Modular JS
│   │       │   ├── markdown.js
│   │       │   ├── components.js
│   │       │   ├── filters.js
│   │       │   ├── collections.js
│   │       │   └── transforms.js
│   │       ├── _includes/
│   │       │   ├── layouts/  # base, chapter, task-list, 404
│   │       │   └── components/ # nav, toc, search, etc.
│   │       ├── _data/        # Generated JSON (by preprocessing)
│   │       └── src/
│   │           ├── css/      # Tailwind + theme files
│   │           ├── js/       # Frontend ES modules
│   │           ├── fonts/    # Self-hosted fonts
│   │           └── vendor/   # KaTeX, Mermaid
│   ├── docs/                 # Framework documentation (this)
│   └── docker/               # Dockerfile + docker-compose + scripts
├── glintstone.yaml            # Course configuration
├── _site/                    # Build output (gitignored)
└── calendario_temas.csv      # Optional calendar
```

## Data Flow

```
Markdown in clase/
    ↓ Python extracts frontmatter, components
    ↓ Builds hierarchy tree
    ↓ Aggregates tasks (homework, exam, project)
JSON data in _data/
    ↓ metadata.json, hierarchy.json, tasks.json, etc.
    ↓ Eleventy reads data + content
    ↓ Applies Nunjucks templates
HTML in _site/
    ↓ Tailwind generates CSS
    ↓ esbuild bundles JS
    ↓ Pagefind indexes content
Static site in _site/
```

## Staging Directory Pattern

The `clase/` directory is mounted read-only in Docker. The build scripts create a `clase-stage/` directory with symlinks to `clase/*` contents, then add generated files (task pages, calendar page, docs symlink) into `clase-stage/`. Eleventy uses `clase-stage/` as its input directory (via `SELLEN_INPUT` env var).

This is why you see `clase-stage` in path-cleaning regexes throughout the codebase.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SELLEN_INPUT` | `clase` | Eleventy input directory (set to `clase-stage` by build scripts) |
| `PATH_PREFIX` | `""` | URL path prefix for GitHub Pages deployment |
| `PORT` | `3000` | Dev server port |

## Docker Multi-Stage Build

The Dockerfile uses three stages:
1. **base** -- Node 20 Alpine + Python 3 + git
2. **deps** -- Installs npm dependencies (cached layer)
3. **runtime** -- Copies node_modules + framework source
