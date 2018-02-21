"""nlelementを使ったテスト用サンプルを作るための場所
"""
from nlelement import nlelement

class NlElementMaker:
    """コード上でそれなりに簡単なオブジェクトを作るためのクラス
    基本的にこのオブジェクト経由で安定したdocumentオブジェクトを作ってください。
    """
    def token(self, surface, pos):
        token = nlelement.Token()
        token.surface = surface
        poses = pos.split('-')
        token.part = poses[0]
        if len(poses) > 1:
            token.attr1 = poses[1]
        if len(poses) > 2:
            token.attr2 = poses[2]
        return token

    def chunk(self, head, func):
        chunk = nlelement.Chunk()
        chunk.head_position = head
        chunk.func_position = func
        return chunk

    def append_chunk_to_sentence(self, sentence, chunk):
        sentence.chunks.append(chunk)
        for token in chunk.tokens:
            sentence.tokens.append(token)

    def set_id_to_sentence(self, sentence, sid):
        sentence.sid = sid
        for cid, chunk in enumerate(sentence.chunks):
            chunk.sid = sid
            chunk.cid = cid

        for chunk in sentence.chunks:
            if chunk.link:
                chunk.link_id = chunk.link.cid

        for tid, token in enumerate(sentence.tokens):
            token.sid = sid
            token.tid = tid

    def set_id_to_sentences(self, document):
        for sid, sentence in enumerate(document.sentences):
            self.set_id_to_sentence(sentence, sid)
        
    def add_coreference_link(self, document, ana_sid, ana_tid, case, ant_sid, ant_tid):
        """述語項構造関係 共参照関係を追加する
        """
        ana_ref = nlelement.TokenReference(ana_sid, ana_tid)
        anaphora = document.refer(ana_ref)
        if anaphora:
            anaphora.coreference_link[case] = nlelement.CoreferenceEntry(
                ana_ref,
                nlelement.TokenReference(ant_sid, ant_tid), 0, 0, ""
            )

    def add_semantic_role(self, document, ana_sid, ana_tid, semrole, ant_sid, ant_tid):
        """意味役割をセットする
        """
        ana_ref = nlelement.TokenReference(ana_sid, ana_tid)
        anaphora = document.refer(ana_ref)
        if anaphora:
            if not hasattr(anaphora, "semroles"):
                setattr(anaphora, "semroles", dict())
            anaphora.semroles[semrole] = nlelement.TokenReference(ant_sid, ant_tid)

    def add_verb_semantic(self, document, sid, tid, semantic):
        ref = nlelement.TokenReference(sid, tid)
        verb = document.refer(ref)
        if verb:
            verb.semantic = semantic

