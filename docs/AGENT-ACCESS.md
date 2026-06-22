# Agent Access Guide

This guide is for the "let the agent go more places on the computer depending on the access you give it" part of the repo.

The short version: use explicit allowed directories. Do not give an agent the whole machine unless you have a very specific reason and you are comfortable with the risk.

![Agent access model](../assets/agent-access-map.svg)

Read this diagram as a permission ladder. Start with one repo folder, add an AgentLab folder for multi-repo experiments, then add personal folders or broader paths only when the task truly needs them.

## Mental Model

```text
You choose roots
  -> MCP filesystem server exposes only those roots
  -> Agent reads/searches/edits through MCP tools
  -> You review important writes
```

The same idea applies to GitHub:

```text
You choose token scopes and toolsets
  -> GitHub MCP server exposes only those capabilities
  -> Agent reads repos/issues/PRs/actions through tools
  -> You review changes before merge
```

## Access Levels

| Level | What the agent can reach | Best for | Risk |
| --- | --- | --- | --- |
| Workspace | One repo folder | Normal coding tasks | Low |
| Project lab | A folder containing many cloned repos | Multi-repo exploration | Medium |
| Selected personal folders | Documents, Downloads, Desktop, or another named folder | File organization and research | Medium to high |
| Whole drive | Most of the local computer | Rare recovery or migration tasks | High |

## Recommended Local Folder Layout

```text
<PATH_TO_MASTER_REPO>
<PATH_TO_AGENT_LAB>
<PATH_TO_AGENT_LAB>\agent-frameworks
<PATH_TO_AGENT_LAB>\rag-memory
<PATH_TO_AGENT_LAB>\context-tools
```

Set it up:

```powershell
$AgentLab = Read-Host "Where should the agent lab folder live?"; New-Item -ItemType Directory -Force $AgentLab | Out-Null
```

## Filesystem MCP Server

Repo: [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

Why this repo matters:

- It provides filesystem tools for agents.
- It can read, write, edit, list, move, search, and inspect files.
- It restricts operations to allowed directories.
- MCP Roots can update allowed directories at runtime when the host supports it.

### Windows VS Code MCP Config Example

Use this as a template, not a secret-bearing file. Put it in your MCP host config if your host supports this shape.

```json
{
  "servers": {
    "filesystem": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "<PATH_TO_MASTER_REPO>",
        "<PATH_TO_AGENT_LAB>"
      ]
    }
  }
}
```

### WSL Or Linux MCP Config Example

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "<PATH_TO_MASTER_REPO>",
        "<PATH_TO_AGENT_LAB>"
      ]
    }
  }
}
```

### Docker Example

Read/write:

```bash
docker run -i --rm --mount type=bind,src="$PWD",dst=/projects/workspace mcp/filesystem /projects
```

Read-only:

```bash
docker run -i --rm --mount type=bind,src="$PWD",dst=/projects/workspace,ro mcp/filesystem /projects
```

## GitHub MCP Server

Repo: [github/github-mcp-server](https://github.com/github/github-mcp-server)

Why this repo matters:

- It connects agents to GitHub repositories, code files, issues, pull requests, Actions, users, and security tooling.
- It supports toolsets so you can expose only the GitHub capabilities you need.
- It supports Docker and local binary workflows.

### Minimal Docker Example

```bash
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="context,repos,issues,pull_requests" ghcr.io/github/github-mcp-server
```

### More Capable Dev Example

```bash
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -e GITHUB_TOOLSETS="repos,issues,pull_requests,actions,code_security" ghcr.io/github/github-mcp-server
```

### MCP Host Config Shape

```json
{
  "servers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_TOOLSETS=context,repos,issues,pull_requests",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
      }
    }
  }
}
```

## Custom Agents

GitHub's custom agent model is file-based: agents can be defined under `.github/agents` in a repository or in organization-level `.github` repos. The GitHub changelog says these agents can specialize Copilot coding agent with prompts, tool selections, and MCP servers.

Use custom agents when you want repeatable behavior, for example:

- `repo-curator`: keeps this catalog clean and updates repo lists.
- `rag-builder`: wires a project into LightRAG or Upstash Vector.
- `context-auditor`: checks whether a session is carrying too much tool output.
- `pitch-builder`: turns project notes into Slidev or Marpit decks.

An inactive starter prompt lives at [examples/copilot-agent/repo-curator.agent.md](../examples/copilot-agent/repo-curator.agent.md).

## Safety Checklist

Before granting access:

- List the folders you want the agent to reach.
- Prefer read-only mounts for research.
- Avoid secrets folders unless the task requires them.
- Avoid whole-drive access for normal coding.
- Use GitHub token scopes and MCP toolsets intentionally.
- Review diffs before committing.

During long sessions:

- Ask the agent to summarize durable decisions.
- Keep important file paths in the prompt or memory.
- Use `/context` and `/compact` in Copilot CLI when available.
- Save handoff notes before major compaction or context resets.

## Source Links

- [Filesystem MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [GitHub custom agents changelog](https://github.blog/changelog/2025-10-28-custom-agents-for-github-copilot/)
- [GitHub Copilot CLI context management](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management)
