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
from pixshapes import box, ramp, round_rect

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


def ingot(c, cx, cy, hw, h, top, lit, shade, edge=None):
    """A solid block, isometric. The house projection (front face + top band,
    no side faces) is right for a machine standing on a floor, where a dozen
    of them have to agree with each other; for a bare lump of metal in a popup
    it draws a rectangle inside a rectangle, which reads as a screen. A block
    needs three faces meeting at a corner before it stops being a panel.
    """
    col = {}
    for x in range(cx - hw, cx + hw + 1):
        dx = abs(x - cx)
        halfh = (hw - dx) // 2
        col[x] = (cy - halfh, cy + halfh)
    for x, (t, b) in col.items():                          # the top face
        for y in range(t, b + 1):
            c.px(x, y, top if y <= cy else (lit if x <= cx else shade))
    for x, (t, b) in col.items():                          # and the two sides
        for y in range(b + 1, b + 1 + h):
            c.px(x, y, lit if x <= cx else shade)
    if edge:
        for x, (t, b) in col.items():
            c.px(x, b + h, edge)
    c.outline(INK, over=None)


def ell_ring(c, cx, cy, rx, ry, col):
    """The outline of an ellipse, one pixel wide. c.ellipse fills, and an
    armillary sphere drawn with filled ellipses is a plate."""
    for y in range(c.h):
        t = 1.0 - ((y - cy) / (ry + 0.5)) ** 2
        if t < 0:
            continue
        dx = (rx + 0.5) * math.sqrt(t)
        c.px(int(round(cx - dx)), y, col)
        c.px(int(round(cx + dx)), y, col)
    for x in range(c.w):
        t = 1.0 - ((x - cx) / (rx + 0.5)) ** 2
        if t < 0:
            continue
        dy = (ry + 0.5) * math.sqrt(t)
        c.px(x, int(round(cy - dy)), col)
        c.px(x, int(round(cy + dy)), col)


def sparkle(c, x, y):
    c.px(x, y, P['white'])
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        c.px(x + dx, y + dy, P['sil_hi'])


# =====================================================================
# Real alloys
# =====================================================================
@product('brass')
def brass(c):
    # The trumpet on the diagonal, as in the reference: bell up and to the
    # right, valves standing off the bore, slide looping back below.
    #
    # Two things had to be learned here. A rotated shape has to be rasterised
    # per pixel — assembled out of 45-degree strokes it comes out as a
    # checkerboard, because two diagonal lines a pixel apart only touch at
    # their corners. And the parts have to be laid down in separate passes
    # with an outline between them, or valves, bore and bell fuse into one
    # gold blob with nothing to tell them apart.
    OX, OY = 5.0, 27.0
    R = math.sqrt(2) / 2
    BORE, BELL = 15.0, 25.0
    VALVES = (4.5, 9.0, 13.5)

    def sweep(test):
        """Paint every pixel the test accepts, in bore coordinates: u along
        the instrument, v across it, v negative on the lit side."""
        for y in range(32):
            for x in range(32):
                u = ((x - OX) - (y - OY)) * R
                v = ((x - OX) + (y - OY)) * R
                col = test(u, v)
                if col is not None:
                    c.px(x, y, col)

    def shade(v, half):
        if v < -half + 1.5:
            return P['brass_hi']
        if v > half - 1.1:
            return P['brass_lo']
        return P['brass']

    def barrel(u, v):
        if 0 <= u <= BORE:
            half = 2.3
        elif BORE < u <= BELL:
            half = min(2.3 + (u - BORE) ** 2 / 8.0, 8.0)
        elif -3.0 <= u < 0:
            half = 1.4 - u * 0.75
        else:
            return None
        return shade(v, half) if abs(v) <= half else None

    sweep(barrel)
    c.outline(INK, over=None)

    def valves(u, v):
        for vu in VALVES:
            if abs(u - vu) <= 1.2 and -8.6 <= v <= -3.9:
                return P['brass_hi'] if u < vu else P['brass']
            if abs(u - vu) <= 2.0 and -10.4 <= v < -8.6:
                return P['brass_hi']
        return None

    sweep(valves)
    c.outline(INK, over=None)

    def slide(u, v):
        if 5.0 <= u <= 14.0 and 4.8 <= v <= 6.9:
            return P['brass'] if v < 6.0 else P['brass_lo']
        if (abs(u - 5.0) <= 1.0 or abs(u - 14.0) <= 1.0) and 2.6 <= v < 4.8:
            return P['brass_lo']
        return None

    sweep(slide)
    c.outline(INK, over=None)
    for t in range(-8, 9):                                # a lip on the bell
        x = int(round(OX + (BELL + t * 0.9) * R))
        y = int(round(OY + (t * 0.9 - BELL) * R))
        if c.d.get((x, y)) not in (None, INK):
            c.px(x, y, P['brass_hi'])


