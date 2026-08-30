/* Shared engine for every atlas design.
 *
 * Each design supplies its own visualization and styling. Everything that must
 * behave identically across designs lives here: data loading, lane mixing, the
 * component detail panel, the capability tabs, the hardware advisor, custom
 * lanes and suggestions.
 *
 * Designs differ in how they LOOK and how you MOVE through them. They must not
 * differ in what the data means.
 */
'use strict';

const AtlasCore = (() => {

  /* ---------------------------------------------------------------- data */

  const state = {
    data: null,
    lanes: [],
    components: [],
    byId: new Map(),
    lanesById: new Map(),
    activeFamilies: new Set(),   // empty means all
    activeKinds: new Set(),
    selected: null,
    platform: detectPlatform(),
    customLanes: load('atlas.customLanes', []),
    suggestions: load('atlas.suggestions', []),
    ram: load('atlas.ram', null),
  };

  function load(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_) {
      return fallback;   // private windows and blocked storage must not break the page
    }
  }

  function save(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* non-fatal */ }
  }

  function detectPlatform() {
    const ua = (navigator.userAgent || '').toLowerCase();
    if (ua.includes('mac')) return 'macos';
    if (ua.includes('linux') && !ua.includes('android')) return 'linux';
    return 'windows';
  }

  async function init(url = 'atlas-data.json') {
    // Embedded first. atlas-data.js is a <script src> tag, which works over
    // file:// where fetch is blocked outright, so the page opens by double-click.
    if (typeof window !== 'undefined' && window.__ATLAS_DATA__) {
      state.data = window.__ATLAS_DATA__;
    } else {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`could not load ${url}: ${response.status}`);
      state.data = await response.json();
    }
    state.lanes = state.data.lanes.concat(state.customLanes);
    state.components = state.data.components;
    state.components.forEach(c => state.byId.set(c.id, c));
    state.lanes.forEach(l => state.lanesById.set(l.id, l));
    return state.data;
  }

  /* ------------------------------------------------------- lane filtering */

  /** Lanes are intermixable: family and kind filters compose rather than replace. */
  function visibleLanes() {
    return state.lanes.filter(lane => {
      const familyOk = !state.activeFamilies.size || state.activeFamilies.has(lane.family);
      const kindOk = !state.activeKinds.size || state.activeKinds.has(lane.kind);
      return familyOk && kindOk;
    });
  }

  function visibleComponents() {
    const laneIds = new Set(visibleLanes().map(l => l.id));
    return state.components.filter(c => laneIds.has(c.lane));
  }

  function toggleFamily(id) {
    state.activeFamilies.has(id) ? state.activeFamilies.delete(id) : state.activeFamilies.add(id);
    emit();
  }

  function toggleKind(id) {
    state.activeKinds.has(id) ? state.activeKinds.delete(id) : state.activeKinds.add(id);
    emit();
  }

  function clearFilters() {
    state.activeFamilies.clear();
    state.activeKinds.clear();
    emit();
  }

  /* ------------------------------------------------- component detail */

  /** Everything a click should reveal: description, lane, connections, command. */
  function detailFor(componentId) {
    const component = state.byId.get(componentId);
    if (!component) return null;
    const lane = state.lanesById.get(component.lane);
    const routes = (component.routes || [])
      .map(id => state.data.routes.find(r => r.id === id))
      .filter(Boolean);
    const connections = (component.connects || [])
      .map(id => state.byId.get(id))
      .filter(Boolean)
      .map(c => ({ id: c.id, name: c.name, lane: laneName(c.lane) }));
    return {
      id: component.id,
      name: component.name,
      kind: component.kind,
      detail: component.detail || 'No description recorded.',
      lane: lane ? lane.name : component.lane,
      laneId: component.lane,
      laneSource: lane ? lane.source : '',
      laneDescription: lane ? lane.description : '',
      command: commandFor(component),
      commands: component.cmd || null,
      routes,
      connections,
      siblings: state.components.filter(c => c.lane === component.lane && c.id !== component.id).length,
    };
  }

  function commandFor(component) {
    if (!component || !component.cmd) return null;
    return component.cmd[state.platform] || component.cmd.linux || null;
  }

  function laneName(id) {
    const lane = state.lanesById.get(id);
    return lane ? lane.name : id;
  }

  function select(componentId) {
    state.selected = componentId;
    emit();
  }

  /* ------------------------------------------------------------ tabs */

  /** Capability tabs. Each reads the same data through a different lens. */
  const TABS = [
    { id: 'map', label: 'Map', hint: 'The whole system as lanes and connections.' },
    { id: 'agents', label: 'Agents', hint: 'Agent contracts and the jobs that act on them.',
      match: l => l.family === 'agents' || /agent/i.test(l.name) },
    { id: 'skills', label: 'Skills', hint: 'Instruction packs loaded on demand.',
      match: l => l.family === 'skills' },
    { id: 'tools', label: 'Tools', hint: 'Scripts and binaries you run directly.',
      match: l => l.family === 'tools' },
    { id: 'plugins', label: 'Plugins', hint: 'Marketplace and installed plugin state.',
      match: l => l.family === 'plugins' },
    { id: 'mcp', label: 'MCP', hint: 'Model Context Protocol servers and connectors.',
      match: l => l.family === 'mcp' },
    { id: 'routes', label: 'Hybrid routes', hint: 'How work is split across models.' },
    { id: 'hardware', label: 'Hardware', hint: 'What this machine can actually host.' },
    { id: 'custom', label: 'Custom lanes', hint: 'Lanes you add yourself.' },
    { id: 'suggest', label: 'Suggest', hint: 'Propose a lane or a feed.' },
  ];

  function lanesForTab(tabId) {
    const tab = TABS.find(t => t.id === tabId);
    if (!tab || !tab.match) return visibleLanes();
    return state.lanes.filter(tab.match);
  }

  /* --------------------------------------------------- custom lanes */

  function addCustomLane({ name, family, kind, description }) {
    if (!name || !name.trim()) return { ok: false, error: 'A lane needs a name.' };
    const id = 'custom-' + name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    if (state.lanesById.has(id)) return { ok: false, error: 'A lane with that name already exists.' };
    const lane = {
      id, name: name.trim(),
      family: family || 'domain',
      kind: kind || 'capability',
      source: 'custom (this browser only)',
      description: (description || '').trim() || 'Added locally.',
      count: 0, catalog: false, custom: true,
    };
    state.customLanes.push(lane);
    state.lanes.push(lane);
    state.lanesById.set(id, lane);
    save('atlas.customLanes', state.customLanes);
    emit();
    return { ok: true, lane };
  }

  function removeCustomLane(id) {
    // Only ever removes a lane the viewer added in this browser. Generated lanes
    // come from files and are not deletable from a web page.
    state.customLanes = state.customLanes.filter(l => l.id !== id);
    state.lanes = state.lanes.filter(l => l.id !== id);
    state.lanesById.delete(id);
    save('atlas.customLanes', state.customLanes);
    emit();
  }

  function addSuggestion({ name, why, link }) {
    if (!name || !name.trim()) return { ok: false, error: 'Give the lane or feed a name.' };
    const entry = { name: name.trim(), why: (why || '').trim(), link: (link || '').trim(), at: new Date().toISOString() };
    state.suggestions.push(entry);
    save('atlas.suggestions', state.suggestions);
    emit();
    return { ok: true, entry };
  }

  /** Suggestions stay in the viewer's browser. Nothing is transmitted. */
  function exportSuggestions() {
    return state.suggestions.map(s =>
      `- ${s.name}${s.link ? ` (${s.link})` : ''}${s.why ? ` : ${s.why}` : ''}`).join('\n');
  }

  /* ------------------------------------------------------- hardware */

  const SCAN = {
    windows: 'powershell -c "$m=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB; $o=(Get-CimInstance Win32_OperatingSystem).Caption; $g=(Get-CimInstance Win32_VideoController).Name -join \', \'; Write-Host (\'RAM {0:N0} GB | {1} | GPU {2}\' -f $m,$o,$g)"',
    wsl: "free -g | awk 'NR==2{print \"RAM \"$2\" GB\"}'; . /etc/os-release && echo $PRETTY_NAME; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo 'no NVIDIA GPU'",
    linux: "free -g | awk 'NR==2{print \"RAM \"$2\" GB\"}'; . /etc/os-release && echo $PRETTY_NAME; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo 'no NVIDIA GPU'",
    macos: "echo \"RAM $(($(sysctl -n hw.memsize)/1073741824)) GB\"; sw_vers -productVersion; sysctl -n machdep.cpu.brand_string",
  };

  function scanCommand(platform = state.platform) {
    return SCAN[platform] || SCAN.linux;
  }

  /** Map a RAM figure to the tier that governs what can be hosted locally. */
  function tierFor(gb) {
    if (!gb || gb < 8) return state.data.hardware.find(h => h.id === '4gb');
    if (gb < 16) return state.data.hardware.find(h => h.id === '8gb');
    if (gb < 32) return state.data.hardware.find(h => h.id === '16gb');
    return state.data.hardware.find(h => h.id === '32gb');
  }

  function setRam(gb) {
    const value = Number(gb);
    state.ram = Number.isFinite(value) && value > 0 ? value : null;
    save('atlas.ram', state.ram);
    emit();
    return state.ram ? tierFor(state.ram) : null;
  }

  /** Routes this machine can actually run, given the recorded RAM. */
  function routesForMachine() {
    const gb = state.ram;
    return state.data.routes.map(route => {
      const needs = /(\d+)\s*GB/i.exec(route.requires || '');
      const min = needs ? Number(needs[1]) : 0;
      const hostedOnly = /hosted only/i.test(route.requires || '');
      let verdict = 'runs here';
      if (hostedOnly) verdict = 'hosted only';
      else if (gb && min && gb < min) verdict = `needs ${min} GB`;
      else if (!gb && min) verdict = `needs ${min} GB, scan first`;
      return { ...route, verdict, ok: verdict === 'runs here' || verdict === 'hosted only' };
    });
  }

  /* -------------------------------------------------------- events */

  const listeners = new Set();
  function on(fn) { listeners.add(fn); return () => listeners.delete(fn); }
  function emit() { listeners.forEach(fn => { try { fn(state); } catch (e) { console.error(e); } }); }

  /* ------------------------------------------------------ utilities */

  function counts() {
    return {
      lanes: state.lanes.length,
      components: state.components.length,
      routes: state.data ? state.data.routes.length : 0,
      families: state.data ? state.data.families.length : 0,
      visibleLanes: visibleLanes().length,
      visibleComponents: visibleComponents().length,
    };
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      return false;   // clipboard is blocked in some embeds; callers show the text instead
    }
  }

  return {
    state, init, on, emit,
    visibleLanes, visibleComponents, lanesForTab, TABS,
    toggleFamily, toggleKind, clearFilters,
    detailFor, select, commandFor, laneName,
    addCustomLane, removeCustomLane, addSuggestion, exportSuggestions,
    scanCommand, tierFor, setRam, routesForMachine,
    counts, copy,
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = AtlasCore;
