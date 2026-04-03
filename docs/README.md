# docs

`affect-wave` の実装前ドキュメント入口です。

`requirements.md` を正本としつつ、`docs/` では実装者が最初に読む順に整理します。

## 読み順

1. [README.md](/Users/ryo-n/Codex_dev/affect-wave/README.md)
2. [実装仕様書](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
3. [RUNBOOK](/Users/ryo-n/Codex_dev/affect-wave/docs/RUNBOOK.md)
4. [実装対比チェックリスト](/Users/ryo-n/Codex_dev/affect-wave/docs/implementation-checklist.md)
5. [受け入れチェックリスト](/Users/ryo-n/Codex_dev/affect-wave/docs/acceptance-checklist.md)
6. [テスト設計書](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md)
7. [評価データセット](/Users/ryo-n/Codex_dev/affect-wave/docs/evaluation-datasets.md)
8. [評価 artifact フォルダ](/Users/ryo-n/Codex_dev/affect-wave/docs/artifacts)
9. [API擬似版 PoC 要件定義 入口](/Users/ryo-n/Codex_dev/affect-wave/docs/requirements-api-poc.md)
10. [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)
11. [PROJECT_CHARTER.md](/Users/ryo-n/Codex_dev/affect-wave/PROJECT_CHARTER.md)
12. [TRADEMARK_POLICY.md](/Users/ryo-n/Codex_dev/affect-wave/TRADEMARK_POLICY.md)

## 役割

- `specification.md`
  実装着手のための短い仕様書です。構成、データ契約、既定値、受け入れ観点をまとめます。
- `requirements-api-poc.md`
  要件定義への入口です。実装前に押さえる必須点だけを短く示します。
- `RUNBOOK.md`
  実装時の進め方、判断基準、落とし穴をまとめた運用ガイドです。
- `implementation-checklist.md`
  仕様に対して実装がどこまで揃ったかを見る対比チェックリストです。
- `acceptance-checklist.md`
  リリース可否を判断するための受け入れ専用チェックリストです。
- `test-design.md`
  実装前の確認観点をまとめたテスト設計書です。テストコードは含みません。
- `evaluation-datasets.md`
  結果出力の検証に使う評価セットと、その見方をまとめたガイドです。主評価は青空文庫の実引用セットです。
- `artifacts/`
  評価実行結果、比較 JSON、補助テキストなどの出力置き場です。

## 使い分け

- 方針や Must/Should の正本を確認したいときは [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)
- 実装の切り方や型・責務を確認したいときは [specification.md](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
- 実装の進め方を確認したいときは [RUNBOOK.md](/Users/ryo-n/Codex_dev/affect-wave/docs/RUNBOOK.md)
- 実装と仕様の差分を点検したいときは [implementation-checklist.md](/Users/ryo-n/Codex_dev/affect-wave/docs/implementation-checklist.md)
- リリース可否を判断したいときは [acceptance-checklist.md](/Users/ryo-n/Codex_dev/affect-wave/docs/acceptance-checklist.md)
- 実装前に確認観点を固めたいときは [test-design.md](/Users/ryo-n/Codex_dev/affect-wave/docs/test-design.md)
- 結果出力を横断的に検証したいときは [evaluation-datasets.md](/Users/ryo-n/Codex_dev/affect-wave/docs/evaluation-datasets.md)
- プロジェクトの思想や境界条件を確認したいときは Charter と Trademark Policy
