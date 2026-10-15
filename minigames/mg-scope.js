// Shared pieces of the analysis minigames.
//
//   MGScope.ui         console widgets (sliders, 2-axis pads, capture row)
//   MGScope.electron   the SEM image engine, used by SEM and QAA
//
// Optical and TEM draw their own images but use the same console widgets,
// so all four instruments are operated the same way.
//
// Scoring rule for every analysis game: image quality is sharpness alone.
// Light, brightness and contrast are on the console because they make the
// image easier to read, never because they move the score.
(function(){
  "use strict";

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rnd = (a, b) => a + Math.random() * (b - a);
  const rsign = () => Math.random() * 2 - 1;

  // ---------------------------------------------------------------------
  // Console widgets
  // ---------------------------------------------------------------------
  const ui = {
    slider(id, label, min, max) {
      return `<div class="sc-row"><span class="lab">${label}</span>
        <input type="range" id="${id}" min="${min}" max="${max}" value="0" step="1">
        <span class="val" id="${id}V">0</span></div>`;
    },
    pad(id, label, hint, alt) {
      return `<div class="sc-padrow">
        <div class="sc-pad" id="${id}"><div class="cx"></div><div class="cy"></div><div class="dot${alt ? ' alt' : ''}"></div></div>
        <div class="side">
          <div class="lab">${label}</div>
          <div>X&nbsp;<span class="v" id="${id}X">0</span></div>
          <div>Y&nbsp;<span class="v" id="${id}Y">0</span></div>
          <div class="hint">${hint}</div>
        </div></div>`;
    },
    quality: `<div class="sc-q"><span>IMG&nbsp;QUALITY</span>
      <div class="sc-qbar"><div class="sc-qfill"></div></div><span class="sc-qpct">0%</span></div>`,
    actions: `<div class="sc-actions">
      <button class="sc-capture">Capture!</button>
      <button class="sc-skip">New<br>Sample</button></div>`,

    // Wire a slider to a getter/setter. `fmt` turns the raw value into the
    // number shown beside it.
    bindSlider(root, id, onInput, fmt) {
      const el = root.querySelector('#' + id), v = root.querySelector('#' + id + 'V');
      const show = x => { v.textContent = fmt ? fmt(x) : Math.round(x); };
      el.addEventListener('input', () => { show(+el.value); onInput(+el.value); });
      return { set(x) { el.value = Math.round(x); show(x); } };
    },

    // A square pad whose dot sits at (x, y) in [-range, range].
    bindPad(root, id, range, onInput, fmt) {
      const pad = root.querySelector('#' + id), dot = pad.querySelector('.dot');
      const xv = root.querySelector('#' + id + 'X'), yv = root.querySelector('#' + id + 'Y');
      const f = fmt || (x => Math.round(x));
      function show(x, y) {
        dot.style.left = clamp(50 + x / range * 46, 2, 98) + '%';
        dot.style.top  = clamp(50 - y / range * 46, 2, 98) + '%';
        xv.textContent = f(x); yv.textContent = f(y);
      }
      function fromEvent(e) {
        const r = pad.getBoundingClientRect();
        const x = clamp((e.clientX - r.left - r.width / 2) / (r.width / 2) * range, -range, range);
        const y = clamp(-(e.clientY - r.top - r.height / 2) / (r.height / 2) * range, -range, range);
        show(x, y); onInput(x, y);
      }
      let drag = false;
      pad.addEventListener('pointerdown', e => { drag = true; pad.setPointerCapture(e.pointerId); fromEvent(e); });
      pad.addEventListener('pointermove', e => { if (drag) fromEvent(e); });
      pad.addEventListener('pointerup', () => { drag = false; });
      pad.addEventListener('pointercancel', () => { drag = false; });
      return { set: show };
    },

    showQuality(root, q) {
      root.querySelector('.sc-qfill').style.width = (q * 100).toFixed(1) + '%';
      root.querySelector('.sc-qpct').textContent = Math.round(q * 100) + '%';
    },

    // Capture scores the current image and moves to the next sample;
    // New Sample skips one without scoring.
    bindActions(root, ctx, quality, newSample) {
      const cap = root.querySelector('.sc-capture');
      cap.addEventListener('click', () => {
        if (!ctx.running || cap.disabled) return;
        ctx.judge(quality());
        if (ctx.running) newSample();
      });
      root.querySelector('.sc-skip').addEventListener('click', () => { if (ctx.running) newSample(); });
      return cap;
    },
  };

  // Sharpness from the blur along two principal axes, on the scale every
  // analysis game shares: S_MIN is the blur floor (a perfect image still
  // has some), SIG_S sets how fast quality falls away from it.
  const S_MIN = 0.45, SIG_S = 2.4;
  const sharpness = (s1, s2) => Math.exp(-(s1 * s1 + s2 * s2) / (2 * SIG_S * SIG_S));

  // ---------------------------------------------------------------------
  // Electron-beam image engine (SEM, QAA)
  //
  // Ported from the SEM prototype. Focus error D and astigmatism a give
  // blurs |D-a| and |D+a| along two axes; the SVG filter frame turns to the
  // astigmatism angle and the content counter-turns, so the smear follows
  // the stigmator.
  //
  // With `wobble`, the column also has a beam-axis error that accumulates
  // from sample to sample. It costs resolution everywhere and makes the
  // image walk as focus changes; the WOBB button swings focus so the walk
  // is plain to see, and the align pad cancels it.
  // ---------------------------------------------------------------------
  // Secondary-electron images of etched microstructures, drawn to a canvas
  // once per sample and placed in the SVG as an image, so the blur filter
  // works on them exactly as it did on the prototype's letters.
  //
  // The scene spans -90..390 in viewBox units (480 square) so that turning
  // it with the astigmatism axis never exposes an empty corner.
  //
  // Tones are chosen on a 0..1 design scale and squeezed into the sample's
  // native window [lo, hi]; contrast stretches them back out.
  //
  //   'precip'  grains with boundary precipitates, a precipitate-free zone
  //             along each boundary, and intragranular precipitates (fine
  //             dots, or needles in two or three variants per grain)
  //   'cuboid'  coarse grains filled with aligned cuboidal precipitates in
  //             narrow matrix channels, as in a Ni-base superalloy
  const SCENE = 480, SCENE_O = -90;

  function voronoi(n, margin) {
    const seeds = [];
    for (let i = 0; i < n; i++) {
      seeds.push({ x: rnd(-margin, SCENE + margin), y: rnd(-margin, SCENE + margin),
                   ang: rnd(0, Math.PI), tone: rnd(-0.05, 0.05) });
    }
    return seeds;
  }

  function microstructure(kind, lo, hi) {
    const cv = document.createElement('canvas');
    cv.width = cv.height = SCENE;
    const g = cv.getContext('2d');
    const img = g.createImageData(SCENE, SCENE), px = img.data;
    const map = v => Math.round(255 * (lo + clamp(v, 0, 1) * (hi - lo)));
    const cuboid = kind === 'cuboid';
    const seeds = voronoi(cuboid ? Math.round(rnd(7, 12)) : Math.round(rnd(14, 24)), 40);
    const n = seeds.length;
    // Per-grain precipitate habit for 'precip'.
    for (const sd of seeds) {
      sd.needle = Math.random() < 0.5;
      sd.p = rnd(9, 12);          // cuboid pitch
      sd.c = sd.p * rnd(0.62, 0.75); // cuboid edge
    }
    const owner = new Int16Array(SCENE * SCENE), edgeA = new Float32Array(SCENE * SCENE);
    const boundary = [];
    for (let y = 0; y < SCENE; y++) {
      for (let x = 0; x < SCENE; x++) {
        let d1 = 1e9, d2 = 1e9, k = 0;
        for (let i = 0; i < n; i++) {
          const dx = x - seeds[i].x, dy = y - seeds[i].y, d = dx * dx + dy * dy;
          if (d < d1) { d2 = d1; d1 = d; k = i; } else if (d < d2) d2 = d;
        }
        const sd = seeds[k], i0 = y * SCENE + x;
        const edge = (Math.sqrt(d2) - Math.sqrt(d1)) * 0.5;   // ~ distance to the boundary
        owner[i0] = k; edgeA[i0] = edge;
        let v = 0.34 + sd.tone;            // matrix, with a little channelling contrast
        if (cuboid) {
          const ca = Math.cos(sd.ang), sa = Math.sin(sd.ang);
          const u = ((x * ca + y * sa) % sd.p + sd.p) % sd.p;
          const w = ((-x * sa + y * ca) % sd.p + sd.p) % sd.p;
          if (u < sd.c && w < sd.c && edge > 2.5) {
            v = 0.62 + sd.tone;
            if (u < 1 || w < 1) v += 0.12;  // bright leading edges
          }
        }
        if (edge < 1.1) v = 0.12;          // etched groove
        else if (edge < 2.0) v = 0.55;     // its bright rim
        if (edge < 0.8 && (x + y * 7) % 23 === 0) boundary.push([x, y, k]);
        v += rnd(-0.03, 0.03);
        const m = map(v);
        px[i0 * 4] = px[i0 * 4 + 1] = px[i0 * 4 + 2] = m;
        px[i0 * 4 + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
    const tone = v => { const m = map(v); return `rgb(${m},${m},${m})`; };

    if (!cuboid) {
      // Boundary precipitates: lens-shaped, bright, with a dark shadow on one side.
      for (const [x, y] of boundary) {
        if (Math.random() < 0.45) continue;
        const r = rnd(1.8, 4.2), a = rnd(0, Math.PI);
        g.fillStyle = tone(0.06);
        g.beginPath(); g.ellipse(x + 1, y + 1.2, r, r * 0.6, a, 0, Math.PI * 2); g.fill();
        g.fillStyle = tone(rnd(0.88, 1));
        g.beginPath(); g.ellipse(x, y, r, r * 0.6, a, 0, Math.PI * 2); g.fill();
      }
      // Intragranular precipitates, kept clear of a precipitate-free zone.
      const PFZ = 9;
      for (let t = 0; t < 2600; t++) {
        const x = Math.floor(rnd(0, SCENE)), y = Math.floor(rnd(0, SCENE));
        const i0 = y * SCENE + x;
        if (edgeA[i0] < PFZ) continue;
        const sd = seeds[owner[i0]];
        if (sd.needle) {
          if (Math.random() < 0.55) continue;
          const variant = Math.floor(Math.random() * 3);
          const a = sd.ang + variant * Math.PI / 3, L = rnd(4, 11);
          g.strokeStyle = tone(rnd(0.80, 0.95));
          g.lineWidth = rnd(0.9, 1.5);
          g.beginPath();
          g.moveTo(x - Math.cos(a) * L / 2, y - Math.sin(a) * L / 2);
          g.lineTo(x + Math.cos(a) * L / 2, y + Math.sin(a) * L / 2);
          g.stroke();
        } else {
          g.fillStyle = tone(rnd(0.78, 0.95));
          g.beginPath(); g.arc(x, y, rnd(0.8, 1.7), 0, Math.PI * 2); g.fill();
        }
      }
    }
    return cv.toDataURL('image/png');
  }

  const K_BLUR = 0.085;      // focus units -> px stdDeviation
  const A_MAX = 60, F_MAX = 70;
  const K_AXIS = 0.075;      // axis error -> isotropic blur (px)
  const AXIS_DRIFT = 11, AXIS_CLAMP = 50;
  const WOBB_AMP = 26;

  function electron(opts) {
    const wobble = !!opts.wobble;
    return function build(body, ctx) {
      body.innerHTML = `
        <div class="sc">
          <div class="sc-stage">
            <svg viewBox="0 0 300 300" preserveAspectRatio="xMidYMid slice">
              <defs>
                <filter id="psf" x="-40%" y="-40%" width="180%" height="180%" primitiveUnits="userSpaceOnUse" color-interpolation-filters="linearRGB">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="0 0" id="blur" result="b"/>
                  <feComponentTransfer in="b">
                    <feFuncR type="linear" slope="1" intercept="0" class="tf"/>
                    <feFuncG type="linear" slope="1" intercept="0" class="tf"/>
                    <feFuncB type="linear" slope="1" intercept="0" class="tf"/>
                  </feComponentTransfer>
                </filter>
                <radialGradient id="vig" cx="50%" cy="50%" r="62%">
                  <stop offset="70%" stop-color="#000" stop-opacity="0"/>
                  <stop offset="100%" stop-color="#000" stop-opacity="1"/>
                </radialGradient>
                <clipPath id="frame"><rect x="0" y="0" width="300" height="300"/></clipPath>
              </defs>
              <g clip-path="url(#frame)">
                <g id="rotA"><g filter="url(#psf)"><g id="rotC"><g id="scene"></g></g></g></g>
                <rect x="0" y="0" width="300" height="300" fill="url(#vig)"/>
              </g>
            </svg>
            <div class="sc-scan"></div>
            <div class="sc-wobbtag">WOBB</div>
            <div class="sc-hud">
              <div class="tl">${opts.hud.tl}</div><div class="tr">${opts.hud.tr}</div>
              <div class="bl">${opts.hud.bl}</div><div class="br">${opts.hud.br}</div>
            </div>
          </div>
          ${ui.quality}
          <div class="sc-console">
            ${ui.slider('focus', 'Focus', -100, 100)}
            ${ui.pad('stig', 'Stigmator', 'drag pad to<br>correct astig.')}
            ${wobble ? ui.pad('align', 'Beam Align', 'turn on WOBB,<br>stop the image<br>from shifting.', true) : ''}
            ${ui.slider('contrast', 'Contrast', 20, 320)}
            ${ui.slider('bright', 'Bright', -100, 100)}
            ${wobble ? '<div class="sc-toggle" id="wobbBtn"><span class="led"></span>WOBB</div>' : ''}
          </div>
          ${ui.actions}
        </div>`;

      const $ = id => body.querySelector('#' + id);
      const scene = $('scene'), rotA = $('rotA'), rotC = $('rotC'), blur = $('blur');
      const tfs = [...body.querySelectorAll('.tf')];

      const S = {
        focus:0, stigX:0, stigY:0, contrast:1, bright:0, f0:0, aX:0, aY:0,
        axisX:0, axisY:0, alignX:0, alignY:0, wobb:false,
      };
      // The SVG filter is the expensive part on phones, so the image is
      // redrawn only when something changed (or continuously while WOBB swings).
      let dirty = true;

      const focusC = ui.bindSlider(body, 'focus', v => { S.focus = v; dirty = true; });
      const contrastC = ui.bindSlider(body, 'contrast', v => { S.contrast = v / 100; dirty = true; }, v => (v / 100).toFixed(2));
      const brightC = ui.bindSlider(body, 'bright', v => { S.bright = v; dirty = true; });
      const stigC = ui.bindPad(body, 'stig', 100, (x, y) => { S.stigX = x; S.stigY = y; dirty = true; });
      const alignC = wobble ? ui.bindPad(body, 'align', AXIS_CLAMP, (x, y) => { S.alignX = x; S.alignY = y; dirty = true; }) : null;

      function buildScene(lo, hi) {
        scene.innerHTML = `<image href="${microstructure(opts.structure, lo, hi)}"
          x="${SCENE_O}" y="${SCENE_O}" width="${SCENE}" height="${SCENE}"/>`;
      }

      function newSample() {
        const span = rnd(0.60, 0.80);
        const mid = 0.5 + rsign() * 0.26 * span;
        buildScene(Math.max(0.03, mid - span / 2), Math.min(0.97, mid + span / 2));
        S.f0 = rsign() * F_MAX * 0.7;
        const aMag = A_MAX * rnd(0.45, 1), aAng = rnd(0, Math.PI * 2);
        S.aX = Math.cos(aAng) * aMag; S.aY = Math.sin(aAng) * aMag;
        // Every sample starts deliberately detuned.
        S.focus = clamp(S.f0 + rsign() * 45, -100, 100);
        S.stigX = clamp(-S.aX + rsign() * 35, -100, 100);
        S.stigY = clamp(-S.aY + rsign() * 35, -100, 100);
        S.contrast = 1; S.bright = 0;
        // The column drifts a little between samples; the player's alignment
        // carries over, so each sample needs only a touch-up.
        if (wobble) {
          S.axisX = clamp(S.axisX + rsign() * AXIS_DRIFT, -AXIS_CLAMP, AXIS_CLAMP);
          S.axisY = clamp(S.axisY + rsign() * AXIS_DRIFT, -AXIS_CLAMP, AXIS_CLAMP);
        }
        focusC.set(S.focus); contrastC.set(100); brightC.set(0); stigC.set(S.stigX, S.stigY);
        dirty = true;
      }

      // Blurs for a given defocus; `walk` is the lateral image shift.
      function optics(D) {
        const rx = S.aX + S.stigX, ry = S.aY + S.stigY;
        const a = Math.hypot(rx, ry) * 0.5;
        const ax = S.axisX + S.alignX, ay = S.axisY + S.alignY;
        const sAx = K_AXIS * Math.hypot(ax, ay);
        return {
          s1: Math.hypot(Math.max(S_MIN, K_BLUR * Math.abs(D - a)), sAx),
          s2: Math.hypot(Math.max(S_MIN, K_BLUR * Math.abs(D + a)), sAx),
          theta: Math.atan2(ry, rx) * 0.5, ax, ay,
        };
      }
      function render(now) {
        let D = S.focus - S.f0, shiftX, shiftY;
        const o0 = optics(D);
        if (S.wobb) {
          const osc = Math.sin(now * 0.011);
          D += osc * WOBB_AMP;
          shiftX = o0.ax * osc * 0.9; shiftY = o0.ay * osc * 0.9;
        } else {
          shiftX = o0.ax * (D / F_MAX) * 0.5; shiftY = o0.ay * (D / F_MAX) * 0.5;
        }
        const { s1, s2, theta } = optics(D);
        const deg = theta * 180 / Math.PI;
        rotA.setAttribute('transform', `rotate(${deg.toFixed(2)} 150 150)`);
        rotC.setAttribute('transform', `rotate(${(-deg).toFixed(2)} 150 150) translate(${shiftX.toFixed(2)} ${shiftY.toFixed(2)})`);
        blur.setAttribute('stdDeviation', `${s1.toFixed(3)} ${s2.toFixed(3)}`);
        const g = S.contrast, off = S.bright / 255 + 0.5 - g * 0.5;
        tfs.forEach(f => { f.setAttribute('slope', g.toFixed(3)); f.setAttribute('intercept', off.toFixed(3)); });
      }
      function quality() {
        const { s1, s2 } = optics(S.focus - S.f0);
        return sharpness(s1, s2);
      }

      const cap = ui.bindActions(body, ctx, quality, newSample);
      if (wobble) {
        // Capture is refused while focus is swinging, as on the real column.
        $('wobbBtn').addEventListener('click', () => {
          S.wobb = !S.wobb;
          $('wobbBtn').classList.toggle('on', S.wobb);
          body.querySelector('.sc-wobbtag').classList.toggle('on', S.wobb);
          cap.disabled = S.wobb;
          dirty = true;
        });
      }

      buildScene(0.08, 0.92);

      return {
        start() {
          if (wobble) {
            // Start from a column that clearly needs aligning.
            const m = rnd(22, 38), t = rnd(0, Math.PI * 2);
            S.axisX = Math.cos(t) * m; S.axisY = Math.sin(t) * m;
            S.alignX = 0; S.alignY = 0; alignC.set(0, 0);
            S.wobb = false; $('wobbBtn').classList.remove('on');
            body.querySelector('.sc-wobbtag').classList.remove('on');
            cap.disabled = false;
          }
          newSample();
        },
        tick(dt, now) {
          if (!dirty && !S.wobb) return;
          dirty = false;
          render(now);
          ui.showQuality(body, S.wobb ? 0 : quality());
        },
      };
    };
  }

  window.MGScope = { ui, electron, sharpness, S_MIN, SIG_S, clamp, rnd, rsign };
})();
