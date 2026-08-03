/*
 * Turns the aiogram_dialog preview page into documentation screenshots.
 *
 * See README.adoc in this directory for the two-step workflow. In short:
 *   node shoot.mjs <preview.html> <shots.json> <out-dir>
 *
 * The preview page renders every dialog window as a fake telegram message and
 * shows only the one matching location.hash, so each state can be shot on its
 * own. We clip a little wider than the bubble to keep the chat wallpaper around
 * it — that is what makes the result look like a real screenshot.
 */
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const [previewArg, shotsArg, outArg] = process.argv.slice(2);
if (!previewArg || !shotsArg || !outArg) {
  console.error('usage: node shoot.mjs <preview.html> <shots.json> <out-dir>');
  process.exit(2);
}

const shots = JSON.parse(fs.readFileSync(shotsArg, 'utf-8'));
const outDir = path.resolve(outArg);
const width = 700;
const pad = 14;

// channel: the default may resolve to the headless shell; ask for the full browser
const browser = await chromium.launch({channel: 'chromium'});
const page = await browser.newPage({viewport: {width, height: 1400}, deviceScaleFactor: 2});
await page.goto('file://' + path.resolve(previewArg));
await page.waitForLoadState('load');
// Roboto, cached next to this script as data-uri @font-face rules. The preview page
// asks Google Fonts for it, which needs network; with the cache the render is the
// same everywhere, and the committed screenshots stay reproducible.
const here = path.dirname(fileURLToPath(import.meta.url));
const robotoPath = path.join(here, 'roboto.css');
if (fs.existsSync(robotoPath)) {
  await page.addStyleTag({content: fs.readFileSync(robotoPath, 'utf-8')});
} else {
  console.log('roboto.css missing — falling back to whatever font the system provides');
}
await page.evaluate(() => document.fonts.ready);
await page.addStyleTag({
  content: `
    /* hide the state picker so the bubble sits at the top of the wallpaper */
    .start-group {display: none !important;}
    body {min-height: 100vh;}
    /* the preview puts the state name where telegram puts the time */
    .time {display: none !important;}
    /* no filler space under short messages */
    .body {min-height: auto !important;}
    /* Noto Color Emoji goes right after Roboto: DejaVu and Liberation carry
       monochrome glyphs for pictographs like U+270F, so if they come first those
       emoji render as black-and-white text. */
    * {font-family: 'Roboto', 'Noto Color Emoji', 'Liberation Sans', 'DejaVu Sans', sans-serif;}
  `,
});
await page.evaluate(() => {
  for (const el of document.querySelectorAll('.author')) el.textContent = 'Схватка';
});

let failed = 0;
for (const [state, out] of Object.entries(shots)) {
  await page.evaluate(s => {
    location.hash = '';
    location.hash = s;
  }, state);
  const handle = await page.$(`[id="${state}"]`);
  if (!handle || !(await handle.isVisible())) {
    console.log(`SKIP ${state} (not in this preview)`);
    failed += 1;
    continue;
  }
  const box = await handle.boundingBox();
  // grow the viewport so the padded clip always fits inside the wallpaper
  await page.setViewportSize({width, height: Math.ceil(box.y + box.height + 3 * pad)});
  const {x, y, width: w, height: h} = await handle.boundingBox();
  const file = path.join(outDir, out);
  fs.mkdirSync(path.dirname(file), {recursive: true});
  await page.screenshot({
    path: file,
    clip: {x: Math.max(0, x - pad), y: Math.max(0, y - pad), width: w + 2 * pad, height: h + 2 * pad},
  });
  console.log(`${state} -> ${out}`);
}

await browser.close();
process.exit(failed ? 1 : 0);
