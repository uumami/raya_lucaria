# Raya Lucaria — Vision Document

This document captures the full vision for evolving sellen into Raya Lucaria, an integrated learning platform. Written as a reference for the migration to a new repository and architectural redesign.

---

## Rebranding

| Current | New | Role |
|---------|-----|------|
| sellen (everything) | **Raya Lucaria** | The platform / academy |
| — | **Glintstone** | Content engine (current sellen core) |
| — | **Primeval Current** | Knowledge graph, backlinks, connections |
| — | **Rennala** | Study & mastery tools (learning science) |
| — | **Debate Parlor** | Live classroom interaction |
| — | **Sellen** | AI assistant / tutor |
| — | **Graven School** | Social & collaborative layer |
| — | **Glintstone Key** | Authentication (the key to enter the academy) |

---

## Architecture Overview

Two fundamental layers:

- **Static layer** — Course content, knowledge graph, search, PDFs. Free to host (GitHub Pages), works forever, no server. This is Glintstone + Primeval Current.
- **Dynamic layer** — Auth, student notes, study tools, live classroom, AI, social features. Needs a backend (Supabase free tier + optional small AWS backend for WebSockets).

The static site works perfectly on its own. The dynamic layer is progressive enhancement — students who log in get additional features. A professor can use only Glintstone and still have a better course site than 99% of what exists.

```
Raya Lucaria (the platform)
├── Glintstone        — content engine, build pipeline, static site
├── Primeval Current  — knowledge graph, backlinks, wikilinks
├── Rennala           — study tools, SRS, retrieval practice, metacognition
├── Debate Parlor     — live classroom, polls, Q&A, real-time
├── Sellen            — AI assistant, chatbot, Socratic tutor (BYOK)
└── Graven School     — social, discussions, peer learning, shared content
```

---

## Layer Details

### Glintstone — Content Engine

**What it is:** The current sellen framework. A static site generator that turns markdown into a themed, navigable course website.

**What it does:**
- Professor writes markdown with YAML frontmatter
- Python preprocessing extracts metadata, generates navigation hierarchy, aggregates tasks, writes JSON data files
- Eleventy builds HTML from Markdown + Nunjucks templates
- Tailwind CSS generates styles with 12 themes in 6 families
- esbuild bundles JavaScript
- Pagefind generates search index
- Output is a fully static site

**Components:** Eight types — homework, exercise, prompt, example, exam, project, quiz, embed. Structured attributes with `:::type{key="value"}` syntax. Components with IDs (homework, exam, project) aggregate to task pages.

**Key properties:**
- Zero backend required
- Free hosting on GitHub Pages
- 12 visual themes (dark/light pairs)
- Accessibility: OpenDyslexic font, size toggle, keyboard navigation
- Responsive layout with collapsible sidebar
- PDF embedding, math (KaTeX), diagrams (Mermaid)
- PWA with offline support
- Print stylesheet

**Current state:** Fully implemented and working.

---

### Primeval Current — Knowledge Graph

**What it is:** The layer that makes connections between pieces of knowledge visible. Wikilinks for authoring, backlinks for discovery, graph visualization for exploration.

**Features to build:**

1. **Wikilink resolution** — Professors write `[[topic-name]]` instead of relative paths like `../../03_chapter/02_topic.md`. During preprocessing, wikilinks are resolved to the correct URL by filename lookup. Massive quality-of-life improvement for content authoring.

2. **Backlinks** — Every page gets a "Referenced by" section at the bottom listing all other pages that link to it. Generated at build time by building an inverted index of all internal links. Students discover connections they wouldn't find reading linearly.

3. **Interactive graph view** — A `/grafo/` page with a force-directed visualization (d3.js or sigma.js). Nodes are pages, edges are links between them. Students can:
   - See the entire course topology
   - Identify clusters of related topics
   - Find central concepts that connect many areas
   - Discover paths between ideas they thought were unrelated
   - Click nodes to navigate to pages

4. **Link data extraction** — During preprocessing, scan all markdown files for internal links (both standard markdown links and wikilinks). Build an adjacency matrix. Output as static JSON consumed by the graph visualization and backlinks template.

**Implementation approach:**
- All build-time, no backend needed
- Link extraction in Python preprocessing (new module)
- Graph data written as JSON to `_data/`
- Backlinks rendered in base.njk template
- Graph page is a standalone HTML page with d3.js reading the JSON
- Wikilinks resolved as a preprocessing transform before Eleventy

**Cost:** $0 (fully static)

---

### Rennala — Study & Mastery Tools

