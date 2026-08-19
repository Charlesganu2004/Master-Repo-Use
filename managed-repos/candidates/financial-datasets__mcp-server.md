# Managed adoption candidate: financial-datasets/mcp-server

Status: **OWNER REVIEW REQUIRED**

The upstream MCP server is MIT licensed and still maps useful Financial Datasets API operations into MCP, but its last GitHub push is more than one year old. It has therefore been removed from the active runtime catalog under the Master Repo lifecycle rule.

## Potentially useful pieces

- MCP tool schemas for financial statements, prices, news, and crypto data.
- Environment/config pattern for `FINANCIAL_DATASETS_API_KEY`.
- Small Python/httpx MCP adapter architecture that should be inexpensive to modernize.

## Adoption plan

1. Verify the current Financial Datasets API contract and authentication model.
2. Deep-scan the final upstream source and dependency lock state.
3. Preserve MIT copyright/license text.
4. Rebuild against the current MCP Python SDK rather than carrying old dependency pins forward.
5. Add strict input validation, request timeouts, retry/backoff, rate-limit handling, logging redaction, and bounded date/range inputs.
6. Add tests that prevent prompt/tool arguments from reaching URLs, shell commands, SQL, or file paths unsafely.
7. Keep any trading/action capability read-only unless a separate explicitly approved write-capable integration is designed.
8. Create the maintained `Charlesganu2004` repo only after owner approval and re-run all Master Repo security gates before cataloging it.
