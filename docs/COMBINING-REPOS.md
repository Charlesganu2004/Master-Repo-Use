# Combining Repos — Stack Recipes

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

Named stack recipes for common combinations. Each recipe tells you exactly what to clone, install, and connect. Use [STANDALONE-USAGE.md](STANDALONE-USAGE.md) to try one lane first, then combine using the recipes here.

Replace `REVIEWED_VERSION` with an exact package release you inspected; never use `latest` or automatic yes.

---

## Recipe 1 — Core Agent Stack

**Use case:** Build an agent team that can reason over your codebase, remember decisions, and call tools safely.

**Repos:**
- `bradygaster/squad` — multi-agent orchestration
- `HKUDS/LightRAG` — knowledge retrieval
- `rohitg00/agentmemory` — durable memory
- `modelcontextprotocol/servers` — filesystem MCP access

**Install (PowerShell):**
```powershell
$LabRoot = Read-Host "Where should the core agent stack live?"
New-Item -ItemType Directory -Force $LabRoot | Out-Null; Set-Location $LabRoot
npm install -g @bradygaster/squad-cli @agentmemory/agentmemory
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip lightrag-hku
```

**Start the MCP server:**
```powershell
$WorkspacePath = Read-Host "Folder the agent may access"
npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION $WorkspacePath
```

**Wire up:**
1. Start the filesystem MCP server pointing to your project folder.
2. Start Squad with the Maxwell orchestrator system prompt from `agents/orchestrator-maxwell.md`.
3. Index your docs folder with LightRAG.
4. Connect agentmemory to Squad for durable memory.

---

## Recipe 2 — Microsoft Stack

**Use case:** Enterprise agent with Copilot Studio frontend, .NET backend, and Azure infrastructure.

**Repos:**
- `microsoft/agents` — .NET agent SDK
- `microsoft/Agents-for-net` — .NET agent extensions
- `OfficeDev/microsoft-365-agents-toolkit` — M365 agent toolkit
- `microsoft/mcp` — Microsoft's MCP implementation
- `bradygaster/Aspiregregator` — .NET Aspire orchestration

**Install:**
```powershell
dotnet tool install -g Microsoft.Agents.CLI
npm install -g @microsoft/m365agentstoolkit-cli
```

**Wire up:**
1. Create an agent with `agents init my-agent`.
2. Add an MCP connector in Copilot Studio pointing to your MCP server.
3. Deploy the .NET backend to Azure Container Apps.
4. Connect Copilot Studio to the deployed endpoint via a custom connector.

---

## Recipe 3 — Cost-Efficient LLM Stack

**Use case:** Maximize work per dollar — compress, cache, and route to the cheapest model that works.

**Repos:**
- `microsoft/LLMLingua` — prompt compression
- `ooples/token-optimizer-mcp` — MCP token optimizer
- `yvgude/lean-ctx` — lean context management

**Install:**
```bash
pip install llmlingua
npx @ooples/token-optimizer-mcp@REVIEWED_VERSION
```

**Wire up:**
1. Route all large prompts through LLMLingua before sending to the model.
2. Start the token-optimizer-mcp server and add it to your agent's tool list.
3. Follow the checklist in [TOKEN-EFFICIENCY.md](TOKEN-EFFICIENCY.md).

---

## Recipe 4 — Market Research Stack

**Use case:** Research stocks, sectors, and market trends using open data.

**Repos:**
- `OpenBB-finance/OpenBB` — market data platform
- `ai4finance-foundation/finrobot` — AI-powered financial research
- `tauricresearch/tradingagents` — multi-agent trading analysis
- `ranaroussi/yfinance` — Yahoo Finance data

**Install:**
```powershell
$LabPath = Read-Host "Where should the market research lab be?"
New-Item -ItemType Directory -Force $LabPath | Out-Null; Set-Location $LabPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip openbb yfinance pandas matplotlib ta
```

**Wire up:**
1. Use OpenBB as the primary data source.
2. Connect yfinance for supplementary price data.
3. Wire Orion (market-intel-orion.md) as the research agent.
4. Wire Nova (portfolio-nova.md) for allocation proposals.
5. Wire Sage (risk-sage.md) as the risk gate before any trade proposal.

---

## Recipe 5 — Autonomous Trading Stack

**Use case:** Paper-trading agent with signal generation, backtesting, and risk gates.

**Repos:**
- `plugins/autonomous-day-trading-agent` — the core plugin
- `alpacahq/alpaca-py` — Alpaca broker SDK
- `alpacahq/alpaca-mcp-server` — Alpaca MCP server
- `HKUDS/Vibe-Trading` — market intelligence signals

