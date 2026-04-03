# affect-wave 評価データセット

## 1. 目的

本書は、`affect-wave` の結果出力を継続的に検証するための評価データセットを定義する。

ここでいう評価データセットは、学習用データではなく以下の確認用である。

- `top_emotions` の大きな取り違えが起きていないか
- `trend.valence` / `trend.arousal` / `trend.stability` が極端に崩れていないか
- `wave_parameter` と `wave_output` が全ケースで同じ見た目に潰れていないか
- 文体や長さを変えても、出力傾向がある程度一貫しているか

## 2. 基本方針

- 1 作品や 1 文体に依存した評価にしない
- 明るいケース、暗いケース、混合ケース、文学調、会話調を混ぜる
- `expected_top_labels` は厳密な正解ラベルではなく、出力検証の基準ラベルとして使う
- 期待は `完全一致` だけでなく、`上位 3 件のうち何件が期待集合に入るか` で見る

## 3. 収録データ

### 3.1 青空文庫ベースの主評価セット

ファイル:

- [aozora-output-validation-v1.json](/Users/ryo-n/Codex_dev/affect-wave/data/evalsets/aozora-output-validation-v1.json)

用途:

- 作品引用ベースでの主評価
- README の比較メモより広いケースで確認する
- モデル調整や renderer 調整のたびに再実行する
- 短文ではなく、段落単位の入力で出力を確認する

構成:

- 中島敦『山月記』 3 ケース
- 太宰治『走れメロス』 3 ケース
- 森鴎外『高瀬舟』 3 ケース
- 夏目漱石『こころ』 3 ケース

各ケースは作者名、作品名、青空文庫 URL、長めの引用本文を持つ。

### 3.2 合成補助セット

ファイル:

- [core-output-validation-v1.json](/Users/ryo-n/Codex_dev/affect-wave/data/evalsets/core-output-validation-v1.json)

用途:

- reassurance や短い対話など、文学作品だけでは拾いにくい UI 寄りケースの補助確認
- 主評価セットで問題が出た後の切り分け用

## 4. ケースの見方

各ケースは次のフィールドを持つ。

- `id`: 一意キー
- `group`: ケース種別
- `author`
- `work_title`
- `source_url`
- `title`: 表示名
- `excerpt`
- `expected_top_labels`: 期待される canonical labels
- `expected_valence_band`: 期待される valence の帯
- `expected_arousal_band`: 期待される arousal の帯
- `notes`: 何を見たいケースか

## 5. 推奨評価観点

### 5.1 `top_emotions`

- 期待ラベルとの一致件数
- `fear` / `tension` / `surprise` に過度に寄っていないか
- `calm` / `joy` / `curiosity` が reassurance 系で沈みすぎていないか

### 5.2 `trend`

- `expected_valence_band` と大きく逆向きになっていないか
- 初回 turn 比較でも `stability` がすべて `0.0` に潰れていないか

### 5.3 `wave_output`

- 全ケースで同一文字列に潰れていないか
- 明るいケースと暗いケースで見た目の密度や余韻が少なくとも少し変わるか
- high arousal ケースだけが一律に同じ記号列になっていないか

## 6. 運用ルール

- 調整前後で同じデータセットを流し、artifact を保存する
- artifact は原則として [docs/artifacts](/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts) に保存する
- 1 ケースだけを見て調整しない
- README に載せる比較メモは、このデータセットの結果から抜粋する
- 作品依存に見える調整を入れたときは、必ず青空文庫セット以外の補助セットでも確認する

## 7. 現時点の注意

- `expected_top_labels` は gold annotation ではない
- 本データセットは PoC の出力検証用であり、論文再現ベンチではない
- 語彙 heuristic を入れる場合、青空文庫セットと補助セットの両方で悪化していないかを見る
