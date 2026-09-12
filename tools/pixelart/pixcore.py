"""Minimal pixel-art canvas.

Everything here works in integer pixel coordinates on a small grid, because
that is the only way dot art stays editable: one number in the source moves
exactly one dot in the output. Nothing anti-aliases, nothing interpolates.

The palette is sampled from the existing hand-drawn art (cream #f8f1df ground,
navy #2b3252 outline) so pixel assets and painted assets can sit side by side
without a colour clash.
"""
from PIL import Image

# --- Shared palette -------------------------------------------------
# Ground / ink, taken from assets/furnace.png and assets/AGT.png.
P = {
    'bg':      (227, 198, 154),   # warm tan ground, sampled off furnace.png
    'bg2':     (248, 241, 223),   # paler cream ground (AGT-family)
    'shadow':  (203, 172, 132),   # contact shadow on the tan ground
    'shadow2': (228, 214, 186),   # ...and on the pale AGT ground
    'ink':     (43, 50, 82),      # outline navy
    'ink2':    (30, 35, 60),      # deeper navy, for cast shadow inside forms

    # Enamelled cabinet (furnace)
    'body_hi': (253, 246, 232),
    'body':    (240, 228, 204),
    'body_lo': (214, 196, 165),
    'body_dk': (176, 157, 129),

    # Bare metal
    'met_hi':  (200, 205, 216),
    'met':     (154, 162, 180),
    'met_lo':  (106, 113, 137),

    # Heat
    'hot_a':   (255, 214, 102),
    'hot_b':   (255, 154, 60),
    'hot_c':   (230, 96, 40),

    # AGT: brass, verdigris frame, dark wood, crystal
    'brass_hi':(226, 205, 138),
    'brass':   (201, 176, 92),
    'brass_lo':(154, 131, 57),
    'grn_hi':  (188, 198, 156),
    'grn':     (150, 163, 118),
    'grn_lo':  (104, 117, 82),
    'wood':    (122, 74, 58),
    'wood_lo': (82, 48, 38),
    'cry_hi':  (250, 240, 255),
    'cry':     (216, 186, 240),
    'cry_lo':  (160, 124, 200),
    'glow':    (236, 222, 250),

    # Skin
    'sk_hi':   (255, 226, 196),
    'sk':      (240, 201, 160),
    'sk_lo':   (214, 166, 124),

    # Coats / cloth
    'coat_hi': (253, 250, 242),
    'coat':    (235, 230, 216),
    'coat_lo': (205, 198, 180),

    'glass':   (206, 227, 242),   # lens tint
    'white':   (255, 255, 255),
}


class Canvas:
    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.d = {}
        self.bg = bg

    def px(self, x, y, c):
        if c is None:
            return
        if 0 <= x < self.w and 0 <= y < self.h:
            self.d[(x, y)] = c

    def get(self, x, y):
        return self.d.get((x, y))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y0, c); self.px(x, y1, c)
        for y in range(y0, y1 + 1):
            self.px(x0, y, c); self.px(x1, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def disc(self, cx, cy, r, c):
        """Filled circle. Half-integer centres are allowed (cx=7.5) so even
        diameters come out symmetric."""
        rr = (r + 0.5) ** 2
        for y in range(self.h):
            for x in range(self.w):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rr:
                    self.px(x, y, c)

    def ring(self, cx, cy, r_out, r_in, c):
        lo, hi = (r_in - 0.5) ** 2, (r_out + 0.5) ** 2
        for y in range(self.h):
            for x in range(self.w):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if lo < d <= hi:
                    self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(self.h):
            for x in range(self.w):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1.0:
                    self.px(x, y, c)

    def outline(self, c, over=None):
        """Trace a navy edge around every drawn pixel. `over` limits which
        colours may be overwritten (None = only empty cells)."""
        add = []
        for (x, y) in list(self.d):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                cur = self.d.get((nx, ny))
                if cur is None or (over is not None and cur in over):
                    add.append((nx, ny))
        for p in add:
            self.d[p] = c

    def mirror(self, axis, src='left'):
        """Mirror one half onto the other. axis is the x of the centre line
        (may be half-integer, e.g. 15.5 on a 32px canvas)."""
        for (x, y), c in list(self.d.items()):
            if (src == 'left' and x < axis) or (src == 'right' and x > axis):
                self.d[(int(round(2 * axis - x)), y)] = c

    def stamp(self, rows, key, ox=0, oy=0):
        """Paint an ASCII block. Every row must be the same length; '.' is a
        no-op so art can be written as readable text."""
        w = len(rows[0])
        for i, r in enumerate(rows):
            assert len(r) == w, f'row {i} is {len(r)} wide, expected {w}'
            for j, ch in enumerate(r):
                if ch == '.':
                    continue
                self.px(ox + j, oy + i, key[ch])

    def to_image(self):
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        pxs = im.load()
        if self.bg is not None:
            for y in range(self.h):
                for x in range(self.w):
                    pxs[x, y] = self.bg + (255,)
        for (x, y), c in self.d.items():
            pxs[x, y] = c + (255,)
        return im

    def save(self, path, scale=1):
        im = self.to_image()
        if scale != 1:
            im = im.resize((self.w * scale, self.h * scale), Image.NEAREST)
        im.save(path)
        return path
