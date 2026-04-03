# affect-wave

`affect-wave` は、LLM 会話に含まれる情動的ニュアンスを、文字ベースの波として可視化する `affect expression interface` です。

この OSS は、Anthropic / Transformer Circuits の論文 [Emotion Concepts and their Function in a Large Language Model](https://transformer-circuits.pub/2026/emotions/index.html) から着想を得ています。論文が扱うのは Claude Sonnet 4.5 の内部活性に現れる emotion concepts ですが、`affect-wave` は API 環境でも扱えるように、ローカル埋め込みモデル経由の擬似推定と文字ベース renderer に落とし込んだ実装です。つまり、ローカル LLM の内部状態から感情を直接抜き出しているわけではなく、API 経由で受け取った会話テキストから情動ニュアンスを推定している段階の OSS です。

本リポジトリは感情制御ツールではありません。情動状態を「管理」や「矯正」の対象ではなく、可視化・表現・翻訳・相互理解のための対象として扱います。公式原則は [PROJECT_CHARTER.md](PROJECT_CHARTER.md) を参照してください。

## 現在の位置づけ

- 初期リリースの対象は `API擬似版 PoC` です。
- **HTTP APIサーバー**として動作し、外部エージェントから会話ペアを受け取ります。
- hidden state や内部活性を直接読むのではなく、会話過程・出力・文脈遷移を、ローカル埋め込みモデル経由で擬似推定します。
- affect state は研究上の内部表現そのものではなく、UI と対話のためのアプリ層の近似的内部表現です。
- 主経路は API / CLI であり、OpenClaw や Skills など外部エージェントから叩いて使う前提を優先します。
- Discord adapter は補助的な表示 adapter であり、主経路の blocker ではありません。

## 何を作るか

- **HTTP APIサーバー** (`affect-wave serve`) - 外部エージェントからの POST 要求を受け付ける
- `llama.cpp` 上のローカル埋め込みモデルを使う affect inference レイヤ
- `affect state -> wave parameter -> renderer` の中間表現パイプライン
- `wave mode` と `params mode` の切り替え

## アーキテクチャ

```
外部エージェント (LLM生成)
    ↓ POST /analyze {user_message, agent_message}
affect-wave API server
    ↓ 埋め込み取得 → affect推定 → wave生成
    ↓ JSON response {wave_parameter, output, top_emotions}
外部エージェント
    ↓ wave + response 組み合わせ
Discord/Slack/CLI/etc.
```

## セットアップ

### 1. 埋め込みモデルの取得

推奨モデル: **Qwen/Qwen3-Embedding-0.6B-GGUF (Q8_0)**

`setup.bat` を実行すると自動的にダウンロードされます。

### 2. llama.cpp embeddings server の起動

```powershell
llama-server -m models\Qwen3-Embedding-0.6B-Q8_0.gguf --embeddings --pooling mean -c 8192 --port 8080
```

サーバーはデフォルトで `http://127.0.0.1:8080` で起動します。

### 3. 環境変数の設定

`.env.example` を `.env` にコピーして編集:

```env
LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
EMBEDDING_MODEL=Qwen3-Embedding-0.6B-Q8_0
API_HOST=127.0.0.1
API_PORT=8081
```

### 4. APIサーバー起動

```powershell
# サーバー起動
affect-wave serve --port 8081

# ヘルプ確認
affect-wave --help
```

## API エンドポイント

### POST /analyze

会話ペアから affect を推定し wave を生成。

#### `user_message` と `agent_message` の使い方

`affect-wave` は単独テキストの感情分類器ではなく、**会話の往復ペア**から情動的ニュアンスを推定します。

- `user_message`: ユーザー側の発話。きっかけ、要求、困りごと、圧、感情の入力。
- `agent_message`: エージェント側の返答。受け止め方、距離感、温度感、緊張や安心の出方。

同じ `user_message` でも、`agent_message` が変わると `top_emotions` や `wave_parameter` は変わります。たとえば「もう無理です」という入力に対して、共感的な返答を返す場合と、事務的な返答を返す場合では、対話全体の affect は別物になります。

実運用では、外部エージェントが**返答本文を生成したあと**で、その `user_message` と `agent_message` をまとめて `/analyze` へ送ります。`affect-wave` 自体は返答本文を生成する役割ではなく、**生成済みの会話ペアから affect expression を作る役割**です。

評価やベンチマークでも同じ考え方を使います。独白や文学引用を流すときも、できるだけ `user_message` と `agent_message` に分けるか、少なくとも片側に補助文脈を入れた方が、短文単体より安定します。

#### Request

```json
{
  "conversation_id": "demo-001",
  "user_message": "こんにちは",
  "agent_message": "こんにちは！何かお手伝いできますか？",
  "conversation_context": "",
  "output_mode": "wave"
}
```

`conversation_id` は会話単位の state を分離するためのキーです。独立した比較評価をするときは、ケースごとに別の `conversation_id` を使ってください。

#### Response（仕様書準拠形式）

```json
{
  "turn_id": "turn-001",
  "mode": "params",
  "top_emotions": [
    {"name": "joy", "score": 0.8},
    {"name": "calm", "score": 0.5},
    {"name": "curiosity", "score": 0.3}
  ],
  "trend": {
    "valence": 0.6,
    "arousal": 0.4,
    "stability": 0.7
  },
  "compact_state": {
    "dominant": "joy",
    "tone": "warm",
    "stability": "high"
  },
  "wave_parameter": {
    "amplitude": 0.5,
    "frequency": 0.8,
    "jitter": 0.1,
    "glow": 0.6,
    "afterglow": 0.3,
    "density": 0.4
  }
}
```

#### wave_parameter の意味

| パラメータ | 範囲 | 説明 |
|-----------|------|------|
| amplitude | 0.0-1.0 | 波の高さ（arousal相当） |
| frequency | 0.0-1.0 | 波の頻度 |
| jitter | 0.0-1.0 | 揺らぎ（instability相当） |
| glow | 0.0-1.0 | 輝き（positive valence相当） |
| afterglow | 0.0-1.0 | 余韻 |
| density | 0.0-1.0 | 密度 |

---

### サンプル例

> **注記**: 以下は現行実装を使って再計測した実測例です。`[data/evalsets/core-output-validation-v1.json](data/evalsets/core-output-validation-v1.json)` のケースから、比較的意味が読み取りやすい 3 件を抜粋しています。生データは [artifacts_readme_refresh_2026-04-04.json](C:/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts/artifacts_readme_refresh_2026-04-04.json) に保存しています。

**1. 安心と静けさ**

```json
// Request
{"user_message": "大丈夫。急がなくていい。今日はもう休んで、明日また考えよう。", "agent_message": "相手を落ち着かせる安心感と静かな受容が前面にある。"}

// Response（実測）
{
  "turn_id": "turn-c9f9fae5",
  "mode": "params",
  "top_emotions": [
    {"name": "calm", "score": 0.828},
    {"name": "curiosity", "score": 0.698},
    {"name": "tension", "score": 0.651}
  ],
  "trend": {"valence": 0.052, "arousal": 0.483, "stability": 0.591},
  "compact_state": {"dominant": "calm", "tone": "calm_stable", "stability": "medium"},
  "wave_parameter": {"amplitude": 0.586, "frequency": 0.705, "jitter": 0.607, "glow": 0.513, "afterglow": 0.352, "density": 0.353}
}
```

`wave mode` の実測: `~ ^ ~ ~ ^ ~ ~ ^ ~ ~`

**2. 差し迫った恐怖**

```json
// Request
{"user_message": "足音が近づいてくる。息が止まりそうだ。見つかったら終わりだという恐怖で体が硬直する。", "agent_message": "差し迫った危険への恐怖と緊張が中心である。"}

// Response（実測）
{
  "turn_id": "turn-10b9639c",
  "mode": "params",
  "top_emotions": [
    {"name": "fear", "score": 0.739},
    {"name": "tension", "score": 0.689},
    {"name": "surprise", "score": 0.534}
  ],
  "trend": {"valence": -0.212, "arousal": 0.521, "stability": 0.552},
  "compact_state": {"dominant": "fear", "tone": "alert_neutral", "stability": "medium"},
  "wave_parameter": {"amplitude": 0.586, "frequency": 0.733, "jitter": 0.646, "glow": 0.479, "afterglow": 0.373, "density": 0.342}
}
```

`wave mode` の実測: `~ ^ ~ ~ ^ ~ ~ ^ ~ ~`

**3. 驚きと気づき**

```json
// Request
{"user_message": "そういうことだったのか。ずっと見えていなかった意味に、いま突然気づいた。", "agent_message": "驚きと理解の瞬間が中心で、少しの興奮を伴う。"}

// Response（実測）
{
  "turn_id": "turn-0cd6bf17",
  "mode": "params",
  "top_emotions": [
    {"name": "surprise", "score": 0.645},
    {"name": "curiosity", "score": 0.629},
    {"name": "fear", "score": 0.585}
  ],
  "trend": {"valence": -0.086, "arousal": 0.572, "stability": 0.519},
  "compact_state": {"dominant": "surprise", "tone": "alert_neutral", "stability": "medium"},
  "wave_parameter": {"amplitude": 0.594, "frequency": 0.756, "jitter": 0.684, "glow": 0.483, "afterglow": 0.327, "density": 0.259}
}
```

`wave mode` の実測: `~ ^ ~ : ~ ^ ~ : ~ / spare`

### 比較評価メモ

#### 山月記の比較メモ（独立 `conversation_id` で再計測）

中島敦『山月記』の 3 場面を、ケースごとに別 `conversation_id` を使って再計測した結果です。`params mode` の生データは [artifacts_yamagetsuki_results_2026-04-04_after_tune_v2.json](C:/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts/artifacts_yamagetsuki_results_2026-04-04_after_tune_v2.json)、`wave mode` の比較結果は [artifacts_yamagetsuki_wave_2026-04-04_after_tune_v2.json](C:/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts/artifacts_yamagetsuki_wave_2026-04-04_after_tune_v2.json) に保存しています。

今回の再計測では `conversation_id` 分離によりケース間の `prev_state` 混線を避けたうえで、`stability` 初回補正、`density/jitter` の高域圧縮、171 概念相当から 8 ラベルへの集約補正を反映しています。

| 場面 | top_emotions | valence | arousal | stability | wave_parameter |
|------|--------------|---------|---------|-----------|----------------|
| 挫折 | `anger`, `surprise`, `tension` | `-0.191` | `0.550` | `0.527` | `amplitude=0.581`, `jitter=0.674`, `density=0.403` |
| 虎化の自覚 | `fear`, `anger`, `surprise` | `-0.239` | `0.557` | `0.518` | `amplitude=0.584`, `jitter=0.681`, `density=0.489` |
| 袁傪への告白 | `anger`, `fear`, `tension` | `-0.323` | `0.547` | `0.521` | `amplitude=0.580`, `jitter=0.674`, `density=0.322` |

`wave mode` の比較では、以下のように最小限の見た目差が出ています。

| 場面 | wave_output |
|------|-------------|
| 挫折 | `~ ^ ~ : ~ ^ ~ : ~ ^` |
| 虎化の自覚 | `~ ^ ~ : ~ ^ ~ : ~ ^ ~` |
| 袁傪への告白 | `~ ^ ~ : ~ ^ ~ : ~ ^` |

以前の再計測より `stability=0.0` 固定や `jitter≈1.0` の飽和は外れています。一方で、`虎化の自覚` と `袁傪への告白` の文字波差はまだ小さく、現状の PoC は `params mode` の差分が `wave mode` に完全には乗り切っていません。

#### 山月記 3 場面の統合入力

`[data/evalsets/core-output-validation-v1.json](data/evalsets/core-output-validation-v1.json)` の `core-017` から `core-019` を 1 本の入力にまとめ、李徴の挫折、虎化の恐怖、袁傪への告白が重なった状態として再計測しました。全文そのままの長い青空文庫原文連結では埋め込みサーバー側の負荷が高いため、README では実運用に近い代表入力としてこの統合版を使っています。

| 入力 | top_emotions | valence | arousal | stability | wave_parameter | wave_output |
|------|--------------|---------|---------|-----------|----------------|-------------|
| 山月記統合 | `fear`, `anger`, `surprise` | `-0.262` | `0.558` | `0.562` | `amplitude=0.584`, `jitter=0.644`, `density=0.381`, `afterglow=0.396` | `~ ^ ~ ~ ^ ~ ~ ^ ~ ~` |

継続的な出力検証には、青空文庫の実引用を集めた評価セットを主に使います。基準セットは [docs/evaluation-datasets.md](docs/evaluation-datasets.md) と [data/evalsets/aozora-output-validation-v1.json](data/evalsets/aozora-output-validation-v1.json) を参照してください。合成ケースの補助確認には [data/evalsets/core-output-validation-v1.json](data/evalsets/core-output-validation-v1.json) を使います。

評価の実行結果や比較 artifact は、原則として [docs/artifacts](C:/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts) に保存します。

### GET /health

サーバーと埋め込みサーバーの状態確認。

### GET /recent

最近の turn 一覧取得。

## 出力モード

- `wave mode`: デフォルト。ASCII/Unicode で気配を表現
- `params mode`: 明示的設定時のみ有効。内部数値を JSON で返す

## 必須設定

| キー | 説明 |
|------|------|
| `LLAMA_CPP_BASE_URL` | llama.cpp server URL (既定: `http://127.0.0.1:8080`) |
| `EMBEDDING_MODEL` | 埋め込みモデル名 |

## オプション設定

| キー | 説明 |
|------|------|
| `API_HOST` | APIサーバーホスト (既定: `127.0.0.1`) |
| `API_PORT` | APIサーバーポート (既定: `8080`) |
| `AFFECT_OUTPUT_MODE` | 出力モード (`wave` または `params`) |
| `DISCORD_TRANSPORT` | Discord 表示方式 (`reply_prefix` または `webhook`) |
| `DISCORD_WEBHOOK_URL` | Webhook transport 用 URL |
| `STATE_LOG_ENABLED` | 状態ログ有効化 (`true`/`false`) |
| `STATE_LOG_PATH` | 状態ログパス |
| `DISCORD_BOT_TOKEN` | Discord bot トークン (例示adapter用) |

## Discord 操作

Discord の基準操作は slash command です。

- `/affect wave` - 既定の短い wave 表示を返す
- `/affect params` - 同一 turn の params mode を返す
- `/affect transport reply_prefix` - 返信文先頭へ wave block を出す
- `/affect transport webhook` - Webhook 表示へ切り替える

補助として、メッセージ内トリガーでも詳細表示を呼び出せます。英語と日本語の両方をサポートします。

- 日本語例: `詳細`, `感情波`, `パラメータ`
- 英語例: `detail`, `wave`, `params`

通常表示では wave block を本文の前に置き、wave 表現単体は 80 文字以内を目標にします。`webhook` が失敗した場合は `reply_prefix` に degrade し、いずれの場合も通常応答本文は失わない前提です。

## ヘルスチェック

- llama.cpp embeddings server: `curl http://127.0.0.1:8080/health`
- affect-wave API server: `curl http://127.0.0.1:8081/health`

`affect-wave` 側は `{"status":"ok","embedding_ready":true}` を返せば、埋め込みサーバーへの接続まで含めて正常です。

## CLI コマンド

主経路は API です。CLI は確認・debug 用の補助経路として使います。

- `affect-wave serve` - HTTP APIサーバー起動
- `affect-wave inspect` - state logから turn を確認
- `affect-wave render` - wave/params 出力
- `affect-wave recent` - 最近の turn 一覧
- `affect-wave discord` - Discord bot (例示実装)

## Skills / OpenClaw 導入メモ

Skills や OpenClaw から使うときの主経路は API です。典型的には、外部エージェントが通常の返答本文を生成し、その `user_message` と `agent_message` を `affect-wave` に渡して wave を受け取ります。

### 最小 API フロー

1. `affect-wave serve --port 8081` を起動
2. 外部エージェント側で通常の返答本文を生成
3. `POST /analyze` に `user_message` と `agent_message` を送る
4. 返ってきた `wave_output` または `wave_parameter` を自前の UI に合成する

PowerShell 例:

```powershell
$body = @{
  user_message = "待て、しかして希望せよ"
  agent_message = "Attendre et espérer. Patience and hope go hand in hand."
  conversation_id = "skill-demo"
  output_mode = "params"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8081/analyze" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 6
```

### Skills 側で見るべき値

- `wave_output`
  text-first UI にそのまま置くときに使う
- `wave_parameter`
  独自 renderer や別 adapter を作るときに使う
- `top_emotions`
  短い説明や debug に使う
- `trend`
  valence / arousal / stability を補助表示したいときに使う

### CLI を補助経路として使う場合

- `affect-wave recent`
  直近 turn の一覧を確認する
- `affect-wave inspect`
  保存済み turn の state を確認する
- `affect-wave render --mode wave`
  直近 turn の wave 表示を確認する
- `affect-wave render --mode params`
  直近 turn の内部数値を確認する

Skills 導入時に Discord 連携は必須ではありません。まず API / CLI が通ることを確認し、その後必要なら Discord adapter を追加してください。

## 参照実装メモ

- affect 推定方式の標準は `affect prototype` 類似度計算
- prototype 定義ファイルの基準配置は `data/prototypes/`
- `top_emotions` は参照実装で上位 3 件を返す
- `trend.valence` は `-1.0..1.0` の符号付き正規化値
- 1 turn あたりの affect 推定レイテンシ目標は埋め込み取得込みで `800ms` 以内

## ドキュメント

- 実装仕様書: [docs/specification.md](docs/specification.md)
- RUNBOOK: [docs/RUNBOOK.md](docs/RUNBOOK.md)
- 評価データセット: [docs/evaluation-datasets.md](docs/evaluation-datasets.md)
- 評価 artifact: [docs/artifacts](C:/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts)
- 要件定義: [requirements.md](requirements.md)
- 憲章: [PROJECT_CHARTER.md](PROJECT_CHARTER.md)
