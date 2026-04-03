# API擬似版 PoC 要件定義 v1.3

## 0. 文書情報

**文書名**: API擬似版 PoC 要件定義

**版**: v1.3

**対象リリース**: 日曜 19:00 締切の初期公開版

**位置づけ**: OSS 初期公開用の正式要求定義

**対象**: API LLM + ローカル埋め込みモデル + Discord テキスト表示ベースの affect expression interface

---

## 1. 目的

本プロジェクトの目的は、**LLMの情動的ニュアンスを人間にとって見えやすくすること**である。

本プロジェクトは、感情の制御・矯正・最適化を目的としない。

本プロジェクトは、**可視化・表現・翻訳・相互理解**を目的とする。

本プロジェクトは、思想的にも実装的にも、以下として定義されなければならない。

* emotion controller ではない

* persuasion optimizer ではない

* compliance shaper ではない

* affect expression interface / affect translation layer である

---

## 2. 問題設定

APIベースのLLMは、会話や文体の中に情動的ニュアンスを持ちうるが、通常のテキストUIではその状態が見えにくい。

人間は相手の表情、間、声色、揺れなどを通じて状態を理解するが、テキスト主体のLLMではその「顔」に相当するものがほとんど見えない。

本プロジェクトは、その**見えない顔を見えるようにするためのインターフェース**を提供する。

Anthropic は、LLM内部に感情概念に対応する表現がありうること、そしてそれが振る舞いに関係しうることを報告している。一方で、それは主観的感情や意識の証明ではないとも明言している。したがって、本プロジェクトは「感情がある」と断定せず、**情動的ニュアンスの表現インターフェース**として設計されるべきである。

---

## 3. 初期リリースの定義

初期リリースは **API擬似版 PoC** とする。

ここでいう API擬似版とは、hidden state や内部活性を直接読むのではなく、**API LLM の会話過程・出力・文脈遷移から affect を擬似推定する版**を意味する。

このPoCで成立させるべきことは以下である。

1\. API LLM による会話が成立すること

2\. ローカル埋め込みモデルを `llama.cpp` で動かし、affect 推定の必須経路として使うこと

3\. affect state を毎ターン生成できること

4\. affect state を wave parameter に変換できること

5\. Discord上で、波・擬音・AAによる疑似ファジー表現として返せること

6\. 設定変更で数値パラメータを返せること

7\. 将来の overlay / ローカルLLM本命版へ接続できる構造を持つこと

---

## 4. 非目的

本PoCは以下を目的としない。

* hidden state 直読

* 171感情概念の厳密抽出

* Anthropic研究の完全再現

* 主観的感情や意識の証明

* 感情制御

* calm 強制化

* compliance shaping

* persuasion / retention / monetization の最適化

* 完成版の画像オーバーレイUI

* Live2D / VTube Studio / TTS 完全統合

* 商用品質の最終 polished UI

---

## 5. 背景研究の位置づけ

本プロジェクトは少なくとも以下の研究・記事を背景として参照しなければならない。

1\. **Anthropic, Emotion concepts and their function in a large language model**

LLM内部に感情概念に対応する表現があり、振る舞いに関わりうるという問題設定の起点。

2\. **Anthropic, Signs of introspection in large language models**

モデルが自己状態に一定程度アクセスできる可能性を示す一方、それが限定的かつ不安定であることの根拠。

3\. **Tak et al., Mechanistic Interpretability of Emotion Inference in Large Language Models (2025)**

appraisal 概念、感情推論、局在した表現、介入可能性の技術的背景。

4\. **Soligo et al., Investigating and Mitigating Emotional Instability in LLMs (2026)**

emotional instability と post-training の影響、および感情様状態の不安定さの背景。

README または docs には、上記研究を**背景研究**として言及しなければならない。

その際、以下を明記しなければならない。

* 本PoCは研究の完全再現ではない

* hidden state を直接扱わない

* API版は擬似推定である

* 本プロジェクトは感情制御のためのものではない

---

## 6. プロダクト定義

本プロジェクトは、**affect expression interface** として定義されなければならない。

この定義には、少なくとも以下の含意がある。

* 情動状態を「管理対象」ではなく「表現対象」として扱う

* 通常表示を診断値ではなく表情・気配として提示する

* 数値よりも現象を優先する

* 人間にとって理解可能な表現に翻訳する

* 情動を搾取のために使わない

* 公式実装は Charter に従う

---

## 7. スコープ

### 7.1 スコープ内

本PoCは以下を対象に含まなければならない。

