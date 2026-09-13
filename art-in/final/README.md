# 手で直したアイコン（最終版）

ブラウザのドットエディタ（`tools/pixelart/make_editor.py` が生成）で
ドット単位で直したもの。**そのまま `assets/pixel/product/` にコピーされる。**
縮小もパレット量子化も輪郭の引き直しもかけない——かけると手で直した箇所が
元に戻る。

`tools/pixelart/build.sh` の最後でコピーされるので、ここに置いたぶんは
`products.py` の描画も `import_product_art.py` の変換も上書きする。

取り込み経路:

    Artifact のドットエディタで編集 → 保存
      → Claude 側で read_db して PNG を復元 → ここに置く → build.sh
