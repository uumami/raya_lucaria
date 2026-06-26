# Graph Node Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formalize current graph node repositioning as a constrained, non-persistent static graph readability affordance.

**Architecture:** Keep the existing local SVG implementation in `packages/static/src/raya_static/graph.py`; add tests that assert its constraints and update foundation/student documentation. Do not add schema fields, storage, URL state, runtime fetches, external libraries, or new generated payloads.

**Tech Stack:** Python static builder, generated local JavaScript, pytest contract tests, Playwright e2e.

---

## File Structure

- `tests/contracts/test_static_builder.py` asserts graph script markers for constrained node repositioning.
- `tests/contracts/test_documentation_surfaces.py` asserts role docs mention the new accepted affordance.
- `docs/foundation/20_learning_renderer_contract.md` records the accepted renderer contract.
- `docs/guides/en/students/index.md` and `docs/guides/es/estudiantes/index.md` explain the student-facing behavior.
- `docs/superpowers/legacy-ux-convergence-audit.md` updates the legacy inventory row from candidate to adapted.

### Task 1: Contract And Documentation RED

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/contracts/test_documentation_surfaces.py`

- [ ] **Step 1: Add graph script contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, after existing graph pan assertions, add:

```python
assert "startGraphNodeDrag" in graph_script
assert "moveGraphNodeDrag" in graph_script
assert "manualNodePositions" in graph_script
assert "pointerType !== \"mouse\"" in graph_script
assert "is-dragging-node" in graph_script
assert "suppressedNodeClick" in graph_script
```

- [ ] **Step 2: Add documentation contract assertions**

Add a test to `tests/contracts/test_documentation_surfaces.py`:

```python
def test_student_docs_cover_constrained_graph_node_repositioning() -> None:
    required = {
        "docs/foundation/20_learning_renderer_contract.md": [
            "temporarily reposition visible SVG graph nodes",
            "must not persist to browser storage",
            "must not mutate URL state",
        ],
        "docs/guides/en/students/index.md": [
            "reposition visible graph nodes",
            "Reset graph restores the generated layout",
            "not a layout editor",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "reposicionar nodos visibles del grafo",
            "Reset graph restaura el layout generado",
            "no es un editor de layout",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_documentation_surfaces.py::test_student_docs_cover_constrained_graph_node_repositioning -q
```

Expected: documentation test fails because authoritative docs do not yet name constrained graph node repositioning.

### Task 2: Documentation And Audit

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/superpowers/legacy-ux-convergence-audit.md`

- [ ] **Step 1: Update foundation contract**

Add one sentence near graph viewport controls:

```markdown
Desktop mouse users may temporarily reposition visible SVG graph nodes to untangle the current view; this updates only local node and visible edge geometry, must stay within graph bounds, must reset through `Reset graph`, and must not persist to browser storage, mutate URL state, change graph data, or imply recommendation, ranking, progress, mastery, or authority.
```

- [ ] **Step 2: Update English student guide**

Add:

```markdown
On wider screens with a mouse, you may also reposition visible graph nodes to untangle the current view. This is temporary visual cleanup only: `Reset graph` restores the generated layout, Fit and zoom keep the moved view readable, and the move is not a layout editor, course-data change, saved preference, recommendation, or progress signal.
```

- [ ] **Step 3: Update Spanish student guide**

Add:

```markdown
En pantallas anchas con mouse, tambien puedes reposicionar nodos visibles del grafo para desenredar la vista actual. Es solo limpieza visual temporal: `Reset graph` restaura el layout generado, Fit y zoom mantienen legible la vista movida, y el movimiento no es un editor de layout, cambio de datos del curso, preferencia guardada, recomendacion ni senal de progreso.
```

- [ ] **Step 4: Update legacy audit**

Change the Graph node dragging row from candidate to adapted with current constraints.

- [ ] **Step 5: Verify GREEN**

Run the focused command from Task 1. Expected: both selected tests pass.

### Task 3: Review And Verification

**Files:**
- All changed files.

- [ ] **Step 1: Request independent review**

Dispatch at least one reviewer focused on foundation alignment and one focused on graph/static-state risks.

- [ ] **Step 2: Run focused browser verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass, proving the existing node repositioning behavior remains intact.

- [ ] **Step 3: Run final host gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-node-repositioning-design.md docs/superpowers/plans/2026-06-26-graph-node-repositioning.md tests/contracts/test_static_builder.py tests/contracts/test_documentation_surfaces.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/superpowers/legacy-ux-convergence-audit.md
git commit -m "Document graph node repositioning"
git push origin new_rayalucaria
```
