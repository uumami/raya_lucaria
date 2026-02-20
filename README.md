# Raya Lucaria

Integrated learning platform for ITAM course materials.

## Glintstone (Content Engine)

The **Glintstone** layer is the content engine — a static site generator that transforms Markdown into navigable course websites. It uses a three-stage pipeline:

1. **Python preprocessing** -- extracts metadata, builds hierarchy, aggregates tasks
2. **Eleventy (11ty)** -- generates HTML from Markdown + Nunjucks templates
3. **Tailwind CSS + esbuild** -- styles and bundles frontend assets

### Quick Start

Add Glintstone as a submodule in your course repo:

```bash
git submodule add <repo-url> glintstone
```

Create `glintstone.yaml` at your course repo root:

```yaml
site:
  name: "My Course - ITAM"
  description: "Spring 2026"
  language: "es"
```

Build:

```bash
docker compose -f glintstone/docker/docker-compose.yaml up build
```

Dev server:

```bash
docker compose -f glintstone/docker/docker-compose.yaml up dev
```

### Features

- 8 component types (homework, exercise, prompt, example, exam, project, quiz, embed)
- 12 themes (6 families x dark/light)
- KaTeX math rendering
- Mermaid diagrams
- Pagefind search
- Keyboard navigation
- OpenDyslexic font support
- Service worker for offline access

See [CLAUDE.md](CLAUDE.md) for architecture details and [CONTENT_SPEC.md](CONTENT_SPEC.md) for the content authoring reference.

## History

This project was previously called **sellen** (after Sorceress Sellen from Elden Ring). The content engine was renamed to Glintstone as part of the broader Raya Lucaria platform vision.
