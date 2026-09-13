"""Bring externally drawn Discovery icons into the game's palette.

Every other sprite in this repository is authored here, in Python, from integer
coordinates. These icons are not: they are drawn elsewhere and handed over as
PNGs. Redrawing them by eye is what went wrong before — looking at a picture
and re-authoring it from a verbal reading of it is a reinterpretation, and the
composition drifts every time. This converts the actual file instead, so the
composition is preserved by construction and only the two things that have to
change do change: the resolution and the colours.

What it does, per file:

  1. strips a flat background if the artwork has one, and trims the margin
  2. downsamples by *majority vote* per destination cell, not by averaging —
     flat pixel-art colour survives a mode filter and turns to mud under a
     mean, especially across an ink outline
  3. snaps every colour to the nearest entry in the shared palette, in Lab,
     so "nearest" means what the eye means rather than what RGB distance means
  4. re-inks the silhouette, because step 2 and 3 both nibble at a 1px outline
  5. writes a 1-bit alpha, since the artifact CSS scales these with
     image-rendering: pixelated and a soft edge shows up as a grey fringe

Usage:
    python3 tools/pixelart/import_product_art.py art-in/product
    python3 tools/pixelart/import_product_art.py art-in/product --size 32
    python3 tools/pixelart/import_product_art.py art-in/product --no-reink

The source files are named <id>.png, with the ids listed in products.py's
SHIPPED. Anything else in the directory is reported and skipped.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image
from pixcore import P
from products import SHIPPED

ROOT = os.path.join(HERE, '..', '..')
OUT = os.path.join(ROOT, 'assets', 'pixel', 'product')

# Ink is picked out of the palette by name rather than by luminance: several
# entries are dark, and only this one is the outline colour.
INK = tuple(P['ink'][:3])
PALETTE = sorted({tuple(v[:3]) for v in P.values() if len(v) == 3 or v[3] == 255})


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------
def _srgb_to_lab(c):
    def f(u):
        u /= 255.0
        u = u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
        return u
    r, g, b = (f(x) for x in c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def g_(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = g_(x), g_(y), g_(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


_LAB = {c: _srgb_to_lab(c) for c in PALETTE}
_SNAP = {}


def snap(c):
    """The nearest palette entry to c, in Lab."""
    if c in _SNAP:
        return _SNAP[c]
    l0, a0, b0 = _srgb_to_lab(c)
    best, bd = None, None
    for p, (l, a, b) in _LAB.items():
        d = (l - l0) ** 2 + (a - a0) ** 2 + (b - b0) ** 2
        if bd is None or d < bd:
            best, bd = p, d
    _SNAP[c] = best
    return best


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def drop_flat_background(im):
    """Make a uniform background transparent.

    Artwork exported on a card rather than on transparency is common, and the
    giveaway is that all four corners are the same opaque colour. Only pixels
    reachable from the edge are cleared, so a patch of that same colour inside
    the drawing is left alone.
    """
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    if not all(c[3] == 255 for c in corners):
        return im
    if len({c[:3] for c in corners}) != 1:
        return im
    bg = corners[0][:3]
    seen = [[False] * h for _ in range(w)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1)]
    stack += [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h) or seen[x][y]:
            continue
        r, g, b, a = px[x, y]
        if a == 0:
            seen[x][y] = True
            continue
        if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) > 12:
            continue
        seen[x][y] = True
        px[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im


def trim(im):
    box = im.getbbox()
    return im.crop(box) if box else im


def downsample(im, size, pad=1):
    """Fit the artwork into a size x size cell by majority vote.

    Every destination pixel takes the most common opaque colour of the source
    region under it, and goes transparent when that region is more than half
    empty. A mean would blend the navy outline into whatever it encloses and
    produce a colour that is in neither.
    """
    w, h = im.size
    inner = size - pad * 2
    scale = min(inner / w, inner / h)
    tw, th = max(1, round(w * scale)), max(1, round(h * scale))
    src = im.load()
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    dst = out.load()
    ox, oy = (size - tw) // 2, (size - th) // 2
    for ty in range(th):
        y0, y1 = int(ty * h / th), max(int(ty * h / th) + 1, int((ty + 1) * h / th))
        for tx in range(tw):
            x0, x1 = int(tx * w / tw), max(int(tx * w / tw) + 1, int((tx + 1) * w / tw))
            votes, empty, total = Counter(), 0, 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b, a = src[x, y]
                    total += 1
                    if a < 128:
                        empty += 1
                    else:
                        votes[(r, g, b)] += 1
            if not votes or empty * 2 > total:
                continue
            dst[ox + tx, oy + ty] = votes.most_common(1)[0][0] + (255,)
    return out


def reink(im):
    """Put the navy back around the silhouette.

    A one-pixel outline is the first thing a downsample eats: half of it falls
    in a cell that votes for the fill instead. Rather than try to preserve it,
    it is redrawn — every opaque pixel with a transparent neighbour becomes
    ink, which is the rule the hand-drawn sprites follow anyway.
    """
    w, h = im.size
    px = im.load()
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or px[nx, ny][3] == 0:
                    edge.append((x, y))
                    break
    for p in edge:
        px[p] = INK + (255,)
    return im


def convert(path, size, do_reink):
    im = drop_flat_background(Image.open(path))
    im = trim(im)
    small = downsample(im, size)
    px = small.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            px[x, y] = (0, 0, 0, 0) if a < 128 else snap((r, g, b)) + (255,)
    if do_reink:
        small = reink(small)
    return small


def main():
    args = [a for a in sys.argv[1:]]
    size = 64
    do_reink = True
    if '--size' in args:
        i = args.index('--size')
        size = int(args[i + 1])
        del args[i:i + 2]
    if '--no-reink' in args:
        do_reink = False
        args.remove('--no-reink')
    if not args:
        print(__doc__)
        return 2
    src_dir = args[0]
    if not os.path.isdir(src_dir):
        print('not a directory:', src_dir)
        return 2

    os.makedirs(OUT, exist_ok=True)
    found = {}
    for name in sorted(os.listdir(src_dir)):
        stem, ext = os.path.splitext(name)
        if ext.lower() != '.png':
            continue
        if stem in SHIPPED:
            found[stem] = os.path.join(src_dir, name)
        else:
            print('  skipped (not a Discovery id):', name)

    for did, path in sorted(found.items()):
        src = Image.open(path)
        out = convert(path, size, do_reink)
        out.save(os.path.join(OUT, did + '.png'))
        print('  %-16s %sx%s -> %sx%s' % (did, src.width, src.height, size, size))

    missing = sorted(SHIPPED - set(found))
    print('converted %d of %d at %dx%d' % (len(found), len(SHIPPED), size, size))
    if missing:
        print('still drawn by products.py:', ' '.join(missing))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
