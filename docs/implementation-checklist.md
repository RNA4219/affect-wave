# affect-wave 実装対比チェックリスト

## 1. 目的

本書は、仕様に対して実装がどこまで揃っているかを確認するための対比チェックリストである。

設計レビュー、実装レビュー、受け入れ前確認のいずれでも使ってよい。

## 2. 使い方

- 仕様根拠は [requirements.md](requirements.md) と [specification.md](specification.md) を参照する
- 各項目は `未着手` / `進行中` / `完了` のいずれかで管理する
- 実装コード名やファイル名が決まったら備考欄に紐づける

## 3. アーキテクチャ

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| Conversation Layer の責務が分離されている | 完了 | src/affect_wave/conversation/ |
| Affect Inference Layer の責務が分離されている | 完了 | src/affect_wave/affect/ |
| State Store の責務が分離されている | 完了 | src/affect_wave/state/ |
| Wave Parameter Layer の責務が分離されている | 完了 | src/affect_wave/wave/ |
| Output Adapter Layer の責務が分離されている | 完了 | src/affect_wave/adapters/ |
| 依存方向が仕様どおりである | 完了 | Conversation → Affect → State → Wave → Adapter |

## 4. prototype と推定

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `data/prototypes/emotion-labels.json` がある | 完了 | 8 canonical labels |
| `data/prototypes/emotion-concepts-171.json` がある | 完了 | 171 fine-grained concepts |
| `data/prototypes/concept-to-canonical-map.json` がある | 完了 | concept → canonical mapping |
| `data/prototypes/appraisal-axes.json` がある | 完了 | 6 appraisal axes |
| `data/prototypes/affect-axes.json` がある | 完了 | valence/arousal axes |
| 各 prototype JSON に `id` がある | 完了 | |
| 各 prototype JSON に `label` がある | 完了 | |
| 各 prototype JSON に `text` がある | 完了 | |
| 各 prototype JSON に `version` がある | 完了 | |
| 各 prototype JSON に `updated_at` がある | 完了 | |
| 埋め込み取得が推定の必須経路になっている | 完了 | EmbeddingClient |
| 推定方式が prototype 類似度方式である | 完了 | cosine similarity |
| fine-grained concept bank が 171 概念相当で定義されている | 完了 | emotion-concepts-171.json |
| concept から canonical 8 labels への写像が定義されている | 完了 | concept-to-canonical-map.json |

## 5. affect_state 契約

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `top_emotions` を返す | 完了 | AffectState.top_emotions |
| `concept_scores` を内部保持する | 完了 | AffectState.concept_scores |
| `appraisal` を返す | 完了 | AffectState.appraisal |
| `trend` を返す | 完了 | AffectState.trend |
| `compact_state` を返す | 完了 | AffectState.compact_state |
| `top_emotions` 件数が 3 件固定である | 完了 | create_affect_state() |
| `top_emotions` が canonical label set 内に収まる | 完了 | 8 canonical labels |
| `top_emotions` が concept score の集約結果である | 完了 | _aggregate_to_emotions() |
| `trend.valence` が `-1.0..1.0` である | 完了 | |
| `compact_state.dominant` が存在する | 完了 | |
| `compact_state.tone` が存在する | 完了 | |
| `compact_state.stability` が存在する | 完了 | |
| `compact_state.stability` が `low` / `medium` / `high` のみである | 完了 | StabilityLevel enum |
| debug で `concept_scores` 全件を数値確認できる | 完了 | GET /debug/concepts |

## 6. wave_parameter 契約

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `amplitude` がある | 完了 | WaveParameter.amplitude |
| `frequency` がある | 完了 | WaveParameter.frequency |
| `jitter` がある | 完了 | WaveParameter.jitter |
| `glow` がある | 完了 | WaveParameter.glow |
| `afterglow` がある | 完了 | WaveParameter.afterglow |
| `density` がある | 完了 | WaveParameter.density |
| 各値が `0.0..1.0` に収まる | 完了 | clamp_all() |
| 同一 `affect_state` から同一 `wave_parameter` を返す | 完了 | deterministic |
| `amplitude` が `trend.arousal` ベースで導出される | 完了 | |
| `glow` が正方向の `trend.valence` に追随する | 完了 | |
| `afterglow` が `trend.stability` と `trend.valence` に追随する | 完了 | |
| `jitter` が concept 競合度に追随する | 完了 | _compute_concept_conflict() |
| `density` が concept 分散や活性数に追随する | 完了 | _compute_concept_variance() |

