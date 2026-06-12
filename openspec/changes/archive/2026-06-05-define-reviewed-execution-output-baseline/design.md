## Context

Phase 4 added explicit local execution and generated run results under the artifact root. Those results are useful for local work, but they are not source truth and are not shown in the static page. The foundation plan already reserves `frozen` for reviewed output, and the current specs intentionally refuse `frozen` until this contract exists.

The reviewed-output baseline should bridge that gap without adding backend approval workflows, remote runners, or implicit execution. Professors need a way to turn a successful generated result into reviewed source support, students need a static visual cue that an output is reviewed and current, and agents need machine-readable metadata that does not require scraping HTML.

## Goals / Non-Goals

**Goals:**

- Add reviewed execution output as source-controlled support material colocated under the learning quantum it serves.
- Keep reviewed output private in source and public only through intentional artifact data/static rendering.
- Add CLI output inspection and freezing commands that do not execute targets.
- Make `policy: frozen` validate reviewed output rather than refusing by default.
- Detect missing or stale reviewed output from current source, runtime profile, lockfile, and cache metadata.
- Render compact reviewed-output panels in static pages while preserving manifest data as authority.
- Keep generated execution results separate from reviewed source support.

**Non-Goals:**

- Add browser execution, remote execution, CI batch execution, GPU runners, or multi-target selectors.
- Add signed attestations, institutional approval services, or identity-backed reviewer trust.
- Treat generated run results as reviewed merely because they exist.
- Store reviewed output under `artifact/` as source truth.
- Render full rich notebook outputs beyond a compact baseline.
- Make `raya build`, `raya validate`, artifact inspection, static serving, output listing, or output freezing execute code.

## Decisions

1. Reviewed output lives under colocated `_reviewed/`.

Use a private support directory such as:

```text
course/
  1_topic/
    0_index.md
    code/
      cache_task.py
    _reviewed/
      execution/
        cache-script/
          reviewed.yaml
          stdout.txt
```

This keeps reviewed output with the learning quantum it explains and preserves the convention-first `source: course` tree. `_reviewed/` is source support, not rendered navigation. The artifact builder decides how to expose it.

Alternative considered: root `reviewed/` beside `course/`. That keeps execution material outside the learning tree, but it weakens ownership and makes it harder for professors to review a topic diff in context.

2. Freezing copies generated output into source support, then human review happens through normal source review.

`raya outputs freeze <course> <target>` should read the latest successful generated execution result, copy declared output/log excerpts into `_reviewed/`, and write a reviewed manifest. The command does not mean an institution approved the output; it prepares source changes for human review and commit.

Alternative considered: keep reviewed output only in `artifact/cache/results/`. That is simpler, but generated artifacts are rebuildable and ignored; they cannot be the long-term source of course truth.

3. `frozen` means "validate reviewed output" and never "execute".

After this phase, `policy: frozen` should pass only when a reviewed output manifest exists and matches the current target source, runtime profile, lockfile, cache key, and declared reviewed files. It must not run the target or refresh the cache.

Alternative considered: `frozen` reuses generated cache output. That confuses generated cache records with reviewed course material and makes static publishing depend on local artifact history.

4. Static visualization is compact and data-backed.

Glintstone should render a reviewed-output panel near the existing reference panel when a page references a target with current reviewed output. The panel should show status, target, reviewed label/date when available, profile, and links or excerpts for reviewed output files. The machine authority remains `data/reviewed-outputs.json`.

Alternative considered: embed full stdout/notebook output directly into the page. That risks large pages and hard-to-review HTML. The baseline should use compact excerpts and links.

5. Validation fails stale reviewed outputs.

A stale reviewed output is worse than no reviewed output because it can mislead students. If source, inputs, runtime profile, lockfile, cache key, or declared files no longer match, validation should fail with diagnostics naming the stale target and the next action.

Alternative considered: render stale output with a warning. That could publish incorrect course material by accident, especially on static hosting.

## Risks / Trade-offs

- Reviewed outputs can become large -> keep compact default previews and copy files by reference into artifact storage.
- Freezing may be mistaken for institutional approval -> document that source review/commit is the approval boundary for this baseline.
- Hash-based staleness can miss hidden dependencies -> require declared inputs for baseline cache keys and keep hidden dependency limitations documented.
- `_reviewed/` adds another private support directory -> keep it colocated and narrowly scoped to execution output.
- Notebook output rendering can grow complex -> baseline links/copies output notebooks and renders compact metadata; rich notebook result rendering can come later.

## Migration Plan

1. Add reviewed-output schemas and validators.
2. Add `_reviewed/` source support discovery and stale diagnostics.
3. Add `raya outputs list` and `raya outputs freeze`.
4. Teach frozen policy to validate reviewed output without execution.
5. Add reviewed output artifact data and static panel rendering.
6. Add fixtures, contract tests, e2e/static-read-path tests, docs, and OpenSpec config updates.

Rollback is straightforward: remove the outputs commands, reviewed-output validators, artifact data, and static panels. Existing Phase 1-4 rendering, execution, and generated-result behavior remains valid.

## Open Questions

- Should a future review workflow add optional reviewer identity/signature fields through Glintstone Key?
- Should reviewed output manifests eventually support multiple named views per target?
- Should CI verification become `raya outputs verify` or a separate `raya verify` command?
