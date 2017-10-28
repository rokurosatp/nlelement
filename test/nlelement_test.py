import unittest
from nlelement import nlelement, cabochainput, KNBCInput


def __split_with_eos__(lines: list):
    result = []
    for subline in lines:
        line = subline[0:-1] if len(subline) > 0 and subline[-1] == '\n' else subline
        if len(line) == 0:
            continue
        if line == "EOS":
            yield result
            result = []
        elif line[0] == '#':
            pass
        else:
            result.append(line)

@unittest.skip("KNBの共参照仕様が今使ってるBCCWJの仕様と合わないため")
class KNBCLoaderTest(unittest.TestCase):
    """KNBC関連のテストを実行する＜テスト停止中＞
    ※BCCWJのテストに適応するのが面倒なのでテストを停止してます
    """
    def test_chunk_simple(self):
        """KNBの文節アノテーションの解析動作を確認する
        """
        test_str = '* 1D <BGH:携帯/けいたい><文節内><係:文節内><文頭><サ変><括弧始><引用内文頭><体言><名詞項候補><先行詞候補><非用言格解析:動><態:未定><正規化代表表記:携帯/けいたい><C用;【不特定:人】;ガ;-1;-1;9.999:(文外)><C用;【電話】;ヲ;0;1;9.999:KN001_Keitai_1-1-1-01(同一文):1タグ>'
        item = KNBCInput.Chunk(0, 0, test_str)
        self.assertEqual(item.sid, 0)
        self.assertEqual(item.cid, 0)
        self.assertEqual(item.link_id, 1)
    def test_token_simple(self):
        """KNBの単語アノテーションの解析動作を確認する
        """
        test_str = 'もはや もはや もはや 副詞 8 * 0 * 0 * 0 "代表表記:もはや/もはや" <代表表記:もはや/もはや><正規化代表表記:もはや/もはや><文頭><かな漢字><ひらがな><自立><内容語><意味有><タグ単位始><文節始><文節主辞>'
        token = KNBCInput.Token(0, test_str)
        self.assertEqual(token.surface, 'もはや')
        self.assertEqual(token.read, 'もはや')
        self.assertEqual(token.basic_surface, 'もはや')
        self.assertEqual(token.part, '副詞')
        self.assertEqual(token.part_id, 8)
        self.assertEqual(token.attr1, '*')
        self.assertEqual(token.attr2, '*')
        self.assertEqual(token.pos, '副詞-*-*')
        self.assertEqual(token.is_content, True)
        self.assertEqual(token.is_indep, True)    
    def test_load_sentence(self):
        """KNBCフォーマットのテスト用ファイルを読み込み,テストを行う
        """
        file = open("test/test_data/knbc_input_senttest", "r", encoding='euc-jp')
        text = file.readlines()
        sent = KNBCInput.Sentence(0, text)
        self.assertEqual(sent.name, "S-ID:TEST001_Test_1-1-1-01")
        self.assertEqual(len(sent.chunks), 3)
        self.assertEqual(len(sent.tokens), 4)
        for (cid, chunk) in enumerate(sent.chunks):
            self.assertEqual(chunk.cid, cid)
        self.assertEqual(sent.chunks[0].link_id, 1)
        self.assertEqual(sent.chunks[1].link_id, 2)
        self.assertEqual(sent.chunks[2].link_id, -1)
        self.assertEqual(sent.chunks[0].first_mentioned, True)
        self.assertEqual(sent.chunks[1].first_mentioned, False)
        self.assertEqual(sent.chunks[2].first_mentioned, False)
        self.assertEqual(sent.chunks[0].link, sent.chunks[1])
        self.assertEqual(sent.chunks[1].link, sent.chunks[2])
        self.assertEqual(sent.chunks[2].link, None)
        self.assertEqual(sent.chunks[2].reverse_links[0], sent.chunks[1])
        self.assertEqual(sent.chunks[1].reverse_links[0], sent.chunks[0])
        self.assertTrue("coref" not in sent.chunks[0].coreference_link)
        self.assertTrue("coref" not in sent.chunks[1].coreference_link)
        self.assertTrue("coref" in sent.chunks[2].coreference_link)
        self.assertTrue("ヲ" in sent.chunks[1].coreference_link)
        self.assertEqual(sent.chunks[2].coreference_link["coref"].antecedent_ref.sid, 0)
        self.assertEqual(sent.chunks[2].coreference_link["coref"].antecedent_ref.cid, 0)
        self.assertEqual(sent.chunks[1].coreference_link["ヲ"].antecedent_ref.sid, 0)
        self.assertEqual(sent.chunks[1].coreference_link["ヲ"].antecedent_ref.cid, 0)
        self.assertEqual(sent.chunks[2].coreference_link["coref"].surface, '表層')
        self.assertEqual(sent.tokens[0].surface, '表層')
        self.assertEqual(sent.tokens[0].read, 'よみ')
        self.assertEqual(sent.tokens[0].basic_surface, '基本')
        self.assertEqual(sent.tokens[0].part, '名詞')
        self.assertEqual(sent.tokens[0].part_id, 6)
        self.assertEqual(sent.tokens[0].attr1, '普通名詞')
        self.assertEqual(sent.tokens[0].attr2, '*')
        self.assertEqual(sent.tokens[0].pos, '名詞-普通名詞-*')
        self.assertEqual(sent.tokens[0].normalnoun, True)
        self.assertEqual(sent.tokens[0].sahen, False)
        self.assertEqual(sent.tokens[0].adjectivenoun, False)
        self.assertEqual(sent.tokens[0].conj_type, "*")
        self.assertEqual(sent.tokens[0].conj_form, "*")
        self.assertEqual(sent.tokens[0].is_content, True)
        self.assertEqual(sent.tokens[0].named_entity, "TEST")
        self.assertEqual(sent.tokens[0].named_entity_part, "テスト")
        self.assertEqual(sent.tokens[1].is_content, False)
        self.assertEqual(sent.tokens[2].part, '動詞')
        self.assertEqual(sent.tokens[2].attr1, '*')
        self.assertEqual(sent.tokens[2].pos, '動詞-*-子音動詞ワ行')
        self.assertEqual(sent.tokens[2].conj_type, "子音動詞ワ行")
        self.assertEqual(sent.tokens[2].conj_form, "未然形")
        self.assertEqual(sent.tokens[2].is_content, True)
        self.assertEqual(sent.tokens[2].surface, 'テスト')
        self.assertEqual(sent.tokens[3].surface, '試験')
        self.assertEqual(sent.tokens[3].is_content, True)
        self.assertEqual(sent.chunks[0].tokens[0], sent.tokens[0])
        self.assertEqual(sent.chunks[1].tokens[0], sent.tokens[2])
        self.assertEqual(sent.chunks[2].tokens[0], sent.tokens[3])
        file.close()
    def test_particle(self):
        with open("test/test_data/particle_test_juman.txt", "r", encoding='cp932') as file:
            text = file.readlines()
            sentences = []
            for lines in __split_with_eos__(text):
                sentences.append(KNBCInput.Sentence(0, lines))
            self.assertEqual(sentences[0].chunks[0].particle.surface, 'が')
            self.assertEqual(sentences[1].chunks[0].particle.surface, 'を')
            self.assertEqual(sentences[2].chunks[0].particle.surface, 'に')
            self.assertEqual(sentences[3].chunks[0].particle.surface, 'から')
            self.assertEqual(sentences[4].chunks[0].particle.surface, 'へ')
            self.assertEqual(sentences[5].chunks[0].particle.surface, 'と')
            self.assertEqual(sentences[6].chunks[0].particle.surface, 'より')
            self.assertEqual(sentences[7].chunks[0].particle.surface, 'で')
            self.assertEqual(sentences[8].chunks[1].particle.surface, 'が')
            self.assertEqual(sentences[8].chunks[4].particle.surface, 'と')
            self.assertEqual(sentences[8].chunks[6].particle.surface, 'は')
            self.assertEqual(sentences[9].chunks[0].particle.surface, 'は')
            self.assertEqual(sentences[11].chunks[1].particle.surface, 'で')
            self.assertEqual(sentences[11].chunks[3].particle.surface, 'が')
            self.assertEqual(sentences[11].chunks[4].particle.surface, 'を')
            self.assertEqual(sentences[11].chunks[6].particle.surface, 'を')
            self.assertEqual(sentences[12].chunks[0].particle.surface, 'は')
            self.assertEqual(sentences[12].chunks[1].particle.surface, 'が')
            self.assertEqual(sentences[12].chunks[2].particle.surface, 'も')

            self.assertEqual(sentences[0].chunks[0].get_particle_surf(), 'が')
            self.assertEqual(sentences[1].chunks[1].get_particle_surf(), '')
            self.assertEqual(sentences[1].chunks[0].get_particle_surf(), 'を')
            self.assertEqual(sentences[2].chunks[0].get_particle_surf(), 'に')


