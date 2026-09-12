"""Build the pixel-art review sheet as a single self-contained HTML file.

Artifact pages sit behind a CSP that blocks every external host, so every PNG
travels inside the file as a data URI. Output goes to build/, which is
git-ignored — the same convention tools/preview.sh follows.
"""
import base64, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def uri(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


A = {k: uri(v) for k, v in {
    'px_furnace': 'assets/pixel/furnace.png',
    'px_agt':     'assets/pixel/AGT.png',
    'px_ben':     'assets/pixel/ben.png',
    'px_grace':   'assets/pixel/grace.png',
    'px_smith':   'assets/pixel/smith.png',
    'og_furnace': 'assets/furnace.png',
    'og_agt':     'assets/AGT.png',
    'og_ben':     'assets/icon/ben.png',
    'og_grace':   'assets/icon/grace.png',
}.items()}

# Smith has no shipped file — his placeholder is drawn inline in the game's
# stylesheet, so it is reproduced here verbatim rather than re-invented.
A['og_smith'] = ("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' "
                 "viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23c9ccd1'/%3E"
                 "%3Ccircle cx='32' cy='24' r='11' fill='%238b9099'/%3E"
                 "%3Cpath d='M11 60c0-12 9.5-19 21-19s21 7 21 19z' fill='%238b9099'/%3E%3C/svg%3E")

CHARS = [
    ('Ben',   'ben',   'Tier 1 / #7e603c', '丸メガネと切りっぱなしの前髪。現行アイコンはメガネ単体のシンボル'),
    ('Grace', 'grace', 'Tier 2 / #e8c878', '横に流れるポニーテールとスカーフ。現行アイコンは空を背にした人影'),
    ('Smith', 'smith', 'Tier 3 / #534ab7', '白い顎髭と半縁の老眼鏡。現行は画像ファイルを持たず、HTML内のグレーのシルエット'),
]

rows_chars = '\n'.join(f'''
      <article class="char">
        <div class="char-big"><img src="{A['px_' + cid]}" alt="{name}のドット絵" width="192" height="192"></div>
        <div class="char-meta">
          <h3>{name}<span class="tag">{tag}</span></h3>
          <p>{note}</p>
          <dl class="sizes">
            <div><dt>ロスター 28px</dt><dd><img class="av" style="--d:28px" src="{A['px_' + cid]}" alt=""></dd></div>
            <div><dt>雇用カード 22px</dt><dd><img class="av" style="--d:22px" src="{A['px_' + cid]}" alt=""></dd></div>
            <div><dt>モバイル 18px</dt><dd><img class="av" style="--d:18px" src="{A['px_' + cid]}" alt=""></dd></div>
            <div class="sep"><dt>現行</dt><dd><img class="av" style="--d:28px;image-rendering:auto" src="{A['og_' + cid]}" alt=""></dd></div>
          </dl>
        </div>
      </article>''' for name, cid, tag, note in CHARS)

HTML = f'''<title>LABolic ドット絵アセット</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Shippori+Mincho+B1:wght@700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
  :root {{
    --ground:#eceef4; --panel:#fff; --panel-2:#f5f6fa;
    --ink:#1b2039; --ink-2:#5d6484; --ink-3:#8a90aa;
    --line:#d2d7e4; --line-2:#e3e7f0;
    --accent:#b34e14; --accent-2:#5f47a0;
    --lab:#b8ad8a; --grid:rgba(93,74,50,0.18);
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
  .wrap {{ max-width:1000px; margin:0 auto; padding-inline:20px; padding-block:48px 72px; }}
  img {{ max-width:100%; }}
  .px {{ image-rendering:pixelated; image-rendering:crisp-edges; display:block; }}

  /* ---- masthead ---- */
  header.top {{ border-bottom:2px solid var(--ink); padding-bottom:20px; }}
  .kicker {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em;
             text-transform:uppercase; color:var(--accent); margin:0 0 8px; }}
  h1 {{ font-family:var(--serif); font-size:clamp(28px,5vw,42px); line-height:1.25;
        margin:0 0 10px; text-wrap:balance; }}
  .standfirst {{ margin:0; color:var(--ink-2); max-width:62ch; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px 20px; margin-top:16px;
           font-family:var(--mono); font-size:12px; color:var(--ink-3); }}
  .meta b {{ color:var(--ink-2); font-weight:600; }}

  /* ---- sections ---- */
  section {{ margin-top:56px; }}
  .sec-head {{ display:flex; align-items:baseline; gap:14px; border-bottom:1px solid var(--line);
               padding-bottom:8px; margin-bottom:28px; }}
  .sec-head h2 {{ font-family:var(--serif); font-size:22px; margin:0; }}
  .sec-head span {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                    letter-spacing:.08em; }}

  /* ---- device comparison ---- */
  .device {{ margin-bottom:40px; }}
  .device > h3 {{ font-size:17px; margin:0 0 4px; }}
  .device > h3 .tag {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       margin-left:10px; font-weight:500; }}
  .device > p {{ margin:0 0 18px; color:var(--ink-2); max-width:62ch; font-size:14px; }}
  .pair {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:18px; }}
  .plate {{ background:var(--panel); border:1px solid var(--line); }}
  .plate figcaption {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                       padding:8px 12px; border-top:1px solid var(--line-2);
                       display:flex; justify-content:space-between; gap:10px; }}
  .plate .art {{ display:grid; place-items:center; padding:14px; }}

  /* the lab floor, reproduced from the game's own .lab rule */
  .floor {{ background:
      linear-gradient(var(--grid) 1px,transparent 1px) 0 0/44px 44px,
      linear-gradient(90deg,var(--grid) 1px,transparent 1px) 0 0/44px 44px,
      var(--lab);
      border:2px solid #6b5c3c; }}
  .floor.m {{ background-size:32px 32px,32px 32px; }}
  .scale-row {{ display:flex; flex-wrap:wrap; align-items:flex-end; gap:22px; margin-top:16px; }}
  .scale-row figure {{ margin:0; }}
  .scale-row figcaption {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                           margin-top:7px; }}
  .scale-row .floor {{ padding:11px; display:grid; place-items:center; }}

  /* ---- characters ---- */
  .char {{ display:grid; grid-template-columns:auto 1fr; gap:22px; align-items:start;
           padding:20px 0; border-top:1px solid var(--line-2); }}
  .char:first-of-type {{ border-top:0; padding-top:0; }}
  .char-big {{ background:var(--panel); border:1px solid var(--line); padding:8px; }}
  .char-big img {{ image-rendering:pixelated; display:block; }}
  .char-meta h3 {{ font-size:17px; margin:0 0 4px; }}
  .char-meta h3 .tag {{ font-family:var(--mono); font-size:11px; color:var(--ink-3);
                        margin-left:10px; font-weight:500; }}
  .char-meta p {{ margin:0 0 14px; color:var(--ink-2); font-size:14px; max-width:52ch; }}
  .sizes {{ display:flex; flex-wrap:wrap; gap:18px; margin:0; }}
  .sizes > div {{ display:flex; flex-direction:column; gap:7px; align-items:center; }}
  .sizes .sep {{ border-left:1px solid var(--line); padding-left:18px; }}
  .sizes dt {{ font-family:var(--mono); font-size:10px; color:var(--ink-3);
               letter-spacing:.04em; order:2; }}
  .sizes dd {{ margin:0; order:1; }}
  .av {{ width:var(--d); height:var(--d); border-radius:50%; border:2px solid var(--ink);
         image-rendering:pixelated; display:block; }}

  /* ---- findings table ---- */
  .tablewrap {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; min-width:520px;
           font-variant-numeric:tabular-nums; }}
  th, td {{ text-align:left; padding:9px 12px; border-bottom:1px solid var(--line-2);
            font-size:13.5px; }}
  th {{ font-family:var(--mono); font-size:11px; letter-spacing:.06em; color:var(--ink-3);
        text-transform:uppercase; border-bottom:1px solid var(--line); font-weight:600; }}
  td.n {{ font-family:var(--mono); }}
  td.bad {{ color:var(--accent); }}
  td.ok {{ color:var(--accent-2); }}

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

  @media (max-width:560px) {{
    .char {{ grid-template-columns:1fr; }}
  }}
</style>

<div class="wrap">
  <header class="top">
    <p class="kicker">welcome-to-LABolic / branch pixelart-trial</p>
    <h1>2Dドット絵アセット 試作</h1>
    <p class="standfirst">現行の手描きアセットを1ドット単位で描き直した試作です。装置は最も単純なFurnaceと最も複雑なAGT、キャラクターはBen・Grace・Smithの3人。ゲーム本体には組み込んでいません。</p>
    <div class="meta">
      <span><b>装置</b> Furnace 64×64 / AGT 96×64</span>
      <span><b>キャラ</b> 32×32</span>
      <span><b>生成</b> tools/pixelart/*.py</span>
    </div>
  </header>

  <section>
    <div class="sec-head"><h2>装置</h2><span>現行アート ↔ ドット絵 ↔ ラボ実寸</span></div>

    <div class="device">
      <h3>Furnace<span class="tag">Lv1 · 1×1タイル · assets/pixel/furnace.png</span></h3>
      <p>クリーム色の筐体、左奥にずれた本体、覗き窓の火。現行アートは余白が広いので、ドット絵側は画面内でゲームの <code>--sprite-zoom</code> がやっている寄せを最初から織り込んで詰めています。</p>
      <div class="pair">
        <figure class="plate" style="margin:0">
          <div class="art"><img class="px" src="{A['px_furnace']}" alt="Furnaceのドット絵" width="256" height="256"></div>
          <figcaption><span>ドット絵 ×4</span><span>64×64</span></figcaption>
        </figure>
        <figure class="plate" style="margin:0">
          <div class="art"><img src="{A['og_furnace']}" alt="Furnaceの現行アート" width="256" height="256"></div>
          <figcaption><span>現行アート</span><span>1036×1036</span></figcaption>
        </figure>
      </div>
      <div class="scale-row">
        <figure><div class="floor"><img class="px" src="{A['px_furnace']}" alt="" width="44" height="44"></div><figcaption>デスクトップ 44px</figcaption></figure>
        <figure><div class="floor m"><img class="px" src="{A['px_furnace']}" alt="" width="32" height="32"></div><figcaption>モバイル 32px</figcaption></figure>
        <figure><div class="floor"><img class="px" src="{A['px_furnace']}" alt="" width="132" height="132"></div><figcaption>デスクトップ ×3ズーム 132px</figcaption></figure>
      </div>
    </div>

    <div class="device">
      <h3>AGT<span class="tag">Lv4 · 3×2タイル · assets/pixel/AGT.png</span></h3>
      <p>輪、その中の原子、両脇の結晶。この3つだけが96pxで生き残る要素なので、残りは足場として平たく大きく描いています。96×64はモバイルの3×2タイルと寸分たがわず一致します。</p>
      <div class="pair">
        <figure class="plate" style="margin:0">
          <div class="art"><img class="px" src="{A['px_agt']}" alt="AGTのドット絵" width="384" height="256"></div>
          <figcaption><span>ドット絵 ×4</span><span>96×64</span></figcaption>
        </figure>
        <figure class="plate" style="margin:0">
          <div class="art"><img src="{A['og_agt']}" alt="AGTの現行アート" width="384" height="259"></div>
          <figcaption><span>現行アート</span><span>1288×868</span></figcaption>
        </figure>
      </div>
      <div class="scale-row">
        <figure><div class="floor"><img class="px" src="{A['px_agt']}" alt="" width="132" height="88"></div><figcaption>デスクトップ 132×88px</figcaption></figure>
        <figure><div class="floor m"><img class="px" src="{A['px_agt']}" alt="" width="96" height="64"></div><figcaption>モバイル 96×64px — 等倍</figcaption></figure>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>キャラクター</h2><span>32×32 バストアップ / 表示は円形18–28px</span></div>
    {rows_chars}
  </section>

  <section>
    <div class="sec-head"><h2>実寸で起きること</h2><span>labolic-playtest-40.html:4295</span></div>
    <div class="tablewrap">
      <table>
        <thead><tr><th>対象</th><th>ドット絵の原寸</th><th>ゲーム内表示</th><th>倍率</th><th>結果</th></tr></thead>
        <tbody>
          <tr><td>Furnace（デスクトップ）</td><td class="n">64×64</td><td class="n">44×44</td><td class="n">0.69×</td><td class="bad">縮小。ドットが潰れる</td></tr>
          <tr><td>Furnace（モバイル）</td><td class="n">64×64</td><td class="n">32×32</td><td class="n">0.50×</td><td class="ok">2:1。かろうじて保つ</td></tr>
          <tr><td>AGT（デスクトップ）</td><td class="n">96×64</td><td class="n">132×88</td><td class="n">1.375×</td><td class="bad">ドット幅が不均一に</td></tr>
          <tr><td>AGT（モバイル）</td><td class="n">96×64</td><td class="n">96×64</td><td class="n">1.00×</td><td class="ok">完全一致</td></tr>
          <tr><td>アバター（ロスター）</td><td class="n">32×32</td><td class="n">28×28 円形</td><td class="n">0.88×</td><td class="bad">縮小＋角を円で切り落とし</td></tr>
          <tr><td>アバター（モバイル）</td><td class="n">32×32</td><td class="n">18×18 円形</td><td class="n">0.56×</td><td class="bad">顔の造作が消える</td></tr>
        </tbody>
      </table>
    </div>
    <div class="note">
      <h4>ドット絵に移行するなら、先に決めるべきこと</h4>
      <p>タイルは <code>TILE_DESKTOP = 44</code> / <code>TILE_MOBILE = 32</code> の固定値に、0.3〜3.0倍の連続ズームが掛かります。ドット絵は整数倍でないと目に見えて崩れるので、① 原寸をタイルの約数に合わせる（1×1装置なら22×22か44×44）、② ズームを整数段に丸める、③ <code>image-rendering:pixelated</code> で崩れを許容する、のいずれかが要ります。</p>
      <p>アバターは円形に切り抜かれるうえ最小18pxです。32×32のバストアップは四隅と襟元が捨てられるので、実装するなら16×16の顔だけに寄せるか、アバター枠を角丸の正方形に変えるかの判断が先になります。</p>
    </div>
  </section>

  <footer>
    生成物と生成スクリプト
    <ul>
      <li>assets/pixel/furnace.png · AGT.png · ben.png · grace.png · smith.png</li>
      <li>tools/pixelart/pixcore.py（キャンバスとパレット）· pixshapes.py · furnace.py · agt.py · characters.py</li>
      <li>tools/pixelart/make_preview.py（このページ）</li>
    </ul>
  </footer>
</div>
'''

out = os.path.join(ROOT, 'build', 'pixelart-preview.html')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    f.write(HTML)
print(out, os.path.getsize(out), 'bytes')