**What it is:** Evidence-based learning tools grounded in cognitive psychology. Fights the forgetting curve with spaced repetition, builds genuine understanding through retrieval practice, develops metacognitive skills.

**Features to build:**

1. **Spaced repetition flashcards**
   - SM-2 algorithm (or similar) for scheduling
   - Per-card per-student tracking: ease factor, interval, next review date
   - Cards resurface right before the student would forget
   - Students can create their own cards or use auto-generated ones
   - Schema: `(user_id, card_id, page_url, front, back, ease, interval, next_review, created_by)`

2. **Retrieval practice quizzes**
   - Quick quizzes per page ("test yourself on this section")
   - 3-5 questions generated from content
   - Free recall exercises: blank text box, "write everything you remember about this topic"
   - Answers compared against source material (by AI or simple keyword matching)

3. **Metacognition tools**
   - Confidence ratings on flashcards and quiz answers (Easy / Hard / Forgot)
   - Calibration tracking: are students overconfident or underconfident?
   - Pre-quiz predictions ("how well do you think you'll do?") vs actual score

4. **Knowledge heatmap**
   - Visual dashboard showing mastery per topic
   - Based on retrieval success rates and time since last review
   - Green = strong retention, yellow = moderate, red = decaying
   - Uses forgetting curve math to estimate current retention

5. **Forgetting curve visualization**
   - Shows estimated retention over time per topic
   - Visual motivation for why reviewing matters

6. **Exam preparation**
   - Identifies weak areas from heatmap
   - Generates targeted practice focused on what the student struggles with
   - Given an exam date, can suggest a study schedule (with AI help)

**Implementation approach:**
- Needs authentication (Glintstone Key / Supabase Auth)
- Student state stored in Supabase Postgres (free tier: 500MB, millions of records)
- SRS scheduling logic runs client-side in JavaScript
- Knowledge heatmap is a client-side visualization from student data
- Quiz questions can be static (authored by professor) or AI-generated (Sellen layer)

**Cost:** $0 (Supabase free tier)

---

### Debate Parlor — Live Classroom

**What it is:** Synchronous tools the professor uses during lectures. Turns passive audiences into active participants.

**Features to build:**

1. **Polls**
   - Multiple choice, scale (1-5), word cloud
   - Professor creates question, students respond from devices
   - Results aggregate in real time
   - Professor sees distribution instantly

2. **Open-ended questions**
   - Students type short text answers
   - Professor sees live feed
   - Can surface interesting responses anonymously to the class

3. **Confusion indicator**
   - Simple button students press when lost
   - Professor sees real-time percentage of confused students
   - Honest signal that requires no hand-raising

4. **Pace feedback**
   - "Too fast" / "Good" / "Too slow"
   - Professor adjusts in real time

5. **Live Q&A**
   - Students submit questions
   - Others upvote
   - Most pressing questions rise to top
   - Professor addresses top questions

**Properties:**
- Ephemeral by default — belongs to the class session, not permanent record
- Professor controls when features are active (opens/closes polls, etc.)
- Works on mobile (students use phones in class)

**Implementation approach:**
- Needs WebSocket or real-time subscription
- Option A: Supabase Realtime (write to table, subscribe to changes) — simplest
- Option B: AWS API Gateway WebSocket + Lambda — more control, small cost
- Session management: professor creates a "class session," students join with a code
- Data schema: `sessions`, `poll_questions`, `poll_responses`, `qa_questions`, `qa_upvotes`, `confusion_signals`, `pace_signals`

**Cost:** $0 with Supabase Realtime, or ~$1-5/month on AWS

---

### Sellen — AI Assistant

**What it is:** A personal AI tutor that has access to all course content. Students bring their own API key (BYOK) — zero cost for the professor.

**Features to build:**

1. **Context-aware chat**
   - Student asks a question in a chat panel (sidebar or floating widget)
   - Pagefind searches course content with the question
   - Primeval Current graph provides related pages via link traversal
   - Top results become the LLM context
   - AI answers using actual course material, cites specific pages with links

2. **Socratic mode**
   - Instead of answering, the AI asks guiding questions
   - Leads the student to figure out the answer themselves
   - Based on the pedagogical principle that active reasoning > passive receiving

3. **Explain mode**
   - "Explain like I'm five" button on any section
   - Simplifies content to a more accessible level
   - Multiple explanation styles (analogy, step-by-step, visual description)

4. **Practice generation**
   - AI reads a page and generates practice questions
   - Worked examples with step-by-step solutions
   - Alternative explanations of the same concept
   - Can feed into Rennala's flashcard system

5. **Answer comparison**
   - In free-recall exercises, AI compares what the student wrote against source material
   - Identifies what they got right, what they missed, what they got wrong
   - Constructive feedback with links to relevant sections