**Install:**
```powershell
$PluginPath = Read-Host "Path to plugins\autonomous-day-trading-agent"
Set-Location $PluginPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip; python -m pip install -e .
autonomous-day-trading-agent smoke-test --risk risk_limits.example.json
```

**Wire up:**
1. Set Alpaca paper credentials as environment variables.
2. Start the Alpaca MCP server in paper mode.
3. Wire Rex (trading-rex.md) as the execution agent.
4. Wire Sage (risk-sage.md) as the approval gate before every order.
5. Wire Maxwell (orchestrator-maxwell.md) as the coordinator.

**Hard rule:** Paper mode only until every risk gate is verified. See [docs/AUTONOMOUS-DAY-TRADING.md](AUTONOMOUS-DAY-TRADING.md).

---

## Recipe 6 — Quantum Sidecar Stack

**Use case:** Add quantum optimization or QML experiments alongside a classical agent workflow.

**Repos:**
- `Qiskit/qiskit` — quantum circuits
- `qiskit-community/qiskit-finance` — quantum finance algorithms
- `PennyLaneAI/pennylane` — QML
- `plugins/quantum-trading-agent` — quantum trading plugin

**Install:**
```powershell
$LabPath = Read-Host "Quantum lab path"
New-Item -ItemType Directory -Force $LabPath | Out-Null; Set-Location $LabPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip qiskit qiskit-finance qiskit-optimization pennylane pandas matplotlib
```

**Wire up:**
1. Run quantum experiments in the lab folder.
2. Always compare quantum results to a classical baseline.
3. Wire Helix (quantum-lab-helix.md) as the experiment assistant.
4. Wire Qubit (quantum-qubit.md) for finance-specific quantum research.
5. Connect to the main trading stack only after experiments are stable.

---

## Recipe 7 — Full MCP Stack

**Use case:** Give an agent access to filesystem, GitHub, browser, and docs — all scoped and safe.

**Repos:**
- `modelcontextprotocol/servers` — filesystem MCP
- `github/github-mcp-server` — GitHub MCP
- `microsoft/playwright-mcp` — browser MCP
- `upstash/context7` — docs MCP

**Start all servers:**
```bash
# Terminal 1 — filesystem
read -rp "Folder for filesystem MCP: " fs_path
npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION "$fs_path"

# Terminal 2 — GitHub (limited toolsets)
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="repos,issues" ghcr.io/github/github-mcp-server

# Terminal 3 — browser
npx @playwright/mcp@REVIEWED_VERSION

# Terminal 4 — docs
npx @upstash/context7-mcp@REVIEWED_VERSION
```

**Wire up:** Add each server's connection URL to your agent's MCP config. Use minimum toolsets for each. See [docs/MCP-SERVERS.md](MCP-SERVERS.md) for the full reference.

---

## Recipe 8 — Mobile Product Stack

**Use case:** Build a mobile app backed by an agent API and RAG knowledge base.

**Repos:**
- `expo/expo` — React Native framework
- `roninoss/create-expo-stack` — project scaffold
- `upstash/rag-chat` — RAG-backed chat API
- `upstash/vector-js` — vector store

**Create the app:**
```bash
npx create-expo-stack@REVIEWED_VERSION my-app --expo-router --nativewind
cd my-app && npm exec --offline -- expo start
```

**Create the RAG backend:**
```bash
npm install @upstash/rag-chat @upstash/vector
```

**Wire up:**
1. Deploy the RAG chat API (Vercel, Azure Functions, or any Node host).
2. Add the API endpoint as an Expo environment variable.
3. Wire Stack (mobile-stack.md) for app development.
4. Wire Vector (rag-vector.md) for knowledge base management.

---

## Recipe 9 — Security Stack

**Use case:** Continuous security monitoring for this repo and its agents.

**Repos:**
- `agents/security-sentinel.md` — security auditor
- `agents/secret-scanner-lock.md` — credential scanner
- `github/github-mcp-server` — GitHub MCP (issues, security advisories)
- `microsoft/playwright-mcp` — browser testing

**Wire up:**
1. Run Lock on every PR to catch secrets before they merge.
2. Run Sentinel monthly for a full security audit.
3. Run Ghost for authorized threat modeling on major new features.
4. Wire Lex for compliance checks on any feature that handles personal data.
5. Use the GitHub MCP server for security advisory monitoring.

---

## How to Add a New Stack Recipe

1. Identify the repos involved.
2. Write the install commands (PowerShell + WSL/Bash).
3. Write the wire-up steps (numbered, with expected outputs).
4. Add the recipe to this file.
5. Add a reference to the recipe in the Decision Map in README.md.
