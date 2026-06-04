---
id: docs-system-model
title: System Model
summary: Source, artifacts, dynamic state, deployment, and user experience boundaries.
status: ready
---
# System Model

Raya Lucaria separates source, artifacts, dynamic state, and deployment.

```text
                         RAYA LUCARIA
              open educational framework and commons

+-------------------+       +------------------------+
| Course Source     |<----->| Course Team            |
| raya.yaml/course  |       | review, canon, quality |
+---------+---------+       +------------------------+
          |
          v
+-------------------+       +------------------------+
| Static Builder    |------>| Course Artifact        |
| fresh package     |       | site + manifest + data |
+---------+---------+       +------------------------+
          |
          v
+----------------------------------------------------+
| Student Learning Experience                        |
| read, retrieve, practice, reflect, ask, contribute |
+---------+------------------+-----------------------+
          |                  |
          v                  v
+-------------------+  +-----------------------------+
| Local Workspace   |  | Optional Shared Installation |
| notes, drafts,    |  | auth, sync, realtime,        |
| cards, agents     |  | study data, community        |
+-------------------+  +-----------------------------+
```

## Source Course

A source course is a portable file tree. It contains canonical course material, configuration, official learning objects, media, and guidance. It can be edited by hand, through a web UI, or with coding-agent help, but official changes require review.

## Course Artifact

A course artifact is the built output. It includes a static site plus a manifest and generated data indexes. Optional dynamic services read the manifest and generated data; they do not scrape rendered HTML as authority.

## Optional Shared Installation

An installation is a deployed dynamic environment that can serve many courses. It can provide identity, sync, study state, realtime classroom tools, collaboration, review queues, and agent workflows.

Courses must remain useful without an installation.

## User Workflows

```text
professor / student / agent output
              |
              v
        classify intent
              |
   +----------+----------+----------------+
   |                     |                |
   v                     v                v
private save      shared artifact   proposed canon
notes/cards       discussion/card   review queue/PR
```

Every save or publish action must preserve authority: official, personal, shared, generated, or accepted.

## Canonical Update Flow

```text
web draft / local patch / agent output
              |
              v
        proposed change
              |
              v
        course team review
              |
              v
      canonical source update
              |
              v
        static rebuild
              |
              v
        updated artifact
```

Git is a strong canonical path, but GitHub access must not be required for everyday teaching and learning.
