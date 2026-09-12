"""Lab floor textures — one per lab level, 32x32 each (two lab tiles square).

The floor is the one asset the player looks at the whole time, so it is the
one that must not shout. Each level gets a different material, and the
material carries the level rather than a colour shift alone:

  Lv1  timber decking          warm, cheap, visibly a shed
  Lv2  bare concrete, cracked  cold and grey, still unfinished
  Lv3  green studded rubber    proper lab flooring, first sign of budget
  Lv4  cream sheet vinyl       finished — and the one seen for most of the run

Tiles are 32x32 rather than 16x16 so a pattern can vary between adjacent lab
tiles without an obvious 16px beat; 32 is a multiple of the 16px art tile, so
alignment with the grid still holds.

No tile boundary is baked in. The game draws its own grid over the floor
(.lab, 0.18 alpha in play and 0.4 in layout mode); over a texture like timber
or rubber that overlay fights the material, so the recommendation is to keep
the grid for layout mode only.
"""
import os, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel', 'floor')
os.makedirs(OUT, exist_ok=True)
S = 32


def new(base):
    im = Image.new('RGBA', (S, S), base + (255,))
    return im, im.load()


def wood():
    """Decking, not brickwork. Butt joints are gone entirely: a vertical joint
    every 16px against a horizontal seam every 8px draws rectangles, and
    rectangles in two tones read as brick no matter what colour they are.
    Long boards plus grain is what says timber."""
    base, seam, grain = (158, 121, 80), (134, 100, 63), (148, 112, 72)
    im, px = new(base)
    rng = random.Random(11)
    for plank in range(4):                       # four 8px boards
        y0 = plank * 8
        tone = rng.choice([base, (163, 126, 84), (152, 116, 76), (160, 123, 81)])
        for y in range(y0, y0 + 8):
            for x in range(S):
                px[x, y] = tone + (255,)
        for x in range(S):
            px[x, y0] = seam + (255,)
        for _ in range(3):                       # grain, the length of the board
            gy = rng.randrange(y0 + 2, y0 + 8)
            gx = rng.randrange(0, S)
            for i in range(rng.randrange(9, 20)):
                px[(gx + i) % S, gy] = grain + (255,)
    return im


def concrete():
    base, lo, hi, crack = (152, 148, 139), (138, 134, 125), (165, 161, 152), (105, 102, 95)
    im, px = new(base)
    rng = random.Random(7)
    for _ in range(150):                         # aggregate mottle
        px[rng.randrange(S), rng.randrange(S)] = rng.choice([lo, hi]) + (255,)
    # Two hairline cracks, kept clear of the edges so the repeat does not
    # produce a crack that stops dead at a tile boundary.
    for (cx, cy, steps) in ((5, 5, 17), (17, 20, 13)):
        x, y = cx, cy
        for i in range(steps):
            px[x % S, y % S] = crack + (255,)
            x += 1
            if i % 3 == 0:
                y += rng.choice([-1, 1])
    return im


def rubber():
    base, hi, lo = (95, 122, 92), (112, 141, 107), (79, 103, 77)
    im, px = new(base)
    for cy in range(4, S, 8):                    # studded rubber sheet
        for cx in range(4, S, 8):
            for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
                px[(cx + dx) % S, (cy + dy) % S] = base + (255,)
            px[(cx - 1) % S, (cy - 1) % S] = hi + (255,)
            px[cx % S, (cy - 1) % S] = hi + (255,)
            px[(cx - 1) % S, cy % S] = hi + (255,)
            px[(cx + 1) % S, (cy + 1) % S] = lo + (255,)
            px[cx % S, (cy + 1) % S] = lo + (255,)
            px[(cx + 1) % S, cy % S] = lo + (255,)
    return im


def vinyl(base):
    """Sheet vinyl: a flat ground with a sparse two-tone fleck. Deliberately
    quiet — this is the surface the player stares at for most of a run."""
    lo = tuple(max(0, v - 14) for v in base)
    hi = tuple(min(255, v + 12) for v in base)
    im, px = new(base)
    rng = random.Random(3)
    for _ in range(70):
        px[rng.randrange(S), rng.randrange(S)] = rng.choice([lo, hi]) + (255,)
    return im


# Lv4 was chosen from a four-step ladder above the current #b8ad8a floor.
# The brightest was picked; the cost is that a cream cabinet sits within a
# hair of the floor in value, which is why every device casts a pixel of
# shadow (see the note in tools/pixelart/devices.py).
LV4 = (222, 212, 183)      # #ded4b7

if __name__ == '__main__':
    wood().save(os.path.join(OUT, 'lv1.png'))
    concrete().save(os.path.join(OUT, 'lv2.png'))
    rubber().save(os.path.join(OUT, 'lv3.png'))
    vinyl(LV4).save(os.path.join(OUT, 'lv4.png'))
    print('floors ok: lv1 lv2 lv3 lv4')
