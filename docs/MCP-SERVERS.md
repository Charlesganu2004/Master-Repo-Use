# MCP Servers

MCP servers are adapters. They let an agent use tools through an explicit protocol instead of every agent inventing its own integration.

## Core Pattern

```text
Agent host
  -> MCP client
  -> MCP server
  -> one bounded capability
  -> filesystem, GitHub, browser, docs, database, cloud, or finance API
```

## Repos To Know

| Repo | Use it when | Cost/risk note |
| --- | --- | --- |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | You want reference servers such as filesystem, memory, fetch, Git, and other baseline integrations. | Use allowlisted folders and read-only mounts where possible. |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | You want to build MCP servers in TypeScript. | Keep tool schemas tight to reduce context size. |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | You want to build MCP servers in Python. | Good for data, finance, quantum, and notebook-adjacent tools. |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | You want to test and debug MCP servers. | Use before attaching a server to a real agent. |
| [microsoft/mcp](https://github.com/microsoft/mcp) | You want Microsoft's MCP catalog and guidance. | Good starting point for Microsoft ecosystem servers. |
| [microsoftdocs/mcp](https://github.com/microsoftdocs/mcp) | You want Microsoft Learn source/docs for MCP. | Good for official docs tracking. |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | You want browser automation through MCP. | Browser tools can be expensive; scope tasks and screenshots. |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | You want GitHub repo, issue, PR, Actions, and security tools. | Use selected toolsets and token scopes. |
| [upstash/context7](https://github.com/upstash/context7) | You want fresh library docs available to agents. | Reduces wasted calls caused by stale docs. |
| [awslabs/mcp](https://github.com/awslabs/mcp) | You want AWS-focused MCP servers. | Watch cloud API and hosted resource costs. |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | You want a broad community MCP server list. | Treat as discovery, not automatic install. |
| [microsoft/lets-learn-mcp-python](https://github.com/microsoft/lets-learn-mcp-python) | You want a learning path for MCP in Python. | Good for building small custom servers. |

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
$AllowedOne = Read-Host "First folder the agent may access"; $AllowedTwo = Read-Host "Second folder the agent may access, or press Enter to skip"; if ($AllowedTwo) { npx -y @modelcontextprotocol/server-filesystem $AllowedOne $AllowedTwo } else { npx -y @modelcontextprotocol/server-filesystem $AllowedOne }
```

Filesystem server, WSL/Bash:

```bash
read -rp "First folder the agent may access: " allowed_one; read -rp "Second folder the agent may access, or press Enter to skip: " allowed_two; if [ -n "$allowed_two" ]; then npx -y @modelcontextprotocol/server-filesystem "$allowed_one" "$allowed_two"; else npx -y @modelcontextprotocol/server-filesystem "$allowed_one"; fi
```

GitHub MCP server with selected toolsets:

```bash
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="context,repos,issues,pull_requests" ghcr.io/github/github-mcp-server
```

Clone MCP repos:

```powershell
$MasterRepo = Read-Host "Path to Master-Repo-Use"; $LanePath = Read-Host "Folder where MCP repos should be cloned"; New-Item -ItemType Directory -Force $LanePath | Out-Null; Get-Content (Join-Path $MasterRepo "repo-lists\mcp-servers-extended.txt") | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { gh repo clone $_ (Join-Path $LanePath ($_ -replace '/','-')) }
```