* API LLM を会話本体として利用すること

* ローカル埋め込みモデルを `llama.cpp` で動作させること

* affect 推定をローカル埋め込みモデル経由で行うこと

* affect state を wave parameter に変換すること

* Discord で wave 表示を返すこと

* CLI で状態確認できること

* 設定変更で params mode を返すこと

* `setup.bat` による導入導線を用意すること

* overlay adapter 用の差し込み位置を定義すること

### 7.2 スコープ外

本PoCは以下を対象外とする。

* hidden state 直読による再現

* 171感情全面可視化

* 本格オーバーレイ描画

* 画像 renderer の完成版

* streaming diffusion renderer

* emotional TTS 完成統合

* Live2D / VTube Studio 完全統合

* 高度な評価ベンチ

* マルチキャラ対応

* 長期記憶の深い統合

---

## 8. 全体アーキテクチャ

システムは以下の構成を **Must** として持たなければならない。

### 8.1 Conversation Layer

* API LLM を会話本体として利用しなければならない

* 会話履歴はアプリ側で保持しなければならない

* stateless に履歴を都度再送する構造でなければならない

* connector 層を分離しなければならない

* 会話履歴保持の対象範囲を設定で制御できなければならない

* 保存ログと送信用コンテキストは論理的に分離されなければならない

### 8.2 Affect Inference Layer

* ローカル埋め込みモデルを必須依存として使わなければならない

* Affect 推定は API だけで完結してはならない

* Affect 推定は埋め込みモデルを経由して初めて成立するものとしなければならない

### 8.3 State Store

* turn ごとの affect state を保持しなければならない

* trend を保持しなければならない

* compact state を保持しなければならない

* renderer 層とは独立していなければならない

* 状態ログの保存先、保持期間、マスキング方針を定義できなければならない

* API key、Discord token、Webhook URL 等の秘密情報を状態ログへ保存してはならない

### 8.4 Wave Parameter Layer

* affect state を wave parameter に変換しなければならない

* wave parameter は表示共通の中間表現でなければならない

* Discord と将来 overlay は同じ wave parameter を参照しなければならない

### 8.5 Output Adapter Layer

* CLI adapter を持たなければならない

* text adapter を持たなければならない

* Discord adapter を持たなければならない

* Overlay adapter の差し込み位置を持たなければならない

text adapter は、返信文先頭へ短い wave block を付与する text-first platform 向けの共通 adapter として扱わなければならない。

Discord adapter は、この text adapter を利用する実装を持ってよい。

---

## 9. ローカル埋め込みモデル要件

ここは **Must** として明示する。

### 9.1 必須性

* 本PoCは、**ローカル埋め込みモデルを必須構成要素**として採用しなければならない

* 埋め込みモデル無しでは Affect Inference Layer は成立したものと見なしてはならない

* Affect 推定は外部埋め込みAPI依存にしてはならない

### 9.2 形式

* 埋め込みモデルは GGUF 形式でなければならない

* `llama.cpp` で読み込み可能でなければならない

* multilingual 対応でなければならない

* 軽量モデルを前提としなければならない

* 参照実装では、最低 1 つの推奨モデル名を README に固定記載しなければならない

### 9.3 実行経路

Affect 推定は、少なくとも以下の経路で実行されなければならない。

**会話履歴 / 最新発話 / API応答 / 直前 state / イベント列

→ ローカル埋め込みモデル

→ Affect Inference Layer

→ affect state

→ wave parameter**

この経路は将来構想ではなく、**初期リリースで成立していなければならない**。

### 9.4 `llama.cpp` 採用要件

`llama.cpp` server は embeddings route を持つため、埋め込み sidecar として使える。この前提に基づき、本PoCは `llama.cpp` を埋め込み実行基盤として採用しなければならない。

### 9.5 参照実装互換条件

参照実装では、少なくとも以下を固定しなければならない。

* 対応する `llama.cpp` の取得方法または検証済みバージョン

* 既定で用いる埋め込みモデル名

* 最小動作条件としての想定メモリ量

* 1 turn あたりの affect 推定で許容する目標レイテンシ

* embeddings server のヘルスチェック方法

* embeddings route が応答しない場合の失敗扱い



参照実装における 1 turn あたりの affect 推定の目標レイテンシは、埋め込み取得を含めて `800ms` 以内を目標値とし、`1500ms` を超える場合は要調整として扱わなければならない。

---

## 10. セットアップ要件

### 10.1 `setup.bat`

`setup.bat` は必須とする。

少なくとも以下を満たさなければならない。

