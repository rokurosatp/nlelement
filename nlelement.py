import re
class ChunkReference:
    def __init__(self, sid, cid):
        self.sid = sid
        self.cid = cid
    def to_tuple(self):
        return (self.sid, self.cid)
    def __bool__(self):
        return self.sid >= 0 or self.cid >= 0
    def __eq__(self, value):
        return self.sid == value.sid and self.cid == value.cid
    def __lt__(self, value):
        return self.sid < value.sid or (self.sid == value.sid and self.cid < value.cid)
    def __repr__(self):
        return '<Ch:{0},{1}>'.format(self.sid, self.cid)
class TokenReference:
    def __init__(self, sid, tid):
        self.sid = sid
        self.tid = tid
    def to_tuple(self):
        return (self.sid, self.tid)
    def __bool__(self):
        return self.sid >= 0 or self.tid >= 0
    def __lt__(self, value):
        return self.sid < value.sid or (self.sid == value.sid and self.sid < value.sid)
    def __eq__(self, value):
        return self.sid == value.sid and self.tid == value.tid
    def __repr__(self):
        return '<Tk:{0},{1}>'.format(self.sid, self.tid)

def make_reference(element):
    if isinstance(element, Chunk):
        return ChunkReference(element.sid, element.cid)
    elif isinstance(element, Token):
        return TokenReference(element.sid, element.tid)
    elif isinstance(element, Sentence):
        return element.sid
    return None
"""
KNBCの入力だけにとどまらなくなってきたので移動
"""
class Document:
    """文章のインスタンスを保持
    """
    def __init__(self):
        self.sentences = []
        self.name = ''
    def print_members(self):
        """メンバを標準出力に表示[デバッグ用]
        """
        print('name:'+self.name)
        print('sentences_count:'+str(self.sentences))
    def print_surfaces(self):
        """表層表現を標準出力に表示する
        """
        print(self.name)
        for sent in self.sentences:
            sent.print_surfaces()
    def print_coreference_tags(self):
        """存在する共参照関係を標準出力に表示
        """
        for sent in self.sentences:
            print(sent.get_surface())
            for token in sent.tokens:
                for name, coref in token.coreference_link.items():
                    if name == 'coref':
                        coref_chunk = coref.get_chunk(self)
                        coref_surf = coref.surface
                        if coref_chunk is not None:
                            coref_surf = coref_chunk.get_surface()
                        print('\tana :', token.get_surface(), '\tant:', coref_surf)
    def get_coreference_list(self):
        """文章内に存在する共参照関係を取得
        """
        result = []
        for sent in self.sentences:
            for token in sent.tokens:
                for name, coref in token.coreference_link.items():
                    if name == 'coref':
                        result.append(coref.get_feature_tuple())
        return result
    def get_predicate_term_list(self):
        """文章内に存在する述語項構造を取得
        """
        case_normalize_table = {
            'ガ':'ga',
            'ヲ':'o',
            '二':'ni',
        }
        result = []
        for sent in self.sentences:
            for token in sent.tokens:
                for name, coref in token.coreference_link.items():
                    if name in case_normalize_table:
                        feature_tuple = coref.get_feature_tuple()
                        case = case_normalize_table[name]
                    else:
                        feature_tuple = coref.get_feature_tuple()
                        case = name
                    result.append(
                        (feature_tuple[0], feature_tuple[1], feature_tuple[2], feature_tuple[3], case)
                    )
        return result
    def refer(self, ref):
        if isinstance(ref, ChunkReference):
            sentence = self.refer_sentence(ref.sid)
            if sentence:
                if ref.cid >= 0 and ref.cid < len(sentence.chunks):
                    return sentence.chunks[ref.cid]
        elif isinstance(ref, TokenReference):
            sentence = self.refer_sentence(ref.sid)
            if sentence:
                if ref.tid >= 0 and ref.tid < len(sentence.tokens):
                    return sentence.tokens[ref.tid]
        elif isinstance(ref, int):
            return self.refer_sentence(ref)
        return None
    def refer_sentence(self, sid):
        try:
            sentence = next(filter(lambda x: x.sid == sid, self.sentences))
        except StopIteration:
            return None
        return sentence
    def refer_chunk(self, sid, cid):
        """文節番号から文節インスタンスへの参照を取得
        """
        if sid >= 0 and sid < len(self.sentences):
            if cid >= 0 and cid < len(self.sentences[sid].chunks):
                return self.sentences[sid].chunks[cid]
        return None
    def refer_chunk_from_char_position(self, sid, char_position):
        """文節番号から文節インスタンスへの参照を取得
        """
        if sid >= 0 and sid < len(self.sentences):
            sent = self.sentences[sid]
            for (cid, position) in enumerate(sent.chunk_positions):
                if position >= char_position:
                    return sent.chunks[cid]
        return None
    def get_surface(self):
        """文章の文字列を文ごとに分けたリストの形で取得
        """
        raw_sentence = []
        for sent in self.sentences:
            raw_sentence.append(sent.get_surface())
        return raw_sentence

