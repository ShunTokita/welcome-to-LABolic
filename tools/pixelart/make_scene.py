"""A mock lab floor at art scale, so the sprites can be judged together.

Everything here is drawn in art pixels (16 per tile). Scale it by a whole
number and you get exactly what the game would show: x3 is the desktop tile,
x2 the mobile one.

The floor is the game's own — #b8ad8a with a 1px grid line at every tile
boundary, matching the .lab rule in labolic-playtest-40.html.
"""
import sys, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
T = spec.ART_TILE
COLS, ROWS = 13, 6
FLOOR = (184, 173, 138)
GRID = (152, 141, 112)


def build():
    scene = Image.new('RGBA', (COLS * T, ROWS * T), FLOOR + (255,))
    px = scene.load()
    for x in range(scene.width):          # the game's 1px grid, at every tile edge
        for y in range(0, scene.height, T):
            px[x, y] = GRID + (255,)
    for y in range(scene.height):
        for x in range(0, scene.width, T):
            px[x, y] = GRID + (255,)

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


if __name__ == '__main__':
    out = os.path.join(ROOT, 'build', 'lab-scene.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    s = build()
    s.save(out)
    s.resize((s.width * 3, s.height * 3), Image.NEAREST).save(
        os.environ['SCRATCH'] + '/scene_x3.png')
    print(out, s.size)
