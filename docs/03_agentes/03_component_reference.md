---
title: "Component Reference"
summary: "Registry, parsing, HTML output, and adding new types"
---

# Component Reference

## Component Registry

The REGISTRY object in `src/eleventy/lib/components.js` defines all component types:

```javascript
const REGISTRY = {
  homework: { label: 'TAREA', colorVar: '--color-homework', ... },
  exercise: { label: 'EJERCICIO', colorVar: '--color-exercise', ... },
  prompt:   { label: 'PROMPT', colorVar: '--color-prompt', ... },
  example:  { label: 'EJEMPLO', colorVar: '--color-example', ... },
  exam:     { label: 'EXAMEN', colorVar: '--color-exam', ... },
  project:  { label: 'PROYECTO', colorVar: '--color-project', ... },
  quiz:     { label: 'QUIZ', colorVar: '--color-quiz', ... },
  embed:    { label: 'RECURSO', colorVar: '--color-embed', ... },
};
```

Each entry maps a type name to its display label, CSS color class, and SVG icon.

## Parsing Flow

1. `markdown-it-container` detects `:::type{...}` fences
2. The opening fence is parsed for attributes using `/(\w+)="([^"]*)"/g`
3. The component's content (between `:::` markers) is rendered as Markdown
4. The HTML output wraps content in a styled container with header and body

## HTML Output Structure

```html
<div class="component component--TYPE" id="COMPONENT_ID">
  <div class="component__header">
    <span class="component__icon">SVG</span>
    <span class="component__label">Label</span>
    <span class="component__title">Title</span>
    <span class="component__badges">due date, points, etc.</span>
  </div>
  <div class="component__body">
    <!-- rendered markdown content -->
  </div>
</div>
```

## Task Aggregation

The `aggregate_all_tasks()` function in `src/preprocessing/aggregate_tasks.py`:

1. Scans all Markdown files for component fences
2. Extracts components with `id` attributes (homework, exam, project)
3. Groups them by type
4. Writes `tasks.json` with structure: `{ "homework": [...], "exams": [...], "projects": [...] }`

The build script (`build.sh`) generates Nunjucks task page templates from `taskPages.json`, which render the aggregated task lists.

## Special Component Types

### Quiz

The `quiz` component transforms checkbox lists into interactive multiple-choice. The JS module `src/eleventy/src/js/quiz.js` handles client-side behavior: it finds `.component--quiz` containers, turns checkbox items into clickable options, and reveals correct/incorrect feedback on click.

### Embed

The `embed` component renders a responsive 16:9 iframe. The `renderComponent` function in `components.js` has a special branch for `type === 'embed'` that outputs an `<iframe>` inside a `.embed__wrapper` div instead of the standard body opening.

## Adding a New Component Type

To add a new component type:

1. **`src/eleventy/lib/components.js`** -- Add entry to REGISTRY:
   ```javascript
   quiz: { label: 'Quiz', color: 'quiz', icon: '<svg>...</svg>' },
   ```

2. **`src/eleventy/src/css/main.css`** -- Add color classes for the new type

3. **`src/preprocessing/aggregate_tasks.py`** -- If the new type should aggregate to a task page, add it to the aggregation logic

4. **`src/preprocessing/schemas/config.py`** -- If it needs a task page, add a default TaskPageConfig entry

5. **`CONTENT_SPEC.md`** -- Document the new component syntax and attributes
