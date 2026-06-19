# Copyable Code Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reset-native copy buttons to rendered fenced code blocks using static HTML and local shell JavaScript.

**Architecture:** `packages/static/src/raya_static/rendering.py` renders code-copy buttons beside fenced code. `packages/static/src/raya_static/shell.py` wires local clipboard behavior without storage, fetch/XHR, or external scripts. Existing static/e2e tests verify markup, shell constraints, and browser behavior.

**Tech Stack:** Python static renderer, generated local JavaScript, pytest contract tests, Playwright e2e tests.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add contract assertions**

In `test_render_fixture_builds_rich_static_pages`, assert:

```python
assert 'class="raya-code-copy"' in html
assert "data-raya-copy-code" in html
assert 'aria-label="Copy code block"' in html
assert html.index('data-language="python"') < html.index("data-raya-copy-code")
assert '&lt;script&gt;not_executed()&lt;/script&gt;' in html
```

In `test_static_build_writes_local_shell_resource`, assert:

```python
assert "data-raya-copy-code" in script_text
assert "navigator.clipboard.writeText" in script_text
assert "execCommand(\"copy\")" in script_text
assert "localStorage" not in script_text
assert "sessionStorage" not in script_text
assert "fetch(" not in script_text
assert "XMLHttpRequest" not in script_text
```

- [x] **Step 2: Add browser clipboard test**

Add `test_render_fixture_code_copy_button_copies_code_text` to `tests/e2e/test_preview_static_read_path.py`. Build a render fixture preview, open `/index.html`, grant clipboard permission when supported, stub `navigator.clipboard.writeText` to capture text, click the first `[data-raya-copy-code]` button, and assert:

```python
copied = page.evaluate("() => window.__rayaCopiedText")
assert "def" in copied or "not_executed" in copied
assert page.locator("[data-raya-copy-code]").first.inner_text() == "Copied"
assert page.url.endswith("/index.html")
```

Use Playwright locator syntax that works with the current test style.

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_code_copy_button_copies_code_text
```

Expected: fail because rendered code-copy markup and shell behavior do not exist yet.

### Task 2: Render Code Copy Controls

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Render a code header**

In `_render_fence(...)`, wrap the language label and copy button in:

```python
header = (
    '<div class="raya-code-header">'
    f"{label}"
    '<button class="raya-code-copy" type="button" '
    'data-raya-copy-code aria-label="Copy code block">Copy</button>'
    "</div>"
)
```

Return:

```python
return (
    f'<div class="raya-code-block"{data_language}>'
    f"{header}"
    f'<pre class="highlight"><code{code_class}>{code_html}</code></pre>'
    "</div>\n"
)
```

- [x] **Step 2: Style the header and button**

In `RICH_CSS`, update the code block styles so `.raya-code-header` is a flex row, `.raya-code-label` remains monospace, `.raya-code-copy` uses accent tokens, and `.raya-code-copy:focus-visible` has a visible outline.

- [x] **Step 3: Run contract markup test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages
```

Expected: markup assertions pass; shell assertions still fail until Task 3.

### Task 3: Add Local Clipboard Behavior

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Add copy helpers**

Add helpers inside the shell closure:

```javascript
function resetCopyButton(button) {
  window.setTimeout(() => {
    button.textContent = "Copy";
    button.removeAttribute("data-raya-copy-state");
  }, 1600);
}

function copyWithFallback(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "-1000px";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    return document.execCommand("copy");
  } finally {
    textarea.remove();
  }
}

async function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  return copyWithFallback(text);
}

function initializeCodeCopyControls() {
  document.querySelectorAll("[data-raya-copy-code]").forEach((button) => {
    button.addEventListener("click", async () => {
      const block = button.closest(".raya-code-block");
      const code = block ? block.querySelector("pre code") : null;
      if (!code) {
        return;
      }
      try {
        const copied = await copyText(code.textContent || "");
        button.textContent = copied ? "Copied" : "Copy failed";
        button.dataset.rayaCopyState = copied ? "copied" : "failed";
      } catch {
        button.textContent = "Copy failed";
        button.dataset.rayaCopyState = "failed";
      }
      resetCopyButton(button);
    });
  });
}
```

Call `initializeCodeCopyControls()` before setting `root.dataset.rayaShellReady = "true"`.

- [x] **Step 2: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_code_copy_button_copies_code_text
```

Expected: focused tests pass.

### Task 4: Docs, Review, Verification, Commit

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- All modified implementation/test files.

- [x] **Step 1: Update docs**

Add copyable code blocks to reader-controls language in the foundation contract and add a short student-facing note in English and Spanish role docs.

- [x] **Step 2: Request independent review**

Ask a reviewer to inspect the uncommitted diff for reset compatibility: static rendering, clipboard safety, exact copied text, no storage/fetch/external requests, accessibility, and tests.

- [x] **Step 3: Run full relevant verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

- [x] **Step 4: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-19-copyable-code-blocks-design.md \
  docs/superpowers/plans/2026-06-19-copyable-code-blocks.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md \
  docs/guides/es/estudiantes/index.md \
  packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add copyable code blocks"
```
