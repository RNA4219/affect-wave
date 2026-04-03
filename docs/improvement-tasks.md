# affect-wave 改善タスク

## 1. 目的

本書は、`affect-wave` の山月記サンプルで見えた「内部差分はあるが表示差分が弱い」問題に対する改善タスクをまとめたものである。

## 2. 実装タスク

- renderer を段階化し、`jitter`、`glow`、`afterglow`、`density` の差を見た目に強く反映する
- canonical emotion 集約を平均から重み付き上位和へ変更し、概念数による平坦化を減らす
- `trend.valence` に fine-grained concept 側の正負寄与を補正として加える
- `density` を active appraisal count 偏重から、top concepts の entropy / canonical spread ベースへ寄せる

## 3. 確認観点

- 山月記 3 ケースで `wave_output` が同一文字列に潰れない
- `jitter` と `afterglow` の差が文字表現に反映される
- `top_emotions` が平均化で平坦になりすぎない
- `valence` が全ケースほぼゼロ近傍に潰れにくくなる
