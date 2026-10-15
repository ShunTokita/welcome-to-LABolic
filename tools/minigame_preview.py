#!/usr/bin/env python3
"""Build single-file previews of the minigames, ready to publish as Artifacts.

Each minigame in minigames/ links the shared mg-*.css / mg-*.js files next to
it. An Artifact is one file behind a CSP that blocks other hosts, so those
links are inlined here. Output goes to build/mg-<name>.html (git-ignored).

Usage: python3 tools/minigame_preview.py [name ...]   (default: all games)
       e.g. python3 tools/minigame_preview.py sem tem
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'minigames')
OUT = os.path.join(ROOT, 'build')

# The original prototype is kept for reference, not previewed.
SKIP = {'sem-proto'}


def inline(path):
    with open(path, encoding='utf-8') as f:
        s = f.read()

    def read(name):
        with open(os.path.join(SRC, name), encoding='utf-8') as f:
            return f.read()

    s = re.sub(r'<link rel="stylesheet" href="([^"/]+\.css)">',
               lambda m: '<style>\n' + read(m.group(1)) + '</style>', s)
    s = re.sub(r'<script src="([^"/]+\.js)"></script>',
               lambda m: '<script>\n' + read(m.group(1)) + '</script>', s)
    return s


def main(names):
    if not names:
        names = sorted(f[:-5] for f in os.listdir(SRC)
                       if f.endswith('.html') and f[:-5] not in SKIP)
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        src = os.path.join(SRC, name + '.html')
        if not os.path.isfile(src):
            sys.exit(f'error: {src} not found')
        dst = os.path.join(OUT, f'mg-{name}.html')
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(inline(src))
        print(dst)


if __name__ == '__main__':
    main(sys.argv[1:])
