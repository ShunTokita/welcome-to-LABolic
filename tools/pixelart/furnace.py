"""Furnace — Lv1, footprint one lab tile.

Two sprites are emitted from one description:

  furnace.png       16x16 — the sprite fits inside its footprint
  furnace_tall.png  16x32 — the same machine drawn a tile taller, overhanging
                            upward, the way the 1x2 characters do

The second exists because of what the mock floor shows: a person is 16x32 and
a Lv1 device confined to 16x16 ends up half their height, so a furnace reads
as a countertop appliance. Overhang costs one CSS change (.equip currently
clips its sprite) and no change to collision, since the footprint is
unchanged. Both are kept so the two can be judged side by side.

Front elevation plus a top face, per tools/pixelart/spec.py. Transparent
background, contact shadow only: a device carrying its own ground would tile
visibly against the floor grid.

The rule that matters at this size: ink draws the outer silhouette and nothing
else. Every interior edge is a step in value instead, because a 1px ink line
inside a 12px face eats an eighth of the form.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import Canvas, P
from pixshapes import shadow_ellipse

OUT = os.path.join(HERE, '..', '..', 'assets', 'pixel')
ink = P['ink']

PORT = ['.ooo.',
        'oaabo',
        'oabbo',
        'obbbo',
        '.ooo.']


def draw(height):
    """height is 16 or 32; every landmark is measured up from the floor."""
    c = Canvas(16, height)
    floor = height - 1                    # the shadow row
    body_bot = floor - 1                  # feet
    body_top = 5 if height == 32 else 2
    flue_top = 0
    top_face = body_top + (3 if height == 32 else 2)   # last row of the top face
    seam = top_face + 1
    door_top = seam + (3 if height == 32 else 2)
    door_bot = body_bot - 1

    # cabinet silhouette
    c.rect(1, body_top, 14, body_bot, ink)

    # Three flat steps, brightest on top, describe the whole box: top face,
    # front face, and the door sunk into it.
    c.rect(2, body_top + 1, 13, top_face, P['body_hi'])
    c.vline(13, body_top + 1, top_face, P['body'])        # the top's right edge turns away
    c.hline(2, 13, seam, P['body_dk'])                    # front/top seam
    c.rect(2, seam + 1, 13, body_bot - 1, P['body'])
    c.vline(2, seam + 1, body_bot - 1, P['body_hi'])      # lit left edge
    c.vline(13, seam + 1, body_bot - 1, P['body_dk'])     # shaded right edge

    # door, set into the front face
    c.rect(3, door_top, 12, door_bot, P['body_lo'])
    c.hline(3, 12, door_top, P['body_dk'])                # recess shadow, top...
    c.vline(3, door_top, door_bot, P['body_dk'])          # ...and left

    # Flue, drawn after the top face and standing ON it. Its base sits one row
    # short of the top face's front edge, so a strip of the top surface still
    # reads in front of the pipe. Rising from the silhouette's upper edge
    # instead — as the first draft did — puts the chimney behind the machine.
    flue_base = top_face - 1
    c.rect(6, flue_top, 9, flue_base, ink)                    # pipe silhouette
    c.rect(7, flue_top + 1, 8, flue_base, P['met_lo'])        # bare metal, not enamel
    c.vline(7, flue_top + 1, flue_base, P['met'])             # lit left edge
    if height == 32:
        c.rect(5, flue_base, 10, flue_base, ink)              # collar where it meets the top
        c.hline(6, 9, flue_base, P['met_lo'])

    port_y = (door_top + door_bot) // 2 - 2
    c.stamp(PORT, {'o': ink, 'a': P['hot_a'], 'b': P['hot_b']}, ox=5, oy=port_y)

    if height == 32:
        # A control strip only earns its pixels on the tall sprite; at 16px
        # the same four pixels read as dirt.
        c.rect(3, seam + 1, 12, door_top - 2, P['body_dk'])
        c.hline(4, 11, seam + 2, P['met'])
        c.px(4, seam + 2, P['hot_b'])
        c.px(6, seam + 2, P['met_hi'])
        c.px(11, seam + 2, P['hot_a'])
    else:
        c.px(11, door_top + 1, P['hot_b'])                # indicator lamp

    # feet
    c.rect(2, floor, 4, floor, ink)
    c.rect(11, floor, 13, floor, ink)
    shadow_ellipse(c, 7.5, floor, 7, 0.6, P['shadow'])
    return c


for h, name in ((16, 'furnace.png'), (32, 'furnace_tall.png')):
    cv = draw(h)
    cv.save(os.path.join(OUT, name))
    cv.save(os.environ['SCRATCH'] + '/%s_x12.png' % name[:-4], scale=12)
print('furnace 16x16 + 16x32 ok')
