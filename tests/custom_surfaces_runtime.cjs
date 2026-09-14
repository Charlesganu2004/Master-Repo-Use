/* Runs designs/custom-surfaces.js against the real atlas-data.json.
 *
 * The generator writes commands people copy into a shell, so the checks that
 * matter are the ones a string comparison in Python cannot make: that a hostile
 * value is refused BEFORE a command exists, that the substituted command is the
 * one the template says, and that saving and removing behave with a storage that
 * can fail. Prints "Custom surfaces runtime: OK" and exits 0 only if every check
 * passed; the Python test asserts both.
 */
'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'designs', 'atlas-data.json'), 'utf8'));

// A storage the tests control, including one that throws, because a blocked or
// full localStorage is a real browser state and the page must survive it.
function memoryStorage() {
  const items = {};
  return {
    getItem: key => (Object.prototype.hasOwnProperty.call(items, key) ? items[key] : null),
    setItem: (key, value) => { items[key] = String(value); },
    removeItem: key => { delete items[key]; },
  };
}
global.window = { localStorage: memoryStorage() };

const CS = require(path.join(ROOT, 'designs', 'custom-surfaces.js'));
assert.strictEqual(global.window.CustomSurfaces, CS, 'the browser global and the module are the same object');

let checks = 0;
function check(name, fn) {
  try {
    fn();
    checks += 1;
  } catch (error) {
    console.error(`FAIL ${name}: ${error.message}`);
    process.exit(1);
  }
}

const kinds = CS.kinds(data);

check('the payload ships the kinds', () => {
  assert.ok(kinds.length >= 5, `only ${kinds.length} kinds`);
  for (const id of ['openai-endpoint', 'ollama', 'ide', 'cli', 'chat']) {
    assert.ok(CS.kind(data, id), `missing kind ${id}`);
  }
});

check('every group preselects a kind that names it, so the + never opens blank', () => {
  for (const group of data.surfaceGroups) {
    const chosen = CS.defaultKindFor(data, group.id);
    assert.ok(chosen, `no default for ${group.id}`);
    assert.ok(CS.kind(data, chosen).defaultFor.includes(group.id),
      `${group.id} preselects ${chosen}, which does not list it`);
  }
});

check('Copilot and other IDE agents get the install, not a proxy', () => {
  const result = CS.commands(data, 'ide', { client: 'copilot', platform: 'windows' });
  assert.ok(result.ok, result.error);
  assert.deepStrictEqual(result.steps.map(s => s.command),
    [data.setupRecipes.find(recipe => recipe.id === 'setup-rules-copilot').commands.windows]);
  assert.match(result.limit, /Only the selected local client/);
});

check('an open frontier endpoint is quoted into the proxy command', () => {
  const result = CS.commands(data, 'openai-endpoint', { url: 'https://openrouter.ai/api/v1' });
  assert.ok(result.ok, result.error);
  assert.strictEqual(result.steps[0].command,
    'master-harness-super --serve --port 11500 --upstream "https://openrouter.ai/api/v1"');
  for (const step of result.steps) assert.doesNotMatch(step.command, /\{\w+\}/, 'a placeholder survived');
});

check('local servers with a port and an IPv6 host are accepted', () => {
  for (const url of ['http://127.0.0.1:11434', 'http://localhost:8000/v1', 'http://[::1]:11434',
                     'https://api.groq.com/openai/v1']) {
    assert.ok(CS.commands(data, 'ollama', { url }).ok, url);
  }
});

check('hostile URLs are refused before any command exists', () => {
  const hostile = [
    'https://x.example/$(id)',            // bash and PowerShell expand this inside double quotes
    'https://x.example/${IFS}',
    'https://x.example/`whoami`',
    'https://x.example/"; rm -rf ~; "',
    'https://x.example/ && calc',
    'https://x.example/%USERPROFILE%',    // cmd.exe expands this inside double quotes
    'https://x.example/a;b',
    'https://x.example/a|b',
    'javascript:alert(1)',
    'file:///etc/passwd',
    'ftp://x.example/',
    'https://x.example/\nrm -rf ~',
  ];
  for (const url of hostile) {
    const result = CS.commands(data, 'openai-endpoint', { url });
    assert.strictEqual(result.ok, false, `accepted ${JSON.stringify(url)}`);
    assert.strictEqual(result.steps, undefined, 'a refused value still produced steps');
  }
});

check('a CLI command is taken as written, and shell operators are refused', () => {
  const ok = CS.commands(data, 'cli', { command: 'aider --message' });
  assert.ok(ok.ok, ok.error);
  assert.strictEqual(ok.steps[0].command, 'master-harness-super --run -- aider --message "your prompt"');
  for (const command of ['ollama run qwen3:4b', 'python my_tool.py --prompt', 'llm -m gpt-4o']) {
    assert.ok(CS.commands(data, 'cli', { command }).ok, command);
  }
  for (const command of ['aider; rm -rf ~', 'aider && calc', 'aider | tee x', 'aider $(id)',
                         'aider `id`', 'aider (Remove-Item x)', 'aider > out', 'aider\ncalc',
                         'aider %PATH%', 'aider "x"']) {
    assert.strictEqual(CS.commands(data, 'cli', { command }).ok, false, `accepted ${JSON.stringify(command)}`);
  }
});

