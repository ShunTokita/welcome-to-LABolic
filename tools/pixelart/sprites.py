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

    # The collar carries the character's roster colour right across the
    # shoulders. At 16px a two-pixel placket is not enough to tell twenty-six
    # white coats apart; a six-pixel band is, and it matches the colour the UI
    # already uses for that person.
    rect(tx0 + 1, TORSO_TOP, tx1 - 1, TORSO_TOP, p['accent'])
    rect(tx0 + 1, TORSO_TOP, tx0 + 1, TORSO_TOP, tint(p['accent'], 1.18))
    rect(tx1 - 1, TORSO_TOP, tx1 - 1, TORSO_TOP, p['accent_lo'])
    if facing == 'front':
        rect(7, TORSO_TOP + 1, 8, TORSO_BOT - 1, p['accent'])
        rect(8, TORSO_TOP + 1, 8, TORSO_BOT - 1, p['accent_lo'])
    elif facing == 'side':
        rect(9, TORSO_TOP + 1, 9, TORSO_BOT - 1, p['accent'])

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

    if facing == 'side':
        rect(4, 1, 7, 8, p['hair'])                             # back of the skull
        px(12, EYE, INK)                                        # nose, past the face line
    elif facing == 'back':
        rect(4, 1, 11, 8, p['hair'])

    HAIR[p['hair_style']](px, p, facing)
    if p['wear']:
        WEAR[p['wear']](px, p, facing)
    if facing != 'back':
        EYES[p['eyes']](px, p, facing)
        if p['face']:
            FACE[p['face']](px, p, facing)
        if p['mouth_w']:
            if facing == 'side':
                px(10, MOUTH, p['mouth']); px(11, MOUTH, p['mouth'])
            else:
                rect(8 - p['mouth_w'] // 2, MOUTH,
                     7 + (p['mouth_w'] + 1) // 2, MOUTH, p['mouth'])

    # --- contact shadow, only under the foot that is actually down ----------
    for x0, x1 in planted:
        for x in range(x0, x1 + 1):
            if (ox + x, oy + SHADOW_ROW) not in c.d:
                px(x, SHADOW_ROW, P['shadow'])


# =====================================================================
# Parts. A character is a palette plus a choice from each of these lists,
# which is what makes a 26-person roster affordable: adding someone is a row
# in CAST, not a drawing.
#
# Every part works inside the head interior, x4..11 by y1..y8:
#   y1..y3  hair      y4  brow line      y5..y7  eye band      y8  mouth
# =====================================================================
GLASS = P['glass']


def tint(c, k):
    return tuple(min(255, max(0, round(v * k))) for v in c)


# --- hair -------------------------------------------------------------
def _cap(px, p, rows, hi_rows=(1,)):
    for y in rows:
        for x in range(4, 12):
            px(x, y, p['hair'])
    for y in hi_rows:                            # a short sheen on the lit side,
        for x in range(5, 8):                    # not a band across the crown
            px(x, y, p['hair_hi'])


def h_short(px, p, f):
    if f == 'side':
        _cap(px, p, (1, 2, 3))
        px(10, 3, p['hair']); px(11, 3, p['hair'])
    else:
        _cap(px, p, (1, 2, 3))
        px(4, 4, p['hair']); px(11, 4, p['hair'])


def h_buzz(px, p, f):
    _cap(px, p, (1, 2), hi_rows=())
    for x in range(4, 12, 2):
        px(x, 3, p['hair'])


def h_bowl(px, p, f):
    _cap(px, p, (1, 2, 3))
    px(4, 4, p['hair']); px(11, 4, p['hair'])
    if f == 'front':
        px(5, 3, p['skin']); px(6, 3, p['skin'])


def h_bob(px, p, f):
    # In profile the length hangs behind the skull, never over the cheek: x11
    # is the front of the face there, not a side lock.
    _cap(px, p, (1, 2, 3))
    if f == 'side':
        for y in (4, 5, 6, 7):
            px(3, y, p['hair']); px(4, y, p['hair'])
        return
    for y in (4, 5, 6, 7):
        px(4, y, p['hair']); px(11, y, p['hair'])
    if f == 'back':
        for y in (4, 5, 6, 7):
            for x in range(4, 12):
                px(x, y, p['hair'])


def h_long(px, p, f):
    h_bob(px, p, f)
    if f == 'side':
        for y in range(4, 10):
            px(2, y, p['hair']); px(3, y, p['hair'])
        return
    for y in range(4, 9):
        px(3, y, p['hair']); px(12, y, p['hair'])
    if f == 'back':
        for y in range(8, 12):
            for x in range(5, 11):
                px(x, y, p['hair'])


def h_ponytail(px, p, f):
    _cap(px, p, (1, 2))
    for x in range(4, 9):
        px(x, 3, p['hair'])
    px(4, 4, p['hair']); px(11, 3, p['hair'])
    if f == 'front':
        for y in (3, 4, 5, 6):
            px(12, y, p['hair'])
        px(13, 4, INK); px(13, 5, INK)
    elif f == 'side':
        for y in (3, 4, 5, 6):
            px(3, y, p['hair'])
        px(2, 4, INK); px(2, 5, INK)
    else:
        for x in range(6, 10):
            px(x, 9, p['hair'])
        px(7, 10, p['hair']); px(8, 10, p['hair'])
        px(7, 11, p['hair_hi']); px(8, 11, p['hair'])


def h_bun(px, p, f):
    _cap(px, p, (1, 2, 3))
    px(4, 4, p['hair']); px(11, 4, p['hair'])
    for x in range(6, 10):                       # the knot, riding the crown
        px(x, 0, p['hair'])
    px(7, 0, p['hair_hi'])
    if f == 'back':
        for x in range(5, 11):
            px(x, 1, p['hair_hi'])


def h_spiky(px, p, f):
    _cap(px, p, (1, 2, 3))
    for x in range(4, 12, 2):
        px(x, 0, p['hair'])
    px(4, 4, p['hair']); px(11, 4, p['hair'])


def h_pomp(px, p, f):
    _cap(px, p, (1, 2, 3))
    for x in range(4, 8):                        # the quiff, swept up front
        px(x, 0, p['hair'])
    px(5, 0, p['hair_hi'])
    px(4, 4, p['hair']); px(11, 4, p['hair'])


def h_horseshoe(px, p, f):
    for x in (4, 5, 10, 11):
        for y in (1, 2, 3):
            px(x, y, p['hair'])
    for x in range(6, 10):
        px(x, 1, p['skin_lo']); px(x, 2, p['skin_lo'])
        px(x, 3, p['skin'] if f != 'back' else p['skin_lo'])
    px(4, 1, p['hair_hi']); px(5, 1, p['hair_hi'])


HAIR = {'short': h_short, 'buzz': h_buzz, 'bowl': h_bowl, 'bob': h_bob,
        'long': h_long, 'ponytail': h_ponytail, 'bun': h_bun, 'spiky': h_spiky,
        'pomp': h_pomp, 'horseshoe': h_horseshoe}


# --- headwear, drawn over the hair -------------------------------------
def w_hardhat(px, p, f):
    for x in range(5, 11):
        px(x, 0, INK)
    for y in (1, 2):
        for x in range(4, 12):
            px(x, y, p['hat'])
    for x in range(5, 11):
        px(x, 1, tint(p['hat'], 1.18))
    for x in range(2, 14):                       # brim, wider than the head
        px(x, 3, INK)
    for x in range(3, 13):
        px(x, 3, tint(p['hat'], 0.78))
    px(7, 0, p['hat']); px(8, 0, p['hat'])
    px(5, 2, tint(p['hat'], 1.25)); px(6, 2, tint(p['hat'], 1.25))


def w_gradcap(px, p, f):
    for x in range(2, 14):                       # the board
        px(x, 1, INK)
    for x in range(3, 13):
        px(x, 0, INK); px(x, 1, p['hat'])
    for x in range(5, 11):
        px(x, 2, p['hat'])
    px(4, 1, tint(p['hat'], 1.5))
    if f != 'back':
        px(12, 2, P['brass']); px(12, 3, P['brass_hi'])   # tassel


def w_headphones(px, p, f):
    for x in range(5, 11):
        px(x, 0, INK)
    for x in range(6, 10):
        px(x, 0, p['hat'])
    for x, y0 in ((3, 4), (12, 4)):              # earcups
        for y in (y0, y0 + 1, y0 + 2):
            px(x, y, p['hat'])
        px(x, y0, tint(p['hat'], 1.3))
        px(x, y0 + 2, INK)


def w_bandana(px, p, f):
    for y in (1, 2):
        for x in range(4, 12):
            px(x, y, p['hat'])
    for x in range(5, 10):
        px(x, 1, tint(p['hat'], 1.2))
    if f != 'back':
        px(12, 2, p['hat']); px(13, 3, p['hat']); px(12, 3, INK)


def w_hood(px, p, f):
    for y in range(0, 9):
        px(3, y, p['hat']); px(12, y, p['hat'])
    for x in range(3, 13):
        px(x, 0, p['hat'])
    for x in range(4, 12):
        px(x, 1, p['hat'] if f == 'back' else p['hair'])
    px(3, 1, tint(p['hat'], 1.2))


WEAR = {'hardhat': w_hardhat, 'gradcap': w_gradcap, 'headphones': w_headphones,
        'bandana': w_bandana, 'hood': w_hood}


# --- eyes ---------------------------------------------------------------
def e_plain(px, p, f):
    if f == 'side':
        px(10, BROW, p['hair'])
        px(10, EYE, INK); px(11, EYE, INK)
    else:
        for x in (5, 6, 9, 10):
            px(x, BROW, p['hair']); px(x, EYE, INK)


def e_tired(px, p, f):
    e_plain(px, p, f)
    if f != 'side':
        for x in (5, 6, 9, 10):
            px(x, EYE + 1, p['skin_lo'])
    else:
        px(10, EYE + 1, p['skin_lo'])


def e_closed(px, p, f):
    if f == 'side':
        px(10, EYE, INK); px(11, EYE, INK)
    else:
        for x in (5, 6, 9, 10):
            px(x, EYE, INK)


def _side_specs(px, p):
    px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)


