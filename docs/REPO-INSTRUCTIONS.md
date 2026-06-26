# Repo Instructions — Install, Run, and Connect Every Lane

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

Per-repo setup instructions. For combining repos, see [COMBINING-REPOS.md](COMBINING-REPOS.md). For CLI one-liners, see [CLI-ONE-LINERS.md](CLI-ONE-LINERS.md).

---

## Agent Frameworks

### bradygaster/Squad

**What it is:** Multi-agent orchestration framework built on .NET.

**Prerequisites:** .NET 8 SDK, Node.js 18+

Install the CLI:
```powershell
npm install -g @bradygaster/squad-cli
```

Run a sample:
```powershell
squad init my-agent-team
cd my-agent-team
squad run
```

Connect to MCP: add MCP server config to `squad.config.json`, then `squad run --mcp`.

---

### microsoft/agents

**What it is:** Microsoft's multi-agent SDK for building production agent systems.

**Prerequisites:** .NET 8 SDK

Clone and run the sample:
```powershell
$Path = Read-Host "Where to clone?"
git clone https://github.com/microsoft/agents.git $Path
cd $Path
dotnet run --project samples/simple-agent
```

---

### runagent-dev/runagent

**What it is:** Lightweight Python agent runner with tool and memory support.

**Prerequisites:** Python 3.11+

Install:
```powershell
python -m pip install runagent
```

Run a sample:
```bash
runagent init my-agent
cd my-agent
runagent run agent.py
```

---

### github/copilot-cli

**What it is:** GitHub Copilot CLI for terminal-native agent workflows.

**Prerequisites:** GitHub account, Copilot subscription

Install:
```powershell
npm install -g @github/copilot-cli
```

Authenticate:
```bash
github-copilot-cli auth login
```

---

## RAG / Knowledge / Memory

### HKUDS/LightRAG

**What it is:** Graph-based RAG framework with entity and relationship awareness.

**Prerequisites:** Python 3.10+, OpenAI API key or local model

Install:
```bash
pip install lightrag-hku
```

Index a folder:
```python
from lightrag import LightRAG
rag = LightRAG(working_dir="./rag-storage")
rag.insert_file("./my-docs")
print(rag.query("What is the main topic?"))
```

---

### upstash/vector-js

**What it is:** Serverless vector database client for TypeScript/JavaScript.

**Prerequisites:** Node.js 18+, Upstash account

Install:
```bash
npm install @upstash/vector
```

Connect:
```typescript
import { Index } from "@upstash/vector";
const index = new Index({
  url: process.env.UPSTASH_VECTOR_REST_URL,
  token: process.env.UPSTASH_VECTOR_REST_TOKEN,
});
```

---

### upstash/rag-chat

**What it is:** Upstash RAG chat with built-in context management.

**Prerequisites:** Node.js 18+, Upstash account

Install:
```bash
pnpm add @upstash/rag-chat
```

---

### rohitg00/agentmemory

**What it is:** Persistent memory for agents using local storage.

Install:
```bash
npm install -g @agentmemory/agentmemory
```

---

### satoshiman/rag-cli

**What it is:** Command-line RAG — index and query from the terminal.

**Prerequisites:** Python 3.10+

Install:
```bash
pip install rag-cli
```

Index a folder:
```bash
rag index ./my-docs
rag query "What is the main topic?"
```

---

## Context & Token Management

### Compresr-ai/Context-Gateway

**What it is:** Compression proxy for LLM context — reduce tokens before sending.

Install (WSL/Bash):
```bash
curl -fsSL https://compresr.ai/api/install | sh && context-gateway
```

---

### microsoft/LLMLingua

**What it is:** Microsoft's prompt compression library — removes redundancy while preserving meaning.

**Prerequisites:** Python 3.10+

Install:
```bash
pip install llmlingua
```

Compress a prompt:
```python
from llmlingua import PromptCompressor
compressor = PromptCompressor()
result = compressor.compress_prompt(prompt, ratio=0.5)
print(result["compressed_prompt"])
```

---

### ooples/token-optimizer-mcp

**What it is:** MCP server for token counting and optimization.

Install:
```bash
npx -y ooples-token-optimizer-mcp
```

---

## MCP Servers

### modelcontextprotocol/servers — Filesystem

**What it is:** Standard filesystem MCP server.

