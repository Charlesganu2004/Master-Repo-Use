# Repo Catalog

Use this file as the detailed reading path. Each row explains what the repo is for, how to get started, and where it fits in the bigger system.

Replace `REVIEWED_VERSION` with an exact package release you inspected; never use `latest` or automatic yes.

## System View

| Layer | Job | Repos to inspect first |
| --- | --- | --- |
| Agent orchestration | Agent roles, teams, tools, task routing | `squad`, `microsoft/agents`, `Agents-for-net`, `copilot-cli` |
| Knowledge and memory | Search docs, retrieve facts, keep durable project memory | `LightRAG`, `AugmentR`, `rag-chat`, `vector-js`, `agentmemory` |
| Context control | Reduce token pressure and keep long sessions coherent | `LLMLingua`, `Prompt-Compression-Survey`, `lean-ctx` |
| MCP server layer | Connect tools through explicit, scoped server boundaries | `modelcontextprotocol/servers`, `github-mcp-server`, `playwright-mcp`, `context7` |
| Copilot Studio front door | Connect business-facing agents to APIs, MCP, and code agents | `microsoft/agents`, `Agents-for-net`, MCP connector docs |
| Product surface | Mobile/web app shell, docs structure, user experience | `expo`, `create-expo-stack`, `github/docs` |
| Cloud and deployment | .NET Aspire, YARP, Azure Container Apps, hosted services | Aspire and cloud-native samples |
| Finance and trading research | Market analysis, backtesting, paper trading, broker research | `OpenBB`, `TradingAgents`, `FinRobot`, `FinRL`, `robin_stocks` |
| Autonomous day trading | Signal generation, backtests, paper orders, investing allocations | `autonomous-day-trading-agent`, `Vibe-Trading`, `alpaca-mcp-server` |
| Quantum sidecar | Standalone quantum learning plus optional optimization/QML experiments | `Qiskit`, `PennyLane`, `Cirq`, `qiskit-finance` |
| Cost reduction | Reduce token, API, MCP, and cloud spend | `Infracost`, `OpenCost`, `Cloud Custodian`, `token-optimizer-mcp` |
| Demo and story | Standalone hackathon resources, Markdown slides, pitch decks | `awesome-hackathon`, `slidev`, `marpit`, `pitch-deck` |
| Spatial and 3D perception | Reconstruct scenes, reason about space, map in real time | `vggt`, `Depth-Anything-3`, `gsplat`, `Open3D`, `stella_vslam` |
| Live retrieval | Keep a RAG index fresh as the corpus changes | `graphiti`, `pathway`, `vespa`, `ragflow`, `pylate` |
| Models and serving | Choose an open-weight model and a serving stack | `vllm`, `sglang`, `llama.cpp`, `litellm`, `Qwen3.6` |
| Supply-chain security | Scan a dependency before you trust it | `gitleaks`, `trivy`, `osv-scanner`, `semgrep`, `scorecard` |
| Spatial and 3D perception | Reconstruct scenes, reason about space, map in real time | `vggt`, `Depth-Anything-3`, `gsplat`, `Open3D`, `stella_vslam` |
| Live retrieval | Keep a RAG index fresh as the corpus changes | `graphiti`, `pathway`, `vespa`, `ragflow`, `pylate` |
| Models and serving | Choose an open-weight model and a serving stack | `vllm`, `sglang`, `llama.cpp`, `litellm`, `Qwen3.6` |
| Supply-chain security | Scan a dependency before you trust it | `gitleaks`, `trivy`, `osv-scanner`, `semgrep`, `scorecard` |
| Access | Give agents safe paths to files and GitHub | MCP filesystem server, GitHub MCP server |

## Integration Flow

Use [docs/INTEGRATION-FLOWS.md](INTEGRATION-FLOWS.md) as the clean map. The short form:

```text
CLI / VS Code / Copilot Studio / app UI
  -> agent framework
  -> MCP tools and APIs
  -> RAG, memory, context, and cost controls
  -> local repo, cloud service, market analysis, or quantum sidecar
```

Pitch and hackathon stay standalone. They can consume summaries, screenshots, and demo notes, but they are not part of the main runtime stack.

Use [docs/STANDALONE-USAGE.md](STANDALONE-USAGE.md) when you want to try any lane by itself on a different computer before connecting it to the full stack.

Open the interactive diagram: **[assets/interactive-diagram.html](../assets/interactive-diagram.html)** — 6 tabs covering main flow, standalone paths, combination stacks, trading safety gates, cost controls, and the 55-agent roster. Works offline in any browser.

```powershell
# Open directly in default browser, PowerShell:
Start-Process (Join-Path $PWD "assets\interactive-diagram.html")
```

```bash
# WSL/Bash:
xdg-open assets/interactive-diagram.html
```

The diagram is the reading order for the catalog: choose a lane, inspect the first few repos in that lane, run the lane standalone, then connect it to the core runtime only when the sample works.

## Agent Frameworks

Status key: `active` = actively maintained · `experimental` = works but not production-hardened · `stale` = no recent activity, uncertain future · `deprecated` = officially replaced or unsupported

