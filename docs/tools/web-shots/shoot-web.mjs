/*
 * Screenshots of the Shvatka web UI for the documentation.
 * Expects the built UI on :4300 and the mock API on :8099.
 *   node shoot-web.mjs <shots.json> <out-dir>
 */
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const shots = JSON.parse(fs.readFileSync(process.argv[2], 'utf-8'));
const outDir = path.resolve(process.argv[3]);
const base = 'http://127.0.0.1:4300';

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: {width: 1180, height: 900},
  deviceScaleFactor: 2,
  locale: 'ru-RU',
  timezoneId: 'Europe/Moscow',
});
// the telegram login widget is the only external asset; block it so the page settles
await context.route('**://telegram.org/**', r => r.abort());
const page = await context.newPage();

// sticky chrome would otherwise overlap element clips
const HIDE_STICKY = 'app-header, .actions-bar {visibility: hidden !important;}';

for (const shot of shots) {
  const {url, out, clicks = [], clip, wait = 800} = shot;
  await page.goto(base + url, {waitUntil: 'networkidle'});
  await page.waitForTimeout(wait);
  for (const sel of clicks) {
    const el = page.locator(sel).first();
    if (await el.count() === 0) {
      console.log(`  no match for click ${sel}`);
      continue;
    }
    await el.click();
    await page.waitForTimeout(400);
  }
  const file = path.join(outDir, out);
  fs.mkdirSync(path.dirname(file), {recursive: true});
  if (clip) {
    await page.addStyleTag({content: HIDE_STICKY});
    const target = page.locator(clip).first();
    await target.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await target.screenshot({path: file});
  } else {
    await page.screenshot({path: file, fullPage: true});
  }
  console.log(`${url} -> ${out} (${Math.round(fs.statSync(file).size / 1024)} KB)`);
}

await browser.close();
