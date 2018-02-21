import sys
import unittest
from nlelement import nlelement, cabocha_extended

class CabochaExtendeTest(unittest.TestCase):
    """cabocha_extendedの検証コード
    生文解析を行った結果の検証
    """
    def setUp(self):
        pass

    def test_load_chunk(self):
        sample_sent = """* 0 2D 0/1 -2.323553
太郎    名詞,固有名詞,人名,名,*,*,太郎,タロウ,タロー
は      助詞,係助詞,*,*,*,*,は,ハ,ワ
* 1 2D 0/1 -2.323553
プリウス        名詞,一般,*,*,*,プリウス,プリウス,プリウス
を      助詞,格助詞,一般,*,*,*,を,ヲ,ヲ
* 2 -1D 0/1 0.000000
買っ    動詞,自立,*,*,五段・ワ行促音便,連用タ接続,買う,カッ,カッ
た      助動詞,*,*,*,特殊・タ,基本形,た,タ,タ
EOS
"""
        item = cabocha_extended.load_from_text(sample_sent, as_label=False)
        doc = item[0]

        for i, sent in enumerate(doc.sentences):
            print(sent.get_surface)
