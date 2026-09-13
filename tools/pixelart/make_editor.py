"""Build the browser dot editor from the template and the live assets.

The palette and the fourteen sprites are not typed into the HTML by hand —
they are read out of pixcore.py and assets/pixel/product/ and substituted in,
so the editor can never drift from what the game actually ships. Rerun it
after the sprites change.

    python3 tools/pixelart/make_editor.py    ->  build/pixel-editor.html
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import P
from products import SHIPPED

ROOT = os.path.join(HERE, '..', '..')
ART = os.path.join(ROOT, 'assets', 'pixel', 'product')
OUT = os.path.join(ROOT, 'build', 'pixel-editor.html')

# The order the Discovery list uses, so the editor's grid reads like the game's.
ORDER = ['brass', 'cupronickel', 'monel', 'invar', 'permalloy', 'nichrome',
         'ferritic_ss', 'austenitic_ss', 'ti_cr_beta', 'nitinol', 'inconel_like',
         'azoth', 'quintessence', 'lapis']

# Grouped the way the hand-drawn sprites use them, not alphabetically: picking
# a colour is picking a material, and the three steps of one material want to
# sit together.
GROUPS = [
    ('輪郭・地', ['ink', 'ink2', 'white', 'bg2', 'bg']),
    ('鋼・ステンレス', ['sil_hi', 'sil', 'sil_lo']),
    ('一般金属', ['met_hi', 'met', 'met_lo']),
    ('真鍮', ['brass_hi', 'brass', 'brass_lo']),
    ('銅', ['cu_hi', 'cu', 'cu_lo']),
    ('高温・炎', ['hot_a', 'hot_b', 'hot_c']),
    ('氷・水', ['ice_hi', 'ice', 'ice_lo', 'liq_hi', 'liq']),
    ('赤', ['red_hi', 'red', 'red_lo']),
    ('汚水・緑', ['grime', 'grime_lo', 'grn_hi', 'grn', 'grn_lo']),
    ('ガラス', ['glass', 'dglass']),
    ('紫', ['cry_hi', 'cry', 'cry_lo', 'glow']),
    ('青（発光）', ['ener_a', 'ener_b', 'ener_c']),
    ('黄土', ['och_hi', 'och', 'och_lo']),
    ('木', ['wood', 'wood_lo']),
    ('クリーム筐体', ['body_hi', 'body', 'body_lo', 'body_dk']),
    ('白衣・肌', ['coat_hi', 'coat', 'coat_lo', 'sk_hi', 'sk', 'sk_lo',
                  'sk_md', 'sk_md_lo', 'sk_dk', 'sk_dk_lo']),
]


def main():
    missing = [i for i in ORDER if not os.path.exists(os.path.join(ART, i + '.png'))]
    if missing:
        print('missing sprites:', ' '.join(missing))
        return 1
    assert set(ORDER) == SHIPPED, 'editor list and SHIPPED disagree'

    palette = []
    for name, v in P.items():
        if len(v) == 4 and v[3] != 255:          # the translucent shadow entries
            continue                             # are not paintable colours
        r, g, b = v[:3]
        palette.append({'name': name, 'hex': '#%02x%02x%02x' % (r, g, b),
                        'rgb': [r, g, b]})

    sprites = {}
    for did in ORDER:
        with open(os.path.join(ART, did + '.png'), 'rb') as f:
            sprites[did] = 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

    with open(os.path.join(HERE, 'editor_template.html'), encoding='utf-8') as f:
        html = f.read()
    html = html.replace('__PALETTE_JSON__', json.dumps(palette, ensure_ascii=False))
    html = html.replace('__GROUPS_JSON__', json.dumps(
        [{'label': lab, 'keys': keys} for lab, keys in GROUPS], ensure_ascii=False))
    html = html.replace('__SPRITES_JSON__', json.dumps(sprites))
    html = html.replace('__ORDER_JSON__', json.dumps(ORDER))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('%s  %d bytes  |  %d colours, %d sprites'
          % (OUT, len(html.encode()), len(palette), len(sprites)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
