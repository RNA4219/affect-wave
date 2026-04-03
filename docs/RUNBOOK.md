# affect-wave RUNBOOK

## 1. 目的

本 RUNBOOK は、`affect-wave` の API 擬似版 PoC を実装する際の作業順、確認ポイント、判断基準をまとめた実装運用ガイドである。

本書はコード実装そのものではなく、実装者が docs を見ながら迷わず進めるための手順書として扱う。

## 2. 読み順

実装に入る前に、少なくとも以下を読む。

1. [README.md](/Users/ryo-n/Codex_dev/affect-wave/README.md)
2. [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)
3. [specification.md](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
4. [test-design.md](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md)
5. [implementation-checklist.md](/Users/ryo-n/Codex_dev/affect-wave/docs/implementation-checklist.md)

## 3. 作業原則

- `requirements.md` を正本とする
- UI は `affect_state` ではなく `wave_parameter` を参照する
- affect 推定は埋め込み取得を必須経路とする
- `params mode` は別計算せず、同一 turn の `wave_parameter` を再利用する
- Discord 実装より先に CLI 経路を通す
- 画像前提にしない

## 4. 実装の推奨順

### Step 1. 雛形を切る

目的:

- 層構造と責務境界を先に固定する

確認:

- Conversation Layer
- Affect Inference Layer
- State Store
- Wave Parameter Layer
- CLI / text / Discord adapter

完了条件:

- 依存方向が `Conversation -> Affect Inference -> State Store -> Wave Parameter -> Adapter` に沿って説明できる

### Step 2. prototype 定義を置く

目的:

- affect 推定の参照元を固定する

確認:

- `data/prototypes/emotion-labels.json`
- `data/prototypes/appraisal-axes.json`
- `data/prototypes/affect-axes.json`

完了条件:

- 各 JSON の役割が分離されている
- `id`、`label`、`text`、`version`、`updated_at` を持つ

### Step 3. 埋め込み取得経路を通す

目的:

- `llama.cpp` 経由で埋め込みを取得できる状態にする

確認:

- `.env` から `LLAMA_CPP_BASE_URL` と `EMBEDDING_MODEL` を読める
- ヘルスチェック方法が README と一致する

完了条件:

- テキスト入力から埋め込み取得までの最小経路が説明できる

### Step 4. affect 推定を作る

目的:

- prototype 類似度方式で `affect_state` を組み立てる

確認:

- `top_emotions` は 3 件固定
- `trend.valence` は `-1.0..1.0`
- `compact_state.stability` は `low` / `medium` / `high`

完了条件:

- 推定結果が仕様書の最小契約を満たす

### Step 5. wave 変換を作る

目的:

- `affect_state` から deterministic に `wave_parameter` を導出する

確認:

- 必須キー 6 個が揃う
- 全値が `0.0..1.0`
- `glow` と `afterglow` が `trend.valence` の符号に追随する

完了条件:

- 同一 `affect_state` から同一 `wave_parameter` が返る

### Step 6. CLI を先に通す

目的:

- 描画と推定を最小コストで確認する

確認:

- `POST /analyze`
- `affect-wave inspect --turn <id>`
- `affect-wave render --mode wave`
- `affect-wave render --mode params`

完了条件:

- `wave mode` と `params mode` の双方を API / CLI で追える

### Step 7. text adapter を作る

目的:

- 返信文先頭に wave block を付与する汎用経路を先に作る

確認:

- 本文を圧迫しない
- Discord 固有の構造に寄りすぎない

完了条件:

- 他の text-first platform にも流用可能な説明ができる

### Step 8. Discord adapter を作る

目的:

- bot 方式を基準に通常応答へ wave を出す

確認:

- `reply_prefix` と `webhook` を切り替えられる
- slash command を正本として持つ
- メッセージ内トリガーを補助導線として持つ
- 日本語と英語の双方で詳細表示を呼び出せる
- 失敗時に state を壊さない

完了条件:

- 少なくとも 1 つの既定方式で Discord 表示が成立する
- `/affect wave` と `/affect params` の基準コマンドが README と一致する
- `webhook` 失敗時に通常応答本文を維持したまま degrade できる

## 5. 実装中の判断基準

### 推定方式を迷ったとき

- 参照実装は prototype 類似度方式を優先する
- probe や規則ベースは将来拡張として扱う

### どこまで数値を露出するか迷ったとき

- 通常 UX は `wave mode`
- 数値露出は `params mode` のみ

### Discord 仕様で迷ったとき

- bot 方式を基準にする
- transport 切替は adapter 差に閉じ込める
- slash command を正本、message trigger を補助とする
- 補助トリガーは日本語と英語の双方を維持する

## 6. 失敗しやすいポイント

- `params mode` だけ別計算してしまう
- Discord renderer が `affect_state` を直接読む
- `top_emotions` の件数が可変になる
- `trend.valence` を `0..1` 扱いにしてしまう
- prototype 定義の所在が曖昧になる

## 7. レビュー前チェック

- [implementation-checklist.md](/Users/ryo-n/Codex_dev/affect-wave/docs/implementation-checklist.md) を全項目確認する
- [test-design.md](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md) の契約テスト観点と矛盾がないか確認する
- README、仕様書、CLI 例、transport 設定の記述をそろえる

## 8. この RUNBOOK で扱わないこと

- 実装コード
- テストコード
- CI 設定
- リリース自動化
