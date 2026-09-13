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
    # Read as an icon of a trumpet first and as a trumpet second: bell, three
    # valves, mouthpiece, nothing else. The first pass drew a real instrument's
    # proportions and at 32px that is a pile of brass tubing.
    CY = 16
    for i in range(10):                                   # the bell, flaring
        x = 21 + i
        half = 3 + (i * i) // 9
        c.vline(x, CY - half, CY + half, INK)
        if i:
            c.vline(x, CY - half + 1, CY + half - 1, P['brass'])
            c.px(x, CY - half + 1, P['brass_hi'])
            c.px(x, CY + half - 1, P['brass_lo'])
    c.vline(30, CY - 12, CY + 12, INK)                    # its rim, straight on
    c.vline(29, CY - 11, CY + 11, P['brass_hi'])
    c.vline(30, CY - 11, CY + 11, P['brass'])
    c.vline(31, CY - 10, CY + 10, P['brass_lo'])
    c.rect(4, CY - 2, 22, CY + 2, INK)                    # the body tube
    c.rect(4, CY - 1, 22, CY + 1, P['brass'])
    c.hline(4, 22, CY - 1, P['brass_hi'])
    c.hline(4, 22, CY + 1, P['brass_lo'])
    for vx in (8, 13, 18):                                # three valve casings
        c.rect(vx, 6, vx + 3, CY - 2, INK)
        c.rect(vx + 1, 7, vx + 2, CY - 2, P['brass'])
        c.vline(vx + 1, 7, CY - 2, P['brass_hi'])
        c.vline(vx + 2, 7, CY - 2, P['brass_lo'])
        c.rect(vx, 3, vx + 3, 6, INK)                     # and finger buttons
        c.rect(vx + 1, 4, vx + 2, 5, P['brass_hi'])
        c.px(vx + 2, 5, P['brass'])
        c.rect(vx, CY + 3, vx + 3, CY + 6, INK)           # valve slides below
        c.rect(vx + 1, CY + 3, vx + 2, CY + 5, P['brass_lo'])
    c.rect(0, CY - 4, 5, CY + 4, INK)                     # the mouthpiece
    c.rect(1, CY - 3, 4, CY + 3, P['brass_hi'])
    c.rect(2, CY - 2, 4, CY + 2, P['brass'])
    c.px(1, CY - 3, P['white'])


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
    # Two ideas side by side, not one on top of the other: a bulk that is
    # plainly polished, and one drop of filthy water that is plainly not
    # wetting it. Overlapping them cost both.
    c.rect(1, 14, 24, 28, INK)                            # the bulk, front face
    c.rect(2, 15, 23, 21, P['sil_hi'])                    # a polished face
    c.rect(2, 22, 23, 27, P['sil_lo'])                    # reflects sky over
    c.hline(2, 23, 21, P['white'])                        # ground: the step is
    c.hline(2, 23, 22, P['met_lo'])                       # what says "mirror"
    c.hline(2, 23, 27, P['met_lo'])
    for i in range(14):                                   # and one polish sweep
        x = 4 + i
        if 2 <= x <= 23:
            c.px(x, 15 + i, P['white'])
            c.px(x + 1, 15 + i, P['sil_hi'])
    c.rect(1, 10, 24, 15, INK)                            # its top face
    c.rect(2, 11, 23, 14, P['sil'])
    c.hline(2, 23, 11, P['sil_hi'])
    c.hline(2, 23, 14, P['sil_lo'])
    c.px(4, 12, P['white']); c.px(5, 12, P['white'])
    DROP = [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4), (2, 5),
            (3, 6), (3, 7), (3, 8), (2, 9), (1, 10)]       # a teardrop: point
    for half, dy in DROP:                                  # at the top, bulb
        c.hline(26 - half, 26 + half, 2 + dy, P['grime'])  # at the bottom
    c.hline(25, 27, 9, P['grime_lo'])
    c.hline(24, 28, 10, P['grime_lo'])
    c.hline(25, 27, 11, P['grime_lo'])
    c.px(25, 8, P['grn_hi']); c.px(25, 7, P['grn_hi'])     # its one highlight
    c.outline(INK, over=None)


