// A very small 3D renderer for the process and synthesis minigames.
//
// The main game is pixel art, so instead of a general-purpose engine this
// rasterises flat-shaded triangles into a low-resolution buffer (192x144 by
// default) with a z-buffer, and the canvas is scaled up with nearest-
// neighbour sampling. Lighting is quantised to a few steps so surfaces read
// as bands of colour, the way a pixel artist would shade them.
//
// At this resolution a scene of one to two thousand triangles costs a few
// milliseconds per frame, and the file is a few KB rather than the ~600 KB
// of three.js. Lightness on phones is the requirement this is built for.
//
//   const r = new M3.Renderer(canvas, { w:192, h:144, bg:[r,g,b] });
//   r.camera([ex,ey,ez], [tx,ty,tz], fovDeg);
//   r.draw([mesh, ...]);
//
// A mesh is { v: [[x,y,z], ...], f: [{ i:[a,b,c], c:[r,g,b], e:bool }, ...],
// m: 4x4 matrix (optional), ds: double-sided }. `e` marks an emissive face:
// drawn at full colour, unaffected by light (flames, glowing glass).
(function(){
  "use strict";

  // ---- 4x4 matrices, row-major, acting on column vectors ----
  const mat = {
    id: () => [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
    mul(a, b) {
      const o = new Array(16);
      for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
        o[r*4+c] = a[r*4]*b[c] + a[r*4+1]*b[4+c] + a[r*4+2]*b[8+c] + a[r*4+3]*b[12+c];
      }
      return o;
    },
    tr: (x, y, z) => [1,0,0,x, 0,1,0,y, 0,0,1,z, 0,0,0,1],
    sc: (x, y, z) => [x,0,0,0, 0,y,0,0, 0,0,z,0, 0,0,0,1],
    rx(a) { const c = Math.cos(a), s = Math.sin(a); return [1,0,0,0, 0,c,-s,0, 0,s,c,0, 0,0,0,1]; },
    ry(a) { const c = Math.cos(a), s = Math.sin(a); return [c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1]; },
    rz(a) { const c = Math.cos(a), s = Math.sin(a); return [c,-s,0,0, s,c,0,0, 0,0,1,0, 0,0,0,1]; },
    // Compose left to right: chain(A, B, C) applies C first.
    chain(...ms) { return ms.reduce((a, b) => mat.mul(a, b)); },
    apply(m, p) {
      return [m[0]*p[0]+m[1]*p[1]+m[2]*p[2]+m[3],
              m[4]*p[0]+m[5]*p[1]+m[6]*p[2]+m[7],
              m[8]*p[0]+m[9]*p[1]+m[10]*p[2]+m[11]];
    },
  };

  const sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const norm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0]/l, a[1]/l, a[2]/l]; };

  class Renderer {
    constructor(canvas, opts = {}) {
      this.w = opts.w || 192; this.h = opts.h || 144;
      canvas.width = this.w; canvas.height = this.h;
      canvas.style.imageRendering = 'pixelated';
      this.g = canvas.getContext('2d');
      this.img = this.g.createImageData(this.w, this.h);
      this.px = new Uint32Array(this.img.data.buffer);
      this.zb = new Float32Array(this.w * this.h);
      this.bg = opts.bg || [12, 14, 18];
      this.light = norm(opts.light || [-0.4, 0.8, 0.5]);
      this.ambient = opts.ambient ?? 0.35;
      this.steps = opts.steps || 4;     // lighting quantisation
      this.camera([0, 0, 3], [0, 0, 0], 45);
    }

    camera(eye, target, fov) {
      const f = norm(sub(target, eye));
      const r = norm(cross(f, [0, 1, 0]));
      const u = cross(r, f);
      this.eye = eye; this.cf = f; this.cr = r; this.cu = u;
      this.focal = (this.h / 2) / Math.tan(fov * Math.PI / 360);
    }

    // World point -> [sx, sy, depth]; null behind the camera.
    project(p) {
      const d = sub(p, this.eye);
      const z = dot(d, this.cf);
      if (z < 0.05) return null;
      return [this.w / 2 + dot(d, this.cr) * this.focal / z,
              this.h / 2 - dot(d, this.cu) * this.focal / z, z];
    }

    draw(meshes, overlay) {
      const { w, h, px, zb } = this;
      const bgc = 0xff000000 | (this.bg[2] << 16) | (this.bg[1] << 8) | this.bg[0];
      px.fill(bgc); zb.fill(Infinity);
      for (const m of meshes) {
        if (m.hidden) continue;
        const wv = m.m ? m.v.map(p => mat.apply(m.m, p)) : m.v;
        const sv = wv.map(p => this.project(p));
        for (const f of m.f) {
          const [a, b, c] = f.i;
          const A = sv[a], B = sv[b], C = sv[c];
          if (!A || !B || !C) continue;
          const area = (B[0]-A[0]) * (C[1]-A[1]) - (B[1]-A[1]) * (C[0]-A[0]);
          if (area === 0 || (!m.ds && area > 0)) continue;   // back face
          let col;
          if (f.e) col = f.c;
          else {
            let n = norm(cross(sub(wv[b], wv[a]), sub(wv[c], wv[a])));
            if (area > 0) n = [-n[0], -n[1], -n[2]];   // double-sided, seen from behind
            const lit = this.ambient + (1 - this.ambient) * Math.max(0, dot(n, this.light));
            const q = Math.round(lit * this.steps) / this.steps;
            col = [f.c[0] * q, f.c[1] * q, f.c[2] * q];
          }
          const rgba = 0xff000000 | (Math.min(255, col[2]) << 16) | (Math.min(255, col[1]) << 8) | Math.min(255, col[0]);
          this.tri(A, B, C, rgba, area);
        }
      }
      this.g.putImageData(this.img, 0, 0);
      if (overlay) overlay(this.g);
    }

    tri(A, B, C, rgba, area) {
      const { w, h, px, zb } = this;
      const x0 = Math.max(0, Math.floor(Math.min(A[0], B[0], C[0])));
      const x1 = Math.min(w - 1, Math.ceil(Math.max(A[0], B[0], C[0])));
      const y0 = Math.max(0, Math.floor(Math.min(A[1], B[1], C[1])));
      const y1 = Math.min(h - 1, Math.ceil(Math.max(A[1], B[1], C[1])));
      const inv = 1 / area;
      for (let y = y0; y <= y1; y++) {
        const py = y + 0.5;
        for (let x = x0; x <= x1; x++) {
          const pxx = x + 0.5;
          const w0 = ((B[0]-pxx) * (C[1]-py) - (B[1]-py) * (C[0]-pxx)) * inv;
          const w1 = ((C[0]-pxx) * (A[1]-py) - (C[1]-py) * (A[0]-pxx)) * inv;
          const w2 = 1 - w0 - w1;
          if (w0 < 0 || w1 < 0 || w2 < 0) continue;
          const z = w0 * A[2] + w1 * B[2] + w2 * C[2];
          const k = y * w + x;
          if (z < zb[k]) { zb[k] = z; px[k] = rgba; }
        }
      }
    }
  }

  // ---- mesh builders ----
  const quad = (f, a, b, c, d, col, e) => { f.push({ i:[a, b, c], c:col, e }, { i:[a, c, d], c:col, e }); };

  const build = {
    box(sx, sy, sz, col) {
      const x = sx / 2, y = sy / 2, z = sz / 2;
      const v = [[-x,-y,-z],[x,-y,-z],[x,y,-z],[-x,y,-z],[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]];
      const f = [];
      quad(f, 4,5,6,7, col); quad(f, 1,0,3,2, col);   // front, back
      quad(f, 5,1,2,6, col); quad(f, 0,4,7,3, col);   // right, left
      quad(f, 7,6,2,3, col); quad(f, 0,1,5,4, col);   // top, bottom
      return { v, f };
    },

    // Solid of revolution about the x axis. `prof` is [[x, r], ...] from
    // one end to the other; `colorAt(i, j)` colours the band between
    // profile points i and i+1 in angular sector j (or pass a colour).
    // `open` leaves the ends uncapped (a tube seen from outside).
    lathe(prof, seg, colorAt, open) {
      const v = [], f = [];
      const cf = typeof colorAt === 'function' ? colorAt : () => ({ c: colorAt });
      for (const [x, r] of prof) {
        for (let j = 0; j < seg; j++) {
          const a = j / seg * Math.PI * 2;
          v.push([x, Math.cos(a) * r, Math.sin(a) * r]);
        }
      }
      for (let i = 0; i < prof.length - 1; i++) {
        for (let j = 0; j < seg; j++) {
          const j1 = (j + 1) % seg;
          const k = cf(i, j);
          quad(f, i*seg + j, i*seg + j1, (i+1)*seg + j1, (i+1)*seg + j, k.c, k.e);
        }
      }
      if (!open) {
        const n = prof.length - 1;
        const c0 = v.push([prof[0][0], 0, 0]) - 1, c1 = v.push([prof[n][0], 0, 0]) - 1;
        const k0 = cf(0, 0), k1 = cf(n - 1, 0);
        for (let j = 0; j < seg; j++) {
          const j1 = (j + 1) % seg;
          f.push({ i:[c0, j1, j], c:k0.c, e:k0.e });
          f.push({ i:[c1, n*seg + j, n*seg + j1], c:k1.c, e:k1.e });
        }
      }
      return { v, f };
    },

    // Cylinder standing on the y axis, from y=0 to y=hgt.
    cylinder(r, hgt, seg, col) {
      const m = build.lathe([[0, r], [hgt, r]], seg, col);
      m.v = m.v.map(([x, y, z]) => [y, x, z]);
      // Swapping x and y mirrors the mesh, which flips its winding.
      m.f.forEach(fc => { fc.i = [fc.i[0], fc.i[2], fc.i[1]]; });
      return m;
    },
  };

  window.M3 = { Renderer, mat, build };
})();