Run with chosen path:
```powershell
$AllowedPath = Read-Host "Folder to expose"; npx -y @modelcontextprotocol/server-filesystem $AllowedPath
```

---

### github/github-mcp-server

**What it is:** GitHub MCP server for reading repos, issues, and PRs.

Run with limited toolsets:
```bash
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" \
  -e GITHUB_TOOLSETS="repos,issues,pull_requests" \
  ghcr.io/github/github-mcp-server
```

---

### microsoft/playwright-mcp

**What it is:** Browser automation MCP server using Playwright.

Install:
```bash
npm install -g @microsoft/playwright-mcp
npx playwright install chromium
```

Run:
```bash
playwright-mcp
```

---

### upstash/context7

**What it is:** MCP server for live library documentation lookup.

Run:
```bash
npx -y @upstash/context7-mcp
```

---

## Finance & Trading Plugins

### plugins/autonomous-day-trading-agent

**What it is:** Risk-gated day trading agent with paper trading and backtesting.

**Prerequisites:** Python 3.11+, Alpaca paper account

Install and smoke test:
```powershell
$PluginPath = Read-Host "Path to plugins\autonomous-day-trading-agent"
Set-Location $PluginPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip; python -m pip install -e .
autonomous-day-trading-agent smoke-test --risk risk_limits.example.json
```

---

### plugins/quantum-trading-agent

**What it is:** Quantum-enhanced trading agent using Qiskit for optimization.

Install and smoke test:
```powershell
$PluginPath = Read-Host "Path to plugins\quantum-trading-agent"
Set-Location $PluginPath
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip; python -m pip install -e .
quantum-trading-agent smoke-test --risk risk_limits.example.json
```

---

### alpacahq/alpaca-mcp-server

**What it is:** MCP server for Alpaca paper and live trading.

Run in paper mode:
```bash
export ALPACA_API_KEY=your_paper_key
export ALPACA_SECRET_KEY=your_paper_secret
export ALPACA_PAPER=true
npx -y alpaca-mcp-server
```

---

## Cost Reduction

### infracost/infracost

**What it is:** IaC cost estimation — get cloud costs before you deploy.

Install:
```powershell
winget install Infracost.Infracost
```

Run against a Terraform project:
```bash
cd my-terraform-project
infracost breakdown --path .
```

---

### opencost/opencost

**What it is:** Kubernetes cost monitoring and allocation.

Install (Helm):
```bash
helm install opencost opencost/opencost --namespace opencost --create-namespace
```

---

### cloud-custodian/cloud-custodian

**What it is:** Policy-based cloud governance — find and fix waste automatically.

Install:
```bash
pip install c7n
```

Run a policy:
```bash
custodian run --output-dir output my-policy.yml
```

---

## Quantum

### Qiskit/qiskit

**What it is:** IBM's quantum computing SDK.

Install:
```bash
pip install qiskit qiskit-aer
```

Run a circuit:
```python
from qiskit import QuantumCircuit
from qiskit_aer import Aer
qc = QuantumCircuit(2, 2)
qc.h(0); qc.cx(0, 1); qc.measure([0,1], [0,1])
backend = Aer.get_backend('qasm_simulator')
job = backend.run(qc, shots=1000)
print(job.result().get_counts())
```

---

### PennyLaneAI/pennylane

**What it is:** Differentiable quantum computing for QML.

Install:
```bash
pip install pennylane
```

---

## App / Mobile

### expo/expo

**What it is:** React Native framework for cross-platform apps.

Create a new app:
```powershell
$AppPath = Read-Host "Where should the app be created?"
npx create-expo-app@latest $AppPath
cd $AppPath
npx expo start
```

---

### roninoss/create-expo-stack

**What it is:** Expo app scaffolding with NativeWind, TypeScript, and expo-router.

Create:
```bash
npx create-expo-stack@latest my-app
```

---

## Pitch / Hackathon

### slidevjs/slidev

**What it is:** Markdown-based slide decks for developers.

Create and start:
```bash
read -rp "Deck folder: " deck_path; mkdir -p "$deck_path"; cd "$deck_path"; npm init slidev
```

---

### marp-team/marpit

**What it is:** Markdown to slide framework.

Install:
```bash
npm install -g @marp-team/marp-cli
marp slides.md --html -o output.html
```
