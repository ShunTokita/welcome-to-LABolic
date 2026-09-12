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
