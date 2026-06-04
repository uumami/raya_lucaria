---
id: docs-legacy-salvage
title: Legacy Salvage
summary: Principles worth keeping from old code without preserving old architecture.
status: ready
---
# Legacy Salvage

Old code and branches are historical reference. They are not current truth. If useful behavior is needed, copy the idea intentionally into new code after a proposal.

## Keep The Principles

The previous implementation proved several useful ideas:

- static courses are valuable without a backend,
- course source should be plain files,
- validation should happen before build,
- generated artifacts should be rebuildable,
- navigation can come from directory structure,
- links and backlinks are educationally useful,
- tasks/cards/quizzes should be structured data, not only prose,
- local assets and relative links matter,
- build output must be separate from source,
- tests around parsing, hierarchy, links, and validation are valuable,
- accessibility features should be part of the baseline,
- docs and code-agent guidance must be explicit.

These ideas survive.

## Do Not Carry Forward By Default

Do not preserve these as architecture:

- old source directory names,
- old course directory names,
- old config filenames except as migration references,
- old renderer stack choices,
- old generated JSON shapes,
- old theme systems,
- old role guides,
- old examples as pedagogy,
- old package names as mandatory public names.

They can be mined, not inherited.

## Salvage Method

When old code contains useful behavior:

1. Describe the principle in a proposal.
2. Define the new contract.
3. Copy or rewrite the smallest useful idea.
4. Add tests against the new contract.
5. Avoid importing legacy assumptions silently.

The test is simple: a new contributor should understand the feature from current docs and specs without reading old branches.
