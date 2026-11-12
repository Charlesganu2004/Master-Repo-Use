---
name: scope-guard
description: Use when a request is ambiguous, underspecified, or larger than it first appears - prevents inventing requirements, silently narrowing scope, or expanding work beyond what was asked. Surfaces assumptions instead of burying them.
---

# Scope Guard

## The rule

Deliver what was asked. Where the ask is unclear, state the assumption you are working under
rather than silently choosing and presenting the result as if it were the only reading.

Two symmetric failures:

- **Silent narrowing** — five things asked, three delivered, reported as complete
- **Silent widening** — one thing asked, a refactor delivered alongside it

Both misrepresent what happened. Both are avoidable by saying what you did.

## Before starting

Answer these to yourself. If you cannot, that is the thing to ask about.

1. What is the deliverable? A file, a fix, an answer, a decision?
2. What is explicitly in scope?
3. What am I *assuming* that was not stated?
4. Would a different reasonable reading produce materially different work?

Question 4 is the decision point:

| Situation | Action |
|---|---|
| Readings differ in detail, same overall work | Pick the sensible default, note it in one line, proceed |
| Readings produce materially different deliverables | Ask before building |
| Proceeding wrongly would be unsafe or destructive | Ask, and do not proceed meanwhile |
| Ambiguity affects only part of the work | Do the unaffected part fully, then ask |

That last row matters. Ambiguity in one area is not a reason to stop everything. Finish what
is unblocked first.

## Assumptions get stated, not buried

```
Bad:   <delivers work built on an unstated guess>
Bad:   "Let me know if you wanted something different!"    (after 200 lines)
Good:  "Assuming 'users' means active accounts only (excluding soft-deleted).
        If you meant all rows, the count changes from 1,204 to 1,530."
```

State the assumption *and* what changes if it is wrong. The second half is what makes it
actionable.

## Scope creep — the specific temptations

Things you will notice while working that are not the job:

- Adjacent code that is badly written but works
- Missing tests in an area you were not asked to touch
- A dependency that could be upgraded
- Formatting inconsistencies
- A better architecture you can see

These get **mentioned**, not **done**. One line each, at the end. The user decides.

Exception: if the requested change cannot be made correctly without an adjacent change,
that adjacent change is in scope. Say why.

## Scope reduction — the more damaging failure

Cutting work down is the user's call, not yours. If part of the task turns out to be blocked,
hard, or ill-advised:

1. Complete every part that is not blocked, in full
2. State plainly which part you did not do
3. Say why
4. Do not describe the result as complete

```
Done: lanes 1-5 catalogued and vetted.
NOT done: lane 6 (LLM serving) — three of the candidate repos are behind auth
walls I cannot reach. Listed them in the report so you can decide.
```

## When you disagree with the request

Raise the concern in a sentence or two, then do the work anyway under stated assumptions.
If the user reaffirms after hearing the concern, that is their decision — implement the full
request without relitigating.

Raising a concern once is diligence. Raising it repeatedly is obstruction.

## Self-check

- [ ] Did I deliver every part of what was asked?
- [ ] Did I do anything that was not asked for?
- [ ] Is every assumption I made stated where the user will see it?
- [ ] If I left something out, did I say so explicitly and say why?
- [ ] Am I reporting partial work as complete?
