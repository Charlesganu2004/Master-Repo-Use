/* The "+" on every surface group: configure a client that is not in the list.
 *
 * One implementation for both pages. The main page (atlas.js) and every design
 * (atlas-panes.js) call this; neither carries its own copy, because two copies
 * of a command generator is two pages that will eventually disagree about what
 * to type for the same client. The command TEMPLATES are not here either: they
 * come from atlas-data.json (customSurfaceKinds), built and tested in Python.
 *
 * What this adds on top of the templates is the part that must not be sloppy:
 *
 *   - every field is checked against its pattern BEFORE anything is shown, so
 *     a pasted value cannot smuggle `; rm -rf ~` or `$(...)` into a command
 *     someone copies. The patterns are allowlists; see build_atlas_data.py
 *   - a URL is quoted when substituted, so a space or an ampersand cannot turn
 *     one command into two
 *   - saved clients live in this browser only (localStorage), because they are
 *     one viewer's convenience, and every read and write is guarded: storage
 *     can be blocked, full, or absent in a preview, and the page must still work
 *
 * No dependencies, no network, no DOM of its own. The pages render; this
 * computes.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'atlas.customClients';
  // Fields whose value is substituted inside double quotes. A command field is
  // not quoted, because it IS the command; its pattern forbids shell operators.
  var QUOTED = { url: true };

  function kinds(data) {
    return (data && data.customSurfaceKinds) || [];
  }

  function kind(data, id) {
    var list = kinds(data);
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }

  function defaultKindFor(data, groupId) {
    var list = kinds(data);
    for (var i = 0; i < list.length; i++) {
      if ((list[i].defaultFor || []).indexOf(groupId) !== -1) return list[i].id;
    }
    return list.length ? list[0].id : null;
  }

  /* The name field's hint: the kind's first example, "OpenRouter" or "aider",
     which is what a person would actually call it. Built from the label it read
     "My an openai-compatible endpoint". */
  function namePlaceholder(spec) {
    var first = String((spec && spec.examples) || '').split(',')[0].trim();
    return first || 'My client';
  }

  /* A command split at its spaces, for rendering each word as one unbreakable
     unit. Left to the browser, a narrow column breaks after the hyphens in
     `--serve` and shows `--` and `serve` on separate lines, which reads as two
     arguments. The spaces between tokens stay the only break points. */
  function tokens(command) {
    return String(command).split(' ').filter(function (token) { return token !== ''; });
  }

  /* Validate every field, then substitute. Returns {ok, steps, limit} or
     {ok: false, error}. Nothing is returned for display unless ok is true. */
  function commands(data, kindId, values) {
    var spec = kind(data, kindId);
    if (!spec) return { ok: false, error: 'Unknown kind of client.' };
    values = values || {};
    var filled = {};
    for (var i = 0; i < spec.fields.length; i++) {
      var field = spec.fields[i];
      var raw = String(values[field.id] == null ? '' : values[field.id]).trim();
      if (!raw) return { ok: false, error: field.label + ' is required.' };
      if (field.options && field.options.indexOf(raw) === -1) {
        return { ok: false, error: field.label + ' must be one of: ' + field.options.join(', ') + '.' };
      }
      if (field.pattern && !(new RegExp(field.pattern)).test(raw)) {
        return { ok: false, error: field.label + ' has characters that are not allowed here.' };
      }
      filled[field.id] = QUOTED[field.id] ? '"' + raw + '"' : raw;
    }
    var steps = spec.steps.map(function (step) {
      var command = step.command.replace(/\{(\w+)\}/g, function (whole, name) {
        return Object.prototype.hasOwnProperty.call(filled, name) ? filled[name] : whole;
      });
      return { label: step.label, command: command };
    });
    return { ok: true, steps: steps, limit: spec.limit, label: spec.label };
  }

  function load() {
    try {
      var parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function store(list) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
      return true;
    } catch (e) {
      return false;
    }
  }

  /* An id that is unique among what is stored. A count-based id repeats after a
     removal (save two, remove the first, save a third with the second's name)
     and remove() would then delete both entries sharing it. */
  function freshId(list) {
    var taken = {};
    for (var i = 0; i < list.length; i++) taken[list[i].id] = true;
    var id;
    do {
      id = 'c' + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36);
    } while (taken[id]);
    return id;
  }

  /* Save a named client. Refuses anything that does not generate cleanly, so a
     saved entry can never show a command that failed validation. Saved entries
     are validated again every time they are shown, because storage is only as
     trustworthy as whatever last wrote to it. */
  function save(data, entry) {
    var result = commands(data, entry.kind, entry.values);
    if (!result.ok) return result;
    var name = String(entry.name || '').trim() || result.label;
    var list = load().filter(function (item) { return item.id !== entry.id; });
    var id = entry.id || freshId(list);
    list.push({ id: id, group: entry.group, name: name.slice(0, 60),
                kind: entry.kind, values: entry.values || {} });
    return store(list) ? { ok: true, id: id }
                       : { ok: false, error: 'This browser would not save it.' };
  }

  function remove(id) {
    return store(load().filter(function (item) { return item.id !== id; }));
  }

  function forGroup(groupId) {
    return load().filter(function (item) { return item.group === groupId; });
  }

  var api = { kinds: kinds, kind: kind, defaultKindFor: defaultKindFor,
              namePlaceholder: namePlaceholder, tokens: tokens,
              commands: commands, load: load, save: save, remove: remove,
              forGroup: forGroup, STORAGE_KEY: STORAGE_KEY };
  if (typeof window !== 'undefined') window.CustomSurfaces = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();