| Repo | Use it when | Fast start | Connects to | Status |
| --- | --- | --- | --- | --- |
| [bradygaster/squad](https://github.com/bradygaster/squad) | You want agent teams for projects and local automation. | `npm install -g @bradygaster/squad-cli` | Works well with repo lists, RAG, memory, and CLI workflows. | active |
| [bradygaster/Squad-IRL](https://github.com/bradygaster/Squad-IRL) | You want real-world examples for Squad. | Clone and run the sample that matches your stack. | Companion examples for `squad`. | active |
| [bradygaster/CustomAgent](https://github.com/bradygaster/CustomAgent) | You want a small custom-agent reference. | Clone, inspect scripts, adapt locally. | Good for prompt and persona experiments. | experimental |
| [bradygaster/MultiAgent](https://github.com/bradygaster/MultiAgent) | You want a C# multi-agent sample. | Clone and run with the .NET SDK. | Good bridge to Microsoft agent and Aspire samples. | active |
| [microsoft/agents](https://github.com/microsoft/agents) | You want the Microsoft 365 Agents SDK across channels. | Start from the samples folder or Microsoft quickstarts. | Teams, Microsoft 365 Copilot, Copilot Studio, Webchat. | active |
| [OfficeDev/microsoft-365-agents-toolkit](https://github.com/OfficeDev/microsoft-365-agents-toolkit) | You want scaffolding, debugging, validation, and deployment tooling. | `npm install -g @microsoft/m365agentstoolkit-cli`; run `atk -h`. | Pairs with VS Code, Visual Studio, Microsoft 365 Agents SDK. | active |
| [microsoft/Agents-for-net](https://github.com/microsoft/Agents-for-net) | You want .NET components for Microsoft 365 Agents SDK. | `dotnet new web`; `dotnet add package Microsoft.Agents.Hosting.AspNetCore`. | Best with .NET samples, Aspire, and Teams/M365 surfaces. | active |
| [runagent-dev/runagent](https://github.com/runagent-dev/runagent) | You want a CLI-first way to run or deploy agents. | `pip install runagent` | Useful for terminal workflows and agent service packaging. | experimental |
| [github/copilot-sdk](https://github.com/github/copilot-sdk) | You want to embed Copilot Agent behavior into apps/services. | Clone and follow the SDK docs for your platform. | Works with Copilot Agent, MCP, remote sessions, hooks. | active |
| [github/copilot-cli](https://github.com/github/copilot-cli) | You want Copilot coding agent in the terminal. | `npm install -g @github/copilot` | Works with custom agents, MCP servers, `/context`, `/compact`, and session resume. | active |

## RAG, Knowledge, And Memory

| Repo | Use it when | Fast start | Connects to | Status |
| --- | --- | --- | --- | --- |
| [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | You need fast retrieval-augmented generation over docs. | `uv tool install "lightrag-hku[api]"` | Feed agents with project docs and local knowledge. | active |

| [upstash/rag-chat](https://github.com/upstash/rag-chat) | You want a quick TypeScript SDK for RAG chat. | `pnpm add @upstash/rag-chat` or `npm i @upstash/rag-chat`. | Pairs with Upstash Vector. | active |
| [upstash/vector-js](https://github.com/upstash/vector-js) | You need a TypeScript client for Upstash Vector. | `npm install @upstash/vector` | Use as vector storage under RAG apps. | active |
| [satoshiman/rag-cli](https://github.com/satoshiman/rag-cli) | You want local-first RAG from the command line. | Clone, `npm install`, then use the CLI commands from its README. | Good for personal docs and local notes. | experimental |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | You want persistent memory for coding agents. | `npm install -g @agentmemory/agentmemory` | Complements RAG by storing durable project facts and decisions. | experimental |

## Context And Token Management

| Repo or article | Use it when | Fast start | Connects to |
| --- | --- | --- | --- |
| [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua) | You want prompt compression research and Python tooling. | `pip install llmlingua` | Useful for custom RAG/context pipelines. |
| [ZongqianLi/Prompt-Compression-Survey](https://github.com/ZongqianLi/Prompt-Compression-Survey) | You want the research map before choosing a compression method. | Read the survey and linked papers. | Helps compare prompt compression strategies. |
| [GitHub Copilot CLI context docs](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management) | You want to understand `/context`, `/compact`, checkpoints, and long CLI sessions. | Install Copilot CLI, then use `/context` and `/compact` inside sessions. | Directly relevant to CLI agent usage. |
| [DeepWiki Copilot CLI context/token management](https://deepwiki.com/github/copilot-cli/3.7-context-and-token-management) | You want a source-oriented view of Copilot CLI context behavior. | Read alongside official GitHub docs. | Explains context categories, compaction, and checkpoint ideas. |
| [Claude compaction docs](https://platform.claude.com/docs/en/build-with-claude/compaction) | You are building API-level long-running agent workflows. | Add a compaction edit strategy in API requests. | Good design pattern even when using other model providers. |
| [Claude automatic context compaction cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction) | You want a worked example for when and how to compact. | Study the threshold and summary loop. | Helps design custom compaction flows. |

Practical context rule:

```text
Preserve decisions, file paths, commands, errors, current plan, and next steps.
Compress repetitive logs, raw search output, duplicated instructions, and stale discussion.
```

## Copilot Studio And MCP Integration

| Repo or docs | Use it when | Connects to |
| --- | --- | --- |
| [Microsoft Copilot Studio MCP connector docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent) | You want Copilot Studio to call MCP tools. | MCP servers, API bridges, Microsoft agents. |
| [Microsoft Copilot Studio REST API action docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-rest-api) | You want Copilot Studio to call normal REST APIs. | API bridge for agents, RAG, finance, quantum, or cloud cost. |
| [microsoft/agents](https://github.com/microsoft/agents) | You want the Microsoft 365 Agents SDK. | Teams, Copilot Studio, Webchat, M365. |
| [microsoft/Agents-for-net](https://github.com/microsoft/Agents-for-net) | You want .NET agent components. | ASP.NET Core, Aspire, Teams/M365 surfaces. |
| [OfficeDev/microsoft-365-agents-toolkit](https://github.com/OfficeDev/microsoft-365-agents-toolkit) | You want tooling for scaffolding and deployment. | VS Code and Microsoft 365 workflows. |

Detailed guide: [docs/COPILOT-STUDIO-INTEGRATION.md](COPILOT-STUDIO-INTEGRATION.md).

## MCP Servers

| Repo | Use it when | Connects to |
| --- | --- | --- |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | You want reference servers such as filesystem and memory. | Local files, Git, fetch, memory. |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | You want to build MCP servers in TypeScript. | Custom tools and web services. |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | You want to build MCP servers in Python. | Data, finance, quantum, notebooks. |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | You want to test/debug MCP servers. | Local MCP development. |
| [microsoft/mcp](https://github.com/microsoft/mcp) | You want Microsoft's MCP catalog. | Microsoft ecosystem tooling. |
| [microsoftdocs/mcp](https://github.com/microsoftdocs/mcp) | You want Microsoft MCP docs source. | Official doc tracking. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | You want browser automation through MCP. | App verification, scraping with care. |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | You want GitHub repo, issue, PR, Actions, and security tools. | Repo automation and PR review. |
| [upstash/context7](https://github.com/upstash/context7) | You want current docs available to coding agents. | Lower hallucination and fewer stale-doc loops. |
| [awslabs/mcp](https://github.com/awslabs/mcp) | You want AWS-focused MCP servers. | Cloud workflows and AWS APIs. |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | You want broad MCP discovery. | Research list, not automatic install. |
| [microsoft/lets-learn-mcp-python](https://github.com/microsoft/lets-learn-mcp-python) | You want a Python MCP learning path. | Custom Python MCP tools. |

Detailed guide: [docs/MCP-SERVERS.md](MCP-SERVERS.md).

## Finance, Trading, And Market Analysis

| Repo or docs | Use it when | Connects to | Status |
| --- | --- | --- | --- |
| [jmfernandes/robin_stocks](https://github.com/jmfernandes/robin_stocks) | You want Robinhood research/account interactions from Python. | Standalone Robinhood research lane. | experimental |
| [siropkin/robinhood-ai-trading-bot](https://github.com/siropkin/robinhood-ai-trading-bot) | You want a simple Robinhood bot example to study. | Educational bot patterns. | experimental |
| [Robinhood Crypto API docs](https://docs.robinhood.com/crypto/trading/) | You want official Robinhood crypto API reference. | Official crypto trading API behavior. | active |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | You need a financial data platform for analysts, quants, and AI agents. | Market research agents and Copilot Studio bridges. | active |
| [tauricresearch/tradingagents](https://github.com/tauricresearch/tradingagents) | You want a multi-agent LLM trading framework. | Market agent workflows. | active |
| [HKUDS/AI-Trader](https://github.com/HKUDS/AI-Trader) | You want agent-native automated trading research. | Paper-trading architecture. | experimental |
| [MingyuJ666/Stockagent](https://github.com/MingyuJ666/Stockagent) | You want simulated stock-agent research. | Backtests and simulated markets. | experimental |
| [ai4finance-foundation/finrobot](https://github.com/ai4finance-foundation/finrobot) | You want LLM financial analysis agents. | Reports, analysis, RAG. | active |
| [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | You want financial LLM research. | Sentiment and finance language tasks. | active |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | You want financial reinforcement learning. | Backtesting and portfolio experiments. | active |
| [quantconnect/Lean](https://github.com/quantconnect/Lean) | You want an algorithmic trading engine. | Strategy research and paper/live modes. | active |
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | You want crypto trading bot/backtesting tooling. | Crypto research and simulation. | active |

| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | You want quick market data. | Research scripts and notebooks. | active |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | You want pandas technical analysis indicators. | Feature engineering. | experimental |
| [bukosabino/ta](https://github.com/bukosabino/ta) | You want technical analysis indicators. | Feature engineering. | stale |

| [georgezouq/awesome-ai-in-finance](https://github.com/georgezouq/awesome-ai-in-finance) | You want wider AI finance discovery. | Research queue. | active |

Detailed guide: [docs/TRADING-MARKET-AGENTS.md](TRADING-MARKET-AGENTS.md).

Broker app integration guide: [docs/BROKER-APP-INTEGRATIONS.md](BROKER-APP-INTEGRATIONS.md).

Autonomous day-trading guide: [docs/AUTONOMOUS-DAY-TRADING.md](AUTONOMOUS-DAY-TRADING.md).

## Autonomous Day-Trading And Investing Agents

This lane is for agents and plugins that can generate trading signals, paper trade, and propose investment allocations. It cannot guarantee profit and should stay paper-first. See [docs/AUTONOMOUS-DAY-TRADING.md](AUTONOMOUS-DAY-TRADING.md) for the full Rex → Sage → human approval flow.

| Repo or docs | Use it when | Connects to | Status |
| --- | --- | --- | --- |
| [plugins/autonomous-day-trading-agent](../plugins/autonomous-day-trading-agent/README.md) | You want this repo's safe standalone plugin scaffold. | CSV signals, toy backtest, paper broker, invest-plan, risk gate. | active |
| [agents/trading-rex.md](../agents/trading-rex.md) | You want Rex, the paper-first trading agent. | Connects to Sage, Maxwell, Alpaca paper, and audit log. | active |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | You want agentic trading experiments around Robinhood Agentic Trading/MCP ideas. | Broker app research and paper trading. | experimental |
| [TradingAgents-AI/TradingAgents](https://github.com/TradingAgents-AI/TradingAgents) | You want another TradingAgents implementation to compare. | Multi-agent market research. | experimental |

| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | You want broker tools exposed through MCP. | Paper broker tools before live toolsets. | active |
| [Robinhood Agentic Trading](https://robinhood.com/us/en/support/articles/agentic-trading/) | You want Robinhood's agent-oriented route where available. | Official broker route review. |

## Quantum Computing

Quantum is standalone first and sidecar second. It is not the main focus.

| Repo | Use it when | Connects to |
| --- | --- | --- |
| [Qiskit/qiskit](https://github.com/Qiskit/qiskit) | You want IBM's open-source quantum SDK. | Simulators, IBM Quantum, finance/optimization demos. |
| [qiskit-community/qiskit-finance](https://github.com/qiskit-community/qiskit-finance) | You want quantum finance examples. | Portfolio optimization experiments. |
| [qiskit-community/qiskit-machine-learning](https://github.com/qiskit-community/qiskit-machine-learning) | You want QML tooling. | Quantum/classical model comparisons. |
| [qiskit-community/qiskit-optimization](https://github.com/qiskit-community/qiskit-optimization) | You want optimization workflows. | Scheduling, portfolio, routing experiments. |
| [PennyLaneAI/pennylane](https://github.com/PennyLaneAI/pennylane) | You want differentiable quantum programming. | QML and hybrid models. |
| [PennyLaneAI/pennylane-qiskit](https://github.com/PennyLaneAI/pennylane-qiskit) | You want PennyLane with Qiskit devices. | Hybrid QML experiments. |
| [quantumlib/Cirq](https://github.com/quantumlib/Cirq) | You want Google's circuit framework. | Circuit simulation. |
| [microsoft/qsharp](https://github.com/microsoft/qsharp) | You want Q#, resource estimation, and katas. | Microsoft quantum learning path. |
| [aws/amazon-braket-sdk-python](https://github.com/aws/amazon-braket-sdk-python) | You want Amazon Braket device access. | Cloud quantum jobs. |
| [dwavesystems/dwave-ocean-sdk](https://github.com/dwavesystems/dwave-ocean-sdk) | You want D-Wave Ocean tools. | Annealing/optimization experiments. |
| [unitaryfund/mitiq](https://github.com/unitaryfund/mitiq) | You want error mitigation. | Hardware/simulator quality experiments. |
| [NVIDIA/cuda-quantum](https://github.com/NVIDIA/cuda-quantum) | You want heterogeneous quantum-classical workflows. | Advanced quantum/classical compute. |
| [qosf/awesome-quantum-software](https://github.com/qosf/awesome-quantum-software) | You want a larger quantum software list. | Discovery. |

Detailed guide: [quantum/README.md](../quantum/README.md).

Quantum trading and investing guide: [quantum/QUANTUM-TRADING.md](../quantum/QUANTUM-TRADING.md).

## Cost Reduction

| Repo | Use it when | Connects to |
| --- | --- | --- |
| [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | You want MCP token optimization experiments. | MCP cost control. |
| [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | You want lean context engineering tools. | Agent context cleanup. |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | You want headroom/context tracking ideas. | Long sessions and budget checks. |
| [infracost/infracost](https://github.com/infracost/infracost) | You want infrastructure cost estimates. | PR review, CI, GitHub MCP. |
| [infracost/agent-skills](https://github.com/infracost/agent-skills) | You want Infracost agent skills. | Coding-agent cost review. |
| [opencost/opencost](https://github.com/opencost/opencost) | You want Kubernetes cost monitoring. | K8s and cloud agents. |
| [opencost/opencost-helm-chart](https://github.com/opencost/opencost-helm-chart) | You want OpenCost Helm deployment. | Kubernetes setup. |
| [cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian) | You want cloud governance and cleanup policies. | Cloud cost cleanup agents. |
| [mlabouardy/komiser](https://github.com/mlabouardy/komiser) | You want cloud resource inventory and cost visibility. | Multi-cloud review. |
| [cloudquery/cloudquery](https://github.com/cloudquery/cloudquery) | You want cloud asset inventory in databases. | Queryable inventory for agents. |
| [turbot/steampipe](https://github.com/turbot/steampipe) | You want SQL over cloud APIs. | CLI cost/security queries. |
| [phildougherty/infracost_mcp](https://github.com/phildougherty/infracost_mcp) | You want an Infracost MCP experiment. | Agent-based infra cost review. |
| [jasonwilbur/cloud-cost-mcp](https://github.com/jasonwilbur/cloud-cost-mcp) | You want a cloud-cost MCP concept. | Cloud spend analysis tools. |
| [OptimNow/finops-mcp-resources](https://github.com/OptimNow/finops-mcp-resources) | You want FinOps MCP resources. | MCP cost/FinOps research. |
| [OptimNow/cloud-finops-skills](https://github.com/OptimNow/cloud-finops-skills) | You want cloud FinOps agent skills. | Agent cost governance. |
| [aarora79/aws-cost-explorer-mcp-server](https://github.com/aarora79/aws-cost-explorer-mcp-server) | You want AWS Cost Explorer via MCP. | AWS spend agents. |
| [nozomi-koborinai/gcp-cost-mcp-server](https://github.com/nozomi-koborinai/gcp-cost-mcp-server) | You want GCP cost data via MCP. | GCP spend agents. |

Detailed guide: [cost-reduction/README.md](../cost-reduction/README.md).

## App, Mobile, And Structure

| Repo | Use it when | Fast start | Connects to |
| --- | --- | --- | --- |
| [expo/examples](https://github.com/expo/examples) | You want examples for Expo APIs and integrations. | Clone the example that matches your app idea. | Good front end for agent demos. |
| [expo/expo](https://github.com/expo/expo) | You want the main universal React Native framework. | Use Expo docs and CLI setup. | Mobile, web, and cross-platform app shell. |
| [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) | You want a serious Expo/React Native template with TypeScript and tooling. | Follow template README setup. | Strong app foundation for production-ish demos. |
| [roninoss/create-expo-stack](https://github.com/roninoss/create-expo-stack) | You want to generate an Expo stack with selected routing/styling/backend choices. | Use the CLI from its README, or start at [rn.new](https://rn.new). | Fast app scaffolding. |
| [github/docs](https://github.com/github/docs) | You want a large, mature docs-site structure to learn from. | Clone and inspect docs/content organization. | Useful pattern for this repo's future docs. |

## Cloud, Aspire, And Samples

| Repo | Use it when | Fast start | Connects to |
| --- | --- | --- | --- |
| [bradygaster/Aspiregregator](https://github.com/bradygaster/Aspiregregator) | You want a .NET Aspire RSS reader sample. | Clone and run with .NET Aspire prerequisites. | Shows service orchestration patterns. |

| [bradygaster/dotnet-cloud-native-build-2023](https://github.com/bradygaster/dotnet-cloud-native-build-2023) | You want .NET cloud-native sample material. | Clone and follow the repo workshop/sample flow. | Good learning path for cloud-native .NET. |

## Hackathon, Pitch, And Slides Standalone

Pitch and hackathon tools are standalone support. They can consume project summaries, screenshots, and demo notes, but they do not belong in the main agent runtime.

| Repo | Use it when | Fast start | Standalone note |
| --- | --- | --- | --- |
| [HappyHackingSpace/awesome-hackathon](https://github.com/HappyHackingSpace/awesome-hackathon) | You need hackathon resources and build/pitch tips. | Read by category before a sprint. | Planning and scope support only. |
| [slidevjs/slidev](https://github.com/slidevjs/slidev) | You want developer-friendly Markdown slides. | `npm init slidev` | Output/presentation layer only. |
| [marp-team/marpit](https://github.com/marp-team/marpit) | You want a slimmer Markdown-to-slide framework. | Clone or use Marp tooling around it. | Output/presentation layer only. |
| [dkorobtsov/pitch-deck](https://github.com/dkorobtsov/pitch-deck) | You want pitch-deck methodology and review prompts. | Clone and inspect plugin/methodology docs. | Story review only. |

## MCP And Agent Access

| Repo | Use it when | Fast start | Connects to |
| --- | --- | --- | --- |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | You need reference MCP servers, especially filesystem access. | Filesystem command: `npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION [allowed-dir]` | Lets agents read/write only approved local directories. |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | You want agents to work with GitHub repos, issues, PRs, Actions, and security tools. | Docker: `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server` | Add GitHub capabilities with token scopes and toolsets. |

## Article And Topic Discoveries

These are not all required. Treat them as an expansion queue.

### From the Fungies AI agent repos article

The article highlights these high-traction agent and AI application repos:

| Repo | Why it is worth scanning |
| --- | --- |
| [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | Autonomous agent pioneer and useful historical reference. |
| [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | Visual agent/workflow builder. |
| [langgenius/dify](https://github.com/langgenius/dify) | Production-oriented app and workflow platform. |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | Foundational chains/tools/agents ecosystem. |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Terminal AI agent from Google. |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Browser automation for agents. |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | RAG engine with agent capabilities. |
| [lobehub/lobe-chat](https://github.com/lobehub/lobe-chat) | Multi-agent/chat productivity UI. |
| [geekan/MetaGPT](https://github.com/geekan/MetaGPT) | Role-based multi-agent software company pattern. |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | Financial data platform that can power analyst agents. |
| [microsoft/autogen](https://github.com/microsoft/autogen) | Microsoft multi-agent conversation framework. |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | Learning path for agent basics. |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Persistent memory layer. |
| [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | Visual flow builder for AI apps. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | Role-playing agent crews. |
| [mudler/LocalAI](https://github.com/mudler/LocalAI) | Local model serving. |
| [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | AI productivity studio. |
| [agno-agi/agno](https://github.com/agno-agi/agno) | Agentic software framework. |
| [mindsdb/mindsdb](https://github.com/mindsdb/mindsdb) | AI analytics over live data. |
| [ToolJet/ToolJet](https://github.com/ToolJet/ToolJet) | Internal tool builder with AI app potential. |

### From GitHub topic `context-compaction`

The topic is small and experimental. Repos worth scanning:

| Repo | Note |
| --- | --- |
| [LQF-dev/Zero-code](https://github.com/LQF-dev/Zero-code) | Engineering AI code generation platform with layered context compression. |
| [wangcangshu/codex-desktop-thread-rescue](https://github.com/wangcangshu/codex-desktop-thread-rescue) | Local GUI workaround for stuck Codex Desktop compaction states. |
| [Sapience-AI/openclaw-middleware-suite](https://github.com/Sapience-AI/openclaw-middleware-suite) | Middleware suite including compaction, approvals, PII redaction, and guardrails. |
| [huahuadeliaoliao/codex-session-compact-collapse](https://github.com/huahuadeliaoliao/codex-session-compact-collapse) | Session compaction/handoff preservation experiment. |
| [Yuchen20/Context-Crumb](https://github.com/Yuchen20/Context-Crumb) | Compact unstructured docs with a tiny local model. |
| [zzallirog/weighted-compact](https://github.com/zzallirog/weighted-compact) | Inspectable weighted compaction for Claude Code. |
| [soolaugust/0CompactMem](https://github.com/soolaugust/0CompactMem) | Persistent memory and MCP-native context approach. |
| [guorunjie/codex-relay-baton-guardian](https://github.com/guorunjie/codex-relay-baton-guardian) | Codex long-task handoff and recovery idea. |
| [YuhaoLin2005/compact-counter-concept](https://github.com/YuhaoLin2005/compact-counter-concept) | Compaction count as a context health metric. |
| [RyanWeb31110/codex-thread-handoff](https://github.com/RyanWeb31110/codex-thread-handoff) | Codex thread recovery and handoff skill. |

## Spatial: 3D Reconstruction And Scene Representation

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Single plain-transformer model that recovers spatially consistent geometry from any number of views, posed or unposed — monocular… | Apache-2.0 — FLAG — the largest/Giant checkpoints are CC BY-NC 4 | vetted |
| [colmap/colmap](https://github.com/colmap/colmap) | General-purpose Structure-from-Motion and Multi-View Stereo pipeline with GUI and CLI, for ordered and unordered image… | NOASSERTION | vetted, see notes |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | End-to-end transformer that regresses factored metric 3D geometry from images, calibration, poses and/or depth, covering 12+… | Apache-2.0 — FLAG — default released model weights are CC-BY-NC 4 | vetted, see notes |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | Feed-forward transformer that infers camera parameters, depth maps, point maps and 3D point tracks from 1 to hundreds of unposed… | NOASSERTION — FLAG — custom Meta license (GitHub reports NOASSERTION) | vetted, see notes |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | Native C++23/CUDA application to train, inspect, edit, automate and export 3D Gaussian Splatting scenes, with a real-time… | GPL-3.0 — FLAG — GPL-3 | vetted, see notes |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | Modular PyTorch framework for neural radiance fields — a common API across NeRF variants plus data parsers, a web viewer, and… | Apache-2.0 | vetted, see notes |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | Free, open-source, browser-based 3D Gaussian Splat editor for inspecting, cleaning, compressing, cropping and publishing splat… | MIT | vetted |

## Spatial: Reasoning VLMs And World Models

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [allenai/molmoact](https://github.com/allenai/molmoact) | Ai2's action reasoning model: a VLA that emits explicit spatial reasoning traces — depth perception tokens and 2D visual trace… | Apache-2.0 | vetted, see notes |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | One-for-all multimodal evaluation toolkit spanning text, image, video and audio tasks — a unified harness with hundreds of… | NOASSERTION | vetted, see notes |
| [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | Meta's self-supervised video world model — PyTorch code and weights for learning predictive latent representations from video,… | MIT | vetted |
| [FlagOpen/RoboBrain2.5](https://github.com/FlagOpen/RoboBrain2.5) | BAAI's embodied brain VLM ('Depth in Sight, Time in Mind') for unified spatial perception, affordance/pointing prediction,… | Apache-2.0 | vetted, see notes |
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | Open platform of world foundation models, datasets and tools for Physical AI — the Cosmos 3 omnimodal family (Super 64B / Nano… | NOASSERTION — FLAG: this is an open model/data license, not a standard OSI permissive license like… | vetted, see notes |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | Physical Intelligence's official open-source VLA models and packages: π₀ (flow-based VLA), π₀-FAST (autoregressive VLA using the… | Apache-2.0 — FLAG: ships a separate LICENSE_GEMMA | vetted |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | Open pipeline for synthesizing spatial VQA training data — lifts 2D images into metric 3D via depth/segmentation/point clouds,… | Apache-2.0 | vetted |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | Real-time streaming interactive world model with long-horizon memory — generates controllable, explorable video environments… | MIT — FLAG: verify the Hugging Face model card separately, as Skywork weight releases sometimes… | vetted, see notes |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | Official repo and evaluation implementation of VSI-Bench: 288 real indoor video sequences (ScanNet, ScanNet++, ARKitScenes) and… | Apache-2.0 | vetted |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | VLM fine-tuned for spatial affordance prediction — takes a language instruction and returns 2D image keypoints indicating where… | Apache-2.0 — FLAG: built on the LLaVA/Vicuna stack, so released checkpoints inherit Llama community… | vetted, see notes |

## Spatial: AR, Robotics Mapping, And SLAM

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [borglab/gtsam](https://github.com/borglab/gtsam) | C++/Python factor-graph optimization library for smoothing and mapping — batch and incremental (iSAM2) solvers, IMU… | NOASSERTION | vetted, see notes |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | Modern C++/Python library for 3D data processing: point clouds, meshes, registration/ICP, RGB-D odometry and integration, plus a… | NOASSERTION | vetted, see notes |
| [koide3/glim](https://github.com/koide3/glim) | Versatile range-based 3D mapping framework: GPU-accelerated LiDAR / LiDAR-inertial SLAM with global trajectory optimization,… | MIT | vetted |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | Builds hierarchical 3D scene graphs (objects, places, rooms, buildings) from live sensor data in real time, with loop closure… | BSD-2-Clause | vetted |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | CUDA-accelerated 3D Gaussian splatting rasterization library with a PyTorch API — the rendering engine behind Nerfstudio's… | Apache-2.0 — non-commercial | vetted |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | GPU-accelerated TSDF and ESDF volumetric mapping library for robots with RGB-D or LiDAR input, producing distance fields suitable… | NOASSERTION | vetted, see notes |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | Rust-based logging and visualization SDK/viewer for multimodal spatial and temporal data — point clouds, transforms/TF trees,… | Apache-2.0 | vetted |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | Real-time dense monocular SLAM that uses the MASt3R two-view 3D reconstruction prior for tracking, dense pointmap fusion, and… | NOASSERTION — CC BY-NC-SA 4 | vetted, see notes |
| [rpng/open_vins](https://github.com/rpng/open_vins) | Filter-based (MSCKF) visual-inertial odometry/navigation platform with sliding-window state estimation, online calibration, and… | GPL-3.0 — GPL-3.0 — FLAG | vetted, see notes |
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | Real-time monocular / stereo / RGB-D visual SLAM framework (the maintained continuation of OpenVSLAM) with map save-load and… | NOASSERTION | vetted, see notes |

## Live, Streaming, And Incremental RAG

Full guide: [docs/LIVE-RAG.md](LIVE-RAG.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | Lightweight, low-dependency unified Python API over essentially every reranking and cross-encoder | Apache-2.0 — non-commercial | vetted |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | Pytest-style LLM evaluation framework with RAG-specific metrics: faithfulness, answer relevancy, contextual… | Apache-2.0 | vetted, see notes |
| [getzep/graphiti](https://github.com/getzep/graphiti) | Framework for building temporal knowledge graphs that AI agents query, where every edge carries a validity | Apache-2.0 | vetted, see notes |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | Open-source RAG engine built on deep document understanding (DeepDoc OCR / table / layout recognition), fused with agent… | Apache-2.0 | vetted, see notes |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | Production-grade multi-agent deep-research system using a supervisor/researcher architecture with parallel isolated-context… | MIT | vetted |
| [lightonai/pylate](https://github.com/lightonai/pylate) | Library for training, fine-tuning, and serving late-interaction (ColBERT-family) multi-vector retrieval models, built on Sentence… | MIT | vetted |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | Self-hostable AI search and chat platform with 40+ enterprise connectors (Slack, Drive, Confluence, Jira, GitHub, | NOASSERTION — FLAG - mixed | vetted, see notes |
| [paradedb/paradedb](https://github.com/paradedb/paradedb) | Postgres extension suite adding BM25 full-text search, vector retrieval, and analytics inside the | AGPL-3.0 — FLAG - AGPL-3 | vetted, see notes |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | Python ETL/stream-processing framework on a Rust Differential Dataflow engine, with LLM tooling and an in-memory real-time vector… | NOASSERTION — FLAG - Business Source License 1 | vetted, see notes |
| [vespa-engine/vespa](https://github.com/vespa-engine/vespa) | Big-data serving and AI search platform combining vector, lexical, and structured retrieval with learned | Apache-2.0 | vetted, see notes |

## Open-Weight LLMs And Serving Stacks

Full guide: [docs/LLM-MODELS.md](LLM-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | Few-shot evaluation framework covering 60+ academic benchmarks with pluggable backends (HF Transformers, vLLM, SGLang,… | MIT | vetted, see notes |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | C/C++ LLM inference with minimal setup, GGUF weights, and an included OpenAI-compatible server; runs CPU-only or GPU-accelerated… | MIT | vetted, see notes |
| [QwenLM/Qwen3.6](https://github.com/QwenLM/Qwen3.6) | Official repo for the Qwen3.5 and Qwen3.6 model generations - dense and MoE open-weight models spanning roughly 0.8B to 35B-A3B,… | Apache-2.0 | vetted |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | Serving framework for LLMs and multimodal models built around RadixAttention prefix caching and a structured-generation frontend… | Apache-2.0 | vetted, see notes |
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | Transformers-compatible library for applying quantisation and compression algorithms (GPTQ, AWQ, SmoothQuant, FP8/NVFP4,… | Apache-2.0 | vetted, see notes |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | High-throughput, memory-efficient LLM inference and serving engine with an OpenAI-compatible API | Apache-2.0 | vetted, see notes |
| [zai-org/GLM-5](https://github.com/zai-org/GLM-5) | Official repo for the GLM-5 series - a 744B-parameter MoE with ~40B active per token, 1M-token context, released in BF16 and FP8,… | Apache-2.0 | vetted |

## Security Scanning Tools

Full guide: [docs/SECURITY-SCANNING.md](SECURITY-SCANNING.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [anchore/syft](https://github.com/anchore/syft) | CLI and Go library that generates a Software Bill of Materials from container images, filesystems, and archives across dozens of… | Apache-2.0 | vetted, see notes |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | All-in-one scanner covering container images, filesystems, git repos, VM images, Kubernetes clusters and cloud accounts for CVEs,… | Apache-2.0 | vetted, see notes |
| [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) | Policy-as-code static analyzer for infrastructure as code — Terraform, CloudFormation, Kubernetes manifests, Helm, ARM, Bicep,… | Apache-2.0 | vetted, see notes |
| [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | Python CLI and REST server that scans MCP servers and their tool definitions for prompt injection, tool poisoning, rug pulls, and… | Apache-2.0 | vetted, see notes |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | Go CLI that detects hardcoded secrets (API keys, tokens, passwords) in git history, working trees, files, and | MIT | vetted, see notes |
| [google/osv-scanner](https://github.com/google/osv-scanner) | Go scanner that resolves your lockfiles, SBOMs, and container images against the OSV.dev distributed vulnerability | Apache-2.0 | vetted |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | LLM vulnerability scanner that probes a model or LLM application with generated attacks for prompt injection, jailbreaks, data… | Apache-2.0 | vetted |
| [opengrep/opengrep](https://github.com/opengrep/opengrep) | Community fork of the Semgrep engine created after Semgrep moved critical analysis features behind a commercial | LGPL-2.1 | vetted |
| [ossf/scorecard](https://github.com/ossf/scorecard) | Automated assessment that scores a repository 0-10 across ~18 supply-chain security heuristics: branch protection, pinned… | Apache-2.0 | vetted, see notes |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | Fast multi-language static analysis engine that matches patterns written in the syntax of the target language itself across 30+… | LGPL-2.1 | vetted, see notes |
| [sigstore/cosign](https://github.com/sigstore/cosign) | Signs, verifies, and attaches attestations/SBOMs to container images and arbitrary artifacts, with keyless signing backed by the… | Apache-2.0 | vetted, see notes |
| [snyk/cli](https://github.com/snyk/cli) | CLI front-end to Snyk's commercial platform, covering open-source dependency CVEs, SAST (Snyk Code), container images, and | NOASSERTION | vetted, see notes |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | Secret scanner with 800+ detectors that additionally makes a live API call to VERIFY whether each found credential is actually… | AGPL-3.0 — AGPL-3 | vetted, see notes |

## Spatial: 3D Reconstruction And Scene Representation

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Single plain-transformer model that recovers spatially consistent geometry from any number of views, posed or unposed — monocular… | Apache-2.0 — FLAG — the largest/Giant checkpoints are CC BY-NC 4 | vetted |
| [colmap/colmap](https://github.com/colmap/colmap) | General-purpose Structure-from-Motion and Multi-View Stereo pipeline with GUI and CLI, for ordered and unordered image… | NOASSERTION | vetted, see notes |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | End-to-end transformer that regresses factored metric 3D geometry from images, calibration, poses and/or depth, covering 12+… | Apache-2.0 — FLAG — default released model weights are CC-BY-NC 4 | vetted, see notes |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | Feed-forward transformer that infers camera parameters, depth maps, point maps and 3D point tracks from 1 to hundreds of unposed… | NOASSERTION — FLAG — custom Meta license (GitHub reports NOASSERTION) | vetted, see notes |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | Native C++23/CUDA application to train, inspect, edit, automate and export 3D Gaussian Splatting scenes, with a real-time… | GPL-3.0 — FLAG — GPL-3 | vetted, see notes |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | Modular PyTorch framework for neural radiance fields — a common API across NeRF variants plus data parsers, a web viewer, and… | Apache-2.0 | vetted, see notes |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | Free, open-source, browser-based 3D Gaussian Splat editor for inspecting, cleaning, compressing, cropping and publishing splat… | MIT | vetted |

## Spatial: Reasoning VLMs And World Models

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [allenai/molmoact](https://github.com/allenai/molmoact) | Ai2's action reasoning model: a VLA that emits explicit spatial reasoning traces — depth perception tokens and 2D visual trace… | Apache-2.0 | vetted, see notes |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | One-for-all multimodal evaluation toolkit spanning text, image, video and audio tasks — a unified harness with hundreds of… | NOASSERTION | vetted, see notes |
| [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | Meta's self-supervised video world model — PyTorch code and weights for learning predictive latent representations from video,… | MIT | vetted |
| [FlagOpen/RoboBrain2.5](https://github.com/FlagOpen/RoboBrain2.5) | BAAI's embodied brain VLM ('Depth in Sight, Time in Mind') for unified spatial perception, affordance/pointing prediction,… | Apache-2.0 | vetted, see notes |
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | Open platform of world foundation models, datasets and tools for Physical AI — the Cosmos 3 omnimodal family (Super 64B / Nano… | NOASSERTION — FLAG: this is an open model/data license, not a standard OSI permissive license like… | vetted, see notes |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | Physical Intelligence's official open-source VLA models and packages: π₀ (flow-based VLA), π₀-FAST (autoregressive VLA using the… | Apache-2.0 — FLAG: ships a separate LICENSE_GEMMA | vetted |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | Open pipeline for synthesizing spatial VQA training data — lifts 2D images into metric 3D via depth/segmentation/point clouds,… | Apache-2.0 | vetted |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | Real-time streaming interactive world model with long-horizon memory — generates controllable, explorable video environments… | MIT — FLAG: verify the Hugging Face model card separately, as Skywork weight releases sometimes… | vetted, see notes |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | Official repo and evaluation implementation of VSI-Bench: 288 real indoor video sequences (ScanNet, ScanNet++, ARKitScenes) and… | Apache-2.0 | vetted |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | VLM fine-tuned for spatial affordance prediction — takes a language instruction and returns 2D image keypoints indicating where… | Apache-2.0 — FLAG: built on the LLaVA/Vicuna stack, so released checkpoints inherit Llama community… | vetted, see notes |

## Spatial: AR, Robotics Mapping, And SLAM

Full guide: [docs/SPATIAL-MODELS.md](SPATIAL-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [borglab/gtsam](https://github.com/borglab/gtsam) | C++/Python factor-graph optimization library for smoothing and mapping — batch and incremental (iSAM2) solvers, IMU… | NOASSERTION | vetted, see notes |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | Modern C++/Python library for 3D data processing: point clouds, meshes, registration/ICP, RGB-D odometry and integration, plus a… | NOASSERTION | vetted, see notes |
| [koide3/glim](https://github.com/koide3/glim) | Versatile range-based 3D mapping framework: GPU-accelerated LiDAR / LiDAR-inertial SLAM with global trajectory optimization,… | MIT | vetted |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | Builds hierarchical 3D scene graphs (objects, places, rooms, buildings) from live sensor data in real time, with loop closure… | BSD-2-Clause | vetted |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | CUDA-accelerated 3D Gaussian splatting rasterization library with a PyTorch API — the rendering engine behind Nerfstudio's… | Apache-2.0 — non-commercial | vetted |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | GPU-accelerated TSDF and ESDF volumetric mapping library for robots with RGB-D or LiDAR input, producing distance fields suitable… | NOASSERTION | vetted, see notes |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | Rust-based logging and visualization SDK/viewer for multimodal spatial and temporal data — point clouds, transforms/TF trees,… | Apache-2.0 | vetted |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | Real-time dense monocular SLAM that uses the MASt3R two-view 3D reconstruction prior for tracking, dense pointmap fusion, and… | NOASSERTION — CC BY-NC-SA 4 | vetted, see notes |
| [rpng/open_vins](https://github.com/rpng/open_vins) | Filter-based (MSCKF) visual-inertial odometry/navigation platform with sliding-window state estimation, online calibration, and… | GPL-3.0 — GPL-3.0 — FLAG | vetted, see notes |
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | Real-time monocular / stereo / RGB-D visual SLAM framework (the maintained continuation of OpenVSLAM) with map save-load and… | NOASSERTION | vetted, see notes |

## Live, Streaming, And Incremental RAG

Full guide: [docs/LIVE-RAG.md](LIVE-RAG.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | Lightweight, low-dependency unified Python API over essentially every reranking and cross-encoder | Apache-2.0 — non-commercial | vetted |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | Pytest-style LLM evaluation framework with RAG-specific metrics: faithfulness, answer relevancy, contextual… | Apache-2.0 | vetted, see notes |
| [getzep/graphiti](https://github.com/getzep/graphiti) | Framework for building temporal knowledge graphs that AI agents query, where every edge carries a validity | Apache-2.0 | vetted, see notes |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | Open-source RAG engine built on deep document understanding (DeepDoc OCR / table / layout recognition), fused with agent… | Apache-2.0 | vetted, see notes |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | Production-grade multi-agent deep-research system using a supervisor/researcher architecture with parallel isolated-context… | MIT | vetted |
| [lightonai/pylate](https://github.com/lightonai/pylate) | Library for training, fine-tuning, and serving late-interaction (ColBERT-family) multi-vector retrieval models, built on Sentence… | MIT | vetted |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | Self-hostable AI search and chat platform with 40+ enterprise connectors (Slack, Drive, Confluence, Jira, GitHub, | NOASSERTION — FLAG - mixed | vetted, see notes |
| [paradedb/paradedb](https://github.com/paradedb/paradedb) | Postgres extension suite adding BM25 full-text search, vector retrieval, and analytics inside the | AGPL-3.0 — FLAG - AGPL-3 | vetted, see notes |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | Python ETL/stream-processing framework on a Rust Differential Dataflow engine, with LLM tooling and an in-memory real-time vector… | NOASSERTION — FLAG - Business Source License 1 | vetted, see notes |
| [vespa-engine/vespa](https://github.com/vespa-engine/vespa) | Big-data serving and AI search platform combining vector, lexical, and structured retrieval with learned | Apache-2.0 | vetted, see notes |

## Open-Weight LLMs And Serving Stacks

Full guide: [docs/LLM-MODELS.md](LLM-MODELS.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | Few-shot evaluation framework covering 60+ academic benchmarks with pluggable backends (HF Transformers, vLLM, SGLang,… | MIT | vetted, see notes |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | C/C++ LLM inference with minimal setup, GGUF weights, and an included OpenAI-compatible server; runs CPU-only or GPU-accelerated… | MIT | vetted, see notes |
| [QwenLM/Qwen3.6](https://github.com/QwenLM/Qwen3.6) | Official repo for the Qwen3.5 and Qwen3.6 model generations - dense and MoE open-weight models spanning roughly 0.8B to 35B-A3B,… | Apache-2.0 | vetted |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | Serving framework for LLMs and multimodal models built around RadixAttention prefix caching and a structured-generation frontend… | Apache-2.0 | vetted, see notes |
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | Transformers-compatible library for applying quantisation and compression algorithms (GPTQ, AWQ, SmoothQuant, FP8/NVFP4,… | Apache-2.0 | vetted, see notes |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | High-throughput, memory-efficient LLM inference and serving engine with an OpenAI-compatible API | Apache-2.0 | vetted, see notes |
| [zai-org/GLM-5](https://github.com/zai-org/GLM-5) | Official repo for the GLM-5 series - a 744B-parameter MoE with ~40B active per token, 1M-token context, released in BF16 and FP8,… | Apache-2.0 | vetted |

## Security Scanning Tools

Full guide: [docs/SECURITY-SCANNING.md](SECURITY-SCANNING.md) · Security verdicts: [docs/VETTING-REPORT.md](VETTING-REPORT.md)

| Repo | What it is | License | Status |
| --- | --- | --- | --- |
| [anchore/syft](https://github.com/anchore/syft) | CLI and Go library that generates a Software Bill of Materials from container images, filesystems, and archives across dozens of… | Apache-2.0 | vetted, see notes |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | All-in-one scanner covering container images, filesystems, git repos, VM images, Kubernetes clusters and cloud accounts for CVEs,… | Apache-2.0 | vetted, see notes |
| [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) | Policy-as-code static analyzer for infrastructure as code — Terraform, CloudFormation, Kubernetes manifests, Helm, ARM, Bicep,… | Apache-2.0 | vetted, see notes |
| [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | Python CLI and REST server that scans MCP servers and their tool definitions for prompt injection, tool poisoning, rug pulls, and… | Apache-2.0 | vetted, see notes |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | Go CLI that detects hardcoded secrets (API keys, tokens, passwords) in git history, working trees, files, and | MIT | vetted, see notes |
| [google/osv-scanner](https://github.com/google/osv-scanner) | Go scanner that resolves your lockfiles, SBOMs, and container images against the OSV.dev distributed vulnerability | Apache-2.0 | vetted |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | LLM vulnerability scanner that probes a model or LLM application with generated attacks for prompt injection, jailbreaks, data… | Apache-2.0 | vetted |
| [opengrep/opengrep](https://github.com/opengrep/opengrep) | Community fork of the Semgrep engine created after Semgrep moved critical analysis features behind a commercial | LGPL-2.1 | vetted |
| [ossf/scorecard](https://github.com/ossf/scorecard) | Automated assessment that scores a repository 0-10 across ~18 supply-chain security heuristics: branch protection, pinned… | Apache-2.0 | vetted, see notes |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | Fast multi-language static analysis engine that matches patterns written in the syntax of the target language itself across 30+… | LGPL-2.1 | vetted, see notes |
| [sigstore/cosign](https://github.com/sigstore/cosign) | Signs, verifies, and attaches attestations/SBOMs to container images and arbitrary artifacts, with keyless signing backed by the… | Apache-2.0 | vetted, see notes |
| [snyk/cli](https://github.com/snyk/cli) | CLI front-end to Snyk's commercial platform, covering open-source dependency CVEs, SAST (Snyk Code), container images, and | NOASSERTION | vetted, see notes |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | Secret scanner with 800+ detectors that additionally makes a live API call to VERIFY whether each found credential is actually… | AGPL-3.0 — AGPL-3 | vetted, see notes |

## Source Links

- [GitHub Copilot CLI context management](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management)
- [GitHub custom agents changelog](https://github.blog/changelog/2025-10-28-custom-agents-for-github-copilot/)
- [Claude automatic context compaction cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction)
- [Claude compaction docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [DeepWiki Copilot CLI context/token management](https://deepwiki.com/github/copilot-cli/3.7-context-and-token-management)
- [GitHub topic: context-compaction](https://github.com/topics/context-compaction)
- [Fungies AI agent repos article](https://fungies.io/top-github-repositories-ai-agent-frameworks-2026/)
- [Microsoft Copilot Studio MCP connector docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [Microsoft Copilot Studio REST API action docs](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-rest-api)
- [Robinhood Agentic Trading](https://robinhood.com/us/en/support/articles/agentic-trading/)
- [Robinhood Crypto API docs](https://docs.robinhood.com/crypto/trading/)
- [Alpaca paper trading docs](https://docs.alpaca.markets/docs/paper-trading)
- [Qiskit](https://github.com/Qiskit/qiskit)
- [PennyLane](https://github.com/PennyLaneAI/pennylane)
- [Infracost](https://github.com/infracost/infracost)
- [OpenCost](https://github.com/opencost/opencost)
