# Spoiler-Safe Static Environments Design

## Goal

Make optional learning aids such as hints, solutions, and answers reveal-on-demand in rendered static course pages while keeping proofs expanded, static, accessible, and free of browser-side rendering dependencies.

## Context

The reset renderer already supports authored fenced environments for `proof`, `solution`, `hint`, and `answer`. Proofs are part of the reasoning flow and render as expanded proof blocks. Hints, solutions, and answers currently render expanded in the same page flow, which can spoil problem-solving and make pages longer than needed.

Old `main` had interactive quiz reveal behavior, but its scoring/progress model is out of scope for the reset. The useful principle is controlled reveal: learners should decide when to inspect optional support.

## Requirements

- Render `hint`, `solution`, and `answer` environments as native HTML disclosures using `<details>` and `<summary>`.
- Keep `proof` environments expanded as proof blocks.
- Default optional disclosures to closed.
- Preserve existing generated IDs, reference text, title text, and body content.
- Avoid JavaScript, local storage, progress state, scoring, analytics, remote requests, CDN assets, and browser-side MathJax conversion.
- Preserve static read path parity between preview and deployment.
- Keep the behavior accessible with keyboard-operable native controls and visible focus styling.
- Document the authoring and reader behavior in foundation guidance and EN/ES role guides.
- Add contract and browser tests that prove disclosure markup, default closed state, reveal behavior, proof behavior, and no external/browser-side renderer dependency.

## Design

`packages/static/src/raya_static/rendering.py` remains the rendering boundary. `_render_static_environment_html` will continue to branch on environment kind. For `proof`, it will keep emitting the existing `<section class="raya-proof">` structure. For `hint`, `solution`, and `answer`, it will emit:

```html
<details id="raya-static-environment-..." class="raya-static-environment raya-static-environment--hint">
  <summary class="raya-static-environment-heading">
    <span class="raya-static-environment-reference">Hint for Activity 4.1</span>
    <span class="raya-static-environment-title">...</span>
  </summary>
  <div class="raya-static-environment-body">...</div>
</details>
```

The summary uses the same heading class so existing styling remains close, with CSS adjusted for summary semantics, pointer affordance, focus visibility, and open-state spacing. Because native `<details>` handles keyboard and state locally, the renderer does not need a script bundle.

## Testing

Contract tests will assert that:

- Hints, solutions, and answers render as `<details>`.
- They are closed by default.
- Their body content and stable IDs remain present in the HTML.
- Proofs remain expanded proof sections.

Browser tests will assert that a fixture hint starts closed, its body is not laid out, clicking the summary opens it, and the URL remains unchanged. Existing render-debug checks continue to inspect static environments across desktop and mobile.

## Documentation

Foundation and role docs will describe optional learning aids as spoiler-safe static disclosures. Professors author them with the same fenced environment syntax. Students can open them when they need support. Contributors and agents must preserve native disclosures and avoid adding scoring, storage, or browser-renderer dependencies.
