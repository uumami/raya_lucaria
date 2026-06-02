# Charter

This document is the memory that should survive a repository wipe. It describes what Raya Lucaria is, what it must protect, and what future code must serve.

## Identity

Raya Lucaria is an open-source educational framework and commons for serious university-level learning. It is not a SaaS product, marketplace, or hosted dependency. It should be possible to run, inspect, modify, export, migrate, and self-host.

The framework exists to help people:

- publish durable course material,
- study actively instead of passively consuming content,
- preserve professor and course-team ownership,
- support student-owned notes and study artifacts,
- collaborate with visible authority boundaries,
- use coding agents and learning agents without surrendering control.

## Equal First Principles

Pedagogical quality and educational freedom are equally important.

Pedagogical quality means the system must support careful reading, retrieval, practice, reflection, adaptation, collaboration, contribution, and review. It must serve university students and professors, not only content delivery.

Educational freedom means courses, student work, schemas, artifacts, and application logic remain portable. Vendors are replaceable adapters.

## Ownership

Raya Lucaria must own its domain model:

- course source model,
- learning quanta,
- artifact manifest,
- authority domains,
- identity and registration concepts,
- validation rules,
- CLI contracts,
- dynamic-state contracts.

External tools can implement pieces, but they must not become the architecture.

## Portability

The framework must support:

- static-only course publishing,
- local development,
- one-machine self-hosting,
- institutional on-premise deployment,
- free-tier managed services,
- paid cloud infrastructure.

The static course path must remain useful without a backend.

## Agent Compatibility

Humans and coding agents should be able to operate the framework through explicit commands, files, schemas, diagnostics, and docs. Hidden manual state is a design failure.

Agents must inherit user authority. They do not get special trust because they are agents.

## From-Zero Rule

Legacy code and historical branches may be referenced for ideas, but they are not current truth. Future implementation starts from these foundation documents and newly proposed contracts.