@product('cupronickel')
def cupronickel(c):
    # A 100-yen piece. The denomination has to be one solid weight — stamping
    # it twice a pixel apart to fake an emboss just broke the strokes.
    c.disc(15.5, 15.5, 14, INK)
    c.disc(15.5, 15.5, 13, P['sil_hi'])
    c.disc(15.5, 15.5, 12, P['sil'])
    c.disc(14, 14, 10, P['sil_hi'])
    c.ring(15.5, 15.5, 12, 11, P['sil_lo'])               # the milled rim
    D = {'1': ['.a.', 'aa.', '.a.', '.a.', 'aaa'],
         '0': ['aaa', 'a.a', 'a.a', 'a.a', 'aaa']}
    for i, ch in enumerate('100'):                        # the denomination
        c.stamp(D[ch], {'a': P['met_lo']}, ox=8 + i * 4, oy=9)
    for (bx, by) in ((10, 18), (15, 17), (20, 19), (13, 22), (18, 22)):
        c.stamp(['.a.', 'aaa', '.a.'], {'a': P['sil_lo']}, ox=bx, oy=by)
        c.px(bx + 1, by + 1, P['met_lo'])                 # the blossoms
    c.px(9, 9, P['white']); c.px(10, 8, P['white'])


@product('monel')
def monel(c):
    # A polished block with one drop of filthy water beside it. They stay
    # apart: overlapped at this size they are one grey smear, and the point
    # of the picture is that the water is not wetting the metal.
    ingot(c, 11, 14, 8, 9, P['white'], P['sil'], P['sil_lo'], P['met_lo'])
    for i in range(7):                                    # a polish sweep down
        c.px(5 + i, 16 + i, P['sil_hi'])                  # the lit face
        c.px(6 + i, 16 + i, P['white'])
    c.px(8, 12, P['white']); c.px(9, 11, P['white'])      # and one on the top
    DROP = [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4), (2, 5),
            (3, 6), (3, 7), (3, 8), (3, 9), (2, 10), (1, 11)]
    for half, dy in DROP:                                 # the drop, beading
        c.hline(25 - half, 25 + half, 3 + dy, P['grime'])
    for half, dy in ((2, 8), (3, 9), (2, 10), (1, 11)):
        c.hline(25 - half, 25 + half, 3 + dy, P['grime_lo'])
    c.px(24, 9, P['grn_hi']); c.px(24, 8, P['grn_hi'])
    c.outline(INK, over=None)


@product('invar')
def invar(c):
    # Bar, thermometer, flame, crystal — four things, so they are ranked and
    # never overlapped: the bar takes the left, the thermometer stands beside
    # it, and fire and ice label the two ends of its scale.
    ingot(c, 7, 13, 6, 8, P['white'], P['sil'], P['sil_lo'], P['met_lo'])
    for i in range(5):
        c.px(3 + i, 15 + i, P['sil_hi']); c.px(4 + i, 15 + i, P['white'])
    c.px(5, 11, P['white'])
    c.rect(15, 4, 20, 23, INK)                            # the thermometer
    c.rect(16, 5, 19, 22, P['bg2'])
    c.vline(16, 5, 22, P['white'])
    c.rect(17, 6, 18, 22, P['red_lo'])
    c.rect(17, 13, 18, 22, P['red'])
    c.px(17, 13, P['red_hi'])
    c.disc(17.5, 25, 4, INK)
    c.disc(17.5, 25, 3, P['red'])
    c.disc(16, 24, 1, P['red_hi'])
    for y in (8, 10, 16, 18):
        c.px(19, y, P['ink2'])
    FLAME = [(0, 0), (1, 1), (2, 2), (2, 3), (3, 4), (3, 5), (2, 6), (1, 7)]
    for half, dy in FLAME:                                # fire at the top
        c.hline(27 - half, 27 + half, 2 + dy, P['hot_c'])
    for half, dy in ((0, 3), (1, 4), (2, 5), (1, 6), (0, 7)):
        c.hline(27 - half, 27 + half, 2 + dy, P['hot_b'])
    c.px(27, 7, P['hot_a']); c.px(27, 8, P['hot_a'])
    c.stamp(['..a.a..', '..aaa..', 'a.aaa.a', '.aaaaa.', 'aaaaaaa',
             '.aaaaa.', 'a.aaa.a', '..aaa..', '..a.a..'],   # ice at the bottom
            {'a': P['ice_hi']}, ox=23, oy=18)
    for (dx, dy) in ((1, 2), (5, 2), (3, 4), (1, 6), (5, 6)):
        c.px(23 + dx, 18 + dy, P['ice'])
    c.outline(INK, over=None)


