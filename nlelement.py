"""日本語テキストに含まれる単語、文節、文、文書と言った要素を階層的なオブジェクトとして実装
    このモジュールはそれぞれのオブジェクトの挙動のみを定義し、ロード、セーブについては外部モジュールで実装します

    USAGE: データベース`test.db`から取得したある文書データの内容を表示する
        >>>loader = database.DatabaseLoader("test.db")
        >>>doc = loader.load_one_sample()[0] # データベースにある文書データ(Document)をランダムに１つロード
        >>>print(doc)                        # 文書データの内容を表示する
        <Document OC01_00001_01 詰め将棋の本を...>
        >>>print(doc.sentences[0])           # 文章データ中の最初の文を表示
        <Sentence 詰め将棋の本を...>
        >>>print(doc.sentences[0].chunks[0]) # 文章データ中の最初の文節を表示
        <Chunk 詰め将棋の 0 0>
        >>>print(doc.sentences[0].tokens[0]) # 文章データ中の最初の単語を表示
        <Token 詰め 0 0> 
    
"""
import re
import weakref
from . import relation
from .reference import TokenReference, ChunkReference, ExoReference

def make_reference(element):
    """Sentence, Chunk, Tokenのインスタンスから対応する参照を生成
    参照はIDのみ保持した
    """
    if isinstance(element, Chunk):
        return ChunkReference(element.sid, element.cid)
    elif isinstance(element, Token):
        return TokenReference(element.sid, element.tid)
    elif isinstance(element, Sentence):
        return element.sid    
    return None

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
    def get_coreference_labels(self):
        """文章内に存在する共参照関係ラベルを取得
        """
        result = []
        for sent in self.sentences:
            for token in sent.tokens:
                for name, coref in token.coreference_link.items():
                    if name == 'coref':
                        result.append(coref.get_relation("coref"))
        return result
    def get_predicate_labels(self):
        """文章内に存在する述語項構造ラベルを取得
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
                        case = case_normalize_table[name]
                    elif name != "coref":
                        case = name
                    else:
                        continue
                    result.append(
                        coref.get_relation(case)
                    )
        return result
    def refer(self, ref):
        """参照オブジェクトからそれに対応するToken, Chunk, Sentenceを取得
        """
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
    def chunkref_from_tokenref(self, token_ref):
        """単語の参照からその単語を含む文節の参照を取得する
        """
        sent = self.refer_sentence(token_ref.sid)
        for chunk in sent.chunks:
            if chunk.tokens:
                if chunk.tokens[0].tid <= token_ref.tid and token_ref.tid <= chunk.tokens[-1].tid:
                    return make_reference(chunk)
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
    def sid_to_position(self, sid):
        """文番号から文字位置への変換
        """
        if sid < 0 or sid >= len(self.sentences):
            return -1
        return get_position(self, self.refer_sentence(sid))

    def to_position(self, obj):
        """変換可能なobjectの文字位置への変換
        """
        return get_position(self, obj)

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

    def get_limited_surface(self):
        """文字数制限をつけて表層表現を取得[デバッグ用]
        """
        raw_surface = ''
        for tok in tokens(self):
            raw_surface += tok.surface
            if len(raw_surface) > 8:
                raw_surface = raw_surface[:8] + "..."
                return raw_surface
        return raw_surface
        

    def __repr__(self):
        return "<Document: {}{}>".format(self.name, "({})".format(self.get_limited_surface()) if self.sentences else "[empty]")

class Sentence:
    """文を格納するクラス
    MEMBERS:
        * sid - 文ID
        * chunks - この文が含む文節
        * tokens - この文が含む単語(これらの単語はchunksが含む単語が含まれている)
        
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
        for cid, chunk in enumerate(self.chunks):
            self.chunk_positions.append(chunk_position) # 
            chunk_position += len(chunk.get_surface())  # 始点の文字上の位置を設定
            #self.__link_chunk__(cid, chunk)             # 係り受け元、係り受け先のオブジェクト参照を設定する NOTE:循環参照が起こる
            chunk.set_token_info()                      # お呼び出し(databaseモジュールでも呼び出されるので問題なし)
        self.add_first_mentioned()                      # first_mentionedの対か
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
    surface = property(get_surface)
    def get_limited_surface(self):
        raw_sent = ''
        for token in self.tokens:
            raw_sent += token.surface
            if len(raw_sent) > 8:
                raw_sent = raw_sent[:8] + "..."
                return raw_sent
        return raw_sent
    def __repr__(self):
        return "<Sentence: {}({})>".format(self.sid, self.get_limited_surface())

