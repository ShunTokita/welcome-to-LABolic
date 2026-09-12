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

DEV = {}


def device(did, tiles):
    w, h = spec.cell(*tiles)

    def deco(fn):
        DEV[did] = (w, h, fn)
        return fn
    return deco


def lamp(c, x, y, col):
    c.px(x, y, col)


def readout(c, x0, x1, y, dark=None):
    """A control strip: dark ground, a pale bar, and a couple of lamps."""
    c.rect(x0, y, x1, y, dark or P['ink2'])
    c.hline(x0 + 1, x1 - 2, y, P['met'])
    c.px(x0, y, P['hot_b'])
    c.px(x1, y, P['ener_b'])


# =====================================================================
# Lv1 — one tile. Sixteen pixels buys a silhouette and one telling detail.
# =====================================================================
@device('furnace', (1, 1))
def furnace(c):
    box(c, 1, 2, 14, 14, 2, BODY, INK)
    c.hline(2, 13, 5, P['body_dk'])                 # front/top seam
    c.rect(3, 7, 12, 13, P['body_lo'])              # door, sunk in
    c.hline(3, 12, 7, P['body_dk'])
    c.vline(3, 7, 13, P['body_dk'])
    c.stamp(['.ooo.', 'oaabo', 'oabbo', 'obbbo', '.ooo.'],
            {'o': INK, 'a': P['hot_a'], 'b': P['hot_b']}, ox=5, oy=8)
    c.rect(6, 0, 9, 3, INK)                         # flue, standing on the top face
    c.rect(7, 1, 8, 3, P['met_lo'])
    c.vline(7, 1, 3, P['met'])
    lamp(c, 11, 8, P['hot_b'])


@device('casting', (1, 1))
def casting(c):
    # A crucible has to taper, but not to a point: taper it to four pixels and
    # the bowl's sides plus the legs draw an X. It stops at six, and the legs
    # drop almost straight from there so the flame sits between them.
    WIDTHS = [(1, 14), (1, 14), (1, 14), (2, 13), (3, 12), (4, 11), (5, 10)]
    c.line(4, 8, 3, 14, INK); c.line(5, 8, 4, 14, INK)       # legs
    c.line(11, 8, 12, 14, INK); c.line(10, 8, 11, 14, INK)
    c.rect(3, 12, 12, 12, INK)                               # brace
    c.hline(4, 11, 12, P['met_lo'])
    for i, y in enumerate(range(9, 12)):                     # flame between the legs
        c.rect(6 + (i > 1), y, 9 - (i > 1), y, P['hot_c'])
    c.px(7, 9, P['hot_a']); c.px(8, 9, P['hot_b']); c.px(7, 10, P['hot_b'])
    for i, (x0, x1) in enumerate(WIDTHS):                    # the bowl
        y = 2 + i
        c.rect(x0, y, x1, y, INK)
        if i and x1 - x0 > 2:
            c.rect(x0 + 1, y, x1 - 1, y, P['body'])
            c.px(x0 + 1, y, P['body_hi']); c.px(x1 - 1, y, P['body_dk'])
    c.rect(1, 1, 14, 2, INK)                                 # rim, and the melt in it
    c.rect(2, 2, 13, 2, P['hot_c'])
    c.rect(3, 2, 12, 2, P['hot_b'])
    c.rect(6, 2, 9, 2, P['hot_a'])


@device('om', (1, 1))
def om(c):
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
    c.px(6, 10, P['ener_b']); c.px(7, 10, P['ener_a'])
    lamp(c, 4, 13, P['hot_b'])


@device('pc', (1, 1))
def pc(c):
    c.rect(3, 3, 12, 11, INK)                       # screen
    c.rect(4, 4, 11, 10, P['dglass'])
    c.rect(5, 5, 10, 9, P['ener_c'])
    c.stamp(['.o.', 'ooo', 'oao'], {'o': P['ener_a'], 'a': P['ener_b']}, ox=7, oy=6)
    c.rect(1, 11, 14, 14, INK)                      # deck, seen from above
    c.rect(2, 12, 13, 13, P['body'])
    c.hline(2, 13, 12, P['body_hi'])
    for x in range(3, 13, 2):
        c.px(x, 13, P['body_dk'])
    lamp(c, 13, 12, P['ener_b'])


# =====================================================================
# Lv2 — two tiles wide, one tall. A machine and its console.
# =====================================================================
@device('arc', (2, 1))
def arc(c):
    box(c, 1, 3, 19, 13, 2, BODY, INK)              # chamber
    c.hline(2, 18, 6, P['body_dk'])
    c.disc(9, 9, 3, INK)                            # viewport
    c.disc(9, 9, 2, P['ener_c'])
    c.px(9, 8, P['ener_a']); c.px(8, 9, P['ener_b'])
    c.rect(15, 7, 17, 12, P['met_lo'])              # electrode feed
    c.vline(15, 7, 12, P['met'])
    box(c, 20, 5, 30, 13, 2, DARK, INK)             # console
    readout(c, 22, 28, 10)
    c.hline(22, 28, 11, P['met_lo'])
    c.rect(2, 14, 5, 14, INK); c.rect(15, 14, 18, 14, INK)
    c.rect(22, 14, 28, 14, INK)


