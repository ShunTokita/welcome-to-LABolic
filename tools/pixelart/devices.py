"""Every lab device, drawn to the projection and grid in spec.py.

Sizes come straight from the game's level-to-footprint table
(labolic-playtest-40.html:3991) at 16 art pixels per tile, and sprites stay
inside their footprint — no upward overhang:

    Lv1 1x1 -> 16x16   Lv3 2x2 -> 32x32   Lv5 4x4 -> 64x64
    Lv2 2x1 -> 32x16   Lv4 3x2 -> 48x32

Backgrounds are transparent. Each sprite gets a one-pixel cast shadow down
and to the right plus a contact band under its feet, both translucent black
so they read on all four floor materials. The cast shadow is what keeps a
cream cabinet off the bright Lv4 floor: their luminances are close and
darkening the cabinet cannot fix that, because the floor's value falls inside
the body ramp and moving the ramp only changes which step collides.

Interior edges are steps in value, not ink. Ink draws silhouettes.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
from pixshapes import box, ramp, drop_shadow, contact_shadow, under
import spec

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
INK = P['ink']

BODY = ramp(P['body_hi'], P['body_hi'], P['body'], P['body_dk'])
METAL = ramp(P['met_hi'], P['met_hi'], P['met'], P['met_lo'])
DARK = ramp(P['met'], P['met'], P['met_lo'], P['ink2'])
BRASS = ramp(P['brass_hi'], P['brass_hi'], P['brass'], P['brass_lo'])
GREEN = ramp(P['grn_hi'], P['grn_hi'], P['grn'], P['grn_lo'])
COPPER = ramp(P['cu_hi'], P['cu_hi'], P['cu'], P['cu_lo'])
# Ochre is the Lv4 house colour, lifted off AGT's brass so the three end-game
# machines read as a family; purple is their shared signature.
OCHRE = ramp(P['och_hi'], P['och_hi'], P['och'], P['och_lo'])

DEV = {}


def device(did, tiles, frames=1):
    """Register a device. `frames` > 1 makes it animated: the function is
    called once per frame with a phase t in [0,1), and the frames are written
    side by side to assets/pixel/anim/<id>.png. The game plays a strip like
    that with background-position and animation: steps(N)."""
    w, h = spec.cell(*tiles)

    def deco(fn):
        DEV[did] = (w, h, fn, frames)
        return fn
    return deco


def erow(cx, rx, ry, cy, y):
    """Half-open x range of an ellipse at row y, or None above/below it. Used
    where a circular thing is seen at an angle: in this projection the top of
    a cylinder is an ellipse as wide as the diameter and a quarter as tall."""
    d = 1.0 - ((y - cy) / ry) ** 2
    if d <= 0:
        return None
    hw = rx * math.sqrt(d)
    return int(round(cx - hw)), int(round(cx + hw))


def tri(t):
    """Triangle wave on [0,1) — a scan that runs out and back."""
    return 2 * t if t < 0.5 else 2 * (1 - t)


def lamp(c, x, y, col):
    c.px(x, y, col)


def knobs(c, x0, x1, y, ramp_=None):
    """A row of controls: turned knobs and lit buttons. A console reads as a
    console because of what is on it, not because it is a box."""
    for x in range(x0, x1 - 1, 4):
        c.rect(x, y, x + 1, y + 1, INK)
        c.px(x, y, P['met_hi']); c.px(x + 1, y + 1, P['met_lo'])
    for i, x in enumerate(range(x0 + 2, x1, 4)):
        c.px(x, y, (P['hot_b'], P['ener_b'], P['cry'])[i % 3])
        c.px(x, y + 1, P['ink2'])


def readout(c, x0, x1, y, dark=None):
    """A control strip: dark ground, a pale bar, and a couple of lamps."""
    c.rect(x0, y, x1, y, dark or P['ink2'])
    c.hline(x0 + 1, x1 - 2, y, P['met'])
    c.px(x0, y, P['hot_b'])
    c.px(x1, y, P['ener_b'])


# =====================================================================
# Lv1 — one tile. Sixteen pixels buys a silhouette and one telling detail.
# =====================================================================
@device('furnace', (1, 1), frames=8)
def furnace(c, t):
    box(c, 1, 2, 14, 14, 2, BODY, INK)
    c.hline(2, 13, 5, P['body_dk'])                 # front/top seam
    c.rect(3, 7, 12, 13, P['body_lo'])              # door, sunk in
    c.hline(3, 12, 7, P['body_dk'])
    c.vline(3, 7, 13, P['body_dk'])
    up = math.sin(2 * math.pi * t)                  # the fire, breathing
    c.stamp(['.ooo.', 'oaabo', 'oabbo', 'obbbo', '.ooo.'],
            {'o': INK, 'a': P['hot_a'] if up > -0.4 else P['hot_b'],
             'b': P['hot_b'] if up > 0.4 else P['hot_c']}, ox=5, oy=8)
    c.px(6 + int(t * 4) % 3, 9, P['white'] if up > 0.6 else P['hot_a'])
    c.rect(8, 1, 11, 3, INK)                        # flue, standing on the top face
    c.rect(9, 2, 10, 3, P['met_lo'])
    c.vline(9, 2, 3, P['met'])
    lamp(c, 11, 8, P['hot_b'] if t < 0.5 else P['hot_a'])


@device('casting', (1, 1), frames=8)
def casting(c, t):
    """A crucible of melt on a tripod over a fire.

    The vessel is a cylinder, so its mouth is an ellipse — as wide as the
    diameter and, at this projection's quarter-depth, about five rows tall.
    Two ellipses do the work: the outer one is the rim of the wall, the inner
    one is the opening, and the melt fills the inner one. That is what makes
    the level readable, and the level is the point of the sprite. The lower
    corners are shaved so the body reads as a cup rather than a can.
    """
    CX, RIM_CY = 7.5, 3.0
    c.line(4, 11, 3, 14, INK); c.line(5, 11, 4, 14, INK)     # tripod
    c.line(11, 11, 12, 14, INK); c.line(10, 11, 11, 14, INK)
    c.rect(3, 14, 12, 14, INK)
    c.hline(4, 11, 14, P['met_lo'])
    up = math.sin(2 * math.pi * t)                           # the fire, breathing
    top = 12 - (1 if up > 0.3 else 0)
    c.rect(6, top, 9, 13, P['hot_c'])
    c.rect(7, top, 8, 13, P['hot_b'])
    c.px(7 + (1 if up > 0 else 0), top, P['hot_a'])

    for y in range(3, 12):                                   # the body
        x0, x1 = (2, 13)
        if y == 10:
            x0, x1 = 3, 12                                   # ...corners shaved
        elif y == 11:
            x0, x1 = 4, 11
        c.rect(x0, y, x1, y, INK)
        if x1 - x0 > 2:
            c.rect(x0 + 1, y, x1 - 1, y, P['body'])
            c.px(x0 + 1, y, P['body_hi']); c.px(x1 - 1, y, P['body_dk'])

    for y in range(0, 7):                                    # the rim, an ellipse
        r = erow(CX, 6.0, 2.6, RIM_CY, y)
        if not r:
            continue
        c.rect(r[0], y, r[1], y, INK)
        if r[1] - r[0] > 2:
            c.rect(r[0] + 1, y, r[1] - 1, y, P['body_hi'])
    for y in range(0, 7):                                    # the melt in the mouth
        r = erow(CX, 5.0, 2.1, RIM_CY, y)
        if not r:
            continue
        near = y > RIM_CY
        c.rect(r[0], y, r[1], y, P['hot_c'] if near else P['hot_a'])
        if not near:
            c.rect(r[0] + 1, y, r[1] - 1, y, P['hot_a'])
    c.px(4 + int(t * 6), 3, P['white'])                      # a highlight, drifting


@device('om', (1, 1), frames=8)
def om(c, t):
    # Four parts have to survive at 16px, and they are what makes a
    # microscope a microscope: a heavy foot, an arm behind, a raked eyepiece,
    # and a stage with something on it.
    box(c, 2, 12, 13, 14, 1, BODY, INK)             # foot
    c.rect(10, 2, 13, 13, INK)                      # arm, standing behind
    c.rect(11, 3, 12, 12, P['body_lo'])
    c.vline(11, 3, 12, P['body_hi'])
    c.line(3, 1, 10, 4, INK)                        # eyepiece, raked forward
    c.line(3, 3, 10, 6, INK)
    c.line(4, 2, 9, 4, P['met'])
    c.line(4, 3, 9, 5, P['met_hi'])
    c.rect(2, 1, 3, 3, INK)
    c.px(3, 2, P['dglass'])
    c.rect(7, 5, 11, 7, INK)                        # body tube
    c.rect(8, 6, 10, 6, P['met'])
    c.rect(7, 7, 10, 9, INK)                        # nosepiece
    c.rect(8, 8, 9, 8, P['met_lo'])
    c.px(8, 9, P['met_hi'])
    c.rect(2, 10, 11, 11, INK)                      # stage
    c.hline(3, 10, 10, P['body_hi'])
    c.hline(3, 10, 11, P['body_dk'])
    lit = math.sin(2 * math.pi * t) > 0
    c.px(6, 10, P['ener_a'] if lit else P['ener_b'])
    c.px(7, 10, P['ener_b'] if lit else P['ener_a'])
    lamp(c, 4, 13, P['hot_b'] if lit else P['hot_c'])


@device('pc', (1, 1), frames=8)
def pc(c, t):
    c.rect(3, 3, 12, 11, INK)                       # screen
    c.rect(4, 4, 11, 10, P['dglass'])
    c.rect(5, 5, 10, 9, P['ener_c'])
    c.stamp(['.o.', 'ooo', 'oao'], {'o': P['ener_a'], 'a': P['ener_b']}, ox=7, oy=6)
    c.hline(5, 10, 9, P['ener_c'])                  # a job, running
    c.hline(5, 5 + int(t * 6), 9, P['ener_a'])
    c.rect(1, 11, 14, 14, INK)                      # deck, seen from above
    c.rect(2, 12, 13, 13, P['body'])
    c.hline(2, 13, 12, P['body_hi'])
    for x in range(3, 13, 2):
        c.px(x, 13, P['body_dk'])
    lamp(c, 13, 12, P['ener_b'] if t < 0.5 else P['ener_c'])


# =====================================================================
# Lv2 — two tiles wide, one tall. A machine and its console.
# =====================================================================
@device('arc', (2, 1), frames=8)
def arc(c, t):
    box(c, 0, 3, 17, 13, 2, BODY, INK)              # chamber
    c.hline(1, 16, 6, P['body_dk'])
    strike = math.sin(2 * math.pi * t * 2)          # the arc, striking
    c.disc(8, 9, 3, INK)                            # viewport
    c.disc(8, 9, 2, P['ener_c'])
    if strike > -0.2:
        c.disc(8, 9, 1, P['ener_b'])
    if strike > 0.6:
        c.disc(8, 9, 1, P['ener_a']); c.px(8, 8, P['white'])
    else:
        c.px(8, 8, P['ener_a'])
    c.rect(13, 7, 15, 12, P['met_lo'])              # electrode feed
    c.vline(13, 7, 12, P['met'])
    box(c, 22, 5, 31, 13, 2, DARK, INK)             # vacuum pump
    readout(c, 24, 29, 10)
    c.hline(24, 29, 11, P['met_lo'])
    c.rect(17, 7, 23, 10, INK)                      # the line between them
    c.rect(18, 8, 22, 9, P['met_lo'])
    c.hline(18, 22, 8, P['met'])
    c.rect(19, 6, 21, 8, INK)                       # an isolation valve on it
    c.px(20, 7, P['met_hi'])
    c.rect(1, 14, 4, 14, INK); c.rect(13, 14, 16, 14, INK)
    c.rect(24, 14, 29, 14, INK)


@device('rolling', (2, 1), frames=10)
def rolling(c, t):
    box(c, 0, 1, 5, 14, 1, BODY, INK)               # left housing
    box(c, 26, 1, 31, 14, 1, BODY, INK)             # right housing
    # One block split by a single ink line: the nip is a line, and every row
    # not spent on an outline goes into the diameter of the rolls.
    # Rolling leaves marks perpendicular to the roll — circumferential rings,
    # which in this view are vertical lines. Those are rotationally symmetric,
    # so they cannot show the roll turning; they stay put. What turns is a
    # band of light scrolling across the face, and it scrolls the opposite way
    # on the two rolls, because at the nip both surfaces have to drive the
    # stock the same way.
    c.rect(4, 2, 27, 14, INK)
    ROWS = 5
    for i, (y0, y1) in enumerate(((3, 7), (9, 13))):
        c.rect(5, y0, 26, y1, P['met'])
        c.hline(5, 26, y0, P['met_hi'])
        c.hline(5, 26, y1, P['met_lo'])
        for x in range(7, 26, 4):                   # circumferential marks
            c.vline(x, y0, y1, P['met_lo'])
        off = int(t * 10) % ROWS
        band = y1 - off if i == 0 else y0 + off     # up on top, down below
        c.hline(5, 26, band, P['met_hi'])
        for x in range(7, 26, 4):
            c.px(x, band, P['met'])
        c.rect(4, y0 - 1, 6, y1 + 1, INK)           # journals at each end
        c.rect(25, y0 - 1, 27, y1 + 1, INK)
        c.rect(5, y0, 5, y1, P['met_hi'])
        c.rect(26, y0, 26, y1, P['met_lo'])
    c.hline(4, 27, 8, INK)                          # the nip
    lamp(c, 2, 4, P['hot_b'])
    lamp(c, 29, 4, P['ener_b'])
    c.hline(1, 4, 12, P['body_dk']); c.hline(27, 30, 12, P['body_dk'])


@device('sem', (2, 1), frames=8)
def sem(c, t):
    box(c, 1, 4, 12, 13, 2, BODY, INK)              # chamber
    c.rect(4, 0, 9, 5, INK)                         # column
    c.rect(5, 1, 8, 4, P['met'])
    c.vline(5, 1, 4, P['met_hi'])
    c.rect(3, 8, 10, 11, P['dglass'])               # specimen port
    c.frame(3, 8, 10, 11, INK)
    c.px(6, 9, P['ener_b']); c.px(7, 10, P['ener_a'])
    c.rect(10, 1, 11, 6, INK)                       # detector, into the top face
    c.vline(10, 2, 5, P['met'])
    c.px(10, 2, P['met_hi'])
    c.rect(0, 8, 3, 10, INK)                        # detector, into the side
    c.rect(0, 9, 2, 9, P['met'])
    c.px(0, 9, P['met_hi'])
    box(c, 15, 2, 30, 12, 1, DARK, INK)             # monitor
    c.rect(17, 5, 28, 10, P['dglass'])
    for gx, gy in ((19, 6), (22, 7), (25, 6), (20, 9), (24, 9), (26, 8)):
        c.px(gx, gy, P['met_lo']); c.px(gx + 1, gy, P['met_lo'])
        c.px(gx, gy + 1, P['met_lo'])                # grains, not a paper dart
        c.px(gx, gy, P['met_hi'])
    c.hline(17, 28, 5 + int(t * 6), P['ener_b'])     # the raster, scanning down
    c.rect(20, 13, 25, 14, INK)                     # its stand
    c.rect(2, 14, 5, 14, INK); c.rect(8, 14, 11, 14, INK)


# =====================================================================
# Lv3 — two tiles square. Room for a cabinet and what is inside it.
# =====================================================================
@device('laser', (2, 2), frames=8)
def laser(c, t):
    box(c, 2, 22, 29, 29, 2, BODY, INK)             # vented base
    for y in range(26, 29):
        for x in range(5, 27, 2):
            c.px(x, y, P['body_dk'])
    box(c, 2, 4, 29, 23, 3, BODY, INK)              # cabinet
    c.rect(5, 11, 26, 21, P['dglass'])              # window
    c.frame(5, 11, 26, 21, INK)
    c.rect(11, 19, 20, 20, INK)                     # substrate on the stage
    c.hline(12, 19, 19, P['met_hi'])
    hx = 8 + int(round(tri(t) * 8))                 # the head, scanning
    c.hline(7, 24, 10, P['met_lo'])                 # the gantry it rides on
    c.rect(hx, 10, hx + 5, 15, INK)
    c.rect(hx + 1, 11, hx + 4, 14, P['met'])
    c.hline(hx + 1, hx + 4, 11, P['met_hi'])
    c.vline(hx + 2, 16, 18, P['ener_a'])            # the beam
    c.vline(hx + 3, 16, 18, P['ener_b'])
    c.px(hx + 2, 19, P['ener_a']); c.px(hx + 3, 19, P['ener_a'])
    c.rect(6, 12, 7, 17, P['met_lo'])               # glazing bars
    c.rect(24, 12, 25, 17, P['met_lo'])
    c.rect(9, 0, 22, 5, INK)                        # optics housing on the top face
    c.rect(10, 1, 21, 4, P['body_lo'])
    c.hline(10, 21, 1, P['body_hi'])
    lamp(c, 26, 8, P['hot_b'])


@device('magnet', (2, 2), frames=8)
def magnet(c, t):
    """The coil gives up four pixels of diameter so the field has somewhere to
    be. In the previous version the arcs were drawn behind a coil that filled
    the tile, and an effect nobody can see is not an effect."""
    for i, r in enumerate((15, 12, 9)):             # the field, pulsing outward
        lit = (int(t * 8) % 3) == i
        for k in range(240):
            a = math.pi * (k / 120.0)
            x = int(round(15.5 + r * math.cos(a)))
            y = int(round(12 - r * 0.85 * math.sin(a)))
            under(c, x, y, P['cry_hi'] if lit else P['glow'])
            y2 = int(round(12 + r * 0.5 * math.sin(a)))
            under(c, x, y2, P['cry'] if lit else P['glow'])
    box(c, 4, 22, 27, 29, 2, BODY, INK)             # bed
    readout(c, 7, 15, 27)
    c.rect(11, 10, 20, 21, INK)                     # coil former
    c.rect(12, 11, 19, 20, P['cu'])
    for x in range(12, 20, 2):                      # windings, around a
        c.vline(x, 11, 20, P['cu_hi'])              # horizontal axis
        c.vline(x + 1, 11, 20, P['cu_lo'])
    c.rect(8, 12, 12, 19, INK)                      # end cheeks
    c.rect(9, 13, 11, 18, P['met'])
    c.vline(9, 13, 18, P['met_hi'])
    c.rect(19, 12, 23, 19, INK)
    c.rect(20, 13, 22, 18, P['met_lo'])
    c.rect(4, 14, 9, 17, INK)                       # pole pieces
    c.rect(5, 15, 8, 16, P['met'])
    c.rect(22, 14, 27, 17, INK)
    c.rect(23, 15, 26, 16, P['met_lo'])


@device('tem', (2, 2), frames=8)
def tem(c, t):
    """A slim column with things stuck into it and a viewing window at their
    foot. That silhouette is the whole read.

    Two rules keep it from going ragged. The lens flanges step out only one
    pixel past the column, not three — a bigger step turns the profile into a
    staircase at this size. And the viewing chamber's upper corners are
    tapered, so the column meets it on a slope instead of a shelf.
    """
    box(c, 3, 27, 28, 30, 1, BODY, INK)             # console
    knobs(c, 6, 14, 28)
    knobs(c, 17, 26, 28)

    def band(y0, y1):                               # a lens flange
        c.rect(11, y0, 20, y1, INK)
        c.rect(12, y0 + 1, 19, y1 - 1, P['body'])
        c.vline(12, y0 + 1, y1 - 1, P['body_hi'])
        c.vline(19, y0 + 1, y1 - 1, P['body_dk'])

    def rod(x0, x1, y, left=False):                 # something stuck into it
        c.rect(x0, y, x1, y + 1, INK)
        c.hline(x0 + 1, x1 - 1, y, P['met'])
        kx = x0 + 1 if left else x1 - 1
        c.rect(kx, y - 1, kx + 1, y + 2, INK)
        c.px(kx, y, P['met_hi'])

    c.rect(12, 1, 19, 22, INK)                      # the column, slim all the way
    c.rect(13, 2, 18, 21, P['body'])
    c.vline(13, 2, 21, P['body_hi'])
    c.vline(18, 2, 21, P['body_dk'])

    c.rect(13, 0, 18, 3, INK)                       # gun at the crown
    c.rect(14, 1, 17, 2, P['ener_c'])
    if math.sin(2 * math.pi * t) > -0.2:            # the emitter, flickering
        c.px(15, 1, P['ener_a']); c.px(16, 1, P['ener_a'])

    band(4, 6); rod(20, 26, 5)                      # condenser
    band(9, 12); rod(20, 25, 10); rod(6, 12, 10, left=True)
    band(15, 17); rod(20, 24, 16)

    for i, y in enumerate((19, 20)):                # the chamber, tapered in
        c.rect(9 + 2 - 2 * i, y, 22 - 2 + 2 * i, y, INK)
        c.rect(10 + 2 - 2 * i, y, 21 - 2 + 2 * i, y, P['body'])
    c.rect(7, 21, 24, 27, INK)                      # the viewing chamber
    c.rect(8, 22, 23, 26, P['body'])
    c.hline(8, 23, 22, P['body_hi'])
    c.rect(10, 23, 21, 25, P['dglass'])             # the fluorescent screen
    glow = 0.5 + 0.5 * math.sin(2 * math.pi * t)    # ...glowing under the beam
    c.rect(14, 23, 17, 25, P['ener_c'])
    if glow > 0.35:
        c.rect(15, 23, 16, 25, P['ener_b'])
    if glow > 0.75:
        c.px(15, 24, P['ener_a'])


# =====================================================================
# Lv4 — three tiles by two. The end-game machines get a stage.
# =====================================================================
@device('phase', (3, 2), frames=8)
def phase(c, t):
    box(c, 2, 24, 45, 30, 2, OCHRE, INK)            # plinth
    knobs(c, 5, 18, 27)
    knobs(c, 28, 42, 27)
    for x0, top in ((5, 8), (18, 2), (31, 8)):      # three columns, centre tallest
        w = 12
        c.rect(x0, top, x0 + w, 25, INK)
        c.rect(x0 + 1, top + 1, x0 + w - 1, 24, P['dglass'])
        c.vline(x0 + 1, top + 1, 24, P['och_lo'])
        c.vline(x0 + w - 1, top + 1, 24, P['ink2'])
        c.rect(x0, top, x0 + w, top + 2, INK)       # cap
        c.rect(x0 + 1, top + 1, x0 + w - 1, top + 1, P['och'])
        c.hline(x0 + 1, x0 + w - 1, top + 1, P['och_hi'])
        c.rect(x0, 23, x0 + w, 25, INK)             # collar at the foot
        c.hline(x0 + 1, x0 + w - 1, 24, P['och'])
        # The field. Purple is the Lv4 signature, so it is drawn two pixels
        # wide with a lit core rather than as a hairline.
        span = 21 - top
        for k in range(90):
            u = k / 89.0
            y = int(round(top + 3 + u * span))
            x = int(round(x0 + 6 + 3.4 * math.sin(u * 7.0 + x0 + 2 * math.pi * t)))
            c.px(x, y, P['cry']); c.px(x + 1, y, P['cry_lo'])
            c.px(x, y, P['cry_hi'] if (k // 8) % 3 == 0 else P['cry'])
        c.px(x0 + 6, 23, P['cry_hi'])
    for bx in (17, 30):                             # cross-links
        c.rect(bx, 19, bx + 1, 21, INK)
        c.px(bx, 20, P['och'])


@device('qaa', (3, 2), frames=8)
def qaa(c, t):
    """A beam line leaves a ring along the tangent, so these leave at twelve
    and six o'clock and run straight out to the detector consoles — an earlier
    version had them radiating from the rim like spokes, which is not how a
    beam gets out of a machine. The L-bends filling the corners are cooling,
    not beam: they come off the cabinets, not the ring.
    """
    cx, cy, R, BAND = 23.5, 13, 9, 6
    box(c, 2, 27, 45, 30, 1, OCHRE, INK)                    # bench

    def console(x0, y0, x1, y1):
        box(c, x0, y0, x1, y1, 2, OCHRE, INK)
        c.rect(x0 + 2, y0 + 4, x1 - 2, y1 - 2, P['dglass'])  # the detector
        c.frame(x0 + 2, y0 + 4, x1 - 2, y1 - 2, P['ink2'])
        return (x0 + x1) // 2

    console(35, 1, 46, 10)                                  # upper right
    console(1, 16, 12, 25)                                  # lower left

    def beamline(x0, x1, y, out_right):
        c.rect(x0, y - 1, x1, y + 2, INK)
        c.rect(x0, y, x1, y + 1, P['met_lo'])
        c.hline(x0, x1, y, P['met'])
        n = x1 - x0
        for k in range(0, n, 3):                            # the beam inside it
            u = (k / max(1, n) + (t if out_right else -t)) % 1.0
            c.px(int(round(x0 + u * n)), y, P['cry'])
        u = (t * 1.0) % 1.0
        px_ = x0 + u * n if out_right else x1 - u * n
        c.px(int(round(px_)), y, P['cry_hi'])
        c.px(int(round(px_)) - 1, y, P['cry'])

    beamline(int(cx), 36, cy - R + 1, True)                 # twelve o'clock, out right
    beamline(11, int(cx), cy + R - 1, False)                # six o'clock, out left

    # Cooling, in L-bends off the consoles. Kept in metal with one cool
    # highlight: drawn in full cyan they shouted over the beam lines, which
    # are the thing the machine is about.
    for (vx, vy0, vy1, hx0, hx1, hy) in ((39, 10, 22, 33, 42, 21),
                                         (5, 5, 17, 5, 14, 4)):
        c.rect(vx, vy0, vx + 3, vy1, INK)
        c.rect(vx + 1, vy0 + 1, vx + 2, vy1 - 1, P['met_lo'])
        c.vline(vx + 1, vy0 + 1, vy1 - 1, P['met'])
        c.rect(hx0, hy, hx1, hy + 3, INK)
        c.rect(hx0 + 1, hy + 1, hx1 - 1, hy + 2, P['met_lo'])
        c.hline(hx0 + 1, hx1 - 1, hy + 1, P['met'])
        c.px(hx0 + 2, hy + 2, P['ener_b']); c.px(hx1 - 2, hy + 1, P['ener_b'])

    c.ring(cx, cy, R, BAND, INK)                            # the ring
    c.ring(cx, cy, R - 1, BAND + 1, P['och'])
    c.ring(cx, cy, R - 1, R - 1, P['och_hi'])
    c.disc(cx, cy, BAND - 1, P['dglass'])
    for k in range(8):                                      # bending magnets
        a = math.pi * k / 4
        bx = int(round(cx + math.cos(a) * (R - 1))); by = int(round(cy + math.sin(a) * (R - 1)))
        c.rect(bx - 1, by - 1, bx + 1, by + 1, INK)
        c.px(bx, by, P['och_hi'])
    for k in range(140):                                    # the circulating beam
        a = 2 * math.pi * k / 140
        c.px(int(round(cx + math.cos(a) * 4)), int(round(cy + math.sin(a) * 4)), P['cry'])
    for i in range(2):                                      # ...and a packet on it
        a = 2 * math.pi * (t + 0.5 * i)
        c.px(int(round(cx + math.cos(a) * 4)),
             int(round(cy + math.sin(a) * 4)), P['cry_hi'])


@device('agt', (3, 2), frames=8)
def agt(c, t):
    CX, CY, R, BAND = 23.5, 13, 12, 9
    CRYSTAL = ['..o..', '.oao.', 'oaabo', 'ooooo', 'oabco', '.obo.', '..o..']
    box(c, 11, 24, 36, 30, 1, GREEN, INK)           # base
    for x0 in (1, 38):                              # crystal-topped pylons
        mid = x0 + 4
        box(c, x0, 25, x0 + 8, 30, 1, BRASS, INK)
        box(c, x0 + 2, 13, x0 + 6, 26, 0, GREEN, INK)
        c.vline(mid, 14, 25, P['wood'])
        box(c, x0 + 1, 10, x0 + 7, 13, 1, BRASS, INK)
        # The crystals pulse a half-cycle apart, so the pair reads as
        # alternating rather than as one blinking lamp.
        lit = math.sin(2 * math.pi * (t + (0.5 if x0 else 0.0))) > 0
        c.stamp(CRYSTAL, {'o': INK,
                          'a': P['white'] if lit else P['cry_hi'],
                          'b': P['cry_hi'] if lit else P['cry'],
                          'c': P['cry'] if lit else P['cry_lo']},
                ox=mid - 2, oy=3)
        c.px(mid, 1, P['cry_hi'])
        if lit:
            for dx, dy in ((-3, 5), (3, 5), (0, 0), (-2, 2), (2, 2)):
                under(c, mid + dx, 3 + dy, P['glow'])
    c.ring(CX, CY, R, BAND, INK)                    # wheel
    c.ring(CX, CY, R - 1, BAND + 1, P['grn'])
    c.ring(CX, CY, R - 1, R - 1, P['grn_hi'])
    c.disc(CX, CY, BAND - 1, P['bg2'])
    for k in range(8):                              # spokes, across the band only
        a = math.pi * k / 4 + math.pi / 8
        ux, uy = math.cos(a), math.sin(a)
        for rr in [x * 0.4 for x in range(int(BAND / 0.4) + 1, int(R / 0.4))]:
            for u in (-0.6, 0.6):
                c.px(int(round(CX + ux * rr - uy * u)),
                     int(round(CY + uy * rr + ux * u)), P['brass'])
    for k in range(4):                              # trunnion blocks
        a = math.pi * k / 2
        bx = int(round(CX + math.cos(a) * R)); by = int(round(CY + math.sin(a) * R))
        c.rect(bx - 1, by - 1, bx + 1, by + 1, INK)
        c.px(bx, by, P['brass_hi'])
    ORBITS = ((7.5, 3.0), (3.0, 7.5))
    for rx, ry in ORBITS:                           # two perpendicular orbits
        for step in range(400):
            a = math.pi * step / 200
            c.px(int(round(CX + rx * math.cos(a))),
                 int(round(CY + ry * math.sin(a))), P['cry_lo'])
    for i, (rx, ry) in enumerate(ORBITS):           # electrons running on them
        for half in (0, 1):
            a = 2 * math.pi * (t + 0.5 * half + 0.25 * i)
            ex, ey = CX + rx * math.cos(a), CY + ry * math.sin(a)
            c.px(int(round(ex)), int(round(ey)), P['cry_hi'])
            c.px(int(round(ex)), int(round(ey)) - 1, P['cry'])
    c.stamp(['.o.', 'ogo', '.o.'], {'o': INK, 'g': P['brass_hi']},
            ox=int(CX) - 1, oy=CY - 1)


# =====================================================================
# Lv5 — four tiles square. The one machine the whole lab is built around.
# =====================================================================
@device('mpss', (4, 4), frames=8)
def mpss(c, t):
    box(c, 2, 50, 61, 61, 3, BODY, INK)             # plinth
    knobs(c, 7, 27, 57); knobs(c, 36, 56, 57)
    for x0 in (2, 46):                              # flanking racks, in three tiers
        box(c, x0, 14, x0 + 15, 51, 3, DARK, INK)
        for y in range(20, 27, 3):                  # upper: card slots
            c.hline(x0 + 2, x0 + 13, y, P['met_lo'])
            c.px(x0 + 2, y, P['ener_b']); c.px(x0 + 13, y, P['hot_b'])
        for y in (28, 41):                          # tier dividers
            c.hline(x0 + 1, x0 + 14, y, INK)
            c.hline(x0 + 1, x0 + 14, y + 1, P['met_lo'])
        for i, px_ in enumerate(range(x0 + 3, x0 + 14, 3)):
            # Clear pipes carrying a clear liquid, so they are drawn in whites
            # and read against the dark rack rather than as more metalwork.
            c.rect(px_ - 1, 30, px_ + 1, 39, INK)   # middle: standpipes
            c.vline(px_ - 1, 30, 39, P['liq'])
            c.vline(px_, 30, 39, P['liq_hi'])
            c.vline(px_ + 1, 30, 39, P['glass'])
            for k in range(3):                      # bubbles, rising
                by = 39 - ((k * 3 + i * 2 + int(t * 9)) % 10)
                c.px(px_, by, P['white'])
                c.px(px_ - 1, by, P['glass']); c.px(px_ + 1, by, P['glass'])
        for y in range(44, 50, 3):                  # lower: card slots
            c.hline(x0 + 2, x0 + 13, y, P['met_lo'])
            c.px(x0 + 13, y, P['cry'])
    box(c, 18, 8, 45, 52, 4, BODY, INK)             # the core housing
    c.rect(21, 16, 42, 47, INK)                     # the window into it
    c.rect(22, 17, 41, 46, P['dglass'])
    # Three strands, not one: they braid because each is a third of a period
    # out of phase with the next, so they cross twice down the window.
    STRANDS = ((P['cry'], P['cry_hi'], 0.0), (P['ener_b'], P['ener_a'], 2.094),
               (P['hot_b'], P['hot_a'], 4.189))
    for base, hi, ph in STRANDS:
        for k in range(320):
            u = k / 319.0
            y = int(round(18 + u * 27))
            x = int(round(31.5 + 7.5 * math.sin(u * 8.0 + ph + 2 * math.pi * t)))
            c.px(x, y, base); c.px(x + 1, y, base)
            if (k // 26) % 3 == 0:
                c.px(x, y, hi)
    c.rect(29, 29, 34, 34, INK)                     # the specimen at the centre
    c.rect(30, 30, 33, 33, P['cry_hi'])
    c.px(31, 31, P['white']); c.px(32, 32, P['glow'])
    for x0 in (24, 36):                             # pipework across the crown
        c.rect(x0, 2, x0 + 3, 9, INK)
        c.rect(x0 + 1, 3, x0 + 2, 9, P['met_lo'])
        c.vline(x0 + 1, 3, 9, P['met'])
    c.rect(24, 2, 39, 4, INK)
    c.rect(25, 3, 38, 3, P['met'])
    c.hline(25, 38, 3, P['met_hi'])
    for x0, x1 in ((13, 19), (44, 50)):             # trunking to the side racks
        c.rect(x0, 26, x1, 29, INK)
        c.rect(x0, 27, x1, 28, P['met_lo'])
        c.hline(x0, x1, 27, P['met'])


# =====================================================================
if __name__ == '__main__':
    from PIL import Image
    anim_dir = os.path.join(OUT, 'anim')
    os.makedirs(anim_dir, exist_ok=True)
    animated = []

    def render(fn, w, h, t):
        c = Canvas(w, h)
        fn(c, t)
        drop_shadow(c, P['drop'])
        contact_shadow(c, P['shadow'])
        return c

    for did, (w, h, fn, frames) in DEV.items():
        render(fn, w, h, 0.0).save(os.path.join(OUT, did + '.png'))
        if frames > 1:
            strip = Image.new('RGBA', (w * frames, h))
            for i in range(frames):
                strip.alpha_composite(render(fn, w, h, i / frames).to_image(), (i * w, 0))
            strip.save(os.path.join(anim_dir, did + '.png'))
            animated.append('%s(%d)' % (did, frames))
    print('devices ok:', len(DEV), '| animated:', ' '.join(animated) or 'none')
