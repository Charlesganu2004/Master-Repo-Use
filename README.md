# Master Repo Use

**GitHub:** https://github.com/Charlesganu2004/Master-Repo-Use
Last curated: 2026-06-26

A self-contained command center for agent frameworks, RAG, memory, MCP servers, token/context management, Microsoft Copilot Studio, autonomous trading agents, finance/trading, quantum computing, cloud/cost reduction, app templates, and hackathon resources.

**You do not need to leave this repo to use any of these tools.** Every lane has install commands, usage instructions, and agent setups here.

**Repo health:** [docs/REPO-HEALTH.md](docs/REPO-HEALTH.md) — run Iris to check which repos are still active.
**Security:** [docs/SECURITY.md](docs/SECURITY.md) — agent injection prevention, MCP scoping, secret scanning.

---

## Interactive Diagrams

Open [assets/interactive-diagram.html](assets/interactive-diagram.html) in your browser for clickable flow diagrams:

- **Main Flow** — click any node to see the tools, options, and standalone path for that layer
- **Standalone Paths** — fastest path to working in each lane without the full stack
- **Combinations** — named stack recipes with install commands (Core Agent, Microsoft, Trading, Quantum, Security, etc.)
- **Trading & Finance** — the full safety gate flow from signal to live order
- **Cost & Tokens** — token efficiency and /compact decision flow
- **Agent Roster** — all 55 agents at a glance

Open in browser:
```powershell
$RepoRoot = Read-Host "Path to Master-Repo-Use"
Start-Process (Join-Path $RepoRoot "assets\interactive-diagram.html")
```

---

## Start Here By Role

| I am a... | Go here first |
|---|---|
| Developer building agents | [Repo Catalog → Agent Frameworks](docs/REPO-CATALOG.md) + [Standalone Usage](docs/STANDALONE-USAGE.md) |
| Trader / researcher | [Autonomous Day Trading](docs/AUTONOMOUS-DAY-TRADING.md) + [Trading & Market Agents](docs/TRADING-MARKET-AGENTS.md) |
| Architect / DevOps | [Integration Flows](docs/INTEGRATION-FLOWS.md) + [Agent: Eden](agents/architect-eden.md) |
| Business analyst / planner | [Agent: Clara](agents/biz-analyst-clara.md) + [Agent: Rho](agents/tech-planner-rho.md) |
| Security engineer | [Security Guide](docs/SECURITY.md) + [Agent: Sentinel](agents/security-sentinel.md) |
| Data scientist | [Agent: Dex](agents/data-dex.md) + [Repo Catalog → RAG](docs/REPO-CATALOG.md) |
| New user | [Agent: Guide](agents/onboarding-guide.md) + [Standalone Usage](docs/STANDALONE-USAGE.md) |
| Cost optimization | [Token Efficiency](docs/TOKEN-EFFICIENCY.md) + [Cost Reduction](cost-reduction/README.md) |
| Copilot Studio | [Copilot Studio Integration](docs/COPILOT-STUDIO-INTEGRATION.md) + [Agent: Nexus](agents/copilot-nexus.md) |

---

## Start Here By Task

