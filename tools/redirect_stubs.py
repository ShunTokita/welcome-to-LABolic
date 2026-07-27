#!/usr/bin/env python3
"""Send superseded builds back to the entry point.

Usage: redirect_stubs.py <live-version-number>

A player who bookmarked labolic-playtest-29.html, or who just refreshes the
tab they already had open, keeps playing that build forever without ever
learning a newer one shipped. Every version except the live one therefore
gets a stub at the top of <head> that bounces to index.html.

The target is index.html rather than the current version file, so shipping a
new build never requires rewriting the older ones — index.html is the single
place the "latest" pointer lives.

That indirection is also the one way this can loop: index.html points at the
live version, so the live version must never carry the stub. This script is
the only thing that adds or removes it, and it always strips the live version
first; tools/check.sh re-checks the invariant afterwards.

To pin an old build for a rollback playtest, delete its stub by hand — the
block is delimited by the markers below and nothing else in the file moves.
"""
import pathlib
import re
import sys

START = "<!-- LABOLIC-REDIRECT-START -->"
END = "<!-- LABOLIC-REDIRECT-END -->"

STUB = f"""{START}
<script>
/* Superseded build — see tools/redirect_stubs.py. Saves are keyed per origin
   in localStorage, not per file, so progress carries over the hop.
   Delete this block to pin this build for a rollback playtest. */
location.replace('index.html' + location.search + location.hash);
</script>
<noscript><meta http-equiv="refresh" content="0; url=index.html"></noscript>
{END}"""

BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
# Anchor after the charset declaration: a redirect this early never renders,
# but leaving the encoding first keeps the file well-formed if it ever does.
CHARSET_RE = re.compile(r'(<meta\s+charset=["\']?[^>"\']+["\']?\s*/?>)', re.IGNORECASE)


def strip(html: str) -> str:
    return BLOCK_RE.sub("", html)


def inject(html: str, path: pathlib.Path) -> str:
    html = strip(html)
    m = CHARSET_RE.search(html)
    if not m:
        raise SystemExit(f"error: no <meta charset> found in {path.name}")
    return html[: m.end()] + "\n" + STUB + html[m.end() :]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    live = sys.argv[1]
    root = pathlib.Path(__file__).resolve().parent.parent
    files = sorted(
        root.glob("labolic-playtest-*.html"),
        key=lambda p: int(re.search(r"(\d+)", p.name).group(1)),
    )
    live_file = root / f"labolic-playtest-{live}.html"
    if not live_file.exists():
        raise SystemExit(f"error: {live_file.name} not found")

    stubbed, cleared = [], None
    for f in files:
        html = f.read_text(encoding="utf-8")
        new = strip(html) if f == live_file else inject(html, f)
        if new != html:
            f.write_text(new, encoding="utf-8")
        if f == live_file:
            cleared = f.name
        elif START in new:
            stubbed.append(f.name)

    print(f"live (no stub): {cleared}")
    print(f"redirecting   : {len(stubbed)} file(s)" + (f" — {', '.join(stubbed)}" if stubbed else ""))


if __name__ == "__main__":
    main()
