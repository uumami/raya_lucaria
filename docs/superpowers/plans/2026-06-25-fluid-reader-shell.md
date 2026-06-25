# Fluid Reader Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the static reader shell feel smoother, wider, and more intentional on desktop while preserving current no-backend, no-fetch, no-storage, and accessibility guarantees.

**Architecture:** Keep the current generated shell markup and `data-raya-*` state model. Improve behavior through focused e2e assertions, CSS token polish in `rendering.py`, and small local script helpers in `shell.py` only where layout state needs synchronization.

**Tech Stack:** Python static renderer, generated HTML/CSS/JS, Playwright e2e tests, current render-debug gate.

---

## File Map

- `tests/e2e/test_preview_static_read_path.py`: add focused browser assertions for shell continuity, reduced motion, compact tabs, rail-panel accessibility, and no overflow.
- `packages/static/src/raya_static/rendering.py`: refine shell/grid transitions, command grouping, compact rail/tab visuals, rail disclosure controls, and reduced-motion CSS.
- `packages/static/src/raya_static/shell.py`: keep existing volatile state; add only tiny helpers if repeated collapse/expand needs stable re-orientation or explicit ready-state timing.
- `docs/foundation/20_learning_renderer_contract.md`: document coordinated reduced-motion-aware shell transitions and intentional compact map/context tabs.
- `docs/guides/en/students/index.md`, `docs/guides/es/estudiantes/index.md`: describe shell controls as reading comfort tools.
- `docs/guides/en/agents/index.md`, `docs/guides/es/agentes/index.md`: document verification expectations for accessibility, no storage, and reduced motion.

## Task 1: Browser Expectations for Fluid Shell

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing desktop shell assertions**

In `test_render_fixture_learning_shell_layout_and_accessibility`, inside the `if viewport["width"] >= 1280:` branch after `metrics = page.evaluate(...)`, extend the evaluated object:

```python
shell_state = page.evaluate(
    """() => {
      const root = document.documentElement;
      const shell = document.querySelector('.raya-learning-shell');
      const map = document.querySelector('#raya-course-map');
      const article = document.querySelector('#raya-article');
      const rail = document.querySelector('#raya-learning-rail');
      const commandBar = document.querySelector('.raya-top-command-bar');
      return {
        ready: root.dataset.rayaShellReady,
        shellTransition: getComputedStyle(shell).transition,
        mapTransition: getComputedStyle(map).transition,
        railTransition: getComputedStyle(rail).transition,
        articleMaxWidth: getComputedStyle(article).maxWidth,
        commandGap: getComputedStyle(commandBar).gap,
      };
    }"""
)
assert shell_state["ready"] == "true"
assert "grid-template-columns" in shell_state["shellTransition"]
assert "transform" in shell_state["mapTransition"]
assert "transform" in shell_state["railTransition"]
assert shell_state["articleMaxWidth"] != "none"
assert shell_state["commandGap"] != "normal"
```

- [ ] **Step 2: Add failing compact-tab assertions**

After the existing `collapsed = page.evaluate(...)`, extend the object:

```javascript
mapButtonText: document
  .querySelector('#raya-course-map .raya-course-map-toggle')
  ?.textContent
  ?.trim(),
railExpandText: document
  .querySelector('.raya-learning-rail-expand')
  ?.textContent
  ?.trim(),
mapButtonWritingMode: getComputedStyle(
  document.querySelector('#raya-course-map .raya-course-map-toggle')
).writingMode,
railButtonWritingMode: getComputedStyle(
  document.querySelector('.raya-learning-rail-expand')
).writingMode,
articleLeft: document.querySelector('#raya-article').getBoundingClientRect().left,
articleRight: document.querySelector('#raya-article').getBoundingClientRect().right,
viewportWidth: window.innerWidth,
```

Then assert:

```python
assert collapsed["mapButtonText"] in {"Expand map", "Map"}
assert collapsed["railExpandText"] == "Context"
assert collapsed["mapButtonWritingMode"] == "horizontal-tb"
assert collapsed["railButtonWritingMode"] == "horizontal-tb"
assert collapsed["articleLeft"] >= 0
assert collapsed["articleRight"] <= collapsed["viewportWidth"]
```

- [ ] **Step 3: Add reduced-motion assertion**

Create a new test near the shell layout test:

```python
def test_render_fixture_shell_respects_reduced_motion(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.emulate_media(reduced_motion="reduce")
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    state = page.evaluate(
                        """() => ({
                          shellTransition: getComputedStyle(
                            document.querySelector('.raya-learning-shell')
                          ).transitionDuration,
                          mapTransition: getComputedStyle(
                            document.querySelector('#raya-course-map')
                          ).transitionDuration,
                          railPanelTransition: getComputedStyle(
                            document.querySelector('.raya-rail-panel-body')
                          ).transitionDuration,
                        })"""
                    )
                    assert state["shellTransition"] in {"0s", "0s, 0s", "0s, 0s, 0s"}
                    assert state["mapTransition"] in {"0s", "0s, 0s", "0s, 0s, 0s", "0s, 0s, 0s, 0s"}
                    assert state["railPanelTransition"] in {"0s", "0s, 0s", "0s, 0s, 0s"}
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 4: Run tests and confirm RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility tests/e2e/test_preview_static_read_path.py::test_render_fixture_shell_respects_reduced_motion -q
```

Expected: FAIL on at least one new assertion before implementation.

