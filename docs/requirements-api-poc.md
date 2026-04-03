# API擬似版 PoC 要件定義 入口

本リポジトリの要件定義の正本は [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md) です。

実装者は、まず [実装仕様書](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md) を読み、そのあとで `requirements.md` の詳細を確認してください。

## 最短の読み順

1. [README.md](/Users/ryo-n/Codex_dev/affect-wave/README.md)
2. [実装仕様書](/Users/ryo-n/Codex_dev/affect-wave/docs/specification.md)
3. [requirements.md](/Users/ryo-n/Codex_dev/affect-wave/requirements.md)

## 実装前に押さえる点

- affect 推定の標準方式は `affect prototype` 類似度計算
- `top_emotions` は canonical label set から上位 3 件を返す
- `trend.valence` は `-1.0..1.0` の符号付き値
- `wave_parameter` は UI 共通の唯一の中間表現
- Discord 参照実装の基準は bot 方式
- `reply_prefix` は共通 text adapter として扱う
