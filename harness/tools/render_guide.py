#!/usr/bin/env python3
"""Render harness/SETUP.md into HARNESS-SETUP.md and a self-contained HARNESS-SETUP.html.

Usage:
    uv run --no-project --with markdown python harness/tools/render_guide.py \
        --in harness/SETUP.md --out-dir <dir> [--set vertex-project-id=my-project ...]
        [--md-name NAME] [--html-name NAME] [--no-md]

Each --set key=value replaces the literal <key> in the guide text.
The public page is: --out-dir harness --html-name SETUP.html --no-md.
The HTML has inline CSS and JS only: no fonts, CDNs or images.
"""
import argparse
import html
import re
import sys
from pathlib import Path

import markdown

SELF_LINK = "](SETUP.html)"

CSS = """
:root { --accent: #0b5cad; --text: #24292f; --muted: #57606a; --line: #d0d7de; --soft: #f6f8fa; --r: 8px; --r-sm: 4px; }
* { box-sizing: border-box; }
html { background: #ffffff; }
body { margin: 0; background: #ffffff; color: var(--text); font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
main { max-width: 820px; margin: 0 auto; padding: 40px 20px 80px; }
h1 { font-size: 2rem; line-height: 1.25; margin: 0 0 16px; }
h2 { font-size: 1.4rem; margin: 2.2rem 0 0.8rem; padding-top: 0.4rem; border-top: 1px solid var(--line); }
h3 { font-size: 1.1rem; margin: 1.6rem 0 0.6rem; }
p, ul, ol { margin: 0.7rem 0; }
li { margin: 0.3rem 0; }
a { color: var(--accent); }
nav.toc { background: var(--soft); border: 1px solid var(--line); border-radius: var(--r); padding: 14px 20px; margin: 20px 0; }
nav.toc strong { display: block; margin-bottom: 6px; }
nav.toc ol { margin: 0; padding-left: 1.4rem; }
code { font-family: ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 0.9em; background: var(--soft); border: 1px solid var(--line); border-radius: var(--r-sm); padding: 0.1em 0.35em; white-space: nowrap; }
.codeblock { margin: 0.9rem 0; background: var(--soft); border: 1px solid var(--line); border-radius: var(--r); overflow: hidden; }
.codebar { display: flex; justify-content: flex-end; padding: 6px 8px; border-bottom: 1px solid var(--line); background: #ffffff; }
.codeblock pre { margin: 0; padding: 14px 16px; overflow-x: auto; }
.codeblock pre code { background: none; border: 0; padding: 0; font-size: 0.88rem; line-height: 1.5; white-space: pre; }
.copy-btn { min-width: 64px; font: 600 0.8rem system-ui, -apple-system, "Segoe UI", Arial, sans-serif; color: var(--accent); background: #ffffff; border: 1px solid var(--accent); border-radius: var(--r-sm); padding: 4px 10px; cursor: pointer; }
.copy-btn:hover, .copy-btn:focus-visible { background: var(--accent); color: #ffffff; outline: none; }
.copy-btn.done { background: var(--accent); color: #ffffff; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.95rem; }
th, td { border: 1px solid var(--line); padding: 8px 12px; text-align: left; vertical-align: top; }
th { background: var(--soft); }
@media print {
  main { max-width: none; padding: 0; }
  .copy-btn, .codebar, nav.toc { display: none; }
  .codeblock { border-color: #999999; }
  .codeblock pre { white-space: pre-wrap; word-break: break-word; }
  .codeblock pre code { white-space: pre-wrap; }
  h2 { break-after: avoid; }
  .codeblock, table { break-inside: avoid; }
}
"""

JS = """
(function () {
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () { fallbackCopy(text); });
    }
    fallbackCopy(text);
    return Promise.resolve();
  }
  var buttons = document.querySelectorAll('.copy-btn');
  Array.prototype.forEach.call(buttons, function (btn) {
    btn.addEventListener('click', function () {
      var block = btn.closest('.codeblock');
      var code = block ? block.querySelector('pre code') : null;
      var text = code ? code.textContent.replace(/\\n$/, '') : '';
      copyText(text).then(function () {
        btn.textContent = 'Copied';
        btn.classList.add('done');
        setTimeout(function () {
          btn.textContent = 'Copy';
          btn.classList.remove('done');
        }, 1500);
      });
    });
  });
})();
"""


def apply_replacements(text, pairs):
    for key, value in pairs:
        text = text.replace("<" + key + ">", value)
    return text


def wrap_code_blocks(body):
    def repl(match):
        return (
            '<div class="codeblock"><div class="codebar">'
            '<button type="button" class="copy-btn" aria-label="Copy command">Copy</button></div>'
            + match.group(0)
            + "</div>"
        )

    return re.sub(r"<pre>.*?</pre>", repl, body, flags=re.S)


def build_toc(body):
    items = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body, flags=re.S):
        label = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        items.append('<li><a href="#%s">%s</a></li>' % (m.group(1), html.escape(label)))
    if not items:
        return ""
    return '<nav class="toc" aria-label="Contents"><strong>Contents</strong><ol>' + "".join(items) + "</ol></nav>"


def render_html(md_text):
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])
    body = md.convert(md_text)
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S)
    title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))) if title_match else "Setup guide"
    toc = build_toc(body)
    body = wrap_code_blocks(body)
    if title_match:
        # Place the table of contents after the intro paragraph that follows the h1.
        body = re.sub(r"(</h1>\s*<p>.*?</p>)", lambda m: m.group(1) + toc, body, count=1, flags=re.S)
        if toc not in body:
            body = body.replace("</h1>", "</h1>" + toc, 1)
    else:
        body = toc + body
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>" + html.escape(title) + "</title>\n<style>" + CSS + "</style>\n</head>\n<body>\n<main>\n"
        + body
        + "\n</main>\n<script>" + JS + "</script>\n</body>\n</html>\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Render the harness setup guide to Markdown and HTML.")
    parser.add_argument("--in", dest="src", required=True, help="source Markdown file")
    parser.add_argument("--out-dir", required=True, help="output directory")
    parser.add_argument("--md-name", default="HARNESS-SETUP.md", help="file name for the Markdown output")
    parser.add_argument("--html-name", default="HARNESS-SETUP.html", help="file name for the HTML output")
    parser.add_argument("--no-md", action="store_true", help="skip writing the Markdown output")
    parser.add_argument("--set", dest="sets", action="append", default=[], metavar="key=value",
                        help="replace the literal <key> with value (repeatable)")
    args = parser.parse_args()

    pairs = []
    for item in args.sets:
        if "=" not in item:
            sys.exit("--set expects key=value, got: " + item)
        key, value = item.split("=", 1)
        pairs.append((key, value))

    text = Path(args.src).read_text(encoding="utf-8")
    text = apply_replacements(text, pairs)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # The Markdown links to the HTML page; the HTML page drops that line, since it is the page.
    html_lines = [ln for ln in text.split("\n") if SELF_LINK not in ln]
    md_out = out_dir / args.md_name
    html_out = out_dir / args.html_name
    if not args.no_md:
        md_text = text.replace(SELF_LINK, "](" + args.html_name + ")")
        md_out.write_text(md_text, encoding="utf-8", newline="\n")
        print("wrote " + str(md_out))
    html_out.write_text(render_html("\n".join(html_lines)), encoding="utf-8", newline="\n")
    print("wrote " + str(html_out))


if __name__ == "__main__":
    main()
