# FDD-Style Course Tree Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the reader course tree so branches use a dedicated FDD-style chevron, titles remain links, same-parent expansion behaves as a protected accordion, and the expanded or mini course rail occupies the full structural viewport without sacrificing static, keyboard, filter, storage, or phone behavior.

**Architecture:** `builder.py` emits semantic branch controls, structural-number/title spans, stable controlled groups, and static current-path exposure. `shell.py` separates persisted branch preference from effective visibility and applies every direct action through one accordion transaction. `rendering.py` owns the compact two-column tree, vertical guides, full-height structural geometry, and no-script fallback. The density fixture, browser suites, foundation contract, and role guides provide the executable and written truth surfaces.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JavaScript, pytest, Playwright with Chromium, uv workspace, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-05-fdd-course-tree-correction-design.md`, approved after UX/UI, accessibility, and technical adversarial review.

## Global Constraints

- Work only on `feature/navigation-first-course-rail`; preserve unrelated user changes.
- `docs/foundation/` remains the highest truth. Update the smallest affected renderer contract before claiming the implementation current.
- Option A is fixed: a dedicated chevron changes expansion; the number/title anchor navigates; row whitespace has no action.
- Fine-pointer rows use `30px minmax(0, 1fr)` and 14px text with 19-21px line height. Coarse/no-hover rows use `44px minmax(0, 1fr)` and operable targets at least 44px.
- Child groups use 16px logical margin, 8px logical padding, one 1px vertical guide, and no horizontal elbows.
- Structural numbers come only from `ContentPage.display_label`, with the established appendix `hierarchy_label`; never infer them from sequence, filenames, CSS counters, or title parsing.
- Keep `raya:course-map-branches:v1:<course_id>` in `sessionStorage`. Its meaning remains the set of collapsed branch IDs.
- Persist one final collapsed-ID set per direct user transaction. Filter, restoration, current-path exposure, and initialization normalization never write.
- At `640px+`, both the 256px expanded rail and 48px mini rail are fixed from viewport top to bottom. The central navigation remains the only left-rail vertical scroll owner.
- Below 640px, preserve the existing modal drawer lifecycle. Mobile is regression coverage, not a visual redesign.
- JavaScript-disabled output must advertise no inert controls and must retain navigable current-path links at every width.
- Do not add dependencies, duplicate the course-tree DOM, edit generated artifacts, persist filter/focus/scroll/drawer state, or introduce learner inference.
- Use `apply_patch` for manual edits. Run focused RED/GREEN commands in every task and the host, smoke, and Docker gates sequentially at the end.
- Browser tests use `RAYA_TEST_BROWSER=/usr/bin/google-chrome` if Chromium auto-detection is unavailable.

## File Map

| File | Responsibility |
| --- | --- |
| `examples/courses/rail-density-fixture/` | Accordion-valid depth, numbering, label, and overflow evidence |
| `packages/static/src/raya_static/builder.py` | Semantic tree markup, labels, chevron icon, initial static state |
| `packages/static/src/raya_static/rendering.py` | Tree geometry, guides, full-height rail, responsive and no-script CSS |
| `packages/static/src/raya_static/shell.py` | Preference/effective state, accordion, filter, keyboard, focus, BFCache |
| `tests/contracts/test_static_builder.py` | Generated markup and resource contracts |
| `tests/contracts/test_documentation_surfaces.py` | Foundation/role parity |
| `tests/e2e/test_preview_static_read_path.py` | Disclosure, persistence, filter, keyboard, static read path |
| `tests/e2e/test_rail_density.py` | Density, guides, overflow, input modality, scroll ownership |
| `tests/e2e/test_rail_collapse_contract.py` | Expanded/mini full-height structural geometry |
| `tests/e2e/test_render_debug_parity_gate.py` | Required render-debug visual states |
| `scripts/check-render-debug.sh` | Local Chromium evidence capture |
| `docs/foundation/20_learning_renderer_contract.md` | Current renderer truth |
| `docs/guides/{en,es}/{contributors,professors,students,agents}/index.md` | Role-facing behavior |

---

### Task 1: Make The Density Fixture Accordion-Complete

**Files:**
- Modify: `examples/courses/rail-density-fixture/raya.yaml`
- Modify: `examples/courses/rail-density-fixture/course/`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Produces sibling branches, three visible levels, a deep current page, `1`, `1.2`, `12.10`, appendix, unnumbered-root, authored-number-prefix, long-label, and direct-leaf overflow cases.
- Preserves existing IDs used by density tests, especially `rail-density-root` and `rail-density-identifier`.

- [ ] **Step 1: Add a failing fixture-shape contract**

Add `test_rail_density_fixture_covers_fdd_tree_contract` to `tests/contracts/test_static_builder.py`. Build the fixture into `tmp_path`, inspect `manifest.json` and rendered HTML, and assert:

```python
labels = {page["label"] for page in manifest["pages"]}
assert {"1", "1.2", "12.10"} <= labels
assert any(page["hierarchy_label"] == "Appendix" for page in manifest["pages"])
assert 'data-raya-map-depth="2"' in rendered
assert rendered.count('data-raya-map-depth="1"') >= 3
assert "12.10 Already numbered navigation title" in rendered
assert "ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007" in rendered
```

Also assert one branch owns at least 18 direct leaf children, enough to overflow a 420px central scroller while no sibling branch is expanded.

- [ ] **Step 2: Confirm RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rail_density_fixture_covers_fdd_tree_contract -v
```

