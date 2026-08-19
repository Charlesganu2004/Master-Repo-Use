# Managed adoption candidate: FlowiseAI/Flowise

Status: **OWNER REVIEW REQUIRED — transition candidate**

The upstream project announced a feature freeze on 2026-07-27, archived the repository on 2026-08-10, and set EOL for 2026-08-31. The last release line includes `flowise@3.1.4`. Upstream explicitly encourages teams to fork the Apache-2.0 code if they need to continue maintaining it.

## Why it is still useful

- Mature visual agent/workflow builder.
- Large integration/node ecosystem.
- RAG, MCP, multi-agent, API, self-hosting, and workflow concepts remain useful to the Master Repo.

## Do not blindly fork

Before creating a Charles-managed replacement:

1. Deep-scan the exact final upstream revision with Guardian, Semgrep, Gitleaks, Trivy, OSV Scanner, and Snyk when available.
2. Review unresolved security advisories and the 3.1.4 startup/dependency reports.
3. Preserve the Apache-2.0 license and notices.
4. Decide whether to maintain a full fork or extract only reusable architecture/integration pieces.
5. Replace deprecated dependencies and remove abandoned integrations.
6. Add tests for authentication, tenant isolation, MCP command allowlists, file-path handling, SSRF, injection, secret handling, and plugin execution.
7. Create the maintained repository under `Charlesganu2004` only after Charles approves the scope.
8. Re-add the maintained replacement to the active catalog through an owner-approved PR.

Until then, `FlowiseAI/Flowise` is **transition/reference material**, not a recommended new production dependency.