## Task 2: CSS Shell Continuity

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Update ready-state transitions**

Find the existing `html[data-raya-shell-ready="true"] .raya-learning-shell` rule and ensure it includes transform-safe grid transitions:

```css
html[data-raya-shell-ready="true"] .raya-learning-shell {
  transition: grid-template-columns 220ms ease, gap 220ms ease;
}
```

Find the existing `html[data-raya-shell-ready="true"] .raya-course-map` and `.raya-learning-rail` transition rules and make them consistent:

```css
html[data-raya-shell-ready="true"] .raya-course-map,
html[data-raya-shell-ready="true"] .raya-learning-rail {
  transition: border-color 180ms ease, box-shadow 180ms ease, opacity 180ms ease, transform 220ms ease, width 220ms ease;
}
```

- [ ] **Step 2: Improve command bar grouping**

Add or adjust command-bar spacing without changing markup:

```css
.raya-top-command-bar {
  gap: 0.55rem;
}
.raya-command {
  min-height: 2.35rem;
}
```

Do not remove existing focus-visible rules.

- [ ] **Step 3: Improve compact map and context tabs**

Inside the desktop media section for collapsed map/rail, ensure the compact controls stay horizontal and stable:

```css
[data-raya-course-map="collapsed"] #raya-course-map .raya-course-map-toggle,
.raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-toggle,
[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand,
.raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand {
  align-items: center;
  display: inline-flex;
  justify-content: center;
  min-height: 2.75rem;
  writing-mode: horizontal-tb;
}
```

- [ ] **Step 4: Improve rail disclosure affordance**

Update `.raya-rail-toggle` and marker styles so collapsed panels look intentional:

```css
.raya-rail-toggle {
  border-radius: 0.3rem;
  min-height: 2rem;
  padding: 0.2rem 0;
}
.raya-rail-toggle::after {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  display: inline-flex;
  height: 1.35rem;
  justify-content: center;
  min-width: 1.35rem;
}
```

- [ ] **Step 5: Keep reduced motion complete**

Extend the existing reduced-motion block so shell, map, rail, controls, and panel bodies all become transition-free:

```css
@media (prefers-reduced-motion: reduce) {
  html[data-raya-shell-ready="true"] .raya-learning-shell,
  html[data-raya-shell-ready="true"] .raya-course-map,
  html[data-raya-shell-ready="true"] .raya-learning-rail,
  html[data-raya-shell-ready="true"] .raya-course-map-toggle,
  html[data-raya-shell-ready="true"] .raya-learning-rail-expand,
  html[data-raya-shell-ready="true"] .raya-rail-panel-body {
    transition: none;
  }
}
```

- [ ] **Step 6: Run focused tests and confirm GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility tests/e2e/test_preview_static_read_path.py::test_render_fixture_shell_respects_reduced_motion -q
```

Expected: PASS.

## Task 3: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update foundation**

In the shell paragraph of `docs/foundation/20_learning_renderer_contract.md`, add:

```markdown
The shell may use coordinated, reduced-motion-aware visual transitions for explicit map, context, and reader-focus state changes so the reader perceives one continuous workspace. These transitions are display state only and must not persist shell state, infer progress, or hide accessible content outside the documented collapsed desktop states.
```

- [ ] **Step 2: Update student docs**

Add one paragraph to English and Spanish student docs near existing shell guidance:

```markdown
The Map, Focus reading, and Context controls are reading-comfort tools. They can widen the article or restore surrounding context without saving a personal progress state.
```

Spanish:

```markdown
Los controles Map, Focus reading y Context son herramientas de comodidad de lectura. Pueden ampliar el articulo o restaurar el contexto alrededor sin guardar un estado personal de avance.
```

- [ ] **Step 3: Update agent docs**

Add one paragraph to English and Spanish agent docs near renderer verification guidance:

```markdown
When shell comfort controls change, verify that map and context state remains volatile, reduced-motion disables nonessential transitions, collapsed desktop regions are removed from keyboard and assistive navigation as specified, and tablet/mobile layouts keep required context accessible.
```

Spanish:

```markdown
Cuando cambien controles de comodidad del shell, verifica que el estado de Map y Context siga siendo volatil, que reduced-motion desactive transiciones no esenciales, que las regiones colapsadas de escritorio salgan de la navegacion por teclado y asistiva como se especifica, y que tablet/mobile mantengan accesible el contexto requerido.
```

## Task 4: Verification, Review, Commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run focused checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility tests/e2e/test_preview_static_read_path.py::test_render_fixture_shell_respects_reduced_motion -q
./scripts/check-render-debug.sh
```

Expected: focused tests pass; render-debug reports `passed`.

- [ ] **Step 2: Request independent review**

Ask three independent reviewers:

- one for shell CSS/accessibility behavior;
- one for static/no-storage/no-external-resource boundaries;
- one for docs/foundation consistency.

- [ ] **Step 3: Run canonical gates**

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both scripts end with `passed`.

- [ ] **Step 4: Commit and push**

```bash
git add tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
git commit -m "Polish fluid reader shell"
git push origin new_rayalucaria
```

## Self-Review

- Spec coverage: tasks cover fluid shell transitions, compact tabs, rail disclosure affordance, reduced motion, no-storage boundaries through existing tests, docs, review, and canonical gates.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type and selector consistency: all selectors already exist in current generated HTML/CSS except the new reduced-motion test assertions, which use current shell selectors.