Expected: FAIL because the fixture lacks the appendix, `12.10`, authored-number-prefix, and direct-leaf overflow cases.

- [ ] **Step 3: Extend source content without replacing existing paths**

Add the smallest numbered directories/pages required by the assertions. Use front matter `nav_title: 12.10 Already numbered navigation title` for the de-duplication case, an appendix-key source entry accepted by the current hierarchy schema, and direct leaf pages under one existing branch. Keep prose to one heading and one sentence per fixture page.

- [ ] **Step 4: Keep the fixture deterministic**

Update `raya.yaml` hierarchy only as required to express appendix behavior. Do not introduce generated files or rely on lexical ordering outside the accepted numbered course-source contract.

- [ ] **Step 5: Run fixture contracts**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "rail_density_fixture or child_ids" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add examples/courses/rail-density-fixture tests/contracts/test_static_builder.py
git commit -m "Extend course tree acceptance fixture"
```

### Task 2: Emit Semantic Disclosure, Number, And Title Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Replaces `_navigation_label(page) -> str` with helpers that separately return the generated structural label and unchanged `nav_title`.
- Emits `.raya-course-map-node-number` and `.raya-course-map-node-title` inside the same anchor.
- Emits branch-only buttons with stable `aria-controls`, stateful accessible names, a decorative `chevron-right` command icon, and an enhancement-only marker.

- [ ] **Step 1: Replace old markup assertions with a failing semantic contract**

Add `test_course_map_emits_fdd_style_disclosure_and_link_ownership`. Parse every visible node row and assert:

```python
assert branch.button["aria-label"] == f"Collapse {branch.title}" or branch.button["aria-label"] == f"Expand {branch.title}"
assert branch.button["aria-controls"] == branch.children["id"]
assert branch.button.select_one('[data-raya-command-icon="chevron-right"]')
assert branch.button.select_one("svg")["aria-hidden"] == "true"
assert branch.anchor.select_one(".raya-course-map-node-title").get_text(strip=True) == branch.nav_title
assert leaf.select_one("button") is None
assert leaf.select_one(".raya-course-map-node-spacer") is not None
assert "data-raya-map-index" not in branch.anchor.attrs
```

For the fixture cases, assert `1`, `1.2`, appendix plus display label, and `12.10` are spoken once; the already-numbered title remains byte-for-byte unchanged and omits the separate number span.

- [ ] **Step 2: Confirm RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "fdd_style_disclosure or course_map_child_ids" -v
```

Expected: FAIL on empty ASCII-era buttons, combined text labels, the global sequence index, and missing spans/icon.

