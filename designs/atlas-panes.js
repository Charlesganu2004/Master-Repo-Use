/* Shared panes for every atlas design.
 *
 * The tabs, the detail panel and the hardware bar must say the same thing in all
 * five designs, so they are written once here. Each design supplies its own CSS
 * and its own map visualization; identical markup under different stylesheets
 * looks nothing alike, which is the point.
 *
 * A design provides:
 *   AtlasPanes.mount({ renderMap, onSelect })
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

  /* ------------------------------------------------------------ tabs */

  function tabsUI() {
    const host = document.getElementById('tabs');
    if (!host) return;
    host.innerHTML = '';
    A.TABS.forEach(t => {
      const b = document.createElement('button');
      b.className = 'tab';
      b.textContent = t.label;
      b.title = t.hint;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', String(t.id === tab));
      b.onclick = () => { tab = t.id; draw(); };
      host.appendChild(b);
    });
  }

  /* -------------------------------------------------- detail panel */

  function detailUI() {
    const side = document.getElementById('side');
    if (!side) return;
    const d = A.state.selected ? A.detailFor(A.state.selected) : null;
    if (!d) {
      side.innerHTML = `<div class="sec">Component detail</div>
        <p class="empty">Select any component to see what it is, which lane it sits in,
        what it connects to, its hybrid routes, and the exact command to use it.</p>`;
      return;
    }
    const cmd = d.command;
    side.innerHTML = `
      <div class="dname">${esc(d.name)}</div>
      <span class="dkind" data-kind="${esc(d.kind)}">${esc(d.kind)}</span>
      <p class="ddesc">${esc(d.detail)}</p>
      <div class="meta">
        Lane: <b>${esc(d.lane)}</b><br>
        ${d.laneSource ? `Source: <code>${esc(d.laneSource)}</code><br>` : ''}
        ${d.siblings} sibling component${d.siblings === 1 ? '' : 's'} in this lane
      </div>
      ${d.laneDescription ? `<p class="meta">${esc(d.laneDescription)}</p>` : ''}
      ${cmd ? `<div class="sec">Command (${esc(A.state.platform)})</div>
        <div class="cmd"><button class="copy" id="cp">copy</button>${esc(cmd)}</div>` : ''}
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

    const cp = document.getElementById('cp');
    if (cp) cp.onclick = async () => {
      cp.textContent = (await A.copy(cmd)) ? 'copied' : 'select it';
      setTimeout(() => { cp.textContent = 'copy'; }, 1400);
    };
    side.querySelectorAll('[data-go]').forEach(b => {
      b.onclick = () => { A.select(b.dataset.go); if (hooks.onSelect) hooks.onSelect(b.dataset.go); };
    });
  }

  /* --------------------------------------------------------- panes */

  function lanesHTML(id) {
    const meta = A.TABS.find(t => t.id === id) || { label: id, hint: '' };
    const lanes = A.lanesForTab(id);
    return `<h2>${esc(meta.label)}</h2>
      <p class="sub">${esc(meta.hint)} ${lanes.length} lane${lanes.length === 1 ? '' : 's'}.</p>
      <div class="grid">${lanes.map(l => `
        <div class="lane-card" data-lane="${esc(l.id)}" data-kind="${esc(l.kind)}">
          <b>${esc(l.name)}</b>
          <p>${esc(l.description)}</p>
          <span class="src">${esc(l.source)} · ${l.count} item${l.count === 1 ? '' : 's'}</span>
        </div>`).join('') || '<p class="empty">No lanes in this tab yet.</p>'}</div>`;
  }

  function routesHTML() {
    const routes = A.routesForMachine();
    return `<h2>Hybrid routes</h2>
      <p class="sub">How work is split across models. Verdicts use the RAM entered in the bar
      above; without it, RAM-dependent routes say so rather than guessing.</p>
      ${routes.map(r => `<div class="route">
        <b>${esc(r.name)}</b><p>${esc(r.detail)}</p>
        <span class="tag${r.ok ? '' : ' no'}">${esc(r.verdict)} · best for ${esc(r.bestFor)}</span>
        <p class="path">Path: ${r.members.map(m => esc(A.state.byId.has(m) ? A.state.byId.get(m).name : m)).join(' → ')}</p>
      </div>`).join('')}`;
  }

  function hardwareHTML() {
    const ram = A.state.ram;
    return `<h2>What this machine can carry</h2>
      <p class="sub">Run the scan command in the bar above first. It reports RAM, OS and GPU,
      which is what decides whether a local model is realistic. Models are held in memory,
      so RAM is the binding constraint, not disk.</p>
      <div class="grid">${A.state.data.hardware.map(t => {
        const active = ram && A.tierFor(ram).id === t.id;
        return `<div class="lane-card${active ? ' active' : ''}">
          <b>${esc(t.label)}${active ? ' · this machine' : ''}</b>
          <p><b class="verdict">${esc(t.verdict)}</b><br>${esc(t.detail)}</p>
          ${t.models.length ? `<span class="src">${t.models.map(esc).join(' · ')}</span>` : ''}
        </div>`;
      }).join('')}</div>`;
  }

  function customHTML() {
    const mine = A.state.customLanes;
    return `<h2>Custom lanes</h2>
      <p class="sub">Add a lane of your own. It mixes with the generated lanes everywhere in
      this design. Stored in this browser only; nothing is transmitted.</p>
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
      <p class="sub">Propose something the catalog is missing. Saved in this browser, then copy
      the list into an issue. Nothing is sent anywhere from this page.</p>
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
        ? `<div class="cmd wrap"><button class="copy" id="sg-copy">copy all</button>${esc(A.exportSuggestions())}</div>`
        : '<p class="empty">None yet.</p>'}`;
  }

  function wirePane() {
    document.querySelectorAll('[data-lane]').forEach(card => {
      card.onclick = () => {
        const first = A.state.components.find(c => c.lane === card.dataset.lane);
        if (first) { tab = 'map'; A.select(first.id); draw(); if (hooks.onSelect) hooks.onSelect(first.id); }
      };
    });
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
    const cp = document.getElementById('sg-copy');
    if (cp) cp.onclick = async () => {
      cp.textContent = (await A.copy(A.exportSuggestions())) ? 'copied' : 'select it';
      setTimeout(() => { cp.textContent = 'copy all'; }, 1400);
    };
  }

  /* ---------------------------------------------------- hardware bar */

  function hwUI() {
    const scan = document.getElementById('scan');
    if (scan) {
      const cmd = A.scanCommand();
      scan.textContent = cmd;
      scan.onclick = async () => {
        const ok = await A.copy(cmd);
        scan.textContent = ok ? 'copied, run it in your terminal' : 'select the text to copy';
        setTimeout(() => { scan.textContent = cmd; }, 1700);
      };
    }
    const ram = document.getElementById('ram');
    if (!ram) return;
    if (A.state.ram) ram.value = A.state.ram;
    const show = () => {
      const t = A.state.ram ? A.tierFor(A.state.ram) : null;
      const el = document.getElementById('tier');
      if (el) el.textContent = t ? t.verdict : 'not set';
    };
    ram.oninput = () => { A.setRam(ram.value); show(); };
    show();
  }

  /* ------------------------------------------------------------ draw */

  function draw() {
    tabsUI();
    const stage = document.getElementById('stage');
    if (!stage) return;
    if (tab === 'map') {
      if (hooks.renderMap) hooks.renderMap(stage);
    } else {
      const pane = document.createElement('div');
      pane.className = 'pane';
      pane.innerHTML =
        tab === 'routes' ? routesHTML() :
        tab === 'hardware' ? hardwareHTML() :
        tab === 'custom' ? customHTML() :
        tab === 'suggest' ? suggestHTML() :
        lanesHTML(tab);
      stage.innerHTML = '';
      stage.appendChild(pane);
      wirePane();
    }
    detailUI();
  }

  function fail(err) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="pane"><h2>Could not load the atlas data</h2>
      <p class="sub">${esc(err.message)}</p>
      <p class="sub">This page fetches <code>atlas-data.json</code>, which browsers block over
      <code>file://</code>. Serve the folder over HTTP instead:</p>
      <div class="cmd">python -m http.server 8000</div></div>`;
  }

  function mount(options) {
    hooks = options || {};
    A.init('atlas-data.json').then(() => {
      hwUI();
      draw();
      A.on(() => detailUI());
    }).catch(fail);
  }

  return { mount, draw, esc, detailUI, get tab() { return tab; }, set tab(v) { tab = v; } };
})();
