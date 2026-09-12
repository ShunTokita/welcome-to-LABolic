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

# The head gained a row by starting at y0 instead of y1, and the neck gave up
# one of its two rows. Both go to the face: the eye band is now three rows
# deep (BROW, EYE, EYE+1), which is what a pair of spectacles needs — at one
# row every frame becomes a dark bar and Ben and Smith stop being tellable.
HEAD_TOP, HEAD_BOT = 0, 9        # ink silhouette rows; interior y1..y8
SHOULDER = 10
TORSO_TOP, TORSO_BOT = 11, 17
LEG_TOP, LEG_BOT = 17, 22
SHADOW_ROW = 23
BROW, EYE = 5, 6
MOUTH = 8


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
    rect(4, 1, 11, 8, p['skin'])
    rect(11, 2, 11, 8, p['skin_lo'])                            # turned-away cheek
    px(7, HEAD_BOT, p['skin']); px(8, HEAD_BOT, p['skin_lo'])   # the jaw opens for a neck

    if facing == 'back':
        rect(4, 1, 11, 8, p['hair'])
        rect(4, 1, 11, 2, p['hair_hi'])
        p['hair_back'](px, p)
    elif facing == 'side':
        rect(4, 1, 7, 8, p['hair'])                             # back of the skull
        rect(4, 1, 7, 2, p['hair_hi'])
        rect(8, 1, 11, 2, p['hair'])                            # fringe over the brow
        rect(8, 3, 11, 8, p['skin'])
        px(12, EYE, INK)                                        # nose, past the face line
        p['eyes_side'](px, p)
        if p['mouth_w']:
            px(10, MOUTH, p['mouth']); px(11, MOUTH, p['mouth'])
        p['hair_side'](px, p)
    else:
        p['hair_front'](px, p)
        p['eyes_front'](px, p)
        if p['mouth_w']:
            rect(8 - p['mouth_w'] // 2, MOUTH, 7 + (p['mouth_w'] + 1) // 2,
                 MOUTH, p['mouth'])

    # --- contact shadow, only under the foot that is actually down ----------
    for x0, x1 in planted:
        for x in range(x0, x1 + 1):
            if (ox + x, oy + SHADOW_ROW) not in c.d:
                px(x, SHADOW_ROW, P['shadow'])


# =====================================================================
# The cast. A character is a palette plus a few small routines: hair for each
# facing, an eye treatment, and how wide a mouth it wants (0 for none — a
# beard or a strong pair of spectacles already carries the lower face, and
# two more dark pixels there only muddy it).
#
# Every routine works inside the head interior, x4..11 by y1..y8:
#   y1..y3  hair            y4  brow line / forehead
#   y5..y7  the eye band    y8  mouth
# =====================================================================
GLASS = P['glass']


def eyes_plain(px, p):
    """Two two-pixel eyes under brows in the character's own hair colour.
    Brows in ink directly above ink eyes read as a scowl."""
    for x in (5, 6, 9, 10):
        px(x, BROW, p['hair'])
        px(x, EYE, INK)


def eyes_plain_side(px, p):
    # One pixel of brow in profile. Two reads as a blob on the cheek.
    px(10, BROW, p['hair'])
    px(10, EYE, INK); px(11, EYE, INK)


def eyes_round_glasses(px, p):
    """Ben's: two round lenses and a bridge, across all three eye rows. His
    shipped icon is nothing but these spectacles, so they get the budget."""
    px(5, BROW, INK); px(10, BROW, INK)
    px(4, EYE, INK); px(5, EYE, GLASS); px(6, EYE, INK)
    px(7, EYE, INK); px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)
    px(5, EYE + 1, INK); px(10, EYE + 1, INK)


def eyes_half_rim(px, p):
    """Smith's: a straight top rim and no bottom rim, over white brows."""
    for x in (4, 5, 10, 11):
        px(x, 4, p['hair'])
    for x in (4, 5, 6, 9, 10, 11):
        px(x, BROW, INK)
    px(4, EYE, INK); px(5, EYE, GLASS); px(6, EYE, INK)
    px(7, EYE, INK); px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)


def eyes_glasses_side(px, p):
    px(8, EYE, INK)                                             # temple
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)


# --- Ben ---------------------------------------------------------------
def ben_front(px, p):
    for y in (1, 2, 3):
        for x in range(4, 12):
            px(x, y, p['hair'])
    for x in range(5, 10):
        px(x, 1, p['hair_hi'])
    px(5, 3, p['skin']); px(6, 3, p['skin'])                    # the gap in his fringe
    px(4, 4, p['hair']); px(11, 4, p['hair'])


