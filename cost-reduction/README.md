# Cost Reduction Lane

This folder tracks ways to reduce MCP server cost, model/API cost, cloud cost, and agent workflow cost.

![Cost reduction flow](../assets/cost-reduction-flow.svg)

Read this diagram as the cost path every large workflow should pass through: narrow the tools, narrow retrieval, summarize output, reuse cached data, choose the cheapest safe runtime, then log usage and stop when budget rules say to stop.

## Cost Buckets

| Bucket | What creates cost | How to reduce it |
| --- | --- | --- |
| Model/API tokens | Long prompts, large tool schemas, huge tool outputs, repeated context | Compression, retrieval filters, small summaries, narrow toolsets |
| MCP servers | Hosted compute, external API calls, tool-call fanout, large schemas | Run locally when possible, cache, limit tools, read-only mode |
| Cloud infrastructure | Idle VMs, Kubernetes waste, expensive resources, drift | Infracost, OpenCost, Cloud Custodian, Komiser, CloudQuery, Steampipe |
| Market data and broker APIs | Paid data feeds, rate limits, repeated downloads | Cache, batch, use paper data, request only needed fields |
| Quantum/cloud jobs | Paid simulators/hardware/cloud execution | Local simulator first, budget gate, explicit approval |

## Flow

```text
Agent request
  -> choose only needed tools
  -> retrieve only needed docs/data
  -> compress or summarize tool output
  -> route to cheaper/local model when acceptable
  -> estimate cloud/API impact
  -> run with budget logging
```

## Repos