@product('permalloy')
def permalloy(c):
    # A C-core with copper wound over about half of it. The E-I version read as
    # a picture frame: its window and its centre limb are the same rectangle
    # twice, and at icon size that is all anyone sees. A C has one shape only,
    # and the gap in it says "magnetic circuit" with no detail needed.
    #
    # The turns are angular wedges, and what separates them is a dark line
    # rather than a glimpse of the core: the core's lit face is nearly white,
    # so letting it show between the turns drew bright slashes across the
    # copper. A winding reads as a solid mass cut by the shadows between wires.
    U = c.w / 32.0
    CX, CY = c.w / 2.0 - 0.5, c.h / 2.0
    RO, RI = 13.0 * U, 7.5 * U
    RIM = 1.2                                             # in pixels, not units
    GAP = 0.62                                            # the C's opening
    TURNS = 8
    A0, A1 = math.radians(128), math.radians(232)         # half the core
    STEP = (A1 - A0) / (TURNS - 1)
    WIDE = STEP * 0.34                                    # leaves steel between

    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x - CX, y - CY
            d = math.hypot(dx, dy)
            if d > RO + 3 or d < RI - 3:
                continue
            aa = math.atan2(dy, dx)
            if aa < 0:
                aa += 2 * math.pi
            wound = any(abs(aa - (A0 + k * STEP)) <= WIDE for k in range(TURNS))
            in_coil = A0 - WIDE <= aa <= A1 + WIDE
            if in_coil and not wound and RI - 2.5 <= d <= RO + 2.5:
                c.px(x, y, P['cu_lo'])                    # the shadow between
                continue                                  # one turn and the next
            if wound and RI - 2.5 <= d <= RO + 2.5:
                # Shaded across the turn, not along it: each one is a round
                # wire, so it wants a highlight up its middle and a dark line
                # where it meets the next.
                rel = (d - (RI - 2.5)) / ((RO + 2.5) - (RI - 2.5))
                if rel > 0.88 or rel < 0.12:
                    col = P['cu_lo']
                elif 0.48 < rel <= 0.80:
                    col = P['cu_hi']
                else:
                    col = P['cu']
                c.px(x, y, col)
                continue
            if not (RI <= d <= RO):
                continue
            if dx > 0 and abs(dy) < dx * GAP:             # its gap, facing right
                continue
            if d > RO - RIM or d < RI + RIM:
                col = P['met_lo']
            elif dx + dy < -4 * U:
                col = P['met_hi']
            else:
                col = P['met']
            c.px(x, y, col)
    c.outline(INK, over=None)