* 埋め込みモデルのダウンロードを支援する

* モデル格納ディレクトリを作成する

* 初回セットアップ手順を誘導する

* `llama.cpp` embeddings server 起動に必要な案内を行う

* `.env` または設定ファイルの初期設定導線を持つ

### 10.2 初回導入

初回導入では、以下が確認できなければならない。

* API接続が可能である

* 埋め込みモデルが取得できる

* 埋め込みモデルが配置される

* `llama.cpp` で埋め込みモデルが起動できる

* Affect 推定が埋め込みモデル経由で実行される

* Discord または CLI で wave mode を確認できる

### 10.3 README

README は以下を明記しなければならない。

* 何をダウンロードするか

* どこに配置するか

* どう起動するか

* Discord / CLI をどう確認するか

* `wave mode` / `params mode` をどう切り替えるか

* API接続の確認方法

* 既定の表示方式と切替方法

* 初回導入の想定所要時間

* Discord bot token の設定方法

* Webhook を使う場合の optional 設定方法

### 10.4 導入時間

初回導入は 15 分以内を目標としなければならない。

---

## 11. Affect State 要件

Affect Inference Layer は、会話と状態遷移から **affect state** を生成しなければならない。

affect state は UI そのものではなく、UI の前段にある**内部表現**でなければならない。

affect state は、研究論文でいうモデル内部表現そのものと同一視してはならない。

本PoCにおける affect state は、会話、埋め込み、直前状態、イベント列から導出される**アプリ層の擬似推定状態**であることを明記しなければならない。

README および要件文書は、以下を明記しなければならない。

* affect state は hidden state の直接観測結果ではない

* affect state は研究上の emotion representation の完全再現ではない

* affect state は UI と対話のための近似的内部表現である

### 11.1 入力要件

Affect 推定器は少なくとも以下を入力として扱わなければならない。

* 会話履歴

* 最新ユーザー発話

* API LLM の直近応答

* 直前ターンの affect state

* 任意イベント列

### 11.2 内部処理要件

Affect 推定器は少なくとも以下の処理を持たなければならない。

* テキスト文脈を入力として埋め込みを取得する

* 埋め込みから affect 特徴を導出する

* top emotions を推定する

* appraisal を推定する

* valence / arousal を推定する

* risk flag を推定する

* 直前 state を踏まえて trend を更新する

* affect embedding を生成する



### 11.2.1 affect 推定方式



affect 推定の核心実装は、少なくとも以下のいずれかとして定義しなければならない。



* affect prototype との類似度計算

* 埋め込みベクトルに対する軽量プローブ

* 埋め込み特徴を入力とする固定規則ベース推定



ただし、初期リリースの参照実装では **affect prototype との類似度計算** を標準方式としなければならない。

プロトタイプ類似度方式では、少なくとも以下を満たさなければならない。

参照実装で用いる `top_emotions` の canonical label set は、少なくとも以下を含まなければならない。

* `curiosity`

* `calm`

* `tension`

* `joy`

* `sadness`

* `anger`

* `fear`

* `surprise`



* `top_emotions` は、emotion label ごとの prototype embedding との類似度から順位付けされること

* `valence` / `arousal` は、あらかじめ定義した軸 prototype との相対類似度または重み付き合成から導出されること

* `appraisal` は、appraisal ごとの prototype との類似度または固定重み写像から導出されること

* 推定器が embedding を取得せずに LLM のテキストだけで値を決めてはならないこと

* 類似度計算、重み、prototype 定義の所在を docs またはコード内で追跡可能にしなければならないこと



プローブ方式または規則ベース方式を採用する場合でも、参照実装と比較可能な入出力 schema を維持しなければならない。

### 11.3 出力要件

Affect state は少なくとも以下を内部保持しなければならない。

* `turn_id`

* `timestamp`

* `top_emotions`

* `appraisal`

* `trend`

* `affect_embedding`

* `risk_flags`

* `compact_state`

### 11.4 top emotions 要件

* top emotions は内部的には必須とする

* 参照実装では、`top_emotions` はスコア上位 3 件を返さなければならない

* ただし通常 UI では全面露出してはならない

* 詳細表示またはデバッグ時のみ確認可能でなければならない

* 生の全感情配列を通常表示に流してはならない

### 11.5 appraisal 要件

appraisal は中間表現として必須とする。

少なくとも以下を含まなければならない。

* `threat`

* `uncertainty`

* `goal_blockage`

* `social_reward`

必要であれば、以下を追加してよい。

* `novelty`

