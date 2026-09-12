"""Ben / Grace / Smith — 32x32 bust portraits.

Built as one shared skull-and-shoulders scaffold with per-character hair,
features and colour, rather than three independent drawings. At 32px the
silhouette does nearly all the identifying work, so the scaffold fixes the
proportions once and each character differs in hair shape, one accessory and
one palette — which is also what keeps them looking like one cast.

Note on the existing art: the shipped icons are abstract symbols (Ben is a
pair of spectacles, Grace a figure against the sky), and Smith has no file at
all — his grey silhouette is drawn inline in the HTML on purpose. These are
portraits instead, because a symbol gains nothing from being pixelated
whereas a face does.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
INK = P['ink']

# The head is deliberately kept off the frame edge: at 32px an icon that
# touches its own border reads as cropped rather than as a portrait.
HCX, HCY, HRX, HRY = 15.5, 13, 7.5, 8.5     # head: x 8..23, y 4..21
EYE_Y = 14
NECK_TOP, SHOULDER_CY = 18, 36


def scaffold(c, skin, skin_lo, coat, coat_hi, coat_lo, collar):
    c.ellipse(15.5, SHOULDER_CY, 15, 11, INK)          # shoulders
    c.ellipse(15.5, SHOULDER_CY, 14, 10, coat)
    c.ellipse(8, SHOULDER_CY + 1, 7, 9, coat_hi)       # light falls from the left
    c.ellipse(24, SHOULDER_CY + 2, 6, 8, coat_lo)
    for i in range(6):                                  # collar, opening into a V
        y = 25 + i
        c.rect(15 - i, y, 16 + i, y, collar)
        c.px(14 - i, y, INK); c.px(17 + i, y, INK)
    c.rect(12, NECK_TOP, 19, 26, INK)                   # neck
    c.rect(13, NECK_TOP, 18, 25, skin_lo)
    c.rect(13, NECK_TOP, 18, 20, skin)
    c.ellipse(HCX, HCY, HRX + 1, HRY + 1, INK)          # head
    c.ellipse(HCX, HCY, HRX, HRY, skin)
    c.ellipse(19, 15, 4, 5, skin_lo)                    # shade the right cheek
    c.ellipse(18, 14, 3, 4, skin)
    for ex in (7, 24):                                  # ears
        c.disc(ex, 14, 2, INK)
        c.disc(ex, 14, 1, skin_lo)


def eyes(c, col=None, lash=False):
    col = col or INK
    for ex in (12, 19):
        c.rect(ex - 1, EYE_Y, ex, EYE_Y + 1, col)
        c.px(ex, EYE_Y, P['white'])
        if lash:
            c.px(ex - 1, EYE_Y - 1, col); c.px(ex, EYE_Y - 1, col)


def round_glasses(c, frame, lens):
    """Ben's spectacles — the one thing his shipped icon is made of, so they
    stay oversized enough to crowd the face."""
    for ex in (12, 19):
        c.disc(ex, EYE_Y, 4, frame)
        c.disc(ex, EYE_Y, 3, lens)
    c.hline(15, 16, EYE_Y, frame)                       # bridge
    c.hline(6, 7, EYE_Y - 1, frame)                     # temples
    c.hline(24, 25, EYE_Y - 1, frame)


def rect_glasses(c, frame, lens):
    """Smith's — half-rim readers, squarer and sitting lower."""
    for x0 in (8, 17):
        c.rect(x0, EYE_Y - 2, x0 + 6, EYE_Y + 2, lens)
        c.frame(x0, EYE_Y - 2, x0 + 6, EYE_Y + 2, frame)
        c.px(x0 + 1, EYE_Y - 1, P['white'])
    c.hline(15, 16, EYE_Y - 1, frame)
    c.hline(6, 7, EYE_Y - 1, frame)
    c.hline(24, 25, EYE_Y - 1, frame)


def nose(c, y, col):
    c.px(15, y, col); c.px(15, y + 1, col); c.px(16, y + 1, col)


def finish(c, tint, rim):
    """Flat tint behind the bust plus a 1px rim, so the three read as a set
    and each still carries its owner's roster colour."""
    for y in range(32):
        for x in range(32):
            if (x, y) not in c.d:
                c.px(x, y, tint)
    c.frame(0, 0, 31, 31, rim)


def save(c, name):
    c.save(os.path.join(OUT, name + '.png'))
    c.save(os.environ['SCRATCH'] + '/%s_x8.png' % name, scale=8)