def e_round(px, p, f):
    if f == 'side':
        return _side_specs(px, p)
    px(5, BROW, INK); px(10, BROW, INK)
    px(4, EYE, INK); px(5, EYE, GLASS); px(6, EYE, INK)
    px(7, EYE, INK); px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)
    px(5, EYE + 1, INK); px(10, EYE + 1, INK)


def e_square(px, p, f):
    if f == 'side':
        return _side_specs(px, p)
    for x in (4, 5, 6, 9, 10, 11):
        px(x, BROW, INK); px(x, EYE + 1, INK)
    px(4, EYE, INK); px(5, EYE, GLASS); px(6, EYE, INK)
    px(7, EYE, INK); px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)


def e_half_rim(px, p, f):
    if f == 'side':
        return _side_specs(px, p)
    for x in (4, 5, 10, 11):
        px(x, 4, p['hair'])
    for x in (4, 5, 6, 9, 10, 11):
        px(x, BROW, INK)
    px(4, EYE, INK); px(5, EYE, GLASS); px(6, EYE, INK)
    px(7, EYE, INK); px(8, EYE, INK)
    px(9, EYE, INK); px(10, EYE, GLASS); px(11, EYE, INK)


def e_goggles(px, p, f):
    """Pushed up on the brow is what a lab goggle actually looks like on
    someone who is working, and it keeps the eye row free."""
    if f == 'side':
        for x in range(8, 13):
            px(x, 3, INK)
        px(10, 3, P['ener_b'])
        px(10, EYE, INK)
        return
    for x in range(3, 13):
        px(x, 3, INK)
    px(5, 3, P['ener_b']); px(6, 3, P['ener_a'])
    px(9, 3, P['ener_b']); px(10, 3, P['ener_a'])
    for x in (5, 6, 9, 10):
        px(x, EYE, INK)


