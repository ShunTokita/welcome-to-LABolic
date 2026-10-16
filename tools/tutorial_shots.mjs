#!/usr/bin/env node
// Retake the screenshots shown on story notices (STORY_EVENTS' `shots`).
//
// They are pictures of the game's own UI, so they go stale when that UI
// changes: rerun this after such a change and commit assets/tutorial/.
// Drives the newest playtest page and the minigames in a headless Chromium,
// crops each shot, and writes assets/tutorial/<name>.webp (via Pillow).
//
// Usage: node tools/tutorial_shots.mjs [version]     (default: newest)
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'assets', 'tutorial');
const TMP = path.join(ROOT, 'build', 'shots');

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('/opt/node22/lib/node_modules/playwright/index.mjs')); }

const ver = process.argv[2] || fs.readdirSync(ROOT)
  .map(f => f.match(/^labolic-playtest-(\d+)\.html$/)?.[1]).filter(Boolean)
  .sort((a, b) => a - b).pop();
const page = path.join(ROOT, `labolic-playtest-${ver}.html`);
const url = f => 'file://' + f;

fs.mkdirSync(TMP, { recursive: true });
fs.mkdirSync(OUT, { recursive: true });

const exe = '/opt/pw-browsers/chromium';
const browser = await chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
const shots = [];
const pad = (b, n = 8) => ({ x: b.x - n, y: b.y - n, width: b.width + 2 * n, height: b.height + 2 * n });
const union = (a, b) => {
  const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y);
  return { x, y, width: Math.max(a.x + a.width, b.x + b.width) - x, height: Math.max(a.y + a.height, b.y + b.height) - y };
};
async function shoot(p, name, clip) {
  const file = path.join(TMP, name + '.png');
  await p.screenshot({ path: file, clip });
  shots.push(name);
}

// ---- the main game: the store card and the Casting popup ----
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto(url(page));
  await p.waitForTimeout(1200);
  await p.evaluate(() => startExperiments());
  await p.waitForTimeout(1000);
  // A Lv1 lab with the starting devices, past the opening, no story waiting.
  await p.evaluate(() => {
    for (const id of ['ST01', 'ST02', 'ST03', 'ST04', 'ST_TRAIN', 'ST_TRAINED', 'ST_BULK_BREAK']) storyFlags[id] = true;
    saveStoryFlags();
    Object.assign(gameStats.ownedEquipment, { casting: 1, om: 1, furnace: 1 });
    gameStats.coins = 2000;
    rebuildEquipmentFromOwnership(); renderLab(); updateTopbar();
    if (document.getElementById('look-backdrop').classList.contains('open')) closeLookPicker(false);
    localStorage.removeItem('labolic.minigames.pt1');
  });
  await p.waitForTimeout(500);
  const card = p.locator('[data-action="train"][data-id="casting"]')
    .locator('xpath=ancestor::*[contains(@class,"dev-card")][1]');
  await p.evaluate(() => { openStore(); activeLTab = 'eqp'; renderLPanel(); });
  await p.waitForTimeout(500);
  await shoot(p, 'train-button', pad(await card.boundingBox(), 4));
  await p.evaluate(() => {
    localStorage.setItem('labolic.minigames.pt1', JSON.stringify({ casting: { cleared: true, best: 98.6 } }));
    renderLPanel();
  });
  await p.waitForTimeout(300);
  await shoot(p, 'break-rate', pad(await card.boundingBox(), 4));
  await p.evaluate(() => { closeStore(); openPopup('casting'); });
  await p.waitForTimeout(600);
  await p.getByText('Cu', { exact: true }).first().click();
  await p.getByText('Zn', { exact: true }).first().click();
  await p.getByText('+10', { exact: true }).first().click();
  await p.waitForTimeout(1200);                       // let the tap ripples fade
  const row = await p.locator('.qty-row').first().boundingBox();
  const go = await p.getByText('Go!', { exact: true }).first().boundingBox();
  await shoot(p, 'train-batch', pad(union(row, go), 10));
  await ctx.close();
}

// ---- the minigames ----
async function minigame(id) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 760 }, deviceScaleFactor: 2 });
  // Keep MG.mount's return value, to end a run with a set score.
  await ctx.addInitScript(() => {
    let mg;
    Object.defineProperty(window, 'MG', { configurable: true, get: () => mg,
      set: v => { const m = v.mount; v.mount = (...a) => (window.__mg = m(...a)); mg = v; } });
  });
  const p = await ctx.newPage();
  await p.goto(url(path.join(ROOT, 'minigames', id + '.html')));
  await p.waitForTimeout(800);
  await p.click('.mg-start');
  await p.waitForTimeout(1500);
  return { ctx, p };
}
const top = async p => union(await p.locator('.pc-stage').boundingBox(), await p.locator('.pc-gauges').boundingBox());

{
  // Casting while taking it apart: the glowing parts and the steps.
  const { ctx, p } = await minigame('casting');
  await shoot(p, 'train-game', pad(await top(p), 6));
  await ctx.close();
}
{
  // Arc while cleaning: the removal rate, then a cleared run's result.
  const { ctx, p } = await minigame('arc');
  const cv = await p.locator('.pc-stage canvas').boundingBox();
  const count = async () => p.locator('#count').textContent();
  for (let pass = 0; pass < 6 && (await count()).startsWith('外した'); pass++) {
    outer: for (let y = 0.1; y < 0.95; y += 0.07) for (let x = 0.08; x < 0.95; x += 0.07) {
      await p.mouse.click(cv.x + cv.width * x, cv.y + cv.height * y);
      if (!(await count()).startsWith('外した')) break outer;
    }
    await p.waitForTimeout(1000);
  }
  await p.waitForTimeout(1500);
  for (let y = 0.15; y < 0.9; y += 0.05) {
    await p.mouse.move(cv.x + cv.width * 0.1, cv.y + cv.height * y);
    await p.mouse.down();
    for (let x = 0.1; x < 0.9; x += 0.04) await p.mouse.move(cv.x + cv.width * x, cv.y + cv.height * y, { steps: 2 });
    await p.mouse.up();
    if (parseFloat((await count()).match(/([\d.]+)%/)?.[1] || 0) > 60) break;
  }
  await p.waitForTimeout(600);
  await shoot(p, 'break-score', pad(await top(p), 6));
  await p.evaluate(() => { const c = window.__mg.ctx; c.note('除去率 98.6%'); c.score(98.6); c.judge(0.986); });
  await p.waitForTimeout(1800);
  const o = p.locator('.mg-overlay');
  const a = await o.locator('h1').boundingBox(), b = await o.locator('.mg-start').boundingBox();
  const box = await o.boundingBox();
  await shoot(p, 'break-result', { x: box.x, y: a.y - 20, width: box.width, height: b.y + b.height + 20 - (a.y - 20) });
  await ctx.close();
}
await browser.close();

// PNG -> WebP: a fraction of the size, and the browsers the game runs on read it.
execFileSync('python3', ['-c', `
import sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
for name in sys.argv[3:]:
    Image.open(f'{src}/{name}.png').convert('RGB').save(f'{out}/{name}.webp', 'WEBP', quality=82, method=6)
`, TMP, OUT, ...shots], { stdio: 'inherit' });
for (const n of shots) {
  const f = path.join(OUT, n + '.webp');
  console.log(path.relative(ROOT, f), Math.round(fs.statSync(f).size / 1024) + ' KB');
}
