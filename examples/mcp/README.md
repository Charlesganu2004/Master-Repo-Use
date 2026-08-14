# MCP Config Examples

These JSON files are templates, not drop-in configs. Replace every path placeholder first.

Install an exact package version that you have reviewed into a dedicated tools folder:

```powershell
$McpTools = Read-Host "Dedicated folder for reviewed MCP packages"
npm install --prefix $McpTools @modelcontextprotocol/server-filesystem@REVIEWED_VERSION
```

Then replace `PATH_TO_MCP_TOOLS` in the JSON. The host launches the installed Node entry point
directly, so startup cannot fetch a package or wait for an `npx` installation prompt. Never replace
`REVIEWED_VERSION` with `latest`.