EYES = {'plain': e_plain, 'tired': e_tired, 'closed': e_closed, 'round': e_round,
        'square': e_square, 'half_rim': e_half_rim, 'goggles': e_goggles}


# --- lower face ----------------------------------------------------------
def f_moustache(px, p, f):
    for x in range(6, 10):
        px(x, EYE + 1, p['hair_hi'])


def f_beard(px, p, f):
    for x in range(6, 10):
        px(x, EYE + 1, p['hair_hi'])
    for x in range(5, 11):
        px(x, MOUTH, p['hair'])
    px(6, MOUTH, p['hair_hi']); px(9, MOUTH, p['hair_hi'])


def f_stubble(px, p, f):
    for x in range(5, 11, 2):
        px(x, MOUTH, p['hair_hi'])


FACE = {'moustache': f_moustache, 'beard': f_beard, 'stubble': f_stubble}


# =====================================================================
# The roster. Each entry is parts plus colour.
#
# The chest accent is the character's own roster colour from the game
# (labolic-playtest-40.html), so a figure on the floor can be matched to its
# row in the UI without reading the name label.
#
# Looks are derived from the illustrated icon each character already has —
# Ben is a pair of round spectacles, Sam a hard hat, Dave headphones, Chen a
# mortarboard, Lee a ghost, Murphy a motorcycle, Jeff a flask boiling over.
# Complexions are spread across three tones for variety and are not inferred
# from anyone's name; they are the easiest thing here to reassign.
# =====================================================================
BROWN, DBROWN, LBROWN = (107, 74, 42), (74, 52, 32), (150, 112, 68)
BLACK, GREY, WHITE = (48, 44, 56), (150, 150, 158), (232, 232, 238)
GOLD, GINGER, RED = (214, 160, 70), (196, 104, 54), (182, 70, 46)
PALE, LILAC, SAND = (222, 218, 228), (186, 166, 214), (198, 168, 118)

