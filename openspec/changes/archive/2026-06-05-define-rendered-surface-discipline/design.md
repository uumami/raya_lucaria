## Context

The current Glintstone baseline can validate and build ordered course pages, rich Markdown, generated navigation/index data, code/notebook references, runtime metadata, local execution metadata, and reviewed-output data. Those data products are useful, but the normal rendered course page is becoming a mixed audience surface: student content, contributor diagnostics, agent metadata, hashes, paths, runtime status, and fixture proof points can all compete for attention.

Foundation docs already separate source truth, artifact data, dynamic state, deployment, role documentation, and rendered documentation. This design makes that separation visible in generated HTML:

```text
source course
   |
   v
artifact data                 rendered HTML views
manifest.json + data/*.json   -------------------
complete machine authority -> student-default page
                            -> compact support panels
                            -> optional inspection pages
```

Stakeholders:

- students need readable course pages without internal build machinery,
- professors need enough visible status to trust resources and reviewed outputs,
- contributors need fixture/gallery views for fast manual inspection,
- agents need complete manifest-declared data without scraping HTML.

## Goals / Non-Goals

**Goals:**

- Define surface tiers for Glintstone-rendered artifacts: student-default, support-panel, inspection, and machine-only.
- Keep artifact data complete while reducing what normal pages display by default.
- Make code/notebook references, reviewed outputs, runtime/execution/cache metadata, and copied files visible only at the right level of detail.
- Add a static examples/gallery view so repository fixtures can be opened and compared quickly.
- Preserve file-serving, local static hosting, deployment-neutral links, and no-execution behavior.
- Update foundation docs, rendered docs, role guides, `AGENTS.md`, and `openspec/config.yaml` so future proposals keep this display discipline.

**Non-Goals:**

- No backend service, account system, client-side router, analytics, or personal study state.
- No browser execution, notebook execution, kernel selection, `uv`, Docker, cache refresh, or automatic `raya run`.
- No new pedagogy feature such as spaced repetition queues or mastery maps.
- No requirement that rendered HTML become the data authority for agents or future services.
- No broad theme redesign beyond the layout and visibility needed to enforce the contract.

## Decisions

### 1. Use surface tiers instead of per-feature ad hoc hiding

Rendered behavior will use a small taxonomy:

| Tier | Audience | Default page behavior |
| --- | --- | --- |
| `student-default` | students and ordinary readers | visible in normal page flow |
| `support-panel` | students/professors | compact summaries, labels, links, optional collapsed details |
| `inspection` | professors/contributors/agents | static audit pages generated from artifact data |
| `machine-only` | tools/agents/services | manifest-declared JSON and copied files, not dumped into page flow |

Rationale: new features can choose a tier without reopening the whole renderer. Alternatives considered were hard-coding behavior per feature or hiding everything behind CSS; both make future pedagogy features harder to reason about.

### 2. Keep complete data in artifacts, not in default HTML

`manifest.json` and `data/*.json` remain the machine authority. Default pages may summarize data, but hashes, source paths, artifact paths, runtime profile internals, cache keys, freshness internals, and raw JSON belong to inspection or machine surfaces.

Rationale: artifact data should remain rich enough for Sellen, Primeval Current, Rennala, launchers, and future services, while the student page remains readable. The alternative, reducing generated data to match the page, would weaken future tooling.

### 3. Render compact panels from data-backed summaries

Default pages may show generated panels for resources and reviewed outputs, but those panels should be compact:

- label, kind, title or filename,
- reviewed/not-executed/current status when relevant,
- deployment-neutral view/download links,
- short excerpt or preview only when it helps reading.

Verbose fields move to `inspection` or `machine-only`.

Rationale: students should know that a script, notebook, or reviewed result exists without reading implementation metadata. Professors and agents can still audit the full data through inspection pages or JSON.

### 4. Generate an examples/gallery surface for fixture review

Repository examples should have a static gallery or equivalent generated page that links to each fixture artifact and labels what the fixture demonstrates. The gallery is contributor-facing fixture documentation, not course canon or pedagogy.

Rationale: the project already uses multiple fixtures to test rendering. A small gallery makes manual review and future screenshot/e2e checks easier without turning examples into architecture truth.

### 5. Do not add dynamic preview as the baseline

The baseline should remain plain static files. A future `raya preview` command can wrap `python3 -m http.server` or a richer local server, but this proposal should pass with static paths and e2e tests.

Rationale: a command is useful ergonomics, but not necessary to define the display contract. Keeping it optional reduces scope and preserves portability.

## Risks / Trade-offs

- [Risk] Hiding useful information makes professor review harder. -> Mitigation: keep compact status visible and provide static inspection pages/data for full audit.
- [Risk] Surface tiers become vague labels with no tests. -> Mitigation: add e2e assertions for both positive visibility and negative leakage on representative fixtures.
- [Risk] Examples become canonical pedagogy by accident. -> Mitigation: label gallery entries as fixtures and point authority back to `docs/foundation/` and accepted specs.
- [Risk] The renderer grows too much UI before pedagogy features land. -> Mitigation: implement only the minimum shell, compact panels, and gallery needed to enforce visibility boundaries.
- [Risk] Reviewed-output contracts are still active in an unarchived change. -> Mitigation: archive or sync `define-reviewed-execution-output-baseline` before applying this change, then apply the same surface tiers to reviewed panels.