- [ ] **Step 3: Add exact label helpers**

Implement private helpers with these contracts:

```python
def _course_map_structural_label(page: ContentPage) -> str:
    parts = [page.display_label] if page.display_label else []
    if page.hierarchy_key == "appendix" and page.hierarchy_label:
        parts.insert(0, page.hierarchy_label)
    return " ".join(parts)

def _nav_title_begins_with_structural_label(title: str, label: str) -> bool:
    if not label:
        return False
    remainder = " ".join(title.split())[len(" ".join(label.split())):]
    return " ".join(title.split()).startswith(" ".join(label.split())) and (
        not remainder or remainder[0].isspace() or remainder[0] in ".:-)"
    )
```

Implement the comparison without slicing the original `nav_title`; normalization is for comparison only. Expand the punctuation set only when a failing accepted fixture proves another authored separator is required.

- [ ] **Step 4: Add the established chevron icon**

Add `chevron-right` to `_COMMAND_ICON_BODIES` and render it with `_command_icon`. Do not create inline one-off SVG markup or visible ASCII pseudo-content.

- [ ] **Step 5: Rewrite `render_node` ownership**

Keep the stable child-group IDs and initial current-path expansion. The anchor contains optional number span followed by the unchanged title span. The disclosure contains the decorative icon and `data-raya-map-enhancement-control`; the leaf spacer occupies the same first grid column. If child-group generation fails, omit the disclosure instead of advertising a broken button.

- [ ] **Step 6: Run contracts**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "course_map or navigation_label or child_ids" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git commit -m "Emit semantic course tree disclosures"
```

### Task 3: Apply Compact FDD Tree Geometry

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_rail_density.py`
- Test: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Owns row columns, 14px type, long-label flow, structural number sizing, current marker, chevron rotation, 16px/8px/1px guides, and fine/coarse targets.
- Removes the current sequence-pill pseudo-element and ASCII disclosure content.

- [ ] **Step 1: Add failing browser geometry assertions**

Replace `test_sequence_badge_shows_only_on_the_current_row` with `test_tree_numbers_titles_and_current_marker_do_not_overlap`. Add `test_fdd_tree_guides_and_targets_match_pointer_mode`. Measure:

```javascript
const row = document.querySelector('.raya-course-map-node-row');
const group = document.querySelector('[data-raya-map-children]:not([hidden])');
const toggle = row.querySelector('[data-raya-map-node-toggle]');
const link = row.querySelector('a');
return {
  columns: getComputedStyle(row).gridTemplateColumns,
  fontSize: getComputedStyle(link).fontSize,
  lineHeight: getComputedStyle(link).lineHeight,
  toggleWidth: toggle.getBoundingClientRect().width,
  groupMargin: getComputedStyle(group).marginInlineStart,
  groupPadding: getComputedStyle(group).paddingInlineStart,
  groupBorder: getComputedStyle(group).borderInlineStartWidth,
  pseudo: getComputedStyle(link, '::before').content,
};
```

Fine expectations are `30px`, `14px`, 19-21px, `16px`, `8px`, `1px`, and no numbered pill content. Repeat with `has_touch=True` and require a 44px first column and 44px link/control height.

- [ ] **Step 2: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "fdd_tree_guides or tree_numbers_titles" -v
```

Expected: FAIL on current 24px columns, 12-13px type, tight guide, ASCII pseudo-content, and sequence pill.

- [ ] **Step 3: Replace tree CSS as one coherent block**

Set `.raya-course-map-node-row` to the exact two-column grid. Give the toggle/spacer fixed logical size, keep the icon 12-14px, rotate it from the button's synchronized `aria-expanded`, and expose hover/pressed/focus-visible boundaries only on the disclosure. Give the anchor `min-width: 0`, the number `flex: 0 0 auto`, and the title `min-width: 0; overflow-wrap: anywhere`.

- [ ] **Step 4: Restore reference-style guides and active states**

Apply only a logical-start vertical border to child `ol` groups. Current anchors use `aria-current`, stronger text/accent, and a 2-3px logical-start marker that does not consume grid width. Ancestors use moderate emphasis. Delete horizontal connector and sequence-pill rules and their obsolete comments.

- [ ] **Step 5: Add coarse/no-hover overrides**

Use the existing pointer media-query structure. Wrapped labels may grow their own row, but every coarse title link and disclosure/spacer remains at least 44px with no target overlap.

- [ ] **Step 6: Run density and CSS contracts**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "long_labels or coarse_pointer or controls_match or fdd_tree or tree_numbers" -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k "compact_control_resources or course_map" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_density.py tests/contracts/test_static_builder.py
git commit -m "Compact the FDD-style course tree"
```

