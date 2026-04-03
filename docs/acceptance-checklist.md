# affect-wave 受け入れチェックリスト

## 1. 目的

本書は、`affect-wave` の API 擬似版 PoC をリリース可と判断する前に確認する受け入れ専用チェックリストである。

設計の網羅確認ではなく、最終的に「公開してよいか」を判断するための最小チェックに絞る。

## 2. 判定ルール

- すべての必須項目が `合格` になった場合のみリリース可
- `要確認` が残る場合は保留
- `不合格` が 1 件でもある場合は差し戻し

判定の根拠は [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md) を優先する。

## 3. 受け入れ票

| 区分 | 項目 | 判定 | 備考 |
| --- | --- | --- | --- |
| 会話 | API LLM との会話が成立する | 未確認 | |
| 推定 | affect 推定が埋め込みモデル経由で行われる | 未確認 | |
| 推定 | 推定方式、prototype または重み定義の所在を追跡できる | 未確認 | |
| 推定 | 171 概念相当の fine-grained concept bank が定義されている | 未確認 | |
| 推定 | fine-grained concept から canonical 8 labels への写像が定義されている | 未確認 | |
| 推定 | debug で 171 概念相当の `concept_scores` 全件を数値確認できる | 合格 | `GET /debug/concepts/turn-81d113b3` で確認 |
| 状態 | `affect_state` を毎ターン生成できる | 合格 | `POST /analyze` と `inspect` で確認 |
| 状態 | `top_emotions` が 3 件固定で返る | 合格 | `turn-8a9ba05e` を確認 |
| 状態 | `top_emotions` が fine-grained concept 集約結果として算出される | 合格 | debug の `concept_scores` と整合 |
| 状態 | `trend.valence` が `-1.0..1.0` の符号付き値である | 合格 | `turn-8a9ba05e` で `0.0278` を確認 |
| 状態 | `compact_state` が最小スキーマを満たす | 合格 | `dominant/tone/stability` を確認 |
| wave | `wave_parameter` を毎ターン生成できる | 合格 | `POST /analyze` と `render` で確認 |
| wave | `wave_parameter` の必須キーがすべて揃う | 合格 | `amplitude..density` を確認 |
| wave | `wave_parameter` が同一入力で deterministic である | 合格 | `tests/test_converter.py::test_deterministic_conversion` と `tests/test_pipeline.py::test_deterministic_pipeline` |
| mode | デフォルトで `params mode` 表示を返せる | 合格 | `POST /analyze output_mode=params` で確認 |
| mode | 補助的に `wave mode` 表示を返せる | 合格 | `render --mode wave` で確認 |
| mode | `params mode` が同一 turn の `wave_parameter` を返す | 合格 | `turn-8a9ba05e` を確認 |
| Discord | Discord で少なくとも 1 つの既定方式が確認できる | 要確認 | token / API LLM 未設定で実機未確認 |
| Discord | 表示方式切替、通常表示位置、詳細表示トリガーが README と一致する | 要確認 | 実機未確認 |
| Discord | slash command の基準コマンド面が成立する | 要確認 | 実機未確認。コード実装済み |
| Discord | 日本語トリガーと英語トリガーの双方で詳細表示を呼び出せる | 要確認 | 実機未確認。テスト/コード実装済み |
| Discord | adapter 失敗時に state を破壊しない | 要確認 | 実機未確認。webhook fallback はテスト済み |
| CLI | CLI で `wave mode` を確認できる | 合格 | `py -m affect_wave.main render --mode wave` |
| CLI | CLI で `params mode` を確認できる | 合格 | `py -m affect_wave.main render --mode params` |
| CLI | CLI のコマンド面が docs と一致する | 合格 | `--help` 出力確認 |
| 導入 | `setup.bat` で導入導線をたどれる | 合格 | Python launcher fallback、モデル取得、起動例を確認 |
| 導入 | README に埋め込みモデル名、`llama.cpp` 条件、ヘルスチェック方法がある | 合格 | README 更新済み |
| ログ | API key、Discord token、Webhook URL がログへ保存されない | 合格 | config/store 実装を確認 |
| ログ | PII の除外またはマスク方針が実装と一致する | 合格 | state log は本文を 200 文字に切り詰め、秘密値は非保存 |
| docs | README と docs の記述が相互に矛盾しない | 合格 | Discord 操作、health check、transport 表記を確認 |

## 4. Discord 専用確認

| 項目 | 判定 | 備考 |
| --- | --- | --- |
| 通常応答で短い wave 表現が確認できる | 要確認 | 実機未確認 |
| 連続 3 turn 以上で表示崩れなく追従する | 要確認 | 実機未確認 |
| 明示的操作で `params mode` に切り替えられる | 要確認 | 実機未確認 |
| `reply_prefix` と `webhook` の切替仕様が README と一致する | 要確認 | 実機未確認 |
| `/affect wave` と `/affect params` が動作する | 要確認 | 実機未確認 |
| `/affect transport reply_prefix` と `/affect transport webhook` が動作する | 要確認 | 実機未確認 |
| 日本語トリガー `詳細` または `感情波` で詳細表示を呼び出せる | 要確認 | 実機未確認 |
| 英語トリガー `detail` または `params` で詳細表示を呼び出せる | 要確認 | 実機未確認 |
| `webhook` 失敗時に通常本文を失わず `reply_prefix` へ degrade できる | 要確認 | 単体テスト済み、実機未確認 |

## 5. CLI 専用確認

| 項目 | 判定 | 備考 |
| --- | --- | --- |
| `affect-wave chat` 相当の経路がある | 合格 | 主経路は外部エージェント + `POST /analyze` として扱う |
| `affect-wave inspect --turn <id>` 相当の経路がある | 合格 | `py -m affect_wave.main inspect` |
| `affect-wave render --mode wave` 相当の経路がある | 合格 | `py -m affect_wave.main render --mode wave` |
| `affect-wave render --mode params` 相当の経路がある | 合格 | `py -m affect_wave.main render --mode params` |

## 6. リリース判定メモ

- 判定日: 2026-04-04
- 判定者:
- 判定結果:
- 差し戻し理由:
- 保留事項: Discord 実機確認には `DISCORD_BOT_TOKEN`、`API_LLM_BASE_URL`、`API_LLM_API_KEY`、`API_LLM_MODEL`、必要に応じて `DISCORD_WEBHOOK_URL` の投入が必要
- 運用メモ: 主経路が OpenClaw 等の外部エージェントによる API / CLI 呼び出しである場合、Discord 実機は補助 adapter 確認として扱ってよい

## 7. 関連文書

- [RUNBOOK.md](/Users/ryo-n/Codex_dev/affect-wave/docs/RUNBOOK.md)
- [implementation-checklist.md](/Users/ryo-n/Codex_dev/affect-wave/docs/implementation-checklist.md)
- [test-design.md](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md)
