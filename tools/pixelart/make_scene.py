"""A mock lab floor at art scale, so the sprites can be judged together.

Everything here is drawn in art pixels (16 per tile). Scale it by a whole
number and you get exactly what the game would show: x3 is the desktop tile,
x2 the mobile one.

The floor is the game's own — #b8ad8a with a 1px grid line at every tile
boundary, matching the .lab rule in labolic-playtest-40.html.
"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
T = spec.ART_TILE
COLS, ROWS = 13, 6


def build(floor='assets/pixel/floor/lv4_b.png'):
    scene = Image.new('RGBA', (COLS * T, ROWS * T))
    tile = Image.open(os.path.join(ROOT, floor)).convert('RGBA')
    for y in range(0, scene.height, tile.height):
        for x in range(0, scene.width, tile.width):
            scene.paste(tile, (x, y))

    def place(path, col, row):
        """Anchor by the sprite's own footprint: a sprite taller than its
        tile block hangs upward, which is how the 1x2 characters stand."""
        im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
        scene.alpha_composite(im, (col * T, (row + 1) * T - im.height))

    # The two furnaces sit side by side on purpose: same footprint, same
    # machine, one confined to its tile and one overhanging upward.
    place('assets/pixel/furnace.png', 1, 4)
    place('assets/pixel/furnace_tall.png', 3, 4)
    place('assets/pixel/AGT.png', 8, 4)
    place('assets/pixel/char/ben_front.png', 5, 4)
    place('assets/pixel/char/grace_front.png', 11, 3)
    place('assets/pixel/char/smith_front.png', 6, 2)
    return scene


FLOORS = ['lv1', 'lv2', 'lv3', 'lv4_a', 'lv4_b', 'lv4_c', 'lv4_d']

if __name__ == '__main__':
    outdir = os.path.join(ROOT, 'build')
    os.makedirs(outdir, exist_ok=True)
    for name in FLOORS:
        sc = build('assets/pixel/floor/%s.png' % name)
        sc.save(os.path.join(outdir, 'lab-scene-%s.png' % name))
    sc = build()
    sc.save(os.path.join(outdir, 'lab-scene.png'))
    print(outdir, sc.size, '/', len(FLOORS), 'floors')