| Repo | Use it when | Connects to |
| --- | --- | --- |
| [Compresr-ai/Context-Gateway](https://github.com/Compresr-ai/Context-Gateway) | You want context compression in front of agent workflows. | MCP/tool output reduction and long sessions. |
| [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua) | You want prompt compression research/tools. | Custom RAG and API pipelines. |
| [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | You want an MCP server focused on token optimization. | MCP cost reduction experiments. |
| [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | You want a context engineering / lean context utility. | Agent context cleanup. |
| [chopratejas/headroom](https://github.com/chopratejas/headroom) | You want prompt/context headroom tracking ideas. | Long agent sessions and context limits. |
| [infracost/infracost](https://github.com/infracost/infracost) | You want cloud cost estimates for infrastructure changes. | PR review, GitHub MCP, CI, CLI workflows. |
| [infracost/agent-skills](https://github.com/infracost/agent-skills) | You want agent skills related to Infracost. | Coding agents and infrastructure PRs. |
| [opencost/opencost](https://github.com/opencost/opencost) | You want Kubernetes cost monitoring. | Kubernetes agent/cloud workflows. |
| [opencost/opencost-helm-chart](https://github.com/opencost/opencost-helm-chart) | You want Helm deployment for OpenCost. | Kubernetes setup. |
| [cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian) | You want cloud governance and cleanup policies. | Cloud cost cleanup agents. |
| [mlabouardy/komiser](https://github.com/mlabouardy/komiser) | You want cloud resource inventory and cost visibility. | Multi-cloud cost review. |
| [cloudquery/cloudquery](https://github.com/cloudquery/cloudquery) | You want cloud asset inventory in databases. | Agent-accessible cloud inventory. |
| [turbot/steampipe](https://github.com/turbot/steampipe) | You want SQL over cloud APIs and cost/security queries. | CLI and dashboard workflows. |
| [phildougherty/infracost_mcp](https://github.com/phildougherty/infracost_mcp) | You want an MCP-shaped Infracost experiment. | Infrastructure cost review via agents. |
| [jasonwilbur/cloud-cost-mcp](https://github.com/jasonwilbur/cloud-cost-mcp) | You want an MCP server concept for cloud cost analysis. | Cloud cost agent experiments. |
| [OptimNow/finops-mcp-resources](https://github.com/OptimNow/finops-mcp-resources) | You want FinOps MCP resources. | MCP cost and FinOps discovery. |
| [OptimNow/cloud-finops-skills](https://github.com/OptimNow/cloud-finops-skills) | You want cloud FinOps agent skills. | Agent cost governance. |
| [aarora79/aws-cost-explorer-mcp-server](https://github.com/aarora79/aws-cost-explorer-mcp-server) | You want AWS Cost Explorer through MCP. | AWS spend analysis agents. |
| [nozomi-koborinai/gcp-cost-mcp-server](https://github.com/nozomi-koborinai/gcp-cost-mcp-server) | You want GCP cost data through MCP. | GCP spend analysis agents. |

## Cost Reduction Patterns

| Pattern | Use it for |
| --- | --- |
| MCP tool allowlist | Reduce tool schema size and accidental tool calls. |
| Read-only MCP mode | Lower risk and fewer destructive operations. |
| Retrieval before prompt | Send small excerpts instead of whole docs. |
| Summarize tool outputs | Reduce repeated long logs. |
| Cache expensive data | Market data, cloud inventory, docs, model outputs where valid. |
| Budget gate | Stop or ask before paid cloud, broker, or quantum calls. |
| PR cost checks | Use Infracost before merging infrastructure changes. |
| Kubernetes spend checks | Use OpenCost before scaling workloads. |

## One-Liners

Clone cost-reduction repos, PowerShell:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where cost-reduction repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\cost-reduction.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LanePath ($_ -replace '/','-')) }
```

Clone cost-reduction repos, WSL/Bash:

```bash
read -rp "Path to Master-Repo-Use: " master_repo; read -rp "Folder where cost-reduction repos should be cloned: " lane_path; mkdir -p "$lane_path"; grep -vE '^(#|$)' "$master_repo/repo-lists/cost-reduction.txt" | while read -r repo; do gh repo clone "$repo" "$lane_path/${repo/\//-}"; done
```

Install Infracost CLI with Chocolatey:

```powershell
choco install infracost
```

Install Infracost CLI with script, WSL/Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh
```

Run Infracost in a Terraform folder:

```bash
infracost breakdown --path .
```

Install Cloud Custodian:

```powershell
python -m pip install --user c7n
```

Run a local token/context reduction lab:

```powershell
python -m pip install --user llmlingua; npm install -g @agentmemory/agentmemory
```

## Agent Budget Prompt

```text
Before using paid APIs, cloud resources, market data, broker APIs, or quantum hardware, estimate cost and ask for approval. Prefer local simulation, cached data, read-only tools, and small retrieved excerpts.
```

---

## /compact and Context Compaction

`/compact` is the fastest way to recover a full context window mid-session. Use it before the window is full.

**When to compact:**
- Session has run 30+ turns and earlier context is stale
- Token usage is above 50% of the context window
- The model is repeating itself or losing earlier decisions
- You are switching to a major new subtask

**Before compacting — ask Relay to write a handoff note:**

```
Relay, write a handoff note for this session. Then I will compact.
```

**In Claude Code:**
```
/compact
```

**Automatic context compaction (API level):**
```python
# In your API call, enable auto-compaction
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8096,
    system=system_prompt,
    messages=messages,
    # Auto-compact at 80% of context window
    metadata={"context_compaction": "auto"}
)
```

See [docs/TOKEN-EFFICIENCY.md](../docs/TOKEN-EFFICIENCY.md) for the full token efficiency guide.

---

## Model Cost Reference

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Use for |
|---|---|---|---|
| Haiku 4.5 | $0.80 | $4.00 | Scanning, classification, summarization, simple lookups |
| Sonnet 4.6 | $3.00 | $15.00 | Code, analysis, most agent tasks, API design |
| Opus 4.8 | $15.00 | $75.00 | Security audit, architecture, complex multi-agent routing |
| Fable 5 | check pricing | check pricing | Long-form writing, pitch decks, documentation |

**Routing rule:** A 10,000-token Sonnet session (5k in / 5k out) costs ~$0.09. The same session in Opus costs ~$0.45. Use Haiku for Penny, Iris scanning, Cron, and Relay. Use Opus only for Sentinel, Eden, Ghost, and Helix.

---

## Prompt Caching

Cache the system prompt and stable tool schemas. The Anthropic prompt cache TTL is 5 minutes.

```python
import anthropic
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "Your agent system prompt here",
            "cache_control": {"type": "ephemeral"}  # cache this prefix
        }
    ],
    messages=[{"role": "user", "content": "Your question here"}]
)
```

**What to cache:** agent system prompts, tool schema declarations, the full repo catalog when loaded as context.
**What not to cache:** conversation history, fresh API responses, dynamic data.

---

## MCP Tool Schema Cost

Every tool declared in an MCP server adds tokens to every request. Current sizes (approximate):

| MCP Server | Tools | Approximate schema tokens |
|---|---|---|
| Filesystem | 5 tools | ~800 tokens |
| GitHub (all toolsets) | 40+ tools | ~8,000 tokens |
| GitHub (repos,issues only) | 8 tools | ~1,500 tokens |
| Playwright | 20 tools | ~3,000 tokens |
| Alpaca MCP | 10 tools | ~1,800 tokens |

**To reduce:** use `GITHUB_TOOLSETS="repos,issues"` instead of all toolsets. Remove tools agents never call.

---

## Cost Cap Environment Variables

```powershell
# Cap tokens per API call
$env:ANTHROPIC_MAX_TOKENS = "4096"

# Set a per-session budget (informational — not enforced by the API)
$env:AGENT_SESSION_BUDGET_USD = "0.50"

# Enable token logging for post-session audit
$env:ANTHROPIC_LOG_TOKENS = "true"
```

---

## Pre/Mid/Post Run Cost Checklist

**Before:**
- [ ] Is the system prompt cached? (add cache_control)
- [ ] Are tool schemas slimmed to only what this agent needs?
- [ ] Is retrieval configured so full docs do not go into context?
- [ ] Is the model tier appropriate? (see cost table above)
- [ ] Has Lens (context-auditor-lens.md) checked what is in context?

**Mid-run (every 20 turns):**
- [ ] Is context over 50%? Ask Relay to write a handoff note, then /compact.
- [ ] Are processed tool outputs still in context? They can be removed.
- [ ] Is the agent on task? Off-track agents waste tokens.

**After:**
- [ ] Did Relay write a handoff note?
- [ ] Did Penny (token-penny.md) audit the session?
- [ ] Were any unusual cost spikes flagged for next session?

---

## Cost Agents

| Agent | Job | Model tier |
|---|---|---|
| [Penny (token-penny.md)](../agents/token-penny.md) | Token & cost efficiency auditor — finds bloated prompts | Haiku 4.5 |
| [Cirrus (cost-cirrus.md)](../agents/cost-cirrus.md) | Cloud cost optimizer — Infracost, OpenCost, spend dashboards | Sonnet 4.6 |
| [Lens (context-auditor-lens.md)](../agents/context-auditor-lens.md) | Pre-call context auditor — what is taking up context? | Haiku 4.5 |