### Task 4: Separate Branch Preference From Effective Visibility

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- `data-raya-map-expanded` is preference state.
- `aria-expanded`, child `hidden`, and child `aria-hidden` are effective state.
- Initialization parses v1 storage, normalizes sibling visibility deterministically, exposes the current path, and performs zero writes.

- [ ] **Step 1: Add failing restoration-layer tests**

Add `test_course_map_restores_preference_and_normalizes_effective_accordion_without_write`. Seed a v1 payload with multiple same-parent siblings expanded, instrument `sessionStorage.setItem`, load a deep current page, and assert:

```python
assert writes == []
assert current_path_toggle.get_attribute("aria-expanded") == "true"
assert current_path_node.get_attribute("data-raya-map-expanded") == "false"
assert effective_expanded_ids == [current_path_id, first_extra_id]
assert later_sibling_toggle.get_attribute("aria-expanded") == "false"
assert later_sibling_node.get_attribute("data-raya-map-expanded") == "true"
```

The exact expected IDs must come from fixture order, not a sorted set.

- [ ] **Step 2: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "normalizes_effective_accordion" -v
```

Expected: FAIL because the existing setter conflates stored preference and effective visibility.

- [ ] **Step 3: Introduce explicit shell helpers**

Implement these JavaScript responsibilities in `shell.py`:

```javascript
function setMapNodePreference(node, expanded) { /* dataset only */ }
function setMapNodeEffective(node, expanded) { /* aria/hidden only */ }
function normalizedPreferenceExpansion(nodes, protectedPath) { /* DOM order */ }
function applyEffectiveMapState({filterQuery = ''} = {}) { /* no writes */ }
```

`loadCollapsedMapNodeIds` validates strings and ignores unavailable/corrupt storage. `applyEffectiveMapState` applies preference, sibling normalization, current-path exposure, then page-local explicit current-ancestor collapses.

- [ ] **Step 4: Synchronize accessible names**

Whenever effective state changes, set the full stateful `Expand <title>` or `Collapse <title>` label from the row's full label metadata. Keep `aria-controls`, `aria-expanded`, child `hidden`, and child `aria-hidden` synchronized.

- [ ] **Step 5: Prove restoration writes nothing**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "course_map and (storage or restores or normalizes)" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "Separate map preference from visibility"
```

### Task 5: Centralize Protected Accordion Transactions

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- One `applyMapUserTransition(node, nextExpanded)` handles pointer, disclosure Enter/Space, and title-anchor arrows.
- Expanding collapses eligible expanded siblings with the same parent/depth, protects the current path, records explicit current-ancestor collapse, and persists once.

- [ ] **Step 1: Add failing pointer and keyboard parity tests**

Add `test_course_map_direct_actions_share_one_protected_accordion_transaction`, parameterized by `click`, disclosure `Enter`, disclosure `Space`, anchor `ArrowRight`, and anchor `ArrowLeft`. For each action reset context/storage and compare:

```python
assert result["expanded"] == expected_expanded_ids
assert result["preferences"] == expected_preference_map
assert result["stored"] == expected_collapsed_ids
assert result["writes"] == 1
assert result["hiddenAriaMismatch"] == []
```

Add a case where a peer expands without collapsing the current-path ancestor and a case where direct collapse of the current ancestor survives a later unrelated peer action.

