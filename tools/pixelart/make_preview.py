"""Build the pixel-art review sheet as a single self-contained HTML file.

Artifact pages sit behind a CSP that blocks every external host, so every PNG
travels inside the file as a data URI. Output goes to build/, which is
git-ignored — the same convention tools/preview.sh follows.
"""
import base64, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixcore import P
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def uri(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


A = {k: uri(v) for k, v in {
    'scene':      'build/lab-scene.png',
    'px_furnace': 'assets/pixel/furnace.png',
    'px_furn_t':  'assets/pixel/furnace_tall.png',
    'px_agt':     'assets/pixel/AGT.png',
    'og_furnace': 'assets/furnace.png',
    'og_agt':     'assets/AGT.png',
}.items()}
for cid in ('ben', 'grace', 'smith'):
    A['sheet_' + cid] = uri('assets/pixel/char/%s.png' % cid)
for fl in ('lv1', 'lv2', 'lv3', 'lv4_a', 'lv4_b', 'lv4_c', 'lv4_d'):
    A['scene_' + fl] = uri('build/lab-scene-%s.png' % fl)
    A['tile_' + fl] = uri('assets/pixel/floor/%s.png' % fl)


# Contrast of each Lv4 candidate against the three steps of the device body
# palette. WCAG relative luminance; these are not text ratios, but they are
# the right instrument for "can you still see the cabinet against the floor".
def _lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)))
    return (lb + 0.05) / (la + 0.05)


LV4 = [('lv4_a', '#b8ad8a', (184, 173, 138), '現行'),
       ('lv4_b', '#c5ba97', (197, 186, 151), '推奨'),
       ('lv4_c', '#d2c7a6', (210, 199, 166), ''),
       ('lv4_d', '#ded4b7', (222, 212, 183), '')]
# Read the device palette rather than restating it: a second copy of these
# three colours is a second thing to keep in step with pixcore.
BODY = [('正面 body', P['body']), ('影 body_lo', P['body_lo']),
        ('濃影 body_dk', P['body_dk'])]

lv4_rows = []
for key, hexv, rgb, tag in LV4:
    cells = ''
    for _, part in BODY:
        r = contrast(rgb, part)
        cls = ' class="bad"' if r < 1.15 else (' class="n"' if r < 1.3 else ' class="n ok"')
        cells += f'<td{cls}>{r:.2f}</td>'
    label = f'{hexv}<span class="pill">{tag}</span>' if tag else hexv
    lv4_rows.append(f'<tr><td class="n">{label}</td>{cells}</tr>')
lv4_rows = '\n'.join(lv4_rows)

C = {key: [contrast(rgb, part) for _, part in BODY] for key, _, rgb, _ in LV4}

FLOORS = [('lv1', '木造', '長尺の床板と木目。突きつけ目地は入れていない——8pxごとの横目地に16pxごとの縦目地が重なると矩形が並び、色を変えても煉瓦に見えるため'),
          ('lv2', 'コンクリート打ちっぱなし', '骨材のまだらと、細いヒビ2本。タイル境界で途切れないよう、ヒビは32pxタイルの内側に収めている'),
          ('lv3', '緑のラバー床', '8px間隔の丸い突起。実験室用ラバーシートの定番で、レベルが上がって予算が付いた最初の兆候'),
          ('lv4_b', 'クリーム色シートビニル', '控えめな2色のフレック。最も長く見る床なので、模様は意図的に静かにしてある')]
floor_blocks = '\n'.join(f'''
      <div class="device">
        <h3>Lv{i + 1} {label}<span class="tag">assets/pixel/floor/{key}.png · 32×32</span></h3>
        <p>{note}</p>
        <div class="floorrow">
          <figure class="plate"><div class="art" style="padding:0"><img class="px" src="{A['tile_' + key]}" alt="" width="128" height="128"></div><figcaption>タイル ×4</figcaption></figure>
          <figure class="plate"><div class="art" style="padding:0"><img class="px" src="{A['scene_' + key]}" alt="Lv{i + 1}の床に置いた装置とキャラクター" width="416" height="192"></div><figcaption>×2 配置</figcaption></figure>
        </div>
      </div>''' for i, (key, label, note) in enumerate(FLOORS))

