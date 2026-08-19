# Optional Token / Work-Spend Budget

This setup is independent from the main Master Repo bootstrap. Nothing here is enabled by the large one-liners in the README.

## Goal

Use paid models until a configurable work budget is reached, then route compatible API/CLI workloads to a free/local model instead of continuing to spend.

## Important distinction

There are three different limits:

1. **Context limit** — how much text/tools/history a model sees in one request.
2. **Output limit** — how many tokens a model may generate in one response.
3. **Spend/work budget** — how much paid usage is allowed over a day/week/month.

A context compressor such as Headroom can reduce token usage, but it is not by itself a billing hard-stop.

## Recommended architecture

```text
Claude Code / Codex / Copilot-compatible API client / custom agent
        |
        v
local budget/router gateway
        |-- under budget --> paid primary provider/model
        |
        `-- budget reached --> local/free OpenAI-compatible model
                                 (LocalAI / llama.cpp / another vetted local server)
```

This works only for clients that allow their model endpoint/provider to be routed through a gateway or custom API configuration. Subscription web UIs such as ordinary ChatGPT, Claude.ai, or GitHub.com model pickers control their own model availability and cannot be silently rerouted by this repository.

## Suggested environment variables

```bash
MASTER_REPO_BUDGET_ENABLED=true
MASTER_REPO_BUDGET_PERIOD=monthly
MASTER_REPO_BUDGET_USD=25
MASTER_REPO_SOFT_LIMIT_PERCENT=80
MASTER_REPO_HARD_LIMIT_PERCENT=100
MASTER_REPO_FALLBACK_PROVIDER=local
MASTER_REPO_FALLBACK_BASE_URL=http://127.0.0.1:8080/v1
MASTER_REPO_FALLBACK_MODEL=local-default
```

Keep API keys in the operating system secret store or ignored environment files. Never commit them.

## Compression before fallback

Install Headroom only if wanted:

```bash
uv tool install --python 3.13 "headroom-ai[all]"
headroom doctor
```

Then wrap a supported local coding client:

```bash
headroom wrap claude
headroom wrap codex
headroom wrap copilot
```

This can reduce context usage before the spend cap is reached.

## Free/local fallback

Use a vetted local OpenAI-compatible server from the Master Repo, for example LocalAI or llama.cpp. The exact model should match the machine's RAM/VRAM and license requirements.

Do not label a hosted model "free" unless its provider actually offers a zero-cost tier at the time of use. A local model is the safest deterministic fallback for avoiding another API charge.

## Hard-stop behavior

Recommended router policy:

```text
0-79% budget     -> normal paid model routing
80-99%           -> cheaper paid model + compression + warning
100% and above   -> block paid provider calls and route supported workloads to local fallback
```

For tasks that require a capability unavailable in the fallback model, fail closed and tell the user instead of silently making a paid call.

## Platform notes

- **Claude Code:** API/provider-based sessions can use a proxy/router path; Claude subscription UI behavior remains controlled by Anthropic.
- **Codex:** use supported provider/configuration or a local OpenAI-compatible endpoint where supported; repo `AGENTS.md` continues to apply.
- **GitHub Copilot:** repo/global instructions can enforce a behavioral budget policy, but GitHub-hosted Copilot model billing/routing is controlled by GitHub. Only external tools or compatible gateway-backed workflows can be rerouted automatically.
- **ChatGPT web / Claude.ai / GitHub.com:** use their native plan/usage controls. The Master Repo cannot intercept their hosted requests.

## Recommended fail-safe

If `MASTER_REPO_BUDGET_ENABLED=true` and the budget state cannot be read reliably, default to **no paid call** until the user resolves the budget state. This prevents accidental overage.
