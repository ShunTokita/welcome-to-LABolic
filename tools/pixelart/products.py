"""Discovery card art — one 32x32 product per material.

The Discovery popup used to show a gradient mixed from the specimen's element
colours, which told the player nothing they did not already know. These are
the thing the alloy is *for* instead: brass is a trumpet, Inconel is a jet
engine, Nitinol is the spectacle frame somebody bent too far.

Drawn to the same rules as everything else — ink for the silhouette, value
steps inside it, light from the upper left — but with one difference: these
are read at 64px in a popup, not at 48px on a floor, so they can carry a
little more detail than a device of the same pixel size.

The fantasy alloys have no real product, so they get the image their flavour
text implies: the balance nobody could weigh AETHERITE on, the magnet that
would not come off the machine, the hourglass CHRONOS made late.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel', 'product')
os.makedirs(OUT, exist_ok=True)
INK = P['ink']
S = 32
ART = {}


def product(did):
    def deco(fn):
        ART[did] = fn
        return fn
    return deco


def bar(c, x0, y0, x1, y1, hi, mid, lo):
    """A lit slab: ink edge, highlight along the top-left, shade bottom-right."""
    c.rect(x0, y0, x1, y1, INK)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, mid)
    c.hline(x0 + 1, x1 - 1, y0 + 1, hi)
    c.vline(x0 + 1, y0 + 1, y1 - 1, hi)
    c.hline(x0 + 1, x1 - 1, y1 - 1, lo)
    c.vline(x1 - 1, y0 + 1, y1 - 1, lo)


def sparkle(c, x, y):
    c.px(x, y, P['white'])
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        c.px(x + dx, y + dy, P['sil_hi'])


# =====================================================================
# Real alloys
# =====================================================================
@product('brass')
def brass(c):
    c.disc(25, 17, 7, INK)
    c.disc(25, 17, 6, P['brass'])
    c.disc(26, 18, 5, P['brass_lo'])
    c.disc(24, 16, 4, P['brass_hi'])
    c.rect(6, 15, 24, 19, INK)                           # lead pipe
    c.rect(7, 16, 23, 18, P['brass'])
    c.hline(7, 23, 16, P['brass_hi'])
    c.hline(7, 23, 18, P['brass_lo'])
    for vx in (11, 15, 19):                              # valves
        c.rect(vx, 8, vx + 3, 17, INK)
        c.rect(vx + 1, 9, vx + 2, 16, P['brass'])
        c.vline(vx + 1, 9, 16, P['brass_hi'])
        c.rect(vx, 6, vx + 3, 8, INK)
        c.px(vx + 1, 7, P['brass_hi'])
    c.rect(2, 14, 7, 20, INK)                            # mouthpiece
    c.rect(3, 15, 6, 19, P['brass_lo'])
    c.px(3, 15, P['brass_hi'])
    c.rect(9, 20, 21, 24, INK)                           # tuning slide
    c.rect(10, 21, 20, 23, P['brass_lo'])
    sparkle(c, 22, 13)


@product('cupronickel')
def cupronickel(c):
    c.disc(15.5, 16, 13, INK)
    c.disc(15.5, 16, 12, P['sil_lo'])
    c.disc(15.5, 16, 11, P['sil'])
    c.disc(14, 14, 8, P['sil_hi'])
    c.disc(15.5, 16, 9, P['sil'])
    c.disc(14.5, 15, 7, P['sil_hi'])
    c.stamp(['ooo.ooo.ooo',                              # 100
             'o.o.o.o.o.o',
             'o.o.o.o.o.o',
             'o.o.o.o.o.o',
             'ooo.ooo.ooo'], {'o': P['sil_lo']}, ox=10, oy=14)
    c.px(11, 9, P['white']); c.px(12, 9, P['white'])
    sparkle(c, 22, 9)


@product('monel')
def monel(c):
    # Corrosion resistance reads as a contrast: the plate stays mirror-bright
    # while the water on it is filthy. A hard horizontal split does the work —
    # chrome reflects the sky above the horizon and the ground below it, so a
    # gradient reads as paint and a step reads as polish.
    c.rect(2, 6, 29, 27, INK)
    c.rect(3, 7, 28, 16, P['sil_hi'])                    # sky half
    c.rect(3, 17, 28, 26, P['sil_lo'])                   # ground half
    c.hline(3, 28, 16, P['white'])
    c.hline(3, 28, 17, P['met_lo'])
    c.hline(3, 28, 26, P['met_lo'])
    for i in range(11):                                  # the sweep of a polish
        c.vline(6 + i, 7, 26, P['white'] if i < 2 else P['sil'])
        if i >= 2:
            break
    for i in range(20):
        x = 5 + i
        if 3 <= x <= 28:
            c.px(x, 7 + i, P['white'])
            c.px(x + 1, 7 + i, P['sil_hi'])
    for (dx, dy, r) in ((10, 12, 4), (21, 10, 3), (24, 20, 3), (14, 22, 2)):
        c.disc(dx, dy, r, INK)                           # dirty water, beading
        c.disc(dx, dy, r - 1, P['grime'])
        c.disc(dx - 1, dy - 1, max(1, r - 2), P['grime_lo'])
        c.px(dx - 1, dy - 2, P['sil_hi'])                # each one still domed
        c.px(dx + 1, dy + r - 2, P['ink2'])
    c.px(24, 27, P['grime']); c.px(24, 28, P['grime'])   # and one running off
    c.px(25, 29, P['grime_lo']); c.px(24, 30, P['grime_lo'])


@product('invar')
def invar(c):
    # Four things at 32px is one too many, so they are ranked: the bar spans
    # the whole width and everything else hangs off it. Fire at one end, ice
    # at the other, and the thermometer in front reading the same either way —
    # that last part is the alloy's entire point.
    c.rect(1, 13, 30, 20, INK)                           # the bar, full width
    c.rect(2, 14, 29, 19, P['sil'])
    c.hline(2, 29, 14, P['sil_hi'])
    c.hline(3, 29, 15, P['white'])
    c.hline(2, 29, 19, P['sil_lo'])
    for i in range(6):                                   # flame licking the left
        c.vline(2 + i, 21 + abs(i - 2), 27, P['hot_c'])
    for i in range(4):
        c.vline(3 + i, 22 + abs(i - 1), 26, P['hot_b'])
    c.vline(4, 24, 26, P['hot_a']); c.px(5, 25, P['hot_a'])
    c.px(2, 20, P['hot_b']); c.px(7, 22, P['hot_c'])
    c.stamp(['..o..', '.oao.', 'oaabo', '.oao.', '..o..'],   # ice, upper right
            {'o': INK, 'a': P['ice_hi'], 'b': P['ice']}, ox=23, oy=5)
    c.stamp(['..o..', '.oao.', 'oaabo', '.oao.', '..o..'],
            {'o': INK, 'a': P['ice_hi'], 'b': P['ice']}, ox=26, oy=22)
    c.px(23, 12, P['ice']); c.px(29, 21, P['ice'])
    c.rect(13, 2, 18, 24, INK)                           # thermometer, in front
    c.rect(14, 3, 17, 23, P['bg2'])
    c.vline(14, 3, 23, P['white'])
    c.rect(15, 6, 16, 22, P['red_lo'])
    c.rect(15, 12, 16, 22, P['red'])
    c.px(15, 12, P['red_hi'])
    c.disc(15.5, 25, 3, INK)
    c.disc(15.5, 25, 2, P['red'])
    c.px(14, 24, P['red_hi'])
    for y in (7, 9, 11, 15, 17, 19):                     # its scale
        c.px(17, y, P['ink2'])


@product('permalloy')
def permalloy(c):
    c.rect(3, 5, 28, 27, INK)                            # E-I laminated core
    c.rect(4, 6, 27, 26, P['met_lo'])
    for y in range(7, 26, 2):
        c.hline(5, 26, y, P['met'])
    c.rect(8, 10, 13, 22, P['bg2'])                      # windows
    c.rect(18, 10, 23, 22, P['bg2'])
    c.frame(8, 10, 13, 22, INK); c.frame(18, 10, 23, 22, INK)
    c.rect(13, 8, 18, 24, INK)                           # centre limb, wound
    for y in range(9, 24, 2):
        c.hline(13, 18, y, P['cu_hi'])
        c.hline(13, 18, y + 1, P['cu_lo'])
    c.rect(10, 2, 12, 6, INK); c.px(11, 3, P['cu'])      # leads
    c.rect(19, 2, 21, 6, INK); c.px(20, 3, P['cu'])


@product('nichrome')
def nichrome(c):
    bar(c, 3, 10, 28, 27, P['sil_hi'], P['sil'], P['sil_lo'])   # the body
    for sx in (7, 17):                                          # two slots
        c.rect(sx, 8, sx + 8, 14, INK)
        c.rect(sx + 1, 9, sx + 7, 13, P['ink2'])
        for y in (10, 12):                                      # the elements
            c.hline(sx + 1, sx + 7, y, P['hot_c'])
        c.hline(sx + 2, sx + 6, 11, P['hot_b'])
    c.rect(2, 14, 5, 17, INK)                                   # lever
    c.rect(3, 15, 4, 16, P['met'])
    c.rect(24, 18, 27, 21, INK)                                 # dial
    c.disc(25.5, 19.5, 1, P['met_hi'])
    for fx in (5, 25):                                          # feet
        c.rect(fx, 27, fx + 3, 29, INK)
    c.hline(6, 25, 22, P['sil_lo'])


@product('ferritic_ss')
def ferritic_ss(c):
    # A rim ellipse sitting on a flat slab is a flying saucer. A washbasin is
    # a rim ellipse on a *body* — the bowl has to be as tall as it is wide,
    # tapering down to the waste, with the trap hanging visibly below it.
    c.rect(14, 0, 18, 7, INK)                            # tap riser
    c.rect(15, 1, 17, 6, P['sil'])
    c.vline(15, 1, 6, P['sil_hi'])
    c.rect(8, 0, 17, 3, INK)                             # gooseneck
    c.rect(9, 1, 16, 2, P['sil'])
    c.hline(9, 16, 1, P['sil_hi'])
    c.rect(7, 1, 11, 6, INK)                             # spout
    c.rect(8, 2, 10, 5, P['sil_lo'])
    c.px(8, 2, P['sil'])
    for y in range(7, 12):                               # water falling in
        c.px(9, y, P['ice_hi'] if y % 2 else P['ice'])
    for i in range(9):                                   # bowl, front face
        y = 12 + i
        x0 = 3 + (i * 6) // 9
        x1 = 28 - (i * 6) // 9
        c.rect(x0, y, x1, y, INK)
        c.rect(x0 + 1, y, x1 - 1, y, P['sil_lo'] if i > 4 else P['sil'])
        c.px(x0 + 1, y, P['sil_hi'])
        c.px(x1 - 1, y, P['met_lo'])
    c.ellipse(15.5, 11, 13, 4, INK)                      # the rim
    c.ellipse(15.5, 11, 12, 3, P['sil'])
    c.hline(4, 27, 9, P['sil_hi'])
    c.ellipse(15.5, 12, 11, 3, P['ink2'])                # down into the bowl
    c.ellipse(15.5, 12, 6, 2, P['met_lo'])
    c.px(15, 12, P['ink2']); c.px(16, 12, P['ink2'])     # the waste
    c.rect(13, 21, 18, 24, INK)                          # tailpiece
    c.rect(14, 22, 17, 24, P['sil_lo'])
    c.vline(14, 22, 24, P['sil'])
    c.rect(11, 23, 20, 28, INK)                          # the trap's bend
    c.rect(12, 24, 19, 27, P['sil'])
    c.hline(12, 19, 24, P['sil_hi'])
    c.rect(14, 24, 17, 26, P['ink2'])
    c.rect(19, 23, 31, 27, INK)                          # and the run to waste
    c.rect(20, 24, 30, 26, P['sil_lo'])
    c.hline(20, 30, 24, P['sil'])
    c.vline(26, 24, 26, P['met_lo'])                     # a joint in it


@product('austenitic_ss')
def austenitic_ss(c):
    # Two implements crossed. The scalpel failed the first time because a
    # 1px line is a pin: it needs a fluted handle wide enough to hold and a
    # blade wide enough to see the edge on.
    c.line(3, 27, 17, 13, INK); c.line(4, 28, 18, 14, INK)   # spoon handle
    c.line(3, 28, 17, 14, P['sil_lo'])
    c.line(4, 27, 18, 13, P['sil'])
    c.ellipse(21, 9, 6, 4, INK)                              # its bowl, tilted
    c.ellipse(21, 9, 5, 3, P['sil'])
    c.ellipse(20, 8, 3, 2, P['sil_hi'])
    c.px(19, 7, P['white'])
    for i in range(13):                                      # scalpel handle
        x, y = 6 + i, 6 + i
        c.rect(x - 1, y, x + 1, y + 1, INK)
        c.px(x, y, P['sil'])
        c.px(x, y + 1, P['sil_lo'] if i % 2 else P['met_lo'])
    c.rect(4, 4, 9, 9, INK)                                  # its butt end
    c.rect(5, 5, 8, 8, P['sil_lo'])
    c.px(5, 5, P['sil_hi'])
    for i in range(8):                                       # the blade, belly
        c.hline(19 + i, 23 + i - i // 3, 19 + i, INK)
    c.rect(20, 20, 24, 24, INK)
    c.line(20, 20, 24, 24, P['sil_hi'])
    c.line(21, 20, 25, 24, P['sil'])
    c.px(22, 20, P['white'])
    c.px(26, 26, INK); c.px(25, 25, P['sil_hi'])             # the point
    sparkle(c, 27, 5)


@product('ti_cr_beta')
def ti_cr_beta(c):
    # The head belongs off to one side with a long stem under it; a short
    # stem under a big ball is a lollipop, and a stem that tapers hard is a
    # hammer, so this one runs nearly parallel most of the way down.
    c.disc(8, 7, 5, INK)                                  # femoral head
    c.disc(8, 7, 4, P['sil'])
    c.disc(7, 6, 2, P['sil_hi'])
    c.px(6, 5, P['white'])
    for i in range(6):                                    # neck, down and right
        x, y = 11 + i, 9 + i
        c.rect(x - 1, y, x + 2, y + 1, INK)
        c.rect(x, y, x + 1, y, P['sil_lo'])
        c.px(x, y, P['sil'])
    c.rect(14, 13, 23, 18, INK)                           # the shoulder
    c.rect(15, 14, 22, 17, P['sil_lo'])
    c.hline(15, 22, 14, P['sil'])
    c.px(15, 14, P['sil_hi'])
    for i in range(13):                                   # the stem
        y = 18 + i
        x0 = 16 + i // 6
        x1 = 22 - (i * 2) // 5
        c.rect(x0, y, x1, y, INK)
        if x1 - x0 >= 2:
            c.rect(x0 + 1, y, x1 - 1, y, P['sil_lo'])
            c.px(x0 + 1, y, P['sil'])
    for y in range(15, 26, 2):                            # porous coating
        c.px(17 + (y % 3), y, P['met_lo'])
        c.px(20 - (y % 2), y + 1, P['met_lo'])
    sparkle(c, 27, 8)


@product('nitinol')
def nitinol(c):
    # Spectacles, not goggles: the rim has to be thin against the lens, and
    # both temples have to be visible or there is nothing to bend. The right
    # one is folded back on itself — pull it that far and any other frame
    # stays that way.
    for ex in (10, 22):
        c.ring(ex, 15, 6, 4, INK)                         # a 2px rim
        c.disc(ex, 15, 4, P['glass'])
        c.disc(ex - 1, 13, 2, P['white'])
        c.px(ex + 2, 17, P['sil_hi'])
    c.hline(15, 17, 12, INK)                              # bridge, over the nose
    c.hline(15, 17, 14, INK)
    c.px(16, 13, P['sil_hi'])
    c.px(15, 13, P['bg2']); c.px(17, 13, P['bg2'])
    c.hline(3, 5, 11, INK)                                # left temple, straight
    c.hline(3, 4, 12, INK)
    c.line(5, 12, 4, 11, INK)
    c.px(4, 11, P['sil_hi'])
    c.px(2, 11, INK); c.px(2, 12, INK)                    # its ear hook
    c.px(1, 12, INK); c.px(1, 13, INK)
    c.line(27, 12, 30, 8, INK)                            # right temple, bent
    c.line(28, 13, 31, 9, INK)
    c.line(30, 8, 27, 4, INK)                             # folded right back
    c.line(31, 9, 28, 5, INK)
    c.px(29, 7, P['sil_hi'])
    c.px(26, 4, INK); c.px(25, 4, INK)
    c.px(24, 3, P['sil_lo'])
    sparkle(c, 21, 25)


@product('inconel_like')
def inconel_like(c):
    c.disc(15.5, 15, 13, INK)                             # nacelle
    c.disc(15.5, 15, 12, P['sil_lo'])
    c.disc(15.5, 15, 11, P['sil'])
    c.disc(13, 12, 8, P['sil_hi'])
    c.disc(15.5, 15, 10, P['ink2'])                       # intake
    for k in range(12):                                   # fan blades
        a = 2 * math.pi * k / 12
        for r in range(3, 10):
            c.px(int(round(15.5 + math.cos(a) * r - math.sin(a) * (r * 0.16))),
                 int(round(15 + math.sin(a) * r + math.cos(a) * (r * 0.16))),
                 P['sil'] if k % 2 else P['sil_lo'])
    c.disc(15.5, 15, 3, INK)                              # spinner
    c.disc(15.5, 15, 2, P['sil_hi'])
    c.px(15, 14, P['white'])
    c.rect(2, 24, 29, 28, INK)                            # pylon and cowl lip
    c.rect(3, 25, 28, 27, P['sil_lo'])
    c.hline(3, 28, 25, P['sil'])


# =====================================================================
# Fantasy alloys — the flavour text made literal
# =====================================================================
@product('aetherite_a')
def aetherite_a(c):
    for r in (11, 8, 5):                                  # it will not sit still
        for k in range(160):
            a = 2 * math.pi * k / 160
            c.px(int(round(15.5 + r * math.cos(a))),
                 int(round(24 + r * 0.35 * math.sin(a))), P['glow'])
    c.rect(14, 12, 17, 22, INK)                           # the column, floating
    c.rect(15, 13, 16, 21, P['brass'])
    c.rect(4, 8, 27, 10, INK)                             # the beam, tipped up
    c.rect(5, 9, 26, 9, P['brass_hi'])
    c.px(15, 11, P['brass_hi']); c.px(16, 11, P['brass_hi'])
    for px_ in (3, 26):                                   # the pans
        c.rect(px_, 12, px_ + 3, 15, INK)
        c.rect(px_ + 1, 13, px_ + 2, 14, P['brass_lo'])
        c.vline(px_ + 1, 10, 12, P['met_lo'])
        c.vline(px_ + 2, 10, 12, P['met_lo'])
    c.rect(11, 24, 20, 27, P['glow'])
    sparkle(c, 21, 6)


@product('nullsteel_b')
def nullsteel_b(c):
    # Flat enough to be a plate. A domed top with a bright crown made it a
    # flying saucer, so the disc is a constant-thickness slab now: top face,
    # one dark edge under it, nothing in between.
    c.rect(1, 25, 30, 30, INK)                            # magnet track
    c.rect(2, 26, 29, 29, P['ink2'])
    for x in range(3, 29, 5):
        c.rect(x, 26, x + 2, 29, P['cry_lo'])
        c.hline(x, x + 2, 26, P['cry'])
    for k in range(160):                                  # the field it expels
        a = math.pi * k / 80
        c.px(int(round(15.5 + 13 * math.cos(a))),
             int(round(20 - 4 * math.sin(a))), P['glow'])
    c.ellipse(15.5, 16, 13, 3, INK)                       # the disc's rim
    c.ellipse(15.5, 16, 12, 2, P['sil_lo'])
    c.ellipse(15.5, 14, 13, 3, INK)                       # its top face
    c.ellipse(15.5, 14, 12, 2, P['sil'])
    c.ellipse(15.5, 13, 10, 1, P['sil_hi'])
    c.hline(7, 24, 12, P['white'])
    c.hline(4, 27, 18, P['ink2'])                         # the underside
    for x in range(6, 27, 5):                             # vapour off the cold
        c.px(x, 22 + (x // 5) % 2, P['ice_hi'])
        c.px(x + 2, 23 - (x // 5) % 2, P['ice'])
    sparkle(c, 26, 6)


@product('pyremite_g')
def pyremite_g(c):
    bar(c, 1, 4, 30, 28, P['met_hi'], P['met'], P['met_lo'])   # the machine
    for y in range(8, 27, 5):
        c.hline(3, 28, y, P['met_lo'])
    c.rect(7, 8, 24, 24, INK)                                  # the magnet,
    c.rect(8, 9, 23, 23, P['red'])                             # stuck for good
    c.hline(8, 23, 9, P['red_hi'])
    c.rect(12, 13, 19, 23, P['met'])
    c.frame(12, 13, 19, 23, INK)
    c.rect(8, 9, 11, 12, P['red_hi'])
    c.rect(20, 9, 23, 12, P['red_lo'])
    for i in range(6):                                         # a crack, closing
        c.px(15 + (i % 2), 4 + i, P['hot_a'] if i < 3 else P['hot_c'])
    sparkle(c, 26, 7)


@product('paradox_d')
def paradox_d(c):
    # Bulk metal whose colour will not settle. Sixteen 1px bands read as a
    # test pattern, so this is a small number of large patches instead, with
    # the ingot's own silhouette and top face left intact underneath — the
    # shape is a normal casting, only the colour is wrong.
    HUES = [P['cry'], P['ener_b'], P['hot_b'], P['grn'], P['brass']]
    DK = [P['cry_lo'], P['ener_c'], P['hot_c'], P['grn_lo'], P['brass_lo']]
    c.rect(2, 8, 29, 25, INK)                             # the front face
    c.rect(3, 9, 28, 24, P['met'])
    PATCH = [(3, 9, 12, 15, 0), (13, 9, 21, 13, 1), (22, 9, 28, 17, 2),
             (3, 16, 10, 24, 3), (11, 16, 19, 24, 4), (20, 18, 28, 24, 0),
             (13, 14, 21, 17, 3)]
    for (x0, y0, x1, y1, k) in PATCH:
        c.rect(x0, y0, x1, y1, HUES[k])
        c.hline(x0, x1, y1, DK[k])
        c.hline(x0, x1, y0, P['white'] if k % 2 else HUES[k])
    for i in range(9):                                    # the seams crawling
        c.px(12 + (i % 3), 9 + i, DK[(i + 1) % 5])
        c.px(21 - (i % 2), 12 + i, DK[i % 5])
    c.rect(2, 4, 29, 9, INK)                              # its top face
    for i, x in enumerate(range(3, 29)):
        c.vline(x, 5, 8, HUES[(i // 6) % 5])
    c.hline(3, 28, 5, P['white'])
    c.hline(3, 28, 8, P['ink2'])
    c.rect(4, 25, 27, 27, INK)                            # sat on its shadow
    c.hline(5, 26, 26, P['ink2'])
    sparkle(c, 27, 2)


@product('project_aether')
def project_aether(c):
    c.rect(4, 10, 27, 24, INK)                            # the former
    c.rect(5, 11, 26, 23, P['ink2'])
    for x in range(5, 27, 3):                             # the winding
        c.rect(x, 9, x + 1, 25, INK)
        c.vline(x, 10, 24, P['cu_hi'])
        c.vline(x + 1, 10, 24, P['cu_lo'])
    c.rect(1, 15, 5, 19, INK)                             # terminals
    c.rect(2, 16, 4, 18, P['brass'])
    c.rect(26, 15, 30, 19, INK)
    c.rect(27, 16, 29, 18, P['brass_lo'])
    for k in range(140):                                  # the field in the bore
        a = 2 * math.pi * k / 140
        c.px(int(round(15.5 + 7 * math.cos(a))),
             int(round(17 + 4 * math.sin(a))), P['cry_lo'])
    c.disc(15.5, 5, 3, INK)                               # and what it holds up
    c.disc(15.5, 5, 2, P['cry_hi'])
    for x in range(12, 20, 3):
        c.px(x, 8, P['glow'])


@product('xenolith_7')
def xenolith_7(c):
    for i in range(11):                                   # the shield
        y = 4 + i
        c.rect(4 + i // 6, y, 27 - i // 6, y, INK)
    for i in range(13):
        y = 15 + i
        c.rect(5 + i, y, 26 - i, y, INK)
    c.rect(6, 6, 25, 14, P['grn'])
    for i in range(11):
        c.rect(7 + i, 16 + i, 24 - i, 16 + i, P['grn'])
    c.hline(6, 25, 6, P['grn_hi'])
    c.vline(6, 6, 14, P['grn_hi'])
    c.rect(13, 9, 18, 20, P['brass'])                     # the boss
    c.frame(13, 9, 18, 20, INK)
    c.px(14, 10, P['brass_hi'])
    for i in range(9):                                    # a crack, healing shut
        x = 8 + i
        y = 8 + (i % 3)
        c.px(x, y, P['hot_a'] if i > 4 else P['ink2'])
        c.px(x, y + 1, P['hot_c'] if i > 4 else P['ink2'])
    sparkle(c, 22, 22)


@product('chronos_ix')
def chronos_ix(c):
    c.rect(4, 2, 27, 5, INK)                              # warped frame
    c.rect(5, 3, 26, 4, P['brass'])
    c.hline(5, 26, 3, P['brass_hi'])
    c.rect(3, 27, 28, 30, INK)
    c.rect(4, 28, 27, 29, P['brass_lo'])
    c.line(6, 5, 8, 27, INK); c.line(25, 5, 24, 27, INK)  # the posts, bent
    for i in range(11):                                   # the upper bulb
        y = 6 + i
        c.rect(8 + i, y, 23 - i, y, INK)
        if 23 - i - (8 + i) > 1:
            c.rect(9 + i, y, 22 - i, y, P['glass'])
    for i in range(11):                                   # the lower
        y = 26 - i
        c.rect(8 + i, y, 23 - i, y, INK)
        if 23 - i - (8 + i) > 1:
            c.rect(9 + i, y, 22 - i, y, P['glass'])
    for i in range(5):                                    # sand, stopped mid-air
        c.rect(11 + i, 22 - i, 20 - i, 22 - i, P['brass'])
    c.px(15, 16, P['brass_hi']); c.px(16, 18, P['brass'])
    c.px(15, 12, P['brass_hi'])
    for x in range(10, 22, 4):
        c.px(x, 2, P['cry_hi'])


@product('azoth')
def azoth(c):
    c.disc(10, 21, 8, INK)                                # the cucurbit
    c.disc(10, 21, 7, P['glass'])
    c.disc(10, 24, 6, P['cry'])
    c.disc(8, 19, 3, P['white'])
    c.rect(7, 8, 13, 14, INK)                             # its neck
    c.rect(8, 9, 12, 13, P['glass'])
    c.rect(6, 4, 15, 9, INK)                              # the head
    c.rect(7, 5, 14, 8, P['glass'])
    c.px(8, 6, P['white'])
    for i in range(9):                                    # the beak, descending
        c.px(14 + i, 6 + i, INK); c.px(15 + i, 6 + i, INK)
        c.px(15 + i, 7 + i, P['glass'])
    c.rect(21, 18, 29, 28, INK)                           # the receiver
    c.rect(22, 19, 28, 27, P['glass'])
    c.rect(22, 23, 28, 27, P['cry_lo'])
    c.hline(22, 28, 23, P['cry_hi'])
    c.px(24, 16, P['cry_hi']); c.px(24, 18, P['cry'])     # a drop falling
    sparkle(c, 5, 14)


@product('quintessence')
def quintessence(c):
    for rx, ry, col in ((13, 5, P['brass']), (13, 13, P['brass_lo']),
                        (5, 13, P['brass'])):
        for k in range(300):
            a = 2 * math.pi * k / 300
            c.px(int(round(15.5 + rx * math.cos(a))),
                 int(round(16 + ry * math.sin(a))), col)
    for rx, ry in ((13, 5), (13, 13), (5, 13)):           # ink under each ring
        for k in range(300):
            a = 2 * math.pi * k / 300
            x = int(round(15.5 + rx * math.cos(a)))
            y = int(round(16 + ry * math.sin(a)))
            if (x, y - 1) not in c.d:
                c.px(x, y - 1, INK)
    c.rect(3, 28, 28, 30, INK)                            # the stand
    c.rect(4, 29, 27, 29, P['brass_lo'])
    c.disc(15.5, 16, 4, INK)                              # the fifth essence
    c.disc(15.5, 16, 3, P['cry'])
    c.disc(15, 15, 2, P['cry_hi'])
    c.px(15, 15, P['white'])
    for dx, dy in ((-6, -6), (7, -5), (-7, 6), (6, 7)):
        c.px(15 + dx, 16 + dy, P['cry_hi'])


@product('lapis')
def lapis(c):
    c.rect(4, 24, 27, 30, INK)                            # the plinth
    c.rect(5, 25, 26, 29, P['brass_lo'])
    c.hline(5, 26, 25, P['brass'])
    c.rect(8, 22, 23, 25, INK)
    c.rect(9, 23, 22, 24, P['brass'])
    c.hline(9, 22, 23, P['brass_hi'])
    STONE = ['....ooo....',
             '..ooaaaoo..',
             '.oaaaaabbo.',
             'oaaaabbbbbo',
             'oaaabbbbbco',
             'oaabbbbbcco',
             '.obbbbbcco.',
             '.obbbbccco.',
             '..obbccco..',
             '...occco...',
             '....ooo....']
    c.stamp(STONE, {'o': INK, 'a': P['red_hi'], 'b': P['red'], 'c': P['red_lo']},
            ox=10, oy=8)
    c.px(13, 11, P['white']); c.px(14, 11, P['white']); c.px(13, 12, P['white'])
    for dx, dy in ((-6, -3), (7, -1), (-7, 5), (8, 6), (0, -6)):
        c.px(15 + dx, 13 + dy, P['hot_a'])
    for k in range(120):                                  # its aura
        a = 2 * math.pi * k / 120
        x = int(round(15.5 + 12 * math.cos(a)))
        y = int(round(13 + 11 * math.sin(a)))
        if (x, y) not in c.d and k % 3 == 0:
            c.px(x, y, P['red_lo'])


if __name__ == '__main__':
    for did, fn in ART.items():
        c = Canvas(S, S)
        fn(c)
        c.save(os.path.join(OUT, did + '.png'))
    print('products ok:', len(ART))
