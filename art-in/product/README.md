# 外部で描いたアイコンの置き場

ここに `<id>.png` を置いて、

    python3 tools/pixelart/import_product_art.py art-in/product

を実行すると `assets/pixel/product/` に変換出力される。
サイズ・色・背景は問わない（不透明なカード地でもよい。自動で抜く）。

ファイル名に使う `id` は 14 個:

    brass  cupronickel  monel  invar  permalloy  nichrome  ferritic_ss
    austenitic_ss  ti_cr_beta  nitinol  inconel_like
    azoth  quintessence  lapis

置いたぶんだけ差し替わる。置かなかった id は `tools/pixelart/products.py`
が描いたものがそのまま残る（`products.py` を再実行すると上書きされるので、
取り込み後は importer を最後に走らせること）。
