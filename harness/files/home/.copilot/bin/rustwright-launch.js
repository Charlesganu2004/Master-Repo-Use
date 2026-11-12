#!/usr/bin/env node
// Launches rustwright-mcp with RUSTWRIGHT_CHROMIUM resolved at runtime, so a
// Playwright browser upgrade (chromium-1234 -> chromium-####) does not break it.
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const SERVER = path.join(os.homedir(), '.local', 'node', 'node_modules',
  'rustwright-mcp', 'bin', 'rustwright-mcp.js');

function findChromium() {
  if (process.env.RUSTWRIGHT_CHROMIUM && fs.existsSync(process.env.RUSTWRIGHT_CHROMIUM)) {
    return process.env.RUSTWRIGHT_CHROMIUM;
  }

  const root = path.join(process.env.LOCALAPPDATA || '', 'ms-playwright');
  try {
    const builds = fs.readdirSync(root)
      .filter((d) => d.startsWith('chromium-'))
      .map((d) => ({ dir: d, n: parseInt(d.split('-')[1], 10) || 0 }))
      .sort((a, b) => b.n - a.n);
    for (const b of builds) {
      for (const sub of ['chrome-win64', 'chrome-win']) {
        const exe = path.join(root, b.dir, sub, 'chrome.exe');
        if (fs.existsSync(exe)) return exe;
      }
    }
  } catch { /* ms-playwright missing; fall through to system browsers */ }

  const fallbacks = [
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  ];
  return fallbacks.find((p) => fs.existsSync(p)) || null;
}

if (process.argv.includes('--which-chromium')) {
  process.stdout.write((findChromium() || 'NONE') + '\n');
  process.exit(0);
}

const chromium = findChromium();
const env = Object.assign({}, process.env);
if (chromium) env.RUSTWRIGHT_CHROMIUM = chromium;

const child = spawn(process.execPath, [SERVER, ...process.argv.slice(2)], {
  stdio: 'inherit',
  env,
});
child.on('exit', (code, signal) => process.exit(signal ? 1 : code === null ? 1 : code));
