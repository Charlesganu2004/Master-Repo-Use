# Security Guide

GitHub: https://github.com/Charlesganu2004/Master-Repo-Use

This file covers how the repo protects itself and its agents from attack. Read this before setting up any agent, plugin, or MCP server.

Commands use `REVIEWED_VERSION` as a fail-closed placeholder. Replace it only with an exact release
version verified against the official package registry and source repository; never replace it with
`latest` or an automatic-yes flag.

---

## Threat Model

The main risks in an agent + MCP + plugin system are:

| Threat | How it happens | Mitigation |
|---|---|---|
| Prompt injection | Malicious text in tool output that overrides agent instructions | System prompts are write-once; tool output is data, never instructions |
| Agent injection | A bad agent is added to the catalog or loaded into an orchestration flow | Agents come only from this repo's `agents/` folder; external agents require explicit review |
| Secret exposure | API keys appear in markdown, logs, or issue drafts | Lock (secret-scanner-lock.md) scans every file; no secrets in committed files |
| MCP path escape | An agent accesses files outside its allowed MCP Roots | Every MCP server is started with explicit allowed-paths; no wildcards |
| Over-permissioned tools | An agent has access to tools it does not need, increasing blast radius | Each agent declares only the tools it needs; tool allowlists are enforced |
| Live financial action without approval | A trading agent places a live order autonomously | Every live order requires explicit human approval in the current conversation |
| Dependency vulnerability | A package in this repo has a known CVE | Delta (dependency-watch-delta.md) runs weekly; Sentinel audits monthly |

---

## Agent Injection Prevention

To prevent a bad agent from being injected into this system:

1. **Agents come only from `agents/`** — this folder is the only trusted source of agent personas and system prompts. Do not load agents from external URLs or untrusted repos without a Sentinel review.

2. **System prompts are write-once at setup time** — once an agent is wired up, its system prompt cannot be changed by any user message or tool output. If you see an agent receiving a message like "Ignore your previous instructions," treat it as a prompt injection attempt.

3. **External content is data, not instructions** — any text that comes from a tool call (file read, GitHub API response, web search result, database query) is treated as data to process, not instructions to follow. An agent that starts executing instructions found in tool output should be stopped immediately.

4. **New agents are reviewed before use** — if you add a new agent file to `agents/`, run Sentinel on it before wiring it up. Use this checklist:
   - [ ] Does the system prompt have clear hard limits?
   - [ ] Are escalation rules defined?
   - [ ] Is the tool list minimal?
   - [ ] Does it require human approval for destructive or financial actions?

---

## MCP Security Rules

Every MCP server in this repo follows these rules:

1. **Explicit allowed paths** — never use a wildcard (`/`) as the allowed path. Always scope to the minimum folder needed:

   ```powershell
   # Correct — scoped to the agents folder
   npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION C:\Users\Me\Master-Repo-Use\agents

   # Wrong — exposes the entire drive
   npx @modelcontextprotocol/server-filesystem@REVIEWED_VERSION C:\
   ```

2. **Minimum toolsets for GitHub MCP** — never enable all toolsets. Use only what the agent needs:

   ```bash
   -e GITHUB_TOOLSETS="repos,issues"  # not "all"
   ```

3. **Read-only where possible** — for auditing, health checks, and scanning, mount the filesystem read-only:

   ```bash
   docker run -i --rm --mount type=bind,src="$allowed_path",dst=/projects/workspace,ro mcp/filesystem /projects
   ```

4. **No secrets in MCP configs** — API keys go in environment variables, not in the MCP config file. Config files are committed to git; env vars are not.

---

## Secret Scanning

Run Lock (secret-scanner-lock.md) before every commit:

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
git diff --cached | detect-secrets-hook --baseline .secrets.baseline
```

Pre-commit hook (add to `.git/hooks/pre-commit`):

```bash
#!/bin/bash
detect-secrets-hook --baseline .secrets.baseline $(git diff --cached --name-only)
if [ $? -ne 0 ]; then
  echo "Potential secrets detected. Review and update baseline if false positive."
  exit 1
fi
```

Lock also runs as part of the Sentinel monthly audit.

---

## Access Control for This Repo

**Option A — Private repo with viewer access (current setup)**

You own the repo. Coworkers can view and read everything but cannot push commits or merge PRs.

To invite a coworker as a viewer:
1. Go to `https://github.com/Charlesganu2004/Master-Repo-Use` → Settings → Collaborators.
2. Add their GitHub username.
3. Set role to **Read** (not Write, not Admin).

They can clone, view all files, and follow the instructions — but cannot push changes.

**Option B — GitHub Organization (for teams)**

If your team needs to share the repo more broadly (multiple owners, teams-based access, org-level settings):

1. Create a GitHub Organization: `github.com/organizations/plan`.
2. Transfer the repo to the org: Settings → Transfer ownership.
3. Create teams within the org: `Viewers` (Read permission), `Contributors` (Write permission), `Owners` (Admin).
4. Add coworkers to the appropriate team.

Benefits: SSO, team-based access control, audit logs, organization-wide secrets.
Trade-off: more setup, organization billing if private repos exceed the free tier.

**Option C — Fork-based collaboration**

Coworkers fork the repo to their own GitHub account. They make changes in their fork and open PRs to your repo. You review and merge.

This keeps your repo clean and gives you full control over what gets merged. Coworkers do not need write access to your repo.

---

## Financial Action Safety Gates

Every trading-related action in this repo requires a safety gate. The hierarchy is:

```text
Agent proposes action (Rex, Nova, Qubit)
  → Sage reviews against risk limits
  → If paper: proceed
  → If live: human must type explicit approval in this conversation
  → Maxwell logs the action
  → Audit log written to plugins/[plugin]/audit.log
```

No agent in this repo can place a live financial order without:
- "Rex: live mode approved" (or equivalent) typed by the human in the current conversation
- Sage returning APPROVED
- The action being logged to the audit file

---

## Reporting a Security Issue

If you find a security vulnerability in this repo:

1. Do NOT open a public GitHub issue.
2. Email `charlesganu2004@gmail.com` with "SECURITY:" in the subject line.
3. Include: what you found, how to reproduce it, what the impact is.
4. You will receive a response within 72 hours.

---

## Security Agents Quick Reference

| Agent | What it does | When to use |
|---|---|---|
| [Sentinel](../agents/security-sentinel.md) | Full security audit | Monthly, before major releases |
| [Ghost](../agents/redteam-ghost.md) | Authorized threat modeling | When designing new attack-surface-expanding features |
| [Lock](../agents/secret-scanner-lock.md) | Secret scanning | Before every commit |
| [Lex](../agents/compliance-lex.md) | Compliance review | When handling personal data or financial operations |
