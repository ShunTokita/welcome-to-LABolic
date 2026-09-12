"""Lab-floor character sprites — 16x24 each (one tile wide, one and a half tall).

Replaces the 0.55-tile circle the game draws today (.character in
labolic-playtest-40.html) with a standing figure that has arms and legs.
The footprint stays 1x1; the sprite simply hangs half a tile above it.

Avatars elsewhere in the game — conversation events, the lab chat, the roster
and hire cards — keep the existing illustrated icons in assets/icon/. Only the
floor is pixel art.

One parametric body serves every character and every cell; a character is a
palette plus three hair routines. That is what makes a 21-person roster
affordable: adding someone is a dict, not a drawing.

SHEET LAYOUT — 48x48 per character, cells of 16x24

        frame 0   |  front   side   back
        frame 1   |  front   side   back

Facings follow the game's own movement, which steps tile to tile on a grid.
`side` is drawn facing right and is mirrored in CSS for left, which the
symmetric projection in spec.py makes free. Two frames are enough because the
figure also slides between tiles under the existing 0.15s transition — the
legs only have to say "walking", not carry the motion.

PROPORTIONS — the landmarks below are the whole design
    head 8 rows, torso 7, legs 6. An earlier 16x32 draft gave the torso 11
    rows and the head 12, which read as a stretched figure rather than a
    stocky one; at this size the head wants to be a touch wider than it is
    tall, and the torso wants to be shorter than the head.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
import spec

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel', 'char')
os.makedirs(OUT, exist_ok=True)
INK = P['ink']
W, H = spec.CHARACTER            # 16 x 24

HEAD_TOP, HEAD_BOT = 1, 9        # ink silhouette rows
SHOULDER = 10
TORSO_TOP, TORSO_BOT = 11, 17
LEG_TOP, LEG_BOT = 17, 22
SHADOW_ROW = 23
EYE = 6


def figure(c, ox, oy, p, facing, frame):
    """Draw one 16x24 cell at (ox, oy)."""
    def px(x, y, col):
        c.px(ox + x, oy + y, col)

    def rect(x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px(x, y, col)

    # --- legs, drawn first so the coat hem overlaps them ----------------
    # The lift has to be two pixels: at one pixel the two frames are
    # indistinguishable in motion, which is worse than not animating at all.
    lift_left = (frame == 1)
    planted = []
    for side, x0, x1 in (('L', 4, 7), ('R', 8, 11)):
        raised = (side == 'L') == lift_left
        bot = LEG_BOT - 2 if raised else LEG_BOT
        rect(x0, LEG_TOP, x1, bot, INK)
        rect(x0 + 1, LEG_TOP + 1, x1 - 1, bot - 2, p['trouser'])
        px(x0 + 1, LEG_TOP + 1, p['trouser_hi'])
        rect(x0 + 1, bot - 1, x1 - 1, bot - 1, p['shoe'])
        if not raised:
            planted.append((x0, x1))

    # --- torso -----------------------------------------------------------
    tx0, tx1 = (5, 10) if facing == 'side' else (4, 11)
    rect(tx0 + 1, SHOULDER, tx1 - 1, SHOULDER, INK)        # shoulders, one step in
    rect(tx0, TORSO_TOP, tx1, TORSO_BOT, INK)
    rect(tx0 + 1, TORSO_TOP, tx1 - 1, TORSO_BOT - 1, p['coat'])
    rect(tx0 + 1, TORSO_TOP, tx0 + 1, TORSO_BOT - 1, p['coat_hi'])
    rect(tx1 - 1, TORSO_TOP, tx1 - 1, TORSO_BOT - 1, p['coat_lo'])
    px(7, SHOULDER, p['skin_lo']); px(8, SHOULDER, p['skin_lo'])   # neck

    if facing == 'front':
        px(7, TORSO_TOP, p['skin_lo']); px(8, TORSO_TOP, p['skin_lo'])   # open collar
        rect(7, TORSO_TOP + 1, 8, TORSO_BOT - 1, p['accent'])
        rect(8, TORSO_TOP + 1, 8, TORSO_BOT - 1, p['accent_lo'])
    elif facing == 'side':
        rect(9, TORSO_TOP + 2, 9, TORSO_BOT - 1, p['accent'])

    # --- arms --------------------------------------------------------------
    swing = 1 if frame == 1 else 0
    arms = [(2, 3, swing), (12, 13, -swing)] if facing != 'side' else [(5, 6, swing)]
    for ax0, ax1, dy in arms:
        rect(ax0, TORSO_TOP + dy, ax1, TORSO_BOT + dy, INK)
        rect(ax0, TORSO_TOP + 1 + dy, ax1, TORSO_BOT - 3 + dy, p['coat'])
        rect(ax0, TORSO_TOP + 1 + dy, ax0, TORSO_BOT - 3 + dy, p['coat_hi'])
        rect(ax0, TORSO_BOT - 2 + dy, ax1, TORSO_BOT - 1 + dy, p['skin'])   # hand

    # --- head ---------------------------------------------------------------
    # Wider than it is tall, and all four corners knocked off: a square head
    # on a body reads as a box, and a tall one reads as stretched.
    rect(3, HEAD_TOP, 12, HEAD_BOT, INK)
    for cx, cy in ((3, HEAD_TOP), (12, HEAD_TOP), (3, HEAD_BOT), (12, HEAD_BOT)):
        c.d.pop((ox + cx, oy + cy), None)
    rect(4, HEAD_TOP + 1, 11, HEAD_BOT - 1, p['skin'])
    rect(11, HEAD_TOP + 2, 11, HEAD_BOT - 1, p['skin_lo'])      # turned-away cheek
    px(7, HEAD_BOT, p['skin']); px(8, HEAD_BOT, p['skin_lo'])   # the jaw opens for a neck

    if facing == 'back':
        rect(4, HEAD_TOP + 1, 11, HEAD_BOT - 1, p['hair'])
        rect(4, HEAD_TOP + 1, 11, HEAD_TOP + 2, p['hair_hi'])
        p['hair_back'](px, p)
    elif facing == 'side':
        rect(4, 2, 7, 8, p['hair'])                             # back of the skull
        rect(4, 2, 7, 3, p['hair_hi'])
        rect(8, 2, 11, 3, p['hair'])                            # fringe over the brow
        rect(8, 4, 11, 8, p['skin'])
        px(12, EYE, INK)                                        # nose, past the face line
        px(10, EYE, INK)                                        # eye
        px(10, 8, p['mouth']); px(11, 8, p['mouth'])            # mouth
        p['hair_side'](px, p)
    else:
        p['hair_front'](px, p)
        px(6, EYE, INK); px(9, EYE, INK)
        px(7, EYE + 1, p['skin_lo'])                            # nose
        px(7, 8, p['mouth']); px(8, 8, p['mouth'])              # mouth

    # --- contact shadow, only under the foot that is actually down ----------
    for x0, x1 in planted:
        for x in range(x0, x1 + 1):
            if (ox + x, oy + SHADOW_ROW) not in c.d:
                px(x, SHADOW_ROW, P['shadow'])


# =====================================================================
# The cast. A character is a palette plus three hair routines.
# =====================================================================
def ben_front(px, p):
    for y in (2, 3, 4):
        for x in range(4, 12):
            px(x, y, p['hair'])
    for x in range(5, 10):
        px(x, 2, p['hair_hi'])
    px(5, 4, p['skin']); px(6, 4, p['skin'])                    # the gap in his fringe
    px(4, 5, p['hair']); px(11, 5, p['hair'])
    for x, col in ((5, INK), (6, P['glass']), (7, INK), (8, INK), (9, P['glass']), (10, INK)):
        px(x, EYE, col)                                         # spectacles, as one bar


def ben_side(px, p):
    px(10, 4, p['hair']); px(11, 4, p['hair'])
    px(10, EYE, INK); px(11, EYE, INK); px(12, EYE, INK)


def ben_back(px, p):
    px(7, 8, p['hair']); px(8, 8, p['hair'])


def grace_front(px, p):
    for y in (2, 3):
        for x in range(4, 12):
            px(x, y, p['hair'])
    for x in range(5, 9):
        px(x, 2, p['hair_hi'])
    for x in range(4, 9):
        px(x, 4, p['hair'])                                     # fringe swept to one side
    px(4, 5, p['hair']); px(11, 4, p['hair']); px(11, 5, p['hair'])
    for y in (4, 5, 6, 7):                                      # ponytail
        px(12, y, p['hair'])
    px(13, 5, INK); px(13, 6, INK)
    px(6, EYE - 1, p['hair']); px(9, EYE - 1, p['hair'])        # brows, in her own hair colour


def grace_side(px, p):
    px(10, 4, p['hair']); px(11, 4, p['hair'])
    px(3, 4, INK); px(3, 5, p['hair']); px(3, 6, p['hair']); px(3, 7, INK)


def grace_back(px, p):
    for x in range(6, 10):                                      # the tail, hanging behind
        px(x, 9, p['hair'])
    px(7, 10, p['hair']); px(8, 10, p['hair'])
    px(7, 11, p['hair_hi']); px(8, 11, p['hair'])


def smith_front(px, p):
    for x in (4, 5, 10, 11):                                    # horseshoe of hair
        px(x, 2, p['hair']); px(x, 3, p['hair']); px(x, 4, p['hair'])
    for x in range(6, 10):
        px(x, 2, p['skin_lo'])                                  # the bald crown
    px(4, 2, p['hair_hi']); px(5, 2, p['hair_hi'])
    px(4, 5, p['hair']); px(11, 5, p['hair'])
    for x, col in ((5, INK), (6, P['glass']), (7, INK), (8, INK), (9, P['glass']), (10, INK)):
        px(x, EYE, col)                                         # half-rim readers
    for x in range(6, 10):
        px(x, EYE + 1, p['hair_hi'])                            # moustache, a step darker

    for x in range(5, 11):                                      # beard
        px(x, 8, p['hair'])
    px(6, 8, p['hair_hi']); px(9, 8, p['hair_hi'])


def smith_side(px, p):
    px(4, 2, p['hair_hi'])
    for y in (7, 8):
        px(10, y, p['hair']); px(11, y, p['hair']); px(12, y, p['hair'])
    px(10, EYE, INK); px(11, EYE, INK); px(12, EYE, INK)


def smith_back(px, p):
    for x in range(6, 10):
        px(x, 2, p['skin_lo']); px(x, 3, p['skin_lo'])          # crown, from behind


CAST = {
    'ben': dict(
        skin=P['sk'], skin_lo=P['sk_lo'], mouth=(176, 114, 86),
        hair=(107, 74, 42), hair_hi=(144, 104, 60),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(126, 96, 60), accent_lo=(92, 68, 40),
        trouser=(128, 138, 166), trouser_hi=(158, 167, 190), shoe=(104, 82, 60),
        hair_front=ben_front, hair_side=ben_side, hair_back=ben_back),
    'grace': dict(
        skin=P['sk_hi'], skin_lo=P['sk'], mouth=(198, 122, 96),
        hair=(214, 160, 70), hair_hi=(242, 202, 124),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(228, 118, 86), accent_lo=(190, 84, 58),
        trouser=(120, 146, 172), trouser_hi=(152, 176, 198), shoe=(112, 88, 66),
        hair_front=grace_front, hair_side=grace_side, hair_back=grace_back),
    'smith': dict(
        skin=P['sk'], skin_lo=P['sk_lo'], mouth=(166, 108, 82),
        hair=(232, 232, 238), hair_hi=(176, 178, 190),
        coat=(109, 100, 190), coat_hi=(142, 133, 216), coat_lo=(76, 68, 148),
        accent=(222, 218, 240), accent_lo=(180, 176, 206),
        trouser=(96, 90, 124), trouser_hi=(124, 118, 152), shoe=(78, 62, 50),
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

print('sprites 16x24 ok:', ', '.join(CAST))