@product('nichrome')
def nichrome(c):
    # An oven toaster with the door on the front, so the elements can be seen
    # actually glowing through it. The pop-up kind is a slot and a lever, and
    # a slot at 32px is a line.
    box(c, 0, 4, 31, 27, 4, ramp(P['met_hi'], P['met_hi'], P['met'], P['met_lo']), INK)
    c.rect(2, 10, 21, 25, INK)                            # the door's glass
    c.rect(3, 11, 20, 24, P['dglass'])
    c.hline(3, 20, 11, P['ink2'])
    for y in (13, 18, 22):                                # three elements
        c.hline(4, 19, y, P['hot_c'])
        c.hline(5, 18, y, P['hot_b'])
        c.hline(7, 16, y, P['hot_a'])
        c.hline(5, 18, y - 1, P['och_lo'])             # the spill above and
        c.hline(5, 18, y + 1, P['wood'])               # below each element
    c.hline(4, 19, 16, P['met_lo'])                       # the wire rack
    for x in range(5, 20, 4):
        c.px(x, 15, P['met_lo']); c.px(x, 17, P['met_lo'])
    c.rect(2, 25, 21, 27, INK)                            # the door handle
    c.hline(3, 20, 26, P['met_hi'])
    c.rect(23, 9, 29, 25, INK)                            # the controls
    c.rect(24, 10, 28, 24, P['met_lo'])
    for (ky, col) in ((13, P['och']), (20, P['met_hi'])):
        c.disc(26, ky, 2, INK)
        c.disc(26, ky, 1, col)
        c.px(25, ky - 1, P['white'])
    c.px(26, 16, P['hot_b']); c.px(26, 17, P['hot_c'])    # the pilot lamp
    c.rect(3, 27, 6, 30, INK); c.rect(25, 27, 28, 30, INK)
    c.hline(4, 5, 29, P['met_lo']); c.hline(26, 27, 29, P['met_lo'])


@product('ferritic_ss')
def ferritic_ss(c):
    # A shallow square sink seen from above and in front, the way the
    # reference has it: the deck is barely a trapezoid, the bowl is a rounded
    # square inside it, and the tap stands at the back right corner.
    for i in range(15):                                   # the deck
        y = 13 + i
        x0 = 3 - (i * 3) // 14
        x1 = 28 + (i * 3) // 14
        c.hline(x0, x1, y, INK)
        c.hline(x0 + 1, x1 - 1, y, P['sil'])
        c.px(x0 + 1, y, P['sil_hi'])
        c.px(x1 - 1, y, P['sil_lo'])
    c.hline(4, 27, 14, P['sil_hi'])
    c.hline(1, 30, 27, P['sil_lo'])
    for i in range(11):                                   # the bowl
        y = 15 + i
        x0 = 6 - (i * 2) // 10
        x1 = 25 + (i * 2) // 10
        c.hline(x0, x1, y, INK)
        if i:
            c.hline(x0 + 1, x1 - 1, y, P['sil_lo'])
    for (x, y) in ((6, 15), (25, 15), (4, 25), (27, 25)):
        c.d.pop((x, y), None)                             # its rounded corners
    c.hline(6, 25, 16, P['met_lo'])                       # the far wall's shade
    c.rect(5, 19, 26, 24, P['sil_lo'])                    # the floor
    c.hline(5, 26, 19, P['met_lo'])
    c.hline(4, 27, 25, P['sil'])                          # the near wall, lit
    c.ellipse(12, 22, 3, 2, INK)                          # the drain
    c.ellipse(12, 22, 2, 1, P['met_lo'])
    c.px(8, 18, P['sil_hi']); c.px(9, 18, P['sil_hi'])
    c.rect(23, 4, 26, 15, INK)                            # the tap, at the
    c.vline(24, 5, 14, P['sil_hi'])                       # back right corner
    c.vline(25, 5, 14, P['sil']) 
    c.rect(27, 6, 30, 9, INK)                             # its lever
    c.px(28, 7, P['sil_hi']); c.px(29, 7, P['sil'])
    c.rect(17, 3, 26, 6, INK)                             # the gooseneck
    c.hline(18, 25, 4, P['sil_hi'])
    c.hline(18, 25, 5, P['sil'])
    c.rect(16, 4, 19, 10, INK)                            # and the spout
    c.vline(17, 5, 9, P['sil_hi'])
    c.vline(18, 5, 9, P['sil_lo'])
    c.px(17, 10, P['ink2']); c.px(18, 10, P['ink2'])


