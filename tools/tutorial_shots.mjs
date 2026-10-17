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

// ---- ST03 (発見の予感): a Discovery card, Furnace's levels, a hint opening ----
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  // A stopped clock: the hint's show is stepped to the same frame every time.
  await p.clock.install();
  await p.goto(url(page));
  await p.clock.runFor(1500);
  await p.evaluate(() => startExperiments());
  await p.clock.runFor(1500);
  // Brass with its elements and synthesis known; the processing still hidden.
  await p.evaluate(() => {
    for (const id of ['ST01', 'ST02', 'ST03', 'ST04', 'ST_TRAIN', 'ST_TRAINED', 'ST_BULK_BREAK']) storyFlags[id] = true;
    saveStoryFlags();
    Object.assign(gameStats.ownedEquipment, { casting: 1, om: 1, furnace: 1 });
    rebuildEquipmentFromOwnership(); renderLab();
    if (document.getElementById('look-backdrop').classList.contains('open')) closeLookPicker(false);
    discoveryState.brass = Object.assign(discoveryState.brass || {}, { stage: 2, hintsRevealed: { elements: true, synthesis: true } });
    renderDisPanel();
  });
  await p.clock.runFor(800);
  const card = p.locator('#dis-content .d-card[data-disc="brass"]');
  const c = await card.boundingBox();
  await shoot(p, 'hint-recipe', pad(c, 4));
  // The processing opens: the orb flies from the player, the plate breaks and
  // the big text stands over the card (at about 0.85 s).
  await p.evaluate(() => {
    discoveryState.brass.hintsRevealed.processing = true;
    DisFx.reveal({ discId: 'brass', segs: ['p0'], full: false, sources: ['you'] });
  });
  for (let t = 0; t < 850; t += 50) await p.clock.runFor(50);   // in steps, as the frames come
  await shoot(p, 'hint-reveal', { x: 0, y: c.y - 34, width: 240, height: c.height + 44 });
  await p.clock.runFor(3000);
  await p.evaluate(() => openPopup('furnace'));
  await p.clock.runFor(800);
  const levels = p.locator('#popup .param-control').locator('xpath=ancestor::*[contains(@class,"popup-section")][1]');
  await shoot(p, 'hint-levels', pad(await levels.boundingBox(), 4));
  await ctx.close();
}

// ---- the first hire (firstHireTutorial): the hire list, the CO and EXP panels ----
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto(url(page));
  await p.waitForTimeout(1200);
  await p.evaluate(() => startExperiments());
  await p.waitForTimeout(1000);
  await p.evaluate(() => {
    for (const id of ['ST01', 'ST02', 'ST03', 'ST04', 'ST05', 'ST_TRAIN', 'ST_TRAINED', 'ST_BULK_BREAK', 'firstHireTutorial']) storyFlags[id] = true;
    saveStoryFlags();
    Object.assign(gameStats.ownedEquipment, { casting: 1, om: 1, furnace: 1 });
    gameStats.coins = 1000;
    rebuildEquipmentFromOwnership(); renderLab(); updateTopbar(); applyTabVisibility();
    if (document.getElementById('look-backdrop').classList.contains('open')) closeLookPicker(false);
  });
  await p.waitForTimeout(500);
  await p.evaluate(() => { openStore(); activeLTab = 'co'; renderLPanel(); });
  await p.waitForTimeout(500);
  const ben = await p.locator('.hire-btn[data-cw="ben"]').locator('xpath=ancestor::*[contains(@class,"hire-card") or contains(@class,"dev-card")][1]').boundingBox();
  const tier = await p.getByText('Tier 1 — 駆け出し').first().boundingBox();
  await shoot(p, 'cw-list', pad(union(tier, ben), 6));
  // Ben hired and at work on E1: every task switched on.
  await p.evaluate(() => {
    closeStore();
    const b = coworkers.find(c => c.id === 'ben');
    b.hired = true; b.present = true;
    Object.assign(b.toggles, { S: 1, P: 1, A: 1, E: 1, W: 1 });
    activeRTab = 'exp'; renderRPanel(); renderLab();
  });
  await p.waitForTimeout(300);
  await p.locator('#rpanel-content .e-accept-btn').first().click();
  await p.waitForTimeout(6000);                       // Ben has the order under way
  const active = p.getByText('取り下げ', { exact: true }).first()
    .locator('xpath=ancestor::*[contains(@class,"e-card")][1]');
  await shoot(p, 'cw-exp', pad(await active.boundingBox(), 6));
  await p.evaluate(() => { activeRTab = 'co'; renderRPanel(); });
  await p.waitForTimeout(300);
  await shoot(p, 'cw-tasks', pad(await p.locator('#rpanel-content .cw-row[data-cw="ben"]').boundingBox(), 3));
  await ctx.close();
}