@product('invar')
def invar(c):
    # Bulk on the left, thermometer on the right, and the two ends of the
    # scale labelled by a flame and a crystal. Nothing overlaps: at 32px an
    # overlap is just a collision.
    c.rect(1, 12, 15, 26, INK)                            # the bulk
    c.rect(2, 13, 14, 19, P['sil_hi'])
    c.rect(2, 20, 14, 25, P['sil_lo'])
    c.hline(2, 14, 19, P['white'])
    c.hline(2, 14, 20, P['met_lo'])
    c.hline(2, 14, 25, P['met_lo'])
    for i in range(11):
        x = 3 + i
        if 2 <= x <= 14:
            c.px(x, 13 + i, P['white'])
    c.rect(1, 8, 15, 13, INK)                             # its top face
    c.rect(2, 9, 14, 12, P['sil'])
    c.hline(2, 14, 9, P['sil_hi'])
    c.hline(2, 14, 12, P['sil_lo'])
    c.rect(17, 2, 22, 23, INK)                            # the thermometer
    c.rect(18, 3, 21, 22, P['bg2'])
    c.vline(18, 3, 22, P['white'])
    c.rect(19, 4, 20, 22, P['red_lo'])
    c.rect(19, 13, 20, 22, P['red'])
    c.px(19, 13, P['red_hi'])
    c.disc(19.5, 25, 4, INK)                              # and its bulb
    c.disc(19.5, 25, 3, P['red'])
    c.disc(18, 24, 1, P['red_hi'])
    for y in (6, 8, 10, 16, 18, 20):                      # a scale on it
        c.px(21, y, P['ink2'])
    FLAME = [(0, 0), (1, 1), (1, 2), (2, 3), (2, 4), (2, 5), (2, 6), (1, 7)]
    for half, dy in FLAME:                                # hot end: a flame
        c.hline(27 - half, 27 + half, 2 + dy, P['hot_c'])
    for half, dy in ((0, 3), (1, 4), (1, 5), (1, 6), (0, 7)):
        c.hline(27 - half, 27 + half, 2 + dy, P['hot_b'])
    c.px(27, 7, P['hot_a']); c.px(27, 8, P['hot_a'])
    c.stamp(['..a..', 'a.a.a', '.aaa.', 'aaaaa',          # cold end: a crystal
             '.aaa.', 'a.a.a', '..a..'],
            {'a': P['ice_hi']}, ox=24, oy=19)
    c.px(25, 21, P['ice']); c.px(29, 23, P['ice'])
    c.px(26, 24, P['ice'])
    c.outline(INK, over=None)


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
    # A front-opening oven toaster, not a pop-up one: the door is what makes
    # the shape a toaster, and it also gives somewhere to show the elements
    # actually glowing.
    c.rect(0, 7, 31, 27, INK)                             # the body
    c.rect(1, 8, 30, 26, P['met'])
    c.hline(1, 30, 8, P['met_hi'])
    c.hline(1, 30, 26, P['met_lo'])
    c.rect(0, 3, 31, 8, INK)                              # its top face
    c.rect(1, 4, 30, 7, P['met_hi'])
    c.hline(1, 30, 7, P['met'])
    c.rect(2, 10, 21, 24, INK)                            # the door's glass
    c.rect(3, 11, 20, 23, P['dglass'])
    c.hline(3, 20, 11, P['ink2'])
    c.hline(4, 19, 13, P['hot_c'])                        # elements, top
    c.hline(5, 18, 13, P['hot_b'])
    c.hline(7, 16, 13, P['hot_a'])
    c.hline(4, 19, 21, P['hot_c'])                        # elements, bottom
    c.hline(5, 18, 21, P['hot_b'])
    c.hline(7, 16, 21, P['hot_a'])
    for x in range(4, 20, 3):                             # the wire rack
        c.px(x, 17, P['met_lo'])
    c.hline(4, 19, 18, P['met_lo'])
    c.hline(5, 18, 16, (255, 200, 120, 60))               # the glow on the glass
    c.rect(2, 24, 21, 26, INK)                            # the door handle
    c.rect(3, 25, 20, 25, P['met_hi'])
    c.rect(23, 10, 29, 24, INK)                           # the control panel
    c.rect(24, 11, 28, 23, P['met_lo'])
    c.disc(26, 14, 2, INK)                                # timer knob
    c.disc(26, 14, 1, P['och'])
    c.px(26, 13, P['och_hi'])
    c.disc(26, 20, 2, INK)                                # and heat knob
    c.disc(26, 20, 1, P['met_hi'])
    c.px(25, 19, P['white'])
    c.px(26, 17, P['hot_b'])                              # the pilot lamp
    c.rect(3, 27, 6, 29, INK); c.rect(25, 27, 28, 29, INK)  # feet
    c.hline(4, 5, 28, P['met_lo']); c.hline(26, 27, 28, P['met_lo'])