lv4_strip = '\n'.join(f'''
        <figure class="plate"><div class="art" style="padding:0"><img class="px" src="{A['scene_' + key]}" alt="{hexv}の床" width="416" height="192"></div><figcaption>{key.replace('lv4_', 'Lv4-')} {hexv}{' — ' + tag if tag else ''}</figcaption></figure>'''
    for key, hexv, rgb, tag in LV4)

AUDIT = [
    ('正面図・左右対称', 'casting, PSS, AGT, QAA, MPSS, TEM', 6),
    ('斜方投射・左右に振れる', 'arcmelt, laserdeposition, furnace, rolling, magnetizer, OM, SEM', 7),
    ('強い俯瞰', 'PC', 1),
]

CAST = [
    ('Ben',   'ben',   '#7e603c', '丸メガネ、切りっぱなしの前髪、大きめの白衣'),
    ('Grace', 'grace', '#e8c878', '横に流れるポニーテール、スカーフ'),
    ('Smith', 'smith', '#534ab7', '白い顎髭、半縁の老眼鏡、カーディガン'),
]

sheets = '\n'.join(f'''
      <article class="cast">
        <div class="cast-art"><img class="px" src="{A['sheet_' + cid]}" alt="{name}のスプライトシート" width="288" height="288"></div>
        <div class="cast-meta">
          <h3>{name}<span class="swatch" style="background:{col}"></span><span class="tag">assets/pixel/char/{cid}.png · 48×48</span></h3>
          <p>{note}</p>
          <dl class="kv">
            <div><dt>セル</dt><dd>16×24（足元1×1）</dd></div>
            <div><dt>列</dt><dd>正面 / 側面 / 背面</dd></div>
            <div><dt>行</dt><dd>歩行2フレーム</dd></div>
            <div><dt>実寸</dt><dd>48×72（デスクトップ）</dd></div>
          </dl>
          <div class="ingame">
            <figure><img class="px" src="{A['sheet_' + cid]}" alt="" style="width:144px;height:144px"><figcaption>×3 実寸</figcaption></figure>
            <figure><img class="px" src="{A['sheet_' + cid]}" alt="" style="width:96px;height:96px"><figcaption>×2 モバイル実寸</figcaption></figure>
          </div>
        </div>
      </article>''' for name, cid, col, note in CAST)

audit_rows = '\n'.join(
    f'<tr><td>{k}</td><td class="n">{n}</td><td class="files">{v}</td></tr>'
    for k, v, n in AUDIT)

