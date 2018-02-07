"""サンプル用のデータセット（db）を生成する
"""
import os
import pathlib
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

def sample_names():
    sample_id = 0
    while 1:
        yield 'SAMPLE_{}'.format(sample_id)
        sample_id += 1

def main():
    app = synchacall.AppCall('predicate/external/syncha-0.3.1.1/syncha')
    docs = []
    for raw_doc, name in zip(raw_samples, sample_names()):
        input_str = raw_doc.rstrip("\n") + "\nEOT\n"
        result_str = app.run('-I 0 -O 2 -u {}'.format('0'), input_str, throws=False)
        doc = cabocha_extended.load_from_text(result_str, as_label=True)[0]
        doc.name = name
        docs.append(doc)
    db_path = pathlib.Path('dat/sample_corpus.db')
    if db_path.exists():
        os.remove(str(db_path))
    sample_db = database.DatabaseLoader(str(db_path))
    sample_db.create_tables()
    sample_db.update_views()
    sample_db.save(docs)
