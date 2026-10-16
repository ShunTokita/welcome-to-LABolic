// Shared engine for the synthesis minigames: take the apparatus apart,
// clean it, clean the parts, (do the apparatus's own odd job), put it back.
//
// A device is data:
//
//   MGSynth.build({
//     hud,                         // top-left label on the stage
//     view:  { target, dist, height, fov },   // orbit camera on the device
//     tray:  { target, dist, height, fov },   // camera on the parts table
//     cleanView: { ... },          // closer in on the device while cleaning (optional)
//     scenery: [mesh, ...],        // fixed: base, chamber, bench, table
//     parts: [{ id, name, mesh, at, tray, needs }],
//        at     matrix of the part when assembled
//        tray   matrix of the part laid on the parts table
//        needs  ids of parts sitting on top of it: they come off first,
//               and go back on after it
//     dirt:  [{ p, n, r, part?, count?, spread?, cyl? }],
//        a dirty patch centred at p on a surface with normal n, in world
//        space, or in the part's own space when `part` is given (those are
//        cleaned on the parts table). It becomes `count` (default 7) small
//        stains of about 0.4 r scattered over `spread` (default 2.4 r) in
//        the surface's plane, or round a cylinder wall when `cyl` gives its
//        axis and radius [cx, cz, R] (axis along y).
//     dirtCount: stains per patch unless the patch says (default 7)
//     special: { ... } | null,     // see runSpecial below
//   })
//
// The phases run in order and the screen shows where the player is:
//   分解     tap the glowing parts; a part with something still on top of
//            it will not come off (and says what to remove first)
//   清掃     rub the stains off the inside of the apparatus; ◀ ▶ walk the
//            camera round to reach the far side. The removal rate (by
//            stain area) is the score; at 90 % the Next button opens, and
//            the dirt scanner (three uses a game) marks what is left
//   部品清掃  the same on the parts table
//   (special) the device's own task
//   組立     tap the glowing ghosts to put each part back
// Finishing is the clear; the overall removal rate is the score.
(function(){
  "use strict";
  const { Renderer, mat, build } = M3;

  const HL = [95, 227, 255];          // highlight colour (the guide colour)
  const RUB = 30;                     // buffer px of rubbing to clear a stain
  const BRUSH = 12;                   // brush radius in CSS px: what a stroke reaches
  const PASS = 0.9;                   // removal rate that opens Next
  const SCANS = 3, SCAN_T = 4;        // scanner uses per game, seconds it shows
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
            <div class="sy-wipe" id="wipe"><i></i><b></b><b></b><b></b><b></b><b></b><b></b></div>
          </div>
          <div class="pc-gauges">
            <div class="pc-steps" id="steps">${phases.map(p => `<span>${p[1]}</span>`).join('')}</div>
            <div class="sy-count" id="count">　</div>
            <div id="spPanel"></div>
          </div>
          <div class="pc-buttons" id="btns">
            <button class="pc-btn" id="rotL">◀</button>
            <button class="pc-btn" id="rotR">▶</button>
            <button class="pc-btn sy-cl" id="scan">スキャン<small id="scanN"></small></button>
            <button class="pc-btn act sy-cl" id="next" disabled>次へ</button>
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
        // A view may fix the angle (`fixAz`: a close-up that only reads from
        // one side); ease toward it the short way round. A device view's
        // `az` is only where the camera starts.
        if (g.fixAz !== undefined && !cam.spin) {
          const d = Math.atan2(Math.sin(g.fixAz - cam.az), Math.cos(g.fixAz - cam.az));
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
      const dirt = [];
      for (const d of cfg.dirt) {
        const count = d.count ?? cfg.dirtCount ?? 7, spread = d.spread ?? d.r * 2.4;
        const B0 = mat.orient(d.p, d.n);
        const xd = [B0[0], B0[4], B0[8]], yd = [B0[1], B0[5], B0[9]];
        for (let k = 0; k < count; k++) {
          let p, n;
          if (d.cyl) {
            // Round a cylinder wall: spread along the arc and up the axis.
            const [cx, cz, R] = d.cyl;
            const inward = (d.p[0] - cx) * d.n[0] + (d.p[2] - cz) * d.n[2] < 0;
            const a = Math.atan2(d.p[0] - cx, d.p[2] - cz) + (Math.random() - 0.5) * 2 * spread / R;
            const rr = R * (inward ? 0.997 : 1.003);
            p = [cx + Math.sin(a) * rr, d.p[1] + (Math.random() - 0.5) * 2 * spread, cz + Math.cos(a) * rr];
            n = inward ? [-Math.sin(a), 0, -Math.cos(a)] : [Math.sin(a), 0, Math.cos(a)];
          } else {
            const rad = spread * Math.sqrt(Math.random()), a = Math.random() * Math.PI * 2;
            p = d.p.map((v, i) => v + xd[i] * Math.cos(a) * rad + yd[i] * Math.sin(a) * rad);
            n = d.n;
          }
          const rs = d.r * 0.42 * (0.7 + Math.random() * 0.6);
          const radii = [];
          for (let j = 0; j < 9; j++) radii.push(rs * (0.65 + Math.random() * 0.6));
          // One brightness factor per stain (not per channel, which tints it).
          // Stains ignore the lighting so a stain on a face turned from the
          // lamp still shows: finding them is the scanner's job, not the shadows'.
          const kc = 0.82 + Math.random() * 0.3;
          const mesh = build.blob(radii, (d.c || [92, 74, 52]).map(v => v * kc));
          mesh.f.forEach(f => { f.e = true; });
          mesh.pick = 1000 + dirt.length; mesh.ds = true;
          // Lift the stain off the surface a hair so it never z-fights.
          const nn = Math.hypot(...n), off = 0.006;
          const q = [p[0] + n[0] / nn * off, p[1] + n[1] / nn * off, p[2] + n[2] / nn * off];
          dirt.push({ d, mesh, local: mat.orient(q, n), hp: 1, w: rs * rs, part: d.part ? byId(d.part) : null });
        }
      }

      let S;
      function reset() {
        S = { phase: 'disasm', done: false, t: 0, dust: [], sparks: [], mistakes: 0,
              scans: SCANS, scanT: 0, next: false, perfect: {}, autoAt: 0 };
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
      // Removal rate, by stain area, over the device's stains or the parts'
      // (or both, for the score).
      function removal(onParts) {
        let tot = 0, left = 0;
        for (const s of dirt) {
          if (onParts !== undefined && !!s.part !== onParts) continue;
          tot += s.w; left += s.w * Math.max(0, s.hp);
        }
        return tot ? 1 - left / tot : 1;
      }
      const cleaning = () => S.phase === 'clean' || S.phase === 'parts';
      const phaseRate = () => removal(S.phase === 'parts');

      $('next').addEventListener('click', () => {
        if (ctx.running && cleaning() && phaseRate() >= PASS) S.next = true;
      });
      $('scan').addEventListener('click', () => {
        if (!ctx.running || !cleaning() || S.scans <= 0 || S.scanT > 0) return;
        S.scans--; S.scanT = SCAN_T;
      });

      function fly(p, to, then) {
        p.fly = { from: p.mesh.m, to, t: 0, then };
      }

      // ---- input on the stage: taps take parts off and put them back,
      // drags rub stains ----
      let down = null, last = null, moved = 0;
      // The brush drawn on the stage while cleaning: under the mouse
      // whenever it is over the stage, under a finger while it touches.
      const brush = { x: 0, y: 0, show: false, touch: false, rubT: -1 };
      const aim = e => { brush.x = e.clientX; brush.y = e.clientY; };
      MG.drag(canvas, {
        start(e) {
          down = last = [e.clientX, e.clientY]; moved = 0;
          brush.touch = e.pointerType !== 'mouse'; brush.show = true; aim(e);
          rub(e, 6);
        },
        move(e) {
          const d = Math.hypot(e.clientX - last[0], e.clientY - last[1]);
          moved += d; last = [e.clientX, e.clientY];
          aim(e);
          rub(e, d);
        },
        end() { if (down && moved < 10) tap(down); down = null; if (brush.touch) brush.show = false; },
      });
      canvas.addEventListener('pointermove', e => { if (e.pointerType === 'mouse') { brush.show = true; aim(e); } });
      canvas.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse' && !down) brush.show = false; });

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
        // A brush, not a pin: sample a disc of BRUSH round the finger.
        const hit = new Set();
        for (const [rr, n] of [[0, 1], [0.5, 6], [1, 10]]) {
          for (let j = 0; j < n; j++) {
            const a = j / n * Math.PI * 2;
            const id = r3.pickAt(canvas, e.clientX + Math.cos(a) * rr * BRUSH, e.clientY + Math.sin(a) * rr * BRUSH);
            if (id >= 1000) hit.add(id - 1000);
          }
        }
        if (hit.size) brush.rubT = S.t;
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
          if (cfg.cleanView) setView(cfg.cleanView);
        } else if (S.phase === 'clean' && (S.next || S.autoAt && S.t >= S.autoAt)) {
          S.phase = 'parts'; S.next = false; S.autoAt = 0; S.scanT = 0; setView(cfg.tray);
        } else if (S.phase === 'parts' && (S.next || S.autoAt && S.t >= S.autoAt)) {
          S.next = false; S.autoAt = 0; S.scanT = 0;
          if (cfg.special) { S.phase = 'special'; cfg.special.start(api); }
          else { S.phase = 'asm'; setView(cfg.view); }
        } else if (S.phase === 'special' && cfg.special.done(api)) {
          body.querySelectorAll('.sy-sp').forEach(el => el.remove());
          $('spPanel').innerHTML = '';
          S.phase = 'asm'; setView(cfg.view);
        } else if (S.phase === 'asm' && parts.every(p => p.where === 'on' && !p.fly)) {
          S.phase = 'done';
          const rate = removal();
          ctx.flash(`組み立て完了！ 除去率 ${(rate * 100).toFixed(1)}%`, '#5fd38a');
          ctx.note(`除去率 ${(rate * 100).toFixed(1)}%`);
          ctx.score(rate * 100);
          ctx.judge(rate);
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
        S.scanT = Math.max(0, S.scanT - dt);
        // Spotless: a white wipe across the stage and a chime, then on to
        // the next phase once it has played.
        if (ctx.running && cleaning() && !S.perfect[S.phase] && phaseRate() >= 1) {
          S.perfect[S.phase] = true;
          S.autoAt = S.t + 1.1;
          const w = $('wipe');
          w.querySelectorAll('b').forEach(b => {
            b.style.left = (10 + Math.random() * 80) + '%';
            b.style.top = (10 + Math.random() * 75) + '%';
            b.style.animationDelay = (0.15 + Math.random() * 0.35).toFixed(2) + 's';
          });
          w.classList.remove('play'); void w.offsetWidth; w.classList.add('play');
          MG.sfx.kirarin();
          ctx.flash('ピカピカ！', '#ffffff');
        }
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
          if (S.scanT > 0) drawScan(g);
          drawBrush(g);
        });
        canvas.style.cursor = ctx.running && cleaning() ? 'none' : '';
      }

      // The brush: its reach as a faint ring, and a scrubbing brush over it
      // that jiggles while it is taking dirt off.
      function drawBrush(g) {
        if (!brush.show || !ctx.running || !cleaning()) return;
        const br = canvas.getBoundingClientRect(), k = r3.w / br.width;
        const x = (brush.x - br.left) * k, y = (brush.y - br.top) * k, R = BRUSH * k;
        g.strokeStyle = 'rgba(255,255,255,0.45)';
        g.lineWidth = 1;
        g.beginPath(); g.arc(x, y, R, 0, Math.PI * 2); g.stroke();
        const busy = S.t - brush.rubT < 0.15;
        const jx = busy ? Math.sin(S.t * 60) * R * 0.12 : 0;
        g.save();
        g.translate(x + jx, y);
        g.rotate(-0.45);
        const w = R * 1.5, u = R / 8;
        g.fillStyle = '#e8e2c8';                        // bristles, at the point of contact
        for (let i = 0; i < 6; i++) g.fillRect(-w / 2 + i * w / 6 + u * 0.3, -u * 2.5, w / 6 - u * 0.6, u * 2.5);
        g.fillStyle = '#5fe3ff';                        // the block
        g.fillRect(-w / 2, -u * 5, w, u * 2.6);
        g.fillStyle = '#2b7f99';
        g.fillRect(-w / 2, -u * 2.9, w, u * 0.5);
        g.fillStyle = '#5fe3ff';                        // the handle
        g.fillRect(-u * 1.2, -u * 11, u * 2.4, u * 6.2);
        g.restore();
      }

      // The scanner: a sweep out from the centre, then a marker on every
      // stain still left in this phase. A stain hidden behind something
      // gets a dashed marker: it is there, but the view has to move.
      function drawScan(g) {
        const age = SCAN_T - S.scanT, fade = Math.min(1, S.scanT / 0.6);
        if (age < 0.7) {
          g.strokeStyle = `rgba(95,227,255,${(0.8 * (1 - age / 0.7)).toFixed(2)})`;
          g.lineWidth = 2;
          g.beginPath(); g.arc(r3.w / 2, r3.h / 2, age / 0.7 * r3.w * 0.8, 0, Math.PI * 2); g.stroke();
        }
        const onParts = S.phase === 'parts';
        for (const s of dirt) {
          if (s.hp <= 0 || !!s.part !== onParts) continue;
          const q = r3.project(stainWorld(s, [0, 0, 0]));
          if (!q || age < Math.min(0.7, Math.hypot(q[0] - r3.w / 2, q[1] - r3.h / 2) / (r3.w * 0.8) * 0.7)) continue;
          const x = q[0] | 0, y = q[1] | 0;
          const seen = x >= 0 && y >= 0 && x < r3.w && y < r3.h && r3.pk[y * r3.w + x] === s.mesh.pick;
          const rad = 5 + 2 * Math.sin(S.t * 8);
          g.strokeStyle = `rgba(95,227,255,${(fade * (seen ? 1 : 0.6)).toFixed(2)})`;
          g.lineWidth = seen ? 2 : 1;
          g.setLineDash(seen ? [] : [2, 2]);
          g.beginPath(); g.arc(q[0], q[1], rad, 0, Math.PI * 2); g.stroke();
        }
        g.setLineDash([]);
        g.lineWidth = 1;
      }

      function hud() {
        const i = phases.findIndex(p => p[0] === S.phase);
        [...$('steps').children].forEach((el, k) => {
          el.className = S.phase === 'done' || k < i ? 'done' : k === i ? 'now' : '';
        });
        const off = parts.filter(p => p.where === 'off').length, n = parts.length;
        const txt = {
          disasm: `外した部品 ${off} / ${n}`,
          clean: `装置内の除去率 ${(removal(false) * 100).toFixed(1)}%（90%で次へ）`,
          parts: `部品の除去率 ${(removal(true) * 100).toFixed(1)}%（90%で次へ）`,
          special: cfg.special ? cfg.special.status(api) : '',
          asm: `取り付けた部品 ${n - off} / ${n}`,
          done: '完了',
        }[S.phase];
        $('count').textContent = txt;
        // Scanner and Next only while cleaning.
        body.querySelectorAll('.sy-cl').forEach(el => { el.style.display = cleaning() ? '' : 'none'; });
        $('scanN').textContent = `×${S.scans}`;
        $('scan').disabled = !ctx.running || S.scans <= 0 || S.scanT > 0;
        $('next').disabled = !ctx.running || !cleaning() || phaseRate() < PASS;
        $('sState').textContent = phases.find(p => p[0] === S.phase)?.[1] || 'done';
        if (!ctx.running || S.phase === 'done') return tips.hide();
        if (cleaning() && phaseRate() >= PASS) return tips.show($('next'), phaseRate() >= 1 ? '完璧！' : '90%を超えた！次へ進める');
        const tipText = {
          disasm: '光っている部品をタップして外そう！',
          clean: '汚れをこすって落とそう！ 見つからなければスキャン',
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
