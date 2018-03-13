"""テキストを解析してdocにしてから単語のbi_gramを作成
"""
from nlelement.loaders import MeCabParser
from nlelement import nlelement

SAMPLE_TEXT = """テキストの本文です。
MeCabによって解析を行ってオブジェクトに変換し、bigramにします。
bigramは辞書オブジェクトとして保存されます。
"""
parser = MeCabParser()
doc = parser.parse_document(SAMPLE_TEXT)
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
print(n_gram_table)