def __is_case__(token):
    if token is None or token.part != '助詞' or token.attr1 != '格助詞':
        return False
    return True
class CoreferenceEntry:
    """共参照関係＋述語項構造における関係のデータ（ラベル用）
    照応詞、述語がこのオブジェクトを保持していて、照応詞、述語の参照と先行詞、項の参照を保持する
    Members:
            anaphora_ref (TokenReference): 照応詞の参照
            antecedent_ref (TokenReference): 先行詞の参照
            link_type (str): 位置関係に基づく関係の種類(dep,adnom,zero)
    """
    def __init__(self, anaphora_ref, antecedent_ref, begin_token=None, end_token=None, surface=None):
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
        self.link_type = None   # ゼロ照応の場合'zero'
        #(self.begin_token, self.end_token, self.surface) = (begin_token, end_token, surface)
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
        if self.antecedent_ref is None:
            return (-1, -1, *self.anaphora_ref.to_tuple())
        return (*self.antecedent_ref.to_tuple(), *self.anaphora_ref.to_tuple())
    def get_coref_surf(self, document):
        """先行詞の表層表現を取得
        """
        return document.refer(self.antecedent_ref).get_surface()+":"+document.refer(self.anaphora_ref).get_surface()
    def get_relation(self, case):
        rel = relation.Relation()
        rel.ana_ref, rel.ant_ref, rel.case = self.anaphora_ref, self.antecedent_ref, case
        return rel

class _ReverseLinkElem:
    """係り元文節リストの一覧の実装（標準のListとほぼ同じ挙動だが、中身がweakrefになる）
    """
    def __init__(self):
        self.links = []

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.links[i]()
        elif isinstance(i, slice):
            return list(map(weakref.ref.__call__, self.links[i]))
    
    def __iter__(self):
        for link in self.links:
            yield link()
    
    def __setitem__(self, i, link):
        self.links[i] = weakref.ref(link)

    def __len__(self):
        return len(self.links)

    def append(self, link):
        self.links.append(weakref.ref(link))

    def index(self, link, start=None, stop=None):
        if start is not None:
            if stop is not None:
                iterator = enumerate(self.links[start:])
            else:
                iterator = enumerate(self.links[start:stop])
        else:
            if stop is not None:
                iterator = enumerate(self.links[:])
            else:
                iterator = enumerate(self.links[:stop])
        for i, _link in iterator:
            if _link() is link:
                return i
        raise ValueError("{} is not in list".format(link))


