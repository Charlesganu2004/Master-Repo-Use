/*
 * Thirteen further Atlas view layers. They deliberately share AtlasCore and
 * AtlasPanes, so every alternative remains an offline, usable product instead
 * of a static concept rendering. The shell, map grammar, navigation placement,
 * and density change per option; the data and actions do not.
 */
'use strict';

const AtlasNext = (() => {
  const A = AtlasCore;
  const P = AtlasPanes;
  const esc = P.esc;
  const MAX_PER_GROUP = 16;

  const COLORS = {
    instruction: 'var(--instruction)', capability: 'var(--capability)',
    knowledge: 'var(--knowledge)', control: 'var(--control)',
    model: 'var(--model)', delivery: 'var(--delivery)',
  };

  const LABELS = {
    transit: {
      title: 'Roadmap Transit', eyebrow: 'Option 1 of 13',
      copy: 'Trace a line, stop at a station, and combine complete setup recipes for your computer.',
      map: 'Line map', note: 'Each family becomes a colored route. Every card is a live station.',
    },
    compiler: {
      title: 'Atlas Compiler', eyebrow: 'Option 2 of 13',
      copy: 'A desktop-workspace route through the system, with files instead of generic cards.',
      map: 'Open roadmap.ts', note: 'Select any source line to inspect it or stage it for Build.',
    },
    cascade: {
      title: 'The Atlas Journal', eyebrow: 'Option 3 of 13',
      copy: 'A large-type learning journal that turns the roadmap into readable chapters.',
      map: 'Journey entries', note: 'Chapters follow the data families. Use filters to narrow the story.',
    },
    command: {
      title: 'Atlas Command', eyebrow: 'Option 4 of 13',
      copy: 'A focused operations wall for comparing active capabilities and execution paths.',
      map: 'Tactical roadmap', note: 'Cells show the live catalog. Inspect a cell for commands and links.',
    },
    deck: {
      title: 'Atlas Index', eyebrow: 'Option 5 of 13',
      copy: 'A physical-card planning surface: collect components, then turn the stack into a build.',
      map: 'Study cards', note: 'The card wall is filterable. Select a card for its practical details.',
    },
    tree: {
      title: 'Skill Tree Atlas', eyebrow: 'Option 6 of 13',
      copy: 'A game-like unlock map that makes prerequisite areas feel like a progression path.',
      map: 'Unlock paths', note: 'Every illuminated node opens the same live inspector and Build action.',
    },
    river: {
      title: 'Atlas River', eyebrow: 'Option 7 of 13',
      copy: 'A flow-first roadmap where related capabilities travel downstream in broad channels.',
      map: 'Live flow', note: 'Channels are generated from the current selection, so filters reshape the flow.',
    },
    city: {
      title: 'Atlas City', eyebrow: 'Option 8 of 13',
      copy: 'A city-map concept: each capability is a district you can enter, inspect, and construct.',
      map: 'District map', note: 'Neighborhood blocks change with the active filters; no fake data is used.',
    },
    patch: {
      title: 'Atlas Patchbay', eyebrow: 'Option 9 of 13',
      copy: 'A modular-synth surface for assembling a local development system from real modules.',
      map: 'Signal rack', note: 'Click a module to inspect it, then patch it into Build with the plus control.',
    },
    campaign: {
      title: 'Atlas Campaign', eyebrow: 'Option 10 of 13',
      copy: 'An accessible board-game journey that turns a large roadmap into one clear next move.',
      map: 'Quest board', note: 'Each waypoint is the real component data. Your Build basket is the pack list.',
    },
    forge: {
      title: 'Stack Forge', eyebrow: 'Option 11 of 13',
      copy: 'A production line from interface structure to reusable skills, with every setup decision visible.',
      map: 'Implementation line', note: 'Read left to right: HTML, JavaScript, TypeScript, JSX, TSX, Repos, then Skills.',
    },
    cinema: {
      title: 'Code Cinema', eyebrow: 'Option 12 of 13',
      copy: 'A storyboard roadmap with large readable scenes, clear sequence, and no hidden interaction.',
      map: 'Roadmap storyboard', note: 'Each family is a scene. Frames hold the live components, setup state, and Build action.',
    },
    bridge: {
      title: 'Repo Bridge', eyebrow: 'Option 13 of 13',
      copy: 'A three-zone system map showing how reviewed sources become runtime capabilities and reusable skills.',
      map: 'Source to skill bridge', note: 'Repos stay visibly separate from runtime pieces and skills, so setup readiness is easy to judge.',
    },
  };

  const TECH_STACK = ['HTML', 'JavaScript', 'TypeScript', 'JSX', 'TSX', 'Repos', 'Skills'];

  function techRibbon(label) {
    return `<div class="tech-ribbon" aria-label="${esc(label)}">${TECH_STACK.map((item, index) =>
      `<span><i>${String(index + 1).padStart(2, '0')}</i>${esc(item)}</span>`).join('')}</div>`;
  }

  function styleFor(component) {
    return `style="--lane-color:${COLORS[component.kind] || 'var(--accent)'}"`;
  }

  function groups() {
    const visible = A.visibleComponents();
    const byFamily = new Map();
    visible.forEach(component => {
      const key = component.family || 'other';
      if (!byFamily.has(key)) byFamily.set(key, []);
      byFamily.get(key).push(component);
    });
    return A.state.data.families
      .filter(family => byFamily.has(family.id))
      .map(family => ({ family, items: byFamily.get(family.id) }));
  }

  function itemMeta(component) {
    return `${esc(A.laneName(component.lane))}${component.sub ? ` / ${esc(component.sub)}` : ''}`;
  }

  function plus(component) {
    const inBasket = A.state.basket.includes(component.id);
    if (!A.canBuild(component)) {
      const state = A.setupStateFor(component);
      const short = state.id === 'review-required' ? 'review first'
        : state.id === 'choose-platform' ? 'choose OS' : 'no recipe';
      return `<span class="plan-tag" title="${esc(state.label)}">${esc(short)}</span>`;
    }
    return `<button class="plus mini${inBasket ? ' in' : ''}" data-add="${esc(component.id)}"
      aria-label="${inBasket ? 'Remove' : 'Add'} ${esc(component.name)} ${inBasket ? 'from' : 'to'} Build"
      title="${inBasket ? 'Remove from Build' : 'Add to Build'}"
      >${inBasket ? '&#10003;' : '+'}</button>`;
  }

  function selectButton(component) {
    return `<button class="map-select" data-select aria-label="View details for ${esc(component.name)}"></button>`;
  }

  function emptyMap() {
    return '<p class="empty">Nothing matches the current filters. Clear a filter or search for another term.</p>';
  }

  function limit(items) {
    return items.slice(0, MAX_PER_GROUP);
  }

  function renderTransit(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="transit-map">${rows.map(({ family, items }) => {
      const shown = limit(items);
      return `<section class="metro-lane" ${styleFor(shown[0] || { kind: 'instruction' })}>
        <div class="metro-lane-head"><h2 class="metro-line-name">${esc(family.name)}</h2>
          <span class="metro-count">${items.length} stop${items.length === 1 ? '' : 's'}${items.length > shown.length ? ` / showing ${shown.length}` : ''}</span></div>
        <div class="metro-stations">${shown.map(component => `<article class="metro-station${A.state.selected === component.id ? ' on' : ''}"
            data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
            ${selectButton(component)}${plus(component)}<span class="metro-station-name">${esc(component.name)}</span>
            <small>${esc(component.detail)}</small><span class="station-meta">${itemMeta(component)}</span>
          </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.metro-station');
  }

  function renderCompiler(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="compiler-map">${rows.map(({ family, items }) => {
      const shown = limit(items);
      const filename = `${family.id || family.name.toLowerCase().replace(/\W+/g, '-')}.roadmap`;
      return `<section class="source-file" ${styleFor(shown[0] || { kind: 'instruction' })}>
        <div class="source-file-head"><b>${esc(filename)}</b><small>${items.length} symbol${items.length === 1 ? '' : 's'}</small></div>
        <div class="source-lines">${shown.map(component => `<article class="source-line${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}${esc(component.name)}<small>// ${esc(component.detail)}</small>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.source-line');
  }

  function renderCascade(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="cascade-map">${rows.map(({ family, items }) => {
      const shown = limit(items);
      return `<section class="journal-family" ${styleFor(shown[0] || { kind: 'instruction' })}>
        <div class="journal-family-head"><h2>${esc(family.name)}</h2><span>${items.length} field note${items.length === 1 ? '' : 's'}</span></div>
        <div class="journal-entries">${shown.map(component => `<article class="journal-entry${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}<b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.journal-entry');
  }

  function renderCommand(stage) {
    const components = A.visibleComponents().slice(0, 88);
    stage.innerHTML = components.length ? `<div class="command-map">${components.map(component => `<article
      class="mission-cell${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
      ${selectButton(component)}${plus(component)}<span class="mission-kind">${esc(component.kind)}</span><b>${esc(component.name)}</b>
      <p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
    </article>`).join('')}</div>` : emptyMap();
    wireMap(stage, '.mission-cell');
  }

  function renderDeck(stage) {
    const components = A.visibleComponents().slice(0, 90);
    stage.innerHTML = components.length ? `<div class="deck-map">${components.map((component, index) => `<article
      class="study-card${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
      ${selectButton(component)}${plus(component)}<span class="deck-index">${String(index + 1).padStart(2, '0')} / ${esc(component.kind)}</span>
      <b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
    </article>`).join('')}</div>` : emptyMap();
    wireMap(stage, '.study-card');
  }

  function renderTree(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="tree-map">${rows.map(({ family, items }, familyIndex) => {
      const shown = limit(items);
      return `<section class="tree-branch" ${styleFor(shown[0] || { kind: 'instruction' })}>
        <div class="tree-root"><span>${String(familyIndex + 1).padStart(2, '0')}</span><h2>${esc(family.name)}</h2><small>${items.length} unlock${items.length === 1 ? '' : 's'}</small></div>
        <div class="tree-nodes">${shown.map((component, index) => `<article class="tree-node${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" style="--tree-step:${index % 4};--lane-color:${COLORS[component.kind] || 'var(--accent)'}">
          ${selectButton(component)}${plus(component)}<span class="tree-level">LVL ${String(index + 1).padStart(2, '0')}</span><b>${esc(component.name)}</b><small>${itemMeta(component)}</small>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.tree-node');
  }

  function renderRiver(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="river-map">${rows.map(({ family, items }, familyIndex) => {
      const shown = limit(items);
      return `<section class="river-channel" ${styleFor(shown[0] || { kind: 'instruction' })}>
        <header><span class="river-mile">${String(familyIndex + 1).padStart(2, '0')}</span><h2>${esc(family.name)}</h2><small>${items.length} current entries</small></header>
        <div class="river-stones">${shown.map(component => `<article class="river-stone${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}<b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.river-stone');
  }

  function renderCity(stage) {
    const components = A.visibleComponents().slice(0, 72);
    stage.innerHTML = components.length ? `<div class="city-map">${components.map((component, index) => {
      const span = index % 11 === 0 ? 2 : index % 7 === 0 ? 2 : 1;
      return `<article class="city-block${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}"
        style="--district-span:${span};--lane-color:${COLORS[component.kind] || 'var(--accent)'}">
        ${selectButton(component)}${plus(component)}<span class="district-zone">${esc(component.kind)}</span><b>${esc(component.name)}</b><small>${itemMeta(component)}</small>
      </article>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.city-block');
  }

  function renderPatch(stage) {
    const visible = A.visibleComponents();
    const kinds = ['instruction', 'capability', 'knowledge', 'control', 'model', 'delivery'];
    const rows = kinds.map(kind => ({ kind, items: visible.filter(component => component.kind === kind) })).filter(row => row.items.length);
    stage.innerHTML = rows.length ? `<div class="patch-map">${rows.map(({ kind, items }) => {
      const shown = limit(items);
      return `<section class="patch-rack" style="--lane-color:${COLORS[kind]}"><header><span class="rack-socket"></span><h2>${esc(kind)}</h2><small>${items.length} module${items.length === 1 ? '' : 's'}</small></header>
        <div class="patch-modules">${shown.map(component => `<article class="patch-module${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}<span class="module-port">IN</span><b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small><span class="module-port out">OUT</span>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.patch-module');
  }

  function renderCampaign(stage) {
    const components = A.visibleComponents().slice(0, 78);
    stage.innerHTML = components.length ? `<div class="campaign-map"><div class="campaign-path">${components.map((component, index) => `<article
      class="quest-stop${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
      ${selectButton(component)}${plus(component)}<span class="quest-number">${String(index + 1).padStart(2, '0')}</span><b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
    </article>`).join('')}</div></div>` : emptyMap();
    wireMap(stage, '.quest-stop');
  }

  const STACK_PHASES = [
    { id: 'html', label: 'HTML', note: 'structure and delivery' },
    { id: 'javascript', label: 'JavaScript', note: 'behavior and tools' },
    { id: 'typescript', label: 'TypeScript', note: 'contracts and controls' },
    { id: 'jsx', label: 'JSX', note: 'surfaces and plugins' },
    { id: 'tsx', label: 'TSX', note: 'models and systems' },
    { id: 'repos', label: 'Repos', note: 'reviewed source boundary' },
    { id: 'skills', label: 'Skills', note: 'reusable behavior' },
  ];

  function stackPhase(component) {
    if (component.slug) return 'repos';
    if (component.family === 'skills' || component.kind === 'instruction') return 'skills';
    if (component.family === 'surfaces' || component.family === 'plugins') return 'jsx';
    if (component.kind === 'model') return 'tsx';
    if (component.kind === 'control') return 'typescript';
    if (component.kind === 'delivery') return 'html';
    return 'javascript';
  }

  function renderForge(stage) {
    const visible = A.visibleComponents();
    const columns = STACK_PHASES.map(phase => ({
      ...phase,
      items: visible.filter(component => stackPhase(component) === phase.id),
    }));
    stage.innerHTML = visible.length ? `<div class="forge-map">${columns.map((phase, phaseIndex) => {
      const shown = phase.items.slice(0, 12);
      return `<section class="forge-phase" style="--phase-index:${phaseIndex}">
        <header><span>${String(phaseIndex + 1).padStart(2, '0')}</span><h2>${esc(phase.label)}</h2>
          <p>${esc(phase.note)}</p><small>${phase.items.length}${phase.items.length > shown.length ? ` / showing ${shown.length}` : ''}</small></header>
        <div class="forge-units">${shown.map((component, index) => `<article
          class="forge-unit${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}"
          style="--unit:${index};--lane-color:${COLORS[component.kind] || 'var(--accent)'}">
          ${selectButton(component)}${plus(component)}<span class="forge-code">${esc(phase.label.slice(0, 3).toUpperCase())}.${String(index + 1).padStart(2, '0')}</span>
          <b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
        </article>`).join('') || '<p class="empty">No matches in this layer.</p>'}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.forge-unit');
  }

  function renderCinema(stage) {
    const rows = groups();
    stage.innerHTML = rows.length ? `<div class="cinema-reel">${rows.map(({ family, items }, sceneIndex) => {
      const shown = items.slice(0, 7);
      return `<section class="cinema-scene" style="--scene:${sceneIndex}">
        <header><span class="scene-number">SCENE ${String(sceneIndex + 1).padStart(2, '0')}</span>
          <h2>${esc(family.name)}</h2><p>${items.length} live frame${items.length === 1 ? '' : 's'}${items.length > shown.length ? ` / showing ${shown.length}` : ''}</p></header>
        <div class="cinema-frames">${shown.map((component, frameIndex) => `<article
          class="cinema-frame${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}<span class="frame-time">${String(sceneIndex + 1).padStart(2, '0')}:${String(frameIndex + 1).padStart(2, '0')}</span>
          <b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
        </article>`).join('')}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.cinema-frame');
  }

  function renderBridge(stage) {
    const visible = A.visibleComponents();
    const source = visible.filter(component => component.slug);
    const skill = visible.filter(component => !component.slug && (component.family === 'skills' || component.kind === 'instruction'));
    const runtime = visible.filter(component => !source.includes(component) && !skill.includes(component));
    const zones = [
      { id: 'source', label: '01 / Repos', note: 'Source stays reference-only until reviewed.', items: source },
      { id: 'runtime', label: '02 / Runtime', note: 'Local components and execution surfaces.', items: runtime },
      { id: 'skill', label: '03 / Skills', note: 'Reusable behavior ready for the system.', items: skill },
    ];
    stage.innerHTML = visible.length ? `<div class="bridge-map">${zones.map(zone => {
      const shown = zone.items.slice(0, 24);
      return `<section class="bridge-zone bridge-${zone.id}"><header><h2>${esc(zone.label)}</h2><p>${esc(zone.note)}</p><small>${zone.items.length}${zone.items.length > shown.length ? ` / showing ${shown.length}` : ''}</small></header>
        <div class="bridge-nodes">${shown.map((component, index) => `<article
          class="bridge-node${A.state.selected === component.id ? ' on' : ''}" data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
          ${selectButton(component)}${plus(component)}<span class="bridge-index">${String(index + 1).padStart(2, '0')}</span>
          <b>${esc(component.name)}</b><p>${esc(component.detail)}</p><small>${itemMeta(component)}</small>
        </article>`).join('') || '<p class="empty">No matches in this zone.</p>'}</div>
      </section>`;
    }).join('')}</div>` : emptyMap();
    wireMap(stage, '.bridge-node');
  }

  const MAPS = { transit: renderTransit, compiler: renderCompiler, cascade: renderCascade, command: renderCommand, deck: renderDeck,
    tree: renderTree, river: renderRiver, city: renderCity, patch: renderPatch, campaign: renderCampaign,
    forge: renderForge, cinema: renderCinema, bridge: renderBridge };

  function wireMap(stage, selector) {
    stage.querySelectorAll(selector).forEach(node => {
      const select = event => {
        if (event.target.closest('[data-add]')) return;
        A.select(node.dataset.comp);
        P.popover(event.clientX, event.clientY, node.dataset.comp);
        stage.querySelectorAll(`${selector}.on`).forEach(active => active.classList.remove('on'));
        node.classList.add('on');
      };
      node.addEventListener('click', select);
    });
    stage.querySelectorAll('[data-add]').forEach(button => {
      button.addEventListener('click', event => {
        event.stopPropagation();
        const id = button.dataset.add;
        if (A.state.basket.includes(id)) A.removeFromBasket(id);
        else A.addToBasket(id);
        P.draw();
        updateLiveStatus();
      });
    });
  }

  function shellTransit(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="transit-shell">
        <nav class="transit-stops" id="tabs" role="tablist" aria-label="Atlas destinations"></nav>
        <main class="transit-main" id="main-content">
          <header class="transit-heading"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><span class="status-chip"><i class="status-dot"></i>data live</span></header>
          <section class="system-ticket" aria-labelledby="system-title"><p class="eyebrow" id="system-title">Your system ticket</p><div id="setup"></div></section>
          <section class="transit-controls" aria-label="Roadmap controls"><div id="themehost"></div><div id="filters"></div></section>
          <section aria-labelledby="roadmap-title"><p class="eyebrow" id="roadmap-title">${copy.map}</p><p class="brand-copy">${copy.note}</p><div id="stage" tabindex="-1"></div></section>
        </main>
        <aside id="side" aria-label="Component inspector"></aside>
      </div>`;
  }

  function shellCompiler(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="compiler-shell">
        <nav class="activity" id="tabs" role="tablist" aria-label="Atlas workspace"></nav>
        <aside class="file-tree"><div class="tree-head"><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="tree-caption">EXPLORER / FILTERS</p></div><div id="filters"></div></aside>
        <main class="compiler-main" id="main-content"><header class="editor-top"><div><p class="editor-tab">${copy.map}</p><p class="brand-copy">${copy.copy}</p></div><span class="count-chip"><b data-basket-count>0</b> staged</span></header><section class="compiler-system" aria-label="System scan"><div id="setup"></div></section><section class="compiler-meta"><span class="status-chip"><i class="status-dot"></i>offline ready</span><div id="themehost"></div></section><div id="stage" tabindex="-1"></div></main>
        <aside id="side" aria-label="Component inspector"></aside>
      </div>`;
  }

  function shellCascade(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="cascade-shell">
        <nav class="cascade-spine" role="tablist" aria-label="Journal sections"><div class="spine-cover"><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1></div><div id="tabs"></div></nav>
        <main class="cascade-paper" id="main-content"><header class="journal-masthead"><p class="eyebrow">Interactive learning roadmap</p><h1>${copy.map}</h1><p class="brand-copy">${copy.copy}</p></header><section class="journal-controls"><span class="status-chip"><i class="status-dot"></i>chapter data loaded</span><div id="themehost"></div></section><section class="journal-system"><div id="setup"></div></section><section class="journal-filter"><div id="filters"></div></section><div id="stage" tabindex="-1"></div></main>
        <aside id="side" aria-label="Component inspector"></aside>
      </div>`;
  }

  function shellCommand(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="command-shell"><header class="command-top"><div class="command-brand"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1></div></div><div class="status-chip"><i class="status-dot"></i>local data / no transfer</div></header><nav class="command-tabs" id="tabs" role="tablist" aria-label="Command views"></nav>
        <div class="command-grid"><aside class="command-left"><div class="metric-stack"><div class="metric"><b data-visible-count>0</b><span>visible components</span></div><div class="metric"><b data-basket-count>0</b><span>Build selections</span></div></div><div id="filters"></div></aside><main class="command-center" id="main-content"><section class="command-system"><div id="setup"></div></section><div class="command-hud"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><div id="themehost"></div></div><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellDeck(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="deck-shell"><header class="deck-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="deck-header-right"><span class="count-chip"><b data-basket-count>0</b> in Build</span><div id="themehost"></div></div></header><nav class="deck-tabs" id="tabs" role="tablist" aria-label="Atlas cards"></nav>
        <div class="deck-body"><main class="deck-board" id="main-content"><section class="deck-system"><div id="setup"></div></section><section class="deck-filter"><div id="filters"></div></section><div class="deck-hud"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="status-chip"><i class="status-dot"></i>click a card</span></div><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellTree(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="tree-shell"><header class="tree-top"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="tree-top-actions"><span class="count-chip"><b data-basket-count>0</b> loadout pieces</span><div id="themehost"></div></div></header>
        <div class="tree-tabs"><nav id="tabs" role="tablist" aria-label="Skill tree sections"></nav></div>
        <div class="tree-layout"><aside class="tree-loadout"><p class="eyebrow">Gear check</p><p class="brand-copy">Choose a system before building your loadout.</p><div id="setup"></div><div class="tree-filter"><p class="eyebrow">Unlock filters</p><div id="filters"></div></div></aside><main class="tree-board" id="main-content"><header class="tree-board-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="status-chip"><i class="status-dot"></i>progress saved locally</span></header><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellRiver(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="river-shell"><header class="river-top"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1></div><p class="brand-copy">${copy.copy}</p><div id="themehost"></div></header>
        <div class="river-work"><nav class="river-nav" id="tabs" role="tablist" aria-label="River views"></nav><main class="river-main" id="main-content"><section class="river-scan"><p class="eyebrow">Source conditions</p><div id="setup"></div></section><section class="river-filter"><p class="eyebrow">Channel filters</p><div id="filters"></div></section><header class="river-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-visible-count>0</b> currents</span></header><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellCity(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="city-shell"><header class="city-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="city-header-actions"><span class="status-chip"><i class="status-dot"></i>city data open</span><div id="themehost"></div></div></header><nav class="city-streets" id="tabs" role="tablist" aria-label="City atlas views"></nav>
        <div class="city-layout"><aside class="city-utility"><section><p class="eyebrow">Power grid scan</p><div id="setup"></div></section><section class="city-filters"><p class="eyebrow">District filters</p><div id="filters"></div></section></aside><main class="city-center" id="main-content"><header class="city-map-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-basket-count>0</b> constructions</span></header><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellPatch(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="patch-shell"><header class="patch-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="patch-leds"><span></span><span></span><span></span><span></span><strong>LOCAL SIGNAL</strong></div></header><nav class="patch-nav" id="tabs" role="tablist" aria-label="Patchbay views"></nav>
        <div class="patch-layout"><aside class="patch-calibration"><p class="eyebrow">Calibration</p><div id="setup"></div><div id="themehost"></div></aside><main class="patch-main" id="main-content"><section class="patch-filters"><p class="eyebrow">Module filters</p><div id="filters"></div></section><header class="patch-rack-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-basket-count>0</b> patched</span></header><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellCampaign(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="campaign-shell"><header class="campaign-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="campaign-score"><span class="status-dot"></span><b data-visible-count>0</b><small>available moves</small></div></header><nav class="campaign-nav" id="tabs" role="tablist" aria-label="Campaign views"></nav>
        <div class="campaign-layout"><aside class="campaign-gear"><p class="eyebrow">Gear check</p><div id="setup"></div><div class="campaign-theme"><div id="themehost"></div></div><div class="campaign-filter"><p class="eyebrow">Quest filters</p><div id="filters"></div></div></aside><main class="campaign-board" id="main-content"><header class="campaign-board-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-basket-count>0</b> in pack</span></header><div id="stage" tabindex="-1"></div></main><aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellForge(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="forge-shell">
        <header class="forge-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="forge-readout"><b data-basket-count>0</b><span>setup recipes staged</span><div id="themehost"></div></div></header>
        ${techRibbon('Implementation stack from HTML through Skills')}
        <nav class="forge-tabs" id="tabs" role="tablist" aria-label="Stack Forge views"></nav>
        <div class="forge-layout"><aside class="forge-controls"><section><p class="eyebrow">01 · computer profile</p><div id="setup"></div></section><section class="forge-filter"><p class="eyebrow">02 · line controls</p><div id="filters"></div></section></aside>
          <main class="forge-main" id="main-content"><header class="forge-stage-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="status-chip"><i class="status-dot"></i><b data-visible-count>0</b> live parts</span></header><div id="stage" tabindex="-1"></div></main>
          <aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellCinema(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="cinema-shell">
        <header class="cinema-marquee"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="cinema-status"><span>NOW SHOWING</span><b data-visible-count>0</b><small>roadmap frames</small><div id="themehost"></div></div></header>
        ${techRibbon('Production credits: HTML, JavaScript, TypeScript, JSX, TSX, repositories, and skills')}
        <div class="cinema-layout"><aside class="cinema-director"><nav id="tabs" role="tablist" aria-label="Code Cinema views"></nav><section><p class="eyebrow">System check</p><div id="setup"></div></section><section class="cinema-filter"><p class="eyebrow">Edit the reel</p><div id="filters"></div></section></aside>
          <main class="cinema-main" id="main-content"><header class="cinema-stage-head"><div><p class="eyebrow">${copy.map}</p><h2>Scan. Choose. Build.</h2><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-basket-count>0</b> in final cut</span></header><div id="stage" tabindex="-1"></div></main>
          <aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  function shellBridge(copy) {
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="bridge-shell">
        <header class="bridge-header"><div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div><div class="bridge-meter"><span class="status-chip"><i class="status-dot"></i>local graph ready</span><div id="themehost"></div></div></header>
        ${techRibbon('Source formats and implementation layers')}
        <nav class="bridge-tabs" id="tabs" role="tablist" aria-label="Repo Bridge views"></nav>
        <section class="bridge-setup" aria-label="System scan"><div><p class="eyebrow">Scan before crossing</p><p class="brand-copy">Choose the computer target so Build emits the correct reviewed setup commands.</p></div><div id="setup"></div></section>
        <div class="bridge-layout"><main class="bridge-main" id="main-content"><header class="bridge-stage-head"><div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div><span class="count-chip"><b data-basket-count>0</b> ready to cross</span></header><section class="bridge-filter"><div id="filters"></div></section><div id="stage" tabindex="-1"></div></main>
          <aside id="side" aria-label="Component inspector"></aside></div>
      </div>`;
  }

  const SHELLS = { transit: shellTransit, compiler: shellCompiler, cascade: shellCascade, command: shellCommand, deck: shellDeck,
    tree: shellTree, river: shellRiver, city: shellCity, patch: shellPatch, campaign: shellCampaign,
    forge: shellForge, cinema: shellCinema, bridge: shellBridge };

  function updateLiveStatus() {
    const counts = A.counts();
    document.querySelectorAll('[data-basket-count]').forEach(node => { node.textContent = counts.basket; });
    document.querySelectorAll('[data-visible-count]').forEach(node => { node.textContent = counts.visibleComponents; });
  }

  function keyboardTabs() {
    const tabHost = document.getElementById('tabs');
    if (!tabHost) return;
    tabHost.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
      const tabs = [...tabHost.querySelectorAll('.tab')];
      if (!tabs.length) return;
      const current = tabs.indexOf(document.activeElement);
      if (current < 0) return;
      event.preventDefault();
      let next = current;
      if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else next = (current + (event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : -1) + tabs.length) % tabs.length;
      tabs[next].focus();
      tabs[next].click();
    });
  }

  function boot(option) {
    const copy = LABELS[option];
    if (!copy || !SHELLS[option] || !MAPS[option]) throw new Error(`Unknown Atlas option: ${option}`);
    document.body.className = `atlas-next next-${option}`;
    document.body.innerHTML = SHELLS[option](copy);
    document.documentElement.lang = 'en';
    AtlasTheme.mount(document.getElementById('themehost'), 'ember');
    keyboardTabs();

    P.mount({
      renderMap: MAPS[option],
      onFilter: () => {
        if (P.tab === 'map') MAPS[option](document.getElementById('stage'));
        updateLiveStatus();
      },
      onSelect: () => updateLiveStatus(),
    });
    A.on(updateLiveStatus);
    updateLiveStatus();
  }

  return { boot };
})();
