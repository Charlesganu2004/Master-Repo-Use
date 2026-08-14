# Token Efficiency & Cost Reduction Guide

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

Everything here reduces the cost and latency of running agents in this catalog without sacrificing quality.

---

## /compact — When and How

`/compact` summarizes the current conversation into a checkpoint, then continues from that checkpoint. Use it:

- When the session has been running for 30+ turns and earlier context is no longer needed
- Before starting a major new subtask in the same session
- When the model starts repeating itself or losing earlier decisions
- When token usage in the session exceeds 50% of the context window

How to use in Claude Code:

```
/compact
```

What happens: Claude summarizes the conversation into a handoff note. Decisions and work-in-progress are preserved. Raw conversation history is dropped. The session continues with a fresh context window.

**Before compacting:** tell Relay (handoff-relay.md) to write a handoff note first:

```
Relay, write a handoff note for this session before I compact.
```

**After compacting:** read the handoff note and confirm the summary is accurate before continuing.

---

## Automatic Context Compaction

In Claude Code, you can enable automatic context compaction so /compact happens before the context limit is hit:

```bash
claude --context-auto-compact
```

Or add to your Claude Code settings:

```json
{
  "contextCompaction": "auto"
}
```

This triggers compaction at 80% of the context window, giving headroom for the compaction itself.

---

## Model Selection — Cost Decision Tree

Choose the cheapest model that can do the job correctly:

```
Is this task simple classification, summarization, or file lookup?
  → Haiku 4.5 ($0.80 / $4.00 per 1M tokens)

Is this task code generation, analysis, API design, or multi-step reasoning?
  → Sonnet 4.6 ($3.00 / $15.00 per 1M tokens)

Is this task security audit, architecture review, complex multi-agent routing, or quantum research?
  → Opus 4.8 ($15.00 / $75.00 per 1M tokens)

Is this task long-form writing, pitch deck narrative, or documentation?
  → Fable 5 (check current pricing)
```

Agents in this repo already specify their recommended model tier. Follow those recommendations.

---

## Model Cost Reference

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best for |
|---|---|---|---|
| Haiku 4.5 | $0.80 | $4.00 | Scanning, classification, summarization |
| Sonnet 4.6 | $3.00 | $15.00 | Code, analysis, most agent tasks |
| Opus 4.8 | $15.00 | $75.00 | Deep reasoning, security, architecture |
| Fable 5 | check pricing | check pricing | Long-form narrative writing |

At $3.00 input / $15.00 output, a 10,000-token session with Sonnet 4.6 (5k in, 5k out) costs ~$0.09. At Opus rates, the same session costs ~$0.45. Choose the right tier.

---

## Prompt Caching

Caching system prompts and stable tool schemas saves money on repeated sessions. The prompt cache TTL is 5 minutes in the Anthropic API.

Cache the system prompt (API usage):

```python
{
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Your system prompt here",
            "cache_control": {"type": "ephemeral"}
        }
    ]
}
```

What to cache:
- Agent system prompts (stable across sessions)
- Tool schemas (change rarely)
- Full repo catalogs loaded as context

What not to cache:
- Conversation history (changes every turn)
- Dynamic API responses

---

## Token Budget Environment Variables

Set token limits to prevent runaway costs:

```powershell
# Max tokens per API call
$env:ANTHROPIC_MAX_TOKENS = "4096"

# Budget warning threshold (not enforced — informational)
$env:ANTHROPIC_TOKEN_BUDGET_WARNING = "80000"
```

Use Penny (agents/token-penny.md) to audit sessions that go over budget.

---

## MCP Tool Schema Slimming

Every tool schema added to an MCP server adds tokens to every request. Reduce this:

1. Expose only the tools the agent needs. Do not add all tools to every agent.
2. Keep tool descriptions under 50 words.
3. Remove optional parameters that the agent never uses.
4. Use `GITHUB_TOOLSETS` to limit which GitHub MCP tools are available:

```bash
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" \
  -e GITHUB_TOOLSETS="repos,issues" \
  ghcr.io/github/github-mcp-server
```

This exposes only repos and issues tools instead of the full 40+ tool schema.

---

## Context Compression Repos

| Repo | What it does | When to use |
|---|---|---|
| [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua) | Prompt compression | Long prompts with redundant content |
| [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | MCP server for token optimization | In-agent token counting and trimming |
| [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | Lean context management | Keeping context minimal per session |
| [chopratejas/headroom](https://github.com/chopratejas/headroom) | Context headroom management | Ensuring space for model output |

---

## Retrieval-Before-Generation Pattern

Never dump a full document into context. Always retrieve first:

```text
User question
  → retrieve top-3 relevant chunks from vector store
  → insert only those chunks into context
  → generate answer with citations
```

This keeps context small and responses grounded. Configure in Vector (agents/rag-vector.md).

---

## Pre/Mid/Post Run Checklist

**Before a long agent run:**
- [ ] Is the system prompt cached?
- [ ] Are tool schemas slimmed to only what this agent needs?
- [ ] Is a retrieval layer set up so full docs do not go into context?
- [ ] Is the model tier appropriate for this task?
- [ ] Has Lens (context-auditor-lens.md) checked what is in context?

**Mid run (every 20 turns):**
- [ ] Is context over 50%? Run /compact.
- [ ] Are there processed tool outputs still in context? Remove them.
- [ ] Is the agent still on task? If off-track, compact and restart.

**After a run:**
- [ ] Did Relay write a handoff note?
- [ ] Did Penny audit the session cost?
- [ ] Were any unusual token spikes logged for investigation?

---

## Token Counting Before a Run

Estimate cost before a large prompt:

```python
import anthropic
client = anthropic.Anthropic()

# Count tokens without sending
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="Your system prompt here",
    messages=[{"role": "user", "content": "Your user message here"}]
)
print(f"Input tokens: {response.input_tokens}")
print(f"Estimated cost: ${response.input_tokens / 1_000_000 * 3:.4f}")
```

---

## Prompt Skeleton Pattern

Reuse a stable prefix that gets cached, then append the dynamic part:

```text
[CACHED PREFIX — system prompt, tool schemas, stable context]
---
[DYNAMIC SUFFIX — user's specific question, fresh data]
```

The prefix is cached after the first call. Subsequent calls only pay for the dynamic suffix.
