# Microsoft Copilot Studio Integration

Copilot Studio is a good front door when the user experience needs to live in Microsoft 365, Teams, or a business workflow. The heavy code can still live in normal repos, APIs, MCP servers, RAG services, finance agents, or quantum sidecars.

## Connection Shapes

| Shape | Use when | How it fits |
| --- | --- | --- |
| Custom connector / OpenAPI action | You have a normal REST API. | Copilot Studio calls your API bridge; the bridge calls agents, RAG, market data, or quantum services. |
| MCP custom connector | You want Copilot Studio to call MCP tools. | Register an MCP server through the connector path and expose selected tools. |
| Microsoft 365 Agents SDK backend | You want a full-code agent that can run across M365, Teams, Copilot Studio, or Webchat. | Use `microsoft/agents`, `Agents-for-net`, and toolkit repos. |
| Child or specialized agents | You want one business-facing agent that delegates to specialists. | Keep finance, quantum, repo-curation, and cost agents separate. |

## Flow: Copilot Studio To Existing Agent

```text
Copilot Studio
  -> topic/action
  -> custom connector or OpenAPI action
  -> HTTPS API bridge
  -> Squad, Microsoft Agent, Copilot CLI service, RunAgent, or custom agent
  -> response
```

Use this when the external agent is not an MCP server yet.

## Flow: Copilot Studio To MCP

```text
Copilot Studio
  -> MCP custom connector
  -> MCP server endpoint
  -> toolset: docs, GitHub, filesystem, market data, quantum job, cloud cost, etc.
  -> response
```

Use this when tools are already MCP-shaped or when you want a standard tool boundary.

## Flow: Copilot Studio To Finance/Trading Research

```text
Copilot Studio
  -> market research action
  -> API bridge
  -> OpenBB, yfinance, FinRobot, TradingAgents, or paper-trading service
  -> risk summary and source links
  -> human decision
```

This repo does not recommend live trading from Copilot Studio. Keep live order placement behind strong permissions, logs, and manual approval.

## Flow: Copilot Studio To Quantum Sidecar

```text
Copilot Studio
  -> optimization or experiment action
  -> API bridge
  -> Qiskit, PennyLane, Cirq, Q#, Braket, D-Wave, or CUDA-Q job
  -> compare with classical baseline
  -> concise explanation
```

Good use cases: portfolio optimization experiments, routing/scheduling problems, quantum machine learning demos, and research notebooks.

## Cost Notes

Copilot Studio + MCP cost is usually not a single line item. Watch these cost buckets:

- Copilot Studio licensing and message/session costs.
- Hosted API bridge compute.
- MCP server hosting.
- External APIs such as market data, broker APIs, GitHub, cloud inventory, or search.
- Model tokens from large tool schemas, large retrieved docs, and long tool outputs.
- Cloud services launched by agents.

## Cost Reduction Moves

- Expose only the MCP tools a Copilot Studio action needs.
- Use read-only connector actions unless writes are required.
- Put a small API bridge between Copilot Studio and risky tools.
- Cache market data, docs, and cloud inventory.
- Use Infracost before infrastructure changes.
- Use OpenCost for Kubernetes spend.
- Use Cloud Custodian policies for cleanup and governance.
- Summarize tool outputs before returning to the agent.

## Starter API Bridge Contract

```json
{
  "request": {
    "task": "summarize_market",
    "symbol": "MSFT",
    "mode": "research_only"
  },
  "response": {
    "summary": "string",
    "sources": ["url"],
    "risk_notes": ["string"],
    "next_actions": ["string"]
  }
}
```

Keep the bridge boring: validate inputs, call one specialist service, return small structured output.

## Repos To Pair With Copilot Studio

| Need | Repos |
| --- | --- |
| Full-code Microsoft agents | [microsoft/agents](https://github.com/microsoft/agents), [microsoft/Agents-for-net](https://github.com/microsoft/Agents-for-net), [OfficeDev/microsoft-365-agents-toolkit](https://github.com/OfficeDev/microsoft-365-agents-toolkit) |
| MCP server layer | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers), [microsoft/mcp](https://github.com/microsoft/mcp), [github/github-mcp-server](https://github.com/github/github-mcp-server) |
| Browser actions | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) |
| Docs grounding | [upstash/context7](https://github.com/upstash/context7), [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) |
| Finance research | [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB), [ai4finance-foundation/finrobot](https://github.com/ai4finance-foundation/finrobot), [tauricresearch/tradingagents](https://github.com/tauricresearch/tradingagents) |
| Quantum experiments | [Qiskit/qiskit](https://github.com/Qiskit/qiskit), [PennyLaneAI/pennylane](https://github.com/PennyLaneAI/pennylane), [microsoft/qsharp](https://github.com/microsoft/qsharp) |
| Cost controls | [infracost/infracost](https://github.com/infracost/infracost), [opencost/opencost](https://github.com/opencost/opencost), [cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian) |

## Source Links

- [Add an MCP server to Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Connect Copilot Studio agents to REST APIs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-rest-api)
- [Microsoft 365 Agents SDK](https://github.com/microsoft/agents)
