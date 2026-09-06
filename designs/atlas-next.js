/*
 * Twenty-three further Atlas view layers. They deliberately share AtlasCore and
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
      title: 'Roadmap Transit', eyebrow: 'Option 1 of 23',
      copy: 'Trace a line, stop at a station, and combine complete setup recipes for your computer.',
      map: 'Line map', note: 'Each family becomes a colored route. Every card is a live station.',
    },
    compiler: {
      title: 'Atlas Compiler', eyebrow: 'Option 2 of 23',
      copy: 'A desktop-workspace route through the system, with files instead of generic cards.',
      map: 'Open roadmap.ts', note: 'Select any source line to inspect it or stage it for Build.',
    },
    cascade: {
      title: 'The Atlas Journal', eyebrow: 'Option 3 of 23',
      copy: 'A large-type learning journal that turns the roadmap into readable chapters.',
      map: 'Journey entries', note: 'Chapters follow the data families. Use filters to narrow the story.',
    },
    command: {
      title: 'Atlas Command', eyebrow: 'Option 4 of 23',
      copy: 'A focused operations wall for comparing active capabilities and execution paths.',
      map: 'Tactical roadmap', note: 'Cells show the live catalog. Inspect a cell for commands and links.',
    },
    deck: {
      title: 'Atlas Index', eyebrow: 'Option 5 of 23',
      copy: 'A physical-card planning surface: collect components, then turn the stack into a build.',
      map: 'Study cards', note: 'The card wall is filterable. Select a card for its practical details.',
    },
    tree: {
      title: 'Skill Tree Atlas', eyebrow: 'Option 6 of 23',
      copy: 'A game-like unlock map that makes prerequisite areas feel like a progression path.',
      map: 'Unlock paths', note: 'Every illuminated node opens the same live inspector and Build action.',
    },
    river: {
      title: 'Atlas River', eyebrow: 'Option 7 of 23',
      copy: 'A flow-first roadmap where related capabilities travel downstream in broad channels.',
      map: 'Live flow', note: 'Channels are generated from the current selection, so filters reshape the flow.',
    },
    city: {
      title: 'Atlas City', eyebrow: 'Option 8 of 23',
      copy: 'A city-map concept: each capability is a district you can enter, inspect, and construct.',
      map: 'District map', note: 'Neighborhood blocks change with the active filters; no fake data is used.',
    },
    patch: {
      title: 'Atlas Patchbay', eyebrow: 'Option 9 of 23',
      copy: 'A modular-synth surface for assembling a local development system from real modules.',
      map: 'Signal rack', note: 'Click a module to inspect it, then patch it into Build with the plus control.',
    },
    campaign: {
      title: 'Atlas Campaign', eyebrow: 'Option 10 of 23',
      copy: 'An accessible board-game journey that turns a large roadmap into one clear next move.',
      map: 'Quest board', note: 'Each waypoint is the real component data. Your Build basket is the pack list.',
    },
    forge: {
      title: 'Stack Forge', eyebrow: 'Option 11 of 23',
      copy: 'A production line from interface structure to reusable skills, with every setup decision visible.',
      map: 'Implementation line', note: 'Read left to right: HTML, JavaScript, TypeScript, JSX, TSX, Repos, then Skills.',
    },
    cinema: {
      title: 'Code Cinema', eyebrow: 'Option 12 of 23',
      copy: 'A storyboard roadmap with large readable scenes, clear sequence, and no hidden interaction.',
      map: 'Roadmap storyboard', note: 'Each family is a scene. Frames hold the live components, setup state, and Build action.',
    },
    bridge: {
      title: 'Repo Bridge', eyebrow: 'Option 13 of 23',
      copy: 'A three-zone system map showing how reviewed sources become runtime capabilities and reusable skills.',
      map: 'Source to skill bridge', note: 'Repos stay visibly separate from runtime pieces and skills, so setup readiness is easy to judge.',
    },
    treemap: {
      title: 'Atlas Treemap', eyebrow: 'Option 14 of 23',
      copy: 'The first layer where size means something: a rectangle covers the area its component count earns.',
      map: 'Area map', note: 'Family area is its share of the visible set. Tiles too small for a readable label drop it rather than faking one.',
    },
    matrix: {
      title: 'Atlas Matrix', eyebrow: 'Option 15 of 23',
      copy: 'Lanes against kinds, so the shape of the catalog is a grid you can read instead of something you infer by opening lanes one at a time.',
      map: 'Lane by kind', note: 'Every cell carries its count on two channels, opacity and size, so it survives greyscale. Pick a cell to list what is in it.',
    },
    sunburst: {
      title: 'Atlas Sunburst', eyebrow: 'Option 16 of 23',
      copy: 'Two rings of drawn arcs: families inside, their lanes outside, angle proportional to what each holds.',
      map: 'Proportion wheel', note: 'The wheel answers how big. The list under it stays the working roadmap, so this is still a tool rather than a chart.',
    },
    sankey: {
      title: 'Atlas Flow', eyebrow: 'Option 17 of 23',
      copy: 'Family to kind to setup readiness, as ribbons whose width is the count that takes that path.',
      map: 'Readiness flow', note: 'The one view that answers why Build cannot add something. Only the ready column can be staged.',
    },
    rail: {
      title: 'Atlas Rail', eyebrow: 'Option 18 of 23',
      copy: 'A timeline whose axis is setup order rather than dates: what has to happen before what.',
      map: 'Setup order', note: 'Positioned with grid column spans, so nothing measures anything. What the data does not sequence says so.',
    },
    contact: {
      title: 'Atlas Contact Sheet', eyebrow: 'Option 19 of 23',
      copy: 'The only layer with no per-family cap. Every component that passes your filters gets an identical frame.',
      map: 'Full sheet', note: 'Frames are numbered continuously, stamped with a three letter kind code, and skipped by the browser while offscreen.',
    },
    terrace: {
      title: 'Atlas Terrace', eyebrow: 'Option 20 of 23',
      copy: 'An isometric stack where each family is a floor, so the imbalance between them is physical rather than a number.',
      map: 'Floor stack', note: 'Labels are counter-rotated so they stay flat. The projection is a toggle, because isometric is genuinely unreadable for some people.',
    },
    broadside: {
      title: 'Atlas Broadside', eyebrow: 'Option 21 of 23',
      copy: 'Award-site craft used honestly: viewport-scale type, a seamless marquee, and reveals driven by the scroll timeline.',
      map: 'Editorial spread', note: 'Every effect degrades to a plain readable page, which is the version most people will actually see.',
    },
    ledger: {
      title: 'Atlas Ledger', eyebrow: 'Option 22 of 23',
      copy: 'Fixed character-width columns that align with no measuring code, and kinds carried as letters rather than only as colour.',
      map: 'Command ledger', note: 'The active filters are printed back as the command that would reproduce them. This layer works with colour removed.',
    },
    bundle: {
      title: 'Atlas Bundle', eyebrow: 'Option 23 of 23',
      copy: 'The routes, drawn: lanes around a circle ordered by family, each route an edge pulled toward the centre so related edges bundle.',
      map: 'Route bundle', note: 'Focus a lane and everything it does not touch dims. A ring of real buttons carries the keyboard, because paths cannot.',
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


  /* ------------------------------------------------ analytical layer support

     The thirteen layers above are, underneath, a list of equal-sized cards in
     some arrangement: a lane holding four entries renders the same as one
     holding a hundred and eighty. The ten below encode quantity and relation in
     the geometry itself, which is the thing styling alone could not fix.

     Four of them (matrix, sunburst, sankey, bundle) draw a chart that is not
     made of components: a cell, a wedge, a ribbon. Those keep a focus and list
     the focused group's real components underneath, because the page still has
     to be a roadmap you can click and build from, not only a picture of one. */

  const AN_KINDS = ['instruction', 'capability', 'knowledge', 'control', 'model', 'delivery'];
  const AN_CODES = { instruction: 'INS', capability: 'CAP', knowledge: 'KNW',
    control: 'CTL', model: 'MDL', delivery: 'DEL' };
  const AN_FOCUS = { matrix: null, sunburst: null, sankey: null, bundle: null };

  function anCode(kind) { return AN_CODES[kind] || 'GEN'; }

  /* Readiness, in the four states the data actually distinguishes. This is what
     the Build tab is deciding when it greys a plus control out. */
  function anReadiness(component) {
    if (component.slug) return 'reference';
    if (component.setupState === 'hosted') return 'hosted';
    if (component.setupRecipe) return 'ready';
    return 'unavailable';
  }

  const AN_READY_LABEL = { ready: 'Setup ready', reference: 'Reference, needs review',
    hosted: 'Hosted, sign in', unavailable: 'No recipe yet' };

  function anByLane() {
    const byLane = new Map();
    A.visibleComponents().forEach(component => {
      if (!byLane.has(component.lane)) byLane.set(component.lane, []);
      byLane.get(component.lane).push(component);
    });
    return [...byLane.entries()].map(([lane, items]) => ({ lane: lane, items: items }))
      .sort((a, b) => b.items.length - a.items.length);
  }

  /* The shared detail strip. Every chart layer ends in one of these, so the
     selectable thing is always a real component with a real plus control. */
  function anStrip(items, label, note) {
    const shown = items.slice(0, 48);
    const more = items.length > shown.length ? `, showing ${shown.length}` : '';
    return `<section class="an-strip"><header class="an-strip-head">
        <div><p class="eyebrow">${esc(label)}</p><p class="brand-copy">${esc(note || '')}</p></div>
        <small>${items.length} component${items.length === 1 ? '' : 's'}${more}</small></header>
      <div class="an-strip-items">${shown.map(component => `<article class="an-node${A.state.selected === component.id ? ' on' : ''}"
        data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
        ${selectButton(component)}${plus(component)}<span class="an-code">${esc(anCode(component.kind))}</span>
        <b>${esc(component.name)}</b><small>${itemMeta(component)}</small>
      </article>`).join('')}</div></section>`;
  }

  /* One delegated handler per chart layer, rebound on every render. The chart
     controls are buttons the shell does not own, so they are re-created each
     time and cannot carry a listener across renders. */
  function anWireFocus(stage, key, renderer) {
    stage.querySelectorAll('[data-an-focus]').forEach(node => {
      node.addEventListener('click', () => {
        AN_FOCUS[key] = node.getAttribute('data-an-focus');
        renderer(stage);
      });
    });
  }

  /* --------------------------------------------------------------- treemap */

  function anWorst(areas, sum, side) {
    /* The squarified cost of a row: the worse of its widest and narrowest
       aspect ratios. Bruls, Huizing and van Wijk, section 2. Keeping a row while
       this improves is the whole algorithm. */
    const max = Math.max.apply(null, areas);
    const min = Math.min.apply(null, areas);
    const s2 = side * side;
    const sum2 = sum * sum;
    return Math.max((s2 * max) / sum2, sum2 / (s2 * min));
  }

  function anSquarify(entries, x, y, w, h) {
    /* Returns percentage rectangles. Descending sort first, then lay each row
       along the SHORTER side of what is left: laying along the longer side is
       what produces the slivers that make naive treemaps unreadable. */
    const out = [];
    const total = entries.reduce((sum, entry) => sum + entry.value, 0);
    if (!total || w <= 0 || h <= 0) return out;
    const scale = (w * h) / total;
    const rest = entries.slice().sort((a, b) => b.value - a.value)
      .map(entry => ({ entry: entry, area: entry.value * scale }));
    let cx = x;
    let cy = y;
    let cw = w;
    let ch = h;
    let guard = 0;
    while (rest.length && guard++ < 4096) {
      const wide = cw >= ch;
      const side = wide ? ch : cw;
      if (side <= 0) break;
      const row = [];
      let sum = 0;
      let best = Infinity;
      while (rest.length) {
        const areas = row.map(item => item.area).concat(rest[0].area);
        const next = sum + rest[0].area;
        const worst = anWorst(areas, next, side);
        if (row.length && worst > best) break;
        best = worst;
        sum = next;
        row.push(rest.shift());
      }
      const thickness = sum / side;
      let offset = 0;
      row.forEach(item => {
        const length = item.area / thickness;
        out.push(wide
          ? { entry: item.entry, x: cx, y: cy + offset, w: thickness, h: length }
          : { entry: item.entry, x: cx + offset, y: cy, w: length, h: thickness });
        offset += length;
      });
      if (wide) { cx += thickness; cw -= thickness; } else { cy += thickness; ch -= thickness; }
      if (cw < 0.0001 || ch < 0.0001) break;
    }
    return out;
  }

  function renderTreemap(stage) {
    const rows = groups();
    if (!rows.length) { stage.innerHTML = emptyMap(); return; }
    /* Two levels. The family rectangle's area is its component count, which is
       the comparison none of the card layouts can make. Inside it every
       component takes an equal share, so the second level reads as texture and
       the first as proportion. */
    const outer = anSquarify(rows.map(row => ({ value: row.items.length, row: row })), 0, 0, 100, 100);
    const cells = outer.map(cell => {
      const row = cell.entry.row;
      const inner = anSquarify(row.items.map(component => ({ value: 1, component: component })),
        0, 0, 100, 100);
      /* A label needs room to be honest. Below roughly 9 percent of the tile
         box it is a smear, so the tile drops it and the name stays reachable
         through the button's aria-label instead of being faked at 4px. */
      const tiles = inner.map(tile => {
        const component = tile.entry.component;
        const tiny = tile.w < 9 || tile.h < 9;
        return `<div class="an-tile${tiny ? ' is-tiny' : ''}${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}"
          style="--lane-color:${COLORS[component.kind] || 'var(--accent)'};left:${tile.x.toFixed(3)}%;top:${tile.y.toFixed(3)}%;width:${tile.w.toFixed(3)}%;height:${tile.h.toFixed(3)}%">
          ${selectButton(component)}${plus(component)}<span class="an-tile-name">${esc(component.name)}</span>
        </div>`;
      }).join('');
      return `<section class="an-cell" style="left:${cell.x.toFixed(3)}%;top:${cell.y.toFixed(3)}%;width:${cell.w.toFixed(3)}%;height:${cell.h.toFixed(3)}%">
        <header class="an-cell-head"><b>${esc(row.family.name)}</b><small>${row.items.length}</small></header>
        <div class="an-cell-body">${tiles}</div>
      </section>`;
    }).join('');
    stage.innerHTML = `<div class="treemap-map">${cells}</div>
      <p class="an-legend-note">Rectangle area is the number of components. Tiles too small to
      carry a readable label drop it; the name is still on the button for a screen reader.</p>`;
    wireMap(stage, '.an-tile');
  }

  /* ---------------------------------------------------------------- matrix */

  function renderMatrix(stage) {
    const lanes = anByLane();
    if (!lanes.length) { stage.innerHTML = emptyMap(); return; }
    const SHOWN = 40;
    const rows = lanes.slice(0, SHOWN);
    let peak = 1;
    rows.forEach(row => {
      AN_KINDS.forEach(kind => {
        peak = Math.max(peak, row.items.filter(component => component.kind === kind).length);
      });
    });
    const head = AN_KINDS.map(kind =>
      `<div class="an-mx-col" style="--lane-color:${COLORS[kind]}"><i>${esc(anCode(kind))}</i><span>${esc(kind)}</span></div>`).join('');
    const body = rows.map(row => {
      const cells = AN_KINDS.map(kind => {
        const items = row.items.filter(component => component.kind === kind);
        const share = items.length / peak;
        const focused = AN_FOCUS.matrix === `${row.lane}::${kind}`;
        /* Magnitude on two channels. Opacity alone dies in greyscale and for
           anyone with low contrast vision, so the inset square carries the same
           number as a size. */
        return `<button type="button" class="an-mx-cell${items.length ? '' : ' is-empty'}${focused ? ' on' : ''}"
          data-an-focus="${esc(row.lane)}::${esc(kind)}"
          style="--lane-color:${COLORS[kind]};--an-share:${share.toFixed(3)}"
          aria-label="${esc(A.laneName(row.lane))}, ${esc(kind)}, ${items.length} component${items.length === 1 ? '' : 's'}"
          ><i></i><span>${items.length || ''}</span></button>`;
      }).join('');
      return `<div class="an-mx-row"><div class="an-mx-lane" title="${esc(A.laneName(row.lane))}">${esc(A.laneName(row.lane))}<small>${row.items.length}</small></div>${cells}</div>`;
    }).join('');
    const focus = AN_FOCUS.matrix ? AN_FOCUS.matrix.split('::') : null;
    const focusRow = focus ? lanes.find(row => row.lane === focus[0]) : null;
    const picked = focusRow ? focusRow.items.filter(component => component.kind === focus[1]) : rows[0].items;
    const label = focusRow ? `${A.laneName(focus[0])} / ${focus[1]}` : A.laneName(rows[0].lane);
    stage.innerHTML = `<div class="matrix-map">
        <div class="an-mx-grid">
          <div class="an-mx-row an-mx-head"><div class="an-mx-lane">lane</div>${head}</div>
          ${body}
        </div>
        <p class="an-legend-note">Showing ${rows.length} of ${lanes.length} lanes, densest first.
        Nothing is hidden silently: the rest are reachable by filtering.</p>
        ${anStrip(picked, label, 'The components at the selected intersection.')}
      </div>`;
    anWireFocus(stage, 'matrix', renderMatrix);
    wireMap(stage, '.an-node');
  }

  /* -------------------------------------------------------------- sunburst */

  function anArc(cx, cy, r0, r1, a0, a1) {
    /* One wedge as a single path: around the inner radius, out to the outer,
       back around, close. largeArcFlag has to be computed from the swept angle
       or any wedge over half a turn renders inside out, which is the classic
       way a hand-built sunburst goes wrong. */
    const large = (a1 - a0) > Math.PI ? 1 : 0;
    const x0 = cx + r0 * Math.cos(a0);
    const y0 = cy + r0 * Math.sin(a0);
    const x1 = cx + r0 * Math.cos(a1);
    const y1 = cy + r0 * Math.sin(a1);
    const x2 = cx + r1 * Math.cos(a1);
    const y2 = cy + r1 * Math.sin(a1);
    const x3 = cx + r1 * Math.cos(a0);
    const y3 = cy + r1 * Math.sin(a0);
    return `M${x0.toFixed(2)} ${y0.toFixed(2)}A${r0} ${r0} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
      + `L${x2.toFixed(2)} ${y2.toFixed(2)}A${r1} ${r1} 0 ${large} 0 ${x3.toFixed(2)} ${y3.toFixed(2)}Z`;
  }

  function renderSunburst(stage) {
    const rows = groups();
    if (!rows.length) { stage.innerHTML = emptyMap(); return; }
    const total = rows.reduce((sum, row) => sum + row.items.length, 0);
    const CX = 200;
    const CY = 200;
    let angle = -Math.PI / 2;            // start at twelve o'clock, not three
    const inner = [];
    const outer = [];
    rows.forEach(row => {
      const sweep = (row.items.length / total) * Math.PI * 2;
      const colour = COLORS[(row.items[0] || {}).kind] || 'var(--accent)';
      inner.push({ row: row, path: anArc(CX, CY, 62, 118, angle, angle + sweep), colour: colour });
      const byLane = new Map();
      row.items.forEach(component => {
        if (!byLane.has(component.lane)) byLane.set(component.lane, []);
        byLane.get(component.lane).push(component);
      });
      let sub = angle;
      [...byLane.entries()].sort((a, b) => b[1].length - a[1].length).forEach(pair => {
        const items = pair[1];
        const laneSweep = (items.length / total) * Math.PI * 2;
        outer.push({ family: row.family.id, path: anArc(CX, CY, 122, 172, sub, sub + laneSweep),
          colour: COLORS[items[0].kind] || 'var(--accent)' });
        sub += laneSweep;
      });
      angle += sweep;
    });
    const focused = AN_FOCUS.sunburst || rows[0].family.id;
    const focusRow = rows.find(row => row.family.id === focused) || rows[0];
    stage.innerHTML = `<div class="sunburst-map">
        <div class="an-wheel">
          <svg viewBox="0 0 400 400" role="img" aria-label="Families and lanes by component count">
            ${inner.map(wedge => `<path d="${wedge.path}" fill="${wedge.colour}"
              opacity="${wedge.row.family.id === focused ? '.95' : '.42'}"/>`).join('')}
            ${outer.map(wedge => `<path d="${wedge.path}" fill="${wedge.colour}"
              opacity="${wedge.family === focused ? '.72' : '.22'}"/>`).join('')}
            <circle cx="200" cy="200" r="58" fill="var(--panel)" stroke="var(--line)"/>
            <text x="200" y="193" text-anchor="middle" class="an-wheel-total">${total}</text>
            <text x="200" y="212" text-anchor="middle" class="an-wheel-label">components</text>
          </svg>
          <div class="an-wheel-keys">
            ${inner.map(wedge => `<button type="button" class="an-key${wedge.row.family.id === focused ? ' on' : ''}"
              data-an-focus="${esc(wedge.row.family.id)}" style="--lane-color:${wedge.colour}"
              ><i></i>${esc(wedge.row.family.name)}<small>${wedge.row.items.length}</small></button>`).join('')}
          </div>
        </div>
        <p class="an-legend-note">Angle is proportion of the visible set. Inner ring is families,
        outer ring their lanes. The wedges are drawn paths, so the buttons beside them are what
        carries the keyboard.</p>
        ${anStrip(focusRow.items, focusRow.family.name, 'Everything in the selected family.')}
      </div>`;
    anWireFocus(stage, 'sunburst', renderSunburst);
    wireMap(stage, '.an-node');
  }

  /* ---------------------------------------------------------------- sankey */

  function anBand(x0, y0a, y0b, x1, y1a, y1b) {
    /* A filled ribbon, not a stroked line: two cubic curves with their control
       points at the horizontal midpoint, joined top and bottom. Control points
       on the midpoint are what makes neighbouring ribbons run parallel instead
       of crossing each other at the ends. */
    const mid = (x0 + x1) / 2;
    return `M${x0} ${y0a.toFixed(2)}C${mid} ${y0a.toFixed(2)} ${mid} ${y1a.toFixed(2)} ${x1} ${y1a.toFixed(2)}`
      + `L${x1} ${y1b.toFixed(2)}C${mid} ${y1b.toFixed(2)} ${mid} ${y0b.toFixed(2)} ${x0} ${y0b.toFixed(2)}Z`;
  }

  function renderSankey(stage) {
    const visible = A.visibleComponents();
    if (!visible.length) { stage.innerHTML = emptyMap(); return; }
    const H = 420;
    const PAD = 8;
    const columns = [
      { id: 'family', x: 20, w: 14, key: component => component.family },
      { id: 'kind', x: 250, w: 14, key: component => component.kind },
      { id: 'ready', x: 480, w: 14, key: anReadiness },
    ];
    const nameOf = { family: id => (A.state.data.families.find(f => f.id === id) || { name: id }).name,
      kind: id => id, ready: id => AN_READY_LABEL[id] || id };
    const placed = columns.map(column => {
      const buckets = new Map();
      visible.forEach(component => {
        const key = column.key(component);
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(component);
      });
      const entries = [...buckets.entries()].sort((a, b) => b[1].length - a[1].length);
      const gaps = Math.max(entries.length - 1, 0) * PAD;
      const usable = H - gaps;
      let y = 0;
      const nodes = entries.map(pair => {
        const height = Math.max((pair[1].length / visible.length) * usable, 3);
        const node = { column: column.id, key: pair[0], items: pair[1], x: column.x,
          w: column.w, y: y, h: height,
          colour: COLORS[pair[1][0].kind] || 'var(--accent)' };
        y += height + PAD;
        return node;
      });
      return { column: column, nodes: nodes };
    });
    const focusKey = AN_FOCUS.sankey;
    const ribbons = [];
    for (let step = 0; step < placed.length - 1; step += 1) {
      const left = placed[step];
      const right = placed[step + 1];
      const offsetsL = new Map();
      const offsetsR = new Map();
      left.nodes.forEach(node => {
        right.nodes.forEach(target => {
          const shared = node.items.filter(component => target.items.indexOf(component) !== -1);
          if (!shared.length) return;
          const lh = (shared.length / node.items.length) * node.h;
          const rh = (shared.length / target.items.length) * target.h;
          const lo = offsetsL.get(node.key) || 0;
          const ro = offsetsR.get(target.key) || 0;
          ribbons.push({
            path: anBand(node.x + node.w, node.y + lo, node.y + lo + lh,
              target.x, target.y + ro, target.y + ro + rh),
            colour: node.colour,
            live: !focusKey || focusKey === `${left.column.id}::${node.key}`
              || focusKey === `${right.column.id}::${target.key}`,
          });
          offsetsL.set(node.key, lo + lh);
          offsetsR.set(target.key, ro + rh);
        });
      });
    }
    const nodeMarkup = placed.map(group => group.nodes.map(node => {
      const id = `${node.column}::${node.key}`;
      const label = nameOf[node.column](node.key);
      return `<button type="button" class="an-sk-node${focusKey === id ? ' on' : ''}"
        data-an-focus="${esc(id)}" style="--lane-color:${node.colour};left:${node.x}px;top:${node.y}px;width:${node.w}px;height:${node.h}px"
        aria-label="${esc(label)}, ${node.items.length} component${node.items.length === 1 ? '' : 's'}"
        ><span class="an-sk-label">${esc(label)}<small>${node.items.length}</small></span></button>`;
    }).join('')).join('');
    const focusNode = focusKey
      ? placed.reduce((found, group) => found
        || group.nodes.find(node => `${node.column}::${node.key}` === focusKey), null)
      : null;
    const picked = focusNode ? focusNode.items : visible;
    const label = focusNode ? nameOf[focusNode.column](focusNode.key) : 'Everything visible';
    stage.innerHTML = `<div class="sankey-map">
        <div class="an-sk-frame" style="--an-sk-h:${H}px">
          <svg viewBox="0 0 560 ${H}" preserveAspectRatio="none" aria-hidden="true">
            ${ribbons.map(ribbon => `<path d="${ribbon.path}" fill="${ribbon.colour}"
              opacity="${ribbon.live ? '.34' : '.06'}"/>`).join('')}
          </svg>
          ${nodeMarkup}
          <div class="an-sk-heads"><span>family</span><span>kind</span><span>setup readiness</span></div>
        </div>
        <p class="an-legend-note">Ribbon width is how many components take that path. The third
        column is the one the Build tab acts on: only <b>Setup ready</b> can be added.</p>
        ${anStrip(picked, label, 'The components flowing through the selected node.')}
      </div>`;
    anWireFocus(stage, 'sankey', renderSankey);
    wireMap(stage, '.an-node');
  }

  /* ------------------------------------------------------------------ rail */

  const AN_STAGES = [
    { id: 'scan', label: 'Scan', note: 'know the machine' },
    { id: 'rules', label: 'Rules', note: 'contract and block' },
    { id: 'runtime', label: 'Runtime', note: 'what runs models' },
    { id: 'models', label: 'Models', note: 'the tags themselves' },
    { id: 'guards', label: 'Guards', note: 'hooks that hold outside the model' },
    { id: 'verify', label: 'Verify', note: 'check rather than trust' },
    { id: 'unsequenced', label: 'Unsequenced', note: 'the data does not order these' },
  ];

  function anStage(component) {
    /* Derived from the data, never guessed. Anything the data does not sequence
       lands in 'unsequenced' and the column says so, which is the honest answer
       and the one a reader can act on. */
    const recipe = component.setupRecipe || '';
    if (recipe.indexOf('rules-guards') !== -1) return 'guards';
    if (recipe.indexOf('rules-verify') !== -1) return 'verify';
    if (recipe.indexOf('setup-rules-') === 0) return 'rules';
    if (recipe.indexOf('ollama-runtime') !== -1) return 'runtime';
    if (component.family === 'models' || recipe.indexOf('setup-model-') === 0) return 'models';
    if (component.lane === 'sys-hardware' || component.family === 'intake') return 'scan';
    return 'unsequenced';
  }

  function renderRail(stage) {
    const lanes = anByLane().slice(0, 26);
    if (!lanes.length) { stage.innerHTML = emptyMap(); return; }
    const basket = A.state.basket || [];
    const head = AN_STAGES.map((entry, index) =>
      `<div class="an-rail-col"><b>${String(index + 1).padStart(2, '0')} ${esc(entry.label)}</b><small>${esc(entry.note)}</small></div>`).join('');
    const body = lanes.map(row => {
      const bars = AN_STAGES.map((entry, index) => {
        const items = row.items.filter(component => anStage(component) === entry.id);
        if (!items.length) return '';
        /* Positioned with a grid column span, not with pixel maths. Nothing here
           measures anything, so nothing here can drift out of alignment. */
        return `<div class="an-rail-bar" style="grid-column:${index + 2} / span 1">
          ${items.slice(0, 6).map(component => `<span class="an-rail-chip${A.state.selected === component.id ? ' on' : ''}${basket.indexOf(component.id) !== -1 ? ' packed' : ''}"
            data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}
            >${selectButton(component)}${plus(component)}<b>${esc(component.name)}</b></span>`).join('')}
          ${items.length > 6 ? `<span class="an-rail-more">+${items.length - 6}</span>` : ''}
        </div>`;
      }).join('');
      return `<div class="an-rail-row"><div class="an-rail-lane">${esc(A.laneName(row.lane))}<small>${row.items.length}</small></div>${bars}</div>`;
    }).join('');
    stage.innerHTML = `<div class="rail-map">
        <div class="an-rail-grid">
          <div class="an-rail-row an-rail-head"><div class="an-rail-lane">lane</div>${head}</div>
          ${body}
        </div>
        <p class="an-legend-note">The axis is setup order, not time. Anything the data does not
        sequence sits in <b>Unsequenced</b> rather than being placed by guesswork. Chips already in
        Build carry a filled marker.</p>
      </div>`;
    wireMap(stage, '.an-rail-chip');
  }

  /* --------------------------------------------------------- contact sheet */

  function renderContact(stage) {
    const rows = groups();
    if (!rows.length) { stage.innerHTML = emptyMap(); return; }
    /* limit() is deliberately not called. Every other layer caps a family at
       MAX_PER_GROUP, and showing the whole visible set is the only reason this
       layer exists; capping it would just produce a worse deck. The extra nodes
       are paid for by content-visibility on each frame, not by truncation. */
    let counted = 0;
    const sheet = rows.map(row => {
      /* Numbering runs continuously across the sheet, like a film roll, so a
         frame number still identifies a frame after you have scrolled past its
         header. Per-family numbering would repeat 001 seventeen times. */
      const start = counted + 1;
      counted += row.items.length;
      const frames = row.items.map((component, index) => {
        const stamp = String(start + index).padStart(3, '0');
        return `<article class="an-frame${A.state.selected === component.id ? ' on' : ''}"
          data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}
          title="${esc(component.name)}">
          ${selectButton(component)}${plus(component)}
          <span class="an-frame-stamp">${stamp}<i>${esc(anCode(component.kind))}</i></span>
          <b class="an-frame-name">${esc(component.name)}</b>
        </article>`;
      }).join('');
      return `<section class="an-sheet-group">
        <header class="an-sheet-head"><h2>${esc(row.family.name)}</h2><small>${row.items.length} frame${row.items.length === 1 ? '' : 's'}</small></header>
        <div class="an-frames">${frames}</div>
      </section>`;
    }).join('');
    stage.innerHTML = `<div class="contact-map">${sheet}</div>`;
    wireMap(stage, '.an-frame');
  }

  /* --------------------------------------------------------------- terrace */

  function renderTerrace(stage) {
    const rows = groups();
    if (!rows.length) { stage.innerHTML = emptyMap(); return; }
    const floors = rows.map((row, index) => {
      const shown = limit(row.items);
      /* Labels are counter-rotated out of the isometric transform. Text inside
         a rotateX/rotateZ parent is unreadable at these angles, and skewed type
         is the single thing that makes hand-built isometric UI unusable. */
      const tiles = shown.map(component => `<div class="an-brick${A.state.selected === component.id ? ' on' : ''}"
        data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
        ${selectButton(component)}${plus(component)}
        <span class="an-brick-face"><b>${esc(component.name)}</b><small>${esc(anCode(component.kind))}</small></span>
      </div>`).join('');
      return `<section class="an-floor" style="--an-level:${index}">
        <div class="an-floor-plate">${tiles}</div>
        <p class="an-floor-label"><b>${esc(row.family.name)}</b><small>${row.items.length}</small></p>
      </section>`;
    }).join('');
    stage.innerHTML = `<div class="terrace-map" data-an-flat="0">
        <div class="an-stack">${floors}</div>
        <p class="an-legend-note">Each family is a floor and the stack makes the imbalance
        physical. Isometric layouts are genuinely hard to read for some people, so the projection
        is a toggle rather than a requirement, and it flattens automatically when the system asks
        for reduced motion.</p>
      </div>`;
    const flatten = document.querySelector('[data-an-flatten]');
    const map = stage.querySelector('.terrace-map');
    if (flatten && map) {
      /* The toggle lives in the shell, which survives re-renders, so its state
         is read from the button rather than kept here. */
      map.setAttribute('data-an-flat', flatten.getAttribute('aria-pressed') === 'true' ? '1' : '0');
    }
    wireMap(stage, '.an-brick');
  }

  /* ------------------------------------------------------------- broadside */

  function renderBroadside(stage) {
    const rows = groups();
    if (!rows.length) { stage.innerHTML = emptyMap(); return; }
    const sections = rows.map((row, index) => {
      const shown = limit(row.items);
      const items = shown.map((component, position) => `<article class="an-item${A.state.selected === component.id ? ' on' : ''}"
        data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)} style="--an-i:${position}">
        ${selectButton(component)}${plus(component)}
        <span class="an-item-rule"></span>
        <b class="an-item-name">${esc(component.name)}</b>
        <p class="an-item-detail">${esc(component.detail)}</p>
        <small class="an-item-meta">${itemMeta(component)}</small>
      </article>`).join('');
      return `<section class="an-spread">
        <header class="an-masthead">
          <span class="an-masthead-index">${String(index + 1).padStart(2, '0')}</span>
          <h2 class="an-masthead-name">${esc(row.family.name)}</h2>
          <span class="an-masthead-count">${row.items.length}</span>
        </header>
        <div class="an-items">${items}</div>
      </section>`;
    }).join('');
    /* The marquee track is duplicated EXACTLY twice and translates to -50%.
       That pairing is what makes the loop seamless; any other multiple leaves a
       visible jump at the wrap. */
    const ribbon = rows.map(row => `<span>${esc(row.family.name)}</span><i>/</i>`).join('');
    stage.innerHTML = `<div class="broadside-map">
        <div class="an-marquee" aria-hidden="true"><div class="an-marquee-track">${ribbon}${ribbon}</div></div>
        ${sections}
      </div>`;
    wireMap(stage, '.an-item');
  }

  /* ---------------------------------------------------------------- ledger */

  function anFilterCommand() {
    /* The active filters, printed back as the command that would reproduce
       them. It teaches the filter model better than a legend does, and it is
       read-only: nothing here parses it back. */
    const state = A.state;
    const parts = ['atlas'];
    if (state.family) parts.push(`--family ${state.family}`);
    if (state.kind) parts.push(`--kind ${state.kind}`);
    if (state.sub) parts.push(`--sub "${state.sub}"`);
    if (state.search) parts.push(`--search "${state.search}"`);
    if (state.platform) parts.push(`--os ${state.platform}`);
    return parts.length === 1 ? 'atlas --all' : parts.join(' ');
  }

  function anPad(text, width) {
    const value = String(text === null || text === undefined ? '' : text);
    return value.length > width ? `${value.slice(0, width - 1)}…` : value.padEnd(width);
  }

  const AN_READY_MARK = { ready: '+', reference: '?', hosted: '~', unavailable: '.' };

  function renderLedger(stage) {
    const visible = A.visibleComponents();
    if (!visible.length) { stage.innerHTML = emptyMap(); return; }
    /* Monospace plus ch units means every column aligns with no measurement
       code at all: column N sits at N ch, and padEnd does the rest. */
    const lines = visible.map((component, index) => {
      const mark = AN_READY_MARK[anReadiness(component)] || '.';
      return `<div class="an-line${A.state.selected === component.id ? ' on' : ''}"
        data-node="1" data-comp="${esc(component.id)}" ${styleFor(component)}>
        ${selectButton(component)}${plus(component)}<code>${esc(String(index + 1).padStart(4, '0'))}  [${esc(anCode(component.kind).charAt(0).toLowerCase())}] ${esc(anPad(A.laneName(component.lane), 26))} ${esc(anPad(component.name, 34))} ${esc(anPad(component.sub || '', 24))} ${esc(mark)}</code>
      </div>`;
    }).join('');
    stage.innerHTML = `<div class="ledger-map">
        <p class="an-prompt"><span>$</span> <code>${esc(anFilterCommand())}</code></p>
        <div class="an-ledger-head"><code>${esc(anPad('#', 6))}${esc(anPad('kind', 4))}${esc(anPad('lane', 27))}${esc(anPad('component', 35))}${esc(anPad('sub-category', 25))}rdy</code></div>
        <div class="an-lines">${lines}</div>
        <p class="an-legend-note">Kind is a letter, not only a colour, and readiness is a mark:
        <code>+</code> setup ready, <code>?</code> reference needing review, <code>~</code> hosted,
        <code>.</code> no recipe yet. This is the layer that still works with colour removed.</p>
      </div>`;
    wireMap(stage, '.an-line');
  }

  /* ---------------------------------------------------------------- bundle */

  function renderBundle(stage) {
    const lanes = anByLane();
    if (!lanes.length) { stage.innerHTML = emptyMap(); return; }
    /* Anchors are ordered BY FAMILY so each family holds a contiguous arc. That
       ordering is what makes a bundle mean anything; ordered arbitrarily the
       same edges render as a hairball. */
    const families = A.state.data.families.map(family => family.id);
    const ordered = lanes.slice().sort((a, b) => {
      const laneA = A.state.data.lanes.find(lane => lane.id === a.lane) || {};
      const laneB = A.state.data.lanes.find(lane => lane.id === b.lane) || {};
      const rank = families.indexOf(laneA.family) - families.indexOf(laneB.family);
      return rank !== 0 ? rank : b.items.length - a.items.length;
    }).slice(0, 56);
    const CX = 210;
    const CY = 210;
    const R = 168;
    const at = {};
    ordered.forEach((row, index) => {
      const angle = (index / ordered.length) * Math.PI * 2 - Math.PI / 2;
      at[row.lane] = { x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle),
        angle: angle, colour: COLORS[row.items[0].kind] || 'var(--accent)' };
    });
    const laneOf = {};
    A.visibleComponents().forEach(component => { laneOf[component.id] = component.lane; });
    const focused = AN_FOCUS.bundle;
    const edges = [];
    (A.state.data.routes || []).forEach(route => {
      const members = (route.members || []).map(id => laneOf[id]).filter(Boolean);
      const unique = [...new Set(members)].filter(lane => at[lane]);
      for (let i = 0; i < unique.length; i += 1) {
        for (let j = i + 1; j < unique.length; j += 1) {
          const from = at[unique[i]];
          const to = at[unique[j]];
          /* One quadratic bezier per edge, its control point pulled toward the
             centre. The tension is what makes edges from the same region share a
             path and read as a bundle rather than as noise. */
          const tension = 0.75;
          const mx = (from.x + to.x) / 2;
          const my = (from.y + to.y) / 2;
          const qx = mx + (CX - mx) * tension;
          const qy = my + (CY - my) * tension;
          edges.push({
            path: `M${from.x.toFixed(1)} ${from.y.toFixed(1)}Q${qx.toFixed(1)} ${qy.toFixed(1)} ${to.x.toFixed(1)} ${to.y.toFixed(1)}`,
            colour: from.colour,
            live: !focused || focused === unique[i] || focused === unique[j],
          });
        }
      }
    });
    const keys = ordered.map(row => {
      const anchor = at[row.lane];
      const degrees = (anchor.angle * 180) / Math.PI;
      return `<button type="button" class="an-anchor${focused === row.lane ? ' on' : ''}"
        data-an-focus="${esc(row.lane)}" style="--lane-color:${anchor.colour};--an-deg:${degrees.toFixed(2)}deg"
        aria-label="${esc(A.laneName(row.lane))}, ${row.items.length} component${row.items.length === 1 ? '' : 's'}"
        ><i></i></button>`;
    }).join('');
    const focusRow = focused ? lanes.find(row => row.lane === focused) : ordered[0];
    const picked = (focusRow || ordered[0]).items;
    const label = A.laneName((focusRow || ordered[0]).lane);
    stage.innerHTML = `<div class="bundle-map">
        <div class="an-ring">
          <svg viewBox="0 0 420 420" role="img" aria-label="Routes drawn as bundled edges between lanes">
            <circle cx="210" cy="210" r="168" fill="none" stroke="var(--line)" stroke-dasharray="3 6"/>
            ${edges.map(edge => `<path d="${edge.path}" fill="none" stroke="${edge.colour}"
              stroke-width="${edge.live ? 1.6 : 0.7}" opacity="${edge.live ? '.62' : '.08'}"/>`).join('')}
          </svg>
          <div class="an-anchors">${keys}</div>
        </div>
        <p class="an-legend-note">${edges.length} edge${edges.length === 1 ? '' : 's'} from
        ${(A.state.data.routes || []).length} routes, across ${ordered.length} of ${lanes.length}
        lanes. Anchors are ordered by family so each family holds one arc. SVG paths cannot take
        focus, so the ring of buttons is what carries the keyboard.</p>
        ${anStrip(picked, label, 'Everything in the focused lane.')}
      </div>`;
    anWireFocus(stage, 'bundle', renderBundle);
    wireMap(stage, '.an-node');
  }

  const MAPS = { transit: renderTransit, compiler: renderCompiler, cascade: renderCascade, command: renderCommand, deck: renderDeck,
    tree: renderTree, river: renderRiver, city: renderCity, patch: renderPatch, campaign: renderCampaign,
    forge: renderForge, cinema: renderCinema, bridge: renderBridge,
    treemap: renderTreemap, matrix: renderMatrix, sunburst: renderSunburst, sankey: renderSankey, rail: renderRail,
    contact: renderContact, terrace: renderTerrace, broadside: renderBroadside, ledger: renderLedger, bundle: renderBundle };

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


  /* -------------------------------------------- shells for the ten analytical layers

     One shell helper, because the ten differ in their MAP grammar rather than
     in their chrome, and thirteen near-identical shells above is already more
     duplication than this file needed. Each layer passes the extras that are
     genuinely its own. */

  function anShell(key, copy, options) {
    const extras = options || {};
    return `<a class="skip" href="#stage">Skip to the interactive roadmap</a>
      <div class="an-shell an-shell-${key}">
        <header class="an-header">
          <div><p class="brand-kicker">${copy.eyebrow}</p><h1 class="brand-name">${copy.title}</h1><p class="brand-copy">${copy.copy}</p></div>
          <div class="an-header-side">
            <span class="count-chip"><b data-visible-count>0</b> visible</span>
            <span class="count-chip"><b data-basket-count>0</b> in Build</span>
            <div id="themehost"></div>
          </div>
        </header>
        <nav class="an-tabs" id="tabs" role="tablist" aria-label="${copy.title} views"></nav>
        <div class="an-layout">
          <aside class="an-rail-side">
            <section class="an-block"><p class="eyebrow">Computer scan</p><div id="setup"></div></section>
            <section class="an-block"><p class="eyebrow">Filters</p><div id="filters"></div></section>
            ${extras.aside || ''}
          </aside>
          <main class="an-main" id="main-content">
            <header class="an-stage-head">
              <div><p class="eyebrow">${copy.map}</p><p class="brand-copy">${copy.note}</p></div>
              ${extras.tools || ''}
            </header>
            <div id="stage" tabindex="-1"></div>
          </main>
          <aside id="side" aria-label="Component inspector"></aside>
        </div>
      </div>`;
  }

  function anLegend() {
    return `<section class="an-block an-block-key"><p class="eyebrow">Kind key</p>
      <ul class="an-legend">${AN_KINDS.map(kind =>
        `<li style="--lane-color:${COLORS[kind]}"><i>${AN_CODES[kind]}</i>${kind}</li>`).join('')}</ul>
      <p class="an-key-note">The three letter code and the colour say the same thing, so every
      layer below still reads with colour removed.</p></section>`;
  }

  function shellTreemap(copy) {
    return anShell('treemap', copy, { aside: anLegend() });
  }

  function shellMatrix(copy) {
    return anShell('matrix', copy, { aside: anLegend() });
  }

  function shellSunburst(copy) {
    return anShell('sunburst', copy, { aside: anLegend() });
  }

  function shellSankey(copy) {
    return anShell('sankey', copy, {
      aside: `<section class="an-block an-block-key"><p class="eyebrow">Readiness key</p>
        <ul class="an-legend an-legend-ready">
          <li><i>+</i>Setup ready, Build can add it</li>
          <li><i>?</i>Reference, needs security review</li>
          <li><i>~</i>Hosted, sign in rather than install</li>
          <li><i>.</i>No reviewed recipe yet</li>
        </ul></section>`,
    });
  }

  function shellRail(copy) {
    return anShell('rail', copy, { aside: anLegend() });
  }

  function shellContact(copy) {
    return anShell('contact', copy, {
      aside: anLegend(),
      tools: `<div class="an-density" role="group" aria-label="Frame density">
        <span class="an-density-label">Density</span>
        <button type="button" class="an-den" data-an-density="tight" aria-pressed="false">Tight</button>
        <button type="button" class="an-den on" data-an-density="normal" aria-pressed="true">Normal</button>
        <button type="button" class="an-den" data-an-density="roomy" aria-pressed="false">Roomy</button>
      </div>`,
    });
  }

  function shellTerrace(copy) {
    return anShell('terrace', copy, {
      aside: anLegend(),
      tools: `<button type="button" class="an-toggle" data-an-flatten aria-pressed="false">
        Flatten the projection</button>`,
    });
  }

  function shellBroadside(copy) {
    return anShell('broadside', copy, { aside: anLegend() });
  }

  function shellLedger(copy) {
    return anShell('ledger', copy, {
      aside: `<section class="an-block an-block-key"><p class="eyebrow">Sigils</p>
        <ul class="an-legend an-legend-ready">
          <li><i>i</i>instruction</li><li><i>c</i>capability</li><li><i>k</i>knowledge</li>
          <li><i>o</i>control</li><li><i>m</i>model</li><li><i>d</i>delivery</li>
        </ul>
        <p class="an-key-note">Text, not colour. This layer is the greyscale-safe one.</p></section>`,
    });
  }

  function shellBundle(copy) {
    return anShell('bundle', copy, { aside: anLegend() });
  }

  /* Two shell-owned controls that outlive a re-render, so they are bound once
     at boot rather than inside a map renderer. Binding them per render would
     stack a listener on every filter change and fire the handler N times. */
  function anWireShellControls() {
    document.querySelectorAll('[data-an-density]').forEach(button => {
      button.addEventListener('click', () => {
        document.querySelectorAll('[data-an-density]').forEach(other => {
          const active = other === button;
          other.classList.toggle('on', active);
          other.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        document.body.setAttribute('data-an-density', button.getAttribute('data-an-density'));
      });
    });
    const flatten = document.querySelector('[data-an-flatten]');
    if (flatten) {
      flatten.addEventListener('click', () => {
        const next = flatten.getAttribute('aria-pressed') !== 'true';
        flatten.setAttribute('aria-pressed', next ? 'true' : 'false');
        flatten.classList.toggle('on', next);
        const map = document.querySelector('.terrace-map');
        if (map) map.setAttribute('data-an-flat', next ? '1' : '0');
      });
    }
  }

  const SHELLS = { transit: shellTransit, compiler: shellCompiler, cascade: shellCascade, command: shellCommand, deck: shellDeck,
    tree: shellTree, river: shellRiver, city: shellCity, patch: shellPatch, campaign: shellCampaign,
    forge: shellForge, cinema: shellCinema, bridge: shellBridge,
    treemap: shellTreemap, matrix: shellMatrix, sunburst: shellSunburst, sankey: shellSankey, rail: shellRail,
    contact: shellContact, terrace: shellTerrace, broadside: shellBroadside, ledger: shellLedger, bundle: shellBundle };

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
    anWireShellControls();

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
