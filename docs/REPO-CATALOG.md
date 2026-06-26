# Repo Catalog

Use this file as the detailed reading path. Each row explains what the repo is for, how to get started, and where it fits in the bigger system.

## System View

| Layer | Job | Repos to inspect first |
| --- | --- | --- |
| Agent orchestration | Agent roles, teams, tools, task routing | `squad`, `microsoft/agents`, `Agents-for-net`, `copilot-cli` |
| Knowledge and memory | Search docs, retrieve facts, keep durable project memory | `LightRAG`, `AugmentR`, `rag-chat`, `vector-js`, `agentmemory` |
| Context control | Reduce token pressure and keep long sessions coherent | `Context-Gateway`, `LLMLingua`, `Prompt-Compression-Survey` |
| MCP server layer | Connect tools through explicit, scoped server boundaries | `modelcontextprotocol/servers`, `github-mcp-server`, `playwright-mcp`, `context7` |
| Copilot Studio front door | Connect business-facing agents to APIs, MCP, and code agents | `microsoft/agents`, `Agents-for-net`, MCP connector docs |
| Product surface | Mobile/web app shell, docs structure, user experience | `expo`, `create-expo-stack`, `github/docs` |
| Cloud and deployment | .NET Aspire, YARP, Azure Container Apps, hosted services | Aspire and cloud-native samples |
| Finance and trading research | Market analysis, backtesting, paper trading, broker research | `OpenBB`, `TradingAgents`, `FinRobot`, `FinRL`, `robin_stocks` |
| Autonomous day trading | Signal generation, backtests, paper orders, investing allocations | `autonomous-day-trading-agent`, `Vibe-Trading`, `alpaca-mcp-server` |
| Quantum sidecar | Standalone quantum learning plus optional optimization/QML experiments | `Qiskit`, `PennyLane`, `Cirq`, `qiskit-finance` |
| Cost reduction | Reduce token, API, MCP, and cloud spend | `Infracost`, `OpenCost`, `Cloud Custodian`, `token-optimizer-mcp` |
| Demo and story | Standalone hackathon resources, Markdown slides, pitch decks | `awesome-hackathon`, `slidev`, `marpit`, `pitch-deck` |
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
| [bradygaster/AugmentR](https://github.com/bradygaster/AugmentR) | You want a .NET Aspire + Semantic Kernel + OpenAI RAG sample. | Clone and run with .NET/Aspire prerequisites. | Good for .NET agent backends. | experimental |
| [varunon9/rag-langchain-nodejs](https://github.com/varunon9/rag-langchain-nodejs) | You want a Node.js LangChain RAG starter. | Clone, `npm install`, set provider/vector DB env vars. | Useful for JavaScript agent prototypes. | experimental |
| [upstash/rag-chat](https://github.com/upstash/rag-chat) | You want a quick TypeScript SDK for RAG chat. | `pnpm add @upstash/rag-chat` or `npm i @upstash/rag-chat`. | Pairs with Upstash Vector. | active |
| [upstash/vector-js](https://github.com/upstash/vector-js) | You need a TypeScript client for Upstash Vector. | `npm install @upstash/vector` | Use as vector storage under RAG apps. | active |
| [satoshiman/rag-cli](https://github.com/satoshiman/rag-cli) | You want local-first RAG from the command line. | Clone, `npm install`, then use the CLI commands from its README. | Good for personal docs and local notes. | experimental |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | You want persistent memory for coding agents. | `npm install -g @agentmemory/agentmemory` | Complements RAG by storing durable project facts and decisions. | experimental |

## Context And Token Management

| Repo or article | Use it when | Fast start | Connects to |
| --- | --- | --- | --- |
| [Compresr-ai/Context-Gateway](https://github.com/Compresr-ai/Context-Gateway) | You want a proxy that compresses agent history/tool output before context gets too large. | In WSL/Bash: `curl -fsSL https://compresr.ai/api/install \| sh`; then `context-gateway`. | Works between coding agents and model APIs. |
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
| [mementum/backtrader](https://github.com/mementum/backtrader) | You want Python backtesting. | Historical strategy tests. | stale |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | You want quick market data. | Research scripts and notebooks. | active |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | You want pandas technical analysis indicators. | Feature engineering. | experimental |
| [bukosabino/ta](https://github.com/bukosabino/ta) | You want technical analysis indicators. | Feature engineering. | stale |
| [matplotlib/mplfinance](https://github.com/matplotlib/mplfinance) | You want financial charts. | Reports and decks. | active |
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
| [LIU-HONGYANG-GZU/Live_Trade_Bench](https://github.com/LIU-HONGYANG-GZU/Live_Trade_Bench) | You want a benchmark for LLM trading agents. | Evaluation before automation. | experimental |
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
| [chopratejas/headroom](https://github.com/chopratejas/headroom) | You want headroom/context tracking ideas. | Long sessions and budget checks. |
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
| [bradygaster/Aspire.Hosting.Facepunch.Rust](https://github.com/bradygaster/Aspire.Hosting.Facepunch.Rust) | You want Aspire hosting ideas around Rust server hosting. | Clone and inspect sample host code. | Cloud/game/server hosting experiments. |
| [bradygaster/dotnet-cloud-native-build-2023](https://github.com/bradygaster/dotnet-cloud-native-build-2023) | You want .NET cloud-native sample material. | Clone and follow the repo workshop/sample flow. | Good learning path for cloud-native .NET. |
| [bradygaster/ASPNETCoreWithYarpOnAzureContainerApps](https://github.com/bradygaster/ASPNETCoreWithYarpOnAzureContainerApps) | You want ASP.NET Core + YARP + Azure Container Apps reference. | Clone and inspect deployment/runtime configuration. | Useful for agent API gateways. |

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
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | You need reference MCP servers, especially filesystem access. | Filesystem command: `npx -y @modelcontextprotocol/server-filesystem <allowed-dir>` | Lets agents read/write only approved local directories. |
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
