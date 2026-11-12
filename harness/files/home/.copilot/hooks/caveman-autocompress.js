#!/usr/bin/env node
/**
 * caveman-autocompress
 *
 * Watches live context-window pressure for the current Copilot session and,
 * once usage crosses a threshold, tells the agent to run the
 * `cavemanultracompress` routine before the runtime's own compaction fires.
 *
 * Wired through ~/.copilot/hooks/caveman-autocompress.json.
 * Fail-safe by design: any error exits 0 with empty output so the session is
 * never blocked or slowed by this hook.
 */

'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const DEFAULT_TIERS = [0.7, 0.8, 0.9];

// Fraction of the context window at which the Copilot runtime starts its own
// background compaction. Used to back out a context-window estimate from the
// highest prompt size a model has ever actually reached on this machine.
const RUNTIME_COMPACTION_POINT = 0.8;

const MODEL_CONTEXT_SEEDS = {
  'claude-opus-5': 350000,
  'claude-opus-4.8': 200000,
  'claude-opus-4.7': 200000,
  'claude-sonnet-5': 200000,
  'claude-haiku-4.5': 200000,
  'gpt-5.6-sol': 264000,
  'gpt-5.6-terra': 264000,
  'gpt-5.6-luna': 264000,
  'gpt-5.5': 264000,
  'gpt-5.4': 264000,
  'gpt-5.4-mini': 128000,
  'gpt-5.3-codex': 264000,
  'gpt-5-mini': 128000,
  'gemini-3.7-flash': 1000000,
  'gemini-3.6-flash': 1000000,
  'gemini-3.5-flash': 1000000,
};

const DEFAULT_CONTEXT = 128000;

const stateDir = path.join(
  process.env.LOCALAPPDATA || path.join(os.homedir(), '.cache'),
  'caveman-autocompress',
);

function emit(obj) {
  process.stdout.write(JSON.stringify(obj || {}));
  process.exit(0);
}

/** Optional user overrides: { tiers: [0.7], contextWindows: { "model": 200000 } }. */
function loadConfig() {
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(stateDir, 'config.json'), 'utf8'));
    return cfg && typeof cfg === 'object' ? cfg : {};
  } catch {
    return {};
  }
}

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function copilotHome() {
  return process.env.COPILOT_HOME || path.join(os.homedir(), '.copilot');
}

function statePath(sessionId) {
  const safe = String(sessionId).replace(/[^A-Za-z0-9._-]/g, '_');
  return path.join(stateDir, safe + '.state.json');
}

function loadState(sessionId) {
  try {
    return JSON.parse(fs.readFileSync(statePath(sessionId), 'utf8'));
  } catch {
    return { firedTier: 0 };
  }
}

function saveState(sessionId, state) {
  try {
    fs.mkdirSync(stateDir, { recursive: true });
    fs.writeFileSync(statePath(sessionId), JSON.stringify(state));
  } catch {
    /* best effort */
  }
}

/** Latest prompt size, model, and turn for a session, plus that model's all-time high. */
function readUsage(sessionId) {
  let DatabaseSync;
  try {
    ({ DatabaseSync } = require('node:sqlite'));
  } catch {
    return null;
  }

  const dbPath = path.join(copilotHome(), 'session-store.db');
  if (!fs.existsSync(dbPath)) return null;

  let db;
  try {
    db = new DatabaseSync(dbPath, { readOnly: true });
    // Latest turn, not MAX: after a compaction the prompt shrinks, and a MAX
    // would stay pinned at the pre-compaction peak for the rest of the session.
    const current = db
      .prepare(
        'SELECT model, input_tokens AS tokens, turn_index FROM assistant_usage_events ' +
          'WHERE session_id = ? AND input_tokens IS NOT NULL ' +
          'ORDER BY turn_index DESC, rowid DESC LIMIT 1',
      )
      .get(sessionId);

    if (!current || !current.tokens) return null;

    const high = db
      .prepare(
        'SELECT MAX(input_tokens) AS tokens FROM assistant_usage_events WHERE model = ?',
      )
      .get(current.model);

    return {
      model: current.model,
      tokens: Number(current.tokens),
      turnIndex: Number(current.turn_index || 0),
      highWater: Number(high && high.tokens ? high.tokens : 0),
    };
  } catch {
    return null;
  } finally {
    try {
      if (db) db.close();
    } catch {
      /* ignore */
    }
  }
}