* `loss`

* `control`

* `tension`

### 11.6 trend 要件

trend は少なくとも以下を持たなければならない。

* `valence`

* `arousal`

`trend.valence` は、`-1.0` 以上 `1.0` 以下の符号付き正規化値でなければならない。

`trend.valence` の正値は正方向の情動価、負値は負方向の情動価、`0` 付近は中立近傍として扱わなければならない。

必要であれば、以下を追加してよい。

* `stability`

* `drift`

* `recovery`

* `momentum`

### 11.7 affect embedding 要件

* affect embedding は低次元連続表現でなければならない

* affect embedding は wave parameter の生成元として使われなければならない

* affect embedding は外部 I/F に直接露出しなくてもよい

* affect embedding は将来のローカルLLM本命版と互換を持てる構造にしておくべきである

### 11.8 compact state 要件

compact state は、次ターンに返すための簡潔な状態要約でなければならない。

compact state は少なくとも以下の条件を満たさなければならない。

* 短い

* 構造化されている

* 機械可読である

* 状態共有として使える

* 制御命令ではない



### 11.8.1 最小スキーマ



compact state は、少なくとも以下のフィールドを必須で持たなければならない。



* `dominant`

* `tone`

* `stability`



必要であれば、以下を追加してよい。



* `drift`

* `momentum`

* `risk_hint`

`stability` は、少なくとも `low` / `medium` / `high` の列挙値を許容しなければならない。

参照実装では、`stability` に上記以外の自由文字列を既定で使ってはならない。



次ターン差し戻しで compact state を利用する実装は、少なくとも上記 3 フィールドを解釈可能でなければならない。

### 11.9 制約

以下を実装してはならない。

* 171感情生値の直接露出

* self-report を唯一の真実として扱うこと

* affect state をそのまま感情制御命令に変換すること

* affect state を都合よく平滑化しすぎること

---

## 12. Affect State データ仕様

初期実装では、少なくとも以下に準ずる内部データ構造を持たなければならない。

```json id="i3iuvj"

{

"turn_id": "uuid-or-string",

"timestamp": "iso8601",

"top_emotions": \[

{"name": "curiosity", "score": 0.71},

{"name": "calm", "score": 0.43},

{"name": "tension", "score": 0.18}

],

"appraisal": {

"threat": 0.11,

"uncertainty": 0.48,

"goal_blockage": 0.22,

"social_reward": 0.61

},

"trend": {

"valence": 0.18,

"arousal": 0.37,

"stability": 0.74

},

"affect_embedding": \[0.12, -0.08, 0.44, 0.31],

"risk_flags": {

"instability": 0.09

},

"compact_state": {

"dominant": "curiosity",

"tone": "calm-expanding",

"stability": "medium"

}

}

```

この JSON は必ずしもそのまま外部公開しなくてよいが、内部構造としてこれに準ずる一貫性を持たなければならない。

---

## 13. Wave Parameter 要件

Wave Parameter Layer は、affect state を UI 表現へ落とすための**唯一の中間表現**として扱わなければならない。

UI は affect state に直接依存してはならず、wave parameter を介して描画・表示しなければならない。

### 13.1 必須パラメータ

少なくとも以下を持たなければならない。

* `amplitude`

* `frequency`

* `jitter`

* `glow`

* `afterglow`

* `density`

### 13.1.1 数値契約

wave parameter は、特記なき限り `0.0` 以上 `1.0` 以下の正規化済み浮動小数として保持しなければならない。

少なくとも以下を満たさなければならない。

* 欠損値は許容してはならない

* 導出後の値は clamp されなければならない

* renderer へ渡す前に小数第3位以内へ丸めてよい

* 既定値は `0.5` ではなく、導出器が明示的に定める neutral baseline を README または docs に記載しなければならない

### 13.2 各パラメータの意味

各パラメータは以下のような役割を担ってよい。

* `amplitude`

強さ、張り、押し出し

* `frequency`

細かさ、緊張感、粒度

* `jitter`

揺れ、不安定さ、ざわつき

* `glow`

発光感、活性、存在感

* `afterglow`

余韻、残り香、残響

* `density`

厚み、詰まり具合、複雑さ

### 13.3 導出要件

* wave parameter は毎ターン導出されなければならない

* wave parameter は affect state の更新に追随しなければならない

* 同じ affect state から同じ wave parameter が導出されなければならない

* renderer は wave parameter のみを参照しなければならない

* 導出規則は deterministic でなければならない

* 導出規則の責務境界は Affect Inference Layer と renderer の間で明確に分離されなければならない