| Need | Go here |
|---|---|
| See the main integration flow | [Integration flows](docs/INTEGRATION-FLOWS.md) |
| See every repo with links and status | [Repo catalog](docs/REPO-CATALOG.md) |
| Install and run any repo | [Repo instructions](docs/REPO-INSTRUCTIONS.md) |
| Combine repos into a named stack | [Combining repos](docs/COMBINING-REPOS.md) |
| Use any lane standalone | [Standalone usage](docs/STANDALONE-USAGE.md) |
| Copy one-liners for PowerShell, WSL, GitHub CLI | [CLI one-liners](docs/CLI-ONE-LINERS.md) |
| Reduce token and API cost | [Token efficiency](docs/TOKEN-EFFICIENCY.md) + [Cost reduction](cost-reduction/README.md) |
| Browse the full agent roster (55 agents) | [Agents overview](agents/AGENTS-OVERVIEW.md) |
| Check if a repo is still active | [Repo health](docs/REPO-HEALTH.md) |
| Add a plugin | [Adding plugins](docs/ADDING-PLUGINS.md) |
| Browse available plugins | [Plugins](plugins/README.md) |
| Secure agents and MCP setup | [Security guide](docs/SECURITY.md) |
| Share with coworkers | [Access control — in Security guide](docs/SECURITY.md#access-control-for-this-repo) |
| Let an agent reach folders safely | [Agent access guide](docs/AGENT-ACCESS.md) |
| Connect Microsoft Copilot Studio | [Copilot Studio integration](docs/COPILOT-STUDIO-INTEGRATION.md) |
| Add quantum computing | [Quantum guide](quantum/README.md) |
| Build autonomous day-trading agents | [Autonomous day-trading guide](docs/AUTONOMOUS-DAY-TRADING.md) |
| Connect broker apps | [Broker app integrations](docs/BROKER-APP-INTEGRATIONS.md) |
| Add market analysis repos | [Trading and market agents](docs/TRADING-MARKET-AGENTS.md) |
| Reduce cloud and API cost | [Cost reduction guide](cost-reduction/README.md) |
| Use curated repo lists in scripts | [repo-lists/all-curated.txt](repo-lists/all-curated.txt) |

---

## Quick Clone

PowerShell:
```powershell
$RepoPath = Read-Host "Where should Master-Repo-Use be cloned?"; git clone https://github.com/Charlesganu2004/Master-Repo-Use.git $RepoPath; Set-Location $RepoPath
```

WSL or Bash:
```bash
read -rp "Where should Master-Repo-Use be cloned? " repo_path; git clone https://github.com/Charlesganu2004/Master-Repo-Use.git "$repo_path" && cd "$repo_path"
```

GitHub CLI:
```bash
read -rp "Where should Master-Repo-Use be cloned? " repo_path; gh repo clone Charlesganu2004/Master-Repo-Use "$repo_path" && cd "$repo_path"
```

---

## Main Flow

```text
CLI, VS Code, Copilot Studio, app UI, or automation
  -> Maxwell (orchestrator) routes to specialist agent
  -> Agent framework (Squad, Microsoft Agents, RunAgent, Copilot CLI)
  -> MCP tools and normal APIs
  -> RAG, memory, context control, and cost controls
  -> app, cloud service, broker (paper mode), or local workflow
```

Specialist lanes (connect to main flow or run standalone):
```text
Market research agents -> optional research and paper-trading sidecar
Quantum labs -> optional optimization/QML sidecar
Pitch/hackathon -> standalone demo/story materials
```

---

## Agents

55 named agents with system prompts, tools, knowledge base setup, and setup CLI. Each is ready to paste into Claude, Copilot Studio, Squad, or any compatible framework.

| Category | Agents |
|---|---|
| Orchestration | Maxwell (routes all tasks), Iris (repo health), Relay (context handoff), Cron (scheduler) |
| Research | Aria, Dex, Orion, Prism, Beacon |
| Business | Clara, Rho, Spark, Deck, Funnel, Quill |
| Software Dev | Atlas, Stack, Canvas, Build, Pipe, Probe, Vera, Trace |
| Architecture | Eden, Nimbus, Schema, Bridge, Volt |
| Security | Sentinel, Ghost, Lex, Lock |
| Finance/Trading | Rex, Qubit, Nova, Sage, Connect |
| Infra/Cost | Cirrus, Penny, Forge |
| Knowledge | Vector, Recall, Memo |
| Copilot Studio | Nexus, Weave |
| Onboarding | Guide, Help |
| Quantum | Helix |
| Cross-cutting | Commit, Lens, Delta, Echo, Pulse, Tempo, Ally |

**Full roster with tools and cost profiles:** [agents/AGENTS-OVERVIEW.md](agents/AGENTS-OVERVIEW.md)

---

## Reading Tabs

<details>
<summary><strong>1. Core agent system</strong></summary>

Use this when you want agents that can reason over a repo, call tools, remember project facts, and run from the terminal or a product surface.

- Agent frameworks: Squad, Microsoft Agents, Copilot CLI, RunAgent.
- Knowledge: LightRAG, Upstash, AugmentR, RAG CLI.
- Memory: AgentMemory, mem0, durable handoff prompts.
- Context/cost: Context Gateway, LLMLingua, token optimizer MCP servers.
- MCP access: filesystem, GitHub, Playwright, docs, databases, cloud tools.
- Orchestrator: Maxwell routes to Aria, Atlas, Sentinel, Penny, and 51 more specialists.

See [agents/AGENTS-OVERVIEW.md](agents/AGENTS-OVERVIEW.md) for the full agent roster.

</details>

<details>
<summary><strong>2. Microsoft Copilot Studio connections</strong></summary>

Copilot Studio can sit in front of the stack as the business-facing agent. Connect it to:

- Existing APIs through custom connectors or OpenAPI actions.
- MCP servers through the Copilot Studio MCP custom connector path.
- Microsoft 365 Agents SDK services when the agent needs a full-code backend.
- RAG or finance/quantum services through a small API bridge.

Agents: Nexus (copilot-nexus.md) orchestrates topics and flows. Weave (connector-weave.md) builds connectors.

See [docs/COPILOT-STUDIO-INTEGRATION.md](docs/COPILOT-STUDIO-INTEGRATION.md).

</details>

<details>
<summary><strong>3. Quantum as standalone or sidecar</strong></summary>

Quantum is not the main focus of this repo. Treat it as:

- Standalone learning: Qiskit, PennyLane, Cirq, Q#, Braket, D-Wave.
- Sidecar optimization: portfolio optimization, routing, scheduling, scenario selection.
- Research lane: quantum machine learning, quantum finance, error mitigation.

Agents: Helix (quantum-lab-helix.md) for experiments. Qubit (quantum-qubit.md) for finance research.

See [quantum/README.md](quantum/README.md).

</details>

<details>
<summary><strong>4. Trading and market agents</strong></summary>

This lane is for research, market analysis, paper trading, and tool exploration. Keep live trading separate until code, risk controls, broker permissions, and compliance are audited.

- Autonomous day trading: safe plugin scaffold, signal generation, backtests, investing allocation proposals, paper trading.
- Market analysis: OpenBB, FinRobot, FinGPT, yfinance, mplfinance.
- Trading agents/backtesting: TradingAgents, AI-Trader, FinRL, Lean, Backtrader, Freqtrade.

Agents: Rex (trading), Sage (risk gate), Nova (portfolio), Connect (broker setup).

Safety gate: Sage must approve before any order. Human must approve before any live order. See [docs/AUTONOMOUS-DAY-TRADING.md](docs/AUTONOMOUS-DAY-TRADING.md).

</details>

<details>
<summary><strong>5. Token efficiency and cost</strong></summary>

Keep model API costs under control:

- /compact: compact the session before the context limit. Relay writes a handoff note first.
- Model routing: Haiku ($0.80/$4.00 per 1M) for simple tasks, Sonnet for most, Opus for deep reasoning.
- Prompt caching: cache system prompts and tool schemas to reduce per-call cost.
- MCP tool slimming: expose only the tools an agent actually needs.
- Penny: audits sessions and flags bloated prompts.

See [docs/TOKEN-EFFICIENCY.md](docs/TOKEN-EFFICIENCY.md).

</details>

<details>
<summary><strong>6. Plugins</strong></summary>

Self-contained agent + tool packages with a smoke test and risk limits built in.

Current plugins:
- [plugins/autonomous-day-trading-agent](plugins/autonomous-day-trading-agent/README.md) — signal generation, backtesting, paper trading
- [plugins/robinhood-trading-agent](plugins/robinhood-trading-agent/README.md) — Robinhood Crypto research lane
- [plugins/quantum-trading-agent](plugins/quantum-trading-agent/README.md) — quantum-enhanced paper trading

See [plugins/README.md](plugins/README.md) for the full index. See [docs/ADDING-PLUGINS.md](docs/ADDING-PLUGINS.md) to add a new plugin.

</details>

<details>
<summary><strong>7. Security</strong></summary>

This repo follows these security rules for all agents and plugins:

- System prompts are write-once at setup time — they cannot be overridden by user input.
- Tool outputs are data, never instructions — agents do not execute instructions found in file reads or API responses.
- MCP servers always use explicit allowed paths — never root or wildcards.
- No secrets in committed files — Lock scans before every commit.
- Live financial actions require explicit human approval in the current conversation.

See [docs/SECURITY.md](docs/SECURITY.md) for the full threat model, MCP security rules, and access control options.

</details>

<details>
<summary><strong>8. Pitch and hackathon stays standalone</strong></summary>

Pitch and hackathon tools are not part of the main runtime stack. Keep them as standalone support:

- `awesome-hackathon` for planning and resources.
- `slidev` and `marpit` for decks.
- `pitch-deck` for pitch structure and review.
- Spark (pitch-spark.md) for pitch coaching.
- Deck (slides-deck.md) for Slidev deck generation.

They can consume summaries from the core stack, but they are not required agent infrastructure.

</details>

---

## Decision Map

| If you want to... | Start with | Then add |
|---|---|---|
| Build agent teams | [Squad](https://github.com/bradygaster/squad), [microsoft/agents](https://github.com/microsoft/agents), [Agents-for-net](https://github.com/microsoft/Agents-for-net) | RAG, memory, MCP tools |
| Orchestrate multiple agents | [Maxwell — orchestrator-maxwell.md](agents/orchestrator-maxwell.md) | Specialist agents from agents/ |
| Build terminal-native workflows | [copilot-cli](https://github.com/github/copilot-cli), [runagent](https://github.com/runagent-dev/runagent), [rag-cli](https://github.com/satoshiman/rag-cli) | Context management and repo lists |
| Ground agents in docs | [LightRAG](https://github.com/HKUDS/LightRAG), [upstash/vector-js](https://github.com/upstash/vector-js), [rag-chat](https://github.com/upstash/rag-chat) | AgentMemory and context compression |
| Connect Copilot Studio | [Copilot Studio Integration](docs/COPILOT-STUDIO-INTEGRATION.md) + [Nexus](agents/copilot-nexus.md) | API bridge, MCP server, Microsoft Agents SDK |
| Add MCP servers | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers), [playwright-mcp](https://github.com/microsoft/playwright-mcp), [github-mcp-server](https://github.com/github/github-mcp-server) | Toolsets, allowlists, token budgets |
| Reduce cost | [TOKEN-EFFICIENCY.md](docs/TOKEN-EFFICIENCY.md), [Penny](agents/token-penny.md), [Cirrus](agents/cost-cirrus.md) | Token compression, tool allowlists, cloud policies |
| Add market analysis | [OpenBB](https://github.com/OpenBB-finance/OpenBB), [finrobot](https://github.com/ai4finance-foundation/finrobot), [TradingAgents](https://github.com/tauricresearch/tradingagents) | RAG, broker APIs, risk checks |
| Build autonomous day-trading agents | [plugins/autonomous-day-trading-agent](plugins/autonomous-day-trading-agent/README.md), [Rex](agents/trading-rex.md), [Sage](agents/risk-sage.md) | Backtests, paper broker, human approval |
| Add quantum experiments | [Qiskit](https://github.com/Qiskit/qiskit), [PennyLane](https://github.com/PennyLaneAI/pennylane), [qiskit-finance](https://github.com/qiskit-community/qiskit-finance) | Helix, Qubit, optimization sidecar |
| Connect broker apps | [plugins/robinhood-trading-agent](plugins/robinhood-trading-agent/README.md), [alpaca-py](https://github.com/alpacahq/alpaca-py), [schwab-py](https://github.com/alexgolec/schwab-py) | Paper mode, broker adapters, approval gates |
| Ship mobile or web apps | [expo/expo](https://github.com/expo/expo), [create-expo-stack](https://github.com/roninoss/create-expo-stack) | Agent API backend and RAG |
| Monitor repo health | [Iris — repo-issue-iris.md](agents/repo-issue-iris.md) | GitHub MCP, REPO-HEALTH.md |
| Secure the stack | [Sentinel](agents/security-sentinel.md), [Lock](agents/secret-scanner-lock.md) | docs/SECURITY.md |
| Demo or pitch the work | [slidev](https://github.com/slidevjs/slidev), [marpit](https://github.com/marp-team/marpit), [awesome-hackathon](https://github.com/HappyHackingSpace/awesome-hackathon) | Standalone only |

---

## Local Access Model

Do not think of agent access as "the whole computer or nothing." Treat it like folder-by-folder permission.

Recommended access levels:

| Level | Use for | Example |
|---|---|---|
| Workspace only | Normal coding tasks | `<PATH_TO_THIS_REPO>` |
| Project lab | Multi-repo experiments | `<PATH_TO_AGENT_LAB>` |
| Documents or Downloads | Personal file workflows | Add only the folder needed |
| Whole drive | Rare, high trust, high risk | Prefer not to do this |

The [filesystem MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) supports allowed directories and MCP Roots. The [GitHub MCP Server](https://github.com/github/github-mcp-server) supports toolsets and read-only modes so GitHub access can also be scoped.

See [docs/AGENT-ACCESS.md](docs/AGENT-ACCESS.md) and [docs/SECURITY.md](docs/SECURITY.md).

---

## Repo Structure

```text
.
├── README.md                          (this file)
├── agents/
│   ├── AGENTS-OVERVIEW.md             (master agent index — 55 agents)
│   ├── orchestrator-maxwell.md        (routes all tasks)
│   ├── repo-issue-iris.md             (repo health monitoring)
│   ├── handoff-relay.md               (context handoff for /compact)
│   ├── scheduler-cron.md              (scheduled task automation)
│   ├── research-aria.md               (research analyst)
│   ├── data-dex.md                    (data scientist)
│   ├── market-intel-orion.md          (market intelligence)
│   ├── summarizer-prism.md            (output summarizer)
│   ├── tech-watch-beacon.md           (technology watch)
│   ├── biz-analyst-clara.md           (business analyst)
│   ├── tech-planner-rho.md            (technology planning analyst)
│   ├── pitch-spark.md                 (pitch coach)
│   ├── slides-deck.md                 (slide builder)
│   ├── market-research-funnel.md      (market research)
│   ├── writer-quill.md                (technical writer)
│   ├── fullstack-atlas.md             (full-stack developer)
│   ├── mobile-stack.md                (mobile/Expo app builder)
│   ├── ui-canvas.md                   (UI/UX designer)
│   ├── api-forge-build.md             (API developer)
│   ├── pipeline-pipe.md               (CI/CD agent)
│   ├── tester-probe.md                (QA & test agent)
│   ├── test-analyst-vera.md           (test analyst)
│   ├── debugger-trace.md              (debugger)
│   ├── architect-eden.md              (software architect)
│   ├── cloud-arch-nimbus.md           (cloud architect)
│   ├── data-arch-schema.md            (data architect)
│   ├── api-bridge.md                  (API/integration architect)
│   ├── devops-volt.md                 (DevOps engineer)
│   ├── security-sentinel.md           (security auditor)
│   ├── redteam-ghost.md               (red team researcher)
│   ├── compliance-lex.md              (compliance reviewer)
│   ├── secret-scanner-lock.md         (secret scanner)
│   ├── trading-rex.md                 (autonomous day trader)
│   ├── quantum-qubit.md               (quantum finance researcher)
│   ├── portfolio-nova.md              (portfolio manager)
│   ├── risk-sage.md                   (risk officer)
│   ├── broker-connect.md              (broker integration)
│   ├── cost-cirrus.md                 (cloud cost optimizer)
│   ├── token-penny.md                 (token cost auditor)
│   ├── mcp-forge.md                   (MCP server builder)
│   ├── rag-vector.md                  (RAG & embedding manager)
│   ├── memory-recall.md               (long-term memory agent)
│   ├── knowledge-memo.md              (knowledge base manager)
│   ├── copilot-nexus.md               (Copilot Studio orchestrator)
│   ├── connector-weave.md             (connector builder)
│   ├── onboarding-guide.md            (new user onboarding)
│   ├── support-help.md                (support agent)
│   ├── quantum-lab-helix.md           (quantum lab assistant)
│   ├── git-commit-auto.md             (git commit & PR agent)
│   ├── context-auditor-lens.md        (context auditor)
│   ├── dependency-watch-delta.md      (dependency watcher)
│   ├── doc-drift-echo.md              (docs drift detector)
│   ├── incident-pulse.md              (incident responder)
│   ├── perf-bench-tempo.md            (performance benchmarker)
│   └── accessibility-ally.md          (accessibility auditor)
├── assets/
│   ├── interactive-diagram.html       (clickable flow diagrams — open in browser)
│   ├── agent-access-map.svg
│   ├── broker-app-agent-flow.svg
│   ├── cost-reduction-flow.svg
│   ├── day-trading-agent-flow.svg
│   ├── quantum-trading-agent-flow.svg
│   └── standalone-setup-flow.svg
├── cost-reduction/
│   └── README.md
├── docs/
│   ├── ADDING-PLUGINS.md              (how to add a plugin)
│   ├── AGENT-ACCESS.md
│   ├── AUTONOMOUS-DAY-TRADING.md
│   ├── BROKER-APP-INTEGRATIONS.md
│   ├── CLI-ONE-LINERS.md
│   ├── COMBINING-REPOS.md             (named stack recipes)
│   ├── COPILOT-STUDIO-INTEGRATION.md
│   ├── INTEGRATION-FLOWS.md
│   ├── MCP-SERVERS.md
│   ├── REPO-CATALOG.md
│   ├── REPO-HEALTH.md                 (repo status tracking)
│   ├── REPO-INSTRUCTIONS.md           (per-repo install/run guides)
│   ├── SECURITY.md                    (security guide)
│   ├── STANDALONE-USAGE.md
│   ├── TOKEN-EFFICIENCY.md            (token efficiency and /compact)
│   └── TRADING-MARKET-AGENTS.md
├── examples/
├── issues/                            (Iris draft reports, Maxwell logs, Relay handoffs)
├── plugins/
│   ├── README.md                      (plugin index)
│   ├── autonomous-day-trading-agent/
│   ├── robinhood-trading-agent/
│   └── quantum-trading-agent/
├── quantum/
│   ├── QUANTUM-TRADING.md
│   └── README.md
└── repo-lists/
```

---

## Source Notes

This README and the docs were built from the linked repositories plus current public docs/articles:

- [Microsoft Copilot Studio MCP connector docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Microsoft Copilot Studio REST API action docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-rest-api)
- [GitHub Copilot CLI context management](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management)
- [GitHub custom agents changelog](https://github.blog/changelog/2025-10-28-custom-agents-for-github-copilot/)
- [Claude automatic context compaction cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction)
- [GitHub topic: context-compaction](https://github.com/topics/context-compaction)
- [Fungies AI agent repository article](https://fungies.io/top-github-repositories-ai-agent-frameworks-2026/)
- [Robinhood Agentic Trading](https://robinhood.com/us/en/support/articles/agentic-trading/)
- [Alpaca paper trading docs](https://docs.alpaca.markets/docs/paper-trading)
