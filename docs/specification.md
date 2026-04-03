# affect-wave 実装仕様書

## 1. 目的

本仕様書は、`affect-wave` の API 擬似版 PoC を実装するための実装者向け仕様を定義する。

正本の要求定義は [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md) とし、本書はその実装用の圧縮版として扱う。

## 2. プロダクト定義

`affect-wave` は、API LLM の会話に含まれる情動的ニュアンスを、文字ベースの波として表現する `affect expression interface` である。

本プロダクトは以下を行わない。

- hidden state の直読
- 感情の証明
- 感情制御
- persuasion や compliance 最適化

`affect_state` は研究上の内部表現そのものではなく、アプリ層で扱う近似的な擬似状態として定義する。

この定義は API で動かす制約に基づく暫定設計であり、論文により近い hidden state / activation ベースのローカル版は別途設計・実装する前提とする。

## 3. 実装スコープ

初期実装で成立させるものは以下とする。

- API LLM を会話本体として使う
- `llama.cpp` 上のローカル埋め込みモデルを affect 推定の必須経路として使う
- 毎ターン `affect_state` を生成する
- `affect_state` から `wave_parameter` を生成する
- CLI と Discord で `wave mode` を表示する
- 設定で `params mode` を返せる

## 4. システム構成

実装は以下の層を分離する。

1. Conversation Layer
   API LLM との会話、履歴管理、connector 分離を担当する。
2. Affect Inference Layer
   埋め込み取得と affect 推定を担当する。
3. State Store
   turn 単位の `affect_state`、`trend`、`compact_state` を保存する。
4. Wave Parameter Layer
   UI 共通の中間表現 `wave_parameter` を生成する。
5. Output Adapter Layer
   CLI、text adapter、Discord adapter を持つ。

依存方向は `Conversation -> Affect Inference -> State Store -> Wave Parameter -> Adapter` とする。

## 5. Affect 推定仕様

### 5.1 許容方式

以下のいずれかを採用してよい。

- `affect prototype` との類似度計算
- 埋め込みベクトルに対する軽量プローブ
- 埋め込み特徴に対する固定規則ベース

参照実装の標準方式は `affect prototype` 類似度計算とする。

### 5.2 必須条件

- 推定器は埋め込み取得なしに結果を決めてはならない
- 類似度計算、重み、prototype 定義の所在を docs またはコードで追跡可能にする
- API LLM の生テキストだけで affect を確定してはならない

### 5.2.1 内部概念層

参照実装は、論文の概念空間に可能な限り近づけるため、**171 概念相当の fine-grained emotion concept layer** を内部に持つ。

これは UI で直接見せるラベル群ではなく、内部推定と集約のための概念層である。

- 1 concept ごとに prototype と textual definition を持つ
- concept ごとに canonical 8 labels への対応を持つ
- `valence`、`arousal`、`appraisal` は concept score の重み付き合成を許容する
- 論文との厳密一致は要求しないが、concept space の方向性は可能な限り寄せる

### 5.3 prototype 定義ファイル規約

参照実装で使う prototype 定義は、リポジトリ内の固定パスから参照できなければならない。

- 配置先は `data/prototypes/` を基準とする
- 細粒度感情概念定義は `data/prototypes/emotion-concepts-171.json` とする
- 感情ラベル定義は `data/prototypes/emotion-labels.json` とする
- concept から canonical 8 labels への写像は `data/prototypes/concept-to-canonical-map.json` とする
- appraisal 軸定義は `data/prototypes/appraisal-axes.json` とする
- valence / arousal 軸定義は `data/prototypes/affect-axes.json` とする

各ファイルは UTF-8 の JSON とし、少なくとも以下を追跡できなければならない。

- `id`
- `label`
- `text`
- `version`
- `updated_at`

初期実装では実ファイルの内容を最小限にしてよいが、ファイル名と責務分割はこの規約に従う。

### 5.4 canonical label set

参照実装で使う `top_emotions` の canonical label set は少なくとも以下を含む。

- `curiosity`
- `calm`
- `tension`
- `joy`
- `sadness`
- `anger`
- `fear`
- `surprise`

これら 8 labels は **表示層の集約カテゴリ** であり、内部推定の最小単位ではない。

### 5.5 出力

`affect_state` は少なくとも以下を含む。

- `top_emotions`
- `concept_scores`
- `appraisal`
- `trend`
- `compact_state`

`top_emotions` は参照実装で上位 3 件を返し、fine-grained concept score を canonical 8 labels へ集約した結果とする。

