// Shared shell for the equipment minigames.
//
// A game supplies only its own stage and controls; the shell owns everything
// the twelve games have in common: the header (goal), the judge
// popup, the start and result overlays, and the permanent clear record.
//
// Clearing a minigame unlocks batch processing on that piece of equipment for
// good, and its best score sets how often a batch breaks the machine, so
// the record lives in localStorage under the same `labolic.*.pt1` naming as
// the main game's saves (the main game reads it). Every access is guarded:
// a private window or blocked storage must not stop the game from being
// played.
//
// Scores run 90..100 on clearing. Each game maps its own measure onto that
// range with MG.lin (what earns 100, what earns 90); analysis games default
// to the mean quality of their Excellent shots against the game's ceiling
// (def.qMax). Breakdown chance per specimen in a batch is
// 0.2 x (100 - best) %: 2 % at 90, 1 % at 95, 0 at 100.
//
// Opened inside the main game (in an iframe), a game shows a Close button
// and tells the parent when it closes.
//
// There is no time limit. The point is to have done the work once, however
// slowly; running out of clock would only punish the players who are
// actually looking at the image.
//
//   MG.mount(rootEl, {
//     id, title, subtitle, desc,
//     goal,                // Excellent judgements needed to clear
//     build(body, ctx),    // returns { start(), tick(dt, now), stop() }
//     onExit(result),      // optional; shown as a Close button when given
//     qMax,                // analysis: the best quality the game allows
//   })
//
//   ctx.judge(q)     score one attempt (0..1); returns the rank
//   ctx.flash(msg, color)
//   ctx.fail(reason) end the run as a failure
//   ctx.note(text)   a line (a score, say) for the result screen
//   ctx.score(s)     this run's score, 90..100, for when it clears
//   ctx.running      true between Start and the result screen
//   ctx.hits         Excellent judgements so far in this run
(function(){
  "use strict";

  const STORE_KEY = 'labolic.minigames.pt1';

  // Thresholds from the SEM prototype. Only Excellent counts toward a clear;
  // the others are feedback.
  const RANKS = [
    { key:'excellent', min:0.90, t:'Excellent!!!', c:'#ffcf3a', glow:'rgba(255,176,0,.65)' },
    { key:'great',     min:0.75, t:'Great!',       c:'#62e6c3', glow:'rgba(60,210,160,.55)' },
    { key:'good',      min:0.45, t:'Good',         c:'#9fc3e2', glow:'rgba(127,168,201,.45)' },
    { key:'umm',       min:-1,   t:'Umm...',       c:'#e2603f', glow:'rgba(226,96,63,.45)' },
  ];
  const rankOf = q => RANKS.find(r => q >= r.min);

  function loadAll() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; }
    catch (e) { return {}; }
  }
  // { cleared, best } or null. Records from before scores existed were a
  // bare `true`; they count as cleared at the lowest passing score.
  function record(id) {
    const r = loadAll()[id];
    if (!r) return null;
    if (r === true) return { cleared: true, best: 90 };
    return { cleared: !!r.cleared, best: +r.best || 90 };
  }
  function isCleared(id) { return !!(record(id) || {}).cleared; }
  // Keep the best score ever; returns the record as stored.
  function markCleared(id, score) {
    const all = loadAll(), prev = record(id);
    const best = Math.max(prev ? prev.best : 0, Math.min(100, Math.max(90, score ?? 90)));
    all[id] = { cleared: true, best: Math.round(best * 10) / 10 };
    try { localStorage.setItem(STORE_KEY, JSON.stringify(all)); } catch (e) {}
    return all[id];
  }

  // 90..100 from a measure x: `at100` earns 100, `at90` earns 90, linear
  // between and clipped outside (either direction of x works).
  const lin = (x, at100, at90) => Math.max(90, Math.min(100, 90 + 10 * (at90 - x) / (at90 - at100)));
  // Breakdown chance per specimen in a batch, from the best score.
  const failRate = best => Math.max(0, 0.002 * (100 - best));
  const pct = p => (p * 100).toFixed(p < 0.01 ? 2 : 1) + '%';

  // Pointer input that survives every browser's habits. A drag is tracked
  // on the window once it starts, so it keeps going when the pointer
  // leaves the element and does not depend on pointer capture, and the
  // default action (text selection, native drag, scrolling) is suppressed.
  function drag(el, h) {
    let id = null;
    const move = e => { if (e.pointerId === id) { e.preventDefault(); h.move && h.move(e); } };
    const end = e => {
      if (e && e.pointerId !== undefined && e.pointerId !== id) return;
      id = null;
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', end);
      window.removeEventListener('pointercancel', end);
      h.end && h.end();
    };
    el.addEventListener('pointerdown', e => {
      if (e.button > 0) return;
      e.preventDefault();
      if (id !== null) end();
      id = e.pointerId;
      window.addEventListener('pointermove', move, { passive: false });
      window.addEventListener('pointerup', end);
      window.addEventListener('pointercancel', end);
      h.start && h.start(e);
    });
  }

  // A button that acts while held: down() on press, up() on release —
  // wherever the release happens, or if the window loses focus mid-press.
  function hold(el, down, up) {
    let held = false;
    const release = () => { if (held) { held = false; up(); } };
    drag(el, { start: () => { held = true; down(); }, end: release });
    window.addEventListener('blur', release);
  }

  // Sound effects, synthesised with Web Audio so nothing has to be loaded.
  // Phones only let a page make sound after a touch, so the context is
  // created (or resumed) on the first press anywhere in a game.
  let ac = null;
  function audio() {
    try {
      ac = ac || new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === 'suspended') ac.resume();
      return ac;
    } catch (e) { return null; }
  }
  const sfx = {
    // "Kirarin": three bright notes climbing an octave and a fifth, each
    // ringing out, over a soft shimmer.
    kirarin() {
      const a = audio();
      if (!a) return;
      const t0 = a.currentTime + 0.01;
      [1318.5, 1975.5, 2637.0].forEach((f, i) => {
        const t = t0 + i * 0.075, o = a.createOscillator(), g = a.createGain();
        o.type = 'triangle'; o.frequency.value = f;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(0.16, t + 0.008);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.7);
        o.connect(g); g.connect(a.destination);
        o.start(t); o.stop(t + 0.75);
      });
      const o = a.createOscillator(), g = a.createGain(), lfo = a.createOscillator(), lg = a.createGain();
      o.type = 'sine'; o.frequency.value = 3951;
      lfo.frequency.value = 18; lg.gain.value = 60;
      lfo.connect(lg); lg.connect(o.frequency);
      g.gain.setValueAtTime(0, t0 + 0.1);
      g.gain.linearRampToValueAtTime(0.05, t0 + 0.16);
      g.gain.exponentialRampToValueAtTime(0.001, t0 + 0.9);
      o.connect(g); g.connect(a.destination);
      o.start(t0 + 0.1); lfo.start(t0 + 0.1); o.stop(t0 + 0.95); lfo.stop(t0 + 0.95);
    },
  };

  const esc = s => String(s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));

  // Inside the main game's iframe: close by telling the parent.
  const embedded = (() => { try { return window.parent !== window; } catch (e) { return true; } })();
  function closeToParent(result) {
    try { window.parent.postMessage({ type: 'labolic-mg-close', id: result.id, record: result.record }, '*'); } catch (e) {}
  }

  function mount(root, def) {
    if (embedded && !def.onExit) def = { ...def, onExit: closeToParent };
    root.classList.add('mg-root');
    // Long-press menus and drag-outs are suppressed for the whole screen.
    for (const ev of ['contextmenu', 'dragstart', 'selectstart']) {
      root.addEventListener(ev, e => { if (!(e.target instanceof HTMLInputElement)) e.preventDefault(); });
    }
    root.addEventListener('pointerdown', audio, { passive: true });
    root.innerHTML = `
      <div class="mg-bar">
        <div class="mg-name"><b>${esc(def.title)}</b><span>${esc(def.subtitle || '')}</span></div>
        <div class="mg-cell"><span class="k">Excellent</span><div class="mg-pips"></div></div>
        ${def.onExit ? '<button class="mg-quit" aria-label="閉じる">✕</button>' : ''}
      </div>
      <div class="mg-body"></div>
      <div class="mg-judge"></div>
      <div class="mg-flash"></div>
      <div class="mg-overlay on">
        <h1>${esc(def.title)}</h1>
        <p class="mg-result"></p>
        <p class="mg-desc">${esc(def.desc || '')}</p>
        <p class="mg-goal"></p>
        <span class="mg-badge" style="display:none"></span>
        <div class="mg-btns">
          <button class="mg-start">Start</button>
          ${def.onExit ? '<button class="mg-sub mg-exit">閉じる</button>' : ''}
        </div>
      </div>`;
    const q = sel => root.querySelector(sel);
    const body = q('.mg-body'), pips = q('.mg-pips');
    const overlay = q('.mg-overlay');

    const goal = def.goal || 1;
    pips.innerHTML = '<i></i>'.repeat(goal);
    q('.mg-goal').textContent = `クリア条件：Excellent を ${goal} 回`;

    const st = { running:false, hits:0, cleared:false, qs:[], score:null };

    const ctx = {
      get running() { return st.running; },
      get hits() { return st.hits; },
      judge(qv) {
        const r = rankOf(qv);
        showJudge(r);
        if (r.key === 'excellent' && st.running) {
          st.hits++;
          st.qs.push(qv);
          drawPips();
          if (st.hits >= goal) finish(true);
        }
        return r;
      },
      flash,
      fail(reason) { if (st.running) finish(false, reason); },
      note(t) { st.note = t; },
      score(v) { st.score = v; },
    };

    const game = def.build(body, ctx);

    function drawPips() {
      [...pips.children].forEach((p, i) => p.classList.toggle('on', i < st.hits));
    }

    const judgeEl = q('.mg-judge');
    function showJudge(r) {
      judgeEl.textContent = r.t;
      judgeEl.style.color = r.c;
      judgeEl.style.textShadow = `0 0 18px ${r.glow}, 0 2px 10px rgba(0,0,0,.7)`;
      judgeEl.classList.remove('play');
      void judgeEl.offsetWidth;         // restart the animation
      judgeEl.classList.add('play');
    }

    const flashEl = q('.mg-flash');
    let flashT;
    function flash(msg, color) {
      flashEl.textContent = msg;
      flashEl.style.color = color || 'var(--mg-amber)';
      flashEl.classList.add('show');
      clearTimeout(flashT);
      flashT = setTimeout(() => flashEl.classList.remove('show'), 850);
    }

    function showOverlay(result, reason) {
      const res = q('.mg-result');
      if (result === undefined) {
        res.style.display = 'none';
      } else {
        res.style.display = '';
        res.className = 'mg-result ' + (result ? 'ok' : 'ng');
        res.textContent = result ? 'CLEAR!' : 'FAILED';
      }
      q('.mg-desc').textContent = reason || def.desc || '';
      const rec = record(def.id), badge = q('.mg-badge');
      badge.style.display = rec ? '' : 'none';
      if (rec) badge.textContent = `ハイスコア ${rec.best.toFixed(1)} ・ 一括処理の故障率 ${pct(failRate(rec.best))}/個`;
      q('.mg-start').textContent = result === undefined ? 'Start' : 'Retry';
      overlay.classList.add('on');
    }

    function start() {
      st.running = true; st.hits = 0; st.cleared = false; st.note = ''; st.qs = []; st.score = null;
      drawPips();
      overlay.classList.remove('on');
      game.start();
    }

    function finish(ok, reason) {
      st.running = false;
      st.cleared = ok;
      let msg = reason || '';
      if (ok) {
        // A game that measured itself said so; otherwise (the analysis
        // games) the mean of the Excellent shots against the game's ceiling.
        const mean = st.qs.reduce((a, b) => a + b, 0) / (st.qs.length || 1);
        const score = st.score ?? lin(mean, def.qMax || 1, 0.9);
        const before = record(def.id);
        const rec = markCleared(def.id, score);
        const best = before && score <= before.best ? '' : '（ハイスコア更新！）';
        msg = `${st.note ? st.note + '　' : ''}スコア ${score.toFixed(1)}${best}`;
      }
      game.stop && game.stop();
      // Let the last judge popup play before the overlay covers it.
      setTimeout(() => showOverlay(ok, msg), 700);
    }

    q('.mg-start').addEventListener('click', start);
    const exitBtn = q('.mg-exit');
    if (exitBtn) exitBtn.addEventListener('click', () => def.onExit({ id:def.id, record:record(def.id) }));
    // ✕ leaves at any time; a run in progress is simply abandoned.
    const quitBtn = q('.mg-quit');
    if (quitBtn) quitBtn.addEventListener('click', () => {
      st.running = false;
      game.stop && game.stop();
      def.onExit({ id:def.id, record:record(def.id) });
    });

    let last = performance.now();
    function frame(now) {
      // Clamp: a backgrounded tab resumes with a huge dt, which would
      // otherwise make a game's own animation jump.
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      game.tick && game.tick(dt, now);
      requestAnimationFrame(frame);
    }
    showOverlay(undefined);
    requestAnimationFrame(frame);

    return { start, ctx };
  }

  window.MG = { mount, isCleared, markCleared, record, lin, failRate, drag, hold, sfx, RANKS, STORE_KEY };
})();
