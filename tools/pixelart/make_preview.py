"""Build the pixel-art review sheet as a single self-contained HTML file.

Artifact pages sit behind a CSP that blocks every external host, so every PNG
travels inside the file as a data URI. Output goes to build/, which is
git-ignored — the same convention tools/preview.sh follows.
"""
import base64, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
import spec


def uri(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


DEVICES = [
    ('furnace', 'Furnace', 1, '熱処理の基本。箱、上面、覗き窓のある扉、煙突の4つで打ち止め'),
    ('casting', 'Casting', 1, 'るつぼは先細りさせないと箱に見える。ただし4pxまで絞ると脚と側面がXを描くので6pxで止めた'),
    ('om', 'OM', 1, '重い台座・背後のアーム・前傾した接眼・載物台の4点が顕微鏡を顕微鏡たらしめる'),
    ('pc', 'PC', 1, '開いたノート。デッキは上面、画面は正面'),
    ('arc', 'Arc Melt', 2, '横長チャンバーと覗き窓、右にコンソール'),
    ('rolling', 'Rolling', 2, '圧延ロール2本。各々にインクを回し、間を通る材料で隙間を示す'),
    ('sem', 'SEM', 2, '左に鏡筒と試料室、右にCRT。画面には組織像'),
    ('laser', 'Laser Dep', 3, '大きな窓の中にレーザーヘッドとビーム。台座はルーバー'),
    ('magnet', 'Magnetizer', 3, '銅の巻線コイルと磁極。磁場は背後の淡い2本の弧'),
    ('tem', 'TEM', 3, '積層レンズ段の鏡筒、上端に電子銃、下に蛍光板'),
    ('phase', 'Phase-Shift', 4, '3本のガラス柱。中央が最も高く、中で場がうねる'),
    ('qaa', 'Q-Accel', 4, '周回リングと8個の磁石ブロック、両脇にラック'),
    ('agt', 'AGT', 4, '輪・原子・結晶の3要素。原子は直交2軌道（3軌道は視野24px未満で癒着する）'),
    ('mpss', 'MPSS', 5, 'ラボ最大。中央の窓に定在場、左右にラック、冠部に配管'),
]

CAST = ['tom', 'lisa', 'ben', 'anna', 'mike', 'owen', 'pam',
        'kate', 'sam', 'carol', 'dave', 'eve', 'frank', 'grace', 'hank', 'iris', 'joe',
        'jeff', 'murphy', 'chen', 'lee', 'watson', 'bobby', 'ingrid', 'smith', 'player']
CAST_NOTE = {
    'ben': '丸メガネ', 'sam': 'ヘルメット', 'dave': 'ヘッドホン', 'chen': '角帽',
    'lee': 'フード・閉じた目', 'jeff': '額に上げたゴーグル', 'murphy': 'リーゼント・革ジャン',
    'smith': '白髭・半縁眼鏡', 'mike': 'バンダナ', 'owen': '寝不足', 'joe': 'ジャージ',
    'frank': '制服', 'watson': '口髭・ベスト', 'bobby': '逆立った髪', 'player': 'プレイヤー',
}
SHEETS = ['ben', 'grace', 'smith']
FLOORS = [('lv1', '木造', '長尺の床板と木目。突きつけ目地は入れていない——8pxごとの横目地に16pxごとの縦目地が重なると矩形が並び、色を変えても煉瓦に見える'),
          ('lv2', 'コンクリート打ちっぱなし', '骨材のまだらと細いヒビ2本。タイル境界で途切れないよう、ヒビは32pxタイルの内側に収めた'),
          ('lv3', '緑のラバー床', '8px間隔の丸い突起。実験室用ラバーシートの定番'),
          ('lv4', 'クリーム色シートビニル', '#ded4b7。4案の中で最も明るいものを採用。最も長く見る床なので模様は意図的に静か')]

A = {'scene': uri('build/lab-scene.png')}
for did, *_ in DEVICES:
    A['d_' + did] = uri('assets/pixel/%s.png' % did)
for cid in CAST:
    A['c_' + cid] = uri('assets/pixel/char/%s_front.png' % cid)
for cid in SHEETS:
    A['s_' + cid] = uri('assets/pixel/char/%s.png' % cid)
for key, *_ in FLOORS:
    A['f_' + key] = uri('assets/pixel/floor/%s.png' % key)
    A['fs_' + key] = uri('build/lab-scene-%s.png' % key)

Z = 5
dev_cells = []
for did, label, lv, note in DEVICES:
    tw, th = spec.FOOTPRINT[lv]
    w, h = spec.cell(tw, th)
    dev_cells.append(f'''
      <figure class="dev">
        <div class="art" style="height:{64 * Z // 2}px"><img class="px" src="{A['d_' + did]}" alt="{label}" width="{w * Z}" height="{h * Z}"></div>
        <figcaption><b>{label}</b><span class="tag">Lv{lv} · {tw}×{th}タイル · {w}×{h}</span><span class="note">{note}</span></figcaption>
      </figure>''')

cast_cells = ''.join(f'''
        <figure class="ch">
          <img class="px" src="{A['c_' + cid]}" alt="{cid}" width="{16 * 4}" height="{24 * 4}">
          <figcaption>{cid}{f'<span>{CAST_NOTE[cid]}</span>' if cid in CAST_NOTE else ''}</figcaption>
        </figure>''' for cid in CAST)

sheet_cells = ''.join(f'''
        <figure class="sheet">
          <img class="px" src="{A['s_' + cid]}" alt="{cid}のシート" width="{48 * 4}" height="{48 * 4}">
          <figcaption>{cid} — assets/pixel/char/{cid}.png</figcaption>
        </figure>''' for cid in SHEETS)

floor_blocks = ''.join(f'''
      <div class="device">
        <h3>Lv{i + 1} {label}<span class="tag">assets/pixel/floor/{key}.png · 32×32</span></h3>
        <p>{note}</p>
        <div class="floorrow">
          <figure class="plate"><div class="art" style="padding:0"><img class="px" src="{A['f_' + key]}" alt="" width="128" height="128"></div><figcaption>タイル ×4</figcaption></figure>
          <figure class="plate"><div class="art" style="padding:0"><img class="px" src="{A['fs_' + key]}" alt="Lv{i + 1}の床" width="416" height="192"></div><figcaption>×2 配置</figcaption></figure>
        </div>
      </div>''' for i, (key, label, note) in enumerate(FLOORS))

HTML = f'''<title>LABolic ドット絵アセット</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Shippori+Mincho+B1:wght@700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
  :root {{
    --ground:#eceef4; --panel:#fff; --panel-2:#f5f6fa;
    --ink:#1b2039; --ink-2:#5d6484; --ink-3:#8a90aa;
    --line:#d2d7e4; --line-2:#e3e7f0;
    --accent:#b34e14; --accent-2:#5f47a0;
    --lab:#ded4b7;
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

  .scene {{ background:var(--lab); border:2px solid #6b5c3c; overflow-x:auto; }}
  .scene img {{ width:768px; height:576px; max-width:none; }}
  .scene-cap {{ display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap;
                font-family:var(--mono); font-size:11px; color:var(--ink-3); margin-top:8px; }}

  .devgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:1px;
              background:var(--line); border:1px solid var(--line); }}
  .dev {{ margin:0; background:var(--panel); }}
  .dev .art {{ background:var(--lab); display:grid; place-items:center; padding:10px;
               overflow:hidden; }}
  .dev figcaption {{ padding:10px 12px; font-size:13px; }}
  .dev figcaption b {{ display:block; }}
  .dev .tag {{ display:block; font-family:var(--mono); font-size:10.5px; color:var(--ink-3);
               margin-bottom:5px; }}
  .dev .note {{ display:block; color:var(--ink-2); font-size:12.5px; line-height:1.6; }}

  .castgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(92px,1fr)); gap:14px; }}
  .ch {{ margin:0; }}
  .ch img {{ background:var(--lab); border:1px solid var(--line); padding:5px;
             margin-inline:auto; }}
  .ch figcaption {{ font-family:var(--mono); font-size:11px; margin-top:6px; text-align:center; }}
  .ch figcaption span {{ display:block; font-family:var(--sans); font-size:10.5px;
                         color:var(--ink-3); }}
  .sheets {{ display:flex; flex-wrap:wrap; gap:18px; margin-top:26px; }}
  .sheet {{ margin:0; }}
  .sheet img {{ background:var(--lab); border:1px solid var(--line); padding:6px; }}
  .sheet figcaption {{ font-family:var(--mono); font-size:10.5px; color:var(--ink-3);
                       margin-top:6px; }}

  .device {{ margin-bottom:34px; }}
  .device > h3 {{ font-size:16px; margin:0 0 4px; }}
  .device > h3 .tag {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       margin-left:10px; font-weight:500; }}
  .device > p {{ margin:0 0 14px; color:var(--ink-2); max-width:62ch; font-size:14px; }}
  .floorrow {{ display:flex; flex-wrap:wrap; gap:16px; align-items:flex-start; }}
  .plate {{ margin:0; background:var(--panel); border:1px solid var(--line); }}
  .plate .art {{ display:grid; place-items:center; }}
  .plate figcaption {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       padding:7px 11px; border-top:1px solid var(--line-2); }}

  .rules {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1px;
            background:var(--line); border:1px solid var(--line); }}
  .rule {{ background:var(--panel); padding:16px 18px; }}
  .rule h4 {{ margin:0 0 6px; font-size:13px; font-family:var(--mono);
              letter-spacing:.04em; color:var(--accent-2); }}
  .rule p {{ margin:0; font-size:13.5px; color:var(--ink-2); }}

  .tablewrap {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; min-width:560px;
           font-variant-numeric:tabular-nums; }}
  th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid var(--line-2);
            font-size:13.5px; vertical-align:top; }}
  th {{ font-family:var(--mono); font-size:11px; letter-spacing:.06em; color:var(--ink-3);
        text-transform:uppercase; border-bottom:1px solid var(--line); font-weight:600; }}
  td.n {{ font-family:var(--mono); }}
  td.act {{ color:var(--accent); }}

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
</style>

<div class="wrap">
  <header class="top">
    <p class="kicker">welcome-to-LABolic / branch pixelart-trial</p>
    <h1>2Dドット絵アセット 全点</h1>
    <p class="standfirst">装置14点とキャラクター26体、床4種。投射は「正面＋上面・左右対称」、アート1タイル＝16px、スプライトはフットプリント内に収まります。ゲーム本体にはまだ組み込んでいません。</p>
    <div class="meta">
      <span><b>装置</b> 14点</span>
      <span><b>キャラクター</b> 26体 × 3方向 × 2フレーム</span>
      <span><b>床</b> 4種</span>
      <span><b>生成</b> tools/pixelart/build.sh</span>
    </div>
  </header>

  <section>
    <div class="sec-head"><h2>ラボ全景</h2><span>16×12タイル / ×3 デスクトップ実寸</span></div>
    <p class="lede">装置の配置はゲームの <code>EQUIPMENT_CATALOG</code> の既定座標そのままで、Lv4のラボが開く配置です。床はLv4のシートビニル、グリッド線は非表示。装置・キャラクターとも背景は透過で、接地影と1pxの落ち影のみを持ちます。</p>
    <div class="scene"><img class="px" src="{A['scene']}" alt="全装置と一部のキャラクターを配置したラボ全景"></div>
    <div class="scene-cap"><span>アート256×192px</span><span>×3 = 768×576px（タイル48px）</span></div>
  </section>

  <section>
    <div class="sec-head"><h2>投射規約</h2><span>tools/pixelart/spec.py</span></div>
    <div class="rules">
      <div class="rule"><h4>PROJECTION</h4><p>正面図＋上面。垂直線は垂直、水平線は水平、消失点なし。側面は描かず、奥行きは正面の真上に積む上面だけで示す。</p></div>
      <div class="rule"><h4>TOP_RATIO = 0.25</h4><p>上面の見かけの深さは幅の1/4。幅12pxの箱なら上面3px。</p></div>
      <div class="rule"><h4>LIGHT</h4><p>左上から固定。上面が最も明るく、正面が中間、右端と庇の下が影。</p></div>
      <div class="rule"><h4>INK</h4><p>インクはシルエットだけを描く。内部のエッジはすべて明度差。12pxの面に1pxの線を引くと面の1/8を食う。</p></div>
    </div>
    <div class="note">
      <h4>落ち影について</h4>
      <p>Lv4の床は明るく、クリーム色の筐体とは輝度が近くなります。筐体を暗くしても解決しません——床の輝度がランプの内側に入るため、ランプを動かすと衝突する段が変わるだけです。そこで全装置に1pxの落ち影（右下方向）を付け、色ではなく奥行きで分離しています。影は半透明の黒なので、4種類の床すべてで正しく乗ります。</p>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>装置 14点</h2><span>Lv1 16×16 / Lv2 32×16 / Lv3 32×32 / Lv4 48×32 / Lv5 64×64</span></div>
    <div class="devgrid">{''.join(dev_cells)}</div>
  </section>

  <section>
    <div class="sec-head"><h2>キャラクター 26体</h2><span>16×24 / 足元1×1マス</span></div>
    <p class="lede">襟にはゲームのロスター色をそのまま使っています。16pxでは2pxの前立てでは26着の白衣を見分けられませんが、6pxの襟なら見分けられ、しかもUIでその人物に使われている色と一致します。</p>
    <p class="lede">容姿は各キャラクターが既に持っているイラストアイコンから起こしました——Benは丸メガネ、Samはヘルメット、Daveはヘッドホン、Chenは角帽、Leeは幽霊、Murphyはバイク、Jeffは吹きこぼれたフラスコ。肌の色は3階調に散らしてあり、名前からは推定していません。ここは最も差し替えやすい箇所です。</p>
    <div class="castgrid">{cast_cells}</div>
    <div class="sheets">{sheet_cells}</div>
    <p class="lede" style="margin-top:14px">シートは3列（正面・側面・背面）× 2行（歩行2フレーム）。側面は右向きだけを描き、左向きはCSSの水平反転で作ります。</p>
  </section>

  <section>
    <div class="sec-head"><h2>床 4種</h2><span>ラボレベル別 / 32×32タイル</span></div>
    {floor_blocks}
  </section>

  <section>
    <div class="sec-head"><h2>組み込みに必要なゲーム側の変更</h2><span>いずれも未実施</span></div>
    <div class="tablewrap">
      <table>
        <thead><tr><th>箇所</th><th>現在</th><th>変更後</th><th>理由</th></tr></thead>
        <tbody>
          <tr><td class="n">TILE_DESKTOP</td><td class="n">44</td><td class="n act">48</td><td>16pxアートが×3の整数倍になる。ラボ幅 704→768px</td></tr>
          <tr><td class="n">TILE_MOBILE</td><td class="n">32</td><td class="n">32（据置）</td><td>すでに16pxの×2</td></tr>
          <tr><td class="n">zoomLevel</td><td class="n">0.3–3.0 連続</td><td class="n act">1/3刻みに丸め</td><td>連続ズームでは非整数倍が生じ、ドット幅が不揃いになる</td></tr>
          <tr><td class="n">.eq-sprite</td><td class="n">background-size:100% 100%</td><td class="n act">image-rendering:pixelated</td><td>拡大時に平滑補間させない</td></tr>
          <tr><td class="n">.character</td><td class="n">0.55タイルの円</td><td class="n act">幅1×高さ1.5タイル</td><td>全身スプライトを置く。足元の占有マスは1×1のまま</td></tr>
          <tr><td class="n">--bg-lab</td><td class="n">#b8ad8a 単色</td><td class="n act">レベル別の32pxタイル</td><td>Lv1木造 / Lv2コンクリート / Lv3ラバー / Lv4 #ded4b7</td></tr>
          <tr><td class="n">.lab のグリッド</td><td class="n">常時0.18</td><td class="n act">レイアウトモードのみ</td><td>床テクスチャと干渉する</td></tr>
          <tr><td class="n">アバター枠</td><td class="n">assets/icon/*.png</td><td class="n">据置</td><td>ラボ以外の画面は現行イラストを踏襲</td></tr>
        </tbody>
      </table>
    </div>
    <div class="note">
      <h4>装置の背丈について</h4>
      <p>スプライトをフットプリント内に収める方針のため、Lv1装置（Furnace, Casting, OM, PC）は16×16で、身長がキャラクターの2/3になります。全景でその見え方が確認できます。</p>
    </div>
  </section>

  <footer>
    生成物と生成スクリプト
    <ul>
      <li>assets/pixel/ — 装置14点（furnace, casting, om, pc, arc, rolling, sem, laser, magnet, tem, phase, qaa, agt, mpss）</li>
      <li>assets/pixel/char/ — 26体のシート ＋ *_front.png</li>
      <li>assets/pixel/floor/ — lv1.png · lv2.png · lv3.png · lv4.png</li>
      <li>tools/pixelart/spec.py（投射とグリッドの規約）· pixcore.py · pixshapes.py</li>
      <li>tools/pixelart/devices.py · sprites.py · floors.py</li>
      <li>tools/pixelart/make_scene.py · make_preview.py · build.sh（全再生成）</li>
    </ul>
  </footer>
</div>
'''

out = os.path.join(ROOT, 'build', 'pixelart-preview.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    f.write(HTML)
print(out, os.path.getsize(out), 'bytes')
