'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class ClassList {
  constructor() { this.values = new Set(); }
  add(...names) { names.forEach(name => this.values.add(name)); }
  remove(...names) { names.forEach(name => this.values.delete(name)); }
  contains(name) { return this.values.has(name); }
  toggle(name, force) {
    const enabled = force === undefined ? !this.contains(name) : Boolean(force);
    if (enabled) this.add(name); else this.remove(name);
    return enabled;
  }
}

class Element {
  constructor(tagName, id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.dataset = {};
    this.classList = new ClassList();
    this.children = [];
    this.hidden = false;
    this.listeners = {};
    this.textContent = '';
    this._html = '';
    this.controls = new Map();
    this.focused = false;
    this.attributes = new Map();
    this.style = {};
  }

  set className(value) {
    this.classList = new ClassList();
    String(value).split(/\s+/).filter(Boolean).forEach(name => this.classList.add(name));
  }

  get className() { return [...this.classList.values].join(' '); }

  set innerHTML(value) {
    this._html = String(value);
    this.textContent = this._html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    const controls = [
      ['[data-open-atlas]', 'button'],
      ['[data-open-command]', 'button'],
      ['[data-return-concept]', 'button']
    ];
    controls.forEach(([selector, tag]) => {
      if (this._html.includes(selector.slice(1, -1))) this.controls.set(selector, new Element(tag));
    });
  }

  get innerHTML() { return this._html; }

  appendChild(child) { this.children.push(child); child.parentElement = this; return child; }
  prepend(child) { this.children.unshift(child); child.parentElement = this; return child; }
  addEventListener(type, listener) { this.listeners[type] = listener; }
  click() {
    assert.ok(this.listeners.click, 'clicked control has no listener');
    this.listeners.click({ currentTarget: this, target: this });
  }
  focus() { this.focused = true; }
  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    this[name] = String(value);
  }
  getAttribute(name) { return this.attributes.has(name) ? this.attributes.get(name) : null; }
  removeAttribute(name) { this.attributes.delete(name); delete this[name]; }
  querySelector(selector) { return this.controls.get(selector) || null; }
  querySelectorAll() { return []; }
}

function makeRuntime(withDependencies, options = {}) {
  const body = new Element('body');
  const legacy = new Element('main', 'legacyAtlas');
  const stage = new Element('div', 'stage');
  stage.textContent = 'Atlas controls ready';
  stage.children.push(new Element('section'));
  if (options.hiddenStage) {
    stage.style.left = '-9999px';
    stage.setAttribute('aria-hidden', 'true');
  }
  const tabs = new Element('nav', 'tabs');
  const script = new Element('script');
  body.appendChild(legacy);
  body.appendChild(script);

  const document = {
    body,
    createElement: tag => new Element(tag),
    getElementById(id) {
      if (id === 'stage') return stage;
      if (id === 'tabs') return tabs;
      return body.children.find(node => node.id === id) || null;
    }
  };
  let drawCount = 0;
  const panes = withDependencies ? {
    tab: 'map',
    draw() { drawCount += 1; },
    mount() {},
    popover() {}
  } : undefined;
  const context = {
    console,
    document,
    Event: class Event {},
    innerWidth: 1280,
    innerHeight: 720,
    requestAnimationFrame: callback => callback(),
    scrollTo() {},
    __ATLAS_DATA__: { lanes: [], components: [], meta: {} },
    AtlasCore: withDependencies ? { on() {} } : undefined,
    AtlasPanes: panes,
    AtlasTheme: undefined
  };
  context.window = context;
  vm.createContext(context);
  const source = fs.readFileSync(path.join(__dirname, '..', 'designs', 'atlas-exhibition.js'), 'utf8');
  vm.runInContext(source, context, { filename: 'atlas-exhibition.js' });
  return { context, body, legacy, stage, tabs, panes, drawCount: () => drawCount };
}

function revealAndReturn(scene) {
  const runtime = makeRuntime(true);
  runtime.context.AtlasExhibition.mount(scene);
  const root = runtime.body.children[0];
  const open = root.querySelector('[data-open-atlas]');
  const command = root.querySelector('[data-open-command]');
  const back = root.querySelector('[data-return-concept]');

  assert.equal(runtime.legacy.hidden, true, 'scene mount hides the full Atlas');
  open.click();
  assert.equal(root.classList.contains('ex-collapsed'), true, 'Open full Atlas collapses the scene');
  assert.equal(runtime.body.classList.contains('exhibition-full-atlas'), true, 'body becomes scrollable');
  assert.equal(runtime.legacy.hidden, false, 'Open full Atlas reveals the existing workspace');
  assert.equal(runtime.stage.focused, true, 'focus moves into the revealed workspace');

  back.click();
  assert.equal(runtime.legacy.hidden, true, 'Return hides the full Atlas again');
  assert.equal(root.classList.contains('ex-collapsed'), false, 'Return restores the scene');
  assert.equal(open.focused, true, 'Return restores focus to its opener');

  runtime.stage.focused = false;
  command.click();
  assert.equal(runtime.panes.tab, 'commands', 'Command center routes to Commands');
  assert.equal(runtime.drawCount(), 1, 'Command center redraws the requested tab');
  assert.equal(runtime.legacy.hidden, false, 'Command center also reveals the workspace');
  assert.equal(runtime.stage.focused, true, 'Command center leaves focus in the workspace');
}

function hiddenStageCommandIsExposed() {
  const runtime = makeRuntime(true, { hiddenStage: true });
  runtime.context.AtlasExhibition.mount('membrane');
  const root = runtime.body.children[0];
  const command = root.querySelector('[data-open-command]');
  const open = root.querySelector('[data-open-atlas]');
  const back = root.querySelector('[data-return-concept]');

  command.click();
  assert.equal(runtime.stage.classList.contains('atlas-command-surface'), true,
    'Command center exposes a stage parked off screen by the concept');
  assert.equal(runtime.stage.getAttribute('aria-hidden'), null,
    'the visible command surface is available to assistive technology');

  back.click();
  assert.equal(runtime.stage.classList.contains('atlas-command-surface'), false,
    'Return restores the concept original stage');
  assert.equal(runtime.stage.getAttribute('aria-hidden'), 'true',
    'Return restores the concept original accessibility state');

  open.click();
  assert.equal(runtime.stage.classList.contains('atlas-command-surface'), true,
    'Open full Atlas respects the currently selected Commands tab');
}

function missingRuntimeIsVisible() {
  const runtime = makeRuntime(false);
  const result = runtime.context.AtlasExhibition.workspace({ skin: 'test' });
  assert.ok(result, 'workspace returns a visible failure surface');
  assert.equal(result.id, 'main-content');
  assert.match(result.textContent, /Full Atlas could not start/);
  assert.match(result.textContent, /atlas-core\.js, atlas-panes\.js/);
  assert.equal(runtime.body.children.includes(result), true, 'failure surface is attached to the page');
}

const scenes = [
  'declassified', 'spatial', 'boresight', 'vitrine', 'tube',
  'poster', 'membrane', 'panes', 'plate', 'riso',
  'stage', 'machined', 'depth', 'reactor', 'atrium',
  'mycelium', 'broadsheet', 'switchboard', 'bathysphere', 'prism'
];
scenes.forEach(revealAndReturn);
hiddenStageCommandIsExposed();
missingRuntimeIsVisible();
console.log(`exhibition reveal runtime: OK (${scenes.length} scenes)`);
