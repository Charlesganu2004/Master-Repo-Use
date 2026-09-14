/* Run against an already privacy-verified public artifact, never the private checkout.
 * NODE_PATH may point at an existing Playwright installation. No downloads or installs.
 * node tests/pages_smoke.cjs --site <public-site> --out <session-artifacts>
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('playwright');

const args = process.argv.slice(2);
const option = key => args[args.indexOf(key) + 1];
assert(args.includes('--site') && args.includes('--out'), '--site and --out are required');
const site = path.resolve(option('--site'));
const output = path.resolve(option('--out'));
const navigationOnly = args.includes('--navigation-only');
assert(fs.existsSync(path.join(site, 'version.json')), 'Build the public artifact with version metadata first');
fs.mkdirSync(output, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };
const server = http.createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  const file = path.resolve(site, '.' + pathname + (pathname.endsWith('/') ? 'index.html' : ''));
  if (file !== site && !file.startsWith(site + path.sep)) { response.writeHead(403).end(); return; }
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { response.writeHead(404).end(); return; }
  response.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(response);
});
let routes = ['index.html', 'designs/index.html', ...fs.readdirSync(path.join(site, 'designs'))
  .filter(name => /^d\d.*\.html$/.test(name))
  .sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))
  .map(name => 'designs/' + name)];
if (fs.existsSync(path.join(site, 'design-options.html'))) routes.push('design-options.html');
if (args.includes('--routes')) routes = routes.filter(route => new RegExp(option('--routes')).test(route));
const viewports = [{ name: 'desktop', width: 1440, height: 900 }, { name: 'mobile', width: 390, height: 844 }];
const results = [];

async function overflow(page) {
  await page.evaluate(() => window.scrollTo({ left: 0, top: window.scrollY, behavior: 'instant' }));
  const dimensions = await page.evaluate(() => ({
    width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth
  }));
  if (dimensions.scroll > dimensions.width + 2) {
    const offenders = await page.evaluate(() => Array.from(document.querySelectorAll('body *')).filter(node => {
      const rect = node.getBoundingClientRect();
      return rect.width && rect.right > innerWidth + 2 && getComputedStyle(node).visibility !== 'hidden';
    }).slice(0, 12).map(node => ({ tag: node.tagName, id: node.id, class: String(node.className),
      right: node.getBoundingClientRect().right })));
    assert.fail(`horizontal overflow: ${JSON.stringify({ ...dimensions, offenders })}`);
  }
}

async function shot(page, stem, phase) {
  const filename = path.join(output, `${stem}-${phase}.png`);
  await page.screenshot({ path: filename, animations: 'disabled', fullPage: false });
  return filename;
}

async function clickable(locator) {
  await locator.scrollIntoViewIfNeeded();
  await locator.evaluate(node => node.scrollIntoView({ block: 'center', inline: 'center' }));
  const hit = await locator.evaluate(node => {
    const r = node.getBoundingClientRect();
    const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { ok: top === node || node.contains(top), target: node.outerHTML.slice(0, 160),
      covering: top && top.outerHTML.slice(0, 160), rect: {x:r.x,y:r.y,width:r.width,height:r.height},
      parent: node.parentElement.parentElement.className };
  });
  assert(hit.ok, 'control covered by another layer: ' + locator.toString() + ' ' + JSON.stringify(hit));
  await locator.click();
}

async function contrast(locator) {
  return locator.evaluate(node => {
    const rgb = value => {
      const values = value.match(/[\d.]+/g);
      if (!values) return null;
      const numbers = values.map(Number);
      if (value.startsWith('color(srgb')) return [...numbers.slice(0, 3).map(v => v * 255), numbers[3] ?? 1];
      return [...numbers.slice(0, 3), numbers[3] ?? 1];
    };
    const over = (front, back) => front.slice(0, 3).map((value, i) => value * front[3] + back[i] * (1 - front[3]));
    const chain = [];
    for (let ancestor = node; ancestor; ancestor = ancestor.parentElement) chain.unshift(ancestor);
    let background = [255, 255, 255], gradient = false;
    for (const ancestor of chain) {
      const style = getComputedStyle(ancestor);
      const color = rgb(style.backgroundColor);
      if (color && color[3] === 1) gradient = false;
      if (color) background = over(color, background);
      if (style.backgroundImage !== 'none') gradient = true;
    }
    if (gradient) return { measured: false, reason: 'Gradient background needs visual contrast review.' };
    const foreground = over(rgb(getComputedStyle(node).color), background);
    const luminance = color => color.map(v => {
      const value = v / 255;
      return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
    }).reduce((total, value, i) => total + value * [.2126, .7152, .0722][i], 0);
    const first = luminance(foreground), second = luminance(background);
    return { measured: true, ratio: (Math.max(first, second) + .05) / (Math.min(first, second) + .05),
      foreground: getComputedStyle(node).color, background: getComputedStyle(node).backgroundColor,
      compositeBackground: background };
  });
}

async function setup(page, root) {
  const prefix = root ? '#surfaceGroups' : '#stage';
  const groups = ['copilot', 'gemini', 'claude', 'chatgpt', 'open', 'other'];
  if (!root) {
    await clickable(page.locator('[data-os="windows"]').first());
    await clickable(page.locator('[data-tab="easy"]'));
  } else {
    await clickable(page.locator('[data-setup-os="windows"]'));
  }
  await page.waitForFunction(() => Boolean(window.CustomSurfaces));
  for (const group of groups) {
    const add = page.locator(`${prefix} [data-add-client="${group}"]`);
    await clickable(add);
    assert(await page.locator(`${prefix} [data-custom-kind]`).isVisible());
    if (['copilot', 'gemini', 'claude'].includes(group)) {
      assert.equal(await page.locator(`${prefix} [data-custom-field="client"]`).inputValue(), group);
      await clickable(page.locator(`${prefix} [data-custom-generate]`));
      const text = await page.locator(prefix).innerText();
      assert(text.includes(`-Client ${group}`), 'wrong local installer');
      assert(!text.includes('master-harness-super --install all'), 'unselected client installation');
    }
    await clickable(page.locator(`${prefix} [data-add-client="${group}"]`));
  }
  assert.equal(await page.locator(`${prefix} [data-surface^="model-"]`).count(), 0,
    'models visible without an explicit report');
  if (root) assert.equal(await page.locator('#hardwareFits').innerText(), '-',
    'hardware advisor inferred compatibility without a report');
  await page.locator(`${prefix} [data-surface="copilot-cli"]`).check();
  assert.equal(await page.evaluate(() => document.activeElement.dataset.surface), 'copilot-cli',
    'selection rerender lost keyboard focus');
  assert(await page.locator(`${prefix} [data-surface="copilot-cli"]`).evaluate(node =>
    parseFloat(getComputedStyle(node.closest('label')).outlineWidth) >= 2), 'missing visible selection focus ring');
  await page.locator(`${prefix} [data-surface="gemini-code-assist"]`).check();
  assert(await page.locator(`${prefix} [data-surface="copilot-cli"]`).isChecked());
  assert(await page.locator(`${prefix} [data-surface="gemini-code-assist"]`).isChecked());
  const reportInput = page.locator(root ? '#setupReport' : '#hardwareReport');
  await reportInput.locator('xpath=ancestor::details/summary').click();
  await reportInput.fill('{"schema":"wrong"}');
  await clickable(page.locator(root ? '#setupReportApply' : '#hardwareReportApply'));
  assert.equal(await page.locator(`${prefix} [data-surface^="model-"]`).count(), 0);
  // This is an explicit synthetic fixture, not a claim about the test machine.
  const report = JSON.stringify({ schema: 'atlas.hardware.v1', platform: 'windows', ramGb: 8,
    compatibleModels: ['gemma3:1b', 'qwen3:32b'] });
  if (!root) await page.locator('#hardwareReport').locator('xpath=ancestor::details/summary').click();
  await page.locator(root ? '#setupReport' : '#hardwareReport').fill(report);
  await clickable(page.locator(root ? '#setupReportApply' : '#hardwareReportApply'));
  assert.equal(await page.locator(`${prefix} [data-surface="model-gemma3-1b"]`).count(), 1);
  assert.equal(await page.locator(`${prefix} [data-surface="model-qwen3-32b"]`).count(), 0);
  if (root) assert.equal(await page.locator('#hardwareFits').innerText(), '1');
  await page.locator(`${prefix} [data-surface="model-gemma3-1b"]`).check();
  await clickable(page.locator(root ? '[data-setup-os="linux"]' : '[data-os="linux"]').first());
  assert.equal(await page.locator(`${prefix} [data-surface^="model-"]`).count(), 0,
    'changing OS must invalidate incompatible report selections');
  const measurement = await contrast(page.locator(`${prefix} [data-add-client="copilot"]`));
  if (measurement.measured) assert(measurement.ratio >= 4.5, `setup action contrast ${measurement.ratio.toFixed(2)}:1`);
  return measurement;
}

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
  try {
    for (const viewport of viewports) {
      for (const route of routes) {
        const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height },
          deviceScaleFactor: 1, reducedMotion: 'reduce' });
        // Never send page content or telemetry to a third party.
        await context.route('**/*', async request => {
          if (request.request().url().startsWith(origin + '/')) await request.continue();
          else await request.abort('blockedbyclient');
        });
        const page = await context.newPage();
        page.setDefaultTimeout(5000);
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
        page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
        const stem = route.replace(/[/\\.]/g, '-') + '-' + viewport.name;
        const result = { route, viewport, zoom: '100%', deviceScaleFactor: 1,
          checks: navigationOnly ? 'navigation-and-contrast' : 'full-controls', screenshots: [], errors };
        try {
          const response = await page.goto(origin + '/' + route, { waitUntil: 'networkidle' });
          assert.equal(response.status(), 200);
          assert(await page.locator('body').innerText(), 'blank page');
          if (await page.locator('[data-open-command]').count()) {
            result.sceneActionContrast = await contrast(page.locator('[data-open-command]'));
            assert(result.sceneActionContrast.measured && result.sceneActionContrast.ratio >= 4.5,
              'scene navigation requires measured contrast of at least 4.5:1');
          }
          await overflow(page);
          result.screenshots.push(await shot(page, stem, 'first'));
          if (await page.locator('[data-open-atlas], #mgOpenAtlas').count()) {
            const mongo = await page.locator('#mgOpenAtlas').count();
            const commandButton = page.locator(mongo ? '#mgOpenCommands' : '[data-open-command]');
            const atlasButton = page.locator(mongo ? '#mgOpenAtlas' : '[data-open-atlas]');
            const returnButton = page.locator(mongo ? '#mgReturn' : '[data-return-concept]');
            const sceneControl = page.locator('#exhibitionRoot button[data-lane]').first();
            if (await sceneControl.count()) await clickable(sceneControl);
            await clickable(commandButton);
            assert.equal(await page.evaluate(() => AtlasPanes.tab), 'commands');
            assert(await page.locator('#stage').isVisible());
            await overflow(page);
            result.screenshots.push(await shot(page, stem, 'commands'));
            await clickable(returnButton);
            await clickable(atlasButton);
            assert(await page.locator('#setup').isVisible());
            if (!navigationOnly) result.setupActionContrast = await setup(page, false);
            await overflow(page);
            result.screenshots.push(await shot(page, stem, navigationOnly ? 'atlas' : 'setup'));
            const query = page.locator('#fq');
            if (await query.count()) {
              await query.fill('nonexistent-smoke-filter');
              assert.equal(await page.evaluate(() => AtlasCore.visibleComponents().length), 0);
              await query.fill('');
            }
          } else if (route === 'index.html') {
            if (!navigationOnly) {
              result.setupActionContrast = await setup(page, true);
              result.screenshots.push(await shot(page, stem, 'setup'));
            }
          } else if (await page.locator('#tabs').count()) {
            if (!navigationOnly) result.setupActionContrast = await setup(page, false);
            await overflow(page);
            result.screenshots.push(await shot(page, stem, navigationOnly ? 'atlas' : 'setup'));
          }
          if (await page.locator('#atlas-tab-easy').count()) {
            await page.locator('#atlas-tab-easy').focus();
            await page.keyboard.press('Home');
            assert.equal(await page.evaluate(() => AtlasPanes.tab), 'map');
            await page.keyboard.press('ArrowRight');
            assert.notEqual(await page.evaluate(() => AtlasPanes.tab), 'map');
            result.keyboardTabs = 'passed';
          }
          assert.deepEqual(errors, [], 'browser runtime/console errors');
          result.status = 'passed';
        } catch (error) {
          result.status = 'failed';
          result.failure = error.message;
          result.layout = await page.evaluate(() => ({
            scrollX, width: innerWidth, document: document.documentElement.scrollWidth,
            body: {width: document.body.clientWidth, scroll: document.body.scrollWidth},
            overflowing: Array.from(document.querySelectorAll('body *')).filter(node =>
              node.clientWidth > 0 && node.scrollWidth > node.clientWidth + 2
            ).slice(0, 18).map(node => ({tag:node.tagName,id:node.id,class:String(node.className),
              width:node.clientWidth,scroll:node.scrollWidth,overflow:getComputedStyle(node).overflowX}))
          }));
          result.screenshots.push(await shot(page, stem, 'failure'));
        }
        results.push(result);
        fs.writeFileSync(path.join(output, 'progress.json'), JSON.stringify(results, null, 2));
        console.log(`${result.status}: ${route} ${viewport.name}${result.failure ? ': ' + result.failure : ''}`);
        await context.close();
      }
    }
  } finally {
    await browser.close();
    server.close();
    fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify({
      generatedAt: new Date().toISOString(), publicSite: site, browser: chromium.executablePath(),
      results, passed: results.filter(r => r.status === 'passed').length,
      failed: results.filter(r => r.status !== 'passed').length
    }, null, 2));
  }
  if (results.some(result => result.status !== 'passed')) process.exitCode = 1;
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
