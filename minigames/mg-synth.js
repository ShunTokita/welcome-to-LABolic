// Shared engine for the synthesis minigames: take the apparatus apart,
// clean it, clean the parts, (do the apparatus's own odd job), put it back.
//
// A device is data:
//
//   MGSynth.build({
//     hud,                         // top-left label on the stage
//     view:  { target, dist, height, fov },   // orbit camera on the device
//     tray:  { target, dist, height, fov },   // camera on the parts table
//     scenery: [mesh, ...],        // fixed: base, chamber, bench, table
//     parts: [{ id, name, mesh, at, tray, needs }],
//        at     matrix of the part when assembled
//        tray   matrix of the part laid on the parts table
//        needs  ids of parts sitting on top of it: they come off first,
//               and go back on after it
//     dirt:  [{ p, n, r, part? }],  // a stain at point p with normal n,
//        in world space, or in the part's own space when `part` is given
//        (those are cleaned on the parts table)
//     special: { ... } | null,     // see runSpecial below
//   })
//
// The phases run in order and the screen shows where the player is:
//   分解     tap the glowing parts; a part with something still on top of
//            it will not come off (and says what to remove first)
//   清掃     rub the stains off the inside of the apparatus; ◀ ▶ walk the
//            camera round to reach the far side
//   部品清掃  the same on the parts table
//   (special) the device's own task
//   組立     tap the glowing ghosts to put each part back
// Finishing is the clear: the spec scores synthesis on completion.
(function(){
  "use strict";
  const { Renderer, mat, build } = M3;

  const HL = [95, 227, 255];          // highlight colour (the guide colour)
  const RUB = 90;                     // canvas px of rubbing to clear a stain
  const FLY_T = 0.8;                  // seconds for a part to travel

  const lerpM = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

  function make(cfg) {
    return function build_(body, ctx) {
      const phases = [['disasm', '分解'], ['clean', '清掃'], ['parts', '部品清掃']]
        .concat(cfg.special ? [['special', cfg.special.name]] : [], [['asm', '組立']]);
      body.innerHTML = `
        <div class="pc">
          <div class="pc-stage"><canvas></canvas>
            <div class="pc-hud"><div class="tl">${cfg.hud}</div><div class="tr" id="sState"></div></div>
            <div class="sy-anchor" id="anchor"></div>
          </div>
          <div class="pc-gauges">
            <div class="pc-steps" id="steps">${phases.map(p => `<span>${p[1]}</span>`).join('')}</div>
            <div class="sy-count" id="count">　</div>
            <div id="spPanel"></div>
          </div>
          <div class="pc-buttons" id="btns">
            <button class="pc-btn" id="rotL">◀</button>
            <button class="pc-btn" id="rotR">▶</button>
          </div>
        </div>`;
      const $ = id => body.querySelector('#' + id);
      const canvas = body.querySelector('canvas');
      const r3 = new Renderer(canvas, { bg: cfg.bg || [18, 20, 26], light: cfg.light || [-0.35, 0.85, 0.55] });
      const tips = MGProc.tips(body);

      // ---- camera: an orbit that eases between the device and the table ----
      const cam = { az: cfg.view.az ?? 0.5, spin: 0, target: cfg.view.target.slice(), dist: cfg.view.dist,
                    height: cfg.view.height, fov: cfg.view.fov || 38, goal: cfg.view };
      function setView(v) { cam.goal = v; }
      function stepCamera(dt) {
        const g = cam.goal, k = Math.min(1, dt * 4);
        for (let i = 0; i < 3; i++) cam.target[i] += (g.target[i] - cam.target[i]) * k;
        cam.dist += (g.dist - cam.dist) * k;
        cam.height += (g.height - cam.height) * k;
        cam.fov += ((g.fov || 38) - cam.fov) * k;
        cam.az += cam.spin * dt;
        // A view may fix the angle too (a close-up that only reads from one
        // side); ease toward it the short way round.
        if (g.az !== undefined && !cam.spin) {
          const d = Math.atan2(Math.sin(g.az - cam.az), Math.cos(g.az - cam.az));
          cam.az += d * k;
        }
        const t = cam.target;
        r3.camera([t[0] + Math.sin(cam.az) * cam.dist, t[1] + cam.height, t[2] + Math.cos(cam.az) * cam.dist], t, cam.fov);
      }
      MG.hold($('rotL'), () => { cam.spin = -1.6; }, () => { cam.spin = 0; });
      MG.hold($('rotR'), () => { cam.spin = 1.6; }, () => { cam.spin = 0; });

      // ---- parts and stains ----
      const parts = cfg.parts.map((d, i) => ({ d, mesh: d.mesh, pick: 100 + i, where: 'on', fly: null }));
      parts.forEach(p => { p.mesh.pick = p.pick; p.mesh.m = p.d.at; });
      const byId = id => parts.find(p => p.d.id === id);
      const dirt = cfg.dirt.map((d, i) => {
        const n = 10, radii = [];
        for (let j = 0; j < n; j++) radii.push(d.r * (0.7 + Math.random() * 0.5));
        const col = d.c || [92 + Math.random() * 30, 74 + Math.random() * 20, 52 + Math.random() * 14];
        const mesh = build.blob(radii, col);
        mesh.pick = 1000 + i; mesh.ds = true;
        // Lift the stain off the surface a hair so it never z-fights.
        const nn = Math.hypot(...d.n), off = 0.006;
        const p = [d.p[0] + d.n[0] / nn * off, d.p[1] + d.n[1] / nn * off, d.p[2] + d.n[2] / nn * off];
        return { d, mesh, local: mat.orient(p, d.n), hp: 1, part: d.part ? byId(d.part) : null };
      });

      let S;
      function reset() {
        S = { phase: 'disasm', done: false, t: 0, dust: [], sparks: [], mistakes: 0 };
        parts.forEach(p => { p.where = 'on'; p.fly = null; p.mesh.m = p.d.at; p.mesh.over = null; p.mesh.tint = null; p.mesh.hidden = false; });
        dirt.forEach(s => { s.hp = 1; });
        cam.az = cfg.view.az ?? 0.5; setView(cfg.view);
        if (cfg.special && cfg.special.reset) cfg.special.reset(api);
        $('spPanel').innerHTML = '';
        body.querySelectorAll('.sy-sp').forEach(el => el.remove());
      }

      const removable = p => p.where === 'on' && !p.fly && (p.d.needs || []).every(id => byId(id).where === 'off');
      const installable = p => p.where === 'off' && !p.fly &&
        parts.every(q => !(q.d.needs || []).includes(p.d.id) || q.where === 'on');
      const stainsLeft = onParts => dirt.filter(s => s.hp > 0 && !!s.part === onParts).length;

      function fly(p, to, then) {
        p.fly = { from: p.mesh.m, to, t: 0, then };
      }

      // ---- input on the stage: taps take parts off and put them back,
      // drags rub stains ----
      let down = null, last = null, moved = 0;
      MG.drag(canvas, {
        start(e) { down = last = [e.clientX, e.clientY]; moved = 0; rub(e, 6); },
        move(e) {
          const d = Math.hypot(e.clientX - last[0], e.clientY - last[1]);
          moved += d; last = [e.clientX, e.clientY];
          rub(e, d);
        },
        end() { if (down && moved < 10) tap(down); down = null; },
      });

      function tap([cx, cy]) {
        if (!ctx.running) return;
        const id = r3.pickAt(canvas, cx, cy);
        const p = parts.find(q => q.pick === id);
        if (!p) return;
        if (S.phase === 'disasm') {
          if (removable(p)) { fly(p, p.d.tray, () => { p.where = 'off'; }); return; }
          const blocking = (p.d.needs || []).map(byId).filter(q => q.where !== 'off').map(q => q.d.name);
          S.mistakes++;
          ctx.flash(`まだ外せない：先に${blocking[0]}を外そう`, '#e2603f');
        } else if (S.phase === 'asm' && installable(p)) {
          p.mesh.over = null;
          fly(p, p.d.at, () => { p.where = 'on'; });
        }
      }

      function rub(e, dist) {
        if (!ctx.running || (S.phase !== 'clean' && S.phase !== 'parts')) return;
        const br = canvas.getBoundingClientRect(), k = r3.w / br.width;
        // A brush, not a pin: sample a small cross around the finger.
        const hit = new Set();
        for (const [ox, oy] of [[0, 0], [7, 0], [-7, 0], [0, 7], [0, -7]]) {
          const id = r3.pickAt(canvas, e.clientX + ox / k, e.clientY + oy / k);
          if (id >= 1000) hit.add(id - 1000);
        }
        for (const i of hit) {
          const s = dirt[i];
          if (s.hp <= 0 || !!s.part !== (S.phase === 'parts')) continue;
          s.hp -= dist * k / RUB;
          if (s.hp <= 0) {
            const q = r3.project(stainWorld(s, [0, 0, 0]));
            if (q) S.sparks.push({ x: q[0], y: q[1], t: 0 });
          }
        }
        if (hit.size) {
          const x = (e.clientX - br.left) * k, y = (e.clientY - br.top) * k;
          for (let j = 0; j < 2; j++) S.dust.push({ x: x + (Math.random() - 0.5) * 10, y, vx: (Math.random() - 0.5) * 40, vy: -20 - Math.random() * 30, t: 0 });
        }
      }

      function partMatrix(p) { return p.mesh.m; }
      function stainWorld(s, local) {
        const M = s.part ? mat.mul(partMatrix(s.part), s.local) : s.local;
        return mat.apply(M, local);
      }

      // ---- special task ----
      const api = { $, ctx, r3, mat, build, body, tips, setView, flash: ctx.flash,
                    panel: html => { $('spPanel').innerHTML = html; },
                    buttons: html => {
                      body.querySelectorAll('.sy-sp').forEach(el => el.remove());
                      $('btns').insertAdjacentHTML('beforeend', html);
                    } };

      function advance() {
        const order = phases.map(p => p[0]);
        if (S.phase === 'disasm' && parts.every(p => p.where === 'off')) {
          S.phase = 'clean';
        } else if (S.phase === 'clean' && stainsLeft(false) === 0) {
          S.phase = 'parts'; setView(cfg.tray);
        } else if (S.phase === 'parts' && stainsLeft(true) === 0) {
          if (cfg.special) { S.phase = 'special'; cfg.special.start(api); }
          else { S.phase = 'asm'; setView(cfg.view); }
        } else if (S.phase === 'special' && cfg.special.done(api)) {
          body.querySelectorAll('.sy-sp').forEach(el => el.remove());
          $('spPanel').innerHTML = '';
          S.phase = 'asm'; setView(cfg.view);
        } else if (S.phase === 'asm' && parts.every(p => p.where === 'on' && !p.fly)) {
          S.phase = 'done';
          ctx.flash('組み立て完了！', '#5fd38a');
          ctx.judge(1);
        }
        void order;
      }

      function step(dt) {
        S.t += dt;
        stepCamera(dt);
        for (const p of parts) {
          if (!p.fly) continue;
          const f = p.fly;
          f.t = Math.min(1, f.t + dt / FLY_T);
          const e = f.t * f.t * (3 - 2 * f.t);
          const M = lerpM(f.from, f.to, e);
          M[7] += Math.sin(Math.PI * e) * 0.6;          // an arc, lifted clear
          p.mesh.m = M;
          if (f.t >= 1) { p.mesh.m = f.to; p.fly = null; f.then(); }
        }
        if (S.phase === 'special') cfg.special.tick(dt, api);
        if (ctx.running) advance();
        S.dust = S.dust.filter(d => (d.t += dt) < 0.6);
        for (const d of S.dust) { d.x += d.vx * dt; d.y += d.vy * dt; d.vy += 160 * dt; }
        S.sparks = S.sparks.filter(s => (s.t += dt) < 0.5);
      }

      function render() {
        const pulse = 0.25 + 0.2 * Math.sin(S.t * 6);
        for (const p of parts) {
          p.mesh.tint = ctx.running && S.phase === 'disasm' && removable(p) ? [...HL, pulse] : null;
          // Parts waiting to go back on show as ghosts where they belong.
          const ghost = ctx.running && S.phase === 'asm' && installable(p);
          p.mesh.over = ghost ? { c: HL, a: 0.25 + pulse * 0.6, e: true } : null;
          if (ghost) p.mesh.m = p.d.at;
          else if (S.phase === 'asm' && p.where === 'off' && !p.fly) p.mesh.m = p.d.tray;
        }
        const meshes = cfg.scenery.concat(parts.map(p => p.mesh));
        for (const s of dirt) {
          if (s.hp <= 0) continue;
          if (s.part && s.part.where === 'on' && !s.part.fly && S.phase !== 'parts' && S.phase !== 'disasm') continue;
          const sc = 0.35 + 0.65 * s.hp;
          s.mesh.m = mat.mul(s.part ? partMatrix(s.part) : mat.id(), mat.mul(s.local, mat.sc(sc, sc, 1)));
          const live = ctx.running && (S.phase === 'clean' && !s.part || S.phase === 'parts' && s.part);
          s.mesh.tint = live ? [255, 150, 60, 0.15 + pulse * 0.3] : null;
          meshes.push(s.mesh);
        }
        if (S.phase === 'special' && cfg.special.meshes) meshes.push(...cfg.special.meshes(api));
        r3.draw(meshes, g => {
          for (const d of S.dust) {
            g.fillStyle = `rgba(190,170,140,${(1 - d.t / 0.6).toFixed(2)})`;
            g.fillRect(d.x | 0, d.y | 0, 2, 2);
          }
          for (const s of S.sparks) {
            const a = 1 - s.t / 0.5, r = 4 + s.t * 30;
            g.strokeStyle = `rgba(255,255,255,${a.toFixed(2)})`;
            g.beginPath(); g.moveTo(s.x - r, s.y); g.lineTo(s.x + r, s.y); g.moveTo(s.x, s.y - r); g.lineTo(s.x, s.y + r); g.stroke();
          }
          if (S.phase === 'special' && cfg.special.overlay) cfg.special.overlay(g, api);
        });
      }

      function hud() {
        const i = phases.findIndex(p => p[0] === S.phase);
        [...$('steps').children].forEach((el, k) => {
          el.className = S.phase === 'done' || k < i ? 'done' : k === i ? 'now' : '';
        });
        const off = parts.filter(p => p.where === 'off').length, n = parts.length;
        const txt = {
          disasm: `外した部品 ${off} / ${n}`,
          clean: `装置内の汚れ 残り ${stainsLeft(false)}`,
          parts: `部品の汚れ 残り ${stainsLeft(true)}`,
          special: cfg.special ? cfg.special.status(api) : '',
          asm: `取り付けた部品 ${n - off} / ${n}`,
          done: '完了',
        }[S.phase];
        $('count').textContent = txt;
        $('sState').textContent = phases.find(p => p[0] === S.phase)?.[1] || 'done';
        if (!ctx.running || S.phase === 'done') return tips.hide();
        const tipText = {
          disasm: '光っている部品をタップして外そう！',
          clean: '汚れをこすって落とそう！ ◀▶で回り込める',
          parts: '部品の汚れも落とそう！',
          asm: '光っている場所をタップして取り付けよう！',
        }[S.phase];
        if (S.phase === 'special') {
          const t = cfg.special.tip && cfg.special.tip(api);
          return t ? tips.show(t[0], t[1]) : tips.hide();
        }
        tips.show($('anchor'), tipText);
      }

      // Automated tests set window.MG_DEBUG before loading to reach inside.
      if (window.MG_DEBUG) window.MG_DEBUG.synth = { parts, dirt, r3, canvas, cam, get S() { return S; } };

      reset();
      return {
        start() { reset(); },
        tick(dt) { step(dt); render(); hud(); },
      };
    };
  }

  window.MGSynth = { build: make };
})();