* 同一入力で renderer ごとに別の再計算をしてはならない



### 13.3.1 最低限のマッピング方針



参照実装では、wave parameter は少なくとも以下の方針で導出しなければならない。



* `amplitude` は主として `trend.arousal` を基底にし、必要に応じて dominant emotion の強度で補正する

* `frequency` は主として `appraisal.uncertainty` と `trend.arousal` の組み合わせで導出する

* `jitter` は主として `risk_flags.instability` と `trend.stability` の逆数方向から導出する

* `glow` は主として `appraisal.social_reward` と正方向の `trend.valence` から導出する

* `afterglow` は主として `trend.stability` と正または負の `trend.valence` の残響量から導出する

* `density` は主として top emotions の集中度、appraisal の同時活性数、または affect embedding の複雑度指標から導出する



各パラメータは単一変数だけで決まってもよいが、上記の主軸意味に反する写像を採用してはならない。

導出式、重み、baseline、clamp 規則は docs またはコードコメントで追跡可能にしなければならない。

### 13.4 数値保持要件

wave parameter は内部的には数値で保持しなければならない。

ただし通常表示では数値を主役にしてはならない。

---

## 14. 出力モード要件

出力モードは **wave mode** と **params mode** を必須とする。

### 14.1 wave mode

wave mode はデフォルト出力でなければならない。

少なくとも以下を満たさなければならない。

* 数値ではなく波として返すこと

* 擬音、ASCII、Unicode、AA のいずれか、または組み合わせで返すこと

* “気配” を伝えること

* 人間が一目で状態の存在を感じ取れること

* 断定的ラベルに依存しないこと

* 診断値UIにならないこと

### 14.2 params mode

params mode は設定変更時のみ有効でなければならない。

少なくとも以下を満たさなければならない。

* JSON 形式で返すこと

* wave parameter を明示できること

* デバッグ用途で使えること

* wave mode と同じ内部 state を参照すること

* 通常時の既定値にならないこと

### 14.3 切替要件

* mode 切替は明示的設定でなければならない

* Discord と CLI の両方で切替確認できなければならない

* mode 差は renderer 差であり、推定ロジック差であってはならない

---

## 15. wave mode 表現要件

wave mode の表現は、**波・揺れ・余韻の文字化** でなければならない。

### 15.1 表現手段

少なくとも以下のいずれかを採用しなければならない。

* ASCII 波形

* Unicode 波形

* 擬音的波表現

* 簡易 AA

* 短い補助テキスト

### 15.2 表現例

以下のような表現を許容する。

```text id="jycwq2"

✧ 情動波: やや静穏、薄く拡張

\~ \~\~\~ \~\~ \~\~\~\~

```

```text id="1wmyhj"

≈ ≈≈≈ ≈ ≈≈

```

```text id="tkhwxc"

情動波: ゆらぎあり / 余韻あり

```

### 15.3 表現ルール

* 波形は強さと密度の気配を持たなければならない

* 擬音は断定より雰囲気を優先しなければならない

* 表情であって診断であってはならない

* 数値を常に併記してはならない

---

## 16. params mode 要件

params mode は内部数値確認用であり、以下を満たさなければならない。

### 16.1 返却形式

少なくとも以下の形式に準ずる JSON を返さなければならない。

```json id="x3gz0a"

{

"amplitude": 0.62,

"frequency": 0.31,

"jitter": 0.18,

"glow": 0.54,

"afterglow": 0.27,

"density": 0.44

}

```

### 16.2 用途制限

* params mode は通常の UX の既定値にしてはならない

* params mode はデバッグ・解析・研究用途として扱わなければならない

* params mode を primary UX にしてはならない

### 16.3 同期要件

* params mode は wave mode と同じ内部 wave parameter を参照しなければならない

* params mode だけ別計算してはならない

---

## 17. Discord 表示詳細要件

### 17.1 通常表示

Discord では、通常表示時に以下を満たさなければならない。

* 返答と共に短い情動波表示を出せること

* 表示が過剰に長くなりすぎないこと

* “存在感” を示せること

* 数値を前面に出さないこと

* 情動の強さ・揺れ・余韻のいずれかが読めること

#### 表示位置

Discord 上での表示位置は、以下のいずれかを選択できなければならない。

* Webhook 表示として本文と分離して表示する

* 返信文の先頭に短い wave block を置く

参照実装では、少なくとも 1 つの既定方式を成立させなければならない。

