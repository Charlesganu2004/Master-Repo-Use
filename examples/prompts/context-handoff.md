# Context Handoff Prompt

Use this before compaction, after a long debugging session, or before handing work to another agent.

```text
Summarize the current state for a future agent. Preserve:

- Objective
- Current branch and repo path
- Files changed
- Commands already run
- Test results
- Decisions made
- Open questions
- Next 3 steps
- Risks or things not to touch

Keep it concise, factual, and useful after older chat history is gone.
```