check('a chat product must be one of the bundle surfaces', () => {
  const ok = CS.commands(data, 'chat', { product: 'chatgpt' });
  assert.ok(ok.ok, ok.error);
  assert.deepStrictEqual(ok.steps.map(s => s.command),
    ['master-harness-super --bundle chatgpt', 'dist/auto-mode/auto-mode-chatgpt.md']);
  assert.strictEqual(CS.commands(data, 'chat', { product: 'chatgpt; rm -rf ~' }).ok, false);
  assert.strictEqual(CS.commands(data, 'chat', { product: 'not-a-product' }).ok, false);
});

check('the name hint is a real example, never "My an ..."', () => {
  for (const spec of kinds) {
    const hint = CS.namePlaceholder(spec);
    assert.ok(hint && spec.examples.startsWith(hint), `${spec.id}: ${hint}`);
    assert.doesNotMatch(hint, /^My an? /);
  }
  assert.strictEqual(CS.namePlaceholder({}), 'My client');
});

check('commands split into words at spaces only, so a flag is never broken', () => {
  assert.deepStrictEqual(CS.tokens('master-harness-super  --serve --port 11500'),
    ['master-harness-super', '--serve', '--port', '11500']);
  const result = CS.commands(data, 'openai-endpoint', { url: 'https://openrouter.ai/api/v1' });
  assert.strictEqual(CS.tokens(result.steps[0].command).join(' '), result.steps[0].command,
    'rejoining the words must give back the exact command');
});

check('empty and unknown input are refused with a reason', () => {
  const empty = CS.commands(data, 'openai-endpoint', { url: '   ' });
  assert.strictEqual(empty.ok, false);
  assert.match(empty.error, /required/);
  assert.strictEqual(CS.commands(data, 'no-such-kind', {}).ok, false);
});

check('save, list by group and remove round-trip, and ids never collide', () => {
  const first = CS.save(data, { kind: 'ollama', name: 'Home box', group: 'local-model',
                                values: { url: 'http://127.0.0.1:11434' } });
  assert.ok(first.ok, first.error);
  const second = CS.save(data, { kind: 'ide', name: 'Copilot', group: 'web-code', values: { client: 'copilot', platform: 'windows' } });
  assert.ok(second.ok, second.error);
  assert.deepStrictEqual(CS.forGroup('local-model').map(c => c.name), ['Home box']);
  assert.ok(CS.remove(first.id));
  // Saving again after a removal must not reuse an id still held by another entry.
  const third = CS.save(data, { kind: 'ide', name: 'Copilot', group: 'web-code', values: { client: 'copilot', platform: 'windows' } });
  assert.ok(third.ok);
  assert.notStrictEqual(third.id, second.id);
  assert.ok(CS.remove(second.id));
  assert.deepStrictEqual(CS.forGroup('web-code').map(c => c.id), [third.id]);
  CS.remove(third.id);
  assert.deepStrictEqual(CS.load(), []);
});

check('a value that fails validation is never saved', () => {
  const refused = CS.save(data, { kind: 'openai-endpoint', name: 'bad', group: 'local-model',
                                  values: { url: 'https://x.example/$(id)' } });
  assert.strictEqual(refused.ok, false);
  assert.deepStrictEqual(CS.load(), []);
});

check('tampered storage is re-validated when shown, not trusted', () => {
  window.localStorage.setItem(CS.STORAGE_KEY, JSON.stringify([
    { id: 'x', group: 'local-model', name: 'planted', kind: 'openai-endpoint',
      values: { url: 'https://x.example/$(id)' } }]));
  const [planted] = CS.forGroup('local-model');
  assert.strictEqual(CS.commands(data, planted.kind, planted.values).ok, false);
  window.localStorage.setItem(CS.STORAGE_KEY, '{not json');
  assert.deepStrictEqual(CS.load(), []);
  window.localStorage.setItem(CS.STORAGE_KEY, '{"an":"object"}');
  assert.deepStrictEqual(CS.load(), []);
  window.localStorage.removeItem(CS.STORAGE_KEY);
});

check('a storage that throws leaves the generator working and says so on save', () => {
  const saved = window.localStorage;
  window.localStorage = {
    getItem() { throw new Error('blocked'); },
    setItem() { throw new Error('blocked'); },
  };
  try {
    assert.deepStrictEqual(CS.load(), []);
    assert.ok(CS.commands(data, 'ide', { client: 'copilot', platform: 'windows' }).ok);
    const result = CS.save(data, { kind: 'ide', name: 'x', group: 'web-code', values: { client: 'copilot', platform: 'windows' } });
    assert.strictEqual(result.ok, false);
    assert.match(result.error, /would not save/);
  } finally {
    window.localStorage = saved;
  }
});

console.log(`Custom surfaces runtime: OK (${checks} checks)`);