- [ ] **Step 2: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "protected_accordion_transaction" -v
```

Expected: FAIL because current pointer and anchor-key paths do not share accordion/persistence behavior.

- [ ] **Step 3: Implement one transaction function**

Compute the final preference map in memory: apply the direct change, collapse eligible same-parent/same-depth siblings, skip protected current-path branches unless they are the direct target, update page-local explicit-collapse tracking, derive effective state, then call `saveCollapsedMapBranches()` once.

- [ ] **Step 4: Route every direct input through it**

Disclosure `click` handles native pointer/Enter/Space activation and retains disclosure focus when visible. Title-anchor ArrowRight expands or moves to the first visible child; ArrowLeft collapses or moves to the parent. Do not intercept arrows while a disclosure owns focus.

- [ ] **Step 5: Make collapse focus-safe**

Before hiding a subtree, detect whether `document.activeElement` is inside it. Move focus to that branch's disclosure before applying `hidden`; cover direct, accordion, restoration, and filter collapse paths.

- [ ] **Step 6: Run interaction coverage**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "course_map and (accordion or keyboard or collapsible or focus or storage)" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "Centralize course tree accordion actions"
```

### Task 6: Enforce Filter, Focus, And BFCache Precedence

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- A direct branch action with an active query clears the volatile filter first, restores base effective state without writing, then performs one user transaction and one write.
- Page-local explicit collapse survives `pageshow` for the same document and resets on navigation/new document.

- [ ] **Step 1: Add the failing filter-input matrix**

Add `test_filtered_branch_actions_clear_then_apply_one_equivalent_transaction`, parameterized over click, Enter, Space, ArrowRight, and ArrowLeft. Filter for a descendant under a normally collapsed branch, activate the target, and assert:

```python
assert filter_input.input_value() == ""
assert empty_state.is_hidden()
assert snapshots_for_all_inputs_are_equal
assert storage_write_count == 1
assert no_hidden_subtree_contains_document_active_element
```

- [ ] **Step 2: Add BFCache assertions**

Directly collapse a current-path ancestor, dispatch or naturally trigger `pageshow(persisted=true)`, and prove it stays effectively collapsed without a storage write. Navigate to a different generated page and prove the new document exposes its own current path.

- [ ] **Step 3: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "filtered_branch_actions or bfcache" -v
```

Expected: FAIL on keyboard/filter ordering and page-local explicit-collapse restoration.

- [ ] **Step 4: Centralize pre-action filter clearing**

Add one helper used before all direct branch input routes. It clears the input and empty state, calls the no-write effective-state restoration in the required order, then calls `applyMapUserTransition`.

- [ ] **Step 5: Preserve page-local intent only in memory**

Keep explicit current-path collapses in a document-local `Set`/`WeakSet`. Do not serialize them. On `pageshow`, reapply effective state using the retained set; a new document naturally initializes a new set.

- [ ] **Step 6: Run filter and navigation coverage**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "course_map and (filter or bfcache or keyboard or focus)" -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/shell.py tests/e2e/test_preview_static_read_path.py
git commit -m "Stabilize filtered course tree actions"
```

### Task 7: Pin Expanded And Mini Rails To The Structural Viewport

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_rail_collapse_contract.py`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- At `640px+`, `.raya-course-map` is fixed with logical block insets zero, `height: 100vh; height: 100dvh`, square outer edges, divider, and clipped outer overflow.
- The shell reserves 256px expanded or 48px mini width. Expanded layout remains `48px minmax(0,1fr) 48px`; only `.raya-course-map-navigation` scrolls.

- [ ] **Step 1: Add failing full-height geometry coverage**

Add `test_structural_course_rail_is_viewport_pinned_in_expanded_and_mini_states`, parameterized at widths `1440, 1024, 894, 893, 768, 640` and normal/short heights. Measure before/after article scroll and viewport resize:

```python
assert abs(rect["top"]) <= 1
assert abs(rect["bottom"] - inner_height) <= 1
assert rect["height"] <= inner_height + 1
assert style["position"] == "fixed"
assert style["borderRadius"] == "0px"
assert style["boxShadow"] == "none"
assert shell_reserved_width in {48, 256}
```

Assert header/footer positions do not move when the central navigation scrolls and outer/list elements do not become scroll owners.

- [ ] **Step 2: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -k "viewport_pinned" -v
```