class Sentence:
    """
    文を格納するクラス
    """
    def __init__(self):
        self.chunk_positions = []
        self.chunks = []
        self.tokens = []
        self.sid = 0
        self.name = ''
        self.__in_q__ = 0       # クラスでもっているが生成時の一時的にしか使わない値なので注意
    def __link_chunk__(self, cid, chunk):
        """文中の文節の追加が終わった時点でリンク先、逆リンク先を追加
        Args:
            id (int):係り元二になるチャンク番号
            chunk (Chunk):係り先のチャンク
        """
        if 0 <= chunk.link_id < len(self.chunks):
            chunk.link = self.chunks[chunk.link_id]
            self.chunks[chunk.link_id].reverse_link_ids.append(cid)
            self.chunks[chunk.link_id].reverse_links.append(chunk)
    def post_initialize(self):
        """caseなどの遅延設定をしなければならないものをここで追加
        * 下で呼ばなきゃいけないってすげえ非合理的
        """
        chunk_position = 0
        for ｃid, chunk in enumerate(self.chunks):
            self.chunk_positions.append(chunk_position)
            chunk_position += len(chunk.get_surface())
            self.__link_chunk__(ｃid, chunk)
            chunk.set_token_info()
        self.add_first_mentioned()
    def add_first_mentioned(self):
        """first_mentionedの追加
        """
        for chunk in self.chunks:
            if chunk.is_cand_all():
                chunk.first_mentioned = True
                break
    def linkchunk(self, chunk):
        """chunkオブジェクトに割り当てられたlink_idを元にlink, revlinksの値をchunkに割り当てる
        Args:
            chunk (Chunk):リンク参照を割り当てるチャンクの名前
        """
        if chunk.link_id < 0:
            return None
        return self.chunks[chunk.link_id]
    def print_members(self):
        """オブジェクトのメンバ変数を標準出力に表示
        """
        print('id:'+str(self.sid))
        print('name:'+self.name)
        for chunk in self.chunks:
            chunk.print_members()
        print('chunks'+str(len(self.chunks)))
        print('tokens'+str(len(self.tokens)))
    def print_surfaces(self):
        """表層表現を標準出力に表示
        """
        print(str(self.sid), end=' :')
        for chunk in self.chunks:
            chunk.print_surfaces()
        print('')
    def chunk_from_token(self, token):
        """参照環境
        """
        for chunk in self.chunks:
            if chunk.tokens:
                if token.tid <= chunk.tokens[-1].tid:
                    return chunk
        return None
    def reverse_link(self, chunk):
        """逆参照を取得するジェネレータ
        """
        for link in chunk.reverse_link_ids:
            yield self.chunks[link]
    def get_length(self):
        return sum((token.get_length() for token in self.tokens))
    def get_surface(self):
        """表層表現を取得
        Returns:
            str: 表層表現の文字列
        """
        raw_sent = ''
        for token in self.tokens:
            raw_sent += token.surface
        return raw_sent
def __is_case__(token):
    if token is None or token.part != '助詞' or token.attr1 != '格助詞':
        return False
    return True
class CoreferenceEntry:
    """共参照関係のデータ
    文内の位置の参照なんだけど引数が爆増えするのでクラスを作ったほうがいいかもしれない
    """
    def __init__(self, anaphora_ref, antecedent_ref, begin_token, end_token, surface):
        """初期化、生成するときは文内の番号を参照する。
        Args:
            anaphora_ref (TokenReference): 照応詞の参照
            antecedent_ref (TokenReference): 先行詞の参照
            begin_token (int): 未使用、文節内の単語を参照することになったらこれを使う文節単位の場合-1を指定
            end_token (int): 未使用、文節内の単語を参照することになったらこれを使う文節単位の場合-1を指定
            surface (int): 先行詞の表層表現、文外照応の場合に先行詞を確認する用
        """
        self.anaphora_ref = anaphora_ref
        self.antecedent_ref = antecedent_ref
        (self.begin_token, self.end_token, self.surface) = (begin_token, end_token, surface)
    def is_in_sentence(self):
        """文内の照応かどうかを判定
        先行詞のsidとcidが負でなければ文章内で照応している
        """
        return bool(self.antecedent_ref)
    def get_chunk(self, document):
        """先行詞の文節を取得
        """
        return document.refer(self.antecedent_ref)
    def get_chunk_from_sentence(self, sentence):
        """先行詞の文節を文の参照から取得
        """
        if self.is_in_sentence():
            return sentence.chunks[self.antecedent_ref.cid] if sentence.sid == self.antecedent_ref.sid else None
        return None
    def get_feature_tuple(self):
        """素性を直線化したタプルに変換
        """
        return (*self.antecedent_ref.to_tuple(), *self.anaphora_ref.to_tuple())
    def get_coref_surf(self, document):
        """先行詞の表層表現を取得
        """
        return document.refer(self.antecedent_ref).get_surface()+ document.refer(self.anaphora_ref).get_surface()
