/* Shared engine for every atlas design.
 *
 * Each design supplies its own visualization and styling. Everything that must
 * behave identically across designs lives here: data loading, platform choice,
 * hardware, lane and sub-category filtering, the component detail, the build
 * basket, custom lanes and suggestions.
 *
 * Designs differ in how they LOOK and how you MOVE through them. They must not
 * differ in what the data means.
 */
'use strict';

const AtlasCore = (() => {

  /* ------------------------------------------------------------ platform */

  /* Chosen explicitly rather than sniffed. A guess from the user agent is wrong
     often enough that it would hand someone a command for the wrong shell, and
     WSL in particular is invisible to the user agent. */
  const PLATFORMS = [
    { id: 'windows', label: 'Windows', shell: 'PowerShell',
      note: 'Commands are PowerShell. Use the WSL option instead if you work inside Ubuntu.' },
    { id: 'wsl', label: 'Ubuntu / WSL', shell: 'bash',
      note: 'WSL has its own home directory and its own client config, separate from Windows.' },
    { id: 'macos', label: 'macOS', shell: 'zsh',
      note: 'Apple silicon shares memory between CPU and GPU, so usable model size sits below the headline RAM.' },
    { id: 'linux', label: 'Linux', shell: 'bash',
      note: 'Commands assume a Debian-family distribution; adjust the package manager if yours differs.' },
    { id: 'other', label: 'Other', shell: 'POSIX sh',
      note: 'Falling back to POSIX commands. Anything platform-specific is marked as such rather than guessed.' },
  ];

  /* Scan commands. Each reports the four numbers that actually decide what a
     machine can host: memory, video memory, free disk, and core count. */
  const SCAN = {
    windows: 'powershell -c "$c=Get-CimInstance Win32_ComputerSystem; $o=Get-CimInstance Win32_OperatingSystem; $g=Get-CimInstance Win32_VideoController; $d=Get-PSDrive C; Write-Host (\'RAM {0:N0} GB | VRAM {1:N0} GB | free disk {2:N0} GB | {3} cores | {4}\' -f ($c.TotalPhysicalMemory/1GB), (($g.AdapterRAM | Measure-Object -Maximum).Maximum/1GB), ($d.Free/1GB), $c.NumberOfLogicalProcessors, $o.Caption)"',
    wsl: "echo \"RAM $(free -g | awk 'NR==2{print $2}') GB | free disk $(df -BG --output=avail / | tail -1 | tr -dc 0-9) GB | $(nproc) cores | $(. /etc/os-release && echo $PRETTY_NAME)\"; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo 'no NVIDIA GPU visible from WSL'",
    linux: "echo \"RAM $(free -g | awk 'NR==2{print $2}') GB | free disk $(df -BG --output=avail / | tail -1 | tr -dc 0-9) GB | $(nproc) cores | $(. /etc/os-release && echo $PRETTY_NAME)\"; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo 'no NVIDIA GPU'",
    macos: "echo \"RAM $(($(sysctl -n hw.memsize)/1073741824)) GB unified | free disk $(df -g / | tail -1 | awk '{print $4}') GB | $(sysctl -n hw.ncpu) cores | $(sysctl -n machdep.cpu.brand_string) | macOS $(sw_vers -productVersion)\"; echo 'GPU shares the unified pool, so VRAM is not separate'",
    other: "echo \"RAM $(free -g 2>/dev/null | awk 'NR==2{print $2}') GB\"; uname -a; nproc 2>/dev/null || echo 'core count unavailable'",
  };

  /* ---------------------------------------------------------------- data */

  const state = {
    data: null,
    lanes: [],
    components: [],
    byId: new Map(),
    lanesById: new Map(),
    activeFamilies: new Set(),    // empty means all
    activeKinds: new Set(),
    activeSubs: new Set(),
    query: '',
    selected: null,
    basket: load('atlas.basket', []),
    platform: load('atlas.platform', null),
    hw: load('atlas.hw', { ram: null, vram: null, storage: null, cpu: null }),
    customLanes: load('atlas.customLanes', []),
    suggestions: load('atlas.suggestions', []),
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

  async function init(url = 'atlas-data.json') {
    // Embedded first. atlas-data.js is a <script src> tag, which works over
    // file:// where fetch is blocked outright, so a design opens by double-click.
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

  /* -------------------------------------------------------- platform api */

  function setPlatform(id) {
    state.platform = PLATFORMS.some(p => p.id === id) ? id : null;
    save('atlas.platform', state.platform);
    emit();
    return platform();
  }

  function platform() {
    return PLATFORMS.find(p => p.id === state.platform) || null;
  }

  /** Null until a platform is chosen, so callers can prompt rather than guess. */
  function scanCommand() {
    return state.platform ? (SCAN[state.platform] || SCAN.other) : null;
  }

  function commandFor(component) {
    if (!component || !component.cmd) return null;
    if (!state.platform) return null;
    return component.cmd[state.platform] || component.cmd.linux || component.cmd.wsl || null;
  }

  /* -------------------------------------------------------- hardware api */

  const HW_FIELDS = [
    { id: 'ram', label: 'RAM', unit: 'GB',
      hint: 'Models are held in memory. This is the binding constraint, not disk.' },
    { id: 'vram', label: 'VRAM', unit: 'GB',
      hint: 'Dedicated video memory. On Apple silicon leave this blank: memory is unified and already counted in RAM.' },
    { id: 'storage', label: 'Free disk', unit: 'GB',
      hint: 'Weights are large. A 7B model at 4-bit is roughly 4 to 5 GB on disk.' },
    { id: 'cpu', label: 'CPU cores', unit: '',
      hint: 'Matters for CPU-only inference speed, not for whether a model fits.' },
  ];

  function setHardware(field, value) {
    const number = Number(value);
    state.hw[field] = Number.isFinite(number) && number > 0 ? number : null;
    save('atlas.hw', state.hw);
    emit();
    return state.hw;
  }

  /** The memory a local model can actually draw on, given the platform. */
  function usableMemory() {
    const { ram, vram } = state.hw;
    if (state.platform === 'macos') return ram;   // unified: VRAM is the same pool
    if (vram && ram) return Math.max(ram, vram);  // discrete GPU: whichever path is larger
    return ram || vram || null;
  }

  function tierFor(gb) {
    const tiers = state.data.hardware;
    if (!gb || gb < 8) return tiers.find(h => h.id === '4gb');
    if (gb < 16) return tiers.find(h => h.id === '8gb');
    if (gb < 32) return tiers.find(h => h.id === '16gb');
    return tiers.find(h => h.id === '32gb');
  }

  function currentTier() {
    const gb = usableMemory();
    return gb ? tierFor(gb) : null;
  }

  /** Routes this machine can run. Says "scan first" rather than guessing. */
  function routesForMachine() {
    const gb = usableMemory();
    return state.data.routes.map(route => {
      const needs = /(\d+)\s*GB/i.exec(route.requires || '');
      const min = needs ? Number(needs[1]) : 0;
      const hostedOnly = /hosted only/i.test(route.requires || '');
      let verdict = 'runs here';
      if (hostedOnly) verdict = 'hosted only';
      else if (gb && min && gb < min) verdict = `needs ${min} GB, you have ${gb}`;
      else if (!gb && min) verdict = `needs ${min} GB, scan first`;
      return { ...route, verdict, ok: verdict === 'runs here' || verdict === 'hosted only' };
    });
  }

  /* ------------------------------------------------------- filtering */

  /** Filters compose. Family, kind, sub-category and text all narrow together. */
  function visibleLanes() {
    return state.lanes.filter(lane => {
      const familyOk = !state.activeFamilies.size || state.activeFamilies.has(lane.family);
      const kindOk = !state.activeKinds.size || state.activeKinds.has(lane.kind);
      return familyOk && kindOk;
    });
  }

  function visibleComponents() {
    const laneIds = new Set(visibleLanes().map(l => l.id));
    const needle = state.query.trim().toLowerCase();
    return state.components.filter(c => {
      if (!laneIds.has(c.lane)) return false;
      if (state.activeSubs.size && !state.activeSubs.has(c.sub || 'Catalog')) return false;
      if (!needle) return true;
      return c.name.toLowerCase().includes(needle)
        || (c.owner || '').toLowerCase().includes(needle)
        || (c.detail || '').toLowerCase().includes(needle)
        || laneName(c.lane).toLowerCase().includes(needle);
    });
  }

  /** Sub-categories present in whatever is currently visible by family and kind. */
  function subcategories() {
    const laneIds = new Set(visibleLanes().map(l => l.id));
    const counts = new Map();
    state.components.forEach(c => {
      if (!laneIds.has(c.lane)) return;
      const key = c.sub || 'Catalog';
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    return [...counts.entries()]
      .map(([id, count]) => ({ id, count }))
      .sort((a, b) => b.count - a.count || a.id.localeCompare(b.id));
  }

  const toggle = (set, id) => { set.has(id) ? set.delete(id) : set.add(id); emit(); };
  const toggleFamily = id => toggle(state.activeFamilies, id);
  const toggleKind = id => toggle(state.activeKinds, id);
  const toggleSub = id => toggle(state.activeSubs, id);

  function setQuery(text) { state.query = text || ''; emit(); }

  function clearFilters() {
    state.activeFamilies.clear();
    state.activeKinds.clear();
    state.activeSubs.clear();
    state.query = '';
    emit();
  }

  function activeFilterCount() {
    return state.activeFamilies.size + state.activeKinds.size + state.activeSubs.size
      + (state.query.trim() ? 1 : 0);
  }

  /* ------------------------------------------------- component detail */

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
      owner: component.owner || '',
      kind: component.kind,
      sub: component.sub || '',
      detail: component.detail || 'No description recorded.',
      lane: lane ? lane.name : component.lane,
      laneId: component.lane,
      laneSource: lane ? lane.source : '',
      laneDescription: lane ? lane.description : '',
      command: commandFor(component),
      allCommands: component.cmd || null,
      routes,
      connections,
      inBasket: state.basket.includes(component.id),
      siblings: state.components.filter(c => c.lane === component.lane && c.id !== component.id).length,
    };
  }

  function laneName(id) {
    const lane = state.lanesById.get(id);
    return lane ? lane.name : id;
  }

  function select(componentId) { state.selected = componentId; emit(); }

  /* ----------------------------------------------------- build basket */

  /* The plus button. Pick several components and get one script that sets all of
     them up in order, written for the chosen platform. */

  function addToBasket(id) {
    if (!state.byId.has(id) || state.basket.includes(id)) return false;
    state.basket.push(id);
    save('atlas.basket', state.basket);
    emit();
    return true;
  }

  function removeFromBasket(id) {
    state.basket = state.basket.filter(x => x !== id);
    save('atlas.basket', state.basket);
    emit();
  }

  function clearBasket() {
    state.basket = [];
    save('atlas.basket', state.basket);
    emit();
  }

  function basketItems() {
    return state.basket.map(id => state.byId.get(id)).filter(Boolean);
  }

  /** One script for everything in the basket, in the order it was added. */
  function combinedCommand() {
    const chosen = platform();
    if (!chosen) return { ok: false, text: 'Choose your operating system first.' };
    const items = basketItems();
    if (!items.length) return { ok: false, text: 'Nothing added yet. Use + on a component.' };

    const comment = chosen.id === 'windows' ? '#' : '#';
    const lines = [
      `${comment} Master Repo Atlas combination`,
      `${comment} ${items.length} component(s), written for ${chosen.label} (${chosen.shell})`,
      '',
    ];
    const skipped = [];
    items.forEach(item => {
      const cmd = commandFor(item);
      const lane = laneName(item.lane);
      if (!cmd) { skipped.push(`${item.name} (${lane})`); return; }
      lines.push(`${comment} ${item.name} - ${lane}`);
      lines.push(cmd);
      lines.push('');
    });
    if (skipped.length) {
      lines.push(`${comment} No command recorded for: ${skipped.join(', ')}.`);
      lines.push(`${comment} These are parts of the system rather than things you install.`);
    }
    return { ok: true, text: lines.join('\n').trim(), count: items.length, skipped };
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
    const entry = { name: name.trim(), why: (why || '').trim(), link: (link || '').trim() };
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

  /* ------------------------------------------------------------ tabs */

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
    { id: 'basket', label: 'Build', hint: 'Components you combined, and the script for them.' },
    { id: 'custom', label: 'Custom lanes', hint: 'Lanes you add yourself.' },
    { id: 'suggest', label: 'Suggest', hint: 'Propose a lane or a feed.' },
  ];

  function lanesForTab(tabId) {
    const tab = TABS.find(t => t.id === tabId);
    if (!tab || !tab.match) return visibleLanes();
    return state.lanes.filter(tab.match);
  }

  /* -------------------------------------------------------- events */

  const listeners = new Set();
  function on(fn) { listeners.add(fn); return () => listeners.delete(fn); }
  function emit() { listeners.forEach(fn => { try { fn(state); } catch (e) { console.error(e); } }); }

  function counts() {
    return {
      lanes: state.lanes.length,
      components: state.components.length,
      routes: state.data ? state.data.routes.length : 0,
      families: state.data ? state.data.families.length : 0,
      subs: subcategories().length,
      visibleLanes: visibleLanes().length,
      visibleComponents: visibleComponents().length,
      basket: state.basket.length,
      filters: activeFilterCount(),
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
    state, init, on, emit, counts, copy,
    PLATFORMS, HW_FIELDS, TABS,
    setPlatform, platform, scanCommand, commandFor,
    setHardware, usableMemory, tierFor, currentTier, routesForMachine,
    visibleLanes, visibleComponents, subcategories, lanesForTab,
    toggleFamily, toggleKind, toggleSub, setQuery, clearFilters, activeFilterCount,
    detailFor, select, laneName,
    addToBasket, removeFromBasket, clearBasket, basketItems, combinedCommand,
    addCustomLane, removeCustomLane, addSuggestion, exportSuggestions,
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = AtlasCore;
