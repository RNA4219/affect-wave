# affect-wave

`affect-wave` は、API LLM の会話に含まれる情動的ニュアンスを、文字ベースの波として可視化する `affect expression interface` です。

本リポジトリは感情制御ツールではありません。情動状態を「管理」や「矯正」の対象ではなく、可視化・表現・翻訳・相互理解のための対象として扱います。公式原則は [PROJECT_CHARTER.md](/Users/ryo-n/Codex_dev/affect-wave/PROJECT_CHARTER.md) を参照してください。

## 現在の位置づけ

- 初期リリースの対象は `API擬似版 PoC` です。
- hidden state や内部活性を直接読むのではなく、API LLM の会話過程・出力・文脈遷移を、ローカル埋め込みモデル経由で擬似推定します。
- affect state は研究上の内部表現そのものではなく、UI と対話のためのアプリ層の近似的内部表現です。

## 何を作るか

- API LLM を会話本体として利用する会話レイヤ
- `llama.cpp` 上のローカル埋め込みモデルを使う affect inference レイヤ
- `affect state -> wave parameter -> renderer` の中間表現パイプライン
- Discord と CLI を起点にした text-first 表示
- `wave mode` と `params mode` の切り替え

## 既知の制約

- 現時点では実装前のドキュメント整備フェーズです。
- hidden state 直読は行いません。
- Anthropic 研究の完全再現は目的に含みません。
- Discord の参照実装は bot 方式を基準とし、Webhook は optional な追加方式として扱います。

## 背景研究

- Anthropic, *Emotion concepts and their function in a large language model*
- Anthropic, *Signs of introspection in large language models*
- Tak et al., *Mechanistic Interpretability of Emotion Inference in Large Language Models (2025)*
- Soligo et al., *Investigating and Mitigating Emotional Instability in LLMs (2026)*

これらは背景研究であり、本リポジトリは研究の完全再現ではありません。

## セットアップ方針

現時点の `setup.bat` は実装前ガイド兼プレースホルダです。最終的には次を支援する想定です。

- 埋め込みモデルの取得
- モデル配置ディレクトリ作成
- `.env` 初期化
- `llama.cpp` embeddings server 起動導線
- Discord / CLI の確認手順

初回導入の目標時間は 15 分以内です。

## 想定する設定

`.env.example` に最低限の設定キーを置いています。

- `OPENAI_API_KEY`
- `LLAMA_CPP_BASE_URL`
- `EMBEDDING_MODEL`
- `DISCORD_BOT_TOKEN`
- `DISCORD_WEBHOOK_URL` (`optional`)
- `AFFECT_OUTPUT_MODE`
- `DISCORD_TRANSPORT`
- `STATE_LOG_ENABLED`
- `STATE_LOG_PATH`

## Discord 表示

参照実装では Discord bot 方式を基準にします。

- 既定方式は bot での通常応答
- 表示位置は `reply_prefix` か `webhook` を切り替え可能にする想定
- `reply_prefix` は他の text-first platform に移植可能な共通 `text adapter` 方式として扱います

## 出力モード

- `wave mode`: デフォルト。擬音、ASCII、Unicode、AA を使って気配を返す
- `params mode`: 明示的設定時のみ有効。内部数値を JSON で返す

## 参照実装メモ

- affect 推定方式の標準は `affect prototype` 類似度計算
- prototype 定義ファイルの基準配置は `data/prototypes/`
- `top_emotions` は参照実装で上位 3 件を返す
- `trend.valence` は `-1.0..1.0` の符号付き正規化値
- 1 turn あたりの affect 推定レイテンシ目標は埋め込み取得込みで `800ms` 以内、`1500ms` 超は要調整

## CLI 想定面

実装前ドキュメント上の基準 CLI は以下です。

- `affect-wave chat`
- `affect-wave inspect --turn <id>`
- `affect-wave render --mode wave`
- `affect-wave render --mode params`

最終的な実装名は調整してよいですが、docs と README の例はこの形にそろえます。

## ドキュメント

- docs 入口: [docs/README.md](/Users/ryo-n/Codex_dev/affect-wave/docs/README.md)
- 実装仕様書: [docs/specification.md](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
- テスト設計書: [docs/test-design.md](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md)
- 要件定義: [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)
- docs 入口: [docs/requirements-api-poc.md](/Users/ryo-n/Codex_dev/affect-wave/docs/requirements-api-poc.md)
- 憲章: [PROJECT_CHARTER.md](/Users/ryo-n/Codex_dev/affect-wave/PROJECT_CHARTER.md)
- 商標・公式性: [TRADEMARK_POLICY.md](/Users/ryo-n/Codex_dev/affect-wave/TRADEMARK_POLICY.md)
