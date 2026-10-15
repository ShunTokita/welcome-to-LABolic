// Shared shell for the equipment minigames.
//
// A game supplies only its own stage and controls; the shell owns everything
// the twelve games have in common: the header (goal), the judge
// popup, the start and result overlays, and the permanent clear record.
//
// Clearing a minigame unlocks batch processing on that piece of equipment for
// good, so the record lives in localStorage under the same `labolic.*.pt1`
// naming as the main game's saves. Every access is guarded: a private window
// or blocked storage must not stop the game from being played.
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
//   })
//
//   ctx.judge(q)     score one attempt (0..1); returns the rank
//   ctx.flash(msg, color)
//   ctx.fail(reason) end the run as a failure
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

  function loadCleared() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; }
    catch (e) { return {}; }
  }
  function isCleared(id) { return !!loadCleared()[id]; }
  function markCleared(id) {
    const all = loadCleared();
    all[id] = true;
    try { localStorage.setItem(STORE_KEY, JSON.stringify(all)); } catch (e) {}
  }

  const esc = s => String(s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));

  function mount(root, def) {
    root.classList.add('mg-root');
    root.innerHTML = `
      <div class="mg-bar">
        <div class="mg-name"><b>${esc(def.title)}</b><span>${esc(def.subtitle || '')}</span></div>
        <div class="mg-cell"><span class="k">Excellent</span><div class="mg-pips"></div></div>
      </div>
      <div class="mg-body"></div>
      <div class="mg-judge"></div>
      <div class="mg-flash"></div>
      <div class="mg-overlay on">
        <h1>${esc(def.title)}</h1>
        <p class="mg-result"></p>
        <p class="mg-desc">${esc(def.desc || '')}</p>
        <p class="mg-goal"></p>
        <span class="mg-badge" style="display:none">CLEARED ・ 一括処理 解放済み</span>
        <div class="mg-btns">
          <button class="mg-start">Start</button>
          ${def.onExit ? '<button class="mg-sub mg-exit">Close</button>' : ''}
        </div>
      </div>`;
    const q = sel => root.querySelector(sel);
    const body = q('.mg-body'), pips = q('.mg-pips');
    const overlay = q('.mg-overlay');

    const goal = def.goal || 1;
    pips.innerHTML = '<i></i>'.repeat(goal);
    q('.mg-goal').textContent = `クリア条件：Excellent を ${goal} 回`;

    const st = { running:false, hits:0, cleared:false };

    const ctx = {
      get running() { return st.running; },
      get hits() { return st.hits; },
      judge(qv) {
        const r = rankOf(qv);
        showJudge(r);
        if (r.key === 'excellent' && st.running) {
          st.hits++;
          drawPips();
          if (st.hits >= goal) finish(true);
        }
        return r;
      },
      flash,
      fail(reason) { if (st.running) finish(false, reason); },
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
      q('.mg-badge').style.display = isCleared(def.id) ? '' : 'none';
      q('.mg-start').textContent = result === undefined ? 'Start' : 'Retry';
      overlay.classList.add('on');
    }

    function start() {
      st.running = true; st.hits = 0; st.cleared = false;
      drawPips();
      overlay.classList.remove('on');
      game.start();
    }

    function finish(ok, reason) {
      st.running = false;
      st.cleared = ok;
      if (ok) markCleared(def.id);
      game.stop && game.stop();
      // Let the last judge popup play before the overlay covers it.
      setTimeout(() => showOverlay(ok, ok ? '一括処理が使えるようになりました。' : reason), 700);
    }

    q('.mg-start').addEventListener('click', start);
    const exitBtn = q('.mg-exit');
    if (exitBtn) exitBtn.addEventListener('click', () => def.onExit({ id:def.id, cleared:isCleared(def.id) }));

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

  window.MG = { mount, isCleared, markCleared, RANKS, STORE_KEY };
})();
