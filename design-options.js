// @ts-check
/*
  Browser runtime for the V7 Graphite Atlas design studio.

  This file intentionally has no runtime dependencies. The matching
  design-options.ts contract keeps the palette model explicit for editor and CI checks.
*/

/** @typedef {import('./design-options').Design} Design */
/** @typedef {import('./design-options').Palette} Palette */
/** @typedef {import('./design-options').StudioMode} StudioMode */

const $ = (id) => document.getElementById(id);
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const designGrid = $('designGrid');
const previewDialog = /** @type {HTMLDialogElement} */ ($('previewDialog'));
const previewBody = $('previewBody');
const previewTitle = $('previewTitle');
const previewClose = $('previewClose');
const choiceStatus = $('choiceStatus');
const toast = $('toast');

/** @type {Design[]} */
const DESIGNS = [
  {
    id: 'graphite', index: '01', name: 'V7 Graphite Atlas', layout: 'graphite',
    label: 'Current reference',
    description: 'Near monochrome tooling with one hot orange accent. The atlas keeps all 52 components and 16 lanes visible across 12 focused canvases.',
    dark: { bg: '#131314', panel: '#1c1c1e', panel2: '#262628', ink: '#fafafb', ink2: '#d2d2d7', ink3: '#a9a9b2', accent: '#ff8a3d', accent2: '#ffb347', onAccent: '#18110c', ok: '#77dd9a', codeBg: '#0c0c0d', codeInk: '#ededf0', codeMuted: '#a9a9b2', r: '12px', rSm: '9px', shadow: '0 20px 52px rgba(0,0,0,.34)', fontDisplay: '"Segoe UI",Tahoma,Arial,sans-serif', fontBody: '"Segoe UI",Tahoma,Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'none' },
    light: { bg: '#f5f5f6', panel: '#ffffff', panel2: '#eeeeef', ink: '#171719', ink2: '#3f4045', ink3: '#666870', accent: '#a84709', accent2: '#9a6200', onAccent: '#ffffff', ok: '#177344', codeBg: '#171719', codeInk: '#f7f7f8', codeMuted: '#bfc0c5', r: '12px', rSm: '9px', shadow: '0 16px 38px rgba(23,23,25,.13)', fontDisplay: '"Segoe UI",Tahoma,Arial,sans-serif', fontBody: '"Segoe UI",Tahoma,Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'none' }
  },
  {
    id: 'polar', index: '02', name: 'Polar Ledger', layout: 'ledger',
    label: 'Precise technical ledger',
    description: 'A low radius, ruled interface with compact ledger rows and a single wide map. Cyan calibration marks keep the routing evidence legible.',
    dark: { bg: '#0d1d24', panel: '#162e39', panel2: '#1d3a46', ink: '#f0fbff', ink2: '#c5dce4', ink3: '#92b1bd', accent: '#58d1df', accent2: '#f19b72', onAccent: '#061b21', ok: '#8ed6b2', codeBg: '#071217', codeInk: '#e6f9ff', codeMuted: '#8eb4bf', r: '4px', rSm: '2px', shadow: '0 14px 32px rgba(0,8,12,.34)', fontDisplay: 'Aptos,"Segoe UI",Arial,sans-serif', fontBody: 'Aptos,"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 31px,rgba(88,209,223,.08) 32px)' },
    light: { bg: '#f4f9fb', panel: '#ffffff', panel2: '#edf6f8', ink: '#10242d', ink2: '#334e59', ink3: '#58737e', accent: '#006b78', accent2: '#9b421f', onAccent: '#ffffff', ok: '#246848', codeBg: '#10242d', codeInk: '#f4fbfd', codeMuted: '#b8ced7', r: '4px', rSm: '2px', shadow: '0 10px 26px rgba(16,52,65,.12)', fontDisplay: 'Aptos,"Segoe UI",Arial,sans-serif', fontBody: 'Aptos,"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 31px,rgba(0,107,120,.06) 32px)' }
  },
  {
    id: 'carbon', index: '03', name: 'Carbon Signal', layout: 'bands',
    label: 'Instrument bands',
    description: 'A dark instrument panel with sharp edges, cyan signal lines, and three stacked bands that make hybrid model routing read like an active system.',
    dark: { bg: '#0b1014', panel: '#121c24', panel2: '#182731', ink: '#edf8ff', ink2: '#c2d5df', ink3: '#88a8b7', accent: '#55d6ff', accent2: '#ff936f', onAccent: '#061217', ok: '#89e3b6', codeBg: '#05090c', codeInk: '#dff6ff', codeMuted: '#7ca5b5', r: '2px', rSm: '2px', shadow: 'inset 0 0 0 1px rgba(85,214,255,.08),0 14px 36px rgba(0,0,0,.44)', fontDisplay: 'Consolas,"Lucida Console",monospace', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(rgba(85,214,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(85,214,255,.06) 1px,transparent 1px)' },
    light: { bg: '#eef7fb', panel: '#ffffff', panel2: '#e8f3f7', ink: '#0b1c25', ink2: '#31515f', ink3: '#557482', accent: '#006f91', accent2: '#9c3a21', onAccent: '#ffffff', ok: '#246545', codeBg: '#0b1c25', codeInk: '#edf9ff', codeMuted: '#9cbdca', r: '2px', rSm: '2px', shadow: 'inset 0 0 0 1px rgba(0,87,113,.08),0 12px 30px rgba(0,49,67,.13)', fontDisplay: 'Consolas,"Lucida Console",monospace', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(rgba(0,111,145,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(0,111,145,.06) 1px,transparent 1px)' }
  },
  {
    id: 'verdant', index: '04', name: 'Verdant Archive', layout: 'archive',
    label: 'Scholarly catalog',
    description: 'A library card catalog where each pathway reads like a referenced record. Soft green, cream, and paper stack depth give the system a deliberate research feel.',
    dark: { bg: '#13231b', panel: '#20372a', panel2: '#294333', ink: '#f7f4e8', ink2: '#d6dccb', ink3: '#a8b5a4', accent: '#9bd09d', accent2: '#d7bd68', onAccent: '#102317', ok: '#9bd09d', codeBg: '#0d1912', codeInk: '#e9f1df', codeMuted: '#9fb39f', r: '6px', rSm: '3px', shadow: '4px 5px 0 rgba(7,19,12,.28),0 18px 34px rgba(3,12,7,.28)', fontDisplay: '"Book Antiqua","Palatino Linotype",Georgia,serif', fontBody: 'Tahoma,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 39px,rgba(155,208,157,.08) 40px)' },
    light: { bg: '#f4f2e8', panel: '#fffdf4', panel2: '#f3f0df', ink: '#183126', ink2: '#40574a', ink3: '#647569', accent: '#1e6842', accent2: '#735704', onAccent: '#ffffff', ok: '#1e6842', codeBg: '#183126', codeInk: '#f4f2e8', codeMuted: '#b7c5b4', r: '6px', rSm: '3px', shadow: '4px 5px 0 rgba(53,76,61,.1),0 15px 28px rgba(37,64,48,.1)', fontDisplay: '"Book Antiqua","Palatino Linotype",Georgia,serif', fontBody: 'Tahoma,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 39px,rgba(30,104,66,.06) 40px)' }
  },
  {
    id: 'cobalt', index: '05', name: 'Cobalt Blueprint', layout: 'blueprint',
    label: 'Engineering schematic',
    description: 'A blue technical drawing board with measurement grid, square panels, and yellow signal accents. The complete map reads as a diagram first and a dashboard second.',
    dark: { bg: '#082b5b', panel: '#0c376e', panel2: '#10427e', ink: '#f1f7ff', ink2: '#c7daf1', ink3: '#91b2d7', accent: '#ffd45a', accent2: '#ff9b72', onAccent: '#10213a', ok: '#a9dba2', codeBg: '#061d3e', codeInk: '#eff7ff', codeMuted: '#91b2d7', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Trebuchet MS",Verdana,sans-serif', fontBody: 'Consolas,"Lucida Console",monospace', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(rgba(241,247,255,.09) 1px,transparent 1px),linear-gradient(90deg,rgba(241,247,255,.09) 1px,transparent 1px)' },
    light: { bg: '#eef5ff', panel: '#ffffff', panel2: '#e5f0ff', ink: '#10213a', ink2: '#334d70', ink3: '#5d7495', accent: '#6c5100', accent2: '#963d20', onAccent: '#ffffff', ok: '#2d6234', codeBg: '#10213a', codeInk: '#eef5ff', codeMuted: '#aec3df', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Trebuchet MS",Verdana,sans-serif', fontBody: 'Consolas,"Lucida Console",monospace', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(rgba(16,33,58,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(16,33,58,.08) 1px,transparent 1px)' }
  },
  {
    id: 'coral', index: '06', name: 'Coral Workshop', layout: 'workshop',
    label: 'Playful assembly bench',
    description: 'Chunky modules, broad corners, and a strong offset shadow make the map feel assembled piece by piece. Coral keeps selected routing vivid without losing clarity.',
    dark: { bg: '#2d1612', panel: '#43231d', panel2: '#512c24', ink: '#fff4ed', ink2: '#f0cfc3', ink3: '#c99f91', accent: '#ffbd64', accent2: '#ff8567', onAccent: '#321712', ok: '#acd797', codeBg: '#210e0a', codeInk: '#fff0e9', codeMuted: '#d49d8b', r: '24px', rSm: '14px', shadow: '7px 7px 0 #160a08,0 20px 36px rgba(30,8,4,.28)', fontDisplay: '"Arial Black",Arial,sans-serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(circle,rgba(255,133,103,.14) 0 4px,transparent 5px)' },
    light: { bg: '#fff4ed', panel: '#ffffff', panel2: '#fff0e8', ink: '#321712', ink2: '#60372e', ink3: '#81564b', accent: '#b9381f', accent2: '#8b5000', onAccent: '#ffffff', ok: '#37651e', codeBg: '#321712', codeInk: '#fff4ed', codeMuted: '#d7afa3', r: '24px', rSm: '14px', shadow: '7px 7px 0 #5b2a20,0 18px 30px rgba(83,34,22,.15)', fontDisplay: '"Arial Black",Arial,sans-serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(circle,rgba(185,56,31,.12) 0 4px,transparent 5px)' }
  },
  {
    id: 'plum', index: '07', name: 'Plum Observatory', layout: 'orbit',
    label: 'Celestial control room',
    description: 'Orbital geometry centers the model router. The rest of the system circles it, so escalation and fallbacks become easy to trace without splitting the canvas.',
    dark: { bg: '#1b1028', panel: '#27183a', panel2: '#322047', ink: '#fcf6ff', ink2: '#decfea', ink3: '#ad98bd', accent: '#e5a3ff', accent2: '#ff8d8d', onAccent: '#211026', ok: '#a8dda5', codeBg: '#13091e', codeInk: '#f9edff', codeMuted: '#b397c5', r: '18px', rSm: '12px', shadow: '0 24px 64px rgba(58,19,89,.42),0 0 36px rgba(229,163,255,.08)', fontDisplay: '"Palatino Linotype",Palatino,Georgia,serif', fontBody: '"Segoe UI",Tahoma,Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(circle at 50% 12%,transparent 0 120px,rgba(229,163,255,.12) 121px 122px,transparent 123px 210px,rgba(242,209,109,.08) 211px 212px,transparent 213px)' },
    light: { bg: '#f7f0fb', panel: '#fffaff', panel2: '#f2e7f7', ink: '#2b1738', ink2: '#583b67', ink3: '#775d84', accent: '#6f2b8c', accent2: '#9a3d46', onAccent: '#ffffff', ok: '#35642f', codeBg: '#2b1738', codeInk: '#f7f0fb', codeMuted: '#c4b0ce', r: '18px', rSm: '12px', shadow: '0 18px 42px rgba(76,34,98,.16)', fontDisplay: '"Palatino Linotype",Palatino,Georgia,serif', fontBody: '"Segoe UI",Tahoma,Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(circle at 50% 12%,transparent 0 120px,rgba(111,43,140,.08) 121px 122px,transparent 123px)' }
  },
  {
    id: 'ink', index: '08', name: 'Ink Newsroom', layout: 'news',
    label: 'Editorial command desk',
    description: 'Heavy rules, tall editorial type, and a sharp red accent turn the workflow into a concise operations story. The primary map remains the front page.',
    dark: { bg: '#171717', panel: '#242321', panel2: '#2c2a27', ink: '#fffdf8', ink2: '#ded8ce', ink3: '#aaa297', accent: '#ff9b8e', accent2: '#e9cb68', onAccent: '#251010', ok: '#b5cd90', codeBg: '#0f0f0f', codeInk: '#fffaf1', codeMuted: '#aaa297', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Times New Roman",Times,serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 47px,rgba(255,253,248,.07) 48px)' },
    light: { bg: '#f4f0e6', panel: '#fffdf8', panel2: '#f2ede3', ink: '#171717', ink2: '#41403d', ink3: '#66635d', accent: '#a32929', accent2: '#6f5804', onAccent: '#ffffff', ok: '#3d6427', codeBg: '#171717', codeInk: '#f4f0e6', codeMuted: '#aaa297', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Times New Roman",Times,serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 47px,rgba(23,23,23,.07) 48px)' }
  },
  {
    id: 'citrus', index: '09', name: 'Citrus Grid', layout: 'swiss',
    label: 'Swiss signal grid',
    description: 'A strict poster grid with olive data bars, big numbers, and a low decoration surface. It makes the map feel both analytical and calm.',
    dark: { bg: '#14200b', panel: '#203315', panel2: '#29401a', ink: '#f8fbef', ink2: '#d5e2c6', ink3: '#a5b894', accent: '#c6ef55', accent2: '#ff9365', onAccent: '#172109', ok: '#9ee06a', codeBg: '#0d1507', codeInk: '#f4ffe0', codeMuted: '#9fb78a', r: '8px', rSm: '4px', shadow: '0 16px 36px rgba(5,18,0,.32)', fontDisplay: '"Helvetica Neue",Arial,sans-serif', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 0 74%,rgba(198,239,85,.08) 74% 75%,transparent 75%)' },
    light: { bg: '#f8fbef', panel: '#ffffff', panel2: '#f1f7e7', ink: '#1a260e', ink2: '#435332', ink3: '#677656', accent: '#4d7000', accent2: '#9b411e', onAccent: '#ffffff', ok: '#356700', codeBg: '#1a260e', codeInk: '#f8fbef', codeMuted: '#b8c7a5', r: '8px', rSm: '4px', shadow: 'none', fontDisplay: '"Helvetica Neue",Arial,sans-serif', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 0 74%,rgba(77,112,0,.06) 74% 75%,transparent 75%)' }
  },
  {
    id: 'phosphor', index: '10', name: 'Phosphor Desk', layout: 'terminal',
    label: 'Vintage workstation',
    description: 'A curved display frame, soft green bloom, and scan lines recast the same complete map as a steady local operations console.',
    dark: { bg: '#10150f', panel: '#182117', panel2: '#1e2b1c', ink: '#ddf5d8', ink2: '#b9d6b4', ink3: '#86a581', accent: '#74e66b', accent2: '#e4a369', onAccent: '#071007', ok: '#93e784', codeBg: '#081007', codeInk: '#ddf5d8', codeMuted: '#86a581', r: '28px', rSm: '6px', shadow: 'inset 0 0 34px rgba(0,0,0,.55),0 0 28px rgba(116,230,107,.1),0 20px 50px rgba(0,0,0,.38)', fontDisplay: '"Lucida Console","Courier New",monospace', fontBody: '"Lucida Console","Courier New",monospace', fontMono: '"Lucida Console","Courier New",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 3px,rgba(116,230,107,.06) 4px)' },
    light: { bg: '#edf6e9', panel: '#f8fff5', panel2: '#e8f3e4', ink: '#10200f', ink2: '#365233', ink3: '#5d7559', accent: '#287321', accent2: '#8d481b', onAccent: '#ffffff', ok: '#356d2c', codeBg: '#10200f', codeInk: '#edf6e9', codeMuted: '#a7bda1', r: '28px', rSm: '6px', shadow: 'inset 0 0 24px rgba(18,62,12,.08),0 15px 34px rgba(24,65,18,.13)', fontDisplay: '"Lucida Console","Courier New",monospace', fontBody: '"Lucida Console","Courier New",monospace', fontMono: '"Lucida Console","Courier New",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 3px,rgba(40,115,33,.05) 4px)' }
  },
  {
    id: 'porcelain', index: '11', name: 'Porcelain Museum', layout: 'museum',
    label: 'Refined gallery',
    description: 'Wide quiet margins and bronze caption rules let each route behave like a curated exhibit. The result is restrained without becoming generic.',
    dark: { bg: '#1d1916', panel: '#2a2520', panel2: '#332d27', ink: '#fcfaf6', ink2: '#ddd5ca', ink3: '#aaa095', accent: '#d9b277', accent2: '#e08a68', onAccent: '#261a0c', ok: '#a8c98d', codeBg: '#15110f', codeInk: '#faf4e9', codeMuted: '#aaa095', r: '2px', rSm: '2px', shadow: '0 20px 50px rgba(0,0,0,.3)', fontDisplay: 'Baskerville,Georgia,"Times New Roman",serif', fontBody: 'Optima,"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 0 8%,rgba(217,178,119,.1) 8% 8.2%,transparent 8.2% 91.8%,rgba(217,178,119,.1) 91.8% 92%,transparent 92%)' },
    light: { bg: '#fcfaf6', panel: '#ffffff', panel2: '#f7f3ed', ink: '#211b17', ink2: '#4e443d', ink3: '#70655d', accent: '#704a18', accent2: '#923d22', onAccent: '#ffffff', ok: '#3d6229', codeBg: '#211b17', codeInk: '#fcfaf6', codeMuted: '#b2a69d', r: '2px', rSm: '2px', shadow: '0 16px 38px rgba(53,43,34,.1)', fontDisplay: 'Baskerville,Georgia,"Times New Roman",serif', fontBody: 'Optima,"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 0 8%,rgba(112,74,24,.07) 8% 8.2%,transparent 8.2% 91.8%,rgba(112,74,24,.07) 91.8% 92%,transparent 92%)' }
  },
  {
    id: 'azure', index: '12', name: 'Azure Metro', layout: 'metro',
    label: 'Asymmetric dashboard',
    description: 'Flat blue tiles make selected pieces of the Graphite system grow into a stronger hierarchy. The output rail becomes a utility tile rather than a side card.',
    dark: { bg: '#0d1f38', panel: '#163253', panel2: '#1c3e64', ink: '#f0f7ff', ink2: '#c7d8ec', ink3: '#91acca', accent: '#67b4ff', accent2: '#ff936a', onAccent: '#07192e', ok: '#83d4b1', codeBg: '#09172a', codeInk: '#eff8ff', codeMuted: '#91acca', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Segoe UI",Arial,sans-serif', fontBody: '"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(135deg,rgba(103,180,255,.08) 0 18%,transparent 18% 82%,rgba(131,212,177,.08) 82%)' },
    light: { bg: '#eff5fa', panel: '#ffffff', panel2: '#e8f1f8', ink: '#10223b', ink2: '#39516d', ink3: '#607690', accent: '#005ac2', accent2: '#9e3e1e', onAccent: '#ffffff', ok: '#246744', codeBg: '#10223b', codeInk: '#eff5fa', codeMuted: '#a8bbcf', r: '0px', rSm: '0px', shadow: 'none', fontDisplay: '"Segoe UI",Arial,sans-serif', fontBody: '"Segoe UI",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(135deg,rgba(0,90,194,.06) 0 18%,transparent 18% 82%,rgba(36,103,68,.06) 82%)' }
  },
  {
    id: 'rose', index: '13', name: 'Rose Circuit', layout: 'circuit',
    label: 'Elegant circuit board',
    description: 'Soft circuit traces illuminate the selected routing and make the system read as a coordinated board rather than a collection of panels.',
    dark: { bg: '#26141c', panel: '#351b27', panel2: '#422132', ink: '#fff5f8', ink2: '#e6ced7', ink3: '#b99aa6', accent: '#ffb0c8', accent2: '#ff8b70', onAccent: '#251019', ok: '#a8d496', codeBg: '#1a0d13', codeInk: '#fff0f4', codeMuted: '#b99aa6', r: '24px', rSm: '12px', shadow: '0 22px 58px rgba(76,11,42,.38),0 0 28px rgba(255,176,200,.08)', fontDisplay: '"Century Gothic",Verdana,sans-serif', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 49.6%,rgba(255,176,200,.1) 50%,transparent 50.4%),linear-gradient(transparent 49.6%,rgba(255,176,200,.1) 50%,transparent 50.4%)' },
    light: { bg: '#fff3f6', panel: '#ffffff', panel2: '#fbeaf0', ink: '#32151f', ink2: '#603745', ink3: '#815867', accent: '#a62e58', accent2: '#9e3c25', onAccent: '#ffffff', ok: '#3c672b', codeBg: '#32151f', codeInk: '#fff3f6', codeMuted: '#c5a9b4', r: '24px', rSm: '12px', shadow: '0 18px 42px rgba(104,30,57,.15)', fontDisplay: '"Century Gothic",Verdana,sans-serif', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'linear-gradient(90deg,transparent 49.6%,rgba(166,46,88,.07) 50%,transparent 50.4%),linear-gradient(transparent 49.6%,rgba(166,46,88,.07) 50%,transparent 50.4%)' }
  },
  {
    id: 'clay', index: '14', name: 'Clay Field Notes', layout: 'notes',
    label: 'Tactile research notebook',
    description: 'Soft clay, stacked fragments, and gentle annotation motion make the map feel like a thoughtful field study. The code rail remains crisp and practical.',
    dark: { bg: '#2b1f19', panel: '#3e2c23', panel2: '#4a352a', ink: '#fff7e9', ink2: '#e4d1bd', ink3: '#b79c87', accent: '#e9b96e', accent2: '#e58c68', onAccent: '#2d1a09', ok: '#abc88a', codeBg: '#20150f', codeInk: '#fff1df', codeMuted: '#b79c87', r: '26px', rSm: '10px', shadow: '8px 9px 0 rgba(22,12,7,.2),0 20px 38px rgba(22,11,5,.25)', fontDisplay: '"Trebuchet MS",Verdana,sans-serif', fontBody: 'Georgia,"Times New Roman",serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 35px,rgba(229,140,104,.08) 36px)' },
    light: { bg: '#f4e7d5', panel: '#fff7e9', panel2: '#f7e6d1', ink: '#2f221b', ink2: '#5d473a', ink3: '#7a6354', accent: '#7d3d25', accent2: '#8e4127', onAccent: '#ffffff', ok: '#466126', codeBg: '#2f221b', codeInk: '#f4e7d5', codeMuted: '#c0a892', r: '26px', rSm: '10px', shadow: '8px 9px 0 rgba(88,51,28,.12),0 16px 30px rgba(96,55,30,.1)', fontDisplay: '"Trebuchet MS",Verdana,sans-serif', fontBody: 'Georgia,"Times New Roman",serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(0deg,transparent 0 35px,rgba(125,61,37,.06) 36px)' }
  },
  {
    id: 'hazard', index: '15', name: 'Hazard Manual', layout: 'manual',
    label: 'Industrial procedure guide',
    description: 'A caution yellow procedure manual with numbered route steps. It turns the same system into an explicit sequence for operators who value certainty over ornament.',
    dark: { bg: '#181700', panel: '#2a2800', panel2: '#373400', ink: '#fff9d9', ink2: '#e8dda5', ink3: '#b8ad74', accent: '#ffe35b', accent2: '#ff7d56', onAccent: '#171500', ok: '#add87a', codeBg: '#0e0d00', codeInk: '#fff9d9', codeMuted: '#b8ad74', r: '0px', rSm: '0px', shadow: '5px 5px 0 #070700', fontDisplay: '"Franklin Gothic Medium","Arial Narrow",Arial,sans-serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(135deg,rgba(255,249,217,.08) 0 12px,transparent 12px 24px)' },
    light: { bg: '#fff4b8', panel: '#fff9d9', panel2: '#fff1ac', ink: '#171500', ink2: '#454000', ink3: '#67600a', accent: '#b31312', accent2: '#9b351b', onAccent: '#ffffff', ok: '#3e650d', codeBg: '#171500', codeInk: '#fff4b8', codeMuted: '#aea35e', r: '0px', rSm: '0px', shadow: '5px 5px 0 #171500', fontDisplay: '"Franklin Gothic Medium","Arial Narrow",Arial,sans-serif', fontBody: 'Arial,"Segoe UI",sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'repeating-linear-gradient(135deg,rgba(23,21,0,.07) 0 12px,transparent 12px 24px)' }
  },
  {
    id: 'dawn', index: '16', name: 'Dawn Topography', layout: 'topography',
    label: 'Calm terrain map',
    description: 'Broad contour bands and generous rounded shapes give the system a quiet landscape. The lens still dims secondary routes without hiding them.',
    dark: { bg: '#20172c', panel: '#322345', panel2: '#3e2c54', ink: '#fbf7ff', ink2: '#ddd2e7', ink3: '#aa9ab7', accent: '#c9a6f4', accent2: '#ed9274', onAccent: '#281939', ok: '#9ed39b', codeBg: '#160f20', codeInk: '#faf2ff', codeMuted: '#aa9ab7', r: '36px', rSm: '22px', shadow: '0 28px 72px rgba(58,35,79,.4)', fontDisplay: 'Optima,"Trebuchet MS",sans-serif', fontBody: 'Georgia,"Times New Roman",serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(ellipse at 18% 8%,transparent 0 90px,rgba(201,166,244,.1) 91px 93px,transparent 94px 160px,rgba(237,146,116,.08) 161px 163px,transparent 164px)' },
    light: { bg: '#f7f2ff', panel: '#ffffff', panel2: '#f2eafb', ink: '#271b37', ink2: '#514063', ink3: '#746184', accent: '#65349a', accent2: '#963c24', onAccent: '#ffffff', ok: '#3b672d', codeBg: '#271b37', codeInk: '#f7f2ff', codeMuted: '#b4a5c0', r: '36px', rSm: '22px', shadow: '0 24px 60px rgba(78,50,105,.16)', fontDisplay: 'Optima,"Trebuchet MS",sans-serif', fontBody: 'Georgia,"Times New Roman",serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(ellipse at 18% 8%,transparent 0 90px,rgba(101,52,154,.08) 91px 93px,transparent 94px)' }
  },
  {
    id: 'pixel', index: '17', name: 'Paper Pixel', layout: 'pixel',
    label: 'Compact game menu',
    description: 'A high precision pixel grid makes all 52 components feel like inventory slots. The bright green routing marks are quick to scan at a glance.',
    dark: { bg: '#151912', panel: '#242a1f', panel2: '#2d3527', ink: '#fffdf4', ink2: '#dddac8', ink3: '#aaa78f', accent: '#69dfb8', accent2: '#f18a63', onAccent: '#07120e', ok: '#98d981', codeBg: '#0b0e09', codeInk: '#fffdf4', codeMuted: '#aaa78f', r: '0px', rSm: '0px', shadow: '4px 4px 0 #070907', fontDisplay: '"Lucida Console","Courier New",monospace', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: '"Lucida Console","Courier New",monospace', texture: 'radial-gradient(circle,rgba(255,253,244,.11) 0 1px,transparent 1px)' },
    light: { bg: '#fffdf4', panel: '#ffffff', panel2: '#f7f4e9', ink: '#231d0e', ink2: '#504936', ink3: '#716a55', accent: '#006b54', accent2: '#943a1f', onAccent: '#ffffff', ok: '#35651f', codeBg: '#231d0e', codeInk: '#fffdf4', codeMuted: '#b2aa91', r: '0px', rSm: '0px', shadow: '4px 4px 0 #231d0e', fontDisplay: '"Lucida Console","Courier New",monospace', fontBody: 'Verdana,"Segoe UI",sans-serif', fontMono: '"Lucida Console","Courier New",monospace', texture: 'radial-gradient(circle,rgba(35,29,14,.1) 0 1px,transparent 1px)' }
  },
  {
    id: 'cinema', index: '18', name: 'Data Cinema', layout: 'cinema',
    label: 'Cinematic chapter view',
    description: 'A spotlighted chapter treatment makes the route map feel like a central scene. Large type and theatrical depth create a strong end state for stakeholder review.',
    dark: { bg: '#120f11', panel: '#20181c', panel2: '#2a1f24', ink: '#fff4eb', ink2: '#e2cec1', ink3: '#aa9184', accent: '#f2703c', accent2: '#ff8b5d', onAccent: '#160a05', ok: '#a8c97e', codeBg: '#0b0809', codeInk: '#fff4eb', codeMuted: '#aa9184', r: '6px', rSm: '2px', shadow: '0 34px 90px rgba(0,0,0,.66)', fontDisplay: 'Impact,"Arial Narrow",Arial,sans-serif', fontBody: '"Arial Narrow",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(ellipse at 50% -10%,rgba(242,112,60,.2),transparent 54%)' },
    light: { bg: '#fff4eb', panel: '#ffffff', panel2: '#f8ebe2', ink: '#211514', ink2: '#503936', ink3: '#735950', accent: '#a63d16', accent2: '#9b3b1d', onAccent: '#ffffff', ok: '#426222', codeBg: '#211514', codeInk: '#fff4eb', codeMuted: '#b9a096', r: '6px', rSm: '2px', shadow: '0 24px 64px rgba(66,35,27,.18)', fontDisplay: 'Impact,"Arial Narrow",Arial,sans-serif', fontBody: '"Arial Narrow",Arial,sans-serif', fontMono: 'Consolas,"Lucida Console",monospace', texture: 'radial-gradient(ellipse at 50% -10%,rgba(166,61,22,.1),transparent 54%)' }
  }
];

const REQUIRED_TOKENS = ['bg', 'panel', 'panel2', 'ink', 'ink2', 'ink3', 'accent', 'accent2', 'onAccent', 'ok', 'codeBg', 'codeInk', 'codeMuted', 'r', 'rSm', 'shadow', 'fontDisplay', 'fontBody', 'fontMono', 'texture'];
const STORAGE = Object.freeze({
  mode: 'mru.design.studio.mode.v1',
  shortlist: 'mru.design.studio.shortlist.v1'
});

/** @type {StudioMode} */
let mode = readMode();
let shortlist = readShortlist();
let lastTrigger = null;
let previewId = null;

/** @returns {StudioMode} */
function readMode() {
  const requested = new URLSearchParams(location.search).get('mode');
  if (requested === 'light' || requested === 'dark') return requested;
  try {
    const saved = localStorage.getItem(STORAGE.mode);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch (_) {}
  return matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

/** @returns {string | null} */
function readShortlist() {
  const requested = new URLSearchParams(location.search).get('design');
  if (DESIGNS.some((design) => design.id === requested)) return requested;
  try {
    const saved = localStorage.getItem(STORAGE.shortlist);
    return DESIGNS.some((design) => design.id === saved) ? saved : null;
  } catch (_) {
    return null;
  }
}

/** @param {string} value */
function escapeHTML(value) {
  return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** @param {string} foreground @param {string} background */
function contrastRatio(foreground, background) {
  const luminance = (hex) => {
    const v = hex.slice(1).match(/.{2}/g).map((part) => Number.parseInt(part, 16) / 255).map((part) => part <= .03928 ? part / 12.92 : ((part + .055) / 1.055) ** 2.4);
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2];
  };
  const a = luminance(foreground);
  const b = luminance(background);
  return ((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toFixed(1);
}

/** @param {HTMLElement} card @param {Design} design */
function applyPalette(card, design) {
  /** @type {Palette} */
  const palette = design[mode];
  const values = {
    '--bg': palette.bg, '--panel': palette.panel, '--panel-2': palette.panel2,
    '--ink': palette.ink, '--ink-2': palette.ink2, '--ink-3': palette.ink3,
    '--accent': palette.accent, '--accent-2': palette.accent2, '--on-accent': palette.onAccent,
    '--ok': palette.ok, '--code-bg': palette.codeBg, '--code-ink': palette.codeInk,
    '--code-muted': palette.codeMuted, '--r': palette.r, '--r-sm': palette.rSm,
    '--shadow': palette.shadow, '--font-display': palette.fontDisplay,
    '--font-body': palette.fontBody, '--font-mono': palette.fontMono, '--texture': palette.texture
  };
  Object.entries(values).forEach(([name, value]) => card.style.setProperty(name, value));
}

/** @param {Design} design @param {boolean} preview */
function makeCard(design, preview) {
  const card = document.createElement('article');
  const headingId = `${preview ? 'preview' : 'design'}-${design.id}-title`;
  card.className = `design-card layout-${design.layout}`;
  card.dataset.design = design.id;
  card.setAttribute('aria-labelledby', headingId);
  applyPalette(card, design);
  const palette = design[mode];
  const nodeColors = [palette.accent, palette.accent2, palette.ok, palette.accent, palette.accent2, palette.ok];
  const nodes = [
    ['Task input', 'one entry'], ['Client grid', 'four clients'], ['Skill layer', 'tools and MCP'],
    ['Hybrid router', 'local or hosted'], ['Model fleet', 'fit before pull'], ['Governance', 'owner gated']
  ].map((node, index) => `<div class="mock-node${index === 3 ? ' on' : ''}" style="--node-color:${nodeColors[index]}"><strong>${node[0]}</strong><small>${node[1]}</small></div>`).join('');
  const textRatio = contrastRatio(palette.ink, palette.bg);
  const accentRatio = contrastRatio(palette.accent, palette.panel);
  card.innerHTML = `
    <div class="mock-top">
      <div class="mock-brand"><span class="mock-mark" aria-hidden="true">MR</span><span><strong>Master Repo Use</strong><small>${escapeHTML(design.label)}</small></span></div>
      <span class="mock-health"><i></i>map live</span>
    </div>
    <div class="mock-intro"><span class="mock-index">${design.index} ${escapeHTML(design.label)}</span><h2 id="${headingId}">${escapeHTML(design.name)}</h2><p>${escapeHTML(design.description)}</p></div>
    <div class="mock-tabs" aria-label="V7 Graphite Atlas facts"><span class="mock-tab on">Full map 52</span><span class="mock-tab">16 lanes</span><span class="mock-tab">12 canvases</span><span class="mock-tab">36 routes</span></div>
    <div class="mock-work">
      <section class="mock-map" aria-label="Graphite map preview">${nodes}</section>
      <aside class="mock-rail"><div><h3>Setup rail</h3><div class="rail-meta">3 selected in route order</div><span class="mock-chip" style="--chip:${palette.accent}"><i></i>Router</span><span class="mock-chip" style="--chip:${palette.accent2}"><i></i>Hosted fallback</span><span class="mock-chip" style="--chip:${palette.ok}"><i></i>Guardian</span></div><div class="mock-code"><span># hybrid routing</span>mru route local then hosted</div></aside>
    </div>
    <div class="mock-metrics"><div class="mock-stat" style="--stat:${palette.accent}"><small>Components</small><strong>52</strong></div><div class="mock-stat" style="--stat:${palette.accent2}"><small>Lanes</small><strong>16</strong></div><div class="mock-stat" style="--stat:${palette.ok}"><small>Canvases</small><strong>12</strong></div></div>
    <footer class="card-foot"><div class="contrast" data-contrast><span><b>${textRatio}:1</b> text</span><span><b>${accentRatio}:1</b> accent</span></div><div class="card-actions"></div></footer>`;

  if (!preview) {
    const actions = card.querySelector('.card-actions');
    const previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.textContent = 'Preview';
    previewButton.setAttribute('aria-label', `Preview ${design.name}`);
    previewButton.addEventListener('click', () => openPreview(design, previewButton));
    const shortlistButton = document.createElement('button');
    shortlistButton.type = 'button';
    shortlistButton.className = 'shortlist';
    shortlistButton.dataset.shortlist = design.id;
    shortlistButton.setAttribute('aria-pressed', String(shortlist === design.id));
    shortlistButton.setAttribute('aria-label', `Shortlist ${design.name}`);
    shortlistButton.textContent = shortlist === design.id ? 'Shortlisted' : 'Shortlist';
    shortlistButton.addEventListener('click', () => setShortlist(design.id));
    actions.append(previewButton, shortlistButton);
  }
  return card;
}

function renderGrid() {
  applyStudioMode();
  designGrid.replaceChildren(...DESIGNS.map((design) => makeCard(design, false)));
  updateModeButtons();
  updateChoiceStatus();
}

function refreshCards() {
  applyStudioMode();
  document.querySelectorAll('.design-card[data-design]').forEach((card) => {
    const design = DESIGNS.find((entry) => entry.id === card.dataset.design);
    if (!design) return;
    applyPalette(/** @type {HTMLElement} */ (card), design);
    const palette = design[mode];
    const contrast = card.querySelector('[data-contrast]');
    if (contrast) contrast.innerHTML = `<span><b>${contrastRatio(palette.ink, palette.bg)}:1</b> text</span><span><b>${contrastRatio(palette.accent, palette.panel)}:1</b> accent</span>`;
  });
  updateModeButtons();
  if (previewId && previewDialog.open) {
    const design = DESIGNS.find((entry) => entry.id === previewId);
    if (design) renderPreview(design);
  }
}

function applyStudioMode() {
  document.documentElement.dataset.studioMode = mode;
}

function updateModeButtons() {
  modeButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.mode === mode)));
}

function updateChoiceStatus() {
  const design = DESIGNS.find((entry) => entry.id === shortlist);
  choiceStatus.innerHTML = design
    ? `<strong>${escapeHTML(design.name)} is shortlisted.</strong> The V7 Graphite Atlas and 36 hybrid route rules stay the same when this direction is applied.`
    : '<strong>No design shortlisted.</strong> Preview any option, then save one direction.';
  document.querySelectorAll('[data-shortlist]').forEach((button) => {
    const selected = button.dataset.shortlist === shortlist;
    button.setAttribute('aria-pressed', String(selected));
    button.textContent = selected ? 'Shortlisted' : 'Shortlist';
  });
}

/** @param {string} id */
function setShortlist(id) {
  shortlist = shortlist === id ? null : id;
  try {
    if (shortlist) localStorage.setItem(STORAGE.shortlist, shortlist);
    else localStorage.removeItem(STORAGE.shortlist);
  } catch (_) {}
  updateChoiceStatus();
  showToast(shortlist ? 'Design shortlisted' : 'Shortlist cleared');
}

/** @param {Design} design */
function renderPreview(design) {
  previewTitle.textContent = `${design.name} full preview`;
  previewBody.replaceChildren(makeCard(design, true));
}

/** @param {Design} design @param {HTMLElement | null} trigger */
function openPreview(design, trigger) {
  lastTrigger = trigger;
  previewId = design.id;
  renderPreview(design);
  if (!previewDialog.open) previewDialog.showModal();
  history.replaceState(null, '', `${location.pathname}#${design.id}`);
}

function closePreview() {
  if (previewDialog.open) previewDialog.close();
}

/** @param {string} message */
function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 1500);
}
let toastTimer = 0;

modeButtons.forEach((button) => button.addEventListener('click', () => {
  const next = button.dataset.mode;
  if (next !== 'light' && next !== 'dark') return;
  /** @type {StudioMode} */
  mode = next;
  try { localStorage.setItem(STORAGE.mode, mode); } catch (_) {}
  refreshCards();
}));

previewClose.addEventListener('click', closePreview);
previewDialog.addEventListener('click', (event) => {
  if (event.target === previewDialog) closePreview();
});
previewDialog.addEventListener('close', () => {
  previewId = null;
  history.replaceState(null, '', location.pathname);
  if (lastTrigger) lastTrigger.focus();
  lastTrigger = null;
});

const requestedId = decodeURIComponent(location.hash.slice(1));
renderGrid();
if (requestedId) {
  const design = DESIGNS.find((entry) => entry.id === requestedId);
  if (design) setTimeout(() => openPreview(design, null), 0);
}

window.addEventListener('hashchange', () => {
  const requested = decodeURIComponent(location.hash.slice(1));
  const design = DESIGNS.find((entry) => entry.id === requested);
  if (design && (!previewDialog.open || previewId !== design.id)) openPreview(design, null);
});

// Static contract guard. It makes missing palette keys obvious in development.
DESIGNS.forEach((design) => {
  for (const currentMode of /** @type {StudioMode[]} */ (['dark', 'light'])) {
    const palette = design[currentMode];
    REQUIRED_TOKENS.forEach((token) => {
      if (!palette[token]) throw new Error(`${design.id} ${currentMode} palette is missing ${token}`);
    });
  }
});
