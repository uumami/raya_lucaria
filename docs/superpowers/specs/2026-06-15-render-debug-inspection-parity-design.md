# Render Debug Inspection Parity Design

## Purpose

The previous renderer loop made `scripts/check-render-debug.sh` a focused gate for screenshots, raw TeX leakage, horizontal overflow, external renderer requests, and browser-side MathJax runtime dependencies. The next quality pillar makes those failures easier to inspect and extends the same guarantees to a copied static deployment shape.

This loop adds a static inspection report for render-debug artifacts and a copied-site parity check. The goal is not a new public workflow; it is a stronger agent and maintainer debugging surface around the existing `raya preview --render-debug` and `scripts/check-render-debug.sh` path.

## Scope

In scope:

- Generate a static render-debug report beside existing `summary.json` and screenshots.
- Generate a machine-readable report JSON with normalized checks and diagnostics.
- Make failure output point directly to the report path.
- Extend the focused gate to inspect a copied external `artifact/site/` directory.
- Verify local preview and copied static site keep the same deployment-neutral assumptions:
  - no browser-side MathJax conversion,
  - no external renderer or CDN requests,
  - local MathJax CSS and fonts remain under `_raya/render/math/`,
  - screenshots and summary entries stay tied to the current debug directory,
  - raw visible TeX and horizontal overflow remain failures.
- Add focused tests before implementation and include the gate in host/Docker verification.

Out of scope:

- A new public CLI command.
- Expanding broad math authoring examples beyond what is needed to explain this debug workflow.
- Introducing browser-side JavaScript into rendered course pages.
- External services, CDN renderer assets, or runtime MathJax conversion in the browser.
- Changing the canonical course source or artifact contracts beyond documenting this debug report as a generated inspection artifact.

## Architecture

The existing `raya preview --render-debug <dir>` remains the capture mechanism. `packages/cli/src/raya_cli/render_debug.py` already captures four fixture screenshots and writes `summary.json`; this loop will extend that same boundary with a small report writer.

The report writer will create:

- `summary.json`: existing capture data, preserved for compatibility.
- `report.json`: normalized status for each capture, generated from `summary.json`, screenshot files, HTML inspection, and copied-site parity checks.
- `index.html`: a static human/agent report with screenshot links, per-page viewport rows, raw TeX markers, external request lists, overflow values, renderer dependency diagnostics, copied-site parity status, and next actions.

`scripts/check-render-debug.sh` will remain the focused gate. Its embedded inspector may be refactored into a small Python helper if that keeps the script understandable, but the user-facing command stays the same.

## Data Flow

1. `scripts/check-render-debug.sh` builds and previews `examples/courses/render-fixture` through `raya preview --render-debug <debug_dir>`.
2. The preview workflow writes screenshots and `summary.json`.
3. The gate inspects the generated local `artifact/site/` HTML for blocked renderer dependencies and expected local MathJax resources.
4. The gate copies `artifact/site/` into a temporary external directory and repeats the static inspection against that copied site.
5. The report writer records the combined result in `report.json` and `index.html`.
6. On failure, the gate prints the failed diagnostics and the report path so humans and agents can inspect the screenshots and normalized status without re-running the capture.

## Report Shape

`report.json` should be intentionally boring and stable:

```json
{
  "ok": false,
  "site_dir": ".../artifact/site",
  "copied_site_dir": ".../copied-site",
  "summary_path": ".../debug/summary.json",
  "html_report_path": ".../debug/index.html",
  "checks": [
    {
      "id": "capture:index:desktop",
      "ok": true,
      "page": "index",
      "viewport": "desktop",
      "screenshot": "desktop-index.png",
      "diagnostics": []
    }
  ],
  "diagnostics": [
    {
      "severity": "error",
      "message": "browser-side renderer dependency 'tex-chtml' in site/index.html",
      "path": ".../site/index.html",
      "next_action": "Remove browser-side MathJax runtime; math must be rendered at build time."
    }
  ]
}
```

The exact schema can remain internal to the gate for now, but tests should lock the fields agents need: `ok`, `checks`, `diagnostics`, screenshot filenames, local/copy site paths, and HTML report path.

`index.html` should be a plain static page, not an app. It should link local screenshots by relative paths, summarize pass/fail status, and include enough context for a coding agent to locate the failing page, viewport, and file.

## Copied Static Parity

The copied parity check proves that the generated static read path does not depend on being served from the course checkout. The gate will copy `artifact/site/` to a temp directory outside the course fixture and inspect that copy.

This does not need to duplicate the full browser screenshot capture. The browser-driven capture already validates rendering against the preview server. The copied-site parity check should focus on static deploy invariants:

- copied HTML files exist and remain deployment-neutral,
- `_raya/render/math/mathjax.css` exists when math is present,
- `_raya/render/math/fonts/` contains local font resources when math is present,
- HTML does not reference browser-side MathJax JavaScript,
- HTML does not reference known renderer CDNs,
- copied pages do not contain raw visible TeX markers in ordinary body text when inspected from generated HTML.

If implementation finds a cheap and reliable way to serve the copied site with the existing static-read-path helper, that can be included, but it is not required for the first report loop.

## Error Handling

The gate should keep collecting diagnostics after the first failure so the report is useful. A missing `summary.json`, malformed capture record, missing screenshot, browser-side MathJax script, external renderer URL, copied-site missing asset, or overflow failure should all appear in `report.json` and `index.html`.

If report generation itself fails, the shell script should fail with a direct message and preserve the debug directory when `RAYA_RENDER_DEBUG_KEEP=1` or `RAYA_RENDER_DEBUG_OUTPUT_DIR` is set. Default temp cleanup may continue for successful runs.

## Testing Strategy

Use TDD before implementation.

Focused tests should cover:

- positive `scripts/check-render-debug.sh` run writes `summary.json`, screenshots, `report.json`, and `index.html`;
- the HTML report links screenshots by relative path;
- failures still write `report.json` and `index.html`;
- missing screenshot appears in diagnostics and the report path is printed;
- local and copied static site inspections both reject browser-side MathJax runtime scripts;
- copied site inspection rejects missing local MathJax CSS/fonts when math is present;
- command guidance mentions the focused report/parity gate where relevant.

Verification commands for the loop:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_renderer_dependencies.py
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

## Documentation

Update role docs only where the debugging workflow is directly referenced:

- contributors and collaborators: report path, copied static parity, and focused gate usage;
- agents: how to inspect `debug/index.html`, `report.json`, screenshots, and diagnostics;
- professors/students only if needed to explain that this is generated debugging output, not course source truth.

Keep English and Spanish role docs separate. Preserve English technical identifiers for commands, paths, report field names, and artifact paths.

## Acceptance Criteria

- `scripts/check-render-debug.sh` creates an inspectable static report for render fixture debug output.
- The focused gate checks both the local preview artifact site and a copied external static site.
- Gate failures print actionable diagnostics and the report path.
- The report is static and self-contained within the debug output directory, except for links to generated/copy-site paths represented as text.
- No browser-side MathJax runtime or external renderer/CDN requests are introduced.
- Host and Docker verification paths continue to pass.
