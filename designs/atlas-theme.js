/* Palette switching, shared by every design.
 *
 * A design keeps its own layout, motion and structure; only the colour tokens
 * change. That makes the palettes comparable: switching to ember on the console
 * and on graphite shows the same red, so the thing being judged is the design
 * rather than the paint.
 *
 * Order of precedence: ?theme= in the URL, then whatever was last chosen in this
 * browser, then the design's own default.
 */
'use strict';

const AtlasTheme = (() => {

  const THEMES = [
    { id: 'ember',  label: 'Ember',   bg: '#0b0708', accent: '#ff3b3b',
      note: 'Red on near-black.' },
    { id: 'ash',    label: 'Ash',     bg: '#0e0f11', accent: '#f97316',
      note: 'Neutral graphite, nothing competing for attention.' },
    { id: 'viper',  label: 'Viper',   bg: '#0b0c0b', accent: '#9ae66e',
      note: 'Phosphor green on black.' },
    { id: 'cobalt', label: 'Cobalt',  bg: '#080b12', accent: '#3b82f6',
      note: 'Cold blue steel, the calmest dark palette.' },
    { id: 'plum',   label: 'Plum',    bg: '#0a0710', accent: '#e879f9',
      note: 'Magenta and violet, most separation between kinds.' },
    { id: 'sand',   label: 'Sand',    bg: '#f6f3ee', accent: '#b4451f',
      note: 'The light one, for a room with a window in it.' },
  ];

  function read(key, fallback) {
    try { return localStorage.getItem(key) || fallback; } catch (_) { return fallback; }
  }

  function write(key, value) {
    try { localStorage.setItem(key, value); } catch (_) { /* non-fatal */ }
  }

  /** URL wins, so a link can carry a palette to someone else. */
  function initial(defaultTheme) {
    let fromUrl = null;
    try {
      fromUrl = new URLSearchParams(location.search).get('theme');
    } catch (_) { /* file:// with no query is fine */ }
    const chosen = fromUrl || read('atlas.theme', defaultTheme);
    return THEMES.some(t => t.id === chosen) ? chosen : defaultTheme;
  }

  function apply(id) {
    document.documentElement.setAttribute('data-theme', id);
    write('atlas.theme', id);
    const bar = document.querySelector('.themebar');
    if (bar) bar.querySelectorAll('[data-theme-id]').forEach(b =>
      b.classList.toggle('on', b.dataset.themeId === id));
  }

  /** Renders the switcher into `host` and applies the starting palette. */
  function mount(host, defaultTheme = 'ember') {
    const current = initial(defaultTheme);
    apply(current);
    if (!host) return current;
    host.className = 'themebar';
    host.innerHTML = `<span class="tlabel">Palette</span>` + THEMES.map(t =>
      `<button class="swatch${t.id === current ? ' on' : ''}" data-theme-id="${t.id}"
        title="${t.label}: ${t.note}"
        style="background:${t.bg}"><i style="background:${t.accent}"></i></button>`).join('');
    host.querySelectorAll('[data-theme-id]').forEach(b => {
      b.onclick = () => apply(b.dataset.themeId);
    });
    return current;
  }

  return { THEMES, mount, apply, initial };
})();

/* Published on window as well as the script-scope binding.
   A top level `const` in a classic script is script-scoped, not a property
   of window, so `window.AtlasTheme` was undefined while the bare `AtlasTheme`
   worked. atlas-exhibition.js reads these through window, so its guard
   `if (!A || !P) return;` fired on every call and workspace() built nothing.
   That is why d31 rendered a root map with no atlas behind it, and why the
   Command center button on the other exhibition designs revealed the atlas
   without ever switching the tab. */
if (typeof window !== 'undefined') window.AtlasTheme = AtlasTheme;
