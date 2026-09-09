/* Immersive first views for designs 16 through 30.
 *
 * Each page still mounts AtlasCore and AtlasPanes underneath this layer. The
 * exhibition view is the first screen, built from the same generated data, and
 * "Open full Atlas" reveals the complete filters, setup, routes, and Build UI.
 * This keeps the operational contract while letting each concept own a truly
 * different information architecture instead of repeating one control rail.
 */
(function () {
  'use strict';

  const DATA = window.__ATLAS_DATA__ || {};
  const LANES = DATA.lanes || [];
  const COMPONENTS = DATA.components || [];
  const META = DATA.meta || {};

  const SCENES = {
    declassified: { number: '16', title: 'Declassified', kicker: 'Evidence room', note: 'A case file you reveal, one decision at a time.' },
    spatial: { number: '17', title: 'Spatial', kicker: 'A field of capabilities', note: 'Move through the system as a luminous room.' },
    boresight: { number: '18', title: 'Boresight', kicker: 'Signal acquisition', note: 'Find one useful route in the noise.' },
    vitrine: { number: '19', title: 'Vitrine', kicker: 'One object, fully seen', note: 'The catalog presented as a changing museum piece.' },
    tube: { number: '20', title: 'Tube', kicker: 'Live transmission', note: 'A broadcast from the automatic prompt pipeline.' },
    poster: { number: '21', title: 'Poster', kicker: 'The rule is the graphic', note: 'Three layers at billboard scale.' },
    membrane: { number: '22', title: 'Membrane', kicker: 'Living system', note: 'Capabilities gather into an organism, not a grid.' },
    panes: { number: '23', title: 'Panes', kicker: 'Operator workspace', note: 'Four working contexts, tiled and focusable.' },
    plate: { number: '24', title: 'Plate', kicker: 'Long exposure', note: 'A navigable sky made from the real lane registry.' },
    riso: { number: '25', title: 'Riso', kicker: 'Two-pass print', note: 'Misregistration becomes the interaction.' },
    stage: { number: '26', title: 'Stage', kicker: 'One cue at a time', note: 'The current pipeline step owns the room.' },
    machined: { number: '27', title: 'Machined', kicker: 'Control surface', note: 'Physical dials for an exact setup state.' },
    depth: { number: '28', title: 'Depth', kicker: 'Focus stack', note: 'Pull a lane toward you and let the rest recede.' },
    reactor: { number: '29', title: 'Reactor', kicker: 'Pipeline core', note: 'The standing rules orbit one enforced center.' },
    atrium: { number: '30', title: 'Atrium', kicker: 'Architecture of light', note: 'Walk the three layers as translucent rooms.' },
    mycelium: { number: '31', title: 'Mycelium', kicker: 'Living index', note: 'Follow a capability through roots that grow from shared rules.' },
    broadsheet: { number: '32', title: 'Broadsheet', kicker: 'Daily system record', note: 'Read the live catalog as a front page with no dashboard chrome.' },
    switchboard: { number: '33', title: 'Switchboard', kicker: 'Manual signal routing', note: 'Patch a lane into focus and inspect the signal at the console.' },
    bathysphere: { number: '34', title: 'Bathysphere', kicker: 'Deep catalog survey', note: 'Descend through the registry and surface one useful signal.' },
    prism: { number: '35', title: 'Prism', kicker: 'Chromatic index', note: 'Split one system into bold, selectable bands of capability.' }
  };

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function laneAt(index) {
    if (!LANES.length) return { id: 'pipeline', name: 'Standing pipeline', detail: 'Automatic on every prompt.' };
    return LANES[((index % LANES.length) + LANES.length) % LANES.length];
  }

  function countFor(lane) {
    return COMPONENTS.filter(function (component) { return component.lane === lane.id; }).length;
  }

  function componentsFor(lane, limit) {
    return COMPONENTS.filter(function (component) { return component.lane === lane.id; }).slice(0, limit || 5);
  }

  function laneButton(lane, index) {
    return '<button type="button" class="ex-lane-button" data-lane-index="' + index + '">' +
      '<span>' + String(index + 1).padStart(2, '0') + '</span>' + esc(lane.name) + '</button>';
  }

  function chrome(scene) {
    return '<header class="ex-chrome">' +
      '<a href="index.html" class="ex-back"><span aria-hidden="true">←</span><span class="ex-label-long">Design collection</span><span class="ex-label-short">Collection</span></a>' +
      '<p class="ex-scene-id">D' + scene.number + ' / ' + esc(scene.kicker) + '</p>' +
      '<div class="ex-chrome-actions"><button type="button" class="ex-command-button" data-open-command>' +
      '<span class="ex-label-long">Command center</span><span class="ex-label-short">Commands</span></button>' +
      '<button type="button" class="ex-atlas-button" data-open-atlas><span class="ex-label-long">Open full Atlas</span>' +
      '<span class="ex-label-short">Atlas</span></button></div>' +
      '</header>';
  }

  function currentReadout(index) {
    const lane = laneAt(index || 0);
    return '<div class="ex-readout" aria-live="polite">' +
      '<span data-current-count>' + countFor(lane) + ' components</span>' +
      '<strong data-current-lane>' + esc(lane.name) + '</strong>' +
      '<p data-current-detail>' + esc(lane.detail || 'A working lane in the Master Repo system.') + '</p>' +
      '</div>';
  }

  function declassified(scene) {
    const lane = laneAt(0);
    const rows = componentsFor(lane, 5).map(function (component, index) {
      return '<li><span>EX-' + String(index + 1).padStart(3, '0') + '</span><b>' +
        esc(component.name) + '</b><i class="ex-redaction">' + esc(component.detail || 'Restricted') + '</i></li>';
    }).join('');
    return '<section class="ex-document"><div class="ex-doc-head"><div><p>MASTER REPO / INTERNAL</p>' +
      '<h1>' + scene.title + '</h1></div><strong>OPEN</strong></div>' +
      '<div class="ex-doc-grid"><aside><p>CASE</p><b>AUTO-MODE</b><p>STATUS</p><b>ENFORCED</b>' +
      '<p>LAYERS</p><b>03</b></aside><article><p class="ex-typewritten">The slash is optional. The standing pipeline arrives before the request.</p>' +
      '<ol class="ex-evidence">' + rows + '</ol><button type="button" data-register>Reveal redactions</button></article></div></section>';
  }

  function spatial(scene) {
    const orbs = LANES.slice(0, 9).map(function (lane, index) {
      return '<button type="button" class="ex-orb ex-orb-' + (index + 1) + '" data-lane-index="' + index +
        '" aria-label="Inspect ' + esc(lane.name) + '"><span>' + esc(lane.name) + '</span></button>';
    }).join('');
    return '<section class="ex-spatial"><div class="ex-spatial-copy"><p>' + esc(scene.kicker) + '</p><h1>' +
      scene.title + '</h1><span>' + esc(scene.note) + '</span></div><div class="ex-orbit-field">' + orbs +
      '</div>' + currentReadout(1) + '</section>';
  }

  function boresight(scene) {
    const contacts = LANES.slice(0, 12).map(function (lane, index) {
      const angle = (index * 137.5) * Math.PI / 180;
      const radius = 19 + (index % 4) * 8;
      const x = 50 + Math.cos(angle) * radius;
      const y = 50 + Math.sin(angle) * radius;
      return '<button type="button" class="ex-contact" style="left:' + x.toFixed(2) + '%;top:' + y.toFixed(2) +
        '%" data-lane-index="' + index + '" aria-label="Acquire ' + esc(lane.name) + '"></button>';
    }).join('');
    return '<section class="ex-boresight"><div class="ex-radar"><div class="ex-sweep"></div>' + contacts +
      '<div class="ex-reticle"><span></span></div></div><div class="ex-hud-copy"><p>' + esc(scene.kicker) +
      '</p><h1>' + scene.title + '</h1>' + currentReadout(2) +
      '<small>SELECT A CONTACT TO LOCK THE ROUTE</small></div></section>';
  }

  function vitrine(scene) {
    const lane = laneAt(3);
    return '<section class="ex-vitrine"><div class="ex-wall-label"><p>COLLECTION ' + scene.number + '</p><h1>' +
      scene.title + '</h1><span>' + esc(scene.note) + '</span></div><div class="ex-pedestal"><div class="ex-object" data-artifact>' +
      '<span data-current-count>' + countFor(lane) + '</span><strong data-current-lane>' + esc(lane.name) +
      '</strong></div><i></i></div><div class="ex-vitrine-controls"><button type="button" data-cycle="-1">Previous object</button>' +
      '<button type="button" data-cycle="1">Next object</button><p data-current-detail>' + esc(lane.detail || scene.note) +
      '</p></div></section>';
  }

  function tube(scene) {
    const log = COMPONENTS.slice(0, 12).map(function (component, index) {
      return '<li><span>' + String(index + 1).padStart(4, '0') + '</span><b>' + esc(component.name) +
        '</b><i>' + esc(component.kind || 'ready') + '</i></li>';
    }).join('');
    return '<section class="ex-tube"><div class="ex-tube-glass"><div class="ex-tube-top"><h1>' + scene.title +
      '</h1><span>LIVE / ' + (META.components || COMPONENTS.length) + ' SIGNALS</span></div><p class="ex-tube-command">' +
      '&gt; pipeline --automatic --every-prompt<span class="ex-cursor"></span></p><ol>' + log +
      '</ol><footer>CH 03 <b>CAVEMAN · PLAN · DESIGN · VERIFY</b></footer></div></section>';
  }

  function poster(scene) {
    return '<section class="ex-poster"><div class="ex-poster-grid"></div><p class="ex-poster-no">D' + scene.number +
      '</p><h1><span>AUTO</span><span>MODE</span><span>ALWAYS</span></h1><div class="ex-poster-copy"><b>01</b><p>Caveman<br>Full output<br>Anti-slop</p>' +
      '<b>02</b><p>Plan<br>Design</p><b>03</b><p>Capabilities<br>Agents<br>Verify</p></div>' +
      '<div class="ex-poster-stamp">NO SLASH<br>REQUIRED</div></section>';
  }

  function membrane(scene) {
    const cells = LANES.slice(0, 12).map(function (lane, index) {
      return '<button type="button" class="ex-cell ex-cell-' + ((index % 6) + 1) + '" data-lane-index="' + index +
        '"><span>' + esc(lane.name) + '</span><i>' + countFor(lane) + '</i></button>';
    }).join('');
    return '<section class="ex-membrane"><svg width="0" height="0" aria-hidden="true"><filter id="ex-goo"><feGaussianBlur in="SourceGraphic" stdDeviation="13" result="blur"/><feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -11" result="goo"/><feComposite in="SourceGraphic" in2="goo" operator="atop"/></filter></svg>' +
      '<div class="ex-membrane-copy"><p>' + esc(scene.kicker) + '</p><h1>' + scene.title + '</h1>' +
      currentReadout(4) + '</div><div class="ex-cells">' + cells + '</div></section>';
  }

  function panes(scene) {
    const panes = LANES.slice(0, 4).map(function (lane, index) {
      const lines = componentsFor(lane, 4).map(function (component) { return '<li>' + esc(component.name) + '</li>'; }).join('');
      return '<button type="button" class="ex-pane ex-pane-' + (index + 1) + '" data-window><span>0' +
        (index + 1) + ' ' + esc(lane.name) + '</span><strong>' + countFor(lane) + '</strong><ol>' + lines + '</ol></button>';
    }).join('');
    return '<section class="ex-panes"><header><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1><span>CLICK A PANE TO FOCUS</span></header><div class="ex-pane-grid">' + panes + '</div>' +
      '<footer>workspace/master-repo <span>4 contexts · 1 shared state</span></footer></section>';
  }

  function plate(scene) {
    const stars = LANES.slice(0, 15).map(function (lane, index) {
      const x = 8 + ((index * 29) % 83);
      const y = 12 + ((index * 47) % 72);
      const size = 3 + Math.min(8, Math.sqrt(countFor(lane)));
      return '<button type="button" class="ex-star" style="--x:' + x + '%;--y:' + y + '%;--s:' + size.toFixed(1) +
        'px" data-lane-index="' + index + '" aria-label="Inspect ' + esc(lane.name) + '"><span>' + esc(lane.name) + '</span></button>';
    }).join('');
    return '<section class="ex-plate"><div class="ex-sky">' + stars + '<div class="ex-plate-ring"></div></div>' +
      '<div class="ex-plate-caption"><p>PLATE MR-' + scene.number + '</p><h1>' + scene.title + '</h1>' + currentReadout(5) +
      '</div></section>';
  }

  function riso(scene) {
    const lane = laneAt(6);
    return '<section class="ex-riso"><div class="ex-registration">+</div><div class="ex-riso-title" aria-label="' +
      scene.title + '"><span>PIPE</span><span>PIPE</span><b>LINE</b></div><p class="ex-riso-kicker">' + esc(scene.kicker) +
      '</p><div class="ex-riso-facts"><strong data-current-lane>' + esc(lane.name) + '</strong><span data-current-count>' +
      countFor(lane) + ' COMPONENTS</span><p data-current-detail>' + esc(lane.detail || scene.note) + '</p></div>' +
      '<button type="button" class="ex-register" data-register>Snap plates into register</button></section>';
  }

  function stage(scene) {
    const lane = laneAt(7);
    return '<section class="ex-stage"><div class="ex-curtain ex-curtain-left"></div><div class="ex-curtain ex-curtain-right"></div>' +
      '<div class="ex-beam"></div><div class="ex-stage-subject"><p>CUE ' + scene.number + '</p><h1 data-current-lane>' +
      esc(lane.name) + '</h1><span data-current-count>' + countFor(lane) + ' components ready</span><p data-current-detail>' +
      esc(lane.detail || scene.note) + '</p><div><button type="button" data-cycle="-1">Previous cue</button>' +
      '<button type="button" data-cycle="1">Next cue</button></div></div><p class="ex-stage-mark">STANDING PIPELINE / LIVE</p></section>';
  }

  function machined(scene) {
    const lane = laneAt(8);
    return '<section class="ex-machined"><div class="ex-machine-plate"><header><p>MASTER REPO CONTROL</p><h1>' +
      scene.title + '</h1><span>SERIAL ' + scene.number + '-AUTO</span></header><div class="ex-machine-controls">' +
      '<label><span>COMPRESSION</span><input type="range" min="0" max="100" value="72" data-depth><b>72</b></label>' +
      '<div class="ex-dial"><i></i><span>ALWAYS</span></div><div class="ex-meter"><i></i><span>VERIFIED</span></div></div>' +
      '<div class="ex-machine-readout"><p>ACTIVE LANE</p><strong data-current-lane>' + esc(lane.name) + '</strong>' +
      '<span data-current-count>' + countFor(lane) + ' UNITS</span><p data-current-detail>' + esc(lane.detail || scene.note) +
      '</p><button type="button" data-cycle="1">Advance selector</button></div></div></section>';
  }

  function depth(scene) {
    const planes = LANES.slice(0, 6).map(function (lane, index) {
      return '<button type="button" class="ex-depth-plane" style="--i:' + index + '" data-lane-index="' + index +
        '"><span>0' + (index + 1) + '</span><strong>' + esc(lane.name) + '</strong><i>' + countFor(lane) + '</i></button>';
    }).join('');
    return '<section class="ex-depth"><div class="ex-depth-copy"><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1><span>' + esc(scene.note) + '</span><label>Focus distance<input type="range" min="0" max="5" value="2" data-focus-range></label></div>' +
      '<div class="ex-depth-stack" style="--focus:2">' + planes + '</div></section>';
  }

  function reactor(scene) {
    const lane = laneAt(9);
    const segments = LANES.slice(0, 12).map(function (item, index) {
      return '<button type="button" class="ex-reactor-segment" style="--i:' + index + '" data-lane-index="' + index +
        '" aria-label="Inspect ' + esc(item.name) + '"></button>';
    }).join('');
    return '<section class="ex-reactor"><div class="ex-reactor-copy"><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1>' + currentReadout(9) + '</div><div class="ex-reactor-core">' + segments + '<div class="ex-core-light"><span>' +
      (META.lanes || LANES.length) + '</span><b>LANES</b></div></div><p class="ex-reactor-status">CORE STABLE · PROMPT PIPELINE ACTIVE</p></section>';
  }

  function atrium(scene) {
    return '<section class="ex-atrium"><div class="ex-rays"></div><header><p>' + esc(scene.kicker) + '</p><h1>' +
      scene.title + '</h1><span>' + esc(scene.note) + '</span></header><div class="ex-atrium-rooms">' +
      '<button type="button" data-room="1"><span>01</span><strong>Before the request</strong><p>Caveman · Full output · Anti-slop</p></button>' +
      '<button type="button" data-room="2"><span>02</span><strong>Before production</strong><p>Plan · Design</p></button>' +
      '<button type="button" data-room="3"><span>03</span><strong>While acting</strong><p>Capabilities · Agents · Verify</p></button>' +
      '</div><div class="ex-atrium-note" aria-live="polite">Choose a room to see why it exists.</div></section>';
  }

  function mycelium(scene) {
    const nodes = LANES.slice(0, 10).map(function (lane, index) {
      const angle = (-154 + index * 34) * Math.PI / 180;
      const radius = 31 + (index % 3) * 8;
      const x = 50 + Math.cos(angle) * radius;
      const y = 53 + Math.sin(angle) * radius * .72;
      return '<button type="button" class="ex-root-node" style="--x:' + x.toFixed(1) + '%;--y:' + y.toFixed(1) +
        '%;--r:' + (index % 4) + '" data-lane-index="' + index + '" aria-label="Follow ' + esc(lane.name) + '">' +
        '<span>' + String(index + 1).padStart(2, '0') + '</span><strong>' + esc(lane.name) + '</strong><i>' +
        countFor(lane) + '</i></button>';
    }).join('');
    return '<section class="ex-mycelium"><header><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1><span>' + esc(scene.note) + '</span></header><div class="ex-root-field" aria-label="Capability root map">' +
      '<div class="ex-root-lines" aria-hidden="true"></div><div class="ex-root-heart"><b>' +
      (META.lanes || LANES.length) + '</b><span>live lanes</span></div>' + nodes + '</div><aside>' +
      currentReadout(0) + '</aside></section>';
  }

  function broadsheet(scene) {
    const briefs = LANES.slice(0, 7).map(function (lane, index) {
      return '<button type="button" class="ex-brief" data-lane-index="' + index + '"><span>0' + (index + 1) +
        '</span><strong>' + esc(lane.name) + '</strong><i>' + countFor(lane) + '</i></button>';
    }).join('');
    return '<section class="ex-broadsheet"><header class="ex-masthead"><span>VOL. ' + scene.number +
      ' / MASTER REPO</span><h1>' + scene.title + '</h1><span>' + (META.components || COMPONENTS.length) +
      ' ITEMS INDEXED</span></header><div class="ex-edition-line"><b>' + esc(scene.kicker) +
      '</b><span>Automatic edition · No slash required</span><time>LIVE</time></div><div class="ex-newsroom">' +
      '<article class="ex-lead-story"><p>THE LEAD</p><h2 data-current-lane>' + esc(laneAt(0).name) +
      '</h2><p data-current-detail>' + esc(laneAt(0).detail || scene.note) + '</p><blockquote>“The index explains what gets stored, where it can be found, and which command can use it.”</blockquote>' +
      '<strong data-current-count>' + countFor(laneAt(0)) + ' components</strong></article><aside class="ex-briefs" aria-label="Section index">' +
      briefs + '</aside><div class="ex-news-number"><span>INDEX</span><b>' + (META.components || COMPONENTS.length) +
      '</b><p>live components in one local edition</p></div></div></section>';
  }

  function switchboard(scene) {
    const jacks = LANES.slice(0, 12).map(function (lane, index) {
      return '<button type="button" class="ex-jack" style="--jack:' + index + '" data-lane-index="' + index +
        '" aria-label="Patch ' + esc(lane.name) + '"><span>J' + String(index + 1).padStart(2, '0') +
        '</span><i aria-hidden="true"></i><strong>' + esc(lane.name) + '</strong><small>' + countFor(lane) + '</small></button>';
    }).join('');
    return '<section class="ex-switchboard"><header><div><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1></div><span>SIGNAL / ' + (META.components || COMPONENTS.length) + '</span></header><div class="ex-patch-panel">' +
      '<div class="ex-cable ex-cable-a" aria-hidden="true"></div><div class="ex-cable ex-cable-b" aria-hidden="true"></div>' +
      jacks + '</div><aside class="ex-signal-console"><p>MONITOR 01</p>' + currentReadout(0) +
      '<div class="ex-levels" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>' +
      '<small>Select a jack to route its description here.</small></aside></section>';
  }

  function bathysphere(scene) {
    const signals = LANES.slice(0, 9).map(function (lane, index) {
      const x = 17 + ((index * 31) % 68);
      const y = 15 + index * 8.5;
      return '<button type="button" class="ex-depth-signal" style="--x:' + x + '%;--y:' + y.toFixed(1) +
        '%" data-lane-index="' + index + '" aria-label="Survey ' + esc(lane.name) + '"><i aria-hidden="true"></i>' +
        '<span>' + esc(lane.name) + '</span></button>';
    }).join('');
    return '<section class="ex-bathysphere"><div class="ex-depth-scale" aria-hidden="true"><span>000 M</span><span>400 M</span><span>800 M</span><span>1200 M</span></div>' +
      '<header><p>' + esc(scene.kicker) + '</p><h1>' + scene.title + '</h1><span>' + esc(scene.note) +
      '</span></header><div class="ex-water-column"><div class="ex-caustics" aria-hidden="true"></div>' + signals +
      '<div class="ex-submersible" aria-hidden="true"><i></i><b></b></div></div><aside class="ex-porthole"><div>' +
      currentReadout(0) + '</div><small>DEPTH LOCKED · LOCAL DATA ONLY</small></aside></section>';
  }

  function prism(scene) {
    const bands = LANES.slice(0, 8).map(function (lane, index) {
      return '<button type="button" class="ex-prism-band" style="--i:' + index + '" data-lane-index="' + index +
        '"><span>0' + (index + 1) + '</span><strong>' + esc(lane.name) + '</strong><i>' + countFor(lane) + '</i></button>';
    }).join('');
    return '<section class="ex-prism"><div class="ex-prism-title"><p>' + esc(scene.kicker) + '</p><h1>' + scene.title +
      '</h1><span>' + esc(scene.note) + '</span></div><div class="ex-spectrum" aria-label="Capability spectrum">' + bands +
      '</div><aside>' + currentReadout(0) + '</aside><p class="ex-prism-rule">ONE SOURCE / MANY ROUTES / ZERO SECRETS</p></section>';
  }

  const RENDERERS = { declassified: declassified, spatial: spatial, boresight: boresight,
    vitrine: vitrine, tube: tube, poster: poster, membrane: membrane, panes: panes,
    plate: plate, riso: riso, stage: stage, machined: machined, depth: depth,
    reactor: reactor, atrium: atrium, mycelium: mycelium, broadsheet: broadsheet,
    switchboard: switchboard, bathysphere: bathysphere, prism: prism };

  function updateReadout(root, index) {
    const lane = laneAt(index);
    root.dataset.laneIndex = String(index);
    root.querySelectorAll('[data-current-lane]').forEach(function (node) { node.textContent = lane.name; });
    root.querySelectorAll('[data-current-count]').forEach(function (node) { node.textContent = countFor(lane) + ' components'; });
    root.querySelectorAll('[data-current-detail]').forEach(function (node) {
      node.textContent = lane.detail || 'A working lane in the Master Repo system.';
    });
  }

  function bind(root) {
    const legacy = Array.from(document.body.children).filter(function (node) {
      return node !== root && node.tagName !== 'SCRIPT';
    });
    legacy.forEach(function (node) { node.hidden = true; node.dataset.atlasLegacy = 'true'; });

    let lastOpener = root.querySelector('[data-open-atlas]');
    const revealAtlas = function (requestedTab, opener) {
      lastOpener = opener || lastOpener;
      root.classList.add('ex-collapsed');
      document.body.classList.add('exhibition-full-atlas');
      legacy.forEach(function (node) { node.hidden = false; });
      if (requestedTab && window.AtlasPanes) {
        window.AtlasPanes.tab = requestedTab;
        window.AtlasPanes.draw();
      }
      window.requestAnimationFrame(function () {
        const main = document.getElementById('stage') || document.getElementById('main-content');
        if (main) main.focus({ preventScroll: true });
      });
    };
    root.querySelector('[data-open-atlas]').addEventListener('click', function (event) {
      revealAtlas('', event.currentTarget);
    });
    root.querySelector('[data-open-command]').addEventListener('click', function (event) {
      revealAtlas('index', event.currentTarget);
    });
    root.querySelector('[data-return-concept]').addEventListener('click', function () {
      legacy.forEach(function (node) { node.hidden = true; });
      document.body.classList.remove('exhibition-full-atlas');
      root.classList.remove('ex-collapsed');
      window.scrollTo(0, 0);
      if (lastOpener) lastOpener.focus();
    });

    root.querySelectorAll('[data-lane-index]').forEach(function (button) {
      button.addEventListener('click', function () {
        const index = Number(button.dataset.laneIndex || 0);
        root.querySelectorAll('[data-lane-index]').forEach(function (item) {
          item.classList.remove('is-active');
          item.setAttribute('aria-pressed', 'false');
        });
        button.classList.add('is-active');
        button.setAttribute('aria-pressed', 'true');
        updateReadout(root, index);
        const focusRange = root.querySelector('[data-focus-range]');
        if (focusRange && button.classList.contains('ex-depth-plane')) {
          focusRange.value = String(index);
          focusRange.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    });

    root.querySelectorAll('[data-cycle]').forEach(function (button) {
      button.addEventListener('click', function () {
        const current = Number(root.dataset.laneIndex || 0);
        updateReadout(root, current + Number(button.dataset.cycle || 1));
      });
    });

    root.querySelectorAll('[data-register]').forEach(function (button) {
      button.addEventListener('click', function () {
        const on = root.classList.toggle('is-registered');
        button.textContent = on ? 'Return to raw state' :
          (root.dataset.scene === 'riso' ? 'Snap plates into register' : 'Reveal redactions');
      });
    });

    root.querySelectorAll('[data-window]').forEach(function (button) {
      button.addEventListener('click', function () {
        root.querySelectorAll('[data-window]').forEach(function (pane) { pane.classList.remove('is-focused'); });
        button.classList.add('is-focused');
      });
    });

    const depth = root.querySelector('[data-depth]');
    if (depth) depth.addEventListener('input', function () {
      const value = Number(depth.value);
      root.style.setProperty('--machine-value', value + '%');
      const output = depth.parentElement.querySelector('b');
      if (output) output.textContent = value;
    });

    const focus = root.querySelector('[data-focus-range]');
    if (focus) {
      const updateFocus = function () {
        root.querySelectorAll('.ex-depth-plane').forEach(function (plane, index) {
          const selected = index === Number(focus.value);
          plane.classList.toggle('is-focused', selected);
          plane.setAttribute('aria-pressed', selected ? 'true' : 'false');
        });
      };
      focus.addEventListener('input', updateFocus);
      updateFocus();
    }

    const roomCopy = {
      1: 'Compression and output rules arrive before the model interprets the request.',
      2: 'The approach and the visible experience are chosen before implementation starts.',
      3: 'Matching capabilities are selected, work fans out, and real checks close the loop.'
    };
    root.querySelectorAll('[data-room]').forEach(function (room) {
      room.addEventListener('click', function () {
        root.querySelectorAll('[data-room]').forEach(function (item) { item.classList.remove('is-active'); });
        room.classList.add('is-active');
        root.querySelector('.ex-atrium-note').textContent = roomCopy[room.dataset.room];
      });
    });

    root.addEventListener('pointermove', function (event) {
      const x = event.clientX / Math.max(window.innerWidth, 1) - .5;
      const y = event.clientY / Math.max(window.innerHeight, 1) - .5;
      root.style.setProperty('--mx', x.toFixed(3));
      root.style.setProperty('--my', y.toFixed(3));
    }, { passive: true });
  }

  function workspace(options) {
    const A = window.AtlasCore;
    const P = window.AtlasPanes;
    const T = window.AtlasTheme;
    if (!A || !P) return;
    const config = options || {};
    const shell = document.createElement('div');
    document.body.dataset.atlasShell = config.skin || 'field';
    shell.className = 'atlas-workspace';
    shell.innerHTML = '<a class="atlas-skip" href="#main-content">Skip to component index</a>' +
      '<header class="atlas-workspace-head"><a href="index.html">Design collection</a><div><p>' +
      esc(config.eyebrow || 'Full Atlas workspace') + '</p><h1>' + esc(config.title || 'Atlas') +
      '</h1><span>' + esc(config.note || 'One local index for every available capability.') + '</span></div>' +
      '<dl><div><dt>Visible</dt><dd data-visible-count>0</dd></div><div><dt>Build</dt><dd data-basket-count>0</dd></div></dl></header>' +
      '<nav class="atlas-workspace-tabs" id="tabs" role="tablist" aria-label="Atlas views"></nav>' +
      '<aside class="atlas-workspace-tools"><section><h2>Palette</h2><div id="themehost"></div></section>' +
      '<section><h2>Setup</h2><div id="setup"></div></section><section><h2>Filter</h2><div id="filters"></div></section></aside>' +
      '<main class="atlas-workspace-main" id="main-content" tabindex="-1"><div class="atlas-index-note">' +
      '<strong>Local system index</strong><span>Agents, tools, skills, plugins, MCP, hybrid routes, hardware, setup and Build. No secrets are sent from this page.</span></div>' +
      '<div id="stage" tabindex="-1"></div></main><aside class="atlas-workspace-detail"><h2>Description</h2>' +
      '<div id="side" aria-label="Selected component description"></div></aside>';
    document.body.appendChild(shell);

    function buildControl(component) {
      if (!A.canBuild(component)) {
        const state = A.setupStateFor(component);
        const label = state.id === 'choose-platform' ? 'Choose OS' : state.id === 'review-required' ? 'Review' :
          state.id === 'hosted' ? 'Hosted' : 'Plan only';
        return '<span class="atlas-plan-state">' + label + '</span>';
      }
      const included = A.state.basket.includes(component.id);
      return '<button type="button" class="atlas-build-toggle' + (included ? ' is-added' : '') + '" data-add="' +
        esc(component.id) + '" aria-label="' + (included ? 'Remove ' : 'Add ') + esc(component.name) +
        (included ? ' from Build">Added' : ' to Build">Add') + '</button>';
    }

    function renderMap(stage) {
      const visible = A.visibleComponents();
      const familyNames = new Map((A.state.data.families || []).map(function (family) { return [family.id, family.name]; }));
      const groups = new Map();
      visible.forEach(function (component) {
        const family = component.family || 'other';
        if (!groups.has(family)) groups.set(family, []);
        groups.get(family).push(component);
      });
      if (!visible.length) {
        stage.innerHTML = '<div class="atlas-empty"><strong>No components match.</strong><p>Clear a filter or choose another family, kind, or subcategory.</p></div>';
        counts();
        return;
      }
      stage.innerHTML = '<div class="atlas-index-groups">' + Array.from(groups.entries()).map(function (entry) {
        const family = entry[0];
        const items = entry[1];
        return '<section class="atlas-index-group"><header><h2>' + esc(familyNames.get(family) || family) +
          '</h2><span>' + items.length + '</span></header><div class="atlas-index-list">' + items.map(function (component) {
            const active = A.state.selected === component.id;
            return '<article class="atlas-index-row' + (active ? ' is-selected' : '') + '"><button type="button" class="atlas-component-open" data-open-component="' +
              esc(component.id) + '" aria-pressed="' + (active ? 'true' : 'false') + '"><span><strong>' +
              esc(component.name) + '</strong><small>' + esc(component.detail || 'Open for the indexed description and available command.') +
              '</small></span><i>' + esc(component.kind || component.subcategory || 'component') + '</i></button>' +
              buildControl(component) + '</article>';
          }).join('') + '</div></section>';
      }).join('') + '</div>';

      const openers = Array.from(stage.querySelectorAll('[data-open-component]'));
      openers.forEach(function (button, index) {
        button.addEventListener('click', function () {
          A.select(button.dataset.openComponent);
          openers.forEach(function (item) { item.setAttribute('aria-pressed', 'false'); });
          stage.querySelectorAll('.atlas-index-row.is-selected').forEach(function (row) { row.classList.remove('is-selected'); });
          button.setAttribute('aria-pressed', 'true');
          button.closest('.atlas-index-row').classList.add('is-selected');
          const rect = button.getBoundingClientRect();
          P.popover(rect.right, rect.top, button.dataset.openComponent);
        });
        button.addEventListener('keydown', function (event) {
          if (!['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft'].includes(event.key)) return;
          event.preventDefault();
          const direction = event.key === 'ArrowDown' || event.key === 'ArrowRight' ? 1 : -1;
          openers[(index + direction + openers.length) % openers.length].focus();
        });
      });
      stage.querySelectorAll('[data-add]').forEach(function (button) {
        button.addEventListener('click', function () {
          const id = button.dataset.add;
          if (A.state.basket.includes(id)) A.removeFromBasket(id); else A.addToBasket(id);
          P.draw();
          counts();
        });
      });
      counts();
    }

    function counts() {
      const current = A.counts();
      shell.querySelectorAll('[data-visible-count]').forEach(function (node) { node.textContent = current.visibleComponents; });
      shell.querySelectorAll('[data-basket-count]').forEach(function (node) { node.textContent = current.basket; });
    }

    if (T && shell.querySelector('#themehost')) T.mount(shell.querySelector('#themehost'), config.theme || 'ember');
    P.mount({
      renderMap: renderMap,
      onFilter: function () { if (P.tab === 'map') renderMap(shell.querySelector('#stage')); counts(); },
      onSelect: counts
    });
    A.on(counts);
  }

  function mount(sceneId) {
    const scene = SCENES[sceneId];
    const renderer = RENDERERS[sceneId];
    if (!scene || !renderer) return;
    const root = document.createElement('div');
    root.id = 'exhibitionRoot';
    root.className = 'exhibition-root';
    root.dataset.scene = sceneId;
    root.dataset.laneIndex = '0';
    root.innerHTML = '<div class="ex-frame">' + chrome(scene) + renderer(scene) + '</div>' +
      '<button type="button" class="ex-return" data-return-concept>Return to D' + scene.number + '</button>';
    document.body.prepend(root);
    document.body.classList.add('exhibition-active');
    bind(root);
  }

  window.AtlasExhibition = { mount: mount, workspace: workspace };
})();