@product('austenitic_ss')
def austenitic_ss(c):
    # Two implements crossed. The scalpel needs a handle wide enough to hold
    # and a blade wide enough to show an edge on — drawn as a 1px line it is
    # a drawing pin.
    c.line(11, 12, 25, 27, INK); c.line(13, 11, 27, 26, INK)   # spoon handle
    c.line(12, 12, 26, 27, P['sil'])
    c.line(12, 11, 26, 26, P['sil_hi'])
    c.ellipse(8, 8, 5, 6, INK)                                 # its bowl
    c.ellipse(8, 8, 4, 5, P['sil'])
    c.ellipse(7, 7, 2, 3, P['sil_hi'])
    c.px(6, 5, P['white'])
    for i in range(13):                                        # scalpel handle
        x, y = 5 + i, 27 - i
        c.rect(x - 1, y - 1, x + 1, y + 1, INK)
        c.px(x, y, P['sil'])
        c.px(x, y + 1, P['sil_lo'] if i % 2 else P['met_lo'])
    c.rect(3, 25, 8, 30, INK)                                  # its butt end
    c.rect(4, 26, 7, 29, P['sil_lo'])
    c.px(4, 26, P['sil_hi'])
    for i in range(8):                                         # the blade
        c.hline(18 + i, 25 - i + i // 3, 14 - i, INK)
    c.line(19, 13, 25, 7, P['sil_hi'])
    c.line(20, 14, 26, 8, P['sil'])
    c.line(21, 15, 24, 12, P['sil_lo'])
    c.px(20, 12, P['white'])
    sparkle(c, 28, 4)


@product('ti_cr_beta')
def ti_cr_beta(c):
    # A femoral stem: the head off to one side on a short neck, and a long
    # stem curving away under it. Straight and stubby it is a lollipop;
    # straight and tapered it is a hammer. The curve is the whole silhouette.
    c.disc(23, 7, 5, INK)                                 # the head
    c.disc(23, 7, 4, P['sil'])
    c.disc(22, 6, 2, P['sil_hi'])
    c.px(21, 5, P['white'])
    for i in range(6):                                    # the neck
        x, y = 20 - i, 9 + i
        c.rect(x - 2, y, x + 2, y + 1, INK)
        c.rect(x - 1, y, x + 1, y, P['sil'])
        c.px(x + 1, y, P['sil_lo'])
    for i in range(16):                                   # the stem, curving
        y = 14 + i
        cx = 15.0 - (i * i) / 42.0
        half = 3.6 - i * 0.16
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        c.rect(x0, y, x1, y, INK)
        if x1 - x0 >= 2:
            c.rect(x0 + 1, y, x1 - 1, y, P['sil'])
            c.px(x0 + 1, y, P['sil_hi'])
            c.px(x1 - 1, y, P['sil_lo'])
    for i in range(0, 12, 2):                             # the porous coating
        c.px(13 - i // 3, 16 + i, P['met_lo'])
    sparkle(c, 28, 15)


@product('nitinol')
def nitinol(c):
    # Spectacles. The rim is one pixel: two, and the lenses stop being lenses
    # and become the dark holes of a pair of goggles.
    for ex in (10, 22):
        ell_ring(c, ex, 15, 6, 6, INK)
        c.disc(ex, 15, 5, P['glass'])
        ell_ring(c, ex, 15, 6, 6, INK)
        c.disc(ex - 2, 13, 2, P['white'])
        c.px(ex + 3, 18, P['sil_hi'])
    c.hline(16, 16, 11, INK)                              # the bridge
    c.px(15, 12, INK); c.px(17, 12, INK); c.px(16, 12, P['glass'])
    c.px(16, 10, P['sil_hi'])
    c.hline(2, 3, 11, INK)                                # left temple
    c.hline(1, 2, 12, INK)
    c.px(0, 13, INK); c.px(0, 14, INK); c.px(1, 15, INK)
    c.px(2, 11, P['sil_hi'])
    c.hline(28, 29, 11, INK)                              # right temple, bent
    c.hline(29, 30, 12, INK)
    c.px(31, 11, INK); c.px(31, 10, INK)
    c.px(30, 9, INK); c.px(29, 8, INK); c.px(28, 8, INK)
    c.px(29, 11, P['sil_hi'])
    sparkle(c, 20, 26)


@product('inconel_like')
def inconel_like(c):
    # Shallow turn. The two cues a non-specialist reads on a jet engine — the
    # swept fan and the spiral on the spinner — only exist head-on, so the fan
    # face stays nearly round and the nacelle runs off behind it to the right,
    # banded, with the hot section marked near the tail.
    for i in range(13):                                   # the nacelle
        x = 19 + i
        top = 4 + (i * 6) // 12
        bot = 29 - (i * 7) // 12
        c.vline(x, top, bot, INK)
        c.vline(x, top + 1, bot - 1, P['met'])
        c.px(x, top + 1, P['met_hi'])
        c.px(x, top + 2, P['met_hi'])
        c.px(x, bot - 1, P['met_lo'])
    for x in (23, 27):                                    # its banding
        c.vline(x, 5 + (x - 19) * 6 // 12, 28 - (x - 19) * 7 // 12, P['met_lo'])
    for x in (28, 29):                                    # the hot section
        c.vline(x, 18, 21, P['hot_c'])
    c.vline(30, 18, 20, P['ink2'])
    c.rect(20, 0, 25, 6, INK)                             # a pylon stub
    c.rect(21, 0, 24, 5, P['met_lo'])
    c.px(21, 1, P['met'])
    c.ellipse(11, 16, 11, 14, INK)                        # the fan case
    c.ellipse(11, 16, 10, 13, P['met_hi'])
    c.ellipse(11, 16, 9, 12, P['met'])
    c.ellipse(11, 16, 8, 11, P['ink2'])
    for k in range(12):                                   # the fan, swept back
        a = 2 * math.pi * k / 12
        x0 = int(round(11 + 3.0 * math.cos(a)))
        y0 = int(round(16 + 4.0 * math.sin(a)))
        x1 = int(round(11 + 7.4 * math.cos(a + 0.55)))
        y1 = int(round(16 + 10.2 * math.sin(a + 0.55)))
        c.line(x0, y0, x1, y1, P['met_hi'] if k % 2 else P['met'])
    c.disc(11, 16, 3, INK)                                # the spinner
    c.disc(11, 16, 2, P['met'])
    for (dx, dy) in ((0, -2), (1, -1), (2, 0), (1, 1)):   # with the spiral
        c.px(11 + dx, 16 + dy, P['white'])
    c.px(10, 15, P['sil_hi'])


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
    # An alembic, not a flask: a copper cucurbit over a flame, a swan neck
    # carrying the vapour sideways, and a separate receiver for what comes
    # out. Drop the neck and the receiver and it is laboratory glassware.
    c.rect(2, 23, 16, 29, INK)                            # the furnace
    c.rect(3, 24, 15, 28, P['met_lo'])
    c.hline(3, 15, 24, P['met'])
    c.rect(6, 25, 12, 29, INK)
    for half, dy in ((0, 0), (1, 1), (2, 2), (2, 3)):     # and its flame
        c.hline(9 - half, 9 + half, 25 + dy, P['hot_c'])
    c.hline(8, 10, 27, P['hot_b']); c.px(9, 28, P['hot_a'])
    c.disc(9, 16, 7, INK)                                 # the cucurbit
    c.disc(9, 16, 6, P['cu'])
    c.disc(7, 14, 4, P['cu_hi'])
    c.disc(11, 19, 3, P['cu_lo'])
    c.px(6, 12, P['white'])
    c.rect(6, 21, 12, 24, INK)
    c.rect(7, 22, 11, 23, P['cu_lo'])
    c.rect(6, 6, 12, 11, INK)                             # its head
    c.rect(7, 7, 11, 10, P['cu'])
    c.hline(7, 11, 7, P['cu_hi'])
    c.rect(11, 5, 22, 8, INK)                             # the swan neck
    c.rect(12, 6, 21, 7, P['cu'])
    c.hline(12, 21, 6, P['cu_hi'])
    c.rect(19, 6, 22, 17, INK)
    c.rect(20, 7, 21, 16, P['cu'])
    c.vline(20, 7, 16, P['cu_hi'])
    c.rect(17, 16, 26, 29, INK)                           # the receiver
    c.rect(18, 17, 25, 28, P['sil'])
    c.vline(18, 17, 28, P['sil_hi'])
    c.vline(25, 17, 28, P['sil_lo'])
    c.hline(18, 25, 17, P['sil_hi'])
    c.rect(18, 23, 25, 28, P['cry'])                      # and what it caught
    c.hline(18, 25, 23, P['cry_hi'])
    c.px(19, 24, P['white'])


@product('quintessence')
def quintessence(c):
    # An armillary sphere: a meridian, an equator, one more hoop each way, and
    # a lit core. Five hoops made a basket; four leave the core visible, which
    # is the only part that says this is not furniture.
    ell_ring(c, 15.5, 14, 12, 12, P['brass'])             # the meridian
    ell_ring(c, 15.5, 14, 5, 12, P['brass_lo'])           # a second, edge-on
    ell_ring(c, 15.5, 14, 12, 4, P['brass_hi'])           # a tropic
    for x in range(3, 29):                                # and the equator
        c.px(x, 14, P['brass_hi'])
        c.px(x, 15, P['brass_lo'])
    c.disc(15.5, 14, 5, INK)                              # the core
    c.disc(15.5, 14, 4, P['ener_c'])
    c.disc(15.5, 14, 3, P['ener_b'])
    c.disc(14, 12, 2, P['ener_a'])
    c.px(13, 11, P['white'])
    c.rect(14, 26, 18, 29, INK)                           # the stand
    c.rect(15, 27, 17, 28, P['brass'])
    c.rect(10, 28, 22, 31, INK)
    c.rect(11, 29, 21, 30, P['brass'])
    c.hline(11, 21, 29, P['brass_hi'])
    c.outline(INK, over=None)


@product('lapis')
def lapis(c):
    # The philosophers' stone: a cut red crystal on a gold plinth. The first
    # pass ringed it in a dashed circle, which read as a loading spinner.
    c.rect(6, 24, 25, 29, INK)                            # the plinth
    c.rect(7, 25, 24, 26, P['brass_hi'])                  # its top face
    c.rect(7, 27, 24, 28, P['brass'])
    c.hline(7, 24, 28, P['brass_lo'])
    c.rect(9, 21, 22, 25, INK)
    c.rect(10, 22, 21, 24, P['brass'])
    c.hline(10, 21, 22, P['brass_hi'])
    c.hline(10, 21, 24, P['brass_lo'])
    for i in range(17):                                   # the crystal, cut
        y = 5 + i
        half = min(i, 6) if i < 13 else max(0, 6 - (i - 12) * 2)
        if half <= 0 and i >= 13:
            continue
        c.hline(15 - half, 16 + half, y, INK)
        if half:
            c.hline(16 - half, 15 + half, y, P['red'])
    for i in range(14):                                   # its facets
        y = 6 + i
        half = min(i, 5) if i < 12 else max(0, 5 - (i - 11) * 2)
        if half > 0:
            c.px(16 - half, y, P['red_hi'])
            c.px(15 + half, y, P['red_lo'])
    c.line(15, 6, 12, 13, P['red_hi'])
    c.line(16, 6, 19, 13, P['red_lo'])
    c.hline(11, 20, 13, P['red_lo'])
    c.hline(12, 19, 12, P['red_hi'])
    c.px(14, 9, P['white']); c.px(14, 10, P['red_hi'])
    for (sx, sy) in ((4, 8), (26, 6), (24, 17), (6, 18)):
        sparkle(c, sx, sy)


SHIPPED = {
    'brass', 'cupronickel', 'monel', 'invar', 'permalloy', 'nichrome',
    'ferritic_ss', 'austenitic_ss', 'ti_cr_beta', 'nitinol', 'inconel_like',
    'azoth', 'quintessence', 'lapis',
}

# The thirteen imported icons are 64px, so anything still drawn here is drawn
# at 64 too — a 32px sprite doubled would show twice the dot size next to them.
CANVAS = 64

if __name__ == '__main__':
    for did in SHIPPED:
        c = Canvas(CANVAS, CANVAS)
        ART[did](c)
        c.save(os.path.join(OUT, did + '.png'))
    for stale in sorted(set(ART) - SHIPPED):
        path = os.path.join(OUT, stale + '.png')
        if os.path.exists(path):
            os.remove(path)
    print('products ok: %d at %dpx | drawn but not shipped: %d'
          % (len(SHIPPED), CANVAS, len(ART) - len(SHIPPED)))