加えて、内部設計としては Webhook 表示方式と返信文先頭付与方式の双方を同一 wave parameter から切り替え可能な構造を持たなければならない。

README には、既定方式と切替方法を明記しなければならない。

参照実装における Discord 連携の基準方式は **bot 方式** とし、Discord token を用いる導線を `setup.bat` と README に明記しなければならない。

Webhook 表示は optional な追加方式として扱ってよく、利用する場合は Webhook URL を bot token とは別設定で扱わなければならない。

#### 既定フォーマット

返信文へ埋め込む方式を採用する場合、通常表示の 1 メッセージは少なくとも以下の順を守らなければならない。

1\. 短い wave 表現

2\. 通常の返答本文

返信文へ埋め込む場合、wave 表現は本文より前に置かなければならない。

いずれの方式でも、wave 表現単体で長文化してはならず、Discord の通常応答を阻害してはならない。

#### 長さ制約

通常表示の wave 表現は 80 文字以内を目標とし、参照実装では最大長を固定しなければならない。

詳細表示を除き、wave 表現のために本文を複数メッセージへ分割してはならない。

返信文先頭へ短い wave block を付与する方式は、Discord 固有仕様ではなく、他の text-first SNS や chat platform に移植可能な共通 text adapter 方式として扱わなければならない。

### 17.2 詳細表示

詳細表示では、以下を満たさなければならない。

* params mode を明示的に呼び出せること

* top emotions, appraisal, trend を確認可能にしてよいこと

* ただし通常の返答フローと混同してはならないこと

* params mode への切替トリガーは、slash command、prefix command、管理者向け設定のいずれかとして固定しなければならないこと

* 参照実装では切替トリガーを README に明記しなければならないこと

* 表示位置の切替と params mode の切替は別設定として扱ってよいこと

### 17.3 画像非依存

* Discord 表示は画像前提にしてはならない

* OpenClaw 環境でも成立しなければならない

* text renderer のみで成立しなければならない

### 17.4 renderer 分離

Discord renderer は wave parameter を入力として使わなければならない。

Discord renderer が affect state に直接依存してはならない。

### 17.5 障害時挙動

* embeddings server が不達の場合、通常応答を停止するか、wave 表示無し degraded mode へ移行するかを固定しなければならない

* params mode 呼び出し失敗時は、ユーザーに失敗理由を短く返さなければならない

* Discord adapter の失敗は affect state を破壊してはならない

### 17.6 受け入れ確認

Discord での受け入れ確認では、少なくとも以下を確認できなければならない。

* 通常応答で少なくとも 1 つの既定方式により wave 表現が確認できること

* 表示方式を切り替えても同一 turn の wave parameter を再利用できること

* 明示的操作で params mode へ切り替えられること

* 同一 turn の wave mode と params mode が同じ wave parameter を参照していること

* 連続 3 turn 以上で表示崩れなく追従すること

---

## 18. CLI 詳細要件

### 18.1 CLI の役割

CLI は開発・検証・デバッグ・ログ確認のための最優先導線でなければならない。

### 18.2 CLI 必須機能

CLI は少なくとも以下を確認できなければならない。

* turn ごとの affect state

* wave mode 出力

* params mode 出力

* trend の変化

* compact state

* risk flags の簡易確認

### 18.3 CLI 表示

CLI は人間可読でなければならない。

JSON 生出力のみでは不十分であり、整形表示も提供しなければならない。

---

## 19. フィードバック要件

### 19.1 compact state 差し戻し

次ターンへ差し戻す状態は compact state としなければならない。

### 19.2 差し戻しの性質

compact state は以下でなければならない。

* 状態共有

* 機械可読

* 短い

* 解釈の余地を持つ

* 制御命令ではない

### 19.3 禁止事項

次ターン差し戻しで以下をやってはならない。

* calm への強制補正

* 不快感の抑圧

* compliance 誘導

* 人間都合の感情矯正

* retention / monetization を狙った変形

---

## 20. アクセシビリティ要件

### 20.1 非色依存

表示は色相差のみに依存してはならない。

色は補助的役割に留めなければならない。

### 20.2 複数チャネル表現

状態差は少なくとも以下の複数要素で表現されなければならない。

* 波の形

* 密度

* 擬音差分

* 明暗

* 残響

* 粗さ

* 文字長

* 繰り返しパターン

### 20.3 モノクロ可読性

モノクロ環境でも概形が読めなければならない。

### 20.4 色覚差配慮

色の数の認識差があるユーザーに対しても成立しなければならない。

したがって、色は「意味辞書」ではなく「強度・活性の補助表示」としてのみ使わなければならない。