`concept_scores` は内部細粒度概念スコア群であり、少なくとも `id`、`canonical`、`score` を持つ。

`trend.valence` は `-1.0` 以上 `1.0` 以下の符号付き正規化値とする。

- 正値: 正方向の情動価
- 負値: 負方向の情動価
- 0 近傍: 中立近傍

## 6. 状態スキーマ

### 6.1 `compact_state`

`compact_state` は次ターン差し戻し用の軽量状態であり、最小スキーマを以下に固定する。

```json
{
  "dominant": "curiosity",
  "tone": "soft_rising",
  "stability": "medium"
}
```

`stability` の許容値は以下の 3 つのみとする。

- `low`
- `medium`
- `high`

### 6.2 `top_emotions`

```json
[
  { "name": "curiosity", "score": 0.71 },
  { "name": "calm", "score": 0.52 },
  { "name": "surprise", "score": 0.31 }
]
```

- `score` は `0.0..1.0` の正規化値
- 件数は 3 件固定
- スコア降順で返す

### 6.3 `concept_scores`

```json
[
  { "id": "fg-001", "canonical": "sadness", "score": 0.83 },
  { "id": "fg-002", "canonical": "anger", "score": 0.79 },
  { "id": "fg-003", "canonical": "tension", "score": 0.76 }
]
```

- 内部的には 171 概念相当を保持する
- `params mode` では全件露出を必須にしない
- debug では 171 概念相当の `concept_scores` 全件を数値で確認できなければならない
- `params mode` では必要に応じて `concept_scores_preview` を返してよい

## 7. wave parameter 仕様

`wave_parameter` は UI 共通の唯一の中間表現である。UI は `affect_state` に直接依存してはならない。

### 7.1 必須キー

- `amplitude`
- `frequency`
- `jitter`
- `glow`
- `afterglow`
- `density`

特記なき限り、各値は `0.0..1.0` の正規化済み浮動小数とする。

### 7.2 導出方針

参照実装では少なくとも以下の主軸マッピングを採用する。

- `amplitude <- trend.arousal`
- `frequency <- appraisal.uncertainty + trend.arousal`
- `jitter <- risk_flags.instability + inverse(trend.stability)`
- `glow <- appraisal.social_reward + positive(trend.valence)`
- `afterglow <- trend.stability + signed(trend.valence)`
- `density <- top_emotions の集中度 または appraisal の同時活性数`

補助方針:

- `jitter` は fine-grained concept の競合度が高いほど上がる
- `density` は fine-grained concept の分散と活性数が高いほど上がる

### 7.3 導出条件

- 同一 `affect_state` から同一 `wave_parameter` を返す
- renderer は `wave_parameter` のみを参照する
- 導出規則は deterministic である

## 8. 出力モード

### 8.1 `wave mode`

既定モード。擬音、ASCII、Unicode、AA を使って短い情動波を返す。

### 8.2 `params mode`

明示的設定時のみ有効。`wave_parameter` を JSON で返す。

`params mode` は `wave mode` と同一 turn の同一 `wave_parameter` を参照しなければならない。

返却 JSON の最小形は以下を基準とする。

```json
{
  "turn_id": "turn-000123",
  "mode": "params",
  "top_emotions": [
    { "name": "curiosity", "score": 0.71 },
    { "name": "calm", "score": 0.52 },
    { "name": "surprise", "score": 0.31 }
  ],
  "concept_scores_preview": [
    { "id": "fg-014", "canonical": "curiosity", "score": 0.74 },
    { "id": "fg-077", "canonical": "calm", "score": 0.68 },
    { "id": "fg-103", "canonical": "surprise", "score": 0.51 }
  ],
  "trend": {
    "valence": 0.18,
    "arousal": 0.37,
    "stability": 0.62
  },
  "compact_state": {
    "dominant": "curiosity",
    "tone": "soft_rising",
    "stability": "medium"
  },
  "wave_parameter": {
    "amplitude": 0.38,
    "frequency": 0.44,
    "jitter": 0.22,
    "glow": 0.41,
    "afterglow": 0.35,
    "density": 0.47
  }
}
```

- `turn_id` は turn 単位で一意
- `mode` は常に `params`
- `wave_parameter` は `wave mode` と同一 turn の同一値を返す
- `concept_scores_preview` は任意だが、返す場合は fine-grained concept の上位プレビューとする
- 追加フィールドは許容するが、上記キーは削除してはならない

## 9. Adapter 仕様

### 9.1 CLI adapter

