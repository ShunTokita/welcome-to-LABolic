"""Lab-floor character sprites — 16x32 each (one tile wide, two tall).

Replaces the 0.55-tile circle the game draws today (.character in
labolic-playtest-40.html) with a standing figure that has arms and legs.

One parametric body serves every character and every cell; a character is a
palette plus a hair shape. That is what makes a 21-person roster affordable:
adding someone is a dict, not a drawing.

SHEET LAYOUT — 48x64 per character, cells of 16x32

        frame 0   |  front   side   back
        frame 1   |  front   side   back

Facings follow the game's own movement, which steps tile to tile on a grid:
`side` is drawn facing right and is mirrored in CSS for left, which the
symmetric projection in spec.py makes free. Two frames are enough because the
figure also slides between tiles under the existing 0.15s transition — the
legs only have to say "walking", not carry the motion.

The feet sit on the last row of the lower tile, so the sprite is anchored by
its feet: a character on tile (col,row) draws into (col, row-1)..(col, row).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
import spec

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel', 'char')
os.makedirs(OUT, exist_ok=True)
INK = P['ink']
W, H = spec.CHARACTER            # 16 x 32


def figure(c, ox, oy, p, facing, frame):
    """Draw one 16x32 cell at (ox, oy)."""
    def px(x, y, col):
        c.px(ox + x, oy + y, col)

    def rect(x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px(x, y, col)

    # --- legs, drawn first so the coat hem overlaps them --------------
    # A two-frame walk at this size alternates which foot is off the ground.
    # The lift has to be two pixels: at one pixel the two frames are
    # indistinguishable in motion, which is worse than not animating at all.
    lift_left = (frame == 1)
    planted = []
    for side, x0, x1 in (('L', 4, 7), ('R', 8, 11)):
        raised = (side == 'L') == lift_left
        top, bot = 23, (28 if raised else 30)
        rect(x0, top, x1, bot, INK)
        rect(x0 + 1, top + 1, x1 - 1, bot - 2, p['trouser'])
        px(x0 + 1, top + 1, p['trouser_hi'])
        rect(x0, bot - 1, x1, bot, INK)
        rect(x0 + 1, bot - 1, x1 - 1, bot - 1, p['shoe'])
        if not raised:
            planted.append((x0, x1))

    # --- torso ---------------------------------------------------------
    if facing == 'side':
        tx0, tx1 = 5, 10
    else:
        tx0, tx1 = 4, 11
    rect(tx0 + 1, 14, tx1 - 1, 14, INK)                    # shoulders, one step in
    rect(tx0, 15, tx1, 24, INK)
    rect(tx0 + 1, 15, tx1 - 1, 23, p['coat'])
    rect(tx0 + 1, 15, tx0 + 1, 23, p['coat_hi'])           # lit left edge
    rect(tx1 - 1, 15, tx1 - 1, 23, p['coat_lo'])           # shaded right edge

    if facing == 'front':
        px(7, 15, p['skin_lo']); px(8, 15, p['skin_lo'])   # open collar
        rect(7, 16, 8, 22, p['accent'])                    # tie / scarf / placket
        rect(8, 16, 8, 22, p['accent_lo'])
    elif facing == 'side':
        rect(9, 16, 9, 22, p['accent'])

    # --- arms ----------------------------------------------------------
    swing = 2 if frame == 1 else 0
    arms = [(2, 3, swing), (12, 13, -swing)] if facing != 'side' else [(5, 6, swing)]
    for ax0, ax1, dy in arms:
        rect(ax0, 15 + dy, ax1, 23 + dy, INK)
        rect(ax0, 16 + dy, ax1, 20 + dy, p['coat'])
        rect(ax0, 16 + dy, ax0, 20 + dy, p['coat_hi'])
        rect(ax0, 21 + dy, ax1, 22 + dy, p['skin'])        # hand

    # --- head ----------------------------------------------------------
    # Square corners read as a box on a body, so all four are knocked off.
    rect(3, 2, 12, 13, INK)
    for cx, cy in ((3, 2), (12, 2), (3, 13), (12, 13)):
        c.d.pop((ox + cx, oy + cy), None)
    rect(4, 3, 11, 12, p['skin'])
    rect(11, 4, 11, 12, p['skin_lo'])                      # turned-away cheek

    if facing == 'back':
        rect(4, 3, 11, 11, p['hair'])
        rect(4, 3, 11, 4, p['hair_hi'])
        p['hair_back'](px, p)
    elif facing == 'side':
        # The profile only reads if the face gets real estate: hair to the
        # back half of the skull, skin from the brow forward, and a nose that
        # breaks the silhouette.
        rect(4, 3, 7, 11, p['hair'])
        rect(4, 3, 7, 4, p['hair_hi'])
        rect(8, 3, 11, 4, p['hair'])                       # fringe over the brow
        rect(8, 5, 11, 12, p['skin'])
        px(12, 7, INK); px(12, 8, INK)                     # nose, past the face line
        px(11, 8, p['skin'])
        px(10, 7, INK)                                     # eye
        px(10, 10, p['skin_lo']); px(11, 10, p['skin_lo']) # mouth
        p['hair_side'](px, p)
    else:
        p['hair_front'](px, p)
        px(6, 8, INK); px(9, 8, INK)                       # eyes
        px(5, 8, p['skin_lo']); px(10, 8, p['skin_lo'])
        px(7, 10, p['skin_lo']); px(8, 10, p['skin_lo'])   # mouth
        px(7, 9, p['skin_lo'])                             # nose

    # --- contact shadow, only under the foot that is actually down -------
    for x0, x1 in planted:
        for x in range(x0, x1 + 1):
            if (ox + x, oy + 31) not in c.d:
                px(x, 31, P['shadow'])


# =====================================================================
# The cast. A character is a palette plus three hair routines.
# =====================================================================
def ben_front(px, p):
    for x in range(4, 12):
        px(x, 3, p['hair']); px(x, 4, p['hair']); px(x, 5, p['hair'])
    for x in range(4, 12):
        px(x, 6, p['hair'] if x not in (6, 7, 8) else p['skin'])   # the gap in his fringe
    px(4, 7, p['hair']); px(11, 7, p['hair'])
    for x in range(5, 10):
        px(x, 3, p['hair_hi'])
    px(5, 6, INK); px(10, 6, INK)                                  # spectacle rims
    for x in (5, 6, 9, 10):
        px(x, 7, INK)
    px(6, 7, P['glass']); px(9, 7, P['glass'])
    px(7, 7, INK); px(8, 7, INK)                                   # bridge


def ben_side(px, p):
    px(10, 4, p['hair']); px(11, 4, p['hair'])
    px(10, 7, INK); px(11, 7, INK); px(12, 7, INK)                 # spectacles in profile


def ben_back(px, p):
    px(7, 11, p['hair']); px(8, 11, p['hair'])


def grace_front(px, p):
    for x in range(4, 12):
        px(x, 3, p['hair']); px(x, 4, p['hair'])
    for i, x in enumerate(range(4, 12)):                           # fringe swept to one side
        px(x, 5, p['hair'] if x < 10 else p['skin'])
        px(x, 6, p['hair'] if x < 7 else p['skin'])
    for x in range(5, 9):
        px(x, 3, p['hair_hi'])
    px(4, 5, p['hair']); px(4, 6, p['hair']); px(4, 7, p['hair'])
    px(11, 5, p['hair']); px(11, 6, p['hair'])
    px(13, 6, INK); px(13, 7, INK); px(13, 8, INK)                 # ponytail
    px(12, 5, p['hair']); px(12, 6, p['hair']); px(12, 7, p['hair']); px(12, 8, p['hair'])


def grace_side(px, p):
    px(10, 4, p['hair']); px(11, 4, p['hair'])
    px(3, 5, INK); px(3, 6, p['hair']); px(3, 7, p['hair']); px(3, 8, INK)


def grace_back(px, p):
    for x in range(5, 11):                                 # the tail, hanging behind
        px(x, 12, p['hair'])
    px(7, 13, p['hair']); px(8, 13, p['hair'])
    px(7, 14, p['hair']); px(8, 14, p['hair'])
    px(7, 15, p['hair_hi']); px(8, 15, p['hair'])


def smith_front(px, p):
    for x in range(4, 12):                                         # horseshoe of hair
        px(x, 3, p['hair'] if x in (4, 5, 10, 11) else p['skin_lo'])
    for x in (4, 5, 10, 11):
        px(x, 4, p['hair']); px(x, 5, p['hair']); px(x, 6, p['hair'])
    px(4, 3, p['hair_hi']); px(11, 3, p['hair'])
    px(5, 7, INK); px(6, 7, INK); px(9, 7, INK); px(10, 7, INK)    # half-rim readers
    px(6, 8, P['glass']); px(9, 8, P['glass'])
    for x in range(5, 11):                                         # beard
        px(x, 11, p['hair']); px(x, 12, p['hair'])
    px(6, 10, p['hair']); px(9, 10, p['hair'])
    px(7, 10, p['hair_hi']); px(8, 10, p['hair_hi'])               # moustache


def smith_side(px, p):
    px(4, 3, p['hair_hi'])
    for y in range(9, 13):
        px(10, y, p['hair']); px(11, y, p['hair'])
    px(12, 10, p['hair'])
    px(10, 7, INK); px(11, 7, INK); px(12, 7, INK)


def smith_back(px, p):
    for x in range(5, 11):
        px(x, 3, p['skin_lo']); px(x, 4, p['skin_lo'])     # the crown, seen from behind
    for x in (4, 5, 10, 11):
        px(x, 3, p['hair'])
    for y in range(5, 12):
        px(4, y, p['hair']); px(11, y, p['hair'])
    for x in range(4, 12):
        px(x, 9, p['hair']); px(x, 10, p['hair']); px(x, 11, p['hair'])


CAST = {
    'ben': dict(
        skin=P['sk'], skin_lo=P['sk_lo'],
        hair=(107, 74, 42), hair_hi=(144, 104, 60),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(126, 96, 60), accent_lo=(92, 68, 40),
        trouser=(96, 104, 128), trouser_hi=(126, 134, 158), shoe=(64, 58, 50),
        hair_front=ben_front, hair_side=ben_side, hair_back=ben_back),
    'grace': dict(
        skin=P['sk_hi'], skin_lo=P['sk'],
        hair=(214, 160, 70), hair_hi=(242, 202, 124),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(228, 118, 86), accent_lo=(190, 84, 58),
        trouser=(88, 110, 132), trouser_hi=(120, 142, 164), shoe=(72, 62, 52),
        hair_front=grace_front, hair_side=grace_side, hair_back=grace_back),
    'smith': dict(
        skin=P['sk'], skin_lo=P['sk_lo'],
        hair=(232, 232, 238), hair_hi=(176, 178, 190),
        coat=(109, 100, 190), coat_hi=(142, 133, 216), coat_lo=(76, 68, 148),
        accent=(222, 218, 240), accent_lo=(180, 176, 206),
        trouser=(62, 58, 82), trouser_hi=(86, 82, 110), shoe=(44, 40, 56),
        hair_front=smith_front, hair_side=smith_side, hair_back=smith_back),
}

FACINGS = ('front', 'side', 'back')

for cid, pal in CAST.items():
    sheet = Canvas(W * len(FACINGS), H * 2)
    for row in (0, 1):
        for col, facing in enumerate(FACINGS):
            figure(sheet, col * W, row * H, pal, facing, row)
    sheet.save(os.path.join(OUT, cid + '.png'))
    sheet.save(os.environ['SCRATCH'] + '/sheet_%s_x8.png' % cid, scale=8)

    single = Canvas(W, H)
    figure(single, 0, 0, pal, 'front', 0)
    single.save(os.path.join(OUT, cid + '_front.png'))

print('sprites ok:', ', '.join(CAST))