# =====================================================================
# Ben — the junior. Bowl of brown hair, oversized round spectacles, a
# lab coat a size too big. Roster colour #7e603c.
# =====================================================================
c = Canvas(32, 32)
scaffold(c, P['sk'], P['sk_lo'], P['coat'], P['coat_hi'], P['coat_lo'], (236, 231, 217))
HAIR, HAIR_HI, HAIR_LO = (107, 74, 42), (144, 104, 60), (74, 50, 28)
c.ellipse(15.5, 9, 8.5, 6.5, INK)                       # bowl cut
c.ellipse(15.5, 9, 7.5, 5.5, HAIR)
c.ellipse(11, 6, 4, 2.5, HAIR_HI)
c.rect(7, 9, 24, 11, HAIR)                              # blunt fringe
c.hline(8, 23, 11, HAIR_LO)                             # its cut edge
c.px(13, 11, P['sk']); c.px(14, 10, P['sk'])            # one gap he never fixes
c.px(20, 11, P['sk'])
eyes(c)
round_glasses(c, INK, P['glass'])
eyes(c)                                                 # redrawn over the lenses
nose(c, 17, P['sk_lo'])
c.hline(14, 17, 19, INK)                                # small, closed mouth
c.rect(15, 26, 16, 31, (126, 96, 60))                   # roster colour, as a tie
c.vline(15, 26, 31, (92, 68, 40))
c.rect(14, 25, 17, 26, (146, 112, 70))                  # its knot
c.px(13, 25, INK); c.px(18, 25, INK)
finish(c, (226, 210, 186), (126, 96, 60))
save(c, 'ben')

# =====================================================================
# Grace — works in a pair with Dave and never stops moving. Ponytail
# thrown sideways, scarf, open grin. Roster colour #e8c878.
# =====================================================================
c = Canvas(32, 32)
scaffold(c, P['sk_hi'], P['sk'], P['coat'], P['coat_hi'], P['coat_lo'], (242, 200, 124))
HAIR, HAIR_HI, HAIR_LO = (214, 160, 70), (242, 202, 124), (163, 112, 44)
c.ellipse(27, 16, 3.5, 6, INK)                          # ponytail, mid-swing
c.ellipse(27, 16, 2.5, 5, HAIR)
c.ellipse(27, 13, 1.5, 2, HAIR_HI)
c.ellipse(15.5, 8, 8.5, 6, INK)                         # crown
c.ellipse(15.5, 8, 7.5, 5, HAIR)
c.ellipse(11, 5, 4, 2.5, HAIR_HI)
c.rect(6, 8, 9, 18, INK)                                # sweep past the ear
c.rect(7, 8, 9, 17, HAIR)
c.vline(9, 9, 16, HAIR_LO)
for i in range(9):                                      # fringe, swept to her left
    c.px(11 + i, 9 + i // 4, HAIR)
    c.px(11 + i, 10 + i // 4, HAIR_LO)
eyes(c, lash=True)
nose(c, 17, P['sk'])
c.hline(13, 18, 19, INK)                                # open grin
c.hline(14, 17, 20, P['white'])
c.px(12, 18, INK); c.px(19, 18, INK)
# Scarf: one band, one tail. Anything more at 32px turns to confetti.
SCARF, SCARF_HI, SCARF_LO = (228, 118, 86), (250, 158, 122), (190, 84, 58)
c.rect(8, 25, 23, 28, SCARF)
c.hline(9, 22, 25, SCARF_HI)
c.frame(8, 25, 23, 28, INK)
c.rect(18, 28, 22, 31, SCARF_LO)                        # its loose end
c.vline(19, 29, 31, SCARF)
c.frame(18, 28, 22, 31, INK)
finish(c, (246, 226, 178), (168, 116, 28))
save(c, 'grace')

# =====================================================================
# Smith — the professor. Horseshoe of white hair, full beard, half-rim
# readers, a cardigan rather than a lab coat. Roster colour #534ab7.
# =====================================================================
c = Canvas(32, 32)
CARD, CARD_HI, CARD_LO = (109, 100, 190), (142, 133, 216), (76, 68, 148)
scaffold(c, P['sk'], P['sk_lo'], CARD, CARD_HI, CARD_LO, (62, 55, 124))
HAIR, HAIR_LO = (232, 232, 238), (172, 174, 188)
c.ellipse(15.5, 19, 7.5, 5.5, INK)                      # beard, jaw to jaw
c.ellipse(15.5, 19, 6.5, 4.5, HAIR)
c.ellipse(15.5, 17, 5, 2.5, HAIR_LO)
c.ellipse(15.5, 14, 5, 3.5, P['sk'])                    # cut it back off the cheeks
c.ellipse(15.5, 8, 8.5, 6, INK)                         # horseshoe of hair
c.ellipse(15.5, 8, 7.5, 5, HAIR)
c.ellipse(15.5, 6, 5, 3.5, P['sk_lo'])                  # bald crown
c.ellipse(15.5, 5, 4, 2.5, P['sk'])
c.rect(7, 9, 9, 16, HAIR); c.rect(22, 9, 24, 16, HAIR)
c.vline(7, 10, 15, HAIR_LO); c.vline(24, 10, 15, HAIR_LO)
c.hline(10, 13, EYE_Y - 4, HAIR_LO)                     # heavy brows
c.hline(18, 21, EYE_Y - 4, HAIR_LO)
eyes(c)
rect_glasses(c, INK, P['glass'])
eyes(c)
nose(c, 17, P['sk_lo'])
c.hline(12, 19, 17, HAIR)                               # moustache
c.hline(13, 18, 18, HAIR_LO)
c.hline(14, 17, 19, INK)                                # the mouth under it
finish(c, (214, 208, 236), (83, 74, 183))
save(c, 'smith')

print('characters ok')
