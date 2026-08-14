# MCP Servers

MCP servers are adapters. They let an agent use tools through an explicit protocol instead of every agent inventing its own integration.

Replace `REVIEWED_VERSION` with an exact package release you inspected; never use `latest` or automatic yes.

## Core Pattern

```text
Agent host
  -> MCP client
  -> MCP server
  -> one bounded capability
  -> filesystem, GitHub, browser, docs, database, cloud, or finance API
```

## Repos To Know

| Repo | Use it when | Cost note | Status |
| --- | --- | --- | --- |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | You want reference servers such as filesystem, memory, fetch, Git, and other baseline integrations. | Free/local. No API cost beyond LLM tokens. | active |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | You want to build MCP servers in TypeScript. | Free/local. | active |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | You want to build MCP servers in Python. | Free/local. | active |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | You want to test and debug MCP servers. | Free/local dev tool. | active |
| [microsoft/mcp](https://github.com/microsoft/mcp) | You want Microsoft's MCP catalog and guidance. | Free/reference. | active |
| [microsoftdocs/mcp](https://github.com/microsoftdocs/mcp) | You want Microsoft Learn source/docs for MCP. | Free/reference. | active |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | You want browser automation through MCP. | Free/local; browser sessions add token cost from screenshots. | active |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | You want GitHub repo, issue, PR, Actions, and security tools. | Free/local with your PAT; API rate limits apply. | active |
| [upstash/context7](https://github.com/upstash/context7) | You want fresh library docs available to agents. | Hosted; free tier available, paid above limits. | active |
| [awslabs/mcp](https://github.com/awslabs/mcp) | You want AWS-focused MCP servers. | Free/local; AWS API calls incur AWS charges. | active |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | You want a broad community MCP server list. | Free/reference. Treat as discovery only. | active |
| [microsoft/lets-learn-mcp-python](https://github.com/microsoft/lets-learn-mcp-python) | You want a learning path for MCP in Python. | Free/local learning resource. | active |
| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | You want broker and account tools exposed through MCP for paper or live trading. | Free/local; live trades incur real broker costs. Paper mode is free. | active |
| [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | You want MCP-based token optimization experiments to reduce LLM token spend. | Free/local; reduces token cost over time. | experimental |
| [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | You want lean context engineering tools for trimming agent session bloat. | Free/local. | experimental |
| [chopratejas/headroom](https://github.com/chopratejas/headroom) | You want headroom/context budget tracking for long agent sessions. | Free/local. | experimental |

## Common Combos

| Combo | What it does |
| --- | --- |
| Filesystem + GitHub MCP | Agent can edit local files and open PRs or issues. |
| Filesystem + Playwright MCP | Agent can edit app code and verify the browser. |
| GitHub MCP + Infracost | Agent can review a PR and estimate cloud cost impact. |
| Context7 + Copilot CLI | Agent can pull current docs instead of guessing. |
| Python MCP + quantum libraries | Agent can call Qiskit/PennyLane experiments from a normal workflow. |
| Python MCP + market libraries | Agent can fetch market data, run backtests, and return analysis artifacts. |

## Cost Controls

- Prefer toolsets over exposing every tool.
- Prefer read-only mode for research.
- Keep tool descriptions short.
- Keep JSON schemas narrow.
- Add caching for expensive external APIs.
- Log tool calls and estimate token/API cost before scaling.
- Use retrieval before sending full documents to the model.

## One-Liners

Filesystem server, PowerShell:

```powershell
$AllowedOne = Read-Host "First folder the agent may access"; $AllowedTwo = Read-Host "Second folder the agent may access, or press Enter to skip"; if ($AllowedTwo) { npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION $AllowedOne $AllowedTwo } else { npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION $AllowedOne }
```

Filesystem server, WSL/Bash:

```bash
read -rp "First folder the agent may access: " allowed_one; read -rp "Second folder the agent may access, or press Enter to skip: " allowed_two; if [ -n "$allowed_two" ]; then npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION "$allowed_one" "$allowed_two"; else npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION "$allowed_one"; fi
```

GitHub MCP server with selected toolsets:

```bash
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="context,repos,issues,pull_requests" ghcr.io/github/github-mcp-server
```

Clone MCP repos:

```powershell
$MasterRepo = (Get-Location).Path  # run from repo root; $LanePath = Read-Host "Folder where MCP repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\mcp-servers-extended.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LanePath ($_ -replace '/','-')) }
```
