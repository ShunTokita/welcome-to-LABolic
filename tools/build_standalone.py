#!/usr/bin/env python3
"""Inline every assets/ reference into a single self-contained HTML file.

Usage: build_standalone.py <source.html> <output.html>

Artifact pages are served under a CSP that blocks every external host, so the
relative assets/ paths that work on GitHub Pages resolve to nothing there.
Rewriting each reference as a data: URI keeps the preview visually identical.
"""
import base64
import pathlib
import re
import sys

# Extensions lie: 14 of the 35 files are JPEG despite a .png name, so the MIME
# type comes from the magic bytes rather than the filename.
MAGIC = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),
    (b"<svg", "image/svg+xml"),
    (b"<?xml", "image/svg+xml"),
]


def mime_of(data: bytes) -> str:
    for sig, mime in MAGIC:
        if data.startswith(sig):
            return mime
    raise SystemExit(f"unrecognised image format (first bytes: {data[:8]!r})")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    root = src.parent
    html = src.read_text(encoding="utf-8")

    paths = sorted(set(re.findall(r"assets/[A-Za-z0-9_/.-]+", html)))
    if not paths:
        raise SystemExit("no assets/ references found — is this the right file?")

    # Longest first so assets/icon/x.png is never clobbered by a prefix match.
    total = 0
    for path in sorted(paths, key=len, reverse=True):
        blob = (root / path).read_bytes()
        if not blob:
            raise SystemExit(f"empty asset: {path}")
        uri = f"data:{mime_of(blob)};base64,{base64.b64encode(blob).decode()}"
        html = html.replace(path, uri)
        total += len(blob)

    leftover = re.findall(r"assets/[A-Za-z0-9_/.-]+", html)
    if leftover:
        raise SystemExit(f"unresolved references remain: {leftover[:5]}")

    out.write_text(html, encoding="utf-8")
    print(f"inlined {len(paths)} assets ({total/1e6:.2f} MB) -> {out}")
    print(f"output size: {out.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
