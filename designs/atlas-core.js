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

  /* Suggested from the user agent, then confirmed by the reader. See
     suggestPlatform below for why it is a labelled suggestion rather than
     either a silent guess or a blocking question. */
  const PLATFORMS = [
    { id: 'windows', label: 'Windows', shell: 'PowerShell',
      note: 'Commands are PowerShell. Use the WSL option instead if you work inside Ubuntu.' },
    { id: 'wsl', label: 'Ubuntu / WSL', shell: 'bash',
      note: 'WSL has its own home directory and its own client config, separate from Windows.' },
    { id: 'macos', label: 'macOS', shell: 'zsh',
      note: 'Apple silicon shares memory between CPU and GPU, so usable model size sits below the headline RAM.' },
    { id: 'linux', label: 'Linux', shell: 'bash',
      note: 'Commands assume a Debian-family distribution; adjust the package manager if yours differs.' },
    { id: 'other', label: 'Other', shell: 'bash',
      note: 'Portable setup requires Bash, Git and Python 3. Platform-specific packages still require review.' },
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
    selectedLane: null,
    basket: load('atlas.basket', []),
    platform: load('atlas.platform', null),
    // Plain by default: the reader who needs it is the one least likely
    // to go looking for a setting.
    reading: load('atlas.reading', 'plain'),
    hw: load('atlas.hw', { ram: null, vram: null, storage: null, cpu: null }),
    customLanes: load('atlas.customLanes', []),
    suggestions: load('atlas.suggestions', []),
    profileClient: load('atlas.profileClient', 'all'),
    surfaceIds: load('atlas.surfaceIds', null),
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

  /* ------------------------------------------------------- reading level

     Charles asked that every design work for a non-technical reader, a beginner
     engineer and an experienced one. Writing one sentence for all three serves
     none of them: an experienced reader needs "a compound index answers its own
     leading prefix", a first-time visitor needs "a shortcut that makes searching
     fast, like a book's index".

     So everything explained carries two registers and the reader picks. Plain is
     the default, because the person who needs it is the person least likely to
     go looking for a setting. The choice persists, so an engineer sets it once.

     This is not a simplified copy of the interface. Same data, same commands,
     same 35 designs. Only the sentences change. */

  function readingLevel() {
    return state.reading === 'technical' ? 'technical' : 'plain';
  }

  function setReadingLevel(level) {
    state.reading = level === 'technical' ? 'technical' : 'plain';
    save('atlas.reading', state.reading);
    emit();
    return state.reading;
  }

  /** A phrase in the reader's register, falling back to the other rather than
      to nothing: a missing plain string must never render as an empty box. */
  function say(entry, fallback) {
    if (!entry) return fallback || '';
    if (typeof entry === 'string') return entry;
    const level = readingLevel();
    return entry[level] || entry.plain || entry.technical || fallback || '';
  }

  function plainData() {
    return (state.data && state.data.plain) || {};
  }

  function familyText(id) {
    const family = (state.data.families || []).find(f => f.id === id);
    if (!family) return '';
    return say({ plain: family.plain, technical: family.technical });
  }

  function kindText(id) {
    return say((plainData().kinds || {})[id]);
  }

  function tabText(id) {
    const entry = (plainData().tabs || {})[id];
    if (entry) return say(entry);
    const tab = TABS.find(t => t.id === id);
    return tab ? tab.hint : '';
  }

  function orientationText() {
    return say(plainData().orientation);
  }

  function glossary() {
    return (plainData().glossary || []).map(entry => ({
      term: entry.term,
      text: say(entry),
    }));
  }

  /* -------------------------------------------------------- platform api */

  function setPlatform(id) {
    state.platform = PLATFORMS.some(p => p.id === id) ? id : null;
    save('atlas.platform', state.platform);
    emit();
    return platform();
  }

  /* Suggested from the user agent, never silently adopted.
     The original rule was that nothing is sniffed, and the reason was sound: a
     wrong guess hands somebody a command for the wrong shell, and WSL cannot be
     seen from a user agent at all. The cost was that every command on the page
     read "Choose OS first" until you found the picker, so the command directory
     of all thirty designs was empty on arrival, which is the opposite of a
     reference.
     So the guess is made, used, and LABELLED. effectivePlatform is what commands
     render with; state.platform stays null until a person actually picks, so
     platformIsSuggested stays true and the interface keeps saying so. WSL is
     never suggested, because it is exactly the case a user agent gets wrong. */
  function suggestPlatform() {
    const ua = (navigator.userAgent || '').toLowerCase();
    if (ua.indexOf('mac') > -1) return 'macos';
    if (ua.indexOf('win') > -1) return 'windows';
    if (ua.indexOf('linux') > -1 || ua.indexOf('x11') > -1) return 'linux';
    return 'other';
  }

  function effectivePlatform() {
    return state.platform || suggestPlatform();
  }

  function platformIsSuggested() {
    return !state.platform;
  }

  function platform() {
    return PLATFORMS.find(p => p.id === effectivePlatform()) || null;
  }

  /** The platform a person explicitly chose, or null. Callers that must not act
      on a guess, such as anything that writes, ask for this one. */
  function chosenPlatform() {
    return PLATFORMS.find(p => p.id === state.platform) || null;
  }

  function scanCommand() {
    const id = effectivePlatform();
    return SCAN[id] || SCAN.other;
  }

  function commandFor(component) {
    if (!component || !component.cmd) return null;
    return component.cmd[effectivePlatform()] || null;
  }

  function setupRecipeFor(component) {
    if (!component || !component.setupRecipe || !state.data) return null;
    return (state.data.setupRecipes || []).find(recipe => recipe.id === component.setupRecipe) || null;
  }

  /** Setup is stricter than an ordinary action: exact shell, reviewed recipe,
      and no unresolved placeholders. A URL or clone-only catalog record never
      becomes setup-ready by accident. */
  /* The platform is a parameter, not a read of global state, so the Build tab can
     render a script for every system at once. A combination you assemble on
     Windows is worth handing to someone on WSL or a Mac unchanged. */
  function setupCommandFor(component, platformId = effectivePlatform()) {
    if (!component || !platformId) return null;
    const recipe = setupRecipeFor(component);
    if (!recipe || recipe.kind !== 'setup' || recipe.state !== 'ready') return null;
    const command = recipe.commands && recipe.commands[platformId];
    if (typeof command !== 'string' || !command.trim()) return null;
    if (/REVIEWED_VERSION|<[^>]+>/.test(command)) return null;
    const executable = command.split(/\r?\n/).some(line => {
      const text = line.trim();
      return text && !text.startsWith('#');
    });
    return executable ? command.trim() : null;
  }

  function setupStateFor(component) {
    if (setupCommandFor(component)) return { id: 'ready', label: 'Setup ready' };
    if (component && component.setupState === 'review-required') {
      return { id: 'review-required', label: 'Setup recipe needs security review' };
    }
    /* A hosted model has nothing to install, so "no recipe yet" would be wrong:
       it reads as work outstanding when there is none to do. */
    if (component && component.setupState === 'hosted') {
      return { id: 'hosted', label: 'Hosted, sign in rather than install' };
    }
    return { id: 'unavailable', label: 'No complete setup recipe yet' };
  }

  function canBuild(component) { return Boolean(setupCommandFor(component)); }

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

  /** What a sub-category means, in the author's words.

      The text comes from the parenthetical or colon clause on the list's own
      '# ---' header, so it is written once beside the entries it describes and
      cannot drift from them. A sub-category appearing in several lanes can carry
      a different description in each; the descriptions are joined rather than
      one silently winning. */
  function subDescription(id) {
    if (!state.data) return '';
    // Not a section anyone wrote: it is where entries land when their list has
    // no '# ---' headers, or when they sit above the first one. Saying so is a
    // fact about the data rather than an invented editorial line.
    if (id === 'Catalog') {
      return 'entries from lists with no section headers, plus any entry sitting above the first header';
    }
    const seen = [];
    (state.data.lanes || []).forEach(lane => {
      (lane.subcategoryInfo || []).forEach(info => {
        if (info.name === id && info.description && !seen.includes(info.description)) {
          seen.push(info.description);
        }
      });
    });
    return seen.join(' | ');
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
      .map(([id, count]) => ({ id, count, description: subDescription(id) }))
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
      family: lane ? lane.family : '',
      sub: component.sub || '',
      detail: component.detail || 'No description recorded.',
      lane: lane ? lane.name : component.lane,
      laneId: component.lane,
      laneSource: lane ? lane.source : '',
      laneDescription: lane ? lane.description : '',
      command: commandFor(component),
      allCommands: component.cmd || null,
      setupCommand: setupCommandFor(component),
      setupRecipe: setupRecipeFor(component),
      setupState: setupStateFor(component),
      sourceUrl: component.sourceUrl || '',
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

  function select(componentId) { state.selected = componentId; state.selectedLane = null; emit(); }

  function selectLane(id) {
    if (!state.lanesById.has(id)) return;
    state.selected = null;
    state.selectedLane = id;
    emit();
  }

  function laneDetailFor(id) {
    const lane = state.lanesById.get(id);
    if (!lane) return null;
    return { ...lane, components: state.components.filter(c => c.lane === id) };
  }

  /* ----------------------------------------------------- build basket */

  /* The plus button. Pick several components and get one script that sets all of
     them up in order, written for the chosen platform. */

  function addToBasket(id) {
    const component = state.byId.get(id);
    if (!component || !canBuild(component) || state.basket.includes(id)) return false;
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
  /** The script for one platform. Pass an id to build for a system you are not on. */
  function combinedCommandFor(platformId) {
    const chosen = PLATFORMS.find(p => p.id === platformId);
    if (!chosen) return { ok: false, text: 'Choose your operating system first.' };
    const items = basketItems();
    if (!items.length) return { ok: false, text: 'Nothing added yet. Use + on a component.' };

    const blocked = [];
    const ready = [];
    const commands = [];
    const seenRecipes = new Set();
    items.forEach(item => {
      const command = setupCommandFor(item, platformId);
      if (!command) {
        const reason = setupRecipeFor(item)
          ? `no ${chosen.label} command in its recipe`
          : setupStateFor(item).label;
        blocked.push(`${item.name} (${laneName(item.lane)}): ${reason}`);
        return;
      }
      ready.push(item);
      const recipe = setupRecipeFor(item);
      const key = recipe ? recipe.id : command;
      if (seenRecipes.has(key)) return;   // one recipe shared by several entries
      seenRecipes.add(key);
      commands.push(command);
    });

    if (!ready.length) {
      return {
        ok: false, platform: chosen,
        text: `No component in this selection has a reviewed setup recipe for ${chosen.label}.`,
        count: items.length, ready, runnable: ready, blocked, skipped: blocked,
      };
    }
    /* text is commands only, deliberately. It is meant to be pasted into a shell,
       and a banner of comment lines is noise at the point of paste. The platform,
       the counts and the skipped list are returned as fields so the interface can
       show them around the block instead of inside it. */
    return {
      ok: true, platform: chosen,
      text: commands.join('\n'),
      count: items.length, commandCount: commands.length,
      ready, runnable: ready, blocked, skipped: blocked,
    };
  }

  /** Backwards-compatible: the script for whatever platform is selected. */
  function combinedCommand() {
    return combinedCommandFor(effectivePlatform());
  }

  /** Every platform at once, so the Build tab can show them all.
      Ordered with the selected system first, since that is the one being run now. */
  function combinedCommandAll() {
    const ids = PLATFORMS.map(p => p.id);
    const current = effectivePlatform();
    if (ids.indexOf(current) > -1) {
      ids.splice(ids.indexOf(current), 1);
      ids.unshift(current);
    }
    return ids.map(id => ({ ...combinedCommandFor(id), id, current: id === current }));
  }


  /* ------------------------------------------------- easy setup profiles */

  /* A profile is an ordered list of reviewed recipes and nothing more. It can
     install nothing the Build tab could not already install one node at a time;
     what it removes is having to know which nodes, and in what order.

     Two steps are tokens rather than fixed ids, because the right answer depends
     on choices made elsewhere on the page: which client the rules go to, and how
     much memory this machine actually has. An unresolved token is dropped and
     named in the notes. It never becomes a command with a placeholder left in. */

  function setProfileClient(id) {
    state.profileClient = id;
    state.surfaceIds = null;
    save('atlas.surfaceIds', null);
    save('atlas.profileClient', id);
    emit();
  }

  function recipeById(id) {
    if (!state.data) return null;
    return (state.data.setupRecipes || []).find(r => r.id === id) || null;
  }

  /** Model recipes are named for their tag, so a tier's tag list resolves directly. */
  function recipeForTag(tag) {
    if (!state.data) return null;
    return (state.data.setupRecipes || []).find(
      r => r.name === tag && r.id.indexOf('setup-model-') === 0) || null;
  }

  function modelRecipesForTier() {
    const tier = currentTier();
    if (!tier || !tier.models || !tier.models.length) return [];
    return tier.models.map(recipeForTag).filter(Boolean);
  }

  function allModelRecipes() {
    if (!state.data) return [];
    return (state.data.setupRecipes || []).filter(
      r => r.id.indexOf('setup-model-') === 0 && r.id !== 'setup-model-list-installed');
  }

  function availableSurfaces() {
    const ram = Number(state.hw.ram) || 0;
    return ((state.data && state.data.surfaces) || []).filter(s =>
      s.group !== 'local-model' || (ram > 0 && ram >= s.minRamGb));
  }

  function selectedSurfaces() {
    if (!Array.isArray(state.surfaceIds)) return [];
    return availableSurfaces().filter(s => state.surfaceIds.includes(s.id));
  }

  function toggleSurface(id) {
    if (!availableSurfaces().some(s => s.id === id)) return;
    if (!Array.isArray(state.surfaceIds)) state.surfaceIds = [];
    state.surfaceIds = state.surfaceIds.includes(id)
      ? state.surfaceIds.filter(value => value !== id) : [...state.surfaceIds, id];
    save('atlas.surfaceIds', state.surfaceIds);
    emit();
  }

  function autoModeText() {
    return (state.data && state.data.autoMode && state.data.autoMode.text) || '';
  }

  /** Steps to recipes, with every failure to resolve recorded rather than hidden. */
  function resolveProfile(profile) {
    const recipes = [];
    const notes = [];
    const push = recipe => {
      if (recipe && !recipes.some(r => r.id === recipe.id)) recipes.push(recipe);
    };
    const multi = Array.isArray(state.surfaceIds);
    const selected = selectedSurfaces();
    const clients = selected.filter(s => s.group === 'local-client');
    const models = selected.filter(s => s.group === 'local-model');
    if (multi && !clients.length && !models.length) {
      notes.push(selected.length ? 'Web-only selection: use the saved-instruction steps below. No local install is required.'
        : 'Select at least one client or compatible local model. No installs are selected by default.');
      return { recipes, notes };
    }
    (profile.steps || []).forEach(step => {
      if (step === 'rules:{client}') {
        if (multi) {
          clients.forEach(s => push(recipeById(s.setupRecipe)));
          if (models.length) push(recipeById('setup-local-model-harness'));
          return;
        }
        const client = state.profileClient || 'all';
        const id = client === 'all' ? 'setup-rules-all-clients' : `setup-rules-${client}`;
        const recipe = recipeById(id);
        if (recipe) push(recipe);
        else notes.push(`No rules recipe for the client "${client}".`);
        return;
      }
      if (step === 'model:{tier}' || step === 'model:{tier2}') {
        if (multi) { models.forEach(s => push(recipeById(s.setupRecipe))); return; }
        const tiered = modelRecipesForTier();
        if (!tiered.length) {
          notes.push('No model chosen: enter the RAM of this machine in step 3, and the '
                     + 'tier decides which tag fits.');
          return;
        }
        const wanted = step === 'model:{tier2}' ? tiered[1] : tiered[0];
        if (wanted) push(wanted);
        else if (step === 'model:{tier2}') {
          notes.push('This tier lists only one model tag, so the second model step is empty.');
        }
        return;
      }
      if (step === 'ALL_MODEL_TAGS') {
        const all = multi ? models.map(s => recipeById(s.setupRecipe)).filter(Boolean)
          : availableSurfaces().filter(s => s.group === 'local-model').map(s => recipeById(s.setupRecipe)).filter(Boolean);
        if (!all.length) notes.push('No model recipes are present in this data file.');
        all.forEach(push);
        return;
      }
      if (step === 'setup-rules-guards' && multi) return; // selected installers already include their own hooks
      if (step === 'setup-ollama-runtime' && multi && !models.length) return;
      if (step === 'setup-model-list-installed' && multi && !models.length) return;
      const recipe = recipeById(step);
      if (recipe) push(recipe);
      else notes.push(`Step "${step}" names a recipe that is not in this data file.`);
    });
    return { recipes, notes };
  }

  /** Same contract as combinedCommandFor: commands only in text, reasons in fields. */
  function profileScriptFor(profileId, platformId = state.platform) {
    const profile = ((state.data && state.data.profiles) || []).find(p => p.id === profileId);
    if (!profile) return { ok: false, text: 'Unknown profile.', notes: [], blocked: [] };
    const chosen = PLATFORMS.find(p => p.id === platformId);
    if (!chosen) {
      return { ok: false, profile, text: 'Choose your operating system first.',
               notes: [], blocked: [] };
    }
    const { recipes, notes } = resolveProfile(profile);
    const commands = [];
    const blocked = [];
    /* Several owner recipes begin by cloning or refreshing the repository. Each
       has to, because Build may run any one of them on its own. In a profile they
       run back to back, and three identical clones in a row reads as a bug even
       though it is harmless. The preamble is a recorded field rather than a
       matched prefix, so this drops the repeat without guessing at strings. */
    const seenPreambles = new Set();
    recipes.forEach(recipe => {
      const command = recipe.commands && recipe.commands[platformId];
      if (typeof command !== 'string' || !command.trim()
          || /REVIEWED_VERSION|<[^>]+>/.test(command)) {
        blocked.push(`${recipe.name}: no ${chosen.label} command in its recipe`);
        return;
      }
      const preamble = recipe.preambles && recipe.preambles[platformId];
      const body = recipe.bodies && recipe.bodies[platformId];
      if (preamble && body && seenPreambles.has(preamble)) {
        commands.push(body.trim());
        return;
      }
      if (preamble) seenPreambles.add(preamble);
      commands.push(command.trim());
    });
    if (!commands.length) {
      return { ok: false, profile, platform: chosen, notes, blocked, steps: recipes,
               text: `Nothing in this profile has a ${chosen.label} command yet.` };
    }
    return { ok: true, profile, platform: chosen, notes, blocked, steps: recipes,
             commandCount: commands.length, text: commands.join('\n') };
  }

  /** The five harnesses, in the order they were built, which is also the order
      from least to most reach. */
  function harnesses() {
    return (state.data && state.data.harnesses) || [];
  }

  /** The standing pipeline: the layers, their rules, the lanes and the commands.

      Parsed by the builder straight out of scripts/hooks/skill_pipeline.py, so
      what the page shows is the text the hook injects rather than a description
      of it. A page that restated the rules said ten while the hook injected
      eleven, which is the whole reason this is read rather than written. */
  function pipeline() {
    return (state.data && state.data.pipeline) || null;
  }

  /** How the goal is set. Captured with nothing typed; the spellings override. */
  function goalPolicy() {
    const p = pipeline();
    return (p && p.goal) || null;
  }

  /** The super harness chain: the extra named passes on top of the three layers.
      Read from the payload, which the builder read from harness_super.py. */
  function superChain() {
    const p = pipeline();
    return (p && p.superChain) || null;
  }

  function profiles() { return (state.data && state.data.profiles) || []; }
  function profileClients() { return (state.data && state.data.profileClients) || []; }

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
    { id: 'index', label: 'Index', hint: 'Searchable directory. Click a lane to learn what it is and browse its entries.' },
    { id: 'commands', label: 'Commands', hint: 'Setup, actions and reference commands, separated by purpose.' },
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
    { id: 'harness', label: 'Harness', hint: 'The three layers on every prompt, the five harnesses that deliver them, and every command that runs one.' },
    { id: 'routes', label: 'Hybrid routes', hint: 'How work is split across models.' },
    { id: 'hardware', label: 'Hardware', hint: 'What this machine can actually host.' },
    { id: 'easy', label: 'Easy setup', hint: 'Choose multiple chat, coding and local-model surfaces, then configure automatic skills.' },
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
    readingLevel, setReadingLevel, say, familyText, kindText, tabText,
    orientationText, glossary,
    setPlatform, platform, scanCommand, commandFor,
    effectivePlatform, platformIsSuggested, suggestPlatform, chosenPlatform,
    setupRecipeFor, setupCommandFor, setupStateFor, canBuild,
    setHardware, usableMemory, tierFor, currentTier, routesForMachine,
    profiles, profileClients, setProfileClient, resolveProfile, profileScriptFor,
    availableSurfaces, selectedSurfaces, toggleSurface, autoModeText,
    harnesses, pipeline, goalPolicy, superChain,
    visibleLanes, visibleComponents, subcategories, subDescription, lanesForTab,
    toggleFamily, toggleKind, toggleSub, setQuery, clearFilters, activeFilterCount,
    detailFor, select, laneName, selectLane, laneDetailFor,
    addToBasket, removeFromBasket, clearBasket, basketItems,
    combinedCommand, combinedCommandFor, combinedCommandAll,
    addCustomLane, removeCustomLane, addSuggestion, exportSuggestions,
  };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = AtlasCore;

/* Published on window as well as the script-scope binding.
   A top level `const` in a classic script is script-scoped, not a property
   of window, so `window.AtlasCore` was undefined while the bare `AtlasCore`
   worked. atlas-exhibition.js reads these through window, so its guard
   `if (!A || !P) return;` fired on every call and workspace() built nothing.
   That is why d31 rendered a root map with no atlas behind it, and why the
   Command center button on the other exhibition designs revealed the atlas
   without ever switching the tab. */
if (typeof window !== 'undefined') window.AtlasCore = AtlasCore;
