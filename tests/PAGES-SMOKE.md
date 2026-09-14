# Pages frontend verification

`build_pages_preview.py` calls the actual public builder, including the hardware
profiles, design studio, version metadata and privacy verifier. It requires an
empty output directory outside the private checkout and never overlays another
artifact.

```powershell
python tests\build_pages_preview.py --out C:\path\to\session-artifacts\public-site
$env:NODE_PATH = 'C:\path\to\existing\node_modules'
node tests\pages_smoke.cjs --site C:\path\to\session-artifacts\public-site --out C:\path\to\session-artifacts\screenshots
```

Use an existing Playwright installation and its Chromium. An alternate installed
Chromium can be supplied through `PLAYWRIGHT_CHROMIUM_EXECUTABLE`. These commands
do not install dependencies or browsers. Nothing is deployed.

The runner serves only the built artifact on loopback, blocks third-party
requests, and visits every published design, the gallery, the root command
center, and the palette studio at **1440 × 900** and **390 × 844**, with device
scale factor 1 and browser zoom 100%. It records every first viewport, command
center and setup view; checks hit targets, multi-select clients, all group +
controls, report validation, OS invalidation, filters, runtime/network errors
and document overflow. `report.json` contains exact screenshot paths and results;
`progress.json` preserves completed cases if interrupted. `--routes REGEX` is
for focused diagnosis only, not evidence of complete gallery coverage.
`--navigation-only` rechecks a navigation/style-only change on every route
without repeating unchanged setup forms. Its report is explicitly labeled and
supplements, never replaces, the full-controls run.

The runner also checks retained checkbox focus, arrow-key tab navigation, and
solid-background setup-action contrast (at least 4.5:1). It explicitly marks
gradient-backed contrast as requiring visual review rather than inventing a
measurement. This focused check is not a full accessibility audit.

Hardware reports use the existing read-only local advisor. The page validates
schema, operating system, memory and explicitly reported catalog model tags.
This is input validation, not remote hardware attestation. The browser cannot
scan the machine. Typed estimates and persisted selections do not enable local
model commands. The smoke's 8 GB report is a **synthetic fixture**, not a claim
about the test host.

Branded groups retain the original surface identifiers and per-client recipes.
The + form's supported local installer uses the existing reviewed recipe for
the selected client and operating system, never an all-client installation.
Hosted instructions remain advisory; local
hooks and proxy-only enforcement are described separately.

The exhibition scenes remain distinct. Their Full Atlas and Command center
actions reuse the existing responsive workspace rather than off-screen drawers
and fixed HUDs that obstructed controls on narrow screens.