class Chunk:
    """文節チャンクのクラス
    """
    def __init__(self):
        """生情報を構造化する
        """
        self.sid = 0
        self.cid = 0
        self.tokens = []
        (self.func_position, self.head_position, self.token_num) = (0, 0, 0)
        self.link_id = -1
        self.link = None
        self.reverse_links = []
        self.first_mentioned = False
        self.chain_num = 0
        (self.in_q, self.begin_paren, self.end_paren, self.emphasis) = (0, False, False, False)
        self.coreference_link = {}
        self.tags = []
        self.reverse_link_ids = []
        self.case = ''
        self.particle = None
        self.chunk_type = ''
    def set_token_info(self):
        """追加された形態素の一覧から格などの属性を設定する
        """
        # 格/係助詞、格の付与
        particles = self.get_func()
        # 係助詞「は」はJumanでは副助詞という名前で扱われる
        if all((particle.attr1 not in {'格助詞', '係助詞', '副助詞'} for particle in particles)):
            self.particle = None
        else:
            # 最後の格助詞あるいは係助詞を付加する
            for particle in filter(
                    lambda particle: particle.attr1 in {'格助詞', '係助詞', '副助詞'}, particles
                ):
                self.particle = particle
        if self.particle != None and __is_case__(self.particle):
            self.case = self.particle.surface
        else:
            self.case = ''
        self.__set_chunk_type__()
    def get_length(self):
        return sum((token.get_length() for token in self.tokens))
    def __set_chunk_type__(self):
        """文節の種別をchunk_typeメンバに設定（意味役割付与タスク用の属性）
        文節の種別はelem / verb / adjective / copulaに分けられる
        """
        self.chunk_type = 'elem'
        for token in self.tokens:
            if token.part == '動詞' and token.is_indep:
                self.chunk_type = 'verb'
            elif re.match('(形容詞|形容動詞)', token.part) and token.is_indep:
                self.chunk_type = 'adjective'
                break
            # Chasen用(コピュラの検出は実質辞書依存なのでここに書くのはちょっと変か？
            elif token.attr1 == '特殊・ダ' or token.attr1 == '特殊・デス':
                self.chunk_type = 'copula'
            # JUMAN用(コピュラの検出は実質辞書依存なのでここに書くのはちょっと変か？
            elif re.match('(ダ|デアル|デス)列', token.conj_form):
                self.chunk_type = 'copula'
    def is_cand_all(self):
        """文節が先行詞の候補になりうるかの判定
        COMMENT:
            基本機能ではないから再利用性を考えると分けておきたいな
        """
        return self.head_token() != None and self.head_token().part == '名詞'
    def get_particle_surf(self):
        """文節に助詞「格助詞、係助詞」があればその表層表現を返す
        """
        return self.particle.surface if self.particle is not None else ''
    def on_add_token(self, token):
        """トークンをチャンクに追加した際に追加したトークンに応じて属性値を変更する
        内容語の場合は機能表現の位置を+1するとか
        「」が入る場合、begin_paren end_paren emphasisの値が変更される
        """
        if token.is_content:
            self.func_position += 1
            self.head_position = self.func_position - 1
        if token.surface == '「':
            self.begin_paren = True
            self.emphasis = True
        elif token.surface == '」':
            self.end_paren = True
            self.emphasis = True
    def add_token(self, token):
        """単語を追加する
        """
        self.tokens.append(token)
        self.token_num += 1
        self.on_add_token(token)
    def is_conj(self):
        """接続詞かどうかを取得
        """
        if self.head_token():
            return self.head_token().part == '接続詞'
    def get_func(self):
        """機能表現の先頭の形態素を取得
        Returns:
            Token:機能語のトークン
        """
        if len(self.tokens) <= self.func_position:
            return []
        else:
            return self.tokens[self.func_position:]
    def head_token(self):
        """単語の内容語を取得
        文節中のfuncでない単語の中で末尾のもの
        """
        if len(self.tokens) == 0:
            return None
        elif len(self.tokens) <= self.func_position or self.func_position < 0:
            return self.tokens[-1]
        else:
            return self.tokens[self.head_position]
    def print_members(self):
        """オブジェクトのメンバ変数を標準出力に表示[デバッグ用]
        """
        print('id :', str(self.cid))
        print('link :', str(self.link_id))
        print('token_num :', str(self.token_num))
        print('func_position :', str(self.func_position))
        funcs = self.get_func()
        for func in funcs:
            print('func :', func.surface)
        else:
            print('func :')
        print('case :', self.case)
        for tag in self.tags:
            print(tag)
        for token in self.tokens:
            token.print_members()
    def print_surfaces(self):
        """表層表現を標準出力に表示
        """
        print('[', end='')
        for tok in self.tokens:
            tok.print_surfaces()
        print(']', end='')
    def get_surface(self):
        """表層表現を取得
        Returns:
            str: 表層表現の文字列
        """
        surface = ''
        for tok in self.tokens:
            surface += tok.surface
        return surface