def ben_side(px, p):
    px(10, 3, p['hair']); px(11, 3, p['hair'])


def ben_back(px, p):
    px(7, 8, p['hair']); px(8, 8, p['hair'])


# --- Grace -------------------------------------------------------------
def grace_front(px, p):
    for y in (1, 2):
        for x in range(4, 12):
            px(x, y, p['hair'])
    for x in range(5, 9):
        px(x, 1, p['hair_hi'])
    for x in range(4, 9):
        px(x, 3, p['hair'])                                     # fringe, swept one way
    px(4, 4, p['hair']); px(11, 3, p['hair'])
    for y in (3, 4, 5, 6):                                      # ponytail
        px(12, y, p['hair'])
    px(13, 4, INK); px(13, 5, INK)


def grace_side(px, p):
    px(10, 3, p['hair'])
    for y in (3, 4, 5, 6):
        px(3, y, p['hair'])
    px(2, 4, INK); px(2, 5, INK)


def grace_back(px, p):
    for x in range(6, 10):                                      # the tail, hanging behind
        px(x, 9, p['hair'])
    px(7, 10, p['hair']); px(8, 10, p['hair'])
    px(7, 11, p['hair_hi']); px(8, 11, p['hair'])


# --- Smith -------------------------------------------------------------
def smith_front(px, p):
    for x in (4, 5, 10, 11):                                    # horseshoe of hair
        for y in (1, 2, 3):
            px(x, y, p['hair'])
    for x in range(6, 10):                                      # the bald crown
        px(x, 1, p['skin_lo']); px(x, 2, p['skin_lo']); px(x, 3, p['skin'])
    px(4, 1, p['hair_hi']); px(5, 1, p['hair_hi'])
    for x in range(6, 10):
        px(x, EYE + 1, p['hair_hi'])                            # moustache
    for x in range(5, 11):
        px(x, MOUTH, p['hair'])                                 # beard
    px(6, MOUTH, p['hair_hi']); px(9, MOUTH, p['hair_hi'])


def smith_side(px, p):
    px(4, 1, p['hair_hi'])
    for y in (EYE + 1, MOUTH):
        px(10, y, p['hair']); px(11, y, p['hair']); px(12, y, p['hair'])


def smith_back(px, p):
    for x in range(6, 10):
        px(x, 1, p['skin_lo']); px(x, 2, p['skin_lo'])          # crown, from behind


CAST = {
    'ben': dict(
        skin=P['sk'], skin_lo=P['sk_lo'], mouth=(176, 114, 86), mouth_w=0,
        hair=(107, 74, 42), hair_hi=(144, 104, 60),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(126, 96, 60), accent_lo=(92, 68, 40),
        trouser=(128, 138, 166), trouser_hi=(158, 167, 190), shoe=(104, 82, 60),
        hair_front=ben_front, hair_side=ben_side, hair_back=ben_back,
        eyes_front=eyes_round_glasses, eyes_side=eyes_glasses_side),
    'grace': dict(
        skin=P['sk_hi'], skin_lo=P['sk'], mouth=(198, 122, 96), mouth_w=2,
        hair=(214, 160, 70), hair_hi=(242, 202, 124),
        coat=P['coat'], coat_hi=P['coat_hi'], coat_lo=P['coat_lo'],
        accent=(228, 118, 86), accent_lo=(190, 84, 58),
        trouser=(120, 146, 172), trouser_hi=(152, 176, 198), shoe=(112, 88, 66),
        hair_front=grace_front, hair_side=grace_side, hair_back=grace_back,
        eyes_front=eyes_plain, eyes_side=eyes_plain_side),
    'smith': dict(
        skin=P['sk'], skin_lo=P['sk_lo'], mouth=(166, 108, 82), mouth_w=0,
        hair=(232, 232, 238), hair_hi=(176, 178, 190),
        coat=(109, 100, 190), coat_hi=(142, 133, 216), coat_lo=(76, 68, 148),
        accent=(222, 218, 240), accent_lo=(180, 176, 206),
        trouser=(96, 90, 124), trouser_hi=(124, 118, 152), shoe=(78, 62, 50),
        hair_front=smith_front, hair_side=smith_side, hair_back=smith_back,
        eyes_front=eyes_half_rim, eyes_side=eyes_glasses_side),
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
