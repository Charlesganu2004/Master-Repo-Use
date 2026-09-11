# Computer control routes

`scripts/harness_computer.py` is the read-only router for screen and browser
work. It does not move a mouse, press a key, open a browser, contact a model,
install a package, or enable a plugin. Its job is to stop an agent from treating
a skill folder or configuration entry as a tool that is definitely active.

## One route per target

| Target | Preferred route | What the check can prove | What it cannot prove |
| --- | --- | --- | --- |
| Native Windows app | Installed OpenAI Computer Use package | Bundled manifest and skill version exist | The current host exposes its Computer Use tool |
| Browser | Microsoft Playwright or Playwright MCP | Local package, executable and configuration evidence | Browser binaries or a live model-session tool are ready |
| Rust application | Official Playwright JavaScript/TypeScript sidecar | The official pinned source and any local Playwright evidence | A Rust binding is supported by Microsoft |
| Direct Rust API | `padamson/playwright-rust` only by explicit choice | A Cargo declaration and toolchain exist | Driver download integrity, browser installation or runtime launch |

Run the checks from the repository root:

```text
python scripts/harness_computer.py --check
python scripts/harness_computer.py --route native
python scripts/harness_computer.py --route browser-js
python scripts/harness_computer.py --route browser-rust --repo PATH
```

Add `--json` for machine-readable evidence. Every route response includes
`actionTaken: false`.

## Injection harnesses and the conditional route

The surface, proxy, wrapper, goal and super harnesses all call the shared prompt
pipeline. A computer-control lane in that pipeline tells the model to load
`master-computer-control` and use this router only when screen, GUI or browser
work matches. `master-computer-control` also travels in the surface harness's
enforced skill set, so hooked clients and browser bundles receive the same
limits. The control lane does not appear on unrelated prompts.

The computer-control router is a separate diagnostic capability, not a
prompt-injection harness. Its check remains available beneath the harness cards
and in the command catalog. The package also exposes a CLI alias for that
diagnostic, so counting installed commands is not a count of injection paths.

## Support boundary

- OpenAI Computer Use `26.903.61454` was the proprietary bundled package
  inspected for the recorded review. It is not a claim about the currently
  installed version. Run the native route check for local package evidence;
  only a supported host can expose its live tool.
- Playwright `v1.63.0` and Playwright MCP `v0.0.80` are Microsoft's official
  routes. The supported language list is JavaScript/TypeScript, Python, Java
  and .NET.
- Microsoft closed the request for an official Rust binding as not planned.
  The default Rust route is therefore official Playwright testing the Rust app
  from outside the process.
- `padamson/playwright-rust` `v0.18.0` is an optional Apache-2.0 third-party
  binding. It passed static intake with a supply-chain note and is never
  installed automatically.

Exact commits, sources and agent routes are in
`skills/master-computer-control/references/capabilities.json`.

## Agent roles

`orchestrator-maxwell` coordinates independent lanes. `ui-canvas` reviews the
visible experience. `tester-probe` verifies behavior and boundaries.
`security-sentinel` reviews permissions, downloads, secrets and untrusted screen
content. The router carries file references only. Full agent definitions load
when their role fits, not on every prompt.
