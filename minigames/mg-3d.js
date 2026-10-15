// A very small 3D renderer for the process and synthesis minigames.
//
// The main game is pixel art, so instead of a general-purpose engine this
// rasterises flat-shaded triangles into a small buffer (384x288 by default,
// about one buffer pixel per CSS pixel on a phone) with a z-buffer, and the canvas is scaled up with nearest-
// neighbour sampling. Lighting is quantised to a few steps so surfaces read
// as bands of colour, the way a pixel artist would shade them.
//
// At this resolution a scene of a few thousand triangles costs a few
// milliseconds per frame, and the file is a few KB rather than the ~600 KB
// of three.js. Lightness on phones is the requirement this is built for.
//
//   const r = new M3.Renderer(canvas, { w:384, h:288, bg:[r,g,b] });
//   r.camera([ex,ey,ez], [tx,ty,tz], fovDeg);
//   r.draw([mesh, ...]);
//
// A mesh is { v: [[x,y,z], ...], f: [face, ...], m: 4x4 matrix (optional),
// ds: double-sided }. A face is { i:[a,b,c], c:[r,g,b] } plus, optionally:
//   e      emissive: full colour, unaffected by light (flames, hot glass)
//   a      alpha 0..1: blended over what is behind it
//   add    additive: adds c x a to what is behind it (flames, glow)
//   glass  with `a`: edges seen at a grazing angle turn more opaque and the
//          light leaves a specular highlight, which is what makes a clear
//          tube readable against the background
// Opaque faces are drawn first with the z-buffer; translucent ones after,
// far to near, tested against the z-buffer but not writing it.
//
// Mesh-wide options, for interaction:
//   pick   a number written to a pick buffer wherever the mesh is visible,
//          so r.pickAt(canvas, clientX, clientY) can say what was tapped
//   tint   [r, g, b, k]: lit colour pulled toward [r, g, b] by k (highlight)
//   over   a face style that replaces every face's own (a ghost preview)
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
      this.w = opts.w || 384; this.h = opts.h || 288;
      canvas.width = this.w; canvas.height = this.h;
      canvas.style.imageRendering = 'pixelated';
      this.g = canvas.getContext('2d');
      this.img = this.g.createImageData(this.w, this.h);
      this.px = new Uint32Array(this.img.data.buffer);
      this.zb = new Float32Array(this.w * this.h);
      this.pk = new Int32Array(this.w * this.h);
      this.bg = opts.bg || [12, 14, 18];
      this.light = norm(opts.light || [-0.4, 0.8, 0.5]);
      this.ambient = opts.ambient ?? 0.35;
      this.steps = opts.steps || 6;     // lighting quantisation
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

    // The per-face work runs on flat typed arrays and plain numbers, with
    // no objects or arrays made per vertex or per face: at a few thousand
    // faces, allocation and the garbage it leaves were as costly as the
    // pixel filling itself.
    draw(meshes, overlay) {
      const { w, h, px, zb } = this;
      const bgc = 0xff000000 | (this.bg[2] << 16) | (this.bg[1] << 8) | this.bg[0];
      px.fill(bgc); zb.fill(Infinity); this.pk.fill(0);
      const [ex, ey, ez] = this.eye, [fx, fy, fz] = this.cf, [rx, ry, rz] = this.cr, [ux, uy, uz] = this.cu;
      const [lx, ly, lz] = this.light, focal = this.focal, hw = w / 2, hh = h / 2;
      const amb = this.ambient, steps = this.steps;
      this.nl = 0;
      for (const m of meshes) {
        if (m.hidden) continue;
        const V = m.v, nv = V.length;
        if (!this.wv || this.wv.length < nv * 3) { this.wv = new Float64Array(nv * 6); this.sv = new Float64Array(nv * 6); }
        const wv = this.wv, sv = this.sv, M = m.m;
        for (let i = 0, o = 0; i < nv; i++, o += 3) {
          const p = V[i];
          let x = p[0], y = p[1], z = p[2];
          if (M) {
            const X = M[0]*x + M[1]*y + M[2]*z + M[3], Y = M[4]*x + M[5]*y + M[6]*z + M[7];
            z = M[8]*x + M[9]*y + M[10]*z + M[11]; x = X; y = Y;
          }
          wv[o] = x; wv[o + 1] = y; wv[o + 2] = z;
          const dx = x - ex, dy = y - ey, dz = z - ez;
          const zc = dx * fx + dy * fy + dz * fz;
          if (zc < 0.05) { sv[o + 2] = -1; continue; }
          const k = focal / zc;
          sv[o] = hw + (dx * rx + dy * ry + dz * rz) * k;
          sv[o + 1] = hh - (dx * ux + dy * uy + dz * uz) * k;
          sv[o + 2] = zc;
        }
        const ds = !!m.ds, pid = m.pick | 0, tint = m.tint, ov = m.over;
        for (const f of m.f) {
          const ia = f.i[0] * 3, ib = f.i[1] * 3, ic = f.i[2] * 3;
          const Az = sv[ia + 2], Bz = sv[ib + 2], Cz = sv[ic + 2];
          if (Az < 0 || Bz < 0 || Cz < 0) continue;
          const Ax = sv[ia], Ay = sv[ia + 1], Bx = sv[ib], By = sv[ib + 1], Cx = sv[ic], Cy = sv[ic + 1];
          const area = (Bx - Ax) * (Cy - Ay) - (By - Ay) * (Cx - Ax);
          if (area === 0 || (!ds && area > 0)) continue;   // back face
          const st = ov || f;
          let cr = st.c[0], cg = st.c[1], cb = st.c[2], alpha = st.a ?? 1;
          if (!st.e) {
            // Face normal, flipped when a double-sided face is seen from behind.
            const e1x = wv[ib] - wv[ia], e1y = wv[ib + 1] - wv[ia + 1], e1z = wv[ib + 2] - wv[ia + 2];
            const e2x = wv[ic] - wv[ia], e2y = wv[ic + 1] - wv[ia + 1], e2z = wv[ic + 2] - wv[ia + 2];
            let nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
            let nn = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
            if (area > 0) nn = -nn;
            nx /= nn; ny /= nn; nz /= nn;
            const d = nx * lx + ny * ly + nz * lz;
            const q = Math.round((amb + (1 - amb) * (d > 0 ? d : 0)) * steps) / steps;
            cr *= q; cg *= q; cb *= q;
            if (st.glass) {
              let vx = ex - (wv[ia] + wv[ib] + wv[ic]) / 3, vy = ey - (wv[ia + 1] + wv[ib + 1] + wv[ic + 1]) / 3, vz = ez - (wv[ia + 2] + wv[ib + 2] + wv[ic + 2]) / 3;
              const vl = Math.sqrt(vx * vx + vy * vy + vz * vz) || 1; vx /= vl; vy /= vl; vz /= vl;
              const nv2 = Math.abs(nx * vx + ny * vy + nz * vz);
              const fres = (1 - nv2) * (1 - nv2);
              let hx = lx + vx, hy = ly + vy, hz = lz + vz;
              const hl = Math.sqrt(hx * hx + hy * hy + hz * hz) || 1;
              const sd = (nx * hx + ny * hy + nz * hz) / hl;
              const sq = sd > 0 ? Math.round(Math.pow(sd, 40) * 3) / 3 : 0;   // banded, like the lighting
              alpha = Math.min(1, alpha + 0.55 * fres + 0.8 * sq);
              cr += 255 * sq; cg += 255 * sq; cb += 255 * sq;
            }
          }
          if (tint) { const k = tint[3]; cr += (tint[0] - cr) * k; cg += (tint[1] - cg) * k; cb += (tint[2] - cb) * k; }
          if (st.add || alpha < 1) this.queue(Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, cr, cg, cb, area, st.add ? 2 : 1, alpha, pid);
          else this.tri(Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, cr, cg, cb, area, 0, 1, pid);
        }
      }
      this.flush();
      this.g.putImageData(this.img, 0, 0);
      if (overlay) overlay(this.g);
    }

    // Translucent faces wait in a flat buffer, 17 numbers each, and are
    // drawn far to near after every opaque face is down.
    queue(Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, r, g, b, area, mode, alpha, pid) {
      const n = this.nl;
      if (!this.lq || this.lq.length < (n + 1) * 17) {
        const grown = new Float64Array(Math.max(4352, (n + 1) * 34));
        if (this.lq) grown.set(this.lq);
        this.lq = grown;
      }
      const q = this.lq, o = n * 17;
      q[o] = Ax; q[o+1] = Ay; q[o+2] = Az; q[o+3] = Bx; q[o+4] = By; q[o+5] = Bz;
      q[o+6] = Cx; q[o+7] = Cy; q[o+8] = Cz; q[o+9] = r; q[o+10] = g; q[o+11] = b;
      q[o+12] = area; q[o+13] = mode; q[o+14] = alpha; q[o+15] = Az + Bz + Cz; q[o+16] = pid;
      this.nl = n + 1;
    }

    // Far to near by a bucket sort on depth: linear in the number of faces,
    // and exact enough at this resolution.
    flush() {
      const n = this.nl, q = this.lq;
      if (!n) return;
      let lo = Infinity, hi = -Infinity;
      for (let i = 0; i < n; i++) { const z = q[i * 17 + 15]; if (z < lo) lo = z; if (z > hi) hi = z; }
      const NB = 1024, span = (hi - lo) || 1;
      if (!this.cnt) this.cnt = new Int32Array(NB + 1);
      if (!this.ord || this.ord.length < n) { this.ord = new Int32Array(n * 2); this.bk = new Int32Array(n * 2); }
      const cnt = this.cnt, ord = this.ord, bk = this.bk, sc = NB / span;
      cnt.fill(0);
      for (let i = 0; i < n; i++) {                       // bucket 0 = farthest
        const k = Math.min(NB - 1, ((hi - q[i * 17 + 15]) * sc) | 0);
        bk[i] = k; cnt[k + 1]++;
      }
      for (let k = 0; k < NB; k++) cnt[k + 1] += cnt[k];
      for (let i = 0; i < n; i++) ord[cnt[bk[i]]++] = i;
      for (let k = 0; k < n; k++) {
        const o = ord[k] * 17;
        this.tri(q[o], q[o+1], q[o+2], q[o+3], q[o+4], q[o+5], q[o+6], q[o+7], q[o+8],
                 q[o+9], q[o+10], q[o+11], q[o+12], q[o+13], q[o+14], q[o+16]);
      }
    }

    // mode 0: opaque, writes depth. 1: alpha blend. 2: additive.
    // Edge functions are stepped incrementally along each row, and a row is
    // left as soon as the scan has passed through the triangle.
    tri(Ax, Ay, Az, Bx, By, Bz, Cx, Cy, Cz, cr, cg, cb, area, mode, alpha, pid) {
      const { w, h, px, zb, pk } = this;
      const r = cr > 255 ? 255 : cr | 0, g = cg > 255 ? 255 : cg | 0, b = cb > 255 ? 255 : cb | 0;
      const rgba = 0xff000000 | (b << 16) | (g << 8) | r;
      let x0 = Math.floor(Math.min(Ax, Bx, Cx)), x1 = Math.ceil(Math.max(Ax, Bx, Cx));
      let y0 = Math.floor(Math.min(Ay, By, Cy)), y1 = Math.ceil(Math.max(Ay, By, Cy));
      if (x0 < 0) x0 = 0; if (y0 < 0) y0 = 0; if (x1 > w - 1) x1 = w - 1; if (y1 > h - 1) y1 = h - 1;
      if (x0 > x1 || y0 > y1) return;
      const inv = 1 / area;
      // w0 = E0 * inv over edge B-C, w1 = E1 * inv over edge C-A.
      const d0x = (By - Cy) * inv, d1x = (Cy - Ay) * inv;
      const za = Az - Cz, zbb = Bz - Cz;
      const sx = x0 + 0.5;
      for (let y = y0; y <= y1; y++) {
        const py = y + 0.5;
        let w0 = ((Bx - sx) * (Cy - py) - (By - py) * (Cx - sx)) * inv;
        let w1 = ((Cx - sx) * (Ay - py) - (Cy - py) * (Ax - sx)) * inv;
        let inside = false;
        let k = y * w + x0;
        for (let x = x0; x <= x1; x++, k++, w0 += d0x, w1 += d1x) {
          if (w0 < 0 || w1 < 0 || w0 + w1 > 1) { if (inside) break; continue; }
          inside = true;
          const z = Cz + w0 * za + w1 * zbb;
          if (z >= zb[k]) continue;
          if (mode === 0) { zb[k] = z; px[k] = rgba; pk[k] = pid; continue; }
          if (pid) pk[k] = pid;
          const p0 = px[k];
          let pr = p0 & 255, pg = (p0 >> 8) & 255, pb = (p0 >> 16) & 255;
          if (mode === 1) {
            pr += (r - pr) * alpha; pg += (g - pg) * alpha; pb += (b - pb) * alpha;
          } else {
            pr += r * alpha; pg += g * alpha; pb += b * alpha;
            if (pr > 255) pr = 255; if (pg > 255) pg = 255; if (pb > 255) pb = 255;
          }
          px[k] = 0xff000000 | ((pb | 0) << 16) | ((pg | 0) << 8) | (pr | 0);
        }
      }
    }
  }

  // ---- mesh builders ----
  // `k` is the face style: { c, e, a, add, glass }.
  const quad = (f, a, b, c, d, k) => { f.push({ c:k.c, e:k.e, a:k.a, add:k.add, glass:k.glass, i:[a, b, c] },
                                               { c:k.c, e:k.e, a:k.a, add:k.add, glass:k.glass, i:[a, c, d] }); };

  const build = {
    box(sx, sy, sz, col) {
      const x = sx / 2, y = sy / 2, z = sz / 2;
      const v = [[-x,-y,-z],[x,-y,-z],[x,y,-z],[-x,y,-z],[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]];
      const f = [], k = { c: col };
      quad(f, 4,5,6,7, k); quad(f, 1,0,3,2, k);   // front, back
      quad(f, 5,1,2,6, k); quad(f, 0,4,7,3, k);   // right, left
      quad(f, 7,6,2,3, k); quad(f, 0,1,5,4, k);   // top, bottom
      return { v, f };
    },

    // Solid of revolution about the x axis. `prof` is [[x, r], ...] from
    // one end to the other; `colorAt(i, j)` returns the face style of the
    // band between profile points i and i+1 in angular sector j (or pass
    // a colour, or a style object, for the whole surface).
    // `open` leaves the ends uncapped (a tube seen from outside).
    lathe(prof, seg, colorAt, open) {
      const v = [], f = [];
      const fixed = Array.isArray(colorAt) ? { c: colorAt } : colorAt;
      const cf = typeof colorAt === 'function' ? colorAt : () => fixed;
      for (const [x, r] of prof) {
        for (let j = 0; j < seg; j++) {
          const a = j / seg * Math.PI * 2;
          v.push([x, Math.cos(a) * r, Math.sin(a) * r]);
        }
      }
      for (let i = 0; i < prof.length - 1; i++) {
        for (let j = 0; j < seg; j++) {
          const j1 = (j + 1) % seg;
          quad(f, i*seg + j, i*seg + j1, (i+1)*seg + j1, (i+1)*seg + j, cf(i, j));
        }
      }
      if (!open) {
        const n = prof.length - 1;
        const c0 = v.push([prof[0][0], 0, 0]) - 1, c1 = v.push([prof[n][0], 0, 0]) - 1;
        const k0 = cf(0, 0), k1 = cf(n - 1, 0);
        for (let j = 0; j < seg; j++) {
          const j1 = (j + 1) % seg;
          f.push({ ...k0, i:[c0, j1, j] });
          f.push({ ...k1, i:[c1, n*seg + j, n*seg + j1] });
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

  // What was drawn under a point given in client coordinates (0 for none).
  Renderer.prototype.pickAt = function (canvas, clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    const x = Math.floor((clientX - r.left) / r.width * this.w), y = Math.floor((clientY - r.top) / r.height * this.h);
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return 0;
    return this.pk[y * this.w + x];
  };

  // A matrix that puts local +z along `n` at point `p` (for decals).
  mat.orient = (p, n) => {
    const z = norm(n);
    const up = Math.abs(z[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0];
    const x = norm(cross(up, z)), y = cross(z, x);
    return [x[0], y[0], z[0], p[0], x[1], y[1], z[1], p[1], x[2], y[2], z[2], p[2], 0, 0, 0, 1];
  };

  // A flat blob in the local xy plane facing +z: `radii` gives the radius
  // at evenly spaced angles, so a list of slightly random values makes an
  // irregular stain.
  build.blob = (radii, col) => {
    const n = radii.length, v = [[0, 0, 0]], f = [];
    for (let j = 0; j < n; j++) { const a = j / n * Math.PI * 2; v.push([Math.cos(a) * radii[j], Math.sin(a) * radii[j], 0]); }
    for (let j = 0; j < n; j++) f.push({ c: col, i: [0, 1 + j, 1 + (j + 1) % n] });
    return { v, f };
  };

  // Several meshes, each placed by its own matrix, as one mesh (one part
  // to tap, one matrix to move).
  build.merge = list => {
    const v = [], f = [];
    for (const m of list) {
      const base = v.length;
      for (const p of m.v) v.push(m.m ? mat.apply(m.m, p) : p);
      for (const fc of m.f) f.push({ ...fc, i: [fc.i[0] + base, fc.i[1] + base, fc.i[2] + base] });
    }
    return { v, f };
  };
  // Stand a lathe (built along x) upright on y. Swapping the axes mirrors
  // the mesh, so the winding is flipped back.
  build.upright = m => {
    m.v = m.v.map(([x, y, z]) => [y, x, z]);
    m.f.forEach(f => { f.i = [f.i[0], f.i[2], f.i[1]]; });
    return m;
  };
  // Shorthand: a mesh with a matrix, for build.merge.
  build.at = (m, M) => { m.m = M; return m; };

  window.M3 = { Renderer, mat, build };
})();
