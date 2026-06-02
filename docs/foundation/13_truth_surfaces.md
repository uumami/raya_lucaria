# Truth Surfaces

Raya Lucaria must keep current truth separate from implementation, examples, tooling, and history.

## Authority Hierarchy

After the reset:

1. `docs/foundation/` is the seed truth.
2. Future OpenSpec specs are generated from foundation decisions.
3. Root guidance explains how to work in the current repository.
4. Package READMEs describe implemented package boundaries.
5. Examples are fixtures only.
6. Git history and old branches are historical reference.

If any lower surface conflicts with foundation docs, the lower surface is wrong until a new decision updates the foundation.

## Surface Classes

| Class | Role |
| --- | --- |
| Foundation | current architecture, pedagogy, ownership, portability, and iteration truth |
| Decision records | explicit accepted choices and rejected alternatives |
| Specs | testable requirements generated from current foundation |
| Package docs | status and ownership of implemented packages |
| Examples | minimal fixtures, never pedagogy by accident |
| Tooling adapters | workflow support for agents/editors |
| History | inspiration and recovery, not current authority |

## Reset Discipline

Do not preserve stale material in the current tree just because it exists. If old code or docs contain a useful idea, copy the principle into a current proposal and rebuild it under current contracts.

## What May Be Deleted

On a from-zero reset, it is acceptable to delete:

- legacy implementation packages,
- legacy examples,
- generated artifacts,
- archived specs,
- old role guides,
- old renderer documentation,
- stale workflows.

The foundation docs are the surviving memory.
