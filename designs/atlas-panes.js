/* Shared panes for every atlas design.
 *
 * The setup bar, the filters, the tabs and the detail panel must say the same
 * thing in all five designs, so they are written once here. Each design supplies
 * its own CSS and its own map visualization; identical markup under different
 * stylesheets looks nothing alike, which is the point.
 *
 * A design provides:
 *   AtlasPanes.mount({ renderMap, onSelect, onFilter })
 * where renderMap draws into #stage for the "map" tab.
 */
'use strict';

const AtlasPanes = (() => {
  const A = AtlasCore;
  let tab = 'map';
  let hooks = {};

  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
    m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const val = id => (document.getElementById(id) || {}).value || '';
  const KIND_NOTES = {
    instruction: 'Rules and written guidance that tell an assistant how to work.',
    capability: 'Tools, agents and integrations that perform a task.',
    knowledge: 'Reference material and searchable information used to answer questions.',
    control: 'Policy, safety and verification checks around actions.',
    model: 'Inference runtimes and model choices, sized for your hardware.',
    delivery: 'Build, publish and handoff workflows for finished work.',
  };

  function familyDescription(family) {
    if (family.description) return family.description;
    const lanes = A.state.lanes.filter(l => l.family === family.id);
    return lanes.length ? lanes.slice(0, 3).map(l => l.description || l.name).join(' ')
      : 'A group of related catalog lanes. No entries are available in this data file.';
  }

  /* ------------------------------------------------------- setup bar */

  /* Order matters. The operating system is asked first because it decides which
     scan command to show, and the scan is what fills in the hardware. Asking for
     RAM before knowing the platform would mean guessing which command produces
     it, and on Apple silicon it would mean asking for VRAM that does not exist. */

  function setupUI() {
    const host = document.getElementById('setup');
    if (!host) return;
    const chosen = A.platform();

    const osButtons = A.PLATFORMS.map(p =>
      `<button class="os${A.effectivePlatform() === p.id ? ' on' : ''}" data-os="${p.id}"
        title="${esc(p.note)}" aria-pressed="${A.effectivePlatform() === p.id}">${esc(p.label)}</button>`).join('');

    const scan = A.scanCommand();
    const tier = A.currentTier();
    const mem = A.usableMemory();

    host.innerHTML = `
      <div class="step">
        <span class="num">1</span>
        <div class="stepbody">
          <div class="steplabel">Your system</div>
          <div class="osrow">${osButtons}</div>
          ${chosen ? `<div class="osnote">${esc(chosen.note)}</div>` : ''}
        </div>
      </div>

      <div class="step${chosen ? '' : ' locked'}">
        <span class="num">2</span>
        <div class="stepbody">
          <div class="steplabel">Scan it</div>
          ${chosen
            ? `<button class="scan" id="scanbtn" title="Click to copy">${esc(scan)}</button>
               <div class="osnote">Run this, then type the numbers below.</div>`
            : '<div class="osnote">Pick your system first and the right scan command appears here.</div>'}
        </div>
      </div>

      <div class="step${chosen ? '' : ' locked'}">
        <span class="num">3</span>
        <div class="stepbody">
          <div class="steplabel">What it has</div>
          <div class="hwrow">
            ${A.HW_FIELDS.map(f => {
              const hidden = f.id === 'vram' && A.state.platform === 'macos';
              return `<label class="hwfield${hidden ? ' dim' : ''}" title="${esc(f.hint)}">
                <span>${esc(f.label)}${f.unit ? ` <i>${esc(f.unit)}</i>` : ''}</span>
                <input type="number" min="0" max="4096" data-hw="${f.id}"
                  value="${A.state.hw[f.id] == null ? '' : A.state.hw[f.id]}"
                  ${hidden ? 'disabled placeholder="unified"' : 'placeholder="?"'}>
              </label>`;
            }).join('')}
          </div>
          <div class="verdictline">
            ${mem
              ? `<b>${esc(tier.label)}</b> · ${esc(tier.verdict)}`
              : 'Enter RAM to see what this machine can host.'}
          </div>
        </div>
      </div>`;

    host.querySelectorAll('[data-os]').forEach(b => {
      b.onclick = () => { A.setPlatform(b.dataset.os); draw(); };
    });
    const scanbtn = document.getElementById('scanbtn');
    if (scanbtn) scanbtn.onclick = async () => {
      const ok = await A.copy(scan);
      scanbtn.textContent = ok ? 'copied, run it in your terminal' : 'select the text to copy';
      setTimeout(() => { scanbtn.textContent = scan; }, 1700);
    };
    host.querySelectorAll('[data-hw]').forEach(input => {
      input.oninput = () => {
        A.setHardware(input.dataset.hw, input.value);
        const line = host.querySelector('.verdictline');
        const t = A.currentTier();
        if (line) {
          line.innerHTML = A.usableMemory()
            ? `<b>${esc(t.label)}</b> · ${esc(t.verdict)}`
            : 'Enter RAM to see what this machine can host.';
        }
        if (tab !== 'map') renderStage();
      };
    });
  }

  /* --------------------------------------------------------- filters */

  /* Every filter row composes with every other. Nothing here replaces a previous
     choice, so families, kinds and sub-categories can be mixed freely. */

  /* Clicking a sub-category says what it is, not only what it filters to.
     A chip label has to stay short enough to fit a row, which leaves "Data
     interchange" and "Multi-model databases" looking self-explanatory when they
     are not. The note appears for whatever is currently selected, so it answers
     the question at the moment it gets asked. */
  function subNotes(subs) {
    const chosen = subs.filter(s => A.state.activeSubs.has(s.id) && s.description);
    if (!chosen.length) return '';
    return `<div class="frow subnote-row">
      <span class="flabel"></span>
      <span class="subnotes">${chosen.map(s =>
        `<span class="subnote"><b>${esc(s.id)}</b> ${esc(s.description)}</span>`).join('')}</span>
    </div>`;
  }

  /* --------------------------------------------------- orientation strip

     Rendered above the filters on every design, so the answer to "what am I
     looking at" is on screen rather than something you have to already know.

     It carries the reading switch, because that is the control a non-technical
     reader needs first and it has to be findable without knowing the word for
     it. Plain is default; the switch says which one is on rather than making
     you infer it from the prose.

     Collapsible and remembered, so an experienced reader closes it once and
     never sees it again, while a first-time visitor is not left guessing. */
  function orientationHTML() {
    const level = A.readingLevel();
    const open = orientationOpen();
    return `<section class="orient${open ? '' : ' closed'}">
      <div class="orient-bar">
        <button type="button" class="orient-toggle" data-orient-toggle
          aria-expanded="${open}">
          <span class="orient-mark" aria-hidden="true">${open ? '&minus;' : '+'}</span>
          <b>Start here</b>
          <span class="orient-sub">What this page is, and how to move around it</span>
        </button>
        <div class="orient-level" role="group" aria-label="Reading level">
          <button type="button" data-reading="plain" aria-pressed="${level === 'plain'}"
            title="Everyday words, no jargon">Plain</button>
          <button type="button" data-reading="technical" aria-pressed="${level === 'technical'}"
            title="Exact names and the detail behind them">Technical</button>
        </div>
      </div>
      ${open ? `<div class="orient-body">
        <p class="orient-lede">${esc(A.orientationText())}</p>
        <ol class="orient-steps">
          <li><b>Pick your system</b> above, so the commands match your computer.</li>
          <li><b>Use the tabs</b> to move: each one says what it holds.</li>
          <li><b>Copy a command</b> from Commands, or let Easy setup write them all.</li>
        </ol>
        <div class="orient-terms">
          <p class="orient-terms-head">Words used on this page</p>
          <dl>${A.glossary().map(entry => `<div>
            <dt>${esc(entry.term)}</dt><dd>${esc(entry.text)}</dd></div>`).join('')}</dl>
        </div>
      </div>` : ''}
    </section>`;
  }

  function orientationOpen() {
    try { return localStorage.getItem('atlas.orient') !== 'closed'; }
    catch (_) { return true; }
  }

  function setOrientationOpen(open) {
    try { localStorage.setItem('atlas.orient', open ? 'open' : 'closed'); }
    catch (_) { /* private windows must not break the page */ }
  }

  function wireOrientation() {
    document.querySelectorAll('[data-reading]').forEach(btn => {
      btn.onclick = () => { A.setReadingLevel(btn.dataset.reading); draw(); };
    });
    document.querySelectorAll('[data-orient-toggle]').forEach(btn => {
      btn.onclick = () => { setOrientationOpen(!orientationOpen()); draw(); };
    });
  }

  function filtersUI() {
    const host = document.getElementById('filters');
    if (!host) return;
    const c = A.counts();
    const subs = A.subcategories();

    host.innerHTML = orientationHTML() + `
      <div class="frow">
        <label class="flabel" for="fq">Search</label>
        <input class="fsearch" id="fq" type="text" placeholder="name, owner, lane or description"
          value="${esc(A.state.query)}">
        <span class="fcount">${c.visibleComponents} of ${c.components}</span>
        ${c.filters ? `<button class="fclear" id="fclear">clear ${c.filters} filter(s)</button>` : ''}
      </div>
      <div class="frow">
        <span class="flabel">Family</span>
        <span class="chips">${A.state.data.families.map(f =>
          `<button class="chip${A.state.activeFamilies.has(f.id) ? ' on' : ''}"
            data-fam="${esc(f.id)}" aria-pressed="${A.state.activeFamilies.has(f.id)}"
            title="${esc(familyDescription(f))}">${esc(f.name)}</button>`).join('')}</span>
      </div>
      <div class="frow">
        <span class="flabel">Kind</span>
        <span class="chips">${['instruction', 'capability', 'knowledge', 'control', 'model', 'delivery']
          .map(k => `<button class="chip k-${k}${A.state.activeKinds.has(k) ? ' on' : ''}"
            data-kind="${k}">${k}</button>`).join('')}</span>
      </div>
      <div class="frow">
        <span class="flabel">Sub-category</span>
        <span class="chips">${subs.map(s =>
          `<button class="chip sub${A.state.activeSubs.has(s.id) ? ' on' : ''}"
            data-sub="${esc(s.id)}"${s.description ? ` title="${esc(s.description)}"` : ''}
            >${esc(s.id)} <i>${s.count}</i></button>`).join('')
          || '<span class="fcount">none in the current selection</span>'}</span>
      </div>
      ${subNotes(subs)}
      <div class="filter-explanations" aria-live="polite">${A.state.data.families
        .filter(f => A.state.activeFamilies.has(f.id))
        .map(f => `<p><b>${esc(f.name)}:</b> ${esc(familyDescription(f))}</p>`).join('')}
      ${[...A.state.activeKinds].map(k => `<p><b>${esc(k)}:</b> ${esc(KIND_NOTES[k] || '')}</p>`).join('')}</div>`;

    const q = document.getElementById('fq');
    if (q) {
      q.oninput = () => { A.setQuery(q.value); refreshFilterCounts(); renderStage(); };
      q.onkeydown = e => { if (e.key === 'Escape') { q.value = ''; q.oninput(); } };
    }
    const clear = document.getElementById('fclear');
    if (clear) clear.onclick = () => { A.clearFilters(); draw(); if (hooks.onFilter) hooks.onFilter(); };
    host.querySelectorAll('[data-fam]').forEach(b =>
      b.onclick = () => { A.toggleFamily(b.dataset.fam); filtersUI(); renderStage(); });
    host.querySelectorAll('[data-kind]').forEach(b =>
      b.onclick = () => { A.toggleKind(b.dataset.kind); filtersUI(); renderStage(); });
    host.querySelectorAll('[data-sub]').forEach(b =>
      b.onclick = () => { A.toggleSub(b.dataset.sub); filtersUI(); renderStage(); });
    wireOrientation();
  }

  function refreshFilterCounts() {
    const c = A.counts();
    const el = document.querySelector('#filters .fcount');
    if (el) el.textContent = `${c.visibleComponents} of ${c.components}`;
  }

  /* Some designs carry their own kind chips on the map. Toggling one of those
     must not leave the filter bar showing the opposite state, so the classes are
     synced in place. Rebuilding the bar instead would steal focus from the search
     box mid-keystroke, which is why this touches classes only. */
  function syncFilterChips() {
    const host = document.getElementById('filters');
    if (!host) return;
    host.querySelectorAll('[data-fam]').forEach(b =>
      b.classList.toggle('on', A.state.activeFamilies.has(b.dataset.fam)));
    host.querySelectorAll('[data-kind]').forEach(b =>
      b.classList.toggle('on', A.state.activeKinds.has(b.dataset.kind)));
    host.querySelectorAll('[data-sub]').forEach(b =>
      b.classList.toggle('on', A.state.activeSubs.has(b.dataset.sub)));
    const search = document.getElementById('fq');
    if (search && document.activeElement !== search && search.value !== A.state.query) {
      search.value = A.state.query;
    }
    refreshFilterCounts();
  }

  /* -------------------------------------------------- detail panel */

  function detailUI() {
    const side = document.getElementById('side');
    if (!side) return;
    const lane = A.laneDetailFor(A.state.selectedLane);
    if (lane) {
      side.innerHTML = `<div class="sec">Lane overview</div><h2>${esc(lane.name)}</h2>
        <p class="ddesc">${esc(lane.description || 'A user-defined catalog lane.')}</p>
        <p class="meta">Family: ${esc(lane.family)} · Kind: ${esc(lane.kind)}<br>
        Source: ${esc(lane.source || 'Saved in this browser')}<br>${lane.components.length} indexed entries</p>
        <div class="conn">${lane.components.map(c => `<button data-lane-component="${esc(c.id)}">
          ${esc(c.name)}<small>${esc(c.detail || c.sub || c.kind)}</small></button>`).join('')
          || '<p class="empty">No entries yet. Add a suggestion from the Suggest tab.</p>'}</div>`;
      side.querySelectorAll('[data-lane-component]').forEach(b => {
        b.onclick = () => A.select(b.dataset.laneComponent);
      });
      return;
    }
    const d = A.state.selected ? A.detailFor(A.state.selected) : null;
    if (!d) {
      side.innerHTML = `<div class="sec">Component detail</div>
        <p class="empty">Select any component to see what it is, which lane it sits in, what it
        connects to, its hybrid routes, and whether it has a complete setup recipe. Use <b>+</b>
        to combine setup-ready components into one commands-only script.</p>`;
      return;
    }
    const setup = d.setupCommand;
    side.innerHTML = `
      <div class="dhead">
        <div>
          <div class="dname">${esc(d.name)}</div>
          ${d.owner ? `<div class="downer">${esc(d.owner)}</div>` : ''}
        </div>
        ${setup ? `<button class="plus${d.inBasket ? ' in' : ''}" id="plus"
          title="${d.inBasket ? 'Remove this setup from the combination' : 'Add this setup to Build'}">
          ${d.inBasket ? '&#10003;' : '+'}</button>`
          : `<span class="dkind sub">${esc(d.setupState.label)}</span>`}
      </div>
      <span class="dkind" data-kind="${esc(d.kind)}">${esc(d.kind)}</span>
      ${d.sub ? `<span class="dkind sub">${esc(d.sub)}</span>` : ''}
      <p class="ddesc">${esc(d.detail)}</p>
      <div class="meta">
        Family: <b>${esc(d.family)}</b><br>
        Lane: <button class="text-link" data-detail-lane="${esc(d.laneId)}">${esc(d.lane)}</button><br>
        ${esc(d.laneDescription)}<br>
        ${d.laneSource ? `Source: <code>${esc(d.laneSource)}</code><br>` : ''}
        ${d.siblings} sibling component${d.siblings === 1 ? '' : 's'} in this lane
      </div>
      ${commandBlock(d)}
      <div class="sec">Connects to (${d.connections.length})</div>
      ${d.connections.length
        ? `<div class="conn">${d.connections.map(c =>
            `<button data-go="${esc(c.id)}">${esc(c.name)}<small>${esc(c.lane)}</small></button>`).join('')}</div>`
        : '<p class="empty">No recorded connections.</p>'}
      <div class="sec">Hybrid routes (${d.routes.length})</div>
      ${d.routes.length
        ? d.routes.map(r => `<div class="route"><b>${esc(r.name)}</b><p>${esc(r.detail)}</p>
            <span class="tag">best for ${esc(r.bestFor)} · needs ${esc(r.requires)}</span></div>`).join('')
        : '<p class="empty">Not part of a hybrid route.</p>'}`;

    wireCopy(side, setup || d.command);
    side.querySelectorAll('[data-detail-lane]').forEach(b => {
      b.onclick = () => A.selectLane(b.dataset.detailLane);
    });
    const plus = document.getElementById('plus');
    if (plus) plus.onclick = () => {
      d.inBasket ? A.removeFromBasket(d.id) : A.addToBasket(d.id);
      detailUI();
      tabsUI();
    };
    side.querySelectorAll('[data-go]').forEach(b => {
      b.onclick = () => { A.select(b.dataset.go); if (hooks.onSelect) hooks.onSelect(b.dataset.go); };
    });
  }

  function commandBlock(d) {
    if (!A.state.platform) {
      return `<div class="sec">Command</div>
        <p class="empty">Choose your operating system in step 1 and the command for it appears here.</p>`;
    }
    if (!d.setupCommand) {
      return `<div class="sec">Computer setup</div>
        <p class="empty"><b>${esc(d.setupState.label)}.</b> A GitHub source, test, workflow, or run
        command is not treated as installation. Only a complete reviewed recipe can enter Build.</p>
        ${d.command ? `<div class="sec">Action or reference command</div>
          <p class="sub">Review prerequisites and permissions before running. This page does not execute commands.</p>
          <div class="cmd wrap"><button class="copy" data-copy>copy</button>${esc(d.command)}</div>` : ''}`;
    }
    return `<div class="sec">Setup for ${esc(A.platform().label)}</div>
      <div class="cmd"><button class="copy" data-copy>copy</button>${esc(d.setupCommand)}</div>`;
  }

  function wireCopy(root, text) {
    const btn = root.querySelector('[data-copy]');
    if (!btn || !text) return;
    btn.onclick = async () => {
      btn.textContent = (await A.copy(text)) ? 'copied' : 'select it';
      setTimeout(() => { btn.textContent = 'copy'; }, 1400);
    };
  }

  /* --------------------------------------------------------- tabs */

  function tabsUI() {
    const host = document.getElementById('tabs');
    if (!host) return;
    const basket = A.state.basket.length;
    host.innerHTML = '';
    A.TABS.forEach(t => {
      const b = document.createElement('button');
      b.className = 'tab';
      b.innerHTML = esc(t.label) + (t.id === 'basket' && basket ? ` <i class="badge">${basket}</i>` : '');
      b.title = t.hint;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', String(t.id === tab));
      b.onclick = () => { tab = t.id; draw(); };
      host.appendChild(b);
    });
  }

  /* -------------------------------------------------------- panes */

  function indexHTML() {
    const needle = A.state.query.trim().toLowerCase();
    const visible = A.visibleComponents();
    const lanes = A.visibleLanes().filter(l => !needle ||
      `${l.name} ${l.description || ''}`.toLowerCase().includes(needle) || visible.some(c => c.lane === l.id));
    const store = A.state.data.store;
    return `<h2>Find what you need</h2><p class="sub">An index is a directory of names, descriptions and metadata.
      Search above, combine Family, Kind and Sub-category, then click a lane for its purpose and entries.</p>
      <p class="sub">Start with Easy setup for a new machine. Use Commands for actions, Build for a combined installation,
      and Hybrid routes to see how agents and models work together. No credentials are requested or stored here.</p>
      <div class="grid">${lanes.map(l => `<button class="lane-card index-lane" data-open-lane="${esc(l.id)}">
        <b>${esc(l.name)}</b><p>${esc(l.description || 'Custom catalog lane.')}</p>
        <span class="src">${esc(l.family)} · ${esc(l.kind)} · ${visible.filter(c => c.lane === l.id).length} matching entries</span>
      </button>`).join('') || '<p class="empty">No lanes match. Clear filters or try a shorter search.</p>'}</div>
      ${store ? `<details class="store-guide"><summary>What does the MongoDB store mean?</summary>
        <p>The optional backend saves redacted activity records in MongoDB. The browser only displays its schema,
        never the live records or database credentials. Database indexes are lookup structures: they help find a
        person, project or time period without scanning every record. They are different from this catalog directory.</p>
        <div class="grid">${store.indexes.map(i => `<article class="lane-card"><b>${esc(i.name)}</b>
          <p>${esc(i.question)}</p><code>${esc(i.collection)} ${esc(i.keys)}</code><p>${esc(i.why)}</p></article>`).join('')}</div>
        <p>Run from the repository on the backend after configuring MongoDB and consent. Keep connection secrets in server-side environment variables.</p>
        <pre class="cmd wrap">${esc(store.command)}</pre>
      </details>` : ''}`;
  }

  /* Said once, where the commands are, rather than left implicit. A reader who
     is on WSL has to be told that a user agent cannot see that, or they will
     copy PowerShell into bash and blame the page. */
  function suggestedNotice() {
    if (!A.platformIsSuggested()) return '';
    const guess = A.platform();
    if (!guess) return '';
    return `<p class="suggested">Showing <b>${esc(guess.shell)}</b> commands for
      <b>${esc(guess.label)}</b>, guessed from your browser. Pick your system above to
      confirm it. Working inside WSL? Choose Ubuntu / WSL: a browser cannot detect it.</p>`;
  }

  /* The directory shows the COMMAND, not just the name of a thing that has one.
     It used to render name, description and lane, and you had to click through
     to see any command text, so a page called "Command directory" contained no
     commands. Measured across all thirty designs: zero command strings in the
     rendered DOM.

     Both kinds are shown and labelled, because they are not interchangeable. A
     setup command comes from a reviewed recipe and installs something; an action
     command is the thing you run afterwards. A component can carry both. */
  function commandRow(component) {
    const setup = A.setupCommandFor(component);
    const action = A.commandFor(component);
    const rows = [];
    if (setup) rows.push({ kind: 'setup', label: 'Setup', text: setup });
    if (action) rows.push({ kind: 'action', label: 'Run', text: action });
    if (!rows.length) {
      const why = A.setupStateFor(component).label;
      return `<p class="cmd-none">No command for ${esc(A.platform().label)}. ${esc(why)}.</p>`;
    }
    return rows.map(row => `<div class="cmd-line cmd-${row.kind}">
      <span class="cmd-tag">${row.label}</span>
      <code>${esc(row.text)}</code>
      <button type="button" class="cmd-copy" data-copy-cmd="${esc(row.text)}"
        aria-label="Copy the ${row.label.toLowerCase()} command for ${esc(component.name)}">Copy</button>
    </div>`).join('');
  }

  function commandsHTML() {
    const items = A.visibleComponents().filter(c => c.cmd || c.setupRecipe);
    const withCommand = items.filter(c => A.setupCommandFor(c) || A.commandFor(c)).length;
    return `<h2>Command directory</h2><p class="sub">Every indexed command, in full, for the system named below.
      Setup commands install something and come from a reviewed recipe. Run commands are what you use afterwards.
      Click an entry for its source, dependencies and lane.</p>
      ${automaticNotice()}
      ${suggestedNotice()}
      <p class="cmd-count">${withCommand} of ${items.length} entries have a command on
        ${esc(A.platform().label)}. The rest name what is missing.</p>
      <div class="cmd-list">${items.map(c => `<article class="cmd-card">
        <button class="cmd-head" data-comp="${esc(c.id)}">
          <b>${esc(c.name)}</b>
          <span class="src">${esc(A.laneName(c.lane))} &middot; ${esc(c.sub || c.kind)}</span>
        </button>
        <p class="cmd-detail">${esc(c.detail)}</p>
        ${commandRow(c)}
      </article>`).join('')
        || '<p class="empty">No commands match. Clear filters or browse the Index.</p>'}</div>`;
  }

  function automaticNotice() {
    return `<details class="auto-mode-guide"><summary>Automatic skills and enforcement</summary>
      <p>Configure each client once in Easy setup. Supported hooks then inject the workflow without a slash:
      caveman, full output, anti-slop; plan and design; suitable tools and agents, verification, then the first layer again.</p>
      <p>Rules apply to model requests, not to arbitrary terminal programs. Shell actions still require review.
      Web chat needs saved instructions; local models must use the harness launch command. Hooks cannot prevent
      manual file deletion or control a product's internal context compaction.</p>
      <button class="btn" data-copy-auto>Copy exact protected instructions</button>
      <pre class="cmd wrap">${esc(A.autoModeText())}</pre></details>`;
  }

  function lanesHTML(id) {
    const meta = A.TABS.find(t => t.id === id) || { label: id, hint: '' };
    const lanes = A.lanesForTab(id);
    const laneIds = new Set(lanes.map(l => l.id));
    const items = A.visibleComponents().filter(c => laneIds.has(c.lane));
    return `<h2>${esc(meta.label)}</h2>
      <p class="sub">${esc(meta.hint)} ${lanes.length} lane${lanes.length === 1 ? '' : 's'},
      ${items.length} entr${items.length === 1 ? 'y' : 'ies'} after filters.</p>
      <div class="grid">${items.map(c => {
        const ready = A.canBuild(c);
        return `<div class="lane-card" role="button" tabindex="0" data-comp="${esc(c.id)}" data-kind="${esc(c.kind)}">
          ${ready ? `<button class="plus mini${A.state.basket.includes(c.id) ? ' in' : ''}"
            data-add="${esc(c.id)}" title="Add setup to combination">
            ${A.state.basket.includes(c.id) ? '&#10003;' : '+'}</button>`
            : `<span class="src">${esc(A.setupStateFor(c).label)}</span>`}
          <b>${esc(c.name)}</b>
          ${c.owner ? `<span class="owner">${esc(c.owner)}</span>` : ''}
          <p>${esc(c.detail)}</p>
          <span class="src">${esc(A.laneName(c.lane))}${c.sub ? ` · ${esc(c.sub)}` : ''}</span>
        </div>`;
      }).join('') || '<p class="empty">Nothing matches the current filters.</p>'}</div>`;
  }

  /* Four harnesses, and the differences are not cosmetic. Each stands in a
     different place, and the place decides what it can enforce, so every card
     leads with the mechanism and carries the limit next to the capability. A
     list of four similar tools would hide the only thing worth knowing. */
  function harnessHTML() {
    const items = A.harnesses();
    if (!items.length) {
      return `<h2>The harness</h2><p class="empty">No harness data in this payload.
        Run <code>python scripts/build_atlas_data.py</code> to regenerate it.</p>`;
    }
    return `<h2>The harness</h2>
      <p class="sub">A harness is the thing that makes the standing rules arrive without anyone
        remembering to ask for them. There are four, because there are four different places to
        stand, and where a harness stands decides what it can reach. Each card says what it
        enforces, when it is the right one, and what it cannot do.</p>
      <div class="harness-list">${items.map((h, index) => `<article class="harness-card">
        <header>
          <span class="harness-num">${String(index + 1).padStart(2, '0')}</span>
          <div><b>${esc(h.name)}</b><code class="harness-file">${esc(h.file)}</code></div>
        </header>
        <p class="harness-detail">${esc(h.detail)}</p>
        <dl class="harness-meta">
          <div><dt>Use it when</dt><dd>${esc(h.useWhen)}</dd></div>
          <div><dt>What it cannot do</dt><dd>${esc(h.limit)}</dd></div>
        </dl>
        <div class="cmd-line cmd-action">
          <span class="cmd-tag">Check</span>
          <code>${esc(h.check)}</code>
          <button type="button" class="cmd-copy" data-copy-cmd="${esc(h.check)}"
            aria-label="Copy the check command for ${esc(h.name)}">Copy</button>
        </div>
      </article>`).join('')}</div>
      <p class="sub harness-foot">All four inject the same three layers, so nothing here changes
        what the rules say. They differ only in how the rules arrive. The goal harness adds one
        thing on top: a goal that survives the turn, set with <code>/goal</code>,
        <code>\\goal</code> or <code>goal:</code>, and lifted only by the person who set it.</p>`;
  }

  function routesHTML() {
    const routes = A.routesForMachine();
    return `<h2>Hybrid routes</h2>
      <p class="sub">How work is split across models. Verdicts use the hardware from step 3;
      without it, memory-dependent routes say so rather than guessing.</p>
      ${routes.map(r => `<div class="route">
        <b>${esc(r.name)}</b><p>${esc(r.detail)}</p>
        <span class="tag${r.ok ? '' : ' no'}">${esc(r.verdict)} · best for ${esc(r.bestFor)}</span>
        <p class="path">Path: ${r.members.map(m => A.state.byId.has(m)
          ? `<button class="text-link" data-comp="${esc(m)}">${esc(A.state.byId.get(m).name)}</button>` : esc(m)).join(' → ')}</p>
      </div>`).join('')}`;
  }

  function hardwareHTML() {
    const mem = A.usableMemory();
    const chosen = A.platform();
    return `<h2>What this machine can carry</h2>
      <p class="sub">${chosen
        ? `Reading as ${esc(chosen.label)}. ${esc(chosen.note)}`
        : 'Choose your operating system in step 1 for an accurate reading.'}</p>
      <div class="grid">${A.state.data.hardware.map(t => {
        const active = mem && A.tierFor(mem).id === t.id;
        return `<div class="lane-card${active ? ' active' : ''}">
          <b>${esc(t.label)}${active ? ' · this machine' : ''}</b>
          <p><b class="verdict">${esc(t.verdict)}</b><br>${esc(t.detail)}</p>
          ${t.models.length ? `<span class="src">${t.models.map(esc).join(' · ')}</span>` : ''}
        </div>`;
      }).join('')}</div>
      <div class="sec">How the numbers are read</div>
      <p class="sub">${A.state.platform === 'macos'
        ? 'Apple silicon shares one memory pool between CPU and GPU, so VRAM is not a separate budget and the field is disabled. Usable model size sits below the headline RAM.'
        : 'With a discrete GPU the larger of RAM and VRAM decides what can be hosted, because a model runs in one or the other, not both.'}</p>`;
  }

  function basketHTML() {
    const items = A.basketItems();
    const combined = A.combinedCommand();
    const ready = combined.ready || [];
    const blocked = combined.blocked || [];
    return `<h2>Build</h2>
      <p class="sub">${ready.length} setup-ready component${ready.length === 1 ? '' : 's'} produce
      ${combined.commandCount || 0} deduplicated command line${combined.commandCount === 1 ? '' : 's'}.
      The copy block contains commands only.</p>
      ${automaticNotice()}
      ${items.length ? `<div class="grid">${items.map(c => `
        <div class="lane-card">
          <button class="plus mini in" data-drop="${esc(c.id)}" title="Remove">&times;</button>
          <b>${esc(c.name)}</b>
          ${c.owner ? `<span class="owner">${esc(c.owner)}</span>` : ''}
          <p>${esc(c.detail)}</p>
          <span class="src">${esc(A.laneName(c.lane))} · ${esc(A.setupStateFor(c).label)}</span>
        </div>`).join('')}</div>` : '<p class="empty">Nothing added yet. Use + on a setup-ready component.</p>'}
      ${setupCommandsSection(items)}
      ${items.length ? '<button class="btn ghost" id="basket-clear">Clear all</button>' : ''}
      ${blocked.length ? `<div class="sec">Not setup-ready on your system</div>
        <p class="empty">These have no complete setup recipe for ${esc((A.platform() || {}).label || 'the chosen system')}:</p>
        <div class="conn">${blocked.map(item => `<span class="route">${esc(item)}</span>`).join('')}</div>` : ''}`;
  }

  /* The script for the system you picked, and only that one.
   *
   * This showed all five platforms at once, which was the wrong call: you choose
   * your system in step 1, so Build answering with five scripts makes you find
   * yours among four you cannot run. The others stay reachable behind a closed
   * disclosure, because handing a teammate the macOS version is genuinely useful,
   * but nothing about another system is on screen unless you ask for it. */
  function setupCommandsSection(items) {
    if (!items.length) return '';
    const chosen = A.platform();
    if (!chosen) {
      return `<div class="sec">Setup commands</div>
        <p class="empty">Choose your operating system in step 1 and the script for it
        appears here.</p>`;
    }
    const all = A.combinedCommandAll();
    const mine = all.find(entry => entry.current);
    const others = all.filter(entry => !entry.current);

    return `<div class="sec">Setup commands for ${esc(chosen.label)}</div>
      <p class="sub">Written for ${esc(chosen.label)} (${esc(chosen.shell)}), because that is
      what you selected. Commands only, so it pastes straight into a shell.</p>
      ${mine ? scriptBlock(mine) : ''}
      ${others.length ? `<details class="otheros">
        <summary>Need it for a different system?</summary>
        <p class="sub">Same components, written for the other platforms. Useful when handing
        the combination to someone who does not run ${esc(chosen.label)}.</p>
        ${others.map(scriptBlock).join('')}
      </details>` : ''}`;
  }

  /** One platform's script, with its own copy button and its own skip list. */
  function scriptBlock(entry) {
    const label = entry.platform ? entry.platform.label : entry.id;
    const shell = entry.platform ? entry.platform.shell : '';
    return `<div class="scriptblock${entry.current ? ' current' : ''}">
      <div class="scripthead">
        <b>${esc(label)}</b>
        <span class="scriptshell">${esc(shell)}</span>
        ${entry.current ? '<span class="scripttag">your system</span>' : ''}
        <span class="scriptcount">${entry.ok ? `${entry.commandCount} command(s)` : 'nothing runnable'}</span>
      </div>
      ${entry.ok
        ? `<div class="cmd wrap"><button class="copy" data-copy-script="${esc(entry.id)}">copy</button>${esc(entry.text)}</div>`
        : `<p class="empty">${esc(entry.text)}</p>`}
      ${(entry.blocked || []).length
        ? `<p class="scriptskip">Not in this script: ${entry.blocked.map(esc).join('; ')}</p>`
        : ''}
    </div>`;
  }

  /* --------------------------------------------------- easy setup */

  /* Four answers to "new machine, what do I run?".
   *
   * Build already assembles a script, but only once you know which nodes to pick
   * and in what order. A profile is that knowledge written down: an ordered list
   * of the same reviewed recipes, nothing extra, nothing the Build tab could not
   * produce by hand. The client picker and the RAM in step 3 fill in the two
   * steps whose right answer is not the same for everyone. */

  function easyHTML() {
    const profiles = A.profiles();
    const chosen = A.platform();
    const tier = A.currentTier();
    // An empty checkbox state is deliberate: web-only users must not install all clients.
    if (!Array.isArray(A.state.surfaceIds)) A.state.surfaceIds = [];
    const available = A.availableSurfaces();
    const selected = A.selectedSurfaces();

    if (!profiles.length) {
      return `<h2>Easy setup</h2>
        <p class="empty">This data file carries no profiles.</p>`;
    }

    return `<h2>Easy setup</h2>
      <p class="sub">Select every chat or coding client you use, then a profile. The script
      is the same reviewed recipes the Build tab uses, ordered so each step has what the
      next one needs.</p>

      <div class="surface-groups">${(A.state.data.surfaceGroups || []).map(group => `<fieldset>
        <legend>${esc(group.name)}</legend><p class="sub">${esc(group.note)}</p>
        ${available.filter(s => s.group === group.id).map(s => `<label class="surface-choice">
          <input type="checkbox" data-surface="${esc(s.id)}" ${A.state.surfaceIds.includes(s.id) ? 'checked' : ''}>
          <span><b>${esc(s.name)}</b><small>${esc(s.detail)}</small>
          <small>${esc((s.enforcement || {}).label)}: ${esc((s.enforcement || {}).detail)}</small></span></label>`).join('')
          || '<p class="empty">Enter scan results above. Only models within the recorded RAM requirement are offered.</p>'}</fieldset>`).join('')}</div>
      ${selected.filter(s => s.runs === 'connect').map(s => `<article class="surface-instructions"><h3>${esc(s.name)}</h3>
        <p>${esc(s.detail)}</p><p>Save the protected instructions in <b>${esc(s.target)}</b>.</p></article>`).join('')}
      ${selected.filter(s => s.launchCommands && chosen).map(s => `<article><h3>Launch ${esc(s.name)} with automatic rules</h3>
        <p>Use after its install profile below. Direct Ollama calls do not receive these instructions.</p>
        <div class="cmd wrap"><button class="copy" data-copy-launch="${esc(s.id)}">copy</button>
        ${esc(s.launchCommands[chosen.id])}</div></article>`).join('')}
      ${automaticNotice()}

      ${chosen ? '' : `<p class="empty">Choose your operating system in step 1 first. Every
        profile writes a different script for each system, so there is nothing to show until
        you pick one.</p>`}
      ${tier ? `<p class="sub">Model steps resolve to the ${esc(tier.label)} tier:
        ${esc((tier.models || []).join(', ') || 'no tags at this size')}.</p>`
        : `<p class="sub">No RAM entered in step 3, so the model steps stay empty rather than
        guessing a tag this machine may not be able to hold.</p>`}

      ${profiles.map(profile => easyProfile(profile, Boolean(chosen))).join('')}`;
  }

  function easyProfile(profile, hasPlatform) {
    const result = hasPlatform ? A.profileScriptFor(profile.id) : null;
    const steps = (result && result.steps) || A.resolveProfile(profile).recipes;
    const notes = (result && result.notes) || A.resolveProfile(profile).notes;
    const open = profile.id === 'software-developer' ? ' open' : '';
    return `<details class="easy"${open}>
      <summary><b>${esc(profile.name)}</b> <span class="src">${esc(profile.summary)}</span></summary>
      <p>${esc(profile.detail)}</p>
      <p class="sub">Best for: ${esc(profile.bestFor)}</p>
      <ol class="easysteps">${steps.map(recipe =>
        `<li><b>${esc(recipe.name)}</b> <span class="src">${esc(recipe.detail)}</span></li>`).join('')
        || '<li class="empty">No step in this profile resolved.</li>'}</ol>
      ${notes.length ? `<p class="scriptskip">${notes.map(esc).join(' ')}</p>` : ''}
      ${result
        ? (result.ok
          ? `<div class="cmd wrap"><button class="copy" data-copy-profile="${esc(profile.id)}"
              >copy</button>${esc(result.text)}</div>
            <p class="sub">${result.commandCount} command line(s) for
            ${esc(result.platform.label)} (${esc(result.platform.shell)}).</p>`
          : `<p class="empty">${esc(result.text)}</p>`)
        : ''}
      ${result && (result.blocked || []).length
        ? `<p class="scriptskip">Not in this script: ${result.blocked.map(esc).join('; ')}</p>`
        : ''}
    </details>`;
  }

  function customHTML() {
    const mine = A.state.customLanes;
    return `<h2>Custom lanes</h2>
      <p class="sub">Add a lane of your own. It mixes with the generated lanes everywhere in this
      design. Stored in this browser only; nothing is transmitted.</p>
      <div class="form">
        <label for="cl-name">Lane name</label>
        <input id="cl-name" type="text" placeholder="e.g. Robotics telemetry">
        <label for="cl-fam">Family</label>
        <select id="cl-fam">${A.state.data.families.map(f =>
          `<option value="${esc(f.id)}">${esc(f.name)}</option>`).join('')}</select>
        <label for="cl-kind">Kind</label>
        <select id="cl-kind">${['capability', 'instruction', 'knowledge', 'control', 'model', 'delivery']
          .map(k => `<option value="${k}">${k}</option>`).join('')}</select>
        <label for="cl-desc">Description</label>
        <textarea id="cl-desc" placeholder="What belongs in this lane?"></textarea>
        <button class="btn" id="cl-add">Add lane</button>
        <div class="err" id="cl-err"></div>
      </div>
      <div class="sec">Your lanes (${mine.length})</div>
      <div class="grid">${mine.map(l => `<div class="lane-card">
        <b>${esc(l.name)}</b><p>${esc(l.description)}</p>
        <span class="src">${esc(l.family)} · ${esc(l.kind)}</span>
        <button class="btn ghost" data-del="${esc(l.id)}">Remove</button>
      </div>`).join('') || '<p class="empty">None yet.</p>'}</div>`;
  }

  function suggestHTML() {
    const list = A.state.suggestions;
    return `<h2>Suggest a lane or feed</h2>
      <p class="sub">Propose something the catalog is missing. Saved in this browser, then copy the
      list into an issue. Nothing is sent anywhere from this page.</p>
      <div class="form">
        <label for="sg-name">Lane or feed</label>
        <input id="sg-name" type="text" placeholder="e.g. Embedded ML on microcontrollers">
        <label for="sg-link">Link (optional)</label>
        <input id="sg-link" type="text" placeholder="https://…">
        <label for="sg-why">Why it belongs</label>
        <textarea id="sg-why"></textarea>
        <button class="btn" id="sg-add">Add suggestion</button>
        <div class="err" id="sg-err"></div>
      </div>
      <div class="sec">Saved (${list.length})</div>
      ${list.length
        ? `<div class="cmd wrap"><button class="copy" data-copy>copy</button>${esc(A.exportSuggestions())}</div>`
        : '<p class="empty">None yet.</p>'}`;
  }

  function wirePane() {
    document.querySelectorAll('[data-comp]').forEach(card => {
      card.onclick = e => {
        if (e.target.closest('[data-add]')) return;
        A.select(card.dataset.comp);
        if (hooks.onSelect) hooks.onSelect(card.dataset.comp);
      };
      if (card.tagName !== 'BUTTON') card.onkeydown = e => {
        if (e.target === card && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); card.click(); }
      };
    });
    document.querySelectorAll('[data-open-lane]').forEach(b => {
      b.onclick = () => A.selectLane(b.dataset.openLane);
    });
    document.querySelectorAll('[data-surface]').forEach(input => {
      input.onchange = () => { A.toggleSurface(input.dataset.surface); renderStage(); };
    });
    document.querySelectorAll('[data-copy-auto]').forEach(b => {
      b.onclick = async () => { b.textContent = await A.copy(A.autoModeText()) ? 'Copied exact instructions' : 'Select the instructions below to copy'; };
    });
    document.querySelectorAll('[data-copy-launch]').forEach(b => {
      b.onclick = async () => {
        const surface = A.selectedSurfaces().find(s => s.id === b.dataset.copyLaunch);
        if (surface && A.platform()) b.textContent = await A.copy(surface.launchCommands[A.state.platform]) ? 'copied' : 'select it';
      };
    });
    document.querySelectorAll('[data-add]').forEach(b => {
      b.onclick = e => {
        e.stopPropagation();
        const id = b.dataset.add;
        A.state.basket.includes(id) ? A.removeFromBasket(id) : A.addToBasket(id);
        draw();
      };
    });
    document.querySelectorAll('[data-drop]').forEach(b => {
      b.onclick = () => { A.removeFromBasket(b.dataset.drop); draw(); };
    });
    document.querySelectorAll('[data-client]').forEach(btn => {
      btn.onclick = () => { A.setProfileClient(btn.dataset.client); draw(); };
    });
    document.querySelectorAll('[data-copy-cmd]').forEach(btn => {
      // The command is on the button because the directory renders it inline;
      // there is no second lookup that could disagree with what is on screen.
      btn.onclick = async () => {
        btn.textContent = (await A.copy(btn.dataset.copyCmd)) ? 'copied' : 'select it';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1400);
      };
    });
    document.querySelectorAll('[data-copy-profile]').forEach(btn => {
      btn.onclick = async () => {
        const result = A.profileScriptFor(btn.dataset.copyProfile);
        if (!result.ok) return;
        btn.textContent = (await A.copy(result.text)) ? 'copied' : 'select it';
        setTimeout(() => { btn.textContent = 'copy'; }, 1400);
      };
    });
    document.querySelectorAll('[data-copy-script]').forEach(btn => {
      btn.onclick = async () => {
        const entry = A.combinedCommandAll().find(e => e.id === btn.dataset.copyScript);
        if (!entry || !entry.ok) return;
        btn.textContent = (await A.copy(entry.text)) ? 'copied' : 'select it';
        setTimeout(() => { btn.textContent = 'copy'; }, 1400);
      };
    });
    const clearBasket = document.getElementById('basket-clear');
    if (clearBasket) clearBasket.onclick = () => { A.clearBasket(); draw(); };

    const pane = document.querySelector('.pane');
    if (pane) {
      const text = tab === 'basket' ? A.combinedCommand().text
        : tab === 'suggest' ? A.exportSuggestions() : '';
      wireCopy(pane, text);
    }

    const add = document.getElementById('cl-add');
    if (add) add.onclick = () => {
      const r = A.addCustomLane({ name: val('cl-name'), family: val('cl-fam'),
                                  kind: val('cl-kind'), description: val('cl-desc') });
      document.getElementById('cl-err').textContent = r.ok ? '' : r.error;
      if (r.ok) draw();
    };
    document.querySelectorAll('[data-del]').forEach(b => {
      b.onclick = () => { A.removeCustomLane(b.dataset.del); draw(); };
    });
    const sg = document.getElementById('sg-add');
    if (sg) sg.onclick = () => {
      const r = A.addSuggestion({ name: val('sg-name'), why: val('sg-why'), link: val('sg-link') });
      document.getElementById('sg-err').textContent = r.ok ? '' : r.error;
      if (r.ok) draw();
    };
  }


  /* ------------------------------------------------------- map popover */

  /* Clicking a node opens this where the click happened, rather than only
     updating the side panel. It carries the same facts the panel does, plus the
     plus button, so a combination can be built without leaving the map. */

  function closePopover() {
    const existing = document.getElementById('pop');
    if (existing) existing.remove();
  }

  function popover(x, y, componentId) {
    closePopover();
    const d = A.detailFor(componentId);
    if (!d) return;

    const node = document.createElement('div');
    node.id = 'pop';
    node.className = 'pop';
    node.innerHTML = `
      <div class="pophead">
        <div>
          <div class="popname">${esc(d.name)}</div>
          ${d.owner ? `<div class="downer">${esc(d.owner)}</div>` : ''}
        </div>
        <div class="popbtns">
          ${d.setupCommand ? `<button class="plus${d.inBasket ? ' in' : ''}" data-pop-add
            title="${d.inBasket ? 'Remove setup from the combination' : 'Add setup to Build'}"
            >${d.inBasket ? '&#10003;' : '+'}</button>`
            : `<span class="dkind sub">${esc(d.setupState.label)}</span>`}
          <button class="popclose" data-pop-close title="Close">&times;</button>
        </div>
      </div>
      <div class="poprow">
        <span class="dkind" data-kind="${esc(d.kind)}">${esc(d.kind)}</span>
        ${d.sub ? `<span class="dkind sub">${esc(d.sub)}</span>` : ''}
      </div>
      <p class="popdesc">${esc(d.detail)}</p>
      <div class="popmeta">${esc(d.lane)}${d.laneSource ? ` · <code>${esc(d.laneSource)}</code>` : ''}</div>
      ${commandBlock(d)}
      ${d.connections.length
        ? `<div class="popsec">Connects to ${d.connections.length}</div>
           <div class="popconn">${d.connections.slice(0, 6).map(c =>
             `<button data-pop-go="${esc(c.id)}">${esc(c.name)}</button>`).join('')}</div>`
        : ''}
      ${A.state.basket.length
        ? `<div class="popfoot">${A.state.basket.length} in your combination ·
           <button data-pop-build>see the script</button></div>` : ''}`;

    document.body.appendChild(node);

    // Keep it on screen: flip rather than overflow the viewport.
    const box = node.getBoundingClientRect();
    const pad = 12;
    let left = x + 14;
    let top = y + 14;
    if (left + box.width > window.innerWidth - pad) left = Math.max(pad, x - box.width - 14);
    if (top + box.height > window.innerHeight - pad) top = Math.max(pad, window.innerHeight - box.height - pad);
    node.style.left = `${left}px`;
    node.style.top = `${top}px`;

    wireCopy(node, d.setupCommand || d.command);
    node.querySelector('[data-pop-close]').onclick = closePopover;
    const add = node.querySelector('[data-pop-add]');
    if (add) add.onclick = () => {
        d.inBasket ? A.removeFromBasket(d.id) : A.addToBasket(d.id);
        popover(x, y, componentId);
        tabsUI();
        detailUI();
      };
    node.querySelectorAll('[data-pop-go]').forEach(b => {
      b.onclick = () => {
        A.select(b.dataset.popGo);
        popover(x, y, b.dataset.popGo);
        if (hooks.onSelect) hooks.onSelect(b.dataset.popGo);
      };
    });
    const build = node.querySelector('[data-pop-build]');
    if (build) build.onclick = () => { closePopover(); tab = 'basket'; draw(); };
  }

  // One dismissal path for every design: click away, or press Escape.
  if (typeof document !== 'undefined') {
    document.addEventListener('pointerdown', e => {
      if (!e.target.closest('#pop') && !e.target.closest('[data-node]')) closePopover();
    }, true);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closePopover(); });
  }

  /* ------------------------------------------------------------ draw */

  /* Base styling for elements this module invents.
   *
   * Every design carries its own CSS, which is the point: they are meant to look
   * different. But a design written before a control existed cannot style it, so
   * a new control arrives unstyled wherever nobody has been back - the client
   * picker rendered as one run-on line of text in six designs.
   *
   * Specificity was the whole difficulty. :where() was the first attempt, at zero
   * specificity so any design rule wins; it lost to the plain `button {}` reset
   * several designs carry, and the chips stayed unstyled. So these are ordinary
   * two-class selectors: high enough to beat an element reset, low enough that a
   * design overrides them by naming the same classes. Colours come from the
   * variables every design already defines, with a fallback for any that do not,
   * so this inherits each theme instead of fighting it.
   */
  const BASE_STYLE_ID = 'atlas-panes-base';
  const BASE_STYLE = `
    *{scrollbar-width:thin;scrollbar-color:var(--accent,#b65039) var(--bg,#181818)}
    *::-webkit-scrollbar{width:10px;height:10px}
    *::-webkit-scrollbar-track{background:var(--bg,#181818)}
    *::-webkit-scrollbar-thumb{background:var(--accent,#b65039);border:2px solid var(--bg,#181818);border-radius:8px}
    #tabs{overflow-x:auto;flex-wrap:wrap}
    #tabs .tab,.pane button,#filters .chip,.conn button{min-height:44px}
    .pane{font-size:14px;line-height:1.55;min-width:0}
    .pane :is(h2,h3,p){text-wrap:pretty}
    .pane .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:16px}
    .pane .lane-card{color:var(--ink,#eee);background:var(--panel,var(--bg,#181818));text-align:left;font:inherit;min-width:0;overflow-wrap:anywhere}
    .pane .lane-card p{line-height:1.55}
    .pane .lane-card b{display:block}
    .pane .lane-card[data-comp],.index-lane{cursor:pointer}
    .text-link{font:inherit;color:var(--accent,#b65039);background:transparent;border:0;text-align:left;text-decoration:underline;cursor:pointer;min-height:44px}
    :is(#side,#stage,#filters) :focus-visible{outline:2px solid var(--accent,#b65039);outline-offset:3px}
    .filter-explanations{max-width:90ch;font-size:14px;line-height:1.55}
    .pane .suggested{max-width:80ch;margin:10px 0 14px;padding:10px 13px;font-size:13px;line-height:1.55;
      border-left:3px solid var(--accent,#b65039);border-radius:0 8px 8px 0;
      background:color-mix(in srgb, var(--accent,#b65039) 10%, transparent)}
    .pane .suggested b{font-weight:700}
    .cmd-count{margin:0 0 14px;color:var(--dim,#9aa);font-size:12.5px}
    .cmd-list{display:flex;flex-direction:column;gap:10px}
    .cmd-card{padding:13px 14px;border:1px solid var(--line,#555);border-radius:10px;min-width:0}
    .cmd-head{display:flex;flex-direction:column;gap:3px;width:100%;padding:0;border:0;background:transparent;
      color:inherit;font:inherit;text-align:left;cursor:pointer;min-height:0}
    .cmd-head b{font-size:14px}
    .cmd-head .src{color:var(--dim,#9aa);font-size:11px}
    .cmd-detail{margin:6px 0 9px;color:var(--dim,#9aa);font-size:12.5px;line-height:1.5;max-width:80ch}
    .cmd-line{display:flex;align-items:flex-start;gap:8px;margin-top:6px;flex-wrap:wrap}
    .cmd-tag{flex:none;padding:3px 7px;border-radius:5px;font:700 9.5px ui-monospace,monospace;
      letter-spacing:.06em;text-transform:uppercase;background:var(--panel-2,#222);color:var(--dim,#9aa)}
    .cmd-setup .cmd-tag{background:color-mix(in srgb, var(--accent,#b65039) 22%, transparent);color:var(--accent,#b65039)}
    .cmd-action .cmd-tag{background:var(--panel-3,#2a2a2a);color:var(--ink-2,#ccc)}
    .orient{margin-bottom:14px;border:1px solid var(--line,#555);border-radius:10px;overflow:hidden}
    .orient-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:9px 11px}
    .orient-toggle{flex:1;min-width:0;display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;
      padding:0;border:0;background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer}
    .orient-mark{flex:none;width:18px;height:18px;display:inline-grid;place-items:center;
      border:1px solid var(--line,#555);border-radius:5px;font-size:12px;line-height:1}
    .orient-toggle b{font-size:13.5px}
    .orient-sub{color:var(--dim,#9aa);font-size:11.5px}
    .orient-level{flex:none;display:flex;gap:2px;padding:2px;border-radius:7px;background:var(--panel-2,#222)}
    .orient-level button{min-height:30px;padding:0 10px;border:0;border-radius:5px;background:transparent;
      color:var(--dim,#9aa);font:inherit;font-size:11px;font-weight:700;cursor:pointer}
    .orient-level button[aria-pressed="true"]{background:var(--accent,#b65039);color:#fff}
    .orient-body{padding:0 11px 12px;border-top:1px solid var(--line,#555)}
    .orient-lede{margin:11px 0;font-size:13px;line-height:1.6;max-width:78ch}
    .orient-steps{margin:0 0 12px;padding-left:20px;display:flex;flex-direction:column;gap:5px;
      font-size:12.5px;line-height:1.55;color:var(--dim,#9aa);max-width:78ch}
    .orient-steps b{color:var(--ink,#eee)}
    .orient-terms-head{margin:0 0 7px;color:var(--dim,#9aa);font:700 9.5px ui-monospace,monospace;
      letter-spacing:.1em;text-transform:uppercase}
    .orient-terms dl{margin:0;display:grid;gap:7px;
      grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr))}
    .orient-terms dl div{min-width:0}
    .orient-terms dt{font-size:12px;font-weight:700;color:var(--accent,#b65039)}
    .orient-terms dd{margin:1px 0 0;font-size:11.5px;line-height:1.5;color:var(--dim,#9aa)}
    .chip-why{display:block;margin-top:2px;font-size:10.5px;line-height:1.4;opacity:.75}
    .cmd-line code{flex:1;min-width:0;padding:7px 9px;border-radius:7px;background:#090a0c;color:#c8f8e0;
      font:11.5px/1.6 ui-monospace,"Cascadia Code",monospace;font-variant-ligatures:none;
      white-space:pre-wrap;overflow-wrap:anywhere}
    .cmd-copy{flex:none;min-height:34px;padding:0 11px;border:1px solid var(--line,#555);border-radius:7px;
      background:transparent;color:inherit;font:inherit;font-size:11px;cursor:pointer}
    .cmd-copy:hover{border-color:var(--accent,#b65039)}
    .cmd-none{margin:6px 0 0;color:var(--dim,#9aa);font-size:12px;font-style:italic}
    .harness-list{display:flex;flex-direction:column;gap:12px}
    .harness-card{padding:16px;border:1px solid var(--line,#555);border-radius:12px;min-width:0}
    .harness-card header{display:flex;align-items:baseline;gap:12px;margin-bottom:9px}
    .harness-num{flex:none;color:var(--accent,#b65039);font:700 11px ui-monospace,monospace;letter-spacing:.08em}
    .harness-card header b{display:block;font-size:15px}
    .harness-file{display:block;margin-top:2px;color:var(--dim,#9aa);
      font:600 11px ui-monospace,"Cascadia Code",monospace;font-variant-ligatures:none}
    .harness-detail{margin:0 0 11px;font-size:13.5px;line-height:1.6;max-width:82ch}
    .harness-meta{margin:0 0 11px;display:grid;gap:9px;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))}
    .harness-meta dt{color:var(--dim,#9aa);font:700 9.5px ui-monospace,monospace;
      letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
    .harness-meta dd{margin:0;font-size:12.5px;line-height:1.5}
    .harness-foot{margin-top:14px}
    .harness-foot code{padding:1px 5px;border-radius:4px;background:var(--panel-2,#222);
      font:600 11.5px ui-monospace,monospace;font-variant-ligatures:none}
    @media(max-width:640px){.cmd-line{flex-direction:column}.cmd-copy{align-self:flex-start}}
    .filter-explanations p{margin:8px 0}
    .surface-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px;margin:20px 0}
    .surface-groups fieldset{border:1px solid var(--line,#555);border-radius:8px;padding:16px;min-width:0}
    .surface-groups legend{font-weight:700;padding:0 8px}
    .surface-choice{display:flex;gap:12px;align-items:flex-start;padding:12px 0;cursor:pointer;border-bottom:1px solid var(--line,#555)}
    .surface-choice input{width:20px;height:20px;accent-color:var(--accent,#b65039);flex-shrink:0;margin:4px 0}
    .surface-choice small{display:block;line-height:1.5;margin-top:6px;font-size:13px}
    .surface-instructions{padding:16px;border:1px solid var(--line,#555);margin:12px 0}
    .store-guide,.auto-mode-guide{margin:20px 0;padding:16px;border:1px solid var(--line,#555);border-radius:8px}
    .store-guide summary,.auto-mode-guide summary{cursor:pointer;min-height:44px;display:flex;align-items:center;font-weight:700}
    .auto-mode-guide pre{max-height:320px;overflow:auto}
    .pane .cmd,.pop .cmd,#side .cmd{white-space:pre-wrap;overflow-wrap:anywhere;min-width:0}
    #side .conn small{white-space:normal;line-height:1.45}
    .easyclients{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 6px}
    .easyclients .chip{min-height:30px;padding:5px 12px;font-size:13px;line-height:1.3;
      border:1px solid var(--line,#3a3a3a);border-radius:999px;background:transparent;
      color:var(--dim,#999);white-space:nowrap;cursor:pointer}
    .easyclients .chip:hover{border-color:var(--accent,#c33);color:var(--ink,#eee)}
    .easyclients .chip.on{background:var(--accent,#c33);border-color:var(--accent,#c33);
      color:var(--bg,#111);font-weight:800}
    .pane .easy{border:1px solid var(--line,#3a3a3a);border-radius:10px;
      padding:10px 14px;margin:10px 0}
    .pane .easy>summary{cursor:pointer;display:flex;gap:10px;align-items:baseline;
      flex-wrap:wrap}
    .pane .easysteps{margin:10px 0;padding-left:22px;display:flex;flex-direction:column;
      gap:6px}
    .frow .subnotes{display:flex;flex-direction:column;gap:4px;min-width:0;flex:1}
    .frow .subnote{color:var(--dim,#999);line-height:1.5;max-width:74ch}
    .frow .subnote b{color:var(--ink,#eee)}
  `;

  function injectBaseStyle() {
    if (document.getElementById(BASE_STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = BASE_STYLE_ID;
    style.textContent = BASE_STYLE;
    // First child of head, so a design's own stylesheet comes after it and wins
    // on equal specificity as well as on higher.
    document.head.insertBefore(style, document.head.firstChild);
  }

  function draw() {
    injectBaseStyle();
    setupUI();
    tabsUI();
    filtersUI();
    renderStage();
    detailUI();
  }

  function renderStage() {
    const stage = document.getElementById('stage');
    if (stage) {
      if (tab === 'map') {
        if (hooks.renderMap) hooks.renderMap(stage);
      } else {
        const pane = document.createElement('div');
        pane.className = 'pane';
        pane.innerHTML =
          tab === 'index' ? indexHTML() :
          tab === 'commands' ? commandsHTML() :
          tab === 'harness' ? harnessHTML() :
          tab === 'routes' ? routesHTML() :
          tab === 'hardware' ? hardwareHTML() :
          tab === 'basket' ? basketHTML() :
          tab === 'easy' ? easyHTML() :
          tab === 'custom' ? customHTML() :
          tab === 'suggest' ? suggestHTML() :
          lanesHTML(tab);
        stage.innerHTML = '';
        stage.appendChild(pane);
        wirePane();
      }
    }
  }

  function fail(err) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="pane"><h2>Could not load the atlas data</h2>
      <p class="sub">${esc(err.message)}</p>
      <p class="sub">Re-run <code>python scripts/build_atlas_data.py</code> to regenerate
      <code>atlas-data.js</code>, which is what this page reads.</p></div>`;
  }

  function mount(options) {
    hooks = options || {};
    A.init('atlas-data.json').then(() => {
      draw();
      A.on(() => { detailUI(); syncFilterChips(); });
    }).catch(fail);
  }

  return { mount, draw, esc, detailUI, filtersUI, syncFilterChips, popover, closePopover,
           get tab() { return tab; }, set tab(v) { tab = v; } };
})();

/* Published on window as well as the script-scope binding.
   A top level `const` in a classic script is script-scoped, not a property
   of window, so `window.AtlasPanes` was undefined while the bare `AtlasPanes`
   worked. atlas-exhibition.js reads these through window, so its guard
   `if (!A || !P) return;` fired on every call and workspace() built nothing.
   That is why d31 rendered a root map with no atlas behind it, and why the
   Command center button on the other exhibition designs revealed the atlas
   without ever switching the tab. */
if (typeof window !== 'undefined') window.AtlasPanes = AtlasPanes;