Expected: FAIL because the current rail retains inset/card/max-height behavior.

- [ ] **Step 3: Replace structural outer geometry**

Inside the existing `640px+` rules, set fixed logical insets, ordered `100vh` then `100dvh`, `box-sizing: border-box`, zero margin/radius/shadow, divider, and outer overflow clipping for both expanded and mini states. Preserve the existing shell grid/state tokens rather than duplicating breakpoint numbers.

- [ ] **Step 4: Preserve the single scroll owner**

Keep header/footer fixed grid tracks and `minmax(0,1fr)` central content. Ensure `.raya-course-map-navigation` alone has `overflow-y:auto`; outer rail, body, content section, and list must not.

- [ ] **Step 5: Run structural and scrolling tests**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -k "collapsed_course_map or viewport_pinned or viewport_height or short_viewports" -q
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -k "single_scroll_owner or header_footer or native_wheel or structural" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_collapse_contract.py tests/e2e/test_rail_density.py
git commit -m "Pin the structural course rail"
```

### Task 8: Provide A Complete No-Script Rail Fallback

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Enhancement controls are hidden until `html[data-raya-shell-ready="true"]`.
- Without JavaScript, the rail is static/in-flow at all widths, current-path groups are visible, static links remain reachable, and no inert filter/toggle/drawer/tooltip surface is visible or focusable.

- [ ] **Step 1: Add a JS-disabled Chromium matrix**

Add `test_no_script_course_rail_is_static_reachable_and_has_no_inert_controls`, parameterized at `1440, 893, 640, 639, 390`. Create a context with `java_script_enabled=False`, then assert:

```python
assert rail.evaluate("e => getComputedStyle(e).position") == "static"
assert static_links == ["Search", "Graph", "Practice", "Tasks", "Schedule"]
assert enhancement_controls_visible == []
assert enhancement_controls_in_tab_order == []
assert current_path_links_are_visible
assert page.locator(".raya-course-map-backdrop:visible").count() == 0
```

Sequentially follow branch-title anchors through three levels to a deep leaf and assert each destination's current-path navigation remains visible.

- [ ] **Step 2: Confirm RED**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "no_script_course_rail" -v
```

Expected: FAIL because current prepaint/drawer rules do not provide the complete inline fallback.

- [ ] **Step 3: Mark every enhancement-only control consistently**

Use a shared `data-raya-enhancement-control` marker on disclosure, Context, collapse/expand/close, Text size, OpenDyslexic, filter/label/empty state, drawer opener/backdrop, and JS-only tooltip wrappers. Static links, home, position, article, tree anchors, and right-rail static content must not receive it.

- [ ] **Step 4: Make readiness opt controls in**

Base CSS hides enhancement markers. `html[data-raya-shell-ready="true"]` restores their intended display through component rules. For non-ready documents, neutralize fixed/drawer/transform/inert-looking geometry, body lock, overlay, and mini state; render the current-path navigation in normal flow before the article.

- [ ] **Step 5: Verify JS and no-JS paths**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "no_script or static_read_path or drawer" -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add static course rail fallback"
```

### Task 9: Replace Expand-All Tests With Valid Accordion Paths

**Files:**
- Modify: `tests/e2e/test_rail_density.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

**Interfaces:**
- Deletes `_expand_course_map_branches` and every live-selector drain loop.
- Adds `_expand_course_map_path(page, node_ids)` and `_expand_overflow_branch(page, node_id)` helpers that produce valid accordion states.

- [ ] **Step 1: Add a static guard that fails while expand-all remains**

Add:

```python
def test_density_suite_never_expands_every_accordion_branch() -> None:
    source = Path(__file__).read_text()
    assert "_expand_course_map_branches" not in source
    assert "while toggles.count()" not in source
```

