"""サンプル用のデータセット（db）を生成する
"""

from predicate.external import synchacall
from nlelement import nlelement, database, cabocha_extended

raw_samples = [
"""このサンプルはコーパスを正しくロードできているか確認をするためのテストデータです。
述語項構造解析ツール新茶で解析を行ったデータをデータベースに保存してください。
データは生のまま使用する予定です。
""",
"""太郎はハワイに行った。
そこにはすでに二郎がいた。
花子はその知らせを聞き、急遽駆け付けた。
太郎は引き続きハワイ旅行を楽しんでいる。
"""
]

def main():
    app = synchacall.AppCall('predicate/external/syncha-0.3.1.1/syncha')
    docs = []
    for raw_doc in raw_samples:
        result_str = app.run('-I 0 -O 2 -u {}'.format('0'), raw_doc.rstrip("\n\r")+"\nEOT\n", throws=False)
        doc = cabocha_extended.load_from_text(result_str, as_label=True)
        docs.append(doc)
    sample_db = database.DatabaseLoader('dat/sample_corpus.db')
    sample_db.save(docs)
