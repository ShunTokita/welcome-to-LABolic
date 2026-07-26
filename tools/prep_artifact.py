#!/usr/bin/env python3
"""Strip the document wrapper so the page can be published as an Artifact.

Usage: prep_artifact.py <inlined.html> <output.html>

Artifact wraps the supplied file in its own <!doctype>/<head>/<body>, so the
game's own document-level tags would end up nested one level deep. Removing
them lets the content merge into the host skeleton instead. The Google
Analytics tag goes too: the CSP blocks it anyway, and dropping it keeps the
console clean and preview loads out of the real property.
"""
import pathlib
import re
import sys


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    html = src.read_text(encoding="utf-8")

    # Google Analytics: the loader tag plus the gtag() bootstrap that follows.
    html = re.sub(
        r"<!-- Google tag \(gtag\.js\) -->\s*<script async src=\"https://www\.googletagmanager\.com[^\"]*\"></script>\s*<script>.*?</script>",
        "",
        html,
        flags=re.DOTALL,
    )
    if "googletagmanager" in html:
        raise SystemExit("google analytics tag survived the strip — check the pattern")

    # Document-level tags only; the inner <title>/<meta>/<style> stay put.
    for pattern in (
        r"<!DOCTYPE html>",
        r"<html[^>]*>",
        r"</html>",
        r"<head[^>]*>",
        r"</head>",
        r"<body[^>]*>",
        r"</body>",
    ):
        html = re.sub(pattern, "", html, flags=re.IGNORECASE)

    html = html.strip() + "\n"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
