---
name: cavemanultracompress
description: >
  Ultra-compress the live context window in place. Restates the whole session as
  one caveman-terse briefing, drops superseded tool output and dead ends, and
  keeps the protected global rules verbatim. Use for /cavemanultracompress,
  "ultra compress", "compress the context", "shrink context", or when a
  <caveman-autocompress> context-pressure notice appears.
---

# Caveman Ultra Compress

Compress the **live conversation context**, not a file. Output replaces the
session's working memory: after it, act from the briefing alone.

Fires two ways:

1. **Manual** — user types `/cavemanultracompress`.
2. **Automatic** — a `<caveman-autocompress>` notice arrives from the
   `caveman-autocompress` hook at 70% context. Same routine, no permission ask,
   done inside the current turn, then the interrupted work continues.

## Protected — never compress

Reproduce verbatim, in full, every time. These outrank compression:

- The **PROTECTED RULES** block from `~/.copilot/copilot-instructions.md`
  (caveman mode, token-goat gate, browser-automation routing, this routine).
- Exact user requirements, constraints, and acceptance criteria as stated.
- Literal strings: code, commands, paths, URLs, error text, IDs, version numbers,
  credential placeholders, regexes, SQL.
- Any negation or scope word: not / never / no / only / except / until.
- Unresolved questions and open decisions.

If compressing something would lose a fact needed to finish the task, keep it.
Ambiguity costs more than tokens.

## Routine

1. **Sweep** the conversation start to end. Sort every item into: durable fact,
   superseded, or noise.
2. **Drop** outright:
   - tool output later re-read, corrected, or replaced
   - abandoned approaches, except the one-line reason they failed
   - full file bodies already summarized into a decision
   - progress narration, restated plans, acknowledgements
   - duplicate search results and repeated directory listings
3. **Fold** what remains into the briefing below, caveman-terse.
4. **Emit** the briefing as the reply. Nothing before it, nothing after it.
5. **Continue** from the briefing. Never re-read a file the briefing already
   settles; use `token-goat read "file::symbol"` if a detail is genuinely missing.

## Briefing shape

```
## PROTECTED RULES
<verbatim, uncompressed>

## TASK
<user goal, exact constraints>

## STATE
<what is true now: files changed, decisions made, versions, paths>

## EVIDENCE
<facts earned from tools, one line each, with the path or command that proved it>

## DEAD ENDS
<approach - why it failed, one line each>

## OPEN
<unresolved questions, blocked items>

## NEXT
<the immediate next action>
```

Empty sections are omitted, not padded.

## Style

Caveman **ultra**: drop articles, filler, hedging, pleasantries, and conjunctions
where cause and effect stay unambiguous. One word when one word enough. State
each fact once.

Never invent abbreviations (`cfg`, `impl`, `req`, `fn`) — the tokenizer splits
them the same as the full word, so they cost the same and read worse. No arrows
(`->`) — own token, saves nothing. Technical terms, symbols, and error strings
exact.

## Boundaries

- Compresses the context window only. Never edits a file. To compress a memory
  file on disk, use `/caveman-compress <path>` instead.
- Never drops a protected item to hit a size target.
- Never compresses text destined for another human — commits, PR bodies, issues,
  docs — those stay normal prose.
- Never claims work is done that the transcript does not prove.