@device('rolling', (2, 1))
def rolling(c):
    box(c, 0, 1, 5, 14, 1, BODY, INK)               # left housing
    box(c, 26, 1, 31, 14, 1, BODY, INK)             # right housing
    # Two rolls, not one slab: each gets its own ink, and the gap between
    # them is where the stock passes.
    for y0 in (3, 10):
        c.rect(5, y0, 26, y0 + 3, INK)
        c.rect(6, y0 + 1, 25, y0 + 2, P['met'])
        c.hline(6, 25, y0 + 1, P['met_hi'])
        c.hline(6, 25, y0 + 2, P['met_lo'])
        c.rect(5, y0, 7, y0 + 3, INK)               # journals at each end
        c.rect(24, y0, 26, y0 + 3, INK)
        c.px(6, y0 + 1, P['met_hi']); c.px(25, y0 + 2, P['met_lo'])
    c.rect(0, 8, 31, 9, INK)                        # the stock being rolled
    c.hline(1, 30, 8, P['body_hi'])
    c.hline(1, 30, 9, P['body_dk'])
    lamp(c, 2, 4, P['hot_b'])
    lamp(c, 29, 4, P['ener_b'])
    c.hline(1, 4, 12, P['body_dk']); c.hline(27, 30, 12, P['body_dk'])


@device('sem', (2, 1))
def sem(c):
    box(c, 1, 4, 12, 13, 2, BODY, INK)              # chamber
    c.rect(4, 0, 9, 5, INK)                         # column
    c.rect(5, 1, 8, 4, P['met'])
    c.vline(5, 1, 4, P['met_hi'])
    c.rect(3, 8, 10, 11, P['dglass'])               # specimen port
    c.frame(3, 8, 10, 11, INK)
    c.px(6, 9, P['ener_b']); c.px(7, 10, P['ener_a'])
    box(c, 15, 2, 30, 12, 1, DARK, INK)             # monitor
    c.rect(17, 5, 28, 10, P['dglass'])
    for gx, gy in ((19, 6), (22, 7), (25, 6), (20, 9), (24, 9), (26, 8)):
        c.px(gx, gy, P['met_lo']); c.px(gx + 1, gy, P['met_lo'])
        c.px(gx, gy + 1, P['met_lo'])                # grains, not a paper dart
        c.px(gx, gy, P['met_hi'])
    c.rect(20, 13, 25, 14, INK)                     # its stand
    c.rect(2, 14, 5, 14, INK); c.rect(8, 14, 11, 14, INK)


# =====================================================================
# Lv3 — two tiles square. Room for a cabinet and what is inside it.
# =====================================================================
@device('laser', (2, 2))
def laser(c):
    box(c, 2, 22, 29, 29, 2, BODY, INK)             # vented base
    for y in range(26, 29):
        for x in range(5, 27, 2):
            c.px(x, y, P['body_dk'])
    box(c, 2, 4, 29, 23, 3, BODY, INK)              # cabinet
    c.rect(5, 11, 26, 21, P['dglass'])              # window
    c.frame(5, 11, 26, 21, INK)
    c.rect(13, 11, 18, 15, INK)                     # laser head
    c.rect(14, 12, 17, 14, P['met'])
    c.hline(14, 17, 12, P['met_hi'])
    c.vline(15, 16, 19, P['ener_a'])                # the beam
    c.vline(16, 16, 19, P['ener_b'])
    c.rect(11, 19, 20, 20, INK)                     # substrate on the stage
    c.hline(12, 19, 19, P['met_hi'])
    c.rect(6, 12, 7, 17, P['met_lo'])               # glazing bars
    c.rect(24, 12, 25, 17, P['met_lo'])
    c.rect(9, 0, 22, 5, INK)                        # optics housing on the top face
    c.rect(10, 1, 21, 4, P['body_lo'])
    c.hline(10, 21, 1, P['body_hi'])
    lamp(c, 26, 8, P['hot_b'])


