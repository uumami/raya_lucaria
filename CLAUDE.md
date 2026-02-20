# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Raya Lucaria** is an integrated learning platform for ITAM course materials. The **Glintstone** layer is the content engine — a static site generator that uses a three-stage pipeline: Python preprocessing -> Eleventy (11ty) SSG -> Tailwind CSS. Content is authored in Markdown under `clase/`, processed into a navigable course website, and deployed to GitHub Pages.

Primary content language is Spanish. Framework code and dev docs are in English.

## Build & Development Commands

All builds run inside Docker. Execute from the **course repo root** (where `glintstone.yaml` lives):

```bash
# Full production build (output in _site/)
docker compose -f glintstone/docker/docker-compose.yaml up build

# Dev server with hot reload (port 3000)
docker compose -f glintstone/docker/docker-compose.yaml up dev

# Run only Python preprocessing
docker compose -f glintstone/docker/docker-compose.yaml up preprocess

# Run content validation
docker compose -f glintstone/docker/docker-compose.yaml up validate

# Run tests
docker compose -f glintstone/docker/docker-compose.yaml up test
```

For the example course (`ejemplo/`), run from inside `ejemplo/`:

```bash
cd ejemplo && docker compose up build   # Build (port N/A)
cd ejemplo && docker compose up dev     # Dev server (port 3001)
```

### Running Tests Locally (without Docker)

```bash
# Python tests (from repo root)
PYTHONPATH=src pytest tests/python/ -v

# Single Python test file
PYTHONPATH=src pytest tests/python/test_config.py -v

# Single Python test function
PYTHONPATH=src pytest tests/python/test_validate_content.py::test_function_name -v

# Node tests (from src/eleventy/)
cd src/eleventy && npx vitest run
```

### Build Pipeline Order

1. `PYTHONPATH=glintstone/src python3 -m preprocessing build` -- generates JSON data files in `_data/`
2. Staging: symlinks `clase/*` into writable `clase-stage/`, adds generated task pages + docs
3. `eleventy` with `SELLEN_INPUT=clase-stage` -- builds HTML from Markdown + Nunjucks templates
4. `tailwindcss` -- generates CSS
5. `esbuild` -- bundles JavaScript
6. Static asset copying (themes, fonts, vendor libs)
7. `pagefind` -- generates search index

## Architecture

### Staging Directory Pattern

`clase/` is mounted read-only in Docker. Build scripts create `clase-stage/` with symlinks to `clase/*` contents, then inject generated files (task pages, calendar page, docs symlink). Eleventy uses `clase-stage/` as input via the `SELLEN_INPUT` env var. This is why path-cleaning regexes throughout the codebase strip both `clase/` and `clase-stage/`.

### Thin Orchestrator

`.eleventy.js` (~78 lines) delegates all logic to `lib/` modules:
- `markdown.js` -- markdown-it + dollarmath + containers + anchors
- `components.js` -- Component registry and rendering (REGISTRY object)
- `filters.js` -- Nunjucks filters
- `collections.js` -- Content + docs collections with sort ordering
- `transforms.js` -- HTML transforms (fix links/images)
- `passthrough.js` -- Asset copying
- `search.js` -- Pagefind integration
- `path-prefix.js` -- URL prefix resolution

### Python Preprocessing CLI

Entry point: `python3 -m preprocessing <command>` (with `PYTHONPATH` pointing to `src/`)

Commands:
- `build` (default) -- Full pipeline: extract metadata, generate hierarchy, aggregate tasks, write JSON
- `validate` -- Content validation only (unclosed components, duplicate IDs, broken links)
- `scaffold chapter "03_name"` -- Generate chapter directory structure
- `scaffold homework` -- Print component template

### Data Files (generated, never edit manually)

`src/eleventy/_data/`: `metadata.json`, `hierarchy.json`, `hierarchy_docs.json`, `tasks.json`, `repo.json`, `site.json`, `features.json`, `navigation.json`, `taskPages.json`

### Content Naming Conventions

- `01_`, `02_` -- Numbered chapters (nav: 1, 2, ...)
- `a_`, `b_` -- Lettered appendices (nav: A, B, ...)
- `z_` -- Documentation sections (sorted last)
- `??_` -- Work-in-progress (excluded from build)
- `00_index.md` -- Section index page (hidden from nav, uses `layout: layouts/chapter.njk`)

### Component System

Eight types: homework, exercise, prompt, example, exam, project, quiz, embed. Syntax: `:::type{key="value"}` ... `:::`. Components with `id` attributes (homework, exam, project) aggregate to task pages. Quiz provides interactive multiple-choice. Embed renders responsive iframes. See `CONTENT_SPEC.md` for full reference.

### Theme System

12 themes in 6 families (dark/light each): EVA-00, EVA-01, EVA-02, EVA-05 Mari, Elden Ring, Raya Lucaria. Theme CSS files use CSS custom properties in `src/eleventy/src/css/themes/`. Creating a new theme = copy a CSS file and change hex values.

### Built-in Documentation

`docs/` contains framework documentation rendered at `/docs/` URLs. Controlled by `features.docs` flag in `glintstone.yaml`. Three sections: student guide (Spanish), professor guide (Spanish), agent guide (English). The agent guide at `docs/03_agentes/` contains detailed technical reference for AI agents.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SELLEN_INPUT` | `clase` | Eleventy input directory (build scripts set to `clase-stage`) |
| `PATH_PREFIX` | `""` | URL path prefix for GitHub Pages |
| `PORT` | `3000` | Dev server port |
