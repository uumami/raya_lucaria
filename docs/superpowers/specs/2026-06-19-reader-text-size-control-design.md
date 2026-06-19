# Reader Text Size Control Design

## Goal

Add a static, local reader text-size control to the top command bar so students can increase reading comfort without changing course content, course skin identity, references, math rendering, or learning state.

## Context

The old `main` branch had a font-size toggle with `normal`, `large`, and `x-large` states. The reset branch already adapted the useful OpenDyslexic control through local static accessibility resources. It does not yet provide a text-size comfort control. Course and section skins are source-authored visual identity, so this feature must not become a browser-side skin or theme resolver.

## Requirements

- Add a command-bar button for text size next to the existing OpenDyslexic control.
- Cycle through `normal`, `large`, and `x-large`.
- Store only a local reader comfort preference in `localStorage`.
- Apply the preference to the document root with a data attribute.
- Use generated local CSS and JavaScript under `_raya/render/accessibility/`.
- Avoid external fonts, CDN requests, fetch/XHR, accounts, progress state, analytics, adaptive behavior, browser-side MathJax, and browser-side skin resolution.
- Preserve course/section `data-raya-skin` as the source-selected visual identity.
- Keep controls keyboard reachable and expose current state through accessible labels and `aria-pressed`.
- Cover the behavior with contract and browser tests.
- Update foundation and EN/ES role docs.

## Design

Extend `packages/static/src/raya_static/accessibility.py`, the existing local accessibility resource generator. The same generated CSS file will define text-size scale attributes:

```css
:root[data-raya-text-size="large"] {
  --raya-reader-text-scale: 1.125;
}

:root[data-raya-text-size="x-large"] {
  --raya-reader-text-scale: 1.25;
}
```

The renderer CSS will multiply article and learning rail text by `--raya-reader-text-scale` while keeping command-bar controls stable. The default scale is `1`, so courses without a stored preference look unchanged.

The generated accessibility script will own two independent local preferences:

- `raya:open-dyslexic`, already current behavior.
- `raya:text-size`, new behavior with values `normal`, `large`, and `x-large`.

The command bar will add:

```html
<button class="raya-command raya-command-size raya-text-size-toggle" type="button" aria-label="Text size: normal" aria-pressed="false">
  <span class="raya-command-label">Text size</span>
</button>
```

Clicking cycles states and updates `data-raya-text-size`, `aria-label`, `aria-pressed`, and the stored preference. Invalid stored values fall back to `normal`.

## Testing

Contract tests will assert the command button, generated CSS variables, generated JavaScript storage key, and absence of browser-side skin/theme resolver behavior.

Browser tests will load the render fixture, record article font size, click the size control through `normal -> large -> x-large -> normal`, verify the root data attribute and computed font sizes change, reload to verify persistence for non-normal states, and verify the URL does not change.

## Documentation

Foundation and role docs will describe text size as a local static reader comfort control. Students can use it without changing course meaning. Professors and contributors should treat skins as source-authored visual identity and text size as reader-local display preference. Agents should verify local generated resources, data attributes, and browser behavior without treating the preference as course authority.