@device('magnet', (2, 2))
def magnet(c):
    for r in (13, 10):                              # field, as two faint arcs
        for k in range(200):
            a = math.pi * (k / 100.0)
            x = int(round(15.5 + r * math.cos(a)))
            y = int(round(13 - r * 0.55 * math.sin(a)))
            under(c, x, y, P['glow'])
    box(c, 3, 20, 28, 29, 2, BODY, INK)             # bed
    readout(c, 6, 14, 26)
    c.rect(8, 6, 23, 21, INK)                       # coil former
    c.rect(9, 7, 22, 20, P['cu'])
    for y in range(7, 21, 2):                       # windings
        c.hline(9, 22, y, P['cu_hi'])
        c.hline(9, 22, y + 1, P['cu_lo'])
    c.rect(5, 8, 9, 19, INK)                        # end cheeks
    c.rect(6, 9, 8, 18, P['met'])
    c.vline(6, 9, 18, P['met_hi'])
    c.rect(22, 8, 26, 19, INK)
    c.rect(23, 9, 25, 18, P['met_lo'])
    c.rect(0, 12, 5, 15, INK)                       # pole pieces
    c.rect(1, 13, 4, 14, P['met'])
    c.rect(26, 12, 31, 15, INK)
    c.rect(27, 13, 30, 14, P['met_lo'])


@device('tem', (2, 2))
def tem(c):
    box(c, 2, 22, 29, 29, 2, BODY, INK)             # console
    readout(c, 5, 15, 27)
    readout(c, 18, 27, 27)
    c.rect(10, 1, 21, 23, INK)                      # the column
    c.rect(11, 2, 20, 22, P['body'])
    c.vline(11, 2, 22, P['body_hi'])
    c.vline(20, 2, 22, P['body_dk'])
    for y in (4, 8, 12, 16):                        # stacked lens stages
        c.rect(8, y, 23, y + 2, INK)
        c.rect(9, y + 1, 22, y + 1, P['met'])
        c.hline(9, 22, y + 1, P['met_hi'])
    c.rect(12, 0, 19, 3, INK)                       # electron gun
    c.rect(13, 1, 18, 2, P['ener_c'])
    c.px(15, 1, P['ener_a']); c.px(16, 1, P['ener_a'])
    c.rect(13, 18, 18, 21, P['dglass'])             # viewing screen
    c.frame(13, 18, 18, 21, INK)
    c.px(15, 19, P['ener_b']); c.px(16, 20, P['ener_b'])


# =====================================================================
# Lv4 — three tiles by two. The end-game machines get a stage.
# =====================================================================
@device('phase', (3, 2))
def phase(c):
    box(c, 2, 24, 45, 30, 2, BODY, INK)             # plinth
    readout(c, 5, 17, 28)
    readout(c, 30, 42, 28)
    for x0, top in ((5, 8), (18, 2), (31, 8)):      # three columns, centre tallest
        w = 12
        c.rect(x0, top, x0 + w, 25, INK)
        c.rect(x0 + 1, top + 1, x0 + w - 1, 24, P['dglass'])
        c.vline(x0 + 1, top + 1, 24, P['met_lo'])
        c.vline(x0 + w - 1, top + 1, 24, P['ink2'])
        c.rect(x0, top, x0 + w, top + 2, INK)       # cap
        c.rect(x0 + 1, top + 1, x0 + w - 1, top + 1, P['met'])
        c.hline(x0 + 1, x0 + w - 1, top + 1, P['met_hi'])
        for k in range(60):                         # the field inside
            t = k / 59.0
            y = int(round(top + 3 + t * (21 - top)))
            x = int(round(x0 + 6 + 3.2 * math.sin(t * 7.0 + x0)))
            c.px(x, y, P['cry'])
            c.px(x + 1, y, P['cry_lo'])
        c.px(x0 + 6, 23, P['cry_hi'])
    c.rect(17, 20, 18, 21, P['met_lo'])             # cross-links
    c.rect(30, 20, 31, 21, P['met_lo'])


@device('qaa', (3, 2))
def qaa(c):
    box(c, 2, 25, 45, 30, 2, BODY, INK)             # bench
    box(c, 2, 9, 13, 26, 2, DARK, INK)              # left rack
    box(c, 34, 9, 45, 26, 2, DARK, INK)             # right rack
    for y in range(14, 25, 3):
        c.hline(4, 11, y, P['met_lo'])
        c.hline(36, 43, y, P['met_lo'])
        c.px(4, y, P['ener_b']); c.px(43, y, P['hot_b'])
    cx, cy = 23.5, 15
    c.ring(cx, cy, 11, 7, INK)                      # the ring itself
    c.ring(cx, cy, 10, 8, P['met'])
    c.ring(cx, cy, 10, 10, P['met_hi'])
    c.disc(cx, cy, 6, P['dglass'])
    for k in range(8):                              # magnet blocks around it
        a = math.pi * k / 4
        bx = int(round(cx + math.cos(a) * 9))
        by = int(round(cy + math.sin(a) * 9))
        c.rect(bx - 1, by - 1, bx + 1, by + 1, INK)
        c.px(bx, by, P['brass_hi'])
    for k in range(120):                            # the beam, circulating
        a = 2 * math.pi * k / 120
        c.px(int(round(cx + math.cos(a) * 4)),
             int(round(cy + math.sin(a) * 4)), P['cry'])
    c.px(int(cx), cy, P['cry_hi'])
    c.rect(13, 20, 34, 21, P['met_lo'])             # feed lines to the racks
    c.rect(20, 26, 27, 27, INK)
    c.hline(21, 26, 26, P['met'])