COAT = P['coat']
SKINS = {'a': (P['sk_hi'], P['sk']), 'b': (P['sk'], P['sk_lo']),
         'c': (P['sk_md'], P['sk_md_lo']), 'd': (P['sk_dk'], P['sk_dk_lo'])}


def hx(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def cw(hair_style, hair, accent, skin='b', eyes='plain', wear=None, hat=None,
       face=None, coat=None, mouth=2, trouser=(120, 132, 160)):
    sk, sk_lo = SKINS[skin]
    coat = coat or COAT
    acc = hx(accent)
    return dict(
        hair_style=hair_style, wear=wear, eyes=eyes, face=face, mouth_w=mouth,
        hair=hair, hair_hi=tint(hair, 1.28), hat=hat or hair,
        skin=sk, skin_lo=sk_lo, mouth=tint(sk_lo, 0.78),
        coat=coat, coat_hi=tint(coat, 1.07), coat_lo=tint(coat, 0.86),
        accent=acc, accent_lo=tint(acc, 0.74),
        trouser=trouser, trouser_hi=tint(trouser, 1.22), shoe=(104, 82, 60))


HOODIE, TRACK, LEATHER = (112, 126, 96), (206, 122, 70), (52, 62, 90)
PALECOAT, VEST, UNIFORM = (214, 214, 222), (128, 72, 46), (108, 116, 128)
CARDIGAN = (109, 100, 190)

CAST = {
    # --- Tier 1 -------------------------------------------------------
    'tom':    cw('short', LBROWN, '#a89b6e', 'b'),
    'lisa':   cw('bob', LBROWN, '#e8a896', 'a'),
    'ben':    cw('bowl', BROWN, '#7e603c', 'b', eyes='round', mouth=0),
    'anna':   cw('bun', DBROWN, '#c9b88f', 'c', eyes='square'),
    'mike':   cw('short', BLACK, '#a8c4d8', 'c', wear='bandana', hat=(96, 148, 192)),
    'owen':   cw('spiky', DBROWN, '#a8b878', 'b', eyes='tired', coat=HOODIE),
    'pam':    cw('ponytail', BROWN, '#f0c878', 'd'),
    # --- Tier 2 -------------------------------------------------------
    'kate':   cw('bob', GINGER, '#f0997b', 'a'),
    'sam':    cw('short', BROWN, '#3a8da8', 'c', wear='hardhat', hat=(232, 190, 60)),
    'carol':  cw('bun', SAND, '#bf7a99', 'b'),
    'dave':   cw('short', BLACK, '#85b7eb', 'd', wear='headphones', hat=(150, 120, 204)),
    'eve':    cw('long', (58, 60, 92), '#9d8ab8', 'a'),
    'frank':  cw('buzz', GREY, '#6e8590', 'b', coat=UNIFORM),
    'grace':  cw('ponytail', GOLD, '#e8c878', 'a'),
    'hank':   cw('short', GREY, '#5c8a5c', 'b', eyes='square', face='moustache'),
    'iris':   cw('bun', BLACK, '#97c459', 'c', eyes='square'),
    'joe':    cw('short', BROWN, '#d8804a', 'd', coat=TRACK),
    # --- Tier 3 -------------------------------------------------------
    'jeff':   cw('spiky', GINGER, '#d85a30', 'b', eyes='goggles'),
    'murphy': cw('pomp', BLACK, '#185fa5', 'c', face='stubble', coat=LEATHER),
    'chen':   cw('short', BLACK, '#0f6e56', 'c', wear='gradcap', hat=(46, 48, 70)),
    'lee':    cw('long', PALE, '#a8a4b0', 'a', eyes='closed', wear='hood',
                 hat=(208, 208, 218), coat=PALECOAT, mouth=0),
    'watson': cw('short', GREY, '#993c1d', 'b', face='moustache', coat=VEST),
    'bobby':  cw('spiky', RED, '#e8704a', 'b', face='stubble'),
    'ingrid': cw('long', LILAC, '#a89bd1', 'a'),
    'smith':  cw('horseshoe', WHITE, '#534ab7', 'b', eyes='half_rim', face='beard',
                 coat=CARDIGAN, mouth=0, trouser=(96, 90, 124)),
    # --- The player ---------------------------------------------------
    'player': cw('short', DBROWN, '#1d9e75', 'b'),
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