class NlElementSampleMaker:
    def __init__(self):
        self.maker = NlElementMaker()
    def sample1(self):
        """取りあえず単純なサンプルを生成する
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('私', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('彼', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('助け', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc)
        return doc

    def sample_deppara_merge_a(self):
        """deppara的なチャンキングと文分けをするやつ
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('私', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('彼', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('助け', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        chunk.tokens.append(self.maker.token('＞', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('今日', '名詞'))
        chunk.tokens.append(self.maker.token('の', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 0)
        chunk.tokens.append(self.maker.token('思い出', '名詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[1]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc)
        return doc

    def sample_deppara_merge_b(self):
        """m_xml的な文分けをするやつのばあい、こうなってほしい
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('私', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('彼', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('助け', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 0)
        chunk.tokens.append(self.maker.token('＞', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('今日', '名詞'))
        chunk.tokens.append(self.maker.token('の', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 0)
        chunk.tokens.append(self.maker.token('思い出', '名詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc)
        return doc

    def sample_deppara_merge_b_unchunked(self):
        """deppara_merge専用のmergeクラス
        """
        doc = self.sample_deppara_merge_b()
        for sent in doc.sentences:
            sent.chunks = []
        return doc

    def sample_pas_annotation(self):
        """pasのアノテーション側用
        述語項関係、共参照関係に加えて文に一部
        """
        doc = nlelement.Document()
        doc.pas_annotated = True
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('私', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('花屋', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('行っ', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('そこ', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('美香', '名詞'))
        chunk.tokens.append(self.maker.token('が', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('い', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc) # NOTE: 共参照ラベルなどの値が正確に変換できないのでここでidを振る

        self.maker.add_coreference_link(doc, 0, 4, 'ga', 0, 0)
        self.maker.add_coreference_link(doc, 0, 4, 'ni', 0, 2)

        self.maker.add_coreference_link(doc, 1, 4, 'ga', 1, 2)
        self.maker.add_coreference_link(doc, 1, 4, 'ni', 1, 0)

        self.maker.add_coreference_link(doc, 1, 0, 'coref', 0, 2)


        return doc

    def sample_pas_original(self):
        """pasのテキスト原文側用
        アノテーションがなく、一部加筆がある
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('私', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('花屋', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('行っ', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('そこ', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('美香', '名詞'))
        chunk.tokens.append(self.maker.token('が', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('い', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('次回', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('続き', '動詞'))
        chunk.tokens.append(self.maker.token('ます', '助動詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[1]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc)
        return doc

    def sample_pth_annotation(self):
        """pthのアノテーション文側用
        """
        doc = nlelement.Document()
        doc.pt_annotated = True
        sentence = nlelement.Sentence()
        sentence.pt_annotated = True
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('そこ', '名詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('美香', '名詞'))
        chunk.tokens.append(self.maker.token('が', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('い', '動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        self.maker.set_id_to_sentences(doc)
        self.maker.add_semantic_role(doc, 0, 4, "経験者", 0, 2)
        self.maker.add_semantic_role(doc, 0, 4, "場所", 0, 0)
        self.maker.add_verb_semantic(doc, 0, 4, "状態変化なし(状態)-位置-存在")

        return doc



    def sample_pth_original(self):
        """pthの原文側用
        NOTE:pas_originalと全く同じ
        """
        return self.sample_pas_original()

    def sample_diffreference_converter_a(self):
        """DiffReferenceConverterのテストデータ(1)
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('アプリケーション', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(1, 2)
        chunk.tokens.append(self.maker.token('終了', '名詞'))
        chunk.tokens.append(self.maker.token('し', '動詞'))
        chunk.tokens.append(self.maker.token('まし', '助動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        chunk.tokens.append(self.maker.token('。', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[1]
        doc.sentences.append(sentence)
        
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(3, 3)
        chunk.tokens.append(self.maker.token('（', '記号'))
        chunk.tokens.append(self.maker.token('Help', '名詞'))
        chunk.tokens.append(self.maker.token(':', '名詞'))
        chunk.tokens.append(self.maker.token('H', '名詞'))
        chunk.tokens.append(self.maker.token('）', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        doc.sentences.append(sentence)

        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(1, 3)
        chunk.tokens.append(self.maker.token('続行', '名詞'))
        chunk.tokens.append(self.maker.token('する', '動詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(1, 2)
        chunk.tokens.append(self.maker.token('Esc', '名詞'))
        chunk.tokens.append(self.maker.token('キー', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 2)
        chunk.tokens.append(self.maker.token('押し', '動詞'))
        chunk.tokens.append(self.maker.token('て', '助詞'))
        chunk.tokens.append(self.maker.token('ください', '動詞'))
        chunk.tokens.append(self.maker.token('。', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[1].link = sentence.chunks[2]
        sentence.chunks[0].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        
        self.maker.set_id_to_sentences(doc)
        return doc

    def sample_diffreference_converter_b(self):
        """DiffReferenceConverterのテストデータ(2)
        """
        doc = nlelement.Document()
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('アプリケーション', '名詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(1, 2)
        chunk.tokens.append(self.maker.token('終了', '名詞'))
        chunk.tokens.append(self.maker.token('し', '動詞'))
        chunk.tokens.append(self.maker.token('まし', '助動詞'))
        chunk.tokens.append(self.maker.token('た', '助詞'))
        chunk.tokens.append(self.maker.token('。', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[1]
        doc.sentences.append(sentence)
        # length:=16
 
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(1, 3)
        chunk.tokens.append(self.maker.token('続行', '名詞'))
        chunk.tokens.append(self.maker.token('する', '動詞'))
        chunk.tokens.append(self.maker.token('に', '助詞'))
        chunk.tokens.append(self.maker.token('は', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(1, 2)
        chunk.tokens.append(self.maker.token('Esc', '名詞'))
        chunk.tokens.append(self.maker.token('キー', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 2)
        chunk.tokens.append(self.maker.token('押し', '動詞'))
        chunk.tokens.append(self.maker.token('て', '助詞'))
        chunk.tokens.append(self.maker.token('ください', '動詞'))
        chunk.tokens.append(self.maker.token('。', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[1].link = sentence.chunks[2]
        sentence.chunks[0].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        # length:=20
        
        sentence = nlelement.Sentence()
        chunk = self.maker.chunk(1, 2)
        chunk.tokens.append(self.maker.token('H', '名詞'))
        chunk.tokens.append(self.maker.token('キー', '名詞'))
        chunk.tokens.append(self.maker.token('で', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('ヘルプ', '名詞'))
        chunk.tokens.append(self.maker.token('を', '助詞'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        chunk = self.maker.chunk(0, 1)
        chunk.tokens.append(self.maker.token('開き', '動詞'))
        chunk.tokens.append(self.maker.token('ます', '助動詞'))
        chunk.tokens.append(self.maker.token('。', '記号'))
        self.maker.append_chunk_to_sentence(sentence, chunk)
        sentence.chunks[0].link = sentence.chunks[2]
        sentence.chunks[1].link = sentence.chunks[2]
        doc.sentences.append(sentence)
        # length:=13

        self.maker.set_id_to_sentences(doc)
        return doc