class Chunk:
    """文節チャンクのクラス
    MEMBER:
        * sid - 文書から見た文ID
        * cid - 文から見た文節ID
        * tokens - 文節が含む単語
        * head_position - 内容語の位置([太郎]が, 一般[人]に, [歓迎]する)
        * func_position - 機能語表現の先頭位置(太郎[が], 一般人[に], 還元され[た])助詞の取得などに使用
        * link_id - 係り先の文節ID
        * link - 係り先文節
        * reverse_links - 係り元文節のリスト(複数の文節が係り元の場合がある)
        * reverse_link_ids - 係り元文節IDのリスト(複数の文節が係り元の場合がある)
        * case - 文節末尾に格助詞があればその格助詞表層表現
        * 
    """
    def __init__(self):
        """生情報を構造化する
        """
        self.sid = 0
        self.cid = 0
        self.tokens = []
        (self.func_position, self.head_position, self.token_num) = (0, 0, 0)
        self.link_id = -1
        self._link = None
        self.reverse_links = _ReverseLinkElem()
        self.first_mentioned = False
        self.chain_num = 0
        (self.in_q, self.begin_paren, self.end_paren, self.emphasis) = (0, False, False, False)
        self.coreference_link = {}
        self.tags = []
        self.reverse_link_ids = []
        self.case = ''
        self.particle = None
        self.chunk_type = ''

    # linkは実際weakrefで実装するが、外部的には普通のオブジェクトに見えるように実装している
    def _get_link(self):
        return self._link() if self._link is not None else None
    def _set_link(self, link_chunk):
        if link_chunk is not None:
            self._link = weakref.ref(link_chunk)
        else:
            self._link = None

    link = property(_get_link, _set_link)

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
        """表層表現文字列の長さを取得する
        """
        return sum((token.get_length() for token in self.tokens))
    def __set_chunk_type__(self):
        """文節の種別をchunk_typeメンバに設定（意味役割付与タスク用の属性）
        文節の種別はelem / verb / adjective / copulaに分けられる
        """
        self.chunk_type = 'elem'
        for token in self.tokens:
            if token.part == '動詞':
                self.chunk_type = 'verb'
            elif re.match('(形容詞|形容動詞)', token.part):
                self.chunk_type = 'adjective'
                break
            # Unidic用(コピュラの検出は実質辞書依存なのでここに書くのはちょっと変か？
            elif token.conj_type == '助動詞-ダ' or token.conj_type == '助動詞-デス':
                self.chunk_type = 'copula'
            # JUMAN用(コピュラの検出は実質辞書依存なのでここに書くのはちょっと変か？
            elif re.match('(ダ|デアル|デス)列', token.conj_form):
                self.chunk_type = 'copula'
    def is_cand_all(self):
        """文節が先行詞の候補になりうるかの判定
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
        if self.head_position == self.func_position or len(self.tokens) <= self.func_position:
            return []
        else:
            return self.tokens[self.func_position:]
    def head_token(self):
        """単語の内容語を取得
        文節中のfuncでない単語の中で末尾のもの
        """
        if len(self.tokens) == 0:
            return None
        elif self.head_position == self.func_position or len(self.tokens) <= self.func_position or self.func_position < 0:
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
    def __repr__(self):
        """表層表現の文字列と文章上の位置（文ID, 文節ID）という基本情報を表示[デバッグ用]
        """
        return "<{}: {}({}, {})>".format("Chunk", self.get_surface(), self.sid, self.cid)
    surface = property(get_surface)

class Token:
    """形態素（単語）のクラス
    MEMBERS:
        * tid - 単語ID
        * sid - 文ID
        * surface - 表層表現
        * read - 読み
        * basic_surface - 基本形
        * part - 品詞
        * part_id - 品詞ID(非推奨)
        * attr1 - 品詞中分類
        * attr2 - 品詞小分類
        * pos - Part of Speechタグ(品詞-品詞中分類-品詞小分類)
        * conj_type - 活用型(ex.カ五段、サ変)
        * conj_form - 活用形(ex.未然形、連用形)
        * named_entity - 固有表現タグ
        * named_entity_part - 固有表現タグ上の位置(B|I|O)
    """
    def __init__(self):
        self.tid = 0
        self.sid = 0
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
        self.pas_type = None
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
    def get_surface(self):
        return self.surface
    def __repr__(self):
        return "<{}: {}({}, {})>".format("Token", self.surface, self.sid, self.tid)

def get_verbchunk_verb(chunk: Chunk):
    """フレームとのマッチング用に統一された動詞の表現を取得する
    辞書としてはIPA, UNIDICを想定
    NOTE:アルゴリズムはSynchaのものを流用
    TODO:ASAに完全対応しているかどうかは微妙なのでできたら統一する
    * サ変動詞(ex.実行する) -> サ変名詞+する
    * サ変副詞する(ex.迷惑する) -> サ変名詞+する
    * 動詞 -> 基本形
    * コピュラ
    * 体言止め(サ変)
    * 体言語幹のサ変動詞
    * 連体詞
    * 体言止め(数値,形容動詞)
    * 生まれ
    * ある（助動詞|連体詞）
    * 体言止め(普通)
    * なる、ない
    * 副詞
    """
    head = chunk.head_token()
    expr = ''
    nhead_posi = chunk.head_position + 1
    nhead = chunk.tokens[nhead_posi] if nhead_posi + 1 < len(chunk.tokens) else None
    
    pre_head_posi = chunk.head_position - 1 if chunk.head_position - 1 < len(chunk.tokens) else -1
    phead = chunk.tokens[pre_head_posi] if pre_head_posi >= 0 else None
    if head.part == "動詞":
        if re.match(r"(する|為る)", head.basic_surface):
            if not phead:
                expr = 'する'
            else:
                if re.match(r"(名詞-サ変.*|名詞-.*-サ変.*)", phead.pos):
                    expr = phead.surface+"する"
                elif re.match(r"(名詞-副詞可能.*|名詞-.*-サ変形状詞.*)", phead.pos):
                    expr = phead.surface+"する"
            return expr
        else:
            expr = head.basic_surface
            return expr
    if head.part == "名詞" and nhead and re.match(r"(だ|です)", nhead.basic_surface):
        expr = head.surface + nhead.surface
        return expr

    if re.match(r"(名詞-サ変.*|名詞-.*-サ変.*)", head.pos):
        if chunk.link_id == -1:
            return head.surface + "する"
        elif re.match(r"(記号-読点)", nhead.pos) and chunk.link.head_token.pas_type == "pred":
            return head.surface + "する"
        elif nhead and (re.match(r"(する|為る)", nhead.basic_surface)):
            return head.surface + "する"
    
    if head.part == "連体詞":
        if head.basic_surface == "大きな":
            return "大きい"
        if head.basic_surface == "小さな":
            return "小さい"
        if head.basic_surface == "同じ":
            return "同じだ"
    if re.match(r"(名詞-形容動詞語幹|名詞-.*-サ変形状詞可能)", head.pos):
        return head.surface + "だ"

    if head.basic_surface == "生まれ":
        return "生まれる"
    
    if head.basic_surface == "ある" and re.match(r"(助動詞|連体詞)", head.part):
        return "ある"

    if re.match(r"(名詞-接尾-助数詞|名詞-普通名詞-助数詞可能)", head.pos):
        return head.basic_surface+"だ"

    if re.match(r"(名詞-一般|名詞-普通名詞-一般)", head.pos):
        return head.basic_surface+"だ"

    if re.match(r"(動詞-非自立|動詞-非自立可能)", head.pos) and head.basic_surface == "なる":
        return "なる"

    if head.part == "助動詞" and head.basic_surface == "ない":
        return "ない"

    if re.match(r"(副詞|形状詞)", head.pos) and nhead and nhead.basic_surface == "。":
        return head.bf + "だ"

    for rev_link in chunk.reverse_links:
        for rev_tok in rev_link.tokens:
            if re.match(r"(は|が|も|を|に|から|へ|と|より|まで|で)", rev_tok.basic_surface) and re.match(r"(助詞-(?!接続助詞))",rev_tok.pos):
                if re.match(r"名詞.*", head.pos):
                    return head.basic_surface+"だ"
    
    return ""

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
    def __convert_tid_only__(self, tid, dest_sent, src_sent, conv_type):
        count = 0
        for token in src_sent.tokens:
            if token.tid == tid:
                #print('□', token.surface)
                if conv_type == 'tail':
                    count += token.get_length() if self.count_func is None else self.count_func(token)
                break
            count += token.get_length() if self.count_func is None else self.count_func(token)
            #print(token.surface, '({0})'.format(count))
        dest_tid = -1
        dest_count = 0
        for token in dest_sent.tokens:
            length = token.get_length() if self.count_func is None else self.count_func(token)
            if (dest_count + length > count and conv_type == 'head') or (dest_count + length >= count and conv_type == 'tail'):               
                #print('■', token.surface)
                dest_tid = token.tid
                break
            dest_count += length
            #print(token.surface, '({0} > {1})'.format(count, dest_count))
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
    def __convert_tid__(self, sid, tid, conv_type):
        count = 0
        for sent in self.src_doc.sentences:
            if sent.sid == sid:
                for token in sent.tokens:
                    if token.tid == tid:
                        if conv_type == 'tail':
                            count += token.get_length() if self.count_func is None else self.count_func(token)                    
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
                    if (dest_count + length > count and conv_type == 'head') or (dest_count + length >= count and conv_type == 'tail'):
                        dest_tid = token.tid
                        break
                    #print('@', token.surface, '({0},{1})'.format(dest_count+length, count))
                    dest_count += length
                dest_sid = sent.sid
                break
            #print('@', sent.get_surface(), '({0},{1})'.format(dest_count+length, count))
            dest_count += length
        return dest_sid, dest_tid
    def convert(self, ref, conv_type='head'):
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
                dest_tid = self.__convert_tid_only__(ref.tid, dest_sent, src_sent, conv_type)
                return TokenReference(dest_sid, dest_tid)
            else:
                dest_sid, dest_tid = self.__convert_tid__(ref.sid, ref.tid, conv_type)
                return TokenReference(dest_sid, dest_tid)
        return None

def get_position(doc, obj):
    """docに所属する指定したオブジェクト(Token, Chunk, Sentence)あるいはオブジェクト参照(TokenReference, ChunkReference)
    の始点position(文字位置)を取得
    """
    if isinstance(obj, (Token, TokenReference)):
        if obj.sid < 0 or obj.tid < 0 or obj.sid >= len(doc.sentences) or obj.tid >= len(doc.sentences[obj.sid].tokens):
            return -1
        return sum(map(lambda t: len(t.surface),filter(lambda t:t.sid < obj.sid or t.sid == obj.sid and t.tid < obj.tid, tokens(doc))))
    elif isinstance(obj, (Chunk, ChunkReference)):
        if obj.sid < 0 or obj.cid < 0 or obj.sid >= len(doc.sentences)  or obj.cid >= len(doc.sentences[obj.sid].chunks):
            return -1
        return sum(map(lambda c: len(c.get_surface()), filter(lambda c:c.sid < obj.sid or c.sid == obj.sid and c.cid < obj.cid, chunks(doc))))
    elif isinstance(obj, Sentence):
        if obj.sid < 0 or obj.sid >= len(doc.sentences):
            return -1
        return sum(map(lambda s: len(s.get_surface()), filter(lambda s:s.sid < obj.sid, doc.sentences)))
    raise TypeError("cannot convert from {} object/reference".format(type(obj)))

def position_to_sentence(doc, position):
    """文字位置から対応する文を取得
    """
    lensum = 0
    if position < 0:
        return None
    for sent in doc.sentences:
        length = len(sent.get_surface())
        if lensum + length > position:
            return sent
        lensum += length
    return None

def position_to_chunk(doc, position):
    """文字位置から対応する文節を取得
    """
    lensum = 0
    if position < 0:
        return None
    for chk in chunks(doc):
        length = len(chk.get_surface())
        if lensum + length > position:
            return chk
        lensum += length
    return None

def position_to_token(doc, position):
    """文字位置から対応する形態素を取得
    """
    if position < 0:
        return None
    lensum = 0
    for tok in tokens(doc):
        if lensum + len(tok.surface) > position:
            return tok
        lensum += len(tok.surface)
    return None

class FlatNLElementIterator:
    """文書データ上の文節や単語をすべて列挙するイテレータ
    """
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
    """指定したオブジェクトが保持している単語(Tokenオブジェクト)を先頭からすべて列挙
        USAGE1: 文章docが保持している単語を先頭からすべて表示
            for tok in tokens(doc):
                print(tok)    
        USAGE2: 文sentが保持している単語を先頭からすべて表示
            for tok in tokens(sent):
                print(tok)
    """
    if isinstance(elem, Document):
        return FlatTokenIterator(elem)
    elif isinstance(elem, Sentence):
        return elem.tokens
    elif isinstance(elem, Chunk):
        return elem.tokens
    raise NotImplementedError

def chunks(elem):
    """指定したオブジェクトが保持している文節(Chunkオブジェクト)を先頭からすべて列挙
        
        USAGE: 文章docが保持している文節を先頭からすべて表示
            for chunk in chunks(doc):
                print(chunk)
        USAGE: 文sentが保持している文節を先頭からすべて表示
            for chunk in chunks(doc):
                print(chunk)
    """
    if isinstance(elem, Document):
        return FlatChunkIterator(elem)
    elif isinstance(elem, Sentence):
        return elem.chunks
    raise NotImplementedError

