"""Lab walls — the top face, one strip per lab level and per time of day.

The room is seen the way every device is: front elevation plus a top face.
That means only the far wall shows its face; the left, right and near walls
are edge-on and are drawn by CSS as plain bands. So the art here is the far
wall alone — the one with the windows in it.

Each strip is 64x32 art pixels: four tiles wide and two tall, tiled
horizontally, so the windows recur every four tiles along the room. Day and
night differ only in what is behind the glass.

  Lv1  timber stud wall, one small sash window
  Lv2  bare concrete block, a mesh-glazed industrial light
  Lv3  painted panel wall, a proper wide window
  Lv4  clean lab panelling, a full glazed band
"""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel', 'wall')
os.makedirs(OUT, exist_ok=True)
W, H = 64, 32
INK = P['ink']

SKY_DAY = ((150, 202, 236), (186, 224, 246), (255, 255, 255))   # sky, haze, cloud
SKY_NIGHT = ((30, 38, 72), (46, 56, 96), (236, 240, 190))       # sky, glow, star


def glazing(c, x0, y0, x1, y1, night, bars_v=(), bars_h=()):
    """A window: frame, glass, and whatever is outside it."""
    sky, haze, spec = SKY_NIGHT if night else SKY_DAY
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, sky)
    for y in range(y0 + 1, y0 + 1 + max(1, (y1 - y0) // 3)):
        c.rect(x0 + 1, y, x1 - 1, y, haze)
    rng = random.Random(x0 * 31 + y0)
    for _ in range((x1 - x0) // 3):
        px_, py = rng.randrange(x0 + 2, x1 - 1), rng.randrange(y0 + 1, y1)
        c.px(px_, py, spec)
        if not night:
            c.px(px_ + 1, py, spec)
    for bx in bars_v:
        c.vline(x0 + bx, y0 + 1, y1 - 1, INK)
    for by in bars_h:
        c.hline(x0 + 1, x1 - 1, y0 + by, INK)


def timber(night):
    c = Canvas(W, H)
    base, dark, light = (150, 114, 74), (122, 92, 58), (170, 132, 88)
    c.rect(0, 0, W - 1, H - 1, base)
    for x in range(0, W, 6):                       # vertical boarding
        c.vline(x, 0, H - 1, dark)
        c.vline(x + 1, 0, H - 1, light)
    c.rect(0, 0, W - 1, 1, (108, 80, 50))          # head plate
    c.rect(0, H - 4, W - 1, H - 1, (108, 80, 50))  # sole plate, meeting the floor
    c.hline(0, W - 1, H - 4, (176, 138, 92))
    glazing(c, 22, 6, 41, 21, night, bars_v=(9,), bars_h=(7,))
    c.rect(20, 4, 43, 5, (108, 80, 50))            # lintel
    c.hline(20, 43, 4, light)
    return c


def blockwork(night):
    c = Canvas(W, H)
    base, joint, light = (156, 152, 143), (128, 124, 116), (172, 168, 158)
    c.rect(0, 0, W - 1, H - 1, base)
    for i, y in enumerate(range(0, H, 7)):         # courses, staggered
        c.hline(0, W - 1, y, joint)
        off = 0 if i % 2 == 0 else 8
        for x in range(off, W, 16):
            c.vline(x, y + 1, y + 6, joint)
        c.hline(0, W - 1, y + 1, light)
    c.rect(0, H - 3, W - 1, H - 1, (116, 112, 105))
    glazing(c, 20, 7, 43, 19, night, bars_v=(6, 12, 18), bars_h=(6,))
    return c


def panelling(night):
    c = Canvas(W, H)
    base, seam, light = (188, 182, 168), (160, 154, 142), (206, 200, 186)
    c.rect(0, 0, W - 1, H - 1, base)
    for x in range(0, W, 16):                      # panel seams
        c.vline(x, 0, H - 1, seam)
        c.vline(x + 1, 0, H - 1, light)
    c.rect(0, 0, W - 1, 2, (168, 162, 150))        # cornice
    c.hline(0, W - 1, 2, light)
    c.rect(0, H - 4, W - 1, H - 1, (150, 144, 132))  # skirting
    c.hline(0, W - 1, H - 4, light)
    glazing(c, 8, 7, 55, 20, night, bars_v=(16, 32), bars_h=())
    c.hline(8, 55, 6, (120, 116, 106))             # a sill above and below
    c.hline(8, 55, 21, (120, 116, 106))
    return c


def cleanroom(night):
    c = Canvas(W, H)
    base, seam, light = (222, 218, 208), (196, 192, 180), (240, 237, 230)
    c.rect(0, 0, W - 1, H - 1, base)
    for x in range(0, W, 16):
        c.vline(x, 0, H - 1, seam)
        c.vline(x + 1, 0, H - 1, light)
    c.rect(0, 0, W - 1, 3, (206, 202, 192))        # service duct along the head
    c.hline(0, W - 1, 1, light)
    for x in range(4, W, 8):
        c.px(x, 2, (150, 146, 138))
    c.rect(0, H - 4, W - 1, H - 1, (188, 184, 172))
    c.hline(0, W - 1, H - 4, light)
    glazing(c, 4, 8, 59, 21, night, bars_v=(18, 36), bars_h=())
    c.rect(3, 6, 60, 7, (170, 166, 156))           # deep sill
    c.hline(3, 60, 6, light)
    c.rect(3, 22, 60, 23, (170, 166, 156))
    return c


BUILDERS = {1: timber, 2: blockwork, 3: panelling, 4: cleanroom}

# The edge-on walls are plain bands, so they are colours rather than art. CSS
# paints them; these are only recorded here so the four levels stay together.
SIDE = {1: '#8a6540', 2: '#7c7870', 3: '#7d8a72', 4: '#b3ac98'}
DOOR = {1: '#5c3f22', 2: '#4e4a44', 3: '#4f5a48', 4: '#6d6656'}

if __name__ == '__main__':
    for lv, fn in BUILDERS.items():
        for night in (False, True):
            fn(night).save(os.path.join(OUT, 'top_lv%d_%s.png' % (lv, 'night' if night else 'day')))
    print('walls ok: 4 levels x day/night')