class Token:
    """形態素（単語）のクラス
    ベースの形を定義しているだけなので
    """
    def __init__(self):
        self.tid = 0
        self.surface = ''
        self.read = ''
        self.basic_surface = ''
        self.part = ''
        self.part_id = 0
        self.attr1 = ''
        self.attr2 = ''
        self.is_indep = False
        self.sahen = False
        self.normalnoun = False
        self.adjectivenoun = False
        self.pos = ''
        self.named_entity = ''
        self.named_entity_part = ''
        self.conj_type = ''
        self.conj_form = ''
        self.other_features = []
        self.is_content = False
        self.coreference_link = {}
    def print_members(self):
        """オブジェクトのメンバ変数を標準出力に表示
        """
        print('id:'+str(self.tid))
        print('surf:'+self.surface)
        print('read:'+self.read)
        print('base:'+self.basic_surface)
        print('part:'+self.part+'('+str(self.part_id)+')')
        print('attr1:'+self.attr1)
        print('attr2:'+self.attr2)
        print('sahen:'+str(self.sahen))
        print('normal:'+str(self.normalnoun))
        print('adjnoun:'+str(self.adjectivenoun))
        print('conj_type:'+self.conj_type)
        print('conj_form:'+self.conj_form)
        for feat in self.other_features:
            print(feat)
    def print_surfaces(self):
        """表層表現を標準出力に表示
        """
        print(self.surface, end='')
    def get_length(self):
        return len(self.surface)
    def __repr__(self):
        members = dict()
        members['id:'] = str(self.tid)
        members['surf']=self.surface
        members['read'] = self.read
        members['base'] = self.basic_surface
        members['part'] = self.part+'('+str(self.part_id)+')'
        members['attr1:']=self.attr1
        members['attr2:']=self.attr2
        members['sahen:']=str(self.sahen)
        members['normal:']=str(self.normalnoun)
        members['adjnoun:']=str(self.adjectivenoun)
        members['conj_type:']=self.conj_type
        members['conj_form:']=self.conj_form
        return repr(members)

