"""Rounded panels — the one shape both device sprites are built from."""


def _corner_skip(x0, y0, x1, y1, r):
    """The cells a rounded rect must leave alone. They are *skipped*, never
    erased: a corner cut into a panel has to reveal the panel behind it, not
    punch a hole through to the background."""
    skip = set()
    for dx in range(r):
        for dy in range(r):
            if dx + dy < r:
                skip.add((x0 + dx, y0 + dy)); skip.add((x1 - dx, y0 + dy))
                skip.add((x0 + dx, y1 - dy)); skip.add((x1 - dx, y1 - dy))
    return skip


def round_rect(cv, x0, y0, x1, y1, col, r=2):
    skip = _corner_skip(x0, y0, x1, y1, r)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in skip:
                cv.px(x, y, col)


def panel(cv, x0, y0, x1, y1, fill, ink, r=2):
    """A rounded rect with a 1px ink border. Drawn as ink-then-fill so the
    border follows the rounding instead of being traced afterwards."""
    round_rect(cv, x0, y0, x1, y1, ink, r)
    round_rect(cv, x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill, max(0, r - 1))


def under(cv, x, y, col):
    """Paint only where nothing has been drawn — used for ground shadows,
    which must never receive an outline."""
    if (x, y) not in cv.d:
        cv.px(x, y, col)


def shadow_ellipse(cv, cx, cy, rx, ry, col):
    for y in range(cv.h):
        for x in range(cv.w):
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1.0:
                under(cv, x, y, col)


def box(cv, x0, y0, x1, y1, top_h, ramp, ink):
    """A rectangular solid in the house projection: a lit top face of top_h
    rows, a mid front face, and a shaded right edge. No side face — see
    tools/pixelart/spec.py for why."""
    cv.rect(x0, y0, x1, y1, ink)
    if top_h:
        cv.rect(x0 + 1, y0 + 1, x1 - 1, y0 + top_h, ramp['top'])
    cv.rect(x0 + 1, y0 + top_h + 1, x1 - 1, y1 - 1, ramp['base'])
    cv.vline(x0 + 1, y0 + top_h + 1, y1 - 1, ramp['lit'])
    cv.vline(x1 - 1, y0 + 1, y1 - 1, ramp['shade'])


def ramp(top, lit, base, shade):
    return {'top': top, 'lit': lit, 'base': base, 'shade': shade}


def drop_shadow(cv, col, dx=1, dy=1):
    """One pixel of cast shadow down and to the right of the silhouette.

    The lab floor at Lv4 is bright enough that a cream cabinet sits within a
    hair of it in value; darkening the cabinet does not help, because the
    floor's luminance falls inside the body ramp and moving the ramp only
    changes which step collides. What restores the separation is depth, so
    the devices cast.
    """
    add = []
    for (x, y), c in cv.d.items():
        if len(c) == 4 and c[3] < 255:
            continue                       # shadows do not cast shadows
        if (x + dx, y + dy) not in cv.d:
            add.append((x + dx, y + dy))
    for p in add:
        cv.px(p[0], p[1], col)


def contact_shadow(cv, col, reach=5, spread=1):
    """A band on the bottom row, but only under the columns the sprite
    actually stands in. A full-width band reads as a plinth the device does
    not have — a microscope and a four-tile rack do not touch the floor over
    the same span."""
    y = cv.h - 1
    feet = {x for (x, yy), c in cv.d.items()
            if yy >= cv.h - reach and not (len(c) == 4 and c[3] < 255)}
    for x in sorted(feet):
        for dx in range(-spread, spread + 1):
            under(cv, x + dx, y, col)
