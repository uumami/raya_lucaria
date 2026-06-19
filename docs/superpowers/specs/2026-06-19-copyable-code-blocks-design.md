# Copyable Code Blocks Design

The old `main` branch had a client-side copy button for every `pre code` block. The reset renderer should keep that student-friendly affordance, but make it native to the current static renderer instead of importing the old Eleventy behavior.

## Goals

- Let readers copy fenced code examples without selecting text manually.
- Keep the control visible, keyboard reachable, and local to each rendered code block.
- Preserve code text exactly as rendered in the `<code>` element.
- Avoid browser storage, fetch/XHR, external scripts, CDN resources, or dynamic study state.
- Keep the feature useful on local preview and deployed static sites.

## Rendering

The Markdown renderer already emits fenced code as:

```html
<div class="raya-code-block" data-language="python">
  ...
  <pre class="highlight"><code class="language-python">...</code></pre>
</div>
```

This slice changes that wrapper to include a compact code header:

```html
<div class="raya-code-block" data-language="python">
  <div class="raya-code-header">
    <div class="raya-code-label">python</div>
    <button class="raya-code-copy" type="button" data-raya-copy-code aria-label="Copy code block">Copy</button>
  </div>
  <pre class="highlight"><code class="language-python">...</code></pre>
</div>
```

Blocks without a language still receive the same copy button, with the header aligned to the end. The button is normal HTML so it is visible before JavaScript runs and remains harmless if the shell script is unavailable.

## Shell Behavior

`shell.js` attaches click handlers to `[data-raya-copy-code]` buttons. On click, it finds the nearest `.raya-code-block`, reads the first nested `pre code`, and attempts to copy its `textContent`.

The preferred path uses `navigator.clipboard.writeText`. A local fallback uses a temporary readonly `<textarea>` and `document.execCommand("copy")` for static contexts where the Clipboard API is unavailable. The temporary element is removed immediately.

Button labels are transient:

- default: `Copy`
- success: `Copied`
- failure: `Copy failed`

The label resets after a short timeout. The behavior stores no state.

## Styling

`rich.css` gets a small code header treatment:

- header uses semantic skin surface/border tokens;
- language label keeps monospace styling;
- copy button uses the current accent tokens and has a visible focus ring;
- code blocks remain horizontally scrollable and full-width in the article.

## Documentation

The learning renderer contract should list copyable code blocks as a current static reader control. Role docs should mention that rendered fenced code can be copied locally, while source code and notebooks remain static support files unless explicit execution commands are used.

## Tests

Contract tests should prove:

- rendered fenced code includes `data-raya-copy-code`;
- unknown language code remains escaped and copyable;
- `shell.js` includes copy behavior;
- `shell.js` still has no storage, fetch/XHR, or external dependency behavior.

Browser tests should prove:

- a rendered code-copy button is keyboard reachable;
- clicking it calls the Clipboard API with the exact code text;
- the button label changes to `Copied`;
- the page remains on the same URL after copying.