@unittest.skip("モジュール cabochaが機能置き換え")
class CabochaLoaderTest(unittest.TestCase):
    """cabochainputの機能テスト なんだけどもはや不要な気が・・・
    """
    def test_chunk_simple(self):
        """CaboChaの文節アノテーションの解析動作を確認する
        """
        test_str = '* 0 1D 0/0 0.00000'
        item = cabochainput.Chunk(0, 0, test_str)
        self.assertEqual(item.sid, 0)
        self.assertEqual(item.cid, 0)
        self.assertEqual(item.link_id, 1)
    def test_token_simple(self):
        """Cabochaの単語アノテーションの解析動作を確認する
        """
        test_str = 'もはや\t副詞,*,*,*,*,*,もはや,もはや\t0'
        token = cabochainput.Token(0, test_str)
        self.assertEqual(token.surface, 'もはや')
        self.assertEqual(token.read, 'もはや')
        self.assertEqual(token.basic_surface, 'もはや')
        self.assertEqual(token.part, '副詞')
        #self.assertEqual(token.part_id, 8)
        self.assertEqual(token.attr1, '*')
        self.assertEqual(token.attr2, '*')
        self.assertEqual(token.pos, '副詞-*-*')
        self.assertEqual(token.is_content, False)
        self.assertEqual(token.is_indep, False)    
    def test_load_sentence(self):
        """Cabochaフォーマットのテスト用ファイルを読み込み,テストを行う
        """
        file = open("test/test_data/cabocha_test.cab", "r", encoding='utf-8')
        text = file.readlines()
        sent = cabochainput.Sentence(0, text)
        self.assertEqual(sent.name, "")
        self.assertEqual(len(sent.chunks), 3)
        self.assertEqual(len(sent.tokens), 4)
        for (cid, chunk) in enumerate(sent.chunks):
            self.assertEqual(chunk.cid, cid)
        self.assertEqual(sent.chunks[0].link_id, 1)
        self.assertEqual(sent.chunks[1].link_id, 2)
        self.assertEqual(sent.chunks[2].link_id, -1)
        self.assertEqual(sent.chunks[0].first_mentioned, True)
        self.assertEqual(sent.chunks[1].first_mentioned, False)
        self.assertEqual(sent.chunks[2].first_mentioned, False)
        self.assertEqual(sent.chunks[0].link, sent.chunks[1])
        self.assertEqual(sent.chunks[1].link, sent.chunks[2])
        self.assertEqual(sent.chunks[2].link, None)
        self.assertEqual(sent.chunks[2].reverse_links[0], sent.chunks[1])
        self.assertEqual(sent.chunks[1].reverse_links[0], sent.chunks[0])
        self.assertEqual(sent.tokens[0].surface, '表層')
        self.assertEqual(sent.tokens[0].read, 'よみ')
        self.assertEqual(sent.tokens[0].basic_surface, '基本')
        self.assertEqual(sent.tokens[0].part, '名詞')
        # TODO: JUMANの名詞IDと単語IDの対応付けができてない
        #self.assertEqual(sent.tokens[0].part_id, 6)
        self.assertEqual(sent.tokens[0].attr1, '一般')
        self.assertEqual(sent.tokens[0].attr2, '*')
        self.assertEqual(sent.tokens[0].pos, '名詞-一般-*')
        self.assertEqual(sent.tokens[0].normalnoun, True)
        self.assertEqual(sent.tokens[0].sahen, False)
        self.assertEqual(sent.tokens[0].adjectivenoun, False)
        self.assertEqual(sent.tokens[0].conj_type, "*")
        self.assertEqual(sent.tokens[0].conj_form, "*")
        self.assertEqual(sent.tokens[0].is_content, True)
        self.assertEqual(sent.tokens[0].named_entity, "TEST")
        self.assertEqual(sent.tokens[0].named_entity_part, "テスト")
        self.assertEqual(sent.tokens[1].is_content, False)
        self.assertEqual(sent.tokens[2].part, '動詞')
        self.assertEqual(sent.tokens[2].attr1, '自立')
        self.assertEqual(sent.tokens[2].pos, '動詞-自立-*')
        self.assertEqual(sent.tokens[2].conj_type, "子音動詞ワ行")
        self.assertEqual(sent.tokens[2].conj_form, "未然形")
        self.assertEqual(sent.tokens[2].is_content, True)
        self.assertEqual(sent.tokens[2].surface, 'テスト')
        self.assertEqual(sent.tokens[3].surface, '試験')
        self.assertEqual(sent.tokens[3].is_content, True)
        self.assertEqual(sent.chunks[0].tokens[0], sent.tokens[0])
        self.assertEqual(sent.chunks[1].tokens[0], sent.tokens[2])
        self.assertEqual(sent.chunks[2].tokens[0], sent.tokens[3])
        file.close()