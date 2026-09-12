"""AGT — 96x64 (the painted asset is 1288x868, so 1.5:1 against its 1.484:1).

The most complicated device in the game, and the one that loses the most in
translation: the painting is a spoked wheel glowing between two crystal-topped
pylons, with cable draping to the floor. At 96px the parts that have to
survive are the wheel, the atom inside it, and the two crystals — everything
else is scaffolding for those three reads, so it is drawn flatter and larger
than the painting would suggest.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
from pixshapes import panel, round_rect, shadow_ellipse

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
c = Canvas(96, 64, bg=P['bg2'])
ink = P['ink']
CX, CY, R = 47.5, 26, 20          # wheel centre and outer radius

# A cut gem, not a flame: a flat table at the top, a hard girdle line across
# the middle, and a brass claw setting under it — all three are what keep the
# finial from reading as a candle on a holder.
CRYSTAL = [
    '..ooo..',
    '.oaabo.',
    'oaaabco',
    'oaaabco',
    'ooooooo',
    'oaabbco',
    '.oabco.',
    '..obo..',
    '...o...',
]

NUCLEUS = [
    '..ooo..',
    '.oghgo.',
    'oghhggo',
    'oggghlo',
    '.oggllo',
    '..oglo.',
    '...oo..',
]


# --- halo, under everything -------------------------------------------
c.disc(CX, CY, R + 4, P['glow'])
c.disc(CX, CY, R + 2, P['glow'])


def pylon(x0):
    """One crystal-topped pylon. x0 is its left edge; the shape is its own
    mirror, so the same routine serves both sides."""
    mid = x0 + 8
    panel(c, x0, 48, x0 + 16, 54, P['brass'], ink, r=1)        # plinth
    c.hline(x0 + 2, x0 + 14, 49, P['brass_hi'])
    panel(c, x0 + 4, 30, x0 + 12, 50, P['grn'], ink, r=2)      # column
    c.vline(mid - 3, 32, 48, P['grn_hi'])                      # lit edge
    c.rect(mid - 1, 32, mid + 1, 48, P['wood'])                # inlaid dark core
    c.vline(mid - 1, 32, 48, P['wood_lo'])
    c.vline(mid + 3, 32, 48, P['grn_lo'])                      # shaded edge
    for by in (36, 44):                                        # brass bands
        c.rect(x0 + 3, by, x0 + 13, by + 1, P['brass'])
        c.hline(x0 + 3, x0 + 13, by, P['brass_hi'])
        c.px(x0 + 3, by + 1, ink); c.px(x0 + 13, by + 1, ink)
    panel(c, x0 + 2, 26, x0 + 14, 31, P['brass'], ink, r=1)    # capital
    c.hline(x0 + 4, x0 + 12, 27, P['brass_hi'])

    # crystal finial: a cut shard, lit facet left, shaded facet right
    c.stamp(CRYSTAL, {'o': ink, 'a': P['cry_hi'], 'b': P['cry'], 'c': P['cry_lo']},
            ox=mid - 3, oy=15)
    panel(c, mid - 2, 24, mid + 2, 26, P['brass'], ink, r=0)   # claw setting
    c.px(mid, 25, P['brass_hi'])
    for dx, dy in ((-5, 20), (5, 20), (0, 13), (-4, 15), (4, 15)):
        c.px(mid + dx, dy, P['glow'])                          # sparkle


pylon(6)
pylon(74)

# --- cable draping from each pylon to the plinth ----------------------
for sgn, sx in ((1, 22), (-1, 73)):
    for i in range(12):
        x = sx + sgn * i
        y = 50 + int(3 * math.sin(math.pi * i / 11))
        c.px(x, y, P['wood_lo']); c.px(x, y + 1, P['wood'])

# --- base the wheel stands on -----------------------------------------
panel(c, 30, 50, 65, 55, P['grn_lo'], ink, r=1)
c.hline(32, 63, 51, P['grn'])
panel(c, 36, 44, 59, 51, P['wood'], ink, r=1)                  # timber bolster
for x in range(38, 58, 3):
    c.vline(x, 45, 50, P['wood_lo'])                           # plank seams
panel(c, 42, 38, 53, 50, P['brass'], ink, r=1)                 # king post
c.vline(45, 39, 49, P['brass_hi'])
c.vline(50, 39, 49, P['brass_lo'])

# --- the wheel ---------------------------------------------------------
c.ring(CX, CY, R, R - 5, ink)                                  # rim band, inked solid
c.ring(CX, CY, R - 1, R - 4, P['grn'])
c.ring(CX, CY, R - 1, R - 3, P['grn_hi'])                      # lit outer face
c.ring(CX, CY, R - 3, R - 4, P['grn_lo'])
c.disc(CX, CY, R - 5, ink)
c.disc(CX, CY, R - 6, P['bg2'])                                # the pale field

# Spokes bridge the two rims, as in the painting — the field inside the inner
# rim stays clear so the atom has somewhere to sit.
for k in range(8):
    a = math.pi * k / 4 + math.pi / 8
    ux, uy = math.cos(a), math.sin(a)
    for rr in [x * 0.34 for x in range(int((R - 6) / 0.34), int(R / 0.34))]:
        for t in (-1.5, -0.5, 0.5, 1.5):
            c.px(int(round(CX + ux * rr - uy * t)),
                 int(round(CY + uy * rr + ux * t)), P['brass'])
        c.px(int(round(CX + ux * rr - uy * 1.5)),
             int(round(CY + uy * rr + ux * 1.5)), P['brass_hi'])
        c.px(int(round(CX + ux * rr + uy * 1.5)),
             int(round(CY + uy * rr - ux * 1.5)), P['brass_lo'])

for k in range(4):                                             # trunnion blocks on the rim
    a = math.pi * k / 2
    bx = int(round(CX + math.cos(a) * R))
    by = int(round(CY + math.sin(a) * R))
    panel(c, bx - 2, by - 2, bx + 2, by + 2, P['brass'], ink, r=1)

# --- the atom, floating in the field ----------------------------------
# Three orbits at 60 degrees, each flat enough to stay an orbit. Two orbits
# alone close into a lens that reads as an eye; fatter ones rasterise into a
# box, because a rotated ellipse this small has long straight runs.
for rot in (0.0, math.pi / 3, 2 * math.pi / 3):
    for step in range(360):
        t = math.pi * step / 180
        ex, ey = 11.0 * math.cos(t), 3.4 * math.sin(t)
        c.px(int(round(CX + ex * math.cos(rot) - ey * math.sin(rot))),
             int(round(CY + ex * math.sin(rot) + ey * math.cos(rot))), P['cry_lo'])
c.stamp(NUCLEUS, {'o': ink, 'g': P['brass'], 'h': P['brass_hi'], 'l': P['brass_lo']},
        ox=int(CX) - 3, oy=CY - 3)

# --- ground shadow, last and never outlined ---------------------------
shadow_ellipse(c, 48, 56, 42, 3, P['shadow2'])

c.save(os.path.join(OUT, 'AGT.png'))
c.save(os.environ['SCRATCH'] + '/agt_x8.png', scale=8)
print('agt ok')
