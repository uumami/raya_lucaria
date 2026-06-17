---
id: docs-learning-science-principles
title: Learning Science Principles
summary: Evidence-backed learning principles used to shape Raya static and future study experiences.
status: ready
---
# Learning Science Principles

Raya Lucaria is learning-first without requiring one teaching doctrine. These principles name the evidence Raya uses when shaping static course pages, future study tools, and guidance for course teams.

This page is foundation truth for learning intent. It does not make every principle current renderer behavior.

The core phrases for this contract are cognitive load, retrieval practice,
spaced practice, self-explanation, and universal design.

## Status Labels

Use three status labels when mapping learning science into Raya behavior:

| Status | Meaning |
| --- | --- |
| `current` | Supported by the current source contract, artifact data, or static renderer. |
| `planned` | Desired and designed, but requiring a later accepted source, artifact, or renderer change. |
| `future` | Requires dynamic study state, accounts, analytics, adaptive review, collaboration, or another package boundary. |

## Cognitive Load

Cognitive load is the pressure placed on working memory. Following Sweller, Raya should reduce extraneous load, expose course structure, and support schema formation without hiding real subject complexity.

Current static pages can help by using stable regions, predictable navigation, concise summaries, local support panels, clear object labels, and restrained visual styling. They should not add decoration, surprise layout shifts, or verbose internals to the normal reading path.

## Coherence, Signaling, And Segmenting

Mayer's coherence, signaling, and segmenting principles support pages that remove irrelevant material, mark important organization, and split material into manageable pieces.

Raya pages should make page title, course position, prerequisites, page contents, numbered objects, and next links easy to scan. Long explanations belong in authored article content. Machine details belong in `manifest.json`, `data/*.json`, copied support files, or `_raya/inspect/` pages.

## Retrieval Practice

Retrieval practice improves durable learning when students recall, test, explain, or apply knowledge instead of only rereading. Roediger and Karpicke are the main evidence anchor for this principle.

In the current static baseline, retrieval practice appears as authored prompts, problems, checkpoints, hints, solutions, answers, examples, and official learning objects. Static HTML may show those surfaces, but it must not claim scoring, mastery, completion, or personal progress.

## Spaced Practice And Interleaving

Spaced practice distributes review over time. Interleaving mixes problem types so students practice choosing methods, not only repeating one pattern. Dunlosky and Bjork are the main evidence anchors for this area.

Current static pages can preserve explicit prerequisites, previous/next links, and authored review prompts. Related practice indexes are planned only when accepted source and artifact data exist. Spaced queues, adaptive schedules, and personal review state are future study features.

## Worked Examples And Fading

Worked examples reduce unnecessary search for novices. A common progression is concept, worked example, partially completed example, independent practice, then mixed review.

Raya should make examples, problems, hints, solutions, answers, proofs, and explanations scannable without turning them into hidden dynamic behavior. Fading is an authoring pattern today, not an automatic renderer transformation.

## Self-Explanation

Self-explanation asks students to explain why a step follows, what assumption changed, or how an example relates to a principle. Chi is the main evidence anchor for this principle.

Raya can support self-explanation through authored checkpoint prompts, callouts, problems, and static environments. The renderer should present these prompts clearly, but it must not infer goals or exercises from prose.

## Metacognition And Calibration

Students benefit when they compare confidence with performance and notice what they can or cannot yet do.

Current static pages can ask calibration questions and provide answer or solution material. Personal confidence logs, analytics, mastery estimates, adaptive review, and instructor dashboards are future work because they require study state.

## Motivation, Autonomy, Relevance, And Belonging

Students persist more readily when work has visible purpose, appropriate challenge, meaningful choice, and signs that they belong in the learning environment.

Raya should let course teams write relevant examples, choose humane reading structures, and keep official expectations clear. It should not hide authority labels, invent goals, or make progress claims that a static page cannot support.

## Universal Design And Accessibility

Universal design and accessibility help more students participate without separate remediation. CAST UDL and WCAG are the main anchors for this area.

Current static behavior should preserve semantic HTML, keyboard-reachable controls, high contrast, local `OpenDyslexic` resources, stable links, readable line lengths, local assets, and no external renderer requests. Accessibility work is continuous: a page can be valid and still need better authoring.

## Static HTML Boundary

Static HTML can honestly provide:

- course maps, page contents, previous/next links, and stable navigation;
- authored summaries, status labels, prerequisites, examples, prompts, and support blocks;
- build-time MathJax, numbered objects, static environments, code display, tables, callouts, and local assets;
- local accessibility controls and deployment-neutral links.

Static HTML cannot honestly provide by itself:

- personal progress, mastery, analytics, or completion state;
- adaptive review, spaced queues, or per-student recommendations;
- inferred goals, hidden assignments, or related practice derived from prose;
- browser-side MathJax conversion or external CSS, font, script, renderer, or CDN dependencies.

Future dynamic features should keep this learning target, but they need accepted contracts in the relevant package boundaries before becoming current behavior.
