"""Mock lab floors at art scale, so the sprites can be judged together.

Everything is drawn in art pixels (16 per tile). Scale by a whole number and
you get what the game would show: x3 is the desktop tile, x2 the mobile one.

Two outputs:
  lab-scene.png        the full 16x12 lab with every device at its catalogue
                       position and the roster walking about
  lab-scene-lvN.png    a smaller corner, one per floor material

Device positions come from EQUIPMENT_CATALOG in the game, so the layout is the
one a Lv4 lab actually opens with rather than an arrangement invented here.
"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
T = spec.ART_TILE

# id, col, row, level — from EQUIPMENT_CATALOG (labolic-playtest-40.html:3999)
LAYOUT = [
    ('casting', 1, 0, 1), ('arc', 3, 0, 2), ('laser', 6, 0, 3), ('phase', 9, 0, 4),
    ('furnace', 1, 4, 1), ('rolling', 3, 4, 2), ('magnet', 6, 4, 3), ('agt', 9, 4, 4),
    ('om', 1, 8, 1), ('sem', 3, 8, 2), ('tem', 6, 8, 3), ('qaa', 9, 8, 4),
    ('pc', 13, 4, 1), ('pc', 15, 4, 1),
]
PEOPLE = [('player', 13, 1), ('ben', 5, 2), ('grace', 8, 3), ('smith', 12, 7),
          ('sam', 2, 6), ('dave', 14, 9), ('jeff', 5, 6), ('chen', 8, 10),
          ('lee', 13, 11), ('murphy', 2, 11), ('ingrid', 11, 2)]


def floor(w, h, tile):
    scene = Image.new('RGBA', (w, h))
    t = Image.open(os.path.join(ROOT, tile)).convert('RGBA')
    for y in range(0, h, t.height):
        for x in range(0, w, t.width):
            scene.paste(t, (x, y))
    return scene


def place(scene, path, col, row, tiles_h=1):
    """Anchor by the bottom of the footprint, so a sprite shorter than its
    block sits on the floor and a character taller than one tile hangs up."""
    im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
    scene.alpha_composite(im, (col * T, (row + tiles_h) * T - im.height))


def full_lab(tile='assets/pixel/floor/lv4.png'):
    scene = floor(16 * T, 12 * T, tile)
    for did, col, row, lv in LAYOUT:
        tw, th = spec.FOOTPRINT[lv]
        place(scene, 'assets/pixel/%s.png' % did, col, row, th)
    for cid, col, row in PEOPLE:
        place(scene, 'assets/pixel/char/%s_front.png' % cid, col, row)
    return scene


def corner(tile):
    """A smaller sample for comparing floor materials."""
    scene = floor(13 * T, 6 * T, tile)
    place(scene, 'assets/pixel/furnace.png', 1, 4)
    place(scene, 'assets/pixel/om.png', 3, 4)
    place(scene, 'assets/pixel/agt.png', 8, 4, 2)
    place(scene, 'assets/pixel/char/ben_front.png', 5, 4)
    place(scene, 'assets/pixel/char/smith_front.png', 6, 2)
    place(scene, 'assets/pixel/char/grace_front.png', 11, 3)
    return scene


if __name__ == '__main__':
    out = os.path.join(ROOT, 'build')
    os.makedirs(out, exist_ok=True)
    full_lab().save(os.path.join(out, 'lab-scene.png'))
    for lv in ('lv1', 'lv2', 'lv3', 'lv4'):
        corner('assets/pixel/floor/%s.png' % lv).save(
            os.path.join(out, 'lab-scene-%s.png' % lv))
    print(out, '/ full lab 16x12 + 4 floor samples')
