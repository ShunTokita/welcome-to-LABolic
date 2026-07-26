# welcome-to-LABolic — 作業手順

ブラウザ版・iOSアプリ版の Claude Code から編集する前提のリポジトリ。
このファイルはセッション開始時に自動で読み込まれるので、毎回説明する必要はない。

## 構成

```
index.html                  最新版へのリダイレクト（実体ではない）
labolic-playtest-NN.html    各バージョンの本体。単一HTMLにゲーム全体が入る
assets/                     装置画像14枚
assets/icon/                キャラクターアイコン21枚
tools/                      運用スクリプト
build/                      プレビュー生成物（git管理外）
```

バージョン番号は**ファイル名と `<title>` の `Beta vNN` の2箇所**にある。
両方を手で直すと `<title>` を忘れるので、`tools/new-version.sh` で更新する。

## 作業ブランチ

`subv2` が Claude Code 専用ブランチ。ここに直接コミットしてよい（ユーザー承認済み）。
`main` は本番。`subv2` から `main` への反映は、ユーザーが明示的に指示したときだけ行う。

## 標準フロー

```bash
tools/new-version.sh          # 最新版を複製し、番号とタイトルを+1
#   → labolic-playtest-NN.html を編集
tools/check.sh                # アセット欠損・タイトル不整合・未追跡ファイルを検査
tools/preview.sh              # 画像を埋め込んだ単一ファイルを build/ に生成
#   → build/artifact-vNN.html を Artifact として公開し、ユーザーに確認してもらう
tools/release.sh              # 確認が取れたら index.html を新版に向ける
git add -A && git commit && git push -u origin subv2
```

**プレビューでの確認が取れる前に `release.sh` を実行しない。**
`release.sh` は公開物を切り替える操作なので、ユーザーの確認が前提。

## プレビュー（Artifact）の制約

Artifact は単一ファイルで、CSPが外部ホストへの通信を全て遮断する。
そのため本番と以下が異なる。プレビューで再現しない不具合は本番で確認すること。

- **リーダーボード**: Firebase への通信が遮断される。エラー表示と再試行ボタンが出るが、
  ゲームは落ちない（`try/catch` で保護済み）
- **フォント**: Google Fonts が遮断され、システムフォントにフォールバックする
- **Google Analytics**: `tools/prep_artifact.py` が除去する。プレビューの閲覧が
  本番の計測に混ざらないようにするため
- **viewport / CSSリセット**: Artifact 側のスケルトンに包まれるため、余白や
  ズーム挙動が本番とわずかにずれる場合がある

Artifact を公開するときは `favicon` に 🧪 を指定し、既存のプレビューを更新する場合は
同じファイルパスで再公開すると同じURLが維持される。

## 画像を追加・差し替えるとき

`assets/` に置いて **`git add` を忘れないこと**。手元では動くのに、
プッシュ後に404になる事故が起きる。`tools/check.sh` がこれを検出する。

拡張子は当てにならない（`.png` のうち14枚は実体がJPEG）。
`tools/build_standalone.py` はマジックバイトからMIMEを判定しているので、
拡張子と中身が食い違っていても問題ない。

## やらないこと

- **`build/` をコミットしない。** 1ファイル約4.5MBで、バージョンごとに積むと
  リポジトリが急速に肥大化する。`.gitignore` 済み
- **`index.html` を直接編集しない。** `tools/release.sh` が生成する
- **過去バージョンのファイルを消さない。** URLで参照できる状態を保つのが方針
- **ローカルサーバー（`python3 -m http.server`）で確認しようとしない。**
  このコンテナはクラウド上にあり、ユーザーの端末からは到達できない。
  動作確認の手段は Artifact か GitHub Pages のどちらか

## 過去バージョンとリーダーボードについて

旧バージョンもURLでアクセスできる状態で残るため、誰かが旧版を遊ぶと
そのスコアも同じ Firebase リーダーボード（`leaderboard.json` /
`leaderboard_udm.json`）に記録される。バランス調整を挟んだ場合、
スコアの比較可能性が崩れる点に注意。