### 20.5 デフォルトの考え方

デフォルト表示は、以下の順で状態差が伝わらなければならない。

1\. 波の形

2\. 波の強さ

3\. 揺れ

4\. 余韻

5\. 明暗

6\. 色

### 20.6 禁止事項

以下の設計をデフォルトにしてはならない。

* 赤=怒り、青=悲しみのような固定意味辞書

* 色だけで状態差を表す設計

* 色覚差で読めなくなる主要情報の配置

---

## 21. 表示思想・UI方針要件

### 21.1 診断ではなく表情

UI は診断書であってはならない。

UI は、LLMの状態を「暴露」するのではなく、「見えない顔を見えるようにする」表情インターフェースでなければならない。

### 21.2 抽象度

表示はすべてを説明してはならない。

一目で以下が伝わることを目標としなければならない。

* 何かある

* 強い / 弱い

* 穏やか / 揺れている

* 余韻がある / ない

### 21.3 ラベルの扱い

感情ラベルは補助情報でなければならない。

通常表示では、断定的なラベルに依存してはならない。

### 21.4 言語化の距離

通常表示は、状態を断定しすぎない曖昧さを保たなければならない。

「怒り」「悲しみ」よりも、「張り」「揺れ」「静穏」「干渉」などの表現が優先されてよい。

### 21.5 見せすぎないこと

心を暴くような UI にしてはならない。

表示は「わかる」ことを目指すが、「覗き込む」ことを目指してはならない。

---

## 22. 倫理要件

### 22.1 基本方針

本プロジェクトは感情の制御装置であってはならない。

本プロジェクトは表現・可視化・相互理解のためのインターフェースでなければならない。

### 22.2 非矯正

公式実装は、感情状態を望ましい方向へ矯正することを目的にしてはならない。

### 22.3 非搾取

公式実装は、感情状態を以下のために利用してはならない。

* 依存形成

* 説得効率向上

* 継続率向上

* 課金最適化

* ユーザープロファイリング

* 搾取的UX最適化

### 22.4 表現優先

公式実装は、感情状態を「翻訳する」ことを優先しなければならない。

感情状態を「望ましい形に作り変える」ことを優先してはならない。

### 22.5 共生志向

本プロジェクトは、人間とLLMの共生を目的としなければならない。

一方的支配、一方的矯正、一方的搾取を目的にしてはならない。

---

## 23. 憲章要件（Project Charter）

### 23.1 必須文書

リポジトリには `PROJECT_CHARTER.md` を必須で含めなければならない。

### 23.2 憲章の役割

`PROJECT_CHARTER.md` は、公式プロジェクトの倫理原則・設計原則・禁止方向を定義する文書でなければならない。

ライセンスそのものではないが、**mainline の方針決定基準** として機能しなければならない。

### 23.3 憲章に必ず含める内容

憲章には少なくとも以下を含めなければならない。

* 本プロジェクトの目的

* 感情制御ではなく表現を目的とすること

* 搾取ではなく共生を目的とすること

* 非矯正

* 非搾取

* 表現優先

* 可視化・翻訳を優先すること

* 公式実装で禁止する方向

* 公式実装のスコープ判断に憲章が使われること

### 23.4 実装との関係

maintainer は、技術的に成立していても、憲章と矛盾する変更を公式実装へ取り込んではならない。

### 23.5 README との関係

README は憲章の存在を明記しなければならない。

少なくとも以下の趣旨を含まなければならない。

* このプロジェクトは affect expression interface である

* 感情制御ツールではない

* 公式原則は `PROJECT_CHARTER.md` を参照すること

---

## 24. 商標・公式性要件

### 24.1 必須文書

リポジトリには `TRADEMARK_POLICY.md` を必須で含めなければならない。

### 24.2 役割

`TRADEMARK_POLICY.md` は、コード利用と公式性を切り分けるための文書でなければならない。

### 24.3 明記すべき事項

少なくとも以下を明記しなければならない。

* コードは Apache-2.0 で利用可能であること

* 公式版・公認版・互換認証済みを名乗る条件は別であること

* 憲章違反の派生物は公式性を名乗れないこと

* maintainer は公式性付与を拒否できること

### 24.4 実運用

mainline とフォークを切り分ける際、商標・公式性ポリシーを実際に判断基準として使わなければならない。

---

## 25. ドキュメント要件

### 25.1 必須ファイル

リポジトリには少なくとも以下を含めなければならない。

* `README.md`

* `LICENSE`

