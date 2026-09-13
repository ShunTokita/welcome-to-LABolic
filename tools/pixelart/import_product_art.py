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
  4. opens and closes the mask, so the silhouette stops zig-zagging by a pixel
  5. absorbs single pixels that match none of their neighbours
  6. re-inks the silhouette, because steps 2 and 3 both nibble at a 1px outline,
     then thins it back to one pixel where the source's own outline survived
  7. writes a 1-bit alpha, since the artifact CSS scales these with
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
def drop_flat_background(im, passes=4):
    """Make a uniform background transparent.

    Artwork exported on a card rather than on transparency is common, and the
    giveaway is that all four corners are the same opaque colour. Only pixels
    reachable from the edge are cleared, so a patch of that same colour inside
    the drawing is left alone.

    Repeated, because a card is often more than one flat layer — a coloured
    border around a cream field is two, and clearing only the outermost leaves
    the field behind as a rectangle that the re-inking then draws a frame
    around.
    """
    im = im.convert('RGBA')
    for _ in range(passes):
        before = sum(1 for p in im.get_flattened_data() if p[3] == 0)
        im = _drop_one_flat_layer(im)
        if sum(1 for p in im.get_flattened_data() if p[3] == 0) == before:
            break
    return im


def _drop_one_flat_layer(im):
    w, h = im.size
    px = im.load()
    ring = []
    for x in range(w):
        ring += [px[x, 0], px[x, h - 1]]
    for y in range(h):
        ring += [px[0, y], px[w - 1, y]]
    opaque = [c[:3] for c in ring if c[3] == 255]
    if not opaque:
        return im
    # The background is whatever most of the border ring is, not whatever the
    # corners happen to be: on a card where the drawing runs into one corner,
    # a corners-only test never agrees and the field is never cleared.
    #
    # Taken as a median with a tolerance rather than as the commonest bucket:
    # a flat colour out of a lossy encoder straddles bucket boundaries, and
    # split three ways it can lose a majority vote to nothing at all.
    bg = tuple(sorted(c[k] for c in opaque)[len(opaque) // 2] for k in range(3))
    near = sum(1 for c in opaque
               if max(abs(c[k] - bg[k]) for k in range(3)) <= 16)
    if near * 100 < len(ring) * 55:
        return im

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
        if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) > 16:
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


# --------------------------------------------------------------------------
# cleanup
# --------------------------------------------------------------------------
INKS = (INK, tuple(P['ink2'][:3]))
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _neighbours(px, w, h, x, y):
    for dx, dy in N4:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            yield nx, ny, px[nx, ny]


def clean_alpha(im, rounds=2):
    """Straighten the silhouette.

    Majority-vote downsampling decides each destination pixel on its own, so
    along a boundary the vote flips back and forth and the edge comes out with
    one-pixel spurs and notches. Opening then closing the mask removes both:
    an opaque pixel hanging off the shape by a single corner goes, and a
    single-pixel bite out of the shape fills in.
    """
    w, h = im.size
    for _ in range(rounds):
        px = im.load()
        drop, fill = [], []
        for y in range(h):
            for x in range(w):
                opaque = [n for n in _neighbours(px, w, h, x, y) if n[2][3] == 255]
                if px[x, y][3] == 255:
                    if len(opaque) < 2:
                        drop.append((x, y))
                elif len(opaque) >= 3:
                    fill.append(((x, y), Counter(n[2][:3] for n in opaque).most_common(1)[0][0]))
        if not drop and not fill:
            break
        for p in drop:
            px[p] = (0, 0, 0, 0)
        for p, col in fill:
            px[p] = col + (255,)
    return im


def despeckle(im):
    """Absorb single pixels that match none of their neighbours.

    The source art is shaded finely enough that at this scale a lone cell can
    win a vote for a colour that appears nowhere around it. One such pixel
    reads as dirt, and a field of them reads as noise.

    Judged over all eight neighbours, not four: a one-pixel line running
    diagonally has no orthogonal neighbour of its own colour, so a four-way
    test calls every pixel of it a speck and dissolves the line. That is what
    happened to the sink's drain the first time.
    """
    w, h = im.size
    px = im.load()
    fix = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 255:
                continue
            here = px[x, y][:3]
            around = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 255:
                        around.append(px[nx, ny][:3])
            if around and here not in around:
                fix.append(((x, y), Counter(around).most_common(1)[0][0]))
    for p, col in fix:
        px[p] = col + (255,)
    return im


def thin_ink(im):
    """Bring the outline back to one pixel everywhere.

    Re-inking only ever marks the boundary, so a two-pixel edge means the
    source's own outline survived the downsample just inside the new one. The
    inner of the two is replaced by whatever it encloses; an interior dark
    line that never touches the silhouette has no boundary ink beside it and
    is left alone.
    """
    w, h = im.size
    px = im.load()
    edge = set()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 255 and px[x, y][:3] in INKS:
                if any(n[2][3] != 255 for n in _neighbours(px, w, h, x, y)) or \
                        x in (0, w - 1) or y in (0, h - 1):
                    edge.add((x, y))
    fix = []
    for y in range(h):
        for x in range(w):
            if (x, y) in edge or px[x, y][3] != 255 or px[x, y][:3] not in INKS:
                continue
            if not any((n[0], n[1]) in edge for n in _neighbours(px, w, h, x, y)):
                continue
            fill = [n[2][:3] for n in _neighbours(px, w, h, x, y)
                    if n[2][3] == 255 and n[2][:3] not in INKS]
            if fill:
                fix.append(((x, y), Counter(fill).most_common(1)[0][0]))
    for p, col in fix:
        px[p] = col + (255,)
    return im


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
    small = clean_alpha(small)
    px = small.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            px[x, y] = (0, 0, 0, 0) if a < 128 else snap((r, g, b)) + (255,)
    small = despeckle(small)
    if do_reink:
        small = reink(small)
        small = thin_ink(small)
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
