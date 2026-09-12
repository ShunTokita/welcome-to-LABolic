"""The projection and grid rules every sprite in assets/pixel/ obeys.

The painted assets were generated one at a time without a stated viewpoint, so
they mix straight elevations (AGT, PSS, QAA, MPSS, casting) with obliques that
recede in different directions (furnace recedes left, laser deposition right,
PC is nearly top-down). Pixel art cannot absorb that: at 16px a device that
disagrees with its neighbour about where "up" is reads as a mistake rather
than as style. So the rules are fixed here, in one place, and imported.

PROJECTION — front elevation plus a top face, left/right symmetric
    Vertical lines stay vertical, horizontal lines stay horizontal, and there
    is no vanishing point. Depth is shown only by a top face stacked directly
    above the front face, never by a side face. TOP_RATIO fixes how deep that
    top face looks relative to the object's width.

    Consequences worth knowing: a sprite can be mirrored horizontally for
    free, two devices sitting side by side never disagree about the direction
    of depth, and at 16px nothing is spent on a side face that would only be
    two or three pixels wide.

LIGHT — from the upper left, fixed
    Top face lightest, front face mid, the right edge and everything under an
    overhang in shade. Every material therefore needs four steps plus ink.

GRID — 16px of art per lab tile
    The game's tile is TILE_DESKTOP px wide on desktop and TILE_MOBILE on
    mobile; both are integer multiples of ART_TILE, so a sprite scales by a
    whole number on either. Zoom has to be snapped to thirds for that to hold
    at every zoom step (see docs in the preview sheet).
"""

ART_TILE = 16          # pixels of art per lab tile
TILE_DESKTOP = 48      # = ART_TILE * 3
TILE_MOBILE = 32       # = ART_TILE * 2
TOP_RATIO = 0.25       # visible depth of a top face, as a fraction of width


def cell(w_tiles, h_tiles):
    """Sprite size in pixels for a device that occupies w x h lab tiles."""
    return w_tiles * ART_TILE, h_tiles * ART_TILE


# Device footprints come from the game's own level table
# (labolic-playtest-40.html:3991).
FOOTPRINT = {1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (3, 2), 5: (4, 4)}

# Characters occupy one tile on the floor but are drawn a tile and a half
# tall. Two full tiles made them read as stretched — the torso especially —
# and the extra height bought nothing the silhouette needed.
CHARACTER = (ART_TILE, ART_TILE * 3 // 2)      # 16 x 24, footprint still 1x1


def top_depth(width):
    """How many rows of top face a form this wide should show."""
    return max(2, round(width * TOP_RATIO))


def ramp(top, front, base, shade):
    """Bundle a material's four steps in the order the light rule uses them."""
    return {'top': top, 'lit': front, 'base': base, 'shade': shade}