@product('ferritic_ss')
def ferritic_ss(c):
    # A sink is looked down into, so the deck is a trapezoid widening toward
    # the viewer and the bowl walls converge to a floor — drawn as a front
    # elevation it was a microwave three times running. The tap is thin, but
    # thin still means ink around a fill: all-ink at 3px read as wireframe.
    c.rect(21, 2, 25, 14, INK)                            # the tap's riser
    c.rect(22, 3, 24, 14, P['sil'])
    c.vline(22, 3, 14, P['sil_hi'])
    c.vline(24, 3, 14, P['sil_lo'])
    c.rect(25, 4, 29, 7, INK)                             # its lever
    c.rect(26, 5, 28, 6, P['sil'])
    c.px(26, 5, P['sil_hi'])
    c.rect(10, 1, 25, 5, INK)                             # the gooseneck
    c.rect(11, 2, 24, 4, P['sil'])
    c.hline(11, 24, 2, P['sil_hi'])
    c.hline(11, 24, 4, P['sil_lo'])
    c.rect(9, 2, 14, 12, INK)                             # and the spout
    c.rect(10, 3, 13, 11, P['sil'])
    c.vline(10, 3, 11, P['sil_hi'])
    c.vline(13, 3, 11, P['sil_lo'])
    c.hline(10, 13, 12, P['ink2'])
    for i in range(17):                                   # the deck
        y = 13 + i
        x0 = 5 - (i * 5) // 16
        x1 = 26 + (i * 5) // 16
        c.hline(x0, x1, y, INK)
        c.hline(x0 + 1, x1 - 1, y, P['sil'])
        c.px(x0 + 1, y, P['sil_hi'])
        c.px(x1 - 1, y, P['sil_lo'])
    c.hline(6, 25, 14, P['sil_hi'])
    c.hline(1, 30, 29, P['sil_lo'])
    for i in range(12):                                   # the bowl, converging
        y = 16 + i
        x0 = 8 - (i * 3) // 11
        x1 = 23 + (i * 3) // 11
        c.hline(x0, x1, y, INK)
        if i:
            c.hline(x0 + 1, x1 - 1, y, P['sil_lo'] if i < 4 else P['met_lo'])
    c.hline(8, 23, 17, P['ink2'])                         # far wall, in shade
    c.rect(6, 21, 25, 26, P['met_lo'])                    # the floor
    c.hline(6, 25, 21, P['ink2'])
    c.hline(6, 25, 26, P['sil_lo'])                       # near wall, lit
    c.hline(5, 26, 27, P['sil'])
    c.ellipse(15.5, 24, 3, 2, INK)                        # the drain
    c.ellipse(15.5, 24, 2, 1, P['ink2'])
    c.px(17, 19, P['sil_hi']); c.px(18, 19, P['sil_hi'])


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
    # Ordinary spectacles. Big lenses and one temple read as goggles, so the
    # lenses come down and both temples go on — the right one folded back is
    # the only thing that says the frame came back from it.
    for ex in (9, 22):
        c.ring(ex, 15, 5, 4, INK)                         # the rims
        c.disc(ex, 15, 3, P['glass'])
        c.disc(ex - 1, 13, 1, P['white'])
        c.px(ex + 2, 17, P['sil_hi'])
    c.hline(14, 17, 12, INK)                              # the bridge
    c.px(14, 13, INK); c.px(17, 13, INK)
    c.px(15, 13, P['bg2']); c.px(16, 13, P['bg2'])
    c.px(15, 12, P['sil_hi'])
    c.hline(2, 4, 12, INK)                                # left temple, straight
    c.hline(1, 3, 13, INK)
    c.px(3, 12, P['sil_hi'])
    c.px(0, 13, INK); c.px(0, 14, INK); c.px(1, 15, INK)  # over the ear
    c.hline(27, 29, 12, INK)                              # right temple, bent
    c.hline(28, 30, 13, INK)
    c.px(28, 12, P['sil_hi'])
    c.px(31, 13, INK); c.px(31, 14, INK); c.px(30, 15, INK)
    c.px(30, 11, INK); c.px(29, 10, INK)                  # kinked where it was
    c.px(28, 9, INK); c.px(27, 9, INK)                    # pulled too far
    c.px(28, 10, P['sil_hi'])
    sparkle(c, 21, 26)