@device('agt', (3, 2))
def agt(c):
    CX, CY, R, BAND = 23.5, 13, 12, 9
    CRYSTAL = ['..o..', '.oao.', 'oaabo', 'ooooo', 'oabco', '.obo.', '..o..']
    box(c, 11, 24, 36, 30, 1, GREEN, INK)           # base
    for x0 in (1, 38):                              # crystal-topped pylons
        mid = x0 + 4
        box(c, x0, 25, x0 + 8, 30, 1, BRASS, INK)
        box(c, x0 + 2, 13, x0 + 6, 26, 0, GREEN, INK)
        c.vline(mid, 14, 25, P['wood'])
        box(c, x0 + 1, 10, x0 + 7, 13, 1, BRASS, INK)
        c.stamp(CRYSTAL, {'o': INK, 'a': P['cry_hi'], 'b': P['cry'], 'c': P['cry_lo']},
                ox=mid - 2, oy=3)
        c.px(mid, 1, P['cry_hi'])
    c.ring(CX, CY, R, BAND, INK)                    # wheel
    c.ring(CX, CY, R - 1, BAND + 1, P['grn'])
    c.ring(CX, CY, R - 1, R - 1, P['grn_hi'])
    c.disc(CX, CY, BAND - 1, P['bg2'])
    for k in range(8):                              # spokes, across the band only
        a = math.pi * k / 4 + math.pi / 8
        ux, uy = math.cos(a), math.sin(a)
        for rr in [x * 0.4 for x in range(int(BAND / 0.4) + 1, int(R / 0.4))]:
            for t in (-0.6, 0.6):
                c.px(int(round(CX + ux * rr - uy * t)),
                     int(round(CY + uy * rr + ux * t)), P['brass'])
    for k in range(4):                              # trunnion blocks
        a = math.pi * k / 2
        bx = int(round(CX + math.cos(a) * R)); by = int(round(CY + math.sin(a) * R))
        c.rect(bx - 1, by - 1, bx + 1, by + 1, INK)
        c.px(bx, by, P['brass_hi'])
    for rx, ry in ((7.5, 3.0), (3.0, 7.5)):         # two perpendicular orbits
        for step in range(400):
            t = math.pi * step / 200
            c.px(int(round(CX + rx * math.cos(t))),
                 int(round(CY + ry * math.sin(t))), P['cry_lo'])
    c.stamp(['.o.', 'ogo', '.o.'], {'o': INK, 'g': P['brass_hi']},
            ox=int(CX) - 1, oy=CY - 1)


# =====================================================================
# Lv5 — four tiles square. The one machine the whole lab is built around.
# =====================================================================
@device('mpss', (4, 4))
def mpss(c):
    box(c, 2, 50, 61, 61, 3, BODY, INK)             # plinth
    readout(c, 6, 26, 58)
    readout(c, 36, 56, 58)
    for x0 in (2, 46):                              # flanking racks
        box(c, x0, 14, x0 + 15, 51, 3, DARK, INK)
        for y in range(21, 49, 4):
            c.hline(x0 + 2, x0 + 13, y, P['met_lo'])
            c.hline(x0 + 2, x0 + 13, y + 1, P['ink2'])
            c.px(x0 + 2, y, P['ener_b']); c.px(x0 + 13, y, P['hot_b'])
    box(c, 18, 8, 45, 52, 4, BODY, INK)             # the core housing
    c.rect(21, 16, 42, 47, INK)                     # the window into it
    c.rect(22, 17, 41, 46, P['dglass'])
    for k in range(300):                            # the field, standing in it
        t = k / 299.0
        y = int(round(18 + t * 27))
        x = int(round(31.5 + 7.0 * math.sin(t * 9.0)))
        c.px(x, y, P['cry']); c.px(x + 1, y, P['cry_lo'])
        x2 = int(round(31.5 + 5.0 * math.sin(t * 9.0 + 2.1)))
        c.px(x2, y, P['ener_b'])
    c.rect(29, 29, 34, 34, INK)                     # the specimen at its centre
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
    for did, (w, h, fn) in DEV.items():
        c = Canvas(w, h)
        fn(c)
        drop_shadow(c, P['drop'])
        contact_shadow(c, P['shadow'])
        c.save(os.path.join(OUT, did + '.png'))
        if 'SCRATCH' in os.environ:
            c.save(os.environ['SCRATCH'] + '/dev_%s_x6.png' % did, scale=6)
    print('devices ok:', len(DEV), '/', ' '.join(sorted(DEV)))