- [ ] **Step 2: Confirm RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_density_suite_never_expands_every_accordion_branch -v
```

Expected: FAIL on the existing helper and deep-fixture drain loop.

- [ ] **Step 3: Add deterministic path helpers**

Implement helpers that locate exact `data-raya-map-node` IDs, click only collapsed ancestors in order, and assert each requested node ends expanded before proceeding. The overflow helper opens the fixture branch containing 18+ direct leaves and asserts central `scrollHeight > clientHeight` without opening a sibling.

- [ ] **Step 4: Migrate all density cases**

Replace expand-all calls in wheel, touch, orientation, long-label, deep-tree, and short-height tests. For depth/DOM counts, inspect the static DOM directly; for geometry/scroll counts, use the single valid current path or overflow branch. Update the fixture guard to assert at least 30 static links, depth at least 2, and one valid overflowing accordion state.

- [ ] **Step 5: Run the complete density suite**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -q
```

Expected: PASS with no guard loops or accordion-invalid state.

- [ ] **Step 6: Commit**

```bash
git add tests/e2e/test_rail_density.py tests/e2e/test_preview_static_read_path.py
git commit -m "Use valid accordion test states"
```

### Task 10: Update Foundation And Role Truth Surfaces

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_documentation_surfaces.py`
- Test: `tests/contracts/test_static_builder.py`

**Interfaces:**
- Documents separate chevron/link ownership, protected same-parent accordion, current-path/direct-intent behavior, full-height expanded/mini structural geometry, single central scroller, and no-script fallback.

- [ ] **Step 1: Add failing parity phrases**

Extend `test_reader_rail_visual_parity_truth_surfaces_agree` to require stable contract language in foundation plus all eight guides. Require English surfaces to describe `separate disclosure control`, `same-parent accordion`, `full viewport height`, and `no-script navigation`; require the equivalent established Spanish terms `control de despliegue separado`, `acordeon entre ramas hermanas`, `altura completa del viewport`, and `navegacion sin JavaScript`.

Also assert obsolete `sequence badge`, `ASCII`, `expand every branch`, and short floating-card claims are absent from renderer guidance.

- [ ] **Step 2: Confirm RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py::test_reader_rail_visual_parity_truth_surfaces_agree -v
```

Expected: FAIL because current truth surfaces describe the pre-correction tree.

- [ ] **Step 3: Amend the smallest foundation paragraphs**

Update only the course-rail structure, interaction, static fallback, and verification paragraphs in `20_learning_renderer_contract.md`. Preserve storage keys, six actions, comfort controls, right-rail behavior, no-inference boundaries, and discovery workspace contracts. `00_index.md` needs no edit because the document inventory is unchanged.

- [ ] **Step 4: Update role guidance by audience**

Student guides explain chevron expansion versus title navigation. Professor/contributor guides explain authored navigation and numbering behavior. Agent guides describe semantic, storage, accessibility, full-height, no-script, and browser checks. Keep emitted English control labels literal in Spanish docs where they identify UI text.

- [ ] **Step 5: Remove stale code-contract wording**

Update assertions/comments in `test_static_builder.py` that still require the sequence pill, generic `Toggle` label, tight guide, short card, or expand-all behavior.

