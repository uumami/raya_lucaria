# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Raya Lucaria** is an integrated learning platform for ITAM course materials (see `docs/VISION.md` for the full platform vision). So far, only the **Glintstone** layer has been built — the content engine. It's a static site generator using a three-stage pipeline: Python preprocessing -> Eleventy (11ty) SSG -> Tailwind CSS. Content is authored in Markdown under `clase/`, processed into a navigable course website, and deployed to GitHub Pages.

This repo serves as both the framework and a working example course. Course repos can either fork/template this repo or add it as a git submodule at `glintstone/` and provide their own `clase/` directory and `glintstone.yaml` config.

Primary content language is Spanish. Framework code and dev docs are in English.

## Build & Development Commands

All builds run inside Docker. Execute from the **repo root**:

```bash
# Full production build (output in _site/)
docker compose up build

# Dev server with hot reload (port 3001)
docker compose up dev

# Run only Python preprocessing
docker compose up preprocess

# Run content validation
docker compose up validate
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

`PYTHONPATH=src` is required because the `preprocessing` package lives under `src/preprocessing/`.

### Build Pipeline Order

1. `PYTHONPATH=src python3 -m preprocessing build` -- generates JSON data files in `_data/` (including `graph.json` and `wikilink_map.json`)
2. Staging: symlinks `clase/*` into writable `clase-stage/`, adds generated task pages, docs, graph page
3. `eleventy` with `GLINTSTONE_INPUT=clase-stage` -- builds HTML from Markdown + Nunjucks templates (wikilinks resolved here)
4. `tailwindcss` -- generates CSS
5. `esbuild` -- bundles JavaScript
6. Static asset copying (themes, fonts, vendor libs)
7. `pagefind` -- generates search index

Build scripts also inject dynamic content during staging: task page templates (from `taskPages.json`), calendar page (if `clase/calendario_temas.csv` exists), announcements page (if `clase/anuncios.md` exists), and graph page (if `features.graph` is enabled).

### CI & Deployment

- **Testing** (`.github/workflows/test.yaml`): Runs on push to main and all PRs. Python 3.11 pytest, Node 20 vitest, and integration build. Uses `continue-on-error: true`.
- **Deployment** (`.github/workflows/deploy.yaml`): Builds without Docker (direct Node/Python), auto-detects `PATH_PREFIX` from repo name. Works with any GitHub Pages custom domain — domain is configured at org/user level via `{user}.github.io` CNAME, not per-repo.

## Architecture

### Staging Directory Pattern

`clase/` is mounted read-only in Docker. Build scripts (`docker/scripts/build.sh`) create `clase-stage/` with symlinks to `clase/*` contents, then inject generated files (task pages, calendar page, docs symlink). Eleventy uses `clase-stage/` as input via the `GLINTSTONE_INPUT` env var. This is why path-cleaning regexes in `transforms.js` and elsewhere strip both `clase/` and `clase-stage/`.

### Thin Orchestrator

`.eleventy.js` (~78 lines) delegates all logic to `lib/` modules:
- `markdown.js` -- markdown-it + custom math tokenizer + wikilinks + containers + anchors
- `components.js` -- Component registry and rendering (REGISTRY object with metadata, labels, color vars)
- `filters.js` -- Nunjucks filters (date formatting uses America/Mexico_City timezone)
- `collections.js` -- Content + docs collections with sort ordering
- `transforms.js` -- HTML transforms (fix `.md` links to clean URLs, fix image paths)
- `passthrough.js` -- Asset copying
- `search.js` -- Pagefind integration (production builds only, skipped in dev)
- `path-prefix.js` -- URL prefix resolution (env var → `repo.json` → `/`)

### Python Preprocessing

Entry point: `python3 -m preprocessing <command>` (with `PYTHONPATH` pointing to `src/`)

Commands:
- `build` (default) -- Full pipeline: extract metadata, generate hierarchy, aggregate tasks, build knowledge graph, write JSON
- `validate` -- Content validation only (unclosed components, duplicate IDs, broken links, unresolved wikilinks)
- `scaffold chapter "03_name"` -- Generate chapter directory structure
- `scaffold homework` -- Print component template

Key modules in `src/preprocessing/`:
- `utils.py` -- **Single source of truth** for title generation, path normalization, attribute parsing, sort keys. Modify here (not in copies) when changing naming logic.
- `config.py` -- Loads `glintstone.yaml`, auto-detects git remote info if `repository` section is omitted.
- `extract_links.py` -- Knowledge graph extraction (Primeval Current): link extraction, wikilink resolution, backlinks, graph building.
- `schemas/` -- Dataclasses for config and metadata structures.

### Data Files (generated, never edit manually)

`src/eleventy/_data/`: `metadata.json`, `hierarchy.json`, `hierarchy_docs.json`, `tasks.json`, `repo.json`, `site.json`, `features.json`, `navigation.json`, `taskPages.json`, `graph.json`, `wikilink_map.json`

### Content Naming Conventions

- `01_`, `02_` -- Numbered chapters (nav: 1, 2, ...)
- `a_`, `b_` -- Lettered appendices (nav: A, B, ...)
- `z_` -- Documentation sections (sorted last)
- `??_` -- Work-in-progress (excluded from build)
- `00_index.md` -- Section index page (hidden from nav, uses `layout: layouts/chapter.njk`)

Sort ordering is enforced in both Python (`utils.py`) and Eleventy (`collections.js`): numbered prefixes sort first, then letter prefixes by ASCII value, then `z_` last.

### Component System

Eight types: homework, exercise, prompt, example, exam, project, quiz, embed. Syntax: `:::type{key="value"}` ... `:::`. Only components with `id` attributes (homework, exam, project) aggregate to task pages — the rest are inline-only. Quiz provides interactive multiple-choice. Embed renders responsive iframes. See `CONTENT_SPEC.md` for full reference.

### Primeval Current (Knowledge Graph)

Controlled by `features.graph` in `glintstone.yaml` (default: `true`). Extracts links between pages and provides:

- **Backlinks**: "Referenciado por" section at the bottom of each page listing pages that link to it.
- **Wikilinks**: `[[target]]` and `[[target|display text]]` syntax resolved to internal links. Resolution is case-insensitive: exact stem (`[[03_matematicas]]`), stripped prefix (`[[matematicas]]`), title (`[[Matematicas]]`), or path-qualified (`[[02_avanzado/03_matematicas]]`). Unresolved wikilinks render as wavy-underlined broken links.
- **Graph page**: Interactive d3.js force-directed visualization at `/grafo/`, color-coded by chapter.

Data: `graph.json` (nodes, edges, backlinks) and `wikilink_map.json` (resolution table). Node IDs are namespaced (`{repo}:{path}`) for future multi-repo graph merging.

### Theme System

12 themes in 6 families (dark/light each): EVA-00, EVA-01, EVA-02, EVA-05 Mari, Elden Ring, Raya Lucaria. Theme CSS files use CSS custom properties in `src/eleventy/src/css/themes/`. Creating a new theme = copy a CSS file and change hex values.

### Built-in Documentation

`docs/` contains framework documentation rendered at `/docs/` URLs. Controlled by `features.docs` flag in `glintstone.yaml`. Three sections: student guide (Spanish), professor guide (Spanish), agent guide (English). The agent guide at `docs/03_agentes/` contains detailed technical reference for AI agents.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GLINTSTONE_INPUT` | `clase` | Eleventy input directory (build scripts set to `clase-stage`) |
| `PATH_PREFIX` | `""` | URL path prefix for GitHub Pages |
| `PORT` | `3000` | Dev server port |

## Gotchas

- **Math is client-side only.** The markdown pipeline wraps `$...$` and `$$...$$` in spans/divs; KaTeX renders them in the browser. No server-side math dependency.
- **Date filters hardcode America/Mexico_City timezone** (ITAM-specific).
- **Docker mounts are read-only.** All content volumes use `:ro`. The staging directory pattern exists specifically to work around this.
- **`features.json` is mutated during build** — `anuncios: true` is set dynamically if `clase/anuncios.md` exists.
- **Service worker and manifest.json are generated during build**, not version-controlled.
