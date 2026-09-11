'use strict';

// Executes the real page script against a small DOM contract. This verifies
// navigation and focus state, not browser layout or pointer hit testing.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const page = fs.readFileSync(path.join(__dirname, '..', 'designs', 'd36-mongo.html'), 'utf8');
const script = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const ids = [...page.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
const nodes = new Map(ids.map(id => [id, {
  id, hidden: ['mgAtlasHost', 'mgReturn'].includes(id), disabled: id.startsWith('mgOpen'),
  children: [], textContent: '', innerHTML: '', focused: false,
  appendChild(node) { this.children.push(node); },
  focus() { this.focused = true; }
}]));
let draws = 0;
let mounts = 0;
const panes = { tab: 'map', draw() { draws += 1; } };
const stage = { focused: false, focus() { this.focused = true; } };
const context = {
  console, setTimeout,
  document: { getElementById: id => nodes.get(id), querySelectorAll: () => [] },
  AtlasTheme: { mount() {} },
  AtlasCore: {
    init: async () => {},
    state: { data: { catalogStore: {
      totalDocuments: 0, collections: [], indexes: [], queries: [],
      checkCommand: 'check', loadCommand: 'load', createCommand: 'create'
    } } },
    copy: async () => true
  },
  AtlasPanes: panes,
  AtlasExhibition: { workspace(options) {
    assert.equal(options.skin, 'store');
    mounts += 1;
    nodes.set('stage', stage);
    return { className: 'atlas-workspace' };
  } }
};
vm.createContext(context);
vm.runInContext(script, context, { filename: 'd36-mongo.html' });

setImmediate(() => {
  assert.equal(mounts, 1, 'the Store design mounts the shared workspace');
  assert.equal(nodes.get('mgAtlasHost').children.length, 1);
  assert.equal(nodes.get('mgAtlasHost').hidden, true, 'the preview is the initial view');
  const open = nodes.get('mgOpenAtlas');
  const commands = nodes.get('mgOpenCommands');
  const back = nodes.get('mgReturn');
  assert.equal(open.disabled, false, 'Open full Atlas is enabled after initialization');
  assert.equal(commands.disabled, false, 'Command center is enabled after initialization');
  open.onclick();
  assert.equal(panes.tab, 'index');
  assert.equal(nodes.get('mgPreview').hidden, true);
  assert.equal(nodes.get('mgAtlasHost').hidden, false);
  assert.equal(stage.focused, true, 'opening the workspace moves focus into it');
  assert.equal(back.hidden, false);
  back.onclick();
  assert.equal(nodes.get('mgPreview').hidden, false);
  assert.equal(nodes.get('mgAtlasHost').hidden, true);
  assert.equal(open.focused, true, 'return restores focus to the last opener');
  commands.onclick();
  assert.equal(panes.tab, 'commands', 'Command center opens the shared command list');
  back.onclick();
  assert.equal(commands.focused, true);
  assert.equal(draws, 2, 'both entry controls render their requested tab');
  console.log('Store navigation runtime: OK (index, commands, return, focus)');
});
