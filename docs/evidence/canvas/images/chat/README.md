# Chat — Evidence Screenshots

Screenshots demonstrating general chat interactions and conversational quality.  
These correspond to **Evaluation Plan §4 — Conversation Quality** (Test Cases #27–#31).

---

## Test Case #27 — Context retention

**Description:** The assistant remembers a course mentioned earlier in the conversation.  
**Input:** Mention a course in message 1, reference "that course" in message 3.  
**Expected:** Remembers course mentioned earlier.

![TC27 — Context retention](tc27-context-retention.png)

---

## Test Case #28 — Multi-language support

**Description:** The assistant responds in the student's language when addressed in that language.  
**Input:** `"¿Qué tareas tengo pendientes?"`  
**Expected:** Response fully in Spanish.

![TC28 — Multi-language support](tc28-multi-language.png)

---

## Test Case #29 — Personality consistency

**Description:** The assistant maintains its "Loop" identity with a warm, encouraging tone and appropriate emojis.  
**Input:** Multiple interactions across different topics.  
**Expected:** Consistent tone and personality.

![TC29 — Personality consistency](tc29-personality-consistency.png)

---

## Test Case #30 — Session continuity

**Description:** The assistant resumes context from previous messages in the same session.  
**Input:** Load a session with 5+ prior messages, ask a follow-up.  
**Expected:** References earlier context.

![TC30 — Session continuity](tc30-session-continuity.png)

---

## Test Case #31 — Auto-title generation

**Description:** The assistant generates a meaningful title (≤60 chars) after the first exchange.  
**Input:** Start a new chat session.  
**Expected:** Descriptive title auto-generated.

![TC31 — Auto-title generation](tc31-auto-title.png)
