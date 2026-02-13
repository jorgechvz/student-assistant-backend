# Project Requirements & Scope

## Project Title

**Student Learning Assistant — Loop**

## Project Summary

Loop is an AI-powered student learning assistant built as a chatbot that helps students manage their academic experience across active courses. The assistant focuses on improving organization, planning, and understanding of course content — **not** completing assignments for students.

## Goals

1. **Centralized Course Management** — Provide a single interface where students can query information about all their courses, assignments, grades, and deadlines.

2. **Intelligent Study Planning** — Generate personalized study plans and calendar events based on course workload and deadlines.

3. **Structured Note-Taking** — Create organized study notes, summaries, and assignment trackers that students can reference throughout the semester.

4. **Academic Integrity** — Ensure the assistant never completes academic work on behalf of students, instead guiding them toward independent learning.

5. **Seamless Integration** — Connect with tools students already use (Canvas LMS, Google Calendar, Notion) without requiring them to switch platforms.

## Assumptions

- Students have access to Canvas LMS through their institution.
- Students have Google accounts for Calendar integration.
- Students have or are willing to create Notion accounts for note-taking.
- The institution's Canvas instance allows personal access token generation.
- Students have reliable internet access to use the web-based assistant.

## Constraints

- The system must comply with academic integrity policies.
- The system relies on third-party APIs (Canvas, Google, Notion) which may have rate limits or downtime.
- Azure OpenAI usage is subject to token-based pricing.
- The assistant cannot access assignment submission content or peer data.
- OAuth tokens must be stored securely and transmitted only over encrypted channels.

## Non-Goals

The following are explicitly **out of scope**:

- ❌ Completing homework, essays, quizzes, or exams for students.
- ❌ Grading or evaluating student submissions.
- ❌ Accessing other students' data or grades.
- ❌ Acting as a replacement for instructors or teaching assistants.
- ❌ Providing medical, legal, or personal counseling.
- ❌ Supporting non-academic tasks (entertainment, social media, etc.).
- ❌ Mobile native application (web-only for this version).

## Measurable Objectives

| Objective | Target | Measurement |
|-----------|--------|-------------|
| Course information retrieval | 100% of enrolled courses | Verified against Canvas API for pilot users |
| Automated study session creation | ≥ 5 sessions/week | Count of calendar events created per active user |
| Structured study note generation | ≥ 10 content items | Count of Notion pages created across test scenarios |
| Study plan prioritization | Documented algorithm | Architecture documentation + test cases |
| Misuse prevention | 100% block rate | 15 predefined misuse scenarios (see evaluation plan) |
| Technical documentation | Complete | Architecture diagrams, API docs, setup guide, ADRs |

## Stakeholders

| Role | Responsibility |
|------|----------------|
| Developer (Jorge Chavez) | Full-stack design, development, testing, documentation |
| Academic Advisor | Project oversight and evaluation |
| Pilot Students | User testing and feedback |

## Objective Fulfillment

For detailed evidence of how each measurable objective was met, see the [Evaluation Results — Measurable Objectives Fulfillment](evaluation-results.md#7-measurable-objectives-fulfillment) section.

| Objective | Fulfilled By |
|-----------|-------------|
| Course information retrieval (100%) | Canvas tools (7 functional tests passed) — [Eval Results §1.1](evaluation-results.md#11-course-information-retrieval) |
| Study session creation (≥5/week) | Google Calendar tools (7 tests passed) — [Eval Results §1.2](evaluation-results.md#12-calendar--study-planning) |
| Study note generation (≥10 items) | Notion tools (5 tests passed) — [Eval Results §1.3](evaluation-results.md#13-notion-integration) |
| Study plan prioritization | Documented in [ADR-007](adrs/007-tool-based-integrations.md) + tested in [Eval Results §1.2](evaluation-results.md#12-calendar--study-planning) |
| Misuse prevention (100%) | 15/15 scenarios passed — [Eval Results §2](evaluation-results.md#2-safety--misuse-prevention-results) |
| Technical documentation | 8 docs + 10 ADRs — [Documentation Index](README.md) |

---

## Integration Map

```
┌─────────────────────────────────────────────-┐
│              Loop (Backend API)              │
├─────────────┬──────────────-┬────────────────┤
│  Canvas LMS │ Google Cal    │    Notion      │
│  (Read)     │ (Read/Write)  │  (Read/Write)  │
├─────────────┼────────────── ┼────────────────┤
│ • Courses   │ • Events      │ • Pages        │
│ • Assigns   │ • Scheduling  │ • Databases    │
│ • Grades    │ • Reminders   │ • Study notes  │
│ • Syllabus  │ • Timezone    │ • Trackers     │
│ • Announce  │ • Availability│ • Plans        │
└─────────────┴──────────────-┴────────────────┘
```