@product('inconel_like')
def inconel_like(c):
    # Shallow turn: the fan face stays nearly round, because the swept blades
    # and the spiral on the spinner are the two cues a non-specialist reads,
    # and both of them only exist head-on. Blades are drawn as lines, not as
    # a scatter of pixels along an arc — the scatter came out as static.
    for i in range(9):                                    # the nacelle, behind
        x = 23 + i                                        # and to the right
        top = 6 + (i * 5) // 8
        bot = 27 - (i * 6) // 8
        c.vline(x, top, bot, INK)
        c.vline(x, top + 1, bot - 1, P['met'])
        c.px(x, top + 1, P['met_hi'])
        c.px(x, bot - 1, P['met_lo'])
    for i in range(3):
        c.vline(29 + i, 16 + i, 20 - i, P['ink2'])        # its nozzle
    for i in range(7):                                    # the pylon, reaching
        y = 7 - i                                         # the nacelle
        c.rect(22 + i // 3, y, 27 - i // 4, y, INK)
        c.rect(23 + i // 3, y, 26 - i // 4, y, P['met_lo'])
    c.ellipse(12, 16, 12, 14, INK)                        # the fan case
    c.ellipse(12, 16, 11, 13, P['met_hi'])
    c.ellipse(12, 16, 10, 12, P['met'])
    c.ellipse(12, 16, 9, 11, P['ink2'])                   # the dark inside it
    for k in range(12):                                   # the fan, swept back
        a = 2 * math.pi * k / 12
        x0 = int(round(12 + 3.4 * math.cos(a)))
        y0 = int(round(16 + 4.0 * math.sin(a)))
        x1 = int(round(12 + 8.2 * math.cos(a + 0.55)))
        y1 = int(round(16 + 10.0 * math.sin(a + 0.55)))
        c.line(x0, y0, x1, y1, P['met_hi'] if k % 2 else P['met'])
    c.disc(12, 16, 3, INK)                                # the spinner
    c.disc(12, 16, 2, P['met'])
    for (dx, dy) in ((0, -2), (1, -1), (2, 0), (1, 1)):   # with the spiral
        c.px(12 + dx, 16 + dy, P['white'])
    c.px(11, 15, P['sil_hi'])


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


# Only these ship. The Discovery popup shows product art for the eleven real
# alloys and for tier t3, and keeps the element gradient for t1 and t2 — those
# seven are still drawn here, but writing their files would put assets in the
# repository that nothing loads.
SHIPPED = {
    'brass', 'cupronickel', 'monel', 'invar', 'permalloy', 'nichrome',
    'ferritic_ss', 'austenitic_ss', 'ti_cr_beta', 'nitinol', 'inconel_like',
    'azoth', 'quintessence', 'lapis',
}

if __name__ == '__main__':
    for did in SHIPPED:
        c = Canvas(S, S)
        ART[did](c)
        c.save(os.path.join(OUT, did + '.png'))
    for stale in sorted(set(ART) - SHIPPED):
        path = os.path.join(OUT, stale + '.png')
        if os.path.exists(path):
            os.remove(path)
    print('products ok:', len(SHIPPED), '| drawn but not shipped:',
          len(ART) - len(SHIPPED))
