"""Extract every distinct index.html from history into ui-history/ and build a gallery.

Each extracted file gets a <base href="/"> injected so its relative fetches for
docs/hardware-profiles.json and docs/catalog-status.json still resolve when it is
served from a subfolder.
"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'ui-history'
OUT.mkdir(exist_ok=True)

VERSIONS = [
    ('v1', '0911870', 'Tabs and cards',
     'Where it started. A tab bar over a grid of command cards. Blue and violet '
     'accents, 14px base, 12px card copy.'),
    ('v2', 'caaa55d', 'Readability pass',
     'Same tabs and cards, but rebuilt for contrast: light and dark toggle, larger '
     'type, and the security scan that had never run.'),
    ('v3', '1178bc5', 'Warm palette, map first',
     'No blue. Amber, copper and sage. The System Map became the landing view and '
     'each node carried the one command that operates it.'),
    ('v4', '1cfff13', 'Mechanism map',
     'Four views, each drawing a mechanism rather than an inventory. Every arrow '
     'labelled with what actually passes along it.'),
    ('v5', 'e70976b', 'Setup builder',
     'A picker. Five maps, multi-select across all of them, eight presets, and a '
     'composed setup script per platform.'),
    ('v6', '5c2fb8e', 'Graphite, one map end to end',
     'Current. Near monochrome with one hot accent. 28 components across 8 lanes on '
     'a single canvas, lenses that dim rather than split, plus hybrid model routing.'),
]

BASE = '<base href="/">'
for slug, sha, name, _ in VERSIONS:
    try:
        html = subprocess.run(['git', 'show', f'{sha}:index.html'], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        print(f'  MISSING {slug} at {sha}')
        continue
    if BASE not in html:
        html = re.sub(r'(<meta charset="utf-8">)', r'\1\n' + BASE, html, count=1)
    (OUT / f'{slug}.html').write_text(html, encoding='utf-8')
    print(f'  {slug}  {sha}  {len(html):>7} bytes  {name}')

cards = []
for slug, sha, name, note in VERSIONS:
    if not (OUT / f'{slug}.html').exists():
        continue
    cards.append(f'''  <article class="v">
    <header>
      <div><h2>{slug.upper()}  {name}</h2><p>{note}</p></div>
      <a class="open" href="ui-history/{slug}.html" target="_blank" rel="noopener">Open full size</a>
    </header>
    <div class="frame"><iframe src="ui-history/{slug}.html" title="{name}" loading="lazy"></iframe></div>
  </article>''')

page = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Master Repo Use: UI history</title>
<style>
/* Every version is rendered live in an iframe at 1600px logical width, scaled
   down, so you are comparing real pages rather than screenshots. */
*{box-sizing:border-box}
body{margin:0;background:#131314;color:#fafafb;
  font:16.5px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1860px;margin:auto;padding:26px 30px 70px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.02em}
.sub{color:#a9a9b2;margin:0 0 26px;font-size:17px;max-width:86ch;font-weight:500}
.sub b{color:#fafafb}
.v{border:1px solid rgba(228,228,232,.17);border-radius:14px;background:#1c1c1e;
  overflow:hidden;margin-bottom:22px}
.v header{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;
  padding:16px 20px;border-bottom:1px solid rgba(228,228,232,.17);flex-wrap:wrap}
.v h2{margin:0;font-size:18px;letter-spacing:-.02em}
.v p{margin:4px 0 0;color:#a9a9b2;font-size:14.5px;font-weight:500;max-width:92ch}
.open{border:1px solid rgba(228,228,232,.17);background:#262628;color:#fafafb;
  border-radius:9px;padding:9px 14px;font-size:14px;font-weight:650;text-decoration:none;flex:none}
.open:hover{border-color:#ff8a3d;color:#ff8a3d}
.frame{height:560px;overflow:hidden;background:#0c0c0d;position:relative}
.frame iframe{width:1600px;height:1245px;border:0;transform:scale(.45);
  transform-origin:0 0;display:block}
@media(max-width:1100px){.frame{height:430px}.frame iframe{transform:scale(.34);height:1265px}}
</style>
</head>
<body>
<div class="wrap">
<h1>UI history</h1>
<p class="sub">Six versions of this page, oldest first, each <b>rendered live</b> rather than
screenshotted. They are scaled to 45 percent, so open one full size to judge type and spacing
properly. V6 is what is on the current branch.</p>
''' + '\n'.join(cards) + '''
</div>
</body>
</html>
'''
(ROOT / 'ui-history.html').write_text(page, encoding='utf-8')
print('\nui-history.html written with', len(cards), 'versions')
