"""AGT — 48x32 (Lv4, three lab tiles by two).

Front elevation plus top faces, per tools/pixelart/spec.py. Transparent
background, contact shadow only.

The wheel is a vertical disc, so it has no top face to show — the projection
is carried by the plinths and capitals of the two pylons, which are boxes.

Two things had to be given up from the 96px draft. The rim band is thinner,
because the atom needs the field: at a 13px field the orbits collapse into a
blocky knot, and only past about 17px do they read as orbits again. And the
halo is gone — a hard-edged disc of lilac on the lab floor read as a printing
error, and the game already has an .eq-fx layer for glow.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
from pixshapes import shadow_ellipse

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
c = Canvas(48, 32)
ink = P['ink']
CX, CY, R = 23.5, 13, 12
BAND_IN = 9                      # inner edge of the rim band


def box(x0, y0, x1, y1, top_h, ramp):
    """A box in the house projection: lit top face, mid front, shaded right."""
    c.rect(x0, y0, x1, y1, ink)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + top_h, ramp['top'])
    c.rect(x0 + 1, y0 + top_h + 1, x1 - 1, y1 - 1, ramp['base'])
    c.vline(x0 + 1, y0 + top_h + 1, y1 - 1, ramp['lit'])
    c.vline(x1 - 1, y0 + 1, y1 - 1, ramp['shade'])


BRASS = {'top': P['brass_hi'], 'lit': P['brass'], 'base': P['brass'], 'shade': P['brass_lo']}
GREEN = {'top': P['grn_hi'], 'lit': P['grn_hi'], 'base': P['grn'], 'shade': P['grn_lo']}

CRYSTAL = ['..o..',
           '.oao.',
           'oaabo',
           'ooooo',
           'oabco',
           '.obo.',
           '..o..']

# --- base the wheel stands on ------------------------------------------
box(11, 24, 36, 30, 1, GREEN)

# --- pylons --------------------------------------------------------------
for x0 in (1, 38):
    mid = x0 + 4
    box(x0, 25, x0 + 8, 30, 1, BRASS)                       # plinth
    box(x0 + 2, 13, x0 + 6, 26, 0, GREEN)                   # column
    c.vline(mid, 14, 25, P['wood'])                         # its dark core
    box(x0 + 1, 10, x0 + 7, 13, 1, BRASS)                   # capital
    c.stamp(CRYSTAL, {'o': ink, 'a': P['cry_hi'], 'b': P['cry'], 'c': P['cry_lo']},
            ox=mid - 2, oy=3)
    c.px(mid, 1, P['cry_hi'])                               # a single spark, not a starburst

# --- wheel ---------------------------------------------------------------
c.ring(CX, CY, R, BAND_IN, ink)
c.ring(CX, CY, R - 1, BAND_IN + 1, P['grn'])
c.ring(CX, CY, R - 1, R - 1, P['grn_hi'])                   # lit outer face
c.disc(CX, CY, BAND_IN - 1, P['bg2'])                       # the pale field

for k in range(8):                                          # spokes across the band
    a = math.pi * k / 4 + math.pi / 8
    ux, uy = math.cos(a), math.sin(a)
    for rr in [x * 0.4 for x in range(int(BAND_IN / 0.4) + 1, int(R / 0.4))]:
        for t in (-0.6, 0.6):
            c.px(int(round(CX + ux * rr - uy * t)),
                 int(round(CY + uy * rr + ux * t)), P['brass'])

for k in range(4):                                          # trunnion blocks
    a = math.pi * k / 2
    bx = int(round(CX + math.cos(a) * R))
    by = int(round(CY + math.sin(a) * R))
    c.rect(bx - 1, by - 1, bx + 1, by + 1, ink)
    c.px(bx, by, P['brass_hi'])

# --- the atom, in the field ----------------------------------------------
# Two perpendicular orbits, not three at 60 degrees. Three orbits need a
# field of roughly 24px: below that the flat ends of each ellipse rasterise
# into 7px straight bars that merge into an asterisk. A wide one crossed with
# a tall one keeps every arc curved at this size.
for rx, ry in ((7.5, 3.0), (3.0, 7.5)):
    for step in range(400):
        t = math.pi * step / 200
        c.px(int(round(CX + rx * math.cos(t))),
             int(round(CY + ry * math.sin(t))), P['cry_lo'])
c.stamp(['.o.', 'ogo', '.o.'], {'o': ink, 'g': P['brass_hi']}, ox=int(CX) - 1, oy=CY - 1)

shadow_ellipse(c, 23.5, 31, 22, 0.6, P['shadow2'])

c.save(os.path.join(OUT, 'AGT.png'))
c.save(os.environ['SCRATCH'] + '/agt_x16.png', scale=16)
print('agt 48x32 ok')