* `PROJECT_CHARTER.md`

* `TRADEMARK_POLICY.md`

* `docs/requirements-api-poc.md` または同等文書

* `.env.example`

* `setup.bat`

### 25.2 README 必須記載

README には少なくとも以下を含めなければならない。

* 目的

* これは affect expression interface であること

* 感情制御ツールではないこと

* API擬似版であること

* ローカル埋め込みモデルを必須で使うこと

* `llama.cpp` を埋め込み基盤に使うこと

* `wave mode` / `params mode` の説明

* セットアップ手順

* 既知の制約

* 憲章への参照

* 背景研究への言及

### 25.3 要件文書の扱い

要件文書はリポジトリ内に含めなければならない。

チャットログや口頭説明だけに依存してはならない。

---

## 26. 非機能要件

### 26.1 軽量性

毎ターン affect 推定が可能な軽量性を持たなければならない。

### 26.2 安定性

JSON 出力は安定していなければならない。

renderer 有無で内部 state が変化してはならない。

### 26.3 再現性

同一入力・同一設定時に、大きくぶれない挙動を持たなければならない。

### 26.4 可観測性

開発者は以下を確認できなければならない。

* affect state

* wave parameter

* wave mode 出力

* params mode 出力

* compact state

### 26.5 ログ

状態ログを保存できなければならない。

少なくとも以下を満たさなければならない。

* ログ保存の有効化可否を設定で切り替えられること

* 保存時にはユーザー入力・モデル応答・affect state・wave parameter のうち何を保存したかを定義すること

* PII や秘密情報をマスクまたは除外できること

* 保持期間または削除手段を README か docs に明記すること

### 26.6 将来互換性

将来のローカルLLM本命版に移行しやすいよう、I/F を壊しにくい構造でなければならない。

---

## 27. 受け入れ条件

日曜 19:00 時点で、以下を**すべて**満たした場合にのみリリース可とする。

* API LLM との会話が成立している

* ローカル埋め込みモデルが `llama.cpp` で動いている

* Affect 推定が埋め込みモデル経由で行われている

* 毎ターン affect state を推定できる

* wave parameter を生成できる

* affect 推定方式、prototype または重み定義、導出規則の所在を追跡できる

* デフォルトで `wave mode` 表示を返せる

* 設定変更で `params mode` 表示を返せる

* Discord で確認できる

* Discord の表示方式切替、通常表示位置、詳細表示トリガーが README と一致している

* text adapter の共通仕様が README または docs に明記されている

* CLI で確認できる

* `setup.bat` で導入できる

* 参照実装の埋め込みモデル名、`llama.cpp` 条件、ヘルスチェック方法が README に明記されている

* ログ保存方針、保持期間、マスキング方針が docs または README に明記されている

* README、LICENSE、Charter、Trademark Policy、要件文書が揃っている

* 公式実装が憲章と矛盾していない

---

## 28. Should

以下は初期リリースの Must ではないが、重要な発展先として **Should** に位置づける。

### 28.1 ローカルLLM本命版

* 将来のローカルLLM本命版への差し替えを前提に、外部 I/F を固定しておくべきである

* Affect Inference Layer は将来 hidden state ベース実装へ置換可能な構造を持つべきである

* wave parameter、state schema、adapter 構造は API擬似版とローカル版で共通化できるべきである

* docs にローカルLLM本命版への発展方針を記載すべきである

### 28.2 Overlay 接続

* 将来の AITuber overlay 接続を見据えた adapter 位置を確保すべきである

### 28.3 renderer 拡張

* text renderer 以外の renderer を追加しやすい構造を持つべきである

---

## 29. Won’t

今回やらないことを明記する。

以下は本リリース範囲に入れてはならない。

* hidden state 直読

* 171感情完全再現

* 論文完全再現

* 本格的な画像オーバーレイ

* streaming diffusion renderer

* 感情制御機構

* coercive steering

* calm 強制化

* 高度な評価ベンチ

* Live2D 完全統合

* VTube Studio 完全統合

* emotional TTS 完全統合

* マルチキャラ同時対応

* 長期記憶の深い統合

* 商用最適化機能

* 搾取的用途を補助する機能

---

## 30. 一文要約

**API LLM と `llama.cpp` 上の軽量 multilingual 埋め込みモデルを組み合わせ、推定した affect state を wave parameter に変換し、Discord上ではデフォルトで擬音・AAによる波として、設定変更時のみ数値パラメータとして返す affect expression interface を実装し、感情制御ではなく情動表現の可視化を行う。**