/**
 * Context window for a model. The seed table is a floor; the all-time high
 * prompt size observed for that model raises the estimate when the seed is too
 * low, since the runtime only lets a prompt grow to ~80% before compacting.
 */
function contextWindowFor(model, highWater, config) {
  const overrides = (config && config.contextWindows) || {};
  const seed = overrides[model] || MODEL_CONTEXT_SEEDS[model] || DEFAULT_CONTEXT;
  if (overrides[model]) return overrides[model];
  const derived = highWater > 0 ? highWater / RUNTIME_COMPACTION_POINT : 0;
  return Math.max(seed, derived);
}

function directive(percent, tokens, limit) {
  return [
    '<caveman-autocompress>',
    'CONTEXT PRESSURE: this session is at ~' +
      percent +
      '% of the context window (' +
      tokens.toLocaleString('en-US') +
      ' / ~' +
      limit.toLocaleString('en-US') +
      ' tokens).',
    '',
    'Run the `cavemanultracompress` routine NOW, before continuing the task:',
    'restate the durable state of this session as one ultra-compressed caveman',
    'briefing, drop superseded tool output and dead ends, then carry on from the',
    'compressed briefing. Reproduce the PROTECTED RULES verbatim - they are never',
    'compressed, summarized, or dropped.',
    '',
    'Do this as part of the current turn. Do not ask permission first.',
    '</caveman-autocompress>',
  ].join('\n');
}

function main() {
  const raw = readStdin();
  if (!raw.trim()) emit({});

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    emit({});
  }

  const sessionId = payload.sessionId || payload.session_id;
  if (!sessionId) emit({});

  const event = String(process.argv[2] || '');

  if (event === 'sessionStart') {
    saveState(sessionId, {});
    emit({});
  }

  const usage = readUsage(sessionId);
  if (!usage) emit({});

  const config = loadConfig();
  const tiers = Array.isArray(config.tiers) && config.tiers.length ? config.tiers : DEFAULT_TIERS;
  const limit = contextWindowFor(usage.model, usage.highWater, config);
  const ratio = usage.tokens / limit;

  let tier = 0;
  for (const t of tiers) {
    if (ratio >= t) tier = t;
  }
  if (tier === 0) emit({});

  const state = loadState(sessionId);
  const primary = state.postToolUse || {};
  const text = directive(Math.round(ratio * 100), usage.tokens, Math.round(limit));

  if (event === 'agentStop') {
    // Fallback channel. Only speaks up when the primary channel demonstrably did
    // not land: either no tool ran at this tier, or it delivered on an earlier
    // turn and the prompt still has not shrunk. Blocks at most once per tier,
    // well inside the runtime's consecutive-block guard.
    const stopped = state.agentStop || {};
    if ((stopped.tier || 0) >= tier) emit({});
    const delivered = (primary.tier || 0) >= tier;
    if (delivered && usage.turnIndex <= (primary.turn || 0)) emit({});

    saveState(sessionId, {
      ...state,
      agentStop: { tier, turn: usage.turnIndex, at: Date.now() },
    });
    emit({ decision: 'block', reason: text });
  }

  if ((primary.tier || 0) >= tier) emit({});

  saveState(sessionId, {
    ...state,
    postToolUse: { tier, turn: usage.turnIndex, at: Date.now() },
  });
  emit({ additionalContext: text });
}

try {
  main();
} catch {
  emit({});
}
