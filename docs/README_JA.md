# nlelement

## これはなに

自然言語文にある単語や文節、文と言った要素をオブジェクトにしたライブラリです

## モジュールの構成

* nlelement - 文書データを構成する要素オブジェクト（単語、文節、文、文書）の定義と、それに関するユーティリティ関数の一部を実装
* reference - 文章中の要素を一意に参照できる参照オブジェクトを定義（ポインタみたいなやつです）
* relation - 要素間の関係（述語項構造、共参照関係などが相当）のオブジェクト
* argument - 述語項構造の項情報、共参照関係情報と言った解析結果に相当する情報をオブジェクト化
* cabocha_extended - NAISTの拡張cabochaフォーマットを微妙に改変したフォーマットによる自然言語オブジェクト<->ファイルの変換
* database - 自然言語オブジェクト<->データベースの変換(このデータベースは現状、独自設計)
* KNBCInput - KNBコーパス->自然言語オブジェクトのローダを定義
* corpus_statistics - コーパスから基本的な統計情報の集計を行う処理を定義

## 使ってみる

### セットアップ

```
pip install git+https://github.com/rokurosatp/nlelement.git
```

### 適当な文をオブジェクトにする

MeCabによる解析（Tokenのみ）

```
from nlelement.loaders import MeCabParser

parser = MeCabParser()
# ランダムにロードされた文書データがdocに代入される
sent = parser.parse("太郎はプリウスを買った")    # 文を解析してロード

print(sent.tokens)  # 文中の単語が列挙される
```

Cabochaによる解析（文節(Chunk)情報、係り受け情報が付加される）

```
from nlelement.loaders import CabochaParser

parser = CabochaParser()
# ランダムにロードされた文書データがdocに代入される
sent = parser.parse("太郎はプリウスを買った")    # 文を解析してロード

print(sent.tokens)  # 文中の単語が列挙される
```

### 解析済みデータベースからロードする

```
from nlelement import database

loader = database.DatabaseLoader("test.db")
# ランダムにロードされた文書データがdocに代入される
doc = loader.load_one_sample()[0]
```

### 練習 単語のbi-gramを集計してみる

```
from nlelement import nlelement
# ※docはデータベースなどからすでに取得済みであると仮定
last_tok = None
n_gram_table = {}
for tok in nlelement.tokens(doc):
    if last_tok:
        key = (last_tok.surface, tok.surface)
        if key not in n_gram_table:
            n_gram_table[key] = 0
        n_gram_table[key] += 1
    last_tok = tok
```