// ---- spontaneous_idea (数撃ちゃ当たる…？): Jeff and Bobby left alone on E25 ----
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto(url(page));
  await p.waitForTimeout(1200);
  await p.evaluate(() => startExperiments());
  await p.waitForTimeout(1000);
  // A Lv4 lab short of the ending (ST18 would bring up the UDM announcement),
  // two Phase-Shift units so both of them synthesize, and only the two of them
  // on shift: Jeff on S, Bobby on S and E. E25 taken with 反復 on.
  await p.evaluate(() => {
    for (const ev of STORY_EVENTS) if (ev.phase !== 'Endgame' && ev.id !== 'ST18') storyFlags[ev.id] = true;
    storyFlags.firstHireTutorial = true;
    saveStoryFlags();
    if (document.getElementById('look-backdrop').classList.contains('open')) closeLookPicker(false);
    gameStats.coins = 10_000_000;
    for (const lv of [2, 3, 4]) purchaseLabUpgrade(lv);
    for (const id of ['casting', 'arc', 'laser', 'furnace', 'rolling', 'magnet', 'agt', 'om', 'sem', 'tem', 'qaa']) gameStats.ownedEquipment[id] = 1;
    gameStats.ownedEquipment.phase = 2;
    rebuildEquipmentFromOwnership();
    for (const e of ['Cu', 'Zn', 'Fe', 'Ni', 'Cr', 'Ti', 'Adam', 'Mit', 'Ori', 'Hii']) gameStats.unlockedElements.add(e);
    // Their default tiles can sit under a machine; start them on the player's.
    for (const id of ['jeff', 'bobby']) Object.assign(coworkers.find(c => c.id === id), { hired: true, present: true, col: playerCol, row: playerRow });
    Object.assign(coworkers.find(c => c.id === 'jeff').toggles, { S: 1, P: 0, A: 0, E: 0, W: 0 });
    Object.assign(coworkers.find(c => c.id === 'bobby').toggles, { S: 1, P: 0, A: 0, E: 1, W: 0 });
    document.querySelector('.chat-overlay')?.classList.add('collapsed');
    renderLab(); updateTopbar(); applyTabVisibility();
    acceptExperiment('E25');
    experiments[experiments.length - 1].repeat = true;
    renderExperiments();
    activeRTab = 'co'; renderRPanel();
  });
  await p.waitForTimeout(500);
  const jeff = await p.locator('#rpanel-content .cw-row[data-cw="jeff"]').boundingBox();
  const bobby = await p.locator('#rpanel-content .cw-row[data-cw="bobby"]').boundingBox();
  await shoot(p, 'idea-tasks', pad(union(jeff, bobby), 3));
  // Bobby fumbles one: the scribble over his head, caught while it is up.
  // Not while a machine is down: the hazard stripes would steal the picture.
  await p.waitForFunction(() => document.querySelector('.character[data-cw="bobby"] .cw-bubble[data-kind="tangle"]')
    && !equipment.some(e => e.broken), null, { timeout: 240000, polling: 100 });
  // The Lv4 lab is wider than a phone: bring him into view first.
  await p.evaluate(() => document.querySelector('.character[data-cw="bobby"]').scrollIntoView({ block: 'center', inline: 'center' }));
  await p.waitForTimeout(150);
  const head = await p.locator('.character[data-cw="bobby"]').boundingBox();
  await shoot(p, 'idea-tangle', { x: head.x - 70, y: head.y - 50, width: head.width + 140, height: head.height + 80 });
  // Their specimens pile up unprocessed under 作業中.
  await p.waitForFunction(() => specimens.filter(s => s.status === 'in_lab').length >= 12, null, { timeout: 240000 });
  await p.evaluate(() => {
    activeRTab = 'res'; renderRPanel();
    document.querySelector('#rpanel-content .d-group-header')?.scrollIntoView({ block: 'start' });
  });
  await p.waitForTimeout(300);
  const list = await p.locator('#rpanel-content').boundingBox();
  const hdr = await p.locator('#rpanel-content .d-group-header').boundingBox();
  await shoot(p, 'idea-results', { x: list.x, y: hdr.y - 4, width: list.width, height: list.y + list.height - hdr.y + 4 });
  // The order card, on a wider screen: a phone's right panel stacks its long title letter by letter.
  await p.setViewportSize({ width: 760, height: 844 });
  await p.evaluate(() => { activeRTab = 'exp'; renderRPanel(); });
  await p.waitForTimeout(500);
  const order = p.locator('#rpanel-content .e-repeat-toggle.on').locator('xpath=ancestor::*[contains(@class,"e-card")][1]');
  await order.evaluate(el => { window.scrollTo(0, 0); el.scrollIntoView({ block: 'center' }); });
  await p.waitForTimeout(200);
  await shoot(p, 'idea-repeat', pad(await order.boundingBox(), 4));
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