HTML = f'''<title>LABolic ドット絵アセット</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Shippori+Mincho+B1:wght@700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
  :root {{
    --ground:#eceef4; --panel:#fff; --panel-2:#f5f6fa;
    --ink:#1b2039; --ink-2:#5d6484; --ink-3:#8a90aa;
    --line:#d2d7e4; --line-2:#e3e7f0;
    --accent:#b34e14; --accent-2:#5f47a0;
    --lab:#b8ad8a;
    --sans:"Zen Kaku Gothic New",-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;
    --serif:"Shippori Mincho B1",Georgia,"Hiragino Mincho ProN",serif;
    --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ground:#141721; --panel:#1c2030; --panel-2:#232839;
      --ink:#e7eaf4; --ink-2:#a0a8c4; --ink-3:#767e9c;
      --line:#2f354a; --line-2:#262b3c;
      --accent:#ee9346; --accent-2:#b094ea;
    }}
  }}
  :root[data-theme="dark"] {{
    --ground:#141721; --panel:#1c2030; --panel-2:#232839;
    --ink:#e7eaf4; --ink-2:#a0a8c4; --ink-3:#767e9c;
    --line:#2f354a; --line-2:#262b3c;
    --accent:#ee9346; --accent-2:#b094ea;
  }}

  body {{ background:var(--ground); color:var(--ink); font-family:var(--sans);
         font-size:15px; line-height:1.72; margin:0; }}
  .wrap {{ max-width:1020px; margin:0 auto; padding-inline:20px; padding-block:48px 72px; }}
  img {{ max-width:100%; }}
  .px {{ image-rendering:pixelated; image-rendering:crisp-edges; display:block; }}

  header.top {{ border-bottom:2px solid var(--ink); padding-bottom:20px; }}
  .kicker {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em;
             text-transform:uppercase; color:var(--accent); margin:0 0 8px; }}
  h1 {{ font-family:var(--serif); font-size:clamp(28px,5vw,42px); line-height:1.25;
        margin:0 0 10px; text-wrap:balance; }}
  .standfirst {{ margin:0; color:var(--ink-2); max-width:62ch; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px 20px; margin-top:16px;
           font-family:var(--mono); font-size:12px; color:var(--ink-3); }}
  .meta b {{ color:var(--ink-2); font-weight:600; }}

  section {{ margin-top:56px; }}
  .sec-head {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;
               border-bottom:1px solid var(--line); padding-bottom:8px; margin-bottom:26px; }}
  .sec-head h2 {{ font-family:var(--serif); font-size:22px; margin:0; }}
  .sec-head span {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                    letter-spacing:.08em; }}
  .lede {{ margin:0 0 22px; color:var(--ink-2); max-width:64ch; }}

  /* the lab floor mock — the headline of the sheet, so it gets the full width */
  .scene {{ background:var(--lab); border:2px solid #6b5c3c; overflow-x:auto; }}
  .scene img {{ width:624px; height:288px; max-width:none; }}
  .scene-cap {{ display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap;
                font-family:var(--mono); font-size:11px; color:var(--ink-3); margin-top:8px; }}

  .device {{ margin-bottom:38px; }}
  .device > h3 {{ font-size:17px; margin:0 0 4px; }}
  .device > h3 .tag {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       margin-left:10px; font-weight:500; }}
  .device > p {{ margin:0 0 16px; color:var(--ink-2); max-width:62ch; font-size:14px; }}
  .floorrow {{ display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start; }}
  .lv4strip {{ display:flex; flex-direction:column; gap:14px; }}
  .pill {{ font-family:var(--mono); font-size:9.5px; letter-spacing:.06em; margin-left:8px;
           padding:1px 6px; border:1px solid var(--accent-2); color:var(--accent-2); }}
  td.ok {{ color:var(--ink-2); }}
  td.bad {{ color:var(--accent); font-weight:600; }}
  .plates {{ display:flex; flex-wrap:wrap; gap:16px; align-items:flex-end; }}
  .plate {{ margin:0; background:var(--panel); border:1px solid var(--line); }}
  .plate .art {{ display:grid; place-items:center; padding:12px; background:var(--lab); }}
  .plate figcaption {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       padding:7px 11px; border-top:1px solid var(--line-2); }}

  .cast {{ display:grid; grid-template-columns:auto 1fr; gap:24px; align-items:start;
           padding:24px 0; border-top:1px solid var(--line-2); }}
  .cast:first-of-type {{ border-top:0; padding-top:0; }}
  .cast-art {{ background:var(--lab); border:1px solid var(--line); padding:8px; }}
  .cast-meta h3 {{ font-size:17px; margin:0 0 4px; display:flex; align-items:center;
                   gap:8px; flex-wrap:wrap; }}
  .cast-meta h3 .tag {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                        font-weight:500; }}
  .swatch {{ width:11px; height:11px; border:1px solid var(--ink); display:inline-block; }}
  .cast-meta > p {{ margin:0 0 14px; color:var(--ink-2); font-size:14px; max-width:50ch; }}
  .kv {{ display:flex; flex-wrap:wrap; gap:4px 26px; margin:0 0 16px; }}
  .kv > div {{ display:flex; gap:8px; align-items:baseline; }}
  .kv dt {{ font-family:var(--mono); font-size:10px; letter-spacing:.05em;
            color:var(--ink-3); }}
  .kv dd {{ margin:0; font-size:13px; font-variant-numeric:tabular-nums; }}
  .ingame {{ display:flex; gap:20px; align-items:flex-end; }}
  .ingame figure {{ margin:0; background:var(--lab); padding:6px; border:1px solid var(--line); }}
  .ingame figcaption {{ font-family:var(--mono); font-size:10px; color:var(--ink-3);
                        margin-top:5px; background:var(--panel); }}

  .tablewrap {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; min-width:520px;
           font-variant-numeric:tabular-nums; }}
  th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid var(--line-2);
            font-size:13.5px; vertical-align:top; }}
  th {{ font-family:var(--mono); font-size:11px; letter-spacing:.06em; color:var(--ink-3);
        text-transform:uppercase; border-bottom:1px solid var(--line); font-weight:600; }}
  td.n {{ font-family:var(--mono); }}
  td.files {{ font-family:var(--mono); font-size:11.5px; color:var(--ink-2); }}
  td.act {{ color:var(--accent); }}

  .rules {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1px;
            background:var(--line); border:1px solid var(--line); }}
  .rule {{ background:var(--panel); padding:16px 18px; }}
  .rule h4 {{ margin:0 0 6px; font-size:13px; font-family:var(--mono);
              letter-spacing:.04em; color:var(--accent-2); }}
  .rule p {{ margin:0; font-size:13.5px; color:var(--ink-2); }}

  .note {{ background:var(--panel-2); border-left:3px solid var(--accent);
           padding:16px 18px; margin-top:24px; }}
  .note h4 {{ margin:0 0 6px; font-size:14px; }}
  .note p {{ margin:0; color:var(--ink-2); font-size:14px; max-width:64ch; }}
  .note p + p {{ margin-top:10px; }}
  code {{ font-family:var(--mono); font-size:.88em; background:var(--panel);
          border:1px solid var(--line-2); padding:1px 5px; }}

  footer {{ margin-top:56px; padding-top:18px; border-top:1px solid var(--line);
            font-family:var(--mono); font-size:11.5px; color:var(--ink-3); }}
  footer ul {{ margin:8px 0 0; padding-left:18px; }}

  @media (max-width:620px) {{ .cast {{ grid-template-columns:1fr; }} }}
</style>

<div class="wrap">
  <header class="top">
    <p class="kicker">welcome-to-LABolic / branch pixelart-trial</p>
    <h1>2Dドット絵アセット 試作</h1>
    <p class="standfirst">投射方向を「正面＋上面・左右対称」に統一し、アート1タイル＝16pxのグリッドで描いた第3稿。キャラクターは足元1×1マス・グラフィックは1×1.5マスの全身スプライトです。ラボ以外の画面（会話イベント、Labo Chat、ロスター、雇用カード）のアバターは現行のイラストを踏襲するため、ドット絵化していません。ゲーム本体には組み込んでいません。</p>
    <div class="meta">
      <span><b>アートグリッド</b> 16px/タイル</span>
      <span><b>実寸</b> ×3 = 48px（デスクトップ）/ ×2 = 32px（モバイル）</span>
      <span><b>生成</b> tools/pixelart/*.py</span>
    </div>
  </header>

  <section>
    <div class="sec-head"><h2>ラボ床</h2><span>×3 実寸（デスクトップ 48px/タイル）</span></div>
    <p class="lede">左から、1×1に収めたFurnace、同じ足元のまま上へ1マスはみ出したFurnace、Ben、Smith、AGT、Grace。床とグリッドはゲームの <code>.lab</code> の値をそのまま使っています。</p>
    <div class="scene"><img class="px" src="{A['scene']}" alt="ドット絵アセットを並べたラボ床のモック"></div>
    <div class="scene-cap"><span>13×6タイル / アート208×96px</span><span>装置・キャラクターとも背景は透過、接地影のみ</span></div>
    <div class="note">
      <h4>ここで分かること — 1×1の装置はキャラクターの半分の高さになる</h4>
      <p>キャラクターが1×2になったことで、Lv1装置を1×1の枠に収めると人の腰までしかない調理家電のように見えます。左端と、その右の背の高い版が同じ機械です。</p>
      <p>足元の占有マスは1×1のまま、スプライトだけ上へ1マスはみ出させれば解決します。当たり判定も配置ロジックも変わりません。必要なのは <code>.equip</code> がスプライトをクリップしている現状（<code>overflow:hidden</code> 前提で <code>.eq-sprite</code> が <code>inset:0</code>）を、上方向だけ開けることです。AGTも同じ理由で3×2のままでは低く見えるので、採用するなら全装置に一律で適用するのが筋だと考えます。</p>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>投射規約</h2><span>tools/pixelart/spec.py</span></div>
    <p class="lede">現行14点は投射方向が混在していました。ドット絵では隣り合った装置が「奥」の方向について食い違うと、様式ではなく作画ミスに見えます。</p>
    <div class="tablewrap">
      <table>
        <thead><tr><th>現行アートの分類</th><th>点数</th><th>該当ファイル</th></tr></thead>
        <tbody>{audit_rows}</tbody>
      </table>
    </div>
    <div class="rules" style="margin-top:22px">
      <div class="rule"><h4>PROJECTION</h4><p>正面図＋上面。垂直線は垂直、水平線は水平、消失点なし。側面は描かず、奥行きは正面の真上に積む上面だけで示す。</p></div>
      <div class="rule"><h4>TOP_RATIO = 0.25</h4><p>上面の見かけの深さは対象の幅の1/4。幅12pxの箱なら上面3px。</p></div>
      <div class="rule"><h4>LIGHT</h4><p>左上から固定。上面が最も明るく、正面が中間、右端と庇の下が影。materialごとに4段＋インク。</p></div>
      <div class="rule"><h4>MIRRORING</h4><p>左右対称なので水平反転が無料。隣接する装置どうしが奥行きの向きで矛盾しない。</p></div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>装置</h2><span>ドット絵 ↔ 現行アート</span></div>

    <div class="device">
      <h3>Furnace<span class="tag">Lv1 · 足元1×1 · assets/pixel/furnace.png</span></h3>
      <p>16pxが買えるのは4つだけ——箱、その上面、覗き窓のある扉、煙突。絵にあるヒンジ・奥にずれた第二の筐体・4本の脚は、ここでは予算切れです。背の高い版では余った1マス分を操作パネルと縦長の扉に使っています。</p>
      <p>煙突は上面の上に立っています。根元は上面の手前端より1行内側に置き、パイプの手前に上面が1行残るようにしました。第1稿のようにシルエットの上端から生やすと、煙突が筐体の背後から出ているように見えます。</p>
      <div class="plates">
        <figure class="plate"><div class="art"><img class="px" src="{A['px_furnace']}" alt="Furnace 16×16" width="128" height="128"></div><figcaption>16×16 ×8</figcaption></figure>
        <figure class="plate"><div class="art"><img class="px" src="{A['px_furn_t']}" alt="Furnace 16×32" width="128" height="256"></div><figcaption>16×32 ×8（上へはみ出す版）</figcaption></figure>
        <figure class="plate"><div class="art" style="background:none"><img src="{A['og_furnace']}" alt="現行アート" width="200" height="200"></div><figcaption>現行アート 1036×1036</figcaption></figure>
      </div>
    </div>

    <div class="device">
      <h3>AGT<span class="tag">Lv4 · 3×2 · assets/pixel/AGT.png</span></h3>
      <p>輪は垂直な円盤なので上面を持ちません。投射を担っているのは2本の塔の台座と柱頭で、こちらは箱です。原子は3軌道ではなく直交2軌道にしました。3軌道は視野が24px程度ないと、各楕円の平らな端が7px前後の直線として量子化され、互いに癒着してアスタリスクになります。</p>
      <div class="plates">
        <figure class="plate"><div class="art"><img class="px" src="{A['px_agt']}" alt="AGT 48×32" width="384" height="256"></div><figcaption>48×32 ×8</figcaption></figure>
        <figure class="plate"><div class="art" style="background:none"><img src="{A['og_agt']}" alt="現行アート" width="280" height="189"></div><figcaption>現行アート 1288×868</figcaption></figure>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>キャラクター — ラボ床スプライト</h2><span>1×2タイル / 3方向 × 歩行2フレーム</span></div>
    <p class="lede">現行の <code>.character</code> は0.55タイルの円です。これを全身像に置き換えます。足元の占有は1×1のまま、グラフィックは半マス上へはみ出します。側面は右向きだけを描き、左向きはCSSの水平反転で作ります——左右対称の投射を選んだ利点がここで効きます。2フレームで足りるのは、タイル間の移動を既存の <code>transition: 0.15s</code> が担っているためです。</p>
    <p class="lede">プロポーションは頭8行・胴7行・脚6行。16×32だった稿は胴に11行、頭に12行を与えていて、ずんぐりではなく引き伸ばされた人物に見えていました。この大きさでは頭は縦より横がわずかに広く、胴は頭より短いほうが収まります。</p>
    <p class="lede">目元には3行を充てています。首を2行から1行に詰め、頭の上端を1行上げて捻出しました。目の帯が1行しかないと眼鏡がただの黒い棒になり、BenとSmithが見分けられなくなります。いまBenは丸レンズとブリッジ、Smithは下縁のない半縁で、それぞれ3行を使っています。口は任意で、眼鏡や髭が下顔面をすでに担っているBenとSmithには置いていません——暗い2pxが増えるだけで濁るためです。</p>
    {sheets}
  </section>

  <section>
    <div class="sec-head"><h2>床</h2><span>ラボレベル別 / 32×32タイル</span></div>
    <p class="lede">床はプレイヤーが最も長く見る面なので、主張しないことが条件になります。レベル差は色だけでなく素材そのもので付けました。タイルを32×32（2×2マス）にしてあるのは、隣り合うマスで模様が変わり、16px周期の反復が目立たないようにするためです。32は16の倍数なのでグリッドとの整合は保たれます。</p>
    {floor_blocks}
    <div class="note">
      <h4>グリッド線について</h4>
      <p>現在ゲームは床の上に1pxのグリッドを重ねています（<code>.lab</code>、通常0.18・レイアウトモード0.4）。木目やラバーの突起の上に乗せると素材と干渉するので、通常時は切ってレイアウトモード専用にするのが良いと考えます。上の配置画像はいずれもグリッドなしです。</p>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Lv4の明るさ</h2><span>4案 / 装置との弁別</span></div>
    <p class="lede">Lv4は最も滞在時間が長いので、明るさを上げすぎると目が疲れます。加えて、上げていくと装置の筐体と床が同化します。下表は各案と筐体パレット3段とのコントラスト比（WCAG相対輝度）で、1.0が完全な同色です。</p>
    <div class="tablewrap">
      <table>
        <thead><tr><th>床</th><th>筐体 正面</th><th>筐体 影</th><th>筐体 濃影</th></tr></thead>
        <tbody>{lv4_rows}</tbody>
      </table>
    </div>
    <div class="note">
      <h4>bを推します</h4>
      <p><b>c は筐体の影側との比が {C['lv4_c'][1]:.2f}</b>、つまりFurnaceの陰になった右端が床と区別できません。d では正面の面そのものが {C['lv4_d'][0]:.2f} まで落ち、筐体が輪郭線だけで浮いた状態になります。b の最悪値は影側の {C['lv4_b'][1]:.2f} ですが、正面は {C['lv4_b'][0]:.2f} を保ち、濃紺の輪郭線がシルエットを担保します。</p>
      <p>ただし表を縦に見ると、これは明るさだけの問題ではありません。現行(a)ですでに濃影が {C['lv4_a'][2]:.2f} で床とほぼ同値です。床を明るくすると濃影は分離し、代わりに影側が沈む——筐体パレットの影の段が床の輝度帯を横切っているためで、どの明るさでも3段のどれかが床に近づきます。</p>
      <p>現行(a)より明るくしたいというご要望と、目の疲れ・弁別の両方を満たす上限が b です。これより明るくするなら、装置パレットの影側（<code>body_lo</code> / <code>body_dk</code>）を先に振り直し、床の輝度帯から離す必要があります。</p>
    </div>
    <div class="lv4strip">{lv4_strip}</div>
  </section>

  <section>
    <div class="sec-head"><h2>組み込みに必要なゲーム側の変更</h2><span>いずれも未実施</span></div>
    <div class="tablewrap">
      <table>
        <thead><tr><th>箇所</th><th>現在</th><th>変更後</th><th>理由</th></tr></thead>
        <tbody>
          <tr><td class="n">TILE_DESKTOP</td><td class="n">44</td><td class="n act">48</td><td>16pxアートが×3の整数倍になる。ラボ幅は704→768px</td></tr>
          <tr><td class="n">TILE_MOBILE</td><td class="n">32</td><td class="n">32（据置）</td><td>すでに16pxの×2</td></tr>
          <tr><td class="n">zoomLevel</td><td class="n">0.3–3.0 連続</td><td class="n act">1/3刻みに丸め</td><td>連続ズームでは非整数倍が生じ、ドット幅が不揃いになる</td></tr>
          <tr><td class="n">.eq-sprite</td><td class="n">inset:0（クリップ）</td><td class="n act">上方向へ1タイル開放</td><td>装置がキャラクターと同じ背丈に立てる</td></tr>
          <tr><td class="n">.character</td><td class="n">0.55タイルの円</td><td class="n act">幅1×高さ1.5タイル</td><td>全身スプライトを置く。足元の占有マスは1×1のまま</td></tr>
          <tr><td class="n">.equip .eq-sprite</td><td class="n">background-size:100% 100%</td><td class="n act">image-rendering:pixelated</td><td>拡大時に平滑補間させない</td></tr>
          <tr><td class="n">--bg-lab</td><td class="n">#b8ad8a 単色</td><td class="n act">レベル別の32pxタイル</td><td>Lv1木造 / Lv2コンクリート / Lv3ラバー / Lv4クリーム</td></tr>
          <tr><td class="n">.lab のグリッド</td><td class="n">常時0.18</td><td class="n act">レイアウトモードのみ</td><td>床テクスチャと干渉するため</td></tr>
        </tbody>
      </table>
    </div>
    <div class="note">
      <h4>残りの作業量</h4>
      <p>装置は14点中2点、キャラクターは21人中3人が描けています。残りは同じ骨格とパレットの上に載るので、1点あたりの手数は今回より小さくなります。ただし装置は種類ごとに形が違うため、キャラクターほど自動化は効きません。</p>
    </div>
  </section>

  <footer>
    生成物と生成スクリプト
    <ul>
      <li>assets/pixel/ — furnace.png · furnace_tall.png · AGT.png</li>
      <li>assets/pixel/char/ — ben.png · grace.png · smith.png（シート）＋ *_front.png</li>
      <li>tools/pixelart/spec.py（投射とグリッドの規約）· pixcore.py · pixshapes.py</li>
      <li>assets/pixel/floor/ — lv1.png · lv2.png · lv3.png · lv4_a〜d.png</li>
      <li>tools/pixelart/furnace.py · agt.py · sprites.py · floors.py</li>
      <li>tools/pixelart/make_scene.py（ラボ床モック）· make_preview.py（このページ）</li>
    </ul>
  </footer>
</div>
'''

out = os.path.join(ROOT, 'build', 'pixelart-preview.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    f.write(HTML)
print(out, os.path.getsize(out), 'bytes')