class ReferenceConverter:
    """トークン、チャンクの参照をなるべく文字単位で正確に変換するためのクラス
    """
    def __init__(self, dest_doc, src_doc, count_func=None):
        self.dest_doc = dest_doc
        self.src_doc = src_doc
        self.count_func = count_func
        self.no_sid_convert = False
    def __convert_cid_only__(self, cid, dest_sent, src_sent):
        count = 0
        for chunk in src_sent.chunks:
            if chunk.cid == cid:
                break
            count += chunk.get_length() if self.count_func is None else self.count_func(chunk)
        dest_cid = -1
        dest_count = 0
        for chunk in dest_sent.chunks:
            if dest_count >= count:
                dest_cid = chunk.cid
                break
            dest_count += chunk.get_length() if self.count_func is None else self.count_func(chunk)
        return dest_cid
    def __convert_tid_only__(self, tid, dest_sent, src_sent):
        count = 0
        for token in src_sent.tokens:
            if token.tid == tid:
                break
            count += token.get_length() if self.count_func is None else self.count_func(token)
        dest_tid = -1
        dest_count = 0
        for token in dest_sent.tokens:
            if dest_count >= count:
                dest_tid = token.tid
                break
            dest_count += token.get_length() if self.count_func is None else self.count_func(token)
        return dest_tid

    def __convert_cid__(self, sid, cid):
        count = 0
        for sent in self.src_doc.sentences:
            if sent.sid == sid:
                for chunk in sent.chunks:
                    if chunk.cid == cid:
                        break
                    count += chunk.get_length() if self.count_func is None else self.count_func(chunk)
                break
            count += sent.get_length() if self.count_func is None else self.count_func(sent)
        dest_sid = -1
        dest_cid = -1
        dest_count = 0
        for sent in self.dest_doc.sentences:
            length = sent.get_length() if self.count_func is None else self.count_func(sent)
            if dest_count + length > count:
                for chunk in sent.chunks:
                    length = chunk.get_length() if self.count_func is None else self.count_func(chunk)
                    if dest_count + length > count:
                        dest_cid = chunk.cid
                        break
                    dest_count += length
                dest_sid = sent.sid
                break
            dest_count += length
        return dest_sid, dest_cid
    def __convert_tid__(self, sid, tid):
        count = 0
        for sent in self.src_doc.sentences:
            if sent.sid == sid:
                for token in sent.tokens:
                    if token.tid == tid:
                        break
                    count += token.get_length() if self.count_func is None else self.count_func(token)
                    #print(token.surface, '({0})'.format(count))
                break
            count += sent.get_length() if self.count_func is None else self.count_func(sent)
            #print(sent.get_surface(), '({0})'.format(count))
        dest_sid = -1
        dest_tid = -1
        dest_count = 0
        for sent in self.dest_doc.sentences:
            length = sent.get_length() if self.count_func is None else self.count_func(sent)
            if dest_count + length > count:
                for token in sent.tokens:
                    length = token.get_length() if self.count_func is None else self.count_func(token)
                    if dest_count + length > count:
                        dest_tid = token.tid
                        break
                    #print('@', token.surface, '({0},{1})'.format(dest_count+length, count))
                    dest_count += length
                dest_sid = sent.sid
                break
            #print('@', sent.get_surface(), '({0},{1})'.format(dest_count+length, count))
            dest_count += length
        return dest_sid, dest_tid
    def convert(self, ref):
        if isinstance(ref, ChunkReference):
            if self.no_sid_convert:
                dest_sid  = ref.sid
                src_sent = self.src_doc.refer_sentence(ref.sid)
                dest_sent = self.dest_doc.refer_sentence(dest_sid)
                dest_cid = self.__convert_cid_only__(ref.cid, dest_sent, src_sent)
                return ChunkReference(dest_sid, dest_cid)
            else:
                dest_sid, dest_cid = self.__convert_cid__(ref.sid, ref.cid)
                return ChunkReference(dest_sid, dest_cid)
        elif isinstance(ref, TokenReference):
            if self.no_sid_convert:
                dest_sid = ref.sid
                src_sent = self.src_doc.refer_sentence(ref.sid)
                dest_sent = self.dest_doc.refer_sentence(dest_sid)
                dest_tid = self.__convert_tid_only__(ref.tid, dest_sent, src_sent)
                return TokenReference(dest_sid, dest_tid)
            else:
                dest_sid, dest_tid = self.__convert_tid__(ref.sid, ref.tid)
                return TokenReference(dest_sid, dest_tid)
        return None

class FlatNLElementIterator:
    def __init__(self, document):
        self.sentence_iter = iter(document.sentences)
        self.cur_sent = None
        self.elem_iter = None
    def __get_next_elem__(self):
        raise NotImplementedError
    def __iter__(self):
        return self
    def __next__(self):
        while True:
            try:
                if self.elem_iter is None:
                    raise StopIteration
                return next(self.elem_iter)
            except StopIteration:
                self.cur_sent = next(self.sentence_iter)
                self.elem_iter = self.__get_next_elem__()
                continue

class FlatChunkIterator(FlatNLElementIterator):
    def __get_next_elem__(self):
        return iter(self.cur_sent.chunks)

class FlatTokenIterator(FlatNLElementIterator):
    def __get_next_elem__(self):
        return iter(self.cur_sent.tokens)

def tokens(elem):
    if isinstance(elem, Document):
        return FlatTokenIterator(elem)
    elif isinstance(elem, Sentence):
        return elem.tokens
    elif isinstance(elem, Chunk):
        return elem.tokens
    raise NotImplementedError

def chunks(elem):
    if isinstance(elem, Document):
        return FlatChunkIterator(elem)
    elif isinstance(elem, Sentence):
        return elem.chunks
    raise NotImplementedError

