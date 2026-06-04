---
id: docs-pedagogy
title: Pedagogy
summary: Learning-first design principles and the minimum surfaces for later study systems.
status: ready
---
# Pedagogy

Raya Lucaria exists to support learning, not only content delivery. It should help university students read carefully, retrieve knowledge, practice, reflect, adapt, collaborate, and contribute.

## Core Learning Loop

```text
+--------+     +----------+     +---------+
| Read   | --> | Retrieve | --> | Reflect |
+--------+     +----------+     +----+----+
                                     |
                                     v
+------------+   +---------+   +----------+
| Contribute | <-| Revisit | <-|  Adapt   |
+------------+   +---------+   +----------+
```

Every feature should make clear which part of the loop it supports.

## Minimum Learning Requirements

The first implementation should not attempt every pedagogical feature. It must establish the minimum surfaces that make later learning systems possible:

- readable course material,
- clear learning quanta,
- official cards, quizzes, prompts, examples, assignments, and projects,
- retrieval-practice hooks tied to course source,
- authority labels for official, personal, shared, and generated material,
- validation that catches broken learning objects before build,
- generated indexes that future study and agent domains can read.

This minimum is a floor. The framework should grow when a new capability improves the learning loop and can be expressed through explicit contracts.

## Course-Provided Base

The course team can provide shared starting points:

- readings and explanations,
- official flashcards,
- official quizzes,
- retrieval prompts,
- worked examples,
- study paths,
- project scaffolds.

These materials should give every student a common base while still allowing personal adaptation.

## Pedagogy-Driven Growth

Raya Lucaria should grow from static learning objects toward richer study systems without losing portability.

```text
official learning objects
        |
        v
retrieval practice hooks
        |
        v
personal study state
        |
        v
adaptive review and spaced repetition
        |
        v
mastery signals and study planning
```

Rennala starts with official cards, quizzes, and prompts. It can later add personal cards, review queues, spaced repetition, confidence ratings, mastery maps, and exam preparation. Those later features need dynamic state, but the official base should remain readable and exportable as course source.

Growth should be staged:

- first define the learning object contract,
- then validate source and artifact outputs,
- then add personal state,
- then add adaptive behavior,
- then add analytics or recommendations.

Analytics must serve learning and teaching, not surveillance. Aggregated course signals are safer defaults than individual monitoring.

## Personalization

Personalization can happen through:

- student-created private notes,
- student-created cards and summaries,
- adaptive review queues,
- agent-generated drafts,
- professor-generated common materials,
- shared peer artifacts.

Generated and personalized material must be labeled so students know whether it is official, private, shared, or machine-generated.

## Agents In Learning

Agents should deepen learning rather than replace it.

Useful modes include:

- Socratic questioning,
- alternative explanations,
- retrieval-practice generation,
- answer comparison,
- flashcard drafting,
- study planning,
- local code/content assistance.

For university work, the system should preserve reasoning, evidence, revision, and responsibility. A final answer is less valuable than a process students can inspect and improve.

Agent features should also grow from contracts. Sellen should first know how to assemble course context and respect authority boundaries. Later it can draft cards, compare answers, guide retrieval practice, and help plan study. Generated material stays a draft until reviewed or explicitly saved by the user in the right authority domain.

## Research Posture

This foundation does not fix one pedagogy. Future features should be research-informed and should distinguish required framework behavior from optional teaching patterns.
