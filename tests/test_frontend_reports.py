"""Client grouping and hardware reports never imply browser hardware access."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FrontendReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reason = "Environment requires working node to execute frontend JavaScript contract tests"
        try:
            probe = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=10
            )
        except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired) as error:
            raise unittest.SkipTest(f"{reason}: {type(error).__name__}") from error
        if probe.returncode != 0:
            raise unittest.SkipTest(f"{reason}: node --version exited {probe.returncode}")

    def test_shared_frontend_contract_in_node(self):
        code = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const cs = require('./designs/custom-surfaces.js');
const data = JSON.parse(fs.readFileSync('atlas-data.json', 'utf8'));
const groups = cs.clientGroups(data);
assert.deepEqual(groups.map(g => g.id), ['copilot','gemini','claude','chatgpt','open','other']);
assert.deepEqual(groups.flatMap(g => g.surfaces.map(s => s.id)).sort(),
  data.surfaces.map(s => s.id).sort());
for (const client of ['copilot','gemini','claude']) {
  const draft = cs.draftFor(data, client);
  const generated = cs.commands(data, draft.kind, draft.values);
  assert(generated.ok);
  assert.equal(generated.steps[0].command, data.setupRecipes.find(r=>r.id===`setup-rules-${client}`).commands.windows);
  for (const platform of ['windows','macos','linux','wsl']) {
    const selected = cs.commands(data, 'ide', {client,platform});
    assert.equal(selected.steps[0].command, data.setupRecipes.find(r=>r.id===`setup-rules-${client}`).commands[platform]);
  }
}
assert(!cs.commands(data, 'ide', {client:'copilot; echo unsafe'}).ok);
assert(!cs.commands(data, 'ide', {client:'all'}).ok);
const raw = {schema:'atlas.hardware.v1', platform:'windows', ramGb:8,
  compatibleModels:['gemma3:1b','qwen3:32b','unknown-model']};
const valid = cs.validateReport(JSON.stringify(raw), data, 'windows');
assert(valid.ok);
assert.deepEqual(valid.modelIds, ['model-gemma3-1b']);
assert(!cs.validateReport(JSON.stringify(raw), data, 'linux').ok);
for (const value of [null, [], {}, { ...raw, ramGb:'8' }, { ...raw, ramGb:-1 },
  {...raw, compatibleModels:[';echo unsafe']}, {...raw,schema:'other'}]) {
  assert(!cs.validateReport(JSON.stringify(value), data, 'windows').ok);
}
assert(!cs.validateReport('x'.repeat(65537), data, 'windows').ok);
const context = {console, navigator:{userAgent:'Windows'}, localStorage:{getItem:()=>null,setItem:()=>{}},
  window:{CustomSurfaces:cs, __ATLAS_DATA__:data}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('designs/atlas-core.js', 'utf8') + ';globalThis.core=AtlasCore;', context);
(async()=>{
  const core = context.core;
  await core.init();
  core.setPlatform('windows');
  core.setHardware('ram', 4096);
  assert.equal(core.availableSurfaces().filter(s=>s.group==='local-model').length,0);
  const modelComponent = {setupRecipe:'setup-model-gemma3-1b'};
  assert.equal(core.setupCommandFor(modelComponent, 'windows'), null);
  assert(core.importHardwareReport(JSON.stringify(raw)).ok);
  assert(core.setupCommandFor(modelComponent, 'windows'));
  core.toggleSurface('model-gemma3-1b');
  assert.equal(core.selectedSurfaces().filter(s=>s.group==='local-model').length,1);
  core.setPlatform('linux');
  assert.equal(core.setupCommandFor(modelComponent, 'windows'), null);
  assert.equal(core.selectedSurfaces().filter(s=>s.group==='local-model').length,0);
  core.setPlatform('windows');
  assert.equal(core.availableSurfaces().filter(s=>s.group==='local-model').length,0);
  console.log('frontend report contract passed');
})().catch(error=>{console.error(error);process.exitCode=1});
"""
        result = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("frontend report contract passed", result.stdout)

    def test_report_command_is_read_only_and_uses_existing_helper(self):
        result = subprocess.run(
            ["node", "-e", "console.log(JSON.stringify(require('./designs/custom-surfaces.js').reportCommand('windows')))"],
            cwd=ROOT, capture_output=True, text=True, check=True)
        command = json.loads(result.stdout)
        self.assertIn("from scripts import local_model_advisor", command)
        self.assertNotIn("--install", command)
        self.assertNotIn("--yes", command)
        self.assertNotIn("fetch", command)
        code = command.split(' -c "', 1)[1][:-1]
        compile(code, "<hardware-report-command>", "exec")


if __name__ == "__main__":
    unittest.main()
