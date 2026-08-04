/*
 * Screenshots of the Shvatka web UI for the documentation.
 * Expects shvatka-ui running against its own API stub — see the README.
 *   node shoot-web.mjs <shots.json> <out-dir>
 * UI_URL overrides the address (default http://localhost:4200).
 */
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const shots = JSON.parse(fs.readFileSync(process.argv[2], 'utf-8'));
const outDir = path.resolve(process.argv[3]);
// where the UI is served; `npm run start:mock` in shvatka-ui puts it here
const base = process.env.UI_URL ?? 'http://localhost:4200';

// channel: the default resolves to the headless shell, which crashes on this app
const browser = await chromium.launch({channel: 'chromium'});
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
  const {url, out, clicks = [], clip, wait = 1500} = shot;
  // not networkidle: the dev server keeps a live-reload socket open forever
  await page.goto(base + url, {waitUntil: 'load'});
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