- [ ] **Step 6: Run truth-surface contracts**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py tests/contracts/test_static_builder.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides tests/contracts/test_documentation_surfaces.py tests/contracts/test_static_builder.py
git commit -m "Document the corrected course tree"
```

### Task 11: Validate The Full Chromium Matrix And Adversarial UX

**Files:**
- Modify: `tests/e2e/test_render_debug_parity_gate.py`
- Modify: `tests/e2e/test_render_debug_report.py`
- Modify: `scripts/check-render-debug.sh`
- Modify only if a defect is found: `packages/static/src/raya_static/{builder.py,rendering.py,shell.py}` and focused tests

**Interfaces:**
- Captures expanded current-path, peer-expanded accordion, long-label, full-height mini, and phone drawer evidence.
- Independently compares desktop/tablet behavior with `/home/uumami/itam/fdd_p26` and `/home/uumami/itam/ia_p26` while enforcing Raya's stronger accessibility/static contracts.

- [ ] **Step 1: Extend the render-debug required-state contract**

Require report scenario IDs:

```python
required = {
    "course-tree-current-path-expanded",
    "course-tree-peer-accordion-expanded",
    "course-tree-long-label",
    "course-rail-mini-full-height",
    "course-tree-phone-drawer",
}
assert required <= set(report["scenarios"])
```

Each scenario records viewport, input modality, rail/tree rects, active branch IDs, focus owner, overflow owners, and screenshot path.

- [ ] **Step 2: Confirm RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_render_debug_report.py -v
```

Expected: FAIL because the new course-tree scenarios are absent.

- [ ] **Step 3: Add deterministic capture scenarios**

Update `check-render-debug.sh` and report tests to build `rail-density-fixture`, open exact node IDs, and capture the five required states. Keep screenshots/reports as ignored local evidence, never source truth.

- [ ] **Step 4: Run the explicit breakpoint/input matrix**

Run Chromium at widths `1440, 1024, 894, 893, 768, 640, 639, 390`, normal height 900/844 and short height 420, with fine pointer plus coarse/hybrid where supported. Cover expanded/collapsed structural rails and open/closed phone drawer. Assert top/bottom pinning, single scroller, row geometry, guide geometry, no overlap, accessible state synchronization, focus safety, accordion protection, filter equivalence, and drawer lifecycle.

- [ ] **Step 5: Dispatch three adversarial reviewers**

Use `superpowers:requesting-code-review` with independent agents:

1. UX/UI compares desktop/tablet screenshots and live disclosures against FDD and IA, checking compactness, hierarchy readability, hit ownership, full-height rail, and clunky transitions.
2. Accessibility/interaction exercises every visible disclosure by pointer and keyboard, focus during collapse, names/states, coarse targets, no-script, and phone modality.
3. Technical/contracts audits preference/effective separation, one-write transactions, current-path exceptions, filter/BFCache precedence, and test validity.

Require findings with file/line references. Fix every confirmed P0/P1/P2 defect with a focused RED/GREEN test; rerun the affected matrix before re-review. All three reviewers must return APPROVED or list only explicitly documented residual risk.

- [ ] **Step 6: Run render-debug evidence**

```bash
RAYA_RENDER_DEBUG_KEEP=1 RAYA_TEST_BROWSER=/usr/bin/google-chrome ./scripts/check-render-debug.sh
```

Expected: PASS and print the retained local report directory.

- [ ] **Step 7: Run focused browser suites**

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py tests/e2e/test_rail_density.py tests/e2e/test_rail_collapse_contract.py tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_render_debug_report.py -q
```

Expected: PASS.

- [ ] **Step 8: Run canonical gates sequentially**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q
./scripts/check.sh
./scripts/smoke-test.sh
./scripts/check-docker.sh
```

Expected: every command exits 0. Do not overlap host and Docker gates.

- [ ] **Step 9: Start the local comparison server**

Build and serve the validated fixture on the first free loopback port. Record the exact URL and keep the server running for the user. Verify the URL once in Chromium after startup.

- [ ] **Step 10: Commit final validation changes**

```bash
git add tests/e2e/test_render_debug_parity_gate.py tests/e2e/test_render_debug_report.py scripts/check-render-debug.sh
git commit -m "Validate FDD-style course tree behavior"
```

## Completion Evidence

Before reporting completion, invoke `superpowers:verification-before-completion` and record:

- focused RED/GREEN commands for every task;
- final host, smoke, and Docker exit codes;
- render-debug report path and five screenshot scenario IDs;
- three adversarial reviewer dispositions;
- local preview URL verified in Chromium;
- `git status --short`, confirming only intentional work remains.

Do not push, merge, open a pull request, or delete the worktree without explicit user instruction.