6. **Study plan generation**
   - Given an exam date and the student's knowledge heatmap (from Rennala)
   - Produces a day-by-day study schedule
   - Prioritizes weak areas
   - Accounts for spaced repetition intervals

**The BYOK (Bring Your Own Key) architecture:**
- Student picks their LLM provider: Cerebras, Mistral, Groq, OpenAI, etc.
- Pastes their API key in a settings page
- Key stored in browser localStorage — never touches a server
- LLM calls happen directly from browser to API (all providers support CORS or have JS SDKs)
- All providers use OpenAI-compatible API format — one interface, multiple backends
- Free/cheap tiers exist on most providers

**The cheapest RAG that works:**
1. Student asks a question
2. Client-side JS runs Pagefind search with the question
3. Pagefind returns top 5 matching content chunks (already indexed at build time)
4. Graph traversal (Primeval Current) adds related pages as additional context
5. Chunks + system prompt → LLM API call from browser
6. Response streams back to the chat panel

No embeddings. No vector database. No server. Pagefind IS the retrieval engine.

**Advanced RAG (future):**
- Pre-compute embeddings of all content chunks at build time
- Store as static JSON or use Supabase pgvector (free tier supports it)
- Client-side cosine similarity for retrieval
- Better semantic matching than keyword search

**Cost:** $0 for the professor. Students pay their own API costs (typically pennies per conversation on cheap providers).

---

### Graven School — Social & Collaborative

**What it is:** Collaborative learning features. Many minds working together.

**Features to build:**

1. **Discussion threads**
   - Every page has an optional thread
   - Students ask questions, answer each other
   - Professor can pin responses or mark as correct
   - Threaded replies

2. **Peer explanations**
   - Students write their own explanation of a concept
   - Others rate explanations as helpful
   - Best explanations surface to the top
   - A peer who understood it 10 minutes ago sometimes explains better than the textbook

3. **Shared annotations**
   - Students highlight passages and attach notes
   - Can mark notes as public
   - When many students mark the same passage as confusing, that signal becomes visible
   - Professor sees aggregated confusion signals per section

4. **Student-generated flashcards**
   - Students create flashcards that can be shared with the class
   - Crowdsourced study material grows over the semester
   - Peer-reviewed: others can rate card quality

5. **Study groups**
   - Students form groups
   - Shared flashcard decks, annotations, discussion threads
   - Group progress tracking

6. **Professor analytics (aggregated, not individual surveillance)**
   - "72% of students struggled with this question"
   - "Most common question about Chapter 5 is about amortized analysis"
   - "Average confidence on this topic is 2.1/5"
   - "This page has the most confused-note annotations"
   - Patterns that tell the professor what to reteach

**Implementation approach:**
- Builds on Glintstone Key auth and Supabase database
- Tables: `discussions`, `replies`, `annotations`, `shared_cards`, `study_groups`, `group_members`, `votes`
- Real-time updates for discussions (Supabase Realtime)
- Aggregation queries for professor analytics

**Cost:** $0 (Supabase free tier)

---

### Glintstone Key — Authentication

**What it is:** The key that gets you into the academy. Unlocks all interactive features beyond the public static content.

**Implementation:**
- Supabase Auth (free tier: 50,000 monthly active users)
- Providers: GitHub OAuth (natural for ITAM CS students), Google OAuth, email/password
- The static site (Glintstone) works without auth — it's always public
- Logging in unlocks: Rennala (study tools), Debate Parlor (live features), Graven School (social), Sellen (AI with persistent history)
- Student identity: `(user_id, display_name, email, provider, created_at)`
- Optional: course enrollment (professor generates invite codes)

**Privacy:**
- Student notes and study data are private by default
- Social features are opt-in (students choose what to share)
- Professor sees aggregated analytics, not individual student data (unless student explicitly shares)
- API keys never leave the browser

---

## Technology Stack

| Component | Technology | Cost |
|-----------|------------|------|
| Static site hosting | GitHub Pages | Free |
| Auth | Supabase Auth | Free (50k MAU) |
| Database | Supabase Postgres | Free (500MB) |
| File storage | Supabase Storage | Free (1GB) |
| Real-time | Supabase Realtime | Free |
| Serverless functions | Supabase Edge Functions or AWS Lambda | Free tier |
| WebSocket (if needed) | AWS API Gateway WebSocket | ~$1-5/mo |
| LLM | Student's own API key (BYOK) | $0 for platform |
| Search | Pagefind (static) | Free |
| Graph visualization | d3.js or sigma.js | Free |
| Content build | Python + Eleventy + Tailwind + esbuild | Free |