- `wave mode` と `params mode` の双方を確認できる
- デバッグ確認の基準経路として使える

CLI の最小コマンド面は以下を基準とする。

- `POST /analyze` を叩く外部エージェント経路を主経路とする
- `affect-wave inspect --turn <id>`
  指定 turn の `affect_state` と `wave_parameter` を確認する
- `affect-wave render --mode wave`
  直近 turn の `wave mode` 表示を確認する
- `affect-wave render --mode params`
  直近 turn の `params mode` JSON を確認する

初期実装では対話そのものは外部エージェント側に置いてよく、`affect-wave chat` のような内蔵会話 CLI は必須にしない。README と docs では API-first の運用を基準例として扱う。

### 9.2 text adapter

- 返信文先頭に短い wave block を付与する
- Discord 固有ではなく、他の text-first SNS / chat platform に流用可能な共通方式とする

### 9.3 Discord adapter

参照実装の基準方式は bot 方式とする。

- 既定表示は bot 応答
- 表示位置は `reply_prefix` または `webhook` を切り替え可能にする
- Webhook は optional な追加方式とする

Discord renderer は `wave_parameter` のみを参照し、`affect_state` に直接依存してはならない。

Discord の操作面は以下を基準とする。

- slash command を正本とする
- 参照実装では `/affect wave`、`/affect params`、`/affect transport reply_prefix`、`/affect transport webhook` を持つ
- メッセージ内トリガーを補助導線として持つ
- メッセージ内トリガーは日本語と英語の双方を受け付ける
- 日本語例: `詳細`、`感情波`、`パラメータ`
- 英語例: `detail`、`wave`、`params`
- params mode は明示的操作でのみ露出し、通常会話で自動露出しない
- `webhook` が失敗した場合は `reply_prefix` へ degrade してよい
- 表示 transport が失敗しても通常応答本文を失ってはならない

## 10. 設定仕様

最低限の設定キーは以下とする。

```env
OPENAI_API_KEY=
LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
EMBEDDING_MODEL=
DISCORD_BOT_TOKEN=
DISCORD_WEBHOOK_URL=
AFFECT_OUTPUT_MODE=wave
DISCORD_TRANSPORT=reply_prefix
STATE_LOG_ENABLED=false
STATE_LOG_PATH=./logs/affect-state.jsonl
```

`AFFECT_OUTPUT_MODE` の既定値は `wave`、`DISCORD_TRANSPORT` の既定値は `reply_prefix` とする。

## 11. パフォーマンス要件

参照実装における 1 turn あたりの affect 推定レイテンシ目標は、埋め込み取得込みで `800ms` 以内とする。

`1500ms` を超える場合は要調整とする。

## 12. ログとプライバシー

- 保存対象は設定で制御可能にする
- 会話ログと送信用コンテキストは論理的に分離する
- 状態ログの保存先、保持期間、マスキング方針を定義可能にする
- API key、Discord token、Webhook URL は保存してはならない
- PII はマスクまたは除外可能にする

## 13. セットアップ要件

`setup.bat` は必須とする。

少なくとも以下を案内または支援できること。

- モデル配置ディレクトリ作成
- `.env` 初期化
- `llama.cpp` embeddings server 起動確認
- Discord または CLI で `wave mode` 確認

初回導入の目標時間は 15 分以内とする。

README または docs には、少なくとも以下の確認例を載せる。

```powershell
curl -X POST http://127.0.0.1:8081/analyze -H "Content-Type: application/json" -d "{\"user_message\":\"hello\",\"agent_message\":\"hi there\"}"
affect-wave render --mode wave
affect-wave render --mode params
```

## 14. 受け入れ基準

最小受け入れ条件は以下とする。

1. API LLM 会話が成立する
2. affect 推定が埋め込みモデル経由で行われる
3. `affect_state` を毎ターン生成できる
4. `wave_parameter` を毎ターン生成できる
5. `wave mode` が既定表示として返る
6. `params mode` が同一 `wave_parameter` を返す
7. Discord で少なくとも 1 つの既定方式が確認できる
8. CLI で状態確認できる
9. `setup.bat` と README に導入導線がある
10. fine-grained concept layer と canonical 8 labels の対応が追跡できる

## 15. 実装順

着手順は以下を推奨する。

1. `Conversation Layer`
2. `llama.cpp` 埋め込み取得
3. `Affect Inference Layer`
4. `State Store`
5. `Wave Parameter Layer`
6. `CLI adapter`
7. `Discord adapter`

Discord より先に CLI を通すと、推定と描画の切り分けがしやすい。