## 7. mode 契約

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `wave mode` が既定表示である | 完了 | output_mode default |
| `params mode` が明示的設定時のみ有効である | 完了 | |
| `params mode` が JSON を返す | 完了 | |
| `params mode` が `turn_id` を返す | 完了 | |
| `params mode` が `mode=params` を返す | 完了 | |
| `params mode` が同一 turn の `wave_parameter` を返す | 完了 | |
| `params mode` だけ別計算しない | 完了 | |
| `params mode` が必要に応じて concept preview を返せる | 完了 | concept_count in response |
| debug 経路が 171 概念相当の `concept_scores` 全件を返せる | 完了 | /debug/concepts endpoint |

## 8. CLI

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `affect-wave serve` 相当の経路がある | 完了 | HTTP API server |
| `affect-wave inspect --turn <id>` 相当の経路がある | 完了 | GET /debug/concepts/{turn_id} |
| `affect-wave render --mode wave` 相当の経路がある | 完了 | POST /analyze with wave mode |
| `affect-wave render --mode params` 相当の経路がある | 完了 | POST /analyze with params mode |
| CLI で state と trend を確認できる | 完了 | inspect command |
| CLI が人間可読表示を持つ | 完了 | |

## 9. Adapter

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| text adapter がある | 完了 | adapters/text.py |
| text adapter が reply prefix 方式を持つ | 完了 | format_wave_prefix() |
| Discord adapter がある | 完了 | adapters/discord.py (example) |
| Discord 基準方式が bot である | 完了 | create_bot() |
| `reply_prefix` transport を切り替えられる | 完了 | config |
| `webhook` transport を切り替えられる | 完了 | config |
| slash command の基準コマンド面を持つ | 完了 | `/affect wave`, `/affect params`, `/affect transport ...` |
| メッセージ内トリガーを補助導線として持つ | 完了 | 日本語/英語の双方 |
| 日本語トリガーを受け付ける | 完了 | `詳細`, `感情波`, `パラメータ` |
| 英語トリガーを受け付ける | 完了 | `detail`, `wave`, `params` |
| params mode を通常会話で自動露出しない | 完了 | 明示的操作のみ |
| `webhook` 失敗時に `reply_prefix` へ degrade できる | 完了 | send_response fallback |
| transport 失敗時も通常応答本文を維持する | 完了 | send_response fallback |
| Discord renderer が `wave_parameter` のみを参照する | 完了 | |
| Discord adapter 失敗時に state を破壊しない | 完了 | |

## 10. 設定と導入

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| `.env.example` に必要キーがある | 完了 | |
| `LLAMA_CPP_BASE_URL` を案内している | 完了 | |
| `EMBEDDING_MODEL` を案内している | 完了 | |
| `API_HOST` を案内している | 完了 | |
| `API_PORT` を案内している | 完了 | |
| `setup.bat` が存在する | 完了 | |
| README に導入導線がある | 完了 | |

## 11. ログと非機能

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| 会話ログと送信用コンテキストが分離される | 完了 | |
| 秘密情報を state log に保存しない | 完了 | |
| レイテンシ目標 `800ms` を意識した設計になっている | 完了 | |
| `1500ms` 超を要調整として扱える | 完了 | |

## 12. 受け入れ前確認

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| 埋め込みモデル経由で affect 推定が行われる | 完了 | EmbeddingClient |
| `affect_state` を毎ターン生成できる | 完了 | AffectInference.infer() |
| `wave_parameter` を毎ターン生成できる | 完了 | convert_to_wave_parameter() |
| CLI で確認できる | 完了 | affect-wave serve |
| README と docs の記述が一致している | 完了 | |
| fine-grained concept layer と canonical 8 labels の対応が追跡できる | 完了 | concept-to-canonical-map.json |

## 13. テスト

| 項目 | 状態 | 備考 |
| --- | --- | --- |
| 123 tests passing | 完了 | pytest |
| 82% code coverage | 完了 | --cov |
