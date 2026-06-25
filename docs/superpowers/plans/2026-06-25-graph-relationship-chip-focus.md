# Graph Relationship Chip Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make graph relationship chips into transient local focus controls for the selected page's relationship walkthrough.

**Architecture:** The graph script already computes relationship chip counts and walkthrough cards from embedded graph edges. This change keeps that computation local, stores the active chip key in a module variable, renders chips as native buttons, and filters existing walkthrough cards by their `data-raya-graph-relationship-kind` and `data-raya-graph-relationship-direction` attributes.

**Tech Stack:** Python static renderer, embedded local JavaScript string, CSS custom properties, pytest, Playwright.

---

### Task 1: Relationship Chip Focus RED Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend graph relationship assertions**

In `test_preview_serves_local_visual_graph_surface`, after the existing relationship chip text assertions, add checks that chips are native buttons and that activating a chip filters walkthrough cards:

```python
content_out_chip = relationship_chips.locator(
    '[data-raya-graph-relationship-kind="content"]'
    '[data-raya-graph-relationship-direction="out"]'
)
assert content_out_chip.evaluate("node => node.tagName") == "BUTTON"
assert content_out_chip.get_attribute("aria-pressed") == "false"
initial_url = page.url
content_out_chip.click()
assert content_out_chip.get_attribute("aria-pressed") == "true"
assert page.url == initial_url
assert page.evaluate(
    "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
) == [[], []]
visible_cards = relationship_walkthrough.locator(
    "[data-raya-graph-relationship-walkthrough-card]"
).evaluate_all(
    """cards => cards
      .filter((card) => !card.hidden)
      .map((card) => [
        card.getAttribute('data-raya-graph-relationship-kind'),
        card.getAttribute('data-raya-graph-relationship-direction'),
        card.textContent,
      ])"""
)
assert len(visible_cards) == 1
assert visible_cards[0][0:2] == ["content", "out"]
assert "Content from this page" in visible_cards[0][2]
assert "Showing Content out relationships." in relationship_walkthrough.inner_text()
```

- [x] **Step 2: Add clear/switch assertions**

Continue the same test with:

```python
content_in_chip = relationship_chips.locator(
    '[data-raya-graph-relationship-kind="content"]'
    '[data-raya-graph-relationship-direction="in"]'
)
content_in_chip.click()
assert content_out_chip.get_attribute("aria-pressed") == "false"
assert content_in_chip.get_attribute("aria-pressed") == "true"
visible_cards = relationship_walkthrough.locator(
    "[data-raya-graph-relationship-walkthrough-card]"
).evaluate_all(
    """cards => cards
      .filter((card) => !card.hidden)
      .map((card) => [
        card.getAttribute('data-raya-graph-relationship-kind'),
        card.getAttribute('data-raya-graph-relationship-direction'),
      ])"""
)
assert visible_cards == [["content", "in"]]
content_in_chip.click()
assert content_in_chip.get_attribute("aria-pressed") == "false"
assert walkthrough_cards.count() == 4
assert relationship_walkthrough.locator(
    "[data-raya-graph-relationship-walkthrough-card]"
).evaluate_all("cards => cards.filter((card) => !card.hidden).length") == 4
```

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: fail because relationship chips are still `SPAN` elements and have no `aria-pressed` state.

### Task 2: Implement Graph Chip Focus

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add graph state and status placeholder**

In `builder.py`, inside the relationship walkthrough section before the walkthrough list, add:

```html
<p class="raya-graph-relationship-focus-status" data-raya-graph-relationship-focus-status aria-live="polite"></p>
```

In `graph.py`, add:

```javascript
const relationshipFocusStatus = document.querySelector(
  "[data-raya-graph-relationship-focus-status]"
);
let activeRelationshipFocus = "";
```

- [x] **Step 2: Add focus helpers**

In `graph.py`, add helpers near the relationship chip functions:

```javascript
function relationshipFocusKey(kind, direction) {
  return `${edgeKind({ kind })}:${direction}`;
}

function relationshipFocusLabel(kind, direction) {
  return relationshipChipLabel(kind, direction);
}

function clearRelationshipFocus() {
  activeRelationshipFocus = "";
  syncRelationshipFocusDom();
}

function setRelationshipFocus(kind, direction) {
  const nextKey = relationshipFocusKey(kind, direction);
  activeRelationshipFocus = activeRelationshipFocus === nextKey ? "" : nextKey;
  syncRelationshipFocusDom();
}

function syncRelationshipFocusDom() {
  if (detailRelationshipChipList) {
    detailRelationshipChipList
      .querySelectorAll("[data-raya-graph-relationship-chip]")
      .forEach((chip) => {
        const key = relationshipFocusKey(
          chip.getAttribute("data-raya-graph-relationship-kind") || "",
          chip.getAttribute("data-raya-graph-relationship-direction") || ""
        );
        chip.setAttribute("aria-pressed", key === activeRelationshipFocus ? "true" : "false");
      });
  }
  if (relationshipWalkthroughList) {
    relationshipWalkthroughList
      .querySelectorAll("[data-raya-graph-relationship-walkthrough-card]")
      .forEach((card) => {
        const key = relationshipFocusKey(
          card.getAttribute("data-raya-graph-relationship-kind") || "",
          card.getAttribute("data-raya-graph-relationship-direction") || ""
        );
        card.hidden = Boolean(activeRelationshipFocus && key !== activeRelationshipFocus);
      });
  }
  if (relationshipFocusStatus) {
    if (!activeRelationshipFocus) {
      relationshipFocusStatus.textContent = "";
    } else {
      const [kind, direction] = activeRelationshipFocus.split(":");
      relationshipFocusStatus.textContent = `Showing ${relationshipFocusLabel(kind, direction)} relationships.`;
    }
  }
}
```

- [x] **Step 3: Render chips as buttons**

Change `renderRelationshipChips(nodeId)` so each chip uses:

```javascript
const item = document.createElement("button");
item.type = "button";
item.className = "raya-graph-detail-relationship-chip";
item.setAttribute("data-raya-graph-relationship-chip", "");
item.setAttribute("data-raya-graph-relationship-kind", chip.kind);
item.setAttribute("data-raya-graph-relationship-direction", chip.direction);
item.setAttribute("aria-pressed", "false");
item.textContent = `${relationshipChipLabel(chip.kind, chip.direction)} ${chip.count}`;
item.addEventListener("click", () => setRelationshipFocus(chip.kind, chip.direction));
```

After appending all chips, call `syncRelationshipFocusDom()`.

- [x] **Step 4: Clear focus on selection reset and selection changes**

In `renderDetail()`, when no node exists, call `clearRelationshipFocus()` before hiding relationship UI.

In `selectGraphNode(nodeId)`, `clearGraphSelection()`, the reset button handler, search input handler, and `initializeGraphStateFromUrl()` before selecting a URL page, clear active relationship focus so stale chip focus never survives a selected page change.

- [x] **Step 5: Add styles**

In `rendering.py`, update `.raya-graph-detail-relationship-chip` for button behavior:

```css
.raya-graph-detail-relationship-chip {
  cursor: pointer;
  font: inherit;
}
.raya-graph-detail-relationship-chip[aria-pressed="true"] {
  background: var(--raya-color-text);
  border-color: var(--raya-color-text);
  color: var(--raya-color-surface);
}
.raya-graph-detail-relationship-chip:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-graph-relationship-focus-status {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: -0.15rem 0 0.55rem;
}
```

- [x] **Step 6: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: pass.

### Task 3: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update foundation contract**

Add one sentence to the graph workspace contract:

```markdown
Selected-page relationship chips may act as transient local focus controls for the existing relationship walkthrough, but they must not persist state, mutate URL state, or infer recommendations.
```

- [x] **Step 2: Update role docs**

Add short English and Spanish role-doc notes describing relationship chips as local graph walkthrough filters. Keep language structural: "show", "focus", "relationship kind"; avoid progress, mastery, recommendation, ranking, or learner-state language.

### Task 4: Review, Verification, Commit

**Files:**
- All files changed in Tasks 1-3.

- [x] **Step 1: Request independent review**

Dispatch a reviewer with this focus:

```text
Review the uncommitted graph relationship chip focus diff. Check static-only constraints, no fetch/XHR/storage/CDN, no schema/data changes, URL state unchanged, accessibility of chip buttons, hidden card focusability, reset behavior, and preservation of existing graph node/page links.
```

- [x] **Step 2: Run verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-25-graph-relationship-chip-focus-design.md docs/superpowers/plans/2026-06-25-graph-relationship-chip-focus.md packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add graph relationship chip focus"
git push origin new_rayalucaria
```
