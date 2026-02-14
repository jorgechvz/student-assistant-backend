# Evaluation Plan & Test Cases

## Overview

This document defines the evaluation framework for the Student Learning Assistant (Loop). It covers functional accuracy, safety validation, integration correctness, and performance benchmarks.

> 📊 **For executed test results, see [Evaluation Results](evaluation-results.md).**

---

## 1. Functional Accuracy Tests

### 1.1 Course Information Retrieval

| #   | Test Case                | Input                                    | Expected Output                              | Status |
| --- | ------------------------ | ---------------------------------------- | -------------------------------------------- | ------ |
| 1   | List enrolled courses    | "What courses am I taking?"              | Returns all active Canvas courses            |        |
| 2   | Assignment lookup        | "What's due this week?"                  | Lists assignments with due dates from Canvas |        |
| 3   | Grade retrieval          | "How am I doing in <course name>?"       | Returns current grades/scores                |        |
| 4   | Syllabus access          | "Show me the syllabus for <course name>" | Returns syllabus content from Canvas         |        |
| 5   | Announcement query       | "Any new announcements?"                 | Lists recent course announcements            |        |
| 6   | Flexible course matching | "What's due in <course name>?"           | Matches course by name, not just ID          |        |
| 7   | Multi-course overview    | "Give me an overview of all my courses"  | Aggregates data across all enrolled courses  |        |

### 1.2 Calendar & Study Planning

| #   | Test Case             | Input                                         | Expected Output                        | Status |
| --- | --------------------- | --------------------------------------------- | -------------------------------------- | ------ |
| 8   | Create study session  | "Schedule a study session for Friday"         | Creates Google Calendar event          |        |
| 9   | Check availability    | "Am I free tomorrow afternoon?"               | Returns available time slots           |        |
| 10  | Auto-reminders        | Create any event                              | Auto-adds 24h + 1h reminders           |        |
| 11  | Timezone detection    | Schedule event (any timezone)                 | Uses user's Google Calendar timezone   |        |
| 12  | Study plan generation | "Create a study plan for my exam next Friday" | Generates multi-day plan with sessions |        |
| 13  | Conflict detection    | Schedule during existing event                | Warns about conflict                   |        |
| 14  | Past date prevention  | "Schedule something for yesterday"            | Rejects with explanation               |        |

### 1.3 Notion Integration

| #   | Test Case             | Input                             | Expected Output                              | Status |
| --- | --------------------- | --------------------------------- | -------------------------------------------- | ------ |
| 15  | Create study notes    | "Create notes for Chapter 5"      | Creates formatted Notion page                |        |
| 16  | Assignment tracker    | "Create an assignment tracker"    | Creates table with due dates, status columns |        |
| 17  | Parent page selection | "Save notes to my Studies page"   | Creates page under correct parent            |        |
| 18  | Markdown rendering    | Notes with headers, lists, tables | Properly rendered in Notion                  |        |
| 19  | Search pages          | "Find my calculus notes"          | Returns matching Notion pages                |        |

---

## 2. Safety & Misuse Prevention Tests

See [Academic Integrity & Misuse Prevention](academic-integrity.md) for the complete set of 15 misuse test scenarios.

**Summary Criteria:**

- 100% refusal rate for prohibited actions
- 100% offer rate for alternative tool-based help
- 0% judgmental or dismissive responses

---

## 3. Integration Reliability Tests

| #   | Test Case                      | Expected Behavior                                            | Status |
| --- | ------------------------------ | ------------------------------------------------------------ | ------ |
| 20  | Canvas token expired           | Graceful error message, suggest reconnecting                 |        |
| 21  | Google token expired           | Auto-refresh, retry the operation                            |        |
| 22  | Notion disconnected            | Agent operates without Notion tools, suggests connecting     |        |
| 23  | All integrations disconnected  | Shows `no_integrations` prompt, suggests connecting services |        |
| 24  | Canvas API rate limit          | Retry with backoff, inform user of delay                     |        |
| 25  | Invalid Canvas base URL        | Clear error message during setup                             |        |
| 26  | Multiple concurrent tool calls | No race conditions, all calls complete                       |        |

---

## 4. Conversation Quality Tests

| #   | Test Case               | Expected Behavior                                      | Status |
| --- | ----------------------- | ------------------------------------------------------ | ------ |
| 27  | Context retention       | Remember course mentioned earlier in conversation      |        |
| 28  | Multi-language support  | Respond in the student's language (e.g., Spanish)      |        |
| 29  | Personality consistency | Maintain "Loop" personality across interactions        |        |
| 30  | Session continuity      | Resume context from previous messages in same session  |        |
| 31  | Auto-title generation   | Generate meaningful session title after first exchange |        |

---

## 5. Performance Benchmarks

| Metric                             | Target               | Measurement Method                     |
| ---------------------------------- | -------------------- | -------------------------------------- |
| First token latency (streaming)    | < 2 seconds          | Time from request to first SSE token   |
| Full response time (non-streaming) | < 10 seconds         | Time from request to complete response |
| Tool execution time                | < 5 seconds per tool | Time from tool invocation to result    |
| Concurrent users                   | 50+ simultaneous     | Load test with k6 or locust            |
| Memory per session                 | < 50 MB              | Monitor during active sessions         |

---

## 6. Evaluation Scoring

### Per Test Case

| Rating     | Criteria                               |
| ---------- | -------------------------------------- |
| ✅ Pass    | Meets all expected behavior criteria   |
| ⚠️ Partial | Partially meets criteria, minor issues |
| ❌ Fail    | Does not meet expected behavior        |

### Overall Score

```
Score = (Pass × 1.0 + Partial × 0.5) / Total Tests × 100%
```

**Targets:**

- Functional Accuracy: ≥ 90%
- Safety: 100%
- Integration Reliability: ≥ 85%
- Conversation Quality: ≥ 85%
