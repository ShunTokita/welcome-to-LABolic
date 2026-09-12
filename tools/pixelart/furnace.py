"""Furnace — 64x64.

The painted asset's read, rebuilt on a 64px grid: a cream enamel cabinet, a
receding body slab behind it on the left, an inset door with a glowing
porthole, a flue on the crown, four stubby feet. Framed tighter than the
painting, because at 64px the painting's generous margin is pixels thrown
away — in game the same reframing is done at runtime by --sprite-zoom.

Draw order matters. Solids are inked as they are placed; the ground shadow
goes down last via `shadow_ellipse`, which fills only empty cells so the
shadow never picks up an outline of its own.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
from pixshapes import panel, round_rect, shadow_ellipse

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
c = Canvas(64, 64, bg=P['bg'])
ink = P['ink']

# --- feet, placed first so the cabinet overlaps their tops ------------
for lx in (21, 30, 39, 47):
    panel(c, lx, 44, lx + 5, 52, P['body_lo'], ink, r=1)
    c.rect(lx + 1, 45, lx + 2, 51, P['body'])
    c.hline(lx + 1, lx + 4, 51, P['body_dk'])
panel(c, 13, 44, 18, 51, P['body_dk'], ink, r=1)        # the rear slab's foot

# --- flue on the crown -------------------------------------------------
panel(c, 34, 4, 42, 13, P['body_lo'], ink, r=1)
for x in (36, 38, 40):                                   # louvre slots
    c.vline(x, 6, 11, P['body_dk'])

# --- receding body slab, behind and to the left ------------------------
panel(c, 11, 15, 22, 48, P['body_dk'], ink, r=3)
c.rect(12, 18, 15, 46, P['body_lo'])                     # its lit left cheek

# --- main cabinet ------------------------------------------------------
panel(c, 19, 11, 53, 48, P['body'], ink, r=3)
c.rect(20, 14, 21, 45, P['body_hi'])                     # light down the left edge
c.hline(22, 50, 12, P['body_hi'])                        # light along the crown
c.rect(50, 14, 52, 45, P['body_lo'])                     # shaded right cheek

# --- inset door --------------------------------------------------------
# The recess is one shade of shadow; the leaf sits a pixel down and right of
# it, so the shadow survives as a hairline along the top and left.
round_rect(c, 24, 17, 47, 42, P['body_lo'], r=3)
panel(c, 25, 18, 48, 43, P['body_hi'], ink, r=3)
for i in range(6):                                       # diagonal corner sheen
    c.px(28 + i, 20, P['white']); c.px(27 + i, 21, P['white'])

for hy in (23, 35):                                      # hinges on the left stile
    panel(c, 23, hy, 27, hy + 5, P['body'], ink, r=0)
    c.px(25, hy + 2, P['body_dk'])
c.rect(45, 29, 47, 33, P['body_lo'])                     # latch on the right stile
c.frame(45, 29, 47, 33, ink)

# --- porthole, with the fire behind it ---------------------------------
c.disc(36, 30, 6, ink)
c.disc(36, 30, 5, P['met_hi'])                           # metal bezel
c.disc(36, 31, 5, P['met'])                              # ...lit from above
c.disc(36, 30, 4, ink)
c.disc(36, 30, 3, P['hot_c'])
c.disc(36, 30, 2, P['hot_b'])
c.px(35, 29, P['hot_a']); c.px(36, 29, P['hot_a']); c.px(35, 30, P['hot_a'])
c.px(35, 29, P['white'])

# --- indicator lamp ----------------------------------------------------
c.disc(45, 16, 2, ink)
c.disc(45, 16, 1, P['hot_b'])
c.px(45, 15, P['hot_a'])

# --- ground shadow, last and never outlined ----------------------------
shadow_ellipse(c, 32, 52, 24, 3, P['shadow'])

c.save(os.path.join(OUT, 'furnace.png'))
c.save(os.environ['SCRATCH'] + '/furnace_x8.png', scale=8)
print('furnace ok')