**Total estimated cost:** $0-5/month

---

## Implementation Phases

### Phase 1 — Primeval Current (static, no backend)
- Wikilink resolution in preprocessing
- Backlinks section on every page
- Interactive graph page at `/grafo/`
- PDF embedding and text extraction for search
- Callout syntax (`> [!tip]`, `> [!warning]`)
- Tag index pages

**Outcome:** Sellen becomes a knowledge-graph-aware course framework. Still fully static.

### Phase 2 — Rennala (study tools, needs auth)
- Supabase integration: Glintstone Key authentication
- Spaced repetition flashcards with SM-2 scheduling
- Per-page retrieval quizzes
- Confidence ratings and metacognition tracking
- Knowledge heatmap dashboard
- Student notes panel (per-page, syncs across devices)
- Student can export all their data as markdown/JSON

**Outcome:** Students have evidence-based study tools integrated with course content. No other LMS provides this.

### Phase 3 — Debate Parlor (live classroom)
- Live polls (multiple choice, scale, word cloud)
- Open-ended questions with live response feed
- Confusion indicator and pace feedback
- Live Q&A with upvoting
- Session management (professor creates session, students join)

**Outcome:** Replaces Kahoot, Mentimeter, and parts of Piazza. Integrated with the course content.

### Phase 4 — Sellen (AI assistant, BYOK)
- Chat panel in sidebar or floating widget
- Settings page: pick provider, paste API key
- Pagefind-based retrieval for context
- Graph-aware context expansion via Primeval Current
- Socratic mode and explain mode
- Practice question generation
- Answer comparison for free-recall exercises
- Study plan generator

**Outcome:** Every student has a personal AI tutor that knows the course material. Zero cost for the professor.

### Phase 5 — Graven School (social/collaborative)
- Per-page discussion threads
- Peer explanations with voting
- Shared annotations
- Student-generated flashcard sharing
- Study groups
- Aggregated analytics for professor

**Outcome:** Isolated studying becomes collective intelligence. Replaces Piazza/Ed Discussion.

---

## What Makes This Different

1. **Professor-owned.** Not a SaaS platform that can raise prices, change terms, or disappear. The professor owns the content (markdown files), the build pipeline (open source), and the deployment (their own GitHub Pages).

2. **Content-first.** The content exists as plain markdown files. It works without the platform. You can read it in a text editor, in Obsidian, in VS Code. The platform enhances it but doesn't own it.

3. **Free to run.** $0/month for a full-featured course site with study tools, live classroom, AI tutoring, and social features. The only variable cost is LLM tokens, paid by the students from their own API keys on providers they choose.

4. **Built on learning science.** Not "we added AI because it's trendy." Spaced repetition, retrieval practice, metacognition, interleaving, desirable difficulty — these are the most evidence-backed techniques in cognitive psychology. The AI enhances them but doesn't replace them.

5. **The knowledge graph.** No other course framework visualizes the connections between topics as a navigable graph. This alone is a differentiator.

6. **Progressive enhancement.** Works as a static site (Phase 0/current). Each phase adds capabilities without breaking what came before. A professor can stop at any phase and have a useful, complete product.

---

## Migration Notes

- Current repo: `sellen` — contains Glintstone (the content engine) in its current form
- Plan: migrate to new repo under the name `raya-lucaria`
- Glintstone engine will be a module/package within Raya Lucaria
- The current `sellen` name will be reused specifically for the AI assistant layer
- All current features (themes, components, build pipeline, PWA, etc.) carry over as Glintstone
- New features build on top as separate layers with clear boundaries
- The existing 7-feature pack (print, reading time, quiz, embed, announcements, slides, PWA) ships with Glintstone

---

## Lore Reference

All naming is based on the Academy of Raya Lucaria from Elden Ring:

- **Raya Lucaria** — The grand academy of glintstone sorcery in Liurnia of the Lakes
- **Glintstone** — Magical material from the stars, the foundation of all sorcery at the academy
- **Primeval Current** — The fundamental cosmic flow connecting all sorcery, studied by the Primeval Sorcerers Azur and Lusat
- **Rennala** — Queen of the Full Moon, head of the academy, offers rebirth in the Grand Library
- **Debate Parlor** — Location inside the academy where scholars held intellectual debates
- **Sellen** — Sorceress and teacher, exiled from the academy for pursuing forbidden knowledge, ran a secret academy guiding students one-on-one
- **Graven School** — Creation of Sellen: multiple sorcerers' minds fused into a unified consciousness, many minds as one
- **Glintstone Key** — The key required to enter the academy gates
