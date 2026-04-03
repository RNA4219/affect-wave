# affect-wave テスト設計書

## 1. 目的

本書は、`affect-wave` の API 擬似版 PoC に対する実装前のテスト設計を定義する。

ここで扱うのは設計のみであり、テストコードや自動テストの実装は含まない。

## 2. 前提

- 正本の要件は [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)
- 実装者向け仕様は [specification.md](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
- 出力検証用データセットは [evaluation-datasets.md](/Users/ryo-n/Codex_dev/affect-wave/docs/evaluation-datasets.md)
- 受け入れ基準の最終判断は要件定義を優先する

## 3. テスト方針

本 PoC の検証は以下の 4 層で分ける。

1. 契約テスト
   スキーマ、値域、件数、導出規則の一貫性を確認する。
2. 振る舞いテスト
   同一入力から同一 `wave_parameter` が得られること、mode 切替で内部値が変わらないことを確認する。
3. adapter テスト
   CLI、text adapter、Discord adapter の出力責務を確認する。
4. 受け入れテスト
   README、setup、既定方式、確認手順が揃っていることを確認する。

## 4. 対象一覧

### 4.1 Conversation Layer

- 会話履歴が stateless 再送の前提で扱えること
- 保存ログと送信用コンテキストが論理分離されること

### 4.2 Affect Inference Layer

- 推定に埋め込み取得が必須経路として含まれること
- `top_emotions`、`trend`、`compact_state` が生成されること

### 4.3 State Store

- turn 単位の state を保存できること
- 秘密情報が state log に混入しないこと

### 4.4 Wave Parameter Layer

- 必須キーが常に揃うこと
- 値域と deterministic 性が守られること

### 4.5 Output Adapter Layer

- CLI で `wave mode` と `params mode` が確認できること
- text adapter が reply prefix 形式を保つこと
- Discord adapter が `wave_parameter` のみを参照して表示を作ること

## 5. 契約テスト設計

### 5.1 `top_emotions`

確認項目:

- canonical label set に存在するラベルのみを返す
- 件数は 3 件固定
- `score` は `0.0..1.0`
- スコア降順である

代表ケース:

1. 通常会話入力で 3 件返る
2. スコアが同値のときも件数が 3 件で固定される
3. label set 外の値が出ない

追加確認:

- `data/prototypes/emotion-labels.json` の定義と返却ラベルが一致する
- `top_emotions` が fine-grained concept score の集約結果として説明できる

### 5.2 `trend.valence`

確認項目:

- 値域は `-1.0..1.0`
- 符号付き値として扱われる
- 0 近傍が中立として解釈できる

代表ケース:

1. 正方向ケースで正値
2. 負方向ケースで負値
3. 中立ケースで 0 近傍

### 5.3 `compact_state`

確認項目:

- `dominant`、`tone`、`stability` が必ず存在する
- `stability` は `low` / `medium` / `high` のみ
- 次ターン差し戻しに使える最小サイズである

### 5.4 prototype 定義ファイル

確認項目:

- `data/prototypes/` 配下に規定ファイル名が存在する
- 各 JSON に `id`、`label`、`text`、`version`、`updated_at` がある
- emotion / appraisal / affect axes が責務ごとに分離される
- `emotion-concepts-171.json` がある
- `concept-to-canonical-map.json` がある
- fine-grained concept から canonical label への写像が欠落していない

### 5.5 fine-grained concept layer

確認項目:

- 内部に 171 概念相当の concept bank を保持する
- 各 concept が canonical label に写像される
- concept score から `top_emotions` が集約される
- `params mode` で必要に応じて preview を返せる
- debug で 171 概念相当の `concept_scores` 全件を数値確認できる

代表ケース:

1. 近い意味の fine-grained concepts が同一 canonical label に集約される
2. 異なる canonical label にまたがる concept score が競合した場合、集約結果に反映される
3. concept score の分散が `density` や `jitter` に影響する
4. debug 出力で 171 概念相当の score が id と score 付きで全件確認できる

## 6. 導出テスト設計

### 6.1 `affect_state -> wave_parameter`

確認項目:

- 同一 `affect_state` で同一 `wave_parameter` が返る
- 必須キーが欠けない
- 全値が `0.0..1.0` に clamp される
- fine-grained concept の競合が `jitter` に反映される
- fine-grained concept の活性分散が `density` に反映される

代表ケース:

1. 同一入力を 10 回与えて同一出力になる
2. `trend.arousal` 上昇で `amplitude` が非減少となる
3. 正の `trend.valence` 上昇で `glow` が増加方向になる
4. `trend.stability` 低下で `jitter` が増加方向になる

### 6.2 mode 同期

確認項目:

- `wave mode` と `params mode` が同一 turn の同一 `wave_parameter` を参照する
- `params mode` だけ別計算しない

代表ケース:

1. 同一 turn で `wave mode` 表示後に `params mode` を呼び、内部値が一致する
2. mode 切替後も `affect_state` 再計算なしで表現だけ切り替わる

### 6.3 `params mode` 契約

確認項目:

- `turn_id`、`mode`、`top_emotions`、`trend`、`compact_state`、`wave_parameter` が存在する
- `mode` は常に `params`
- `wave_parameter` の必須キーがすべて揃う
- `concept_scores_preview` を返す場合は fine-grained concept の preview である

## 7. Adapter テスト設計

### 7.1 CLI

確認項目:

- `wave mode` を人間可読に表示できる
- `params mode` を JSON で表示できる
- turn ごとの state と trend を確認できる
- `chat`、`inspect`、`render --mode wave`、`render --mode params` のコマンド面が README と一致する

### 7.2 text adapter

確認項目:

- 返信文先頭に短い wave block を付与する
- 本文を過度に圧迫しない
- Discord 以外へ移植可能な形式を保つ

### 7.3 Discord adapter

確認項目:

- bot 方式が基準経路として成立する
- `reply_prefix` と `webhook` を切り替え可能である
- slash command の基準コマンド面が成立する
- メッセージ内トリガーを補助導線として持つ
- 日本語トリガーと英語トリガーの双方で詳細表示を呼び出せる
- params mode は明示的操作でのみ露出する
- `webhook` 失敗時に `reply_prefix` へ degrade できる
- transport 失敗時も通常応答本文を失わない
- adapter 失敗時に state を破壊しない

代表ケース:

1. 既定方式で通常応答と短い wave が併記される
2. transport 切替後も同一 turn の `wave_parameter` を再利用できる
3. 日本語トリガー `詳細` または `感情波` で params mode を呼び出せる
4. 英語トリガー `detail` または `params` で params mode を呼び出せる
5. `/affect wave` と `/affect params` が README の説明どおりに動作する
6. `params mode` 呼び出し失敗時に短い失敗理由を返す

## 8. セットアップ受け入れ設計

確認項目:

- `setup.bat` の存在
- `.env.example` の存在
- README に導入手順がある
- `llama.cpp` 条件、埋め込みモデル、ヘルスチェック方法が記載されている

代表ケース:

1. 新規利用者が docs と README のみで導入手順を追える
2. Discord token と Webhook optional 設定の区別が分かる
3. CLI での最小確認手順が明記されている

## 9. 非機能テスト設計

### 9.1 レイテンシ

確認項目:

- affect 推定の目標が `800ms` 以内
- `1500ms` 超で要調整として判定できる

### 9.2 ログとプライバシー

確認項目:

- API key、Discord token、Webhook URL がログに出ない
- 保存対象、保持期間、マスキング方針が設定で定義できる
- PII を除外またはマスクできる

## 10. 受け入れチェックリスト

- API LLM 会話が成立する
- 埋め込みモデル経由で affect 推定が行われる
- `affect_state` が毎ターン生成される
- `wave_parameter` が毎ターン生成される
- `wave mode` が既定表示として返る
- `params mode` が同一 `wave_parameter` を返す
- Discord で少なくとも 1 つの既定方式が確認できる
- Discord の slash command と message trigger が docs と一致する
- 日本語トリガーと英語トリガーの双方が確認できる
- CLI で確認できる
- `setup.bat` と README の導線がある
- fine-grained concept layer と canonical 8 labels の対応が追跡できる

## 11. 実装前レビューで見るべき点

- prototype 定義や重み定義の所在が追跡可能か
- `top_emotions` 件数、`trend.valence` 値域、`compact_state.stability` 列挙が仕様と一致しているか
- `wave_parameter` 導出が deterministic か
- transport 切替が renderer 差に留まり、推定ロジック差になっていないか
- fine-grained concept bank と 8 label 集約の責務境界が明確か

## 12. 出力検証データセット

確認項目:

- 単一作品や単一文体に依存せず、青空文庫の複数作品を横断して確認する
- 調整前後で同じ評価セットを流し、artifact を保存する
- `expected_top_labels` との一致件数だけでなく、`wave_output` の差分も見る

推奨データセット:

- 主評価: [aozora-output-validation-v1.json](/Users/ryo-n/Codex_dev/affect-wave/data/evalsets/aozora-output-validation-v1.json)
- 補助確認: [core-output-validation-v1.json](/Users/ryo-n/Codex_dev/affect-wave/data/evalsets/core-output-validation-v1.json)

最低確認:

1. 青空文庫セットで作品間の偏りが極端でない
2. `fear` / `tension` / `surprise` に一律偏重していない
3. 主評価セットだけを良くして補助セットを壊していない
4. `wave_output` が全ケースで同一文字列に潰れていない
