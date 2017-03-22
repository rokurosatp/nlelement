#-*- coding utf8 -*-
"""
KNBコーパスから素性をロードする

TODO　だいぶコードが複雑になってきたのでリファクタリングしたい

"""
import glob
import os
import re
from enum import Enum
import myprofiles
from . import nlelement

class LoadError(Exception):
    """KNBCの解析時に発生したエラーを上に伝える
    """
    def __init__(self, inst=None):
        """例外を伝播させる例外
        1回目はLoadError以外の例外が渡されるのでとくに何もせず初期化
        2回目以降は渡されたLoaｄErrorをコピーして属性を埋めてく
        """
        Exception.__init__(self)
        if isinstance(inst, LoadError):
            self.copy_from(inst)
        else:
            self.exception = inst
            self.token_i = -1
            self.chunk_i = -1
            self.sent_i = -1
            self.sent_surf = ''
            self.sent_name = ''
            self.document_name = ''
            self.input_line = ''
            self.problemed = ''
            self.args = ('',)
    def copy_from(self, src):
        """属性をシャローコピーする
        """
        self.exception = src.exception
        self.token_i = src.token_i
        self.chunk_i = src.chunk_i
        self.sent_i = src.sent_i
        self.sent_surf = src.sent_surf
        self.sent_name = src.sent_name
        self.document_name = src.document_name
        self.input_line = src.input_line
        self.problemed = src.problemed
        self.args = src.args
    def set_args(self):
        """例外のメッセージを更新する、
        Documentの解析処理で例外を発生させる場合はこの関数を呼び出してメッセージを確定させる
        """
        self.args = (str(self.__get_expr__()),)
    def __get_expr__(self):
        """現在の状態を文字列表現に変換
        """
        result_list = []
        positional_expr = ''
        if len(self.sent_name) > 0:
            positional_expr += self.sent_name + ':'
        elif len(self.document_name) > 0:
            positional_expr += self.document_name + ':'
        if self.sent_i > 0:
            positional_expr += str(self.sent_i) + '文目'
        if self.chunk_i > 0:
            positional_expr += str(self.chunk_i) + '文節'
        if self.token_i > 0:
            positional_expr += str(self.token_i) + '番目の単語'
        result_list.append(positional_expr)
        if len(self.sent_surf) > 0:
            result_list.append(self.sent_surf)
        if len(self.input_line) > 0:
            result_list.append(self.input_line)
        if len(self.problemed) > 0:
            result_list.append(self.problemed)
        if self.exception is not None:
            result_list.append(str(type(self.exception))+':'+str(self.exception))
        result = ''
        result += join_with(result_list, '\n')
        return result
def join_with(str_list, delim):
    """テキストリストをデリミタを挟んで結合する
    代替の関数がありそうなのであったら入れ替えよう
    """
    try:
        result = str_list[0]
    except IndexError:
        return ''
    for i in range(1, len(str_list)):
        result += delim + str_list[i]
    return result
def pathexpr(expr):
    """パス表現を環境に応じて正規化
    """
    # ここはわかりづらいけどWindowsかどうかの判定
    # (WindowsにはUSERDOMAINという環境変数がある)
    if 'USERDOMAIN' in os.environ:
        result = expr.replace('/', "\\")
    else:
        result = expr
    return result
def get_corpus_path():
    """コーパスのパスを取得
    内部引数からファイルに変更したので注意
    """
    # domain = os.getenv('USERDOMAIN', 'default')
    # pathdic = {
    #     'admin-PC': r'C:\Users\Rokuro Sato\Software\KNBC_v1.0_090925\KNBC_v1.0_090925',
    #     'NECROCK-PC': r'C:\Users\六郎\Ownbin\KNBC_v1.0_090925',
    #     'default': r'/home/rokurou/programs/KNBC_v1.0_090925'
    # }
    prof = myprofiles.Profile()
    if 'KNBC_INSTALL_PATH' in prof.config:
        return prof.config['KNBC_INSTALL_PATH']
    print('Error: there is no profile')
    raise FileNotFoundError()
class AnnotationState(Enum):
    """アノテーション状態
    """
    none = 0
    delim = 1
class AnnotationBroadState(Enum):
    """どの属性を解析しているかを示す
    """
    default = 0
    quoted = 1
    angled = 2
class AnnotationLineParser:
    """KNBCの入力を適当な区切りに変換する
    """
    def __init__(self):
        self.angle_bracket_level = 0
        self.sqel_bracket_level = 0
        self.tokenized_number = 0
        self.is_quoted = False
        self.iter = None
        self.state = AnnotationState.none
        self.broad_state = AnnotationBroadState.default
        self.buffer = ''
    def load_chunk_text(self, sentence: str):
        """ タプルに分割
        """
        self.iter = iter(sentence)
        token_attr = []
        quote_attr = []
        angled_attr = []
        self.angle_bracket_level = 0
        self.sqel_bracket_level = 0
        self.tokenized_number = 0
        try:
            while 1:
                self.load_char()
                if self.state != AnnotationState.none:
                    if self.broad_state == AnnotationBroadState.default:
                        if self.angle_bracket_level != 0:
                            self.broad_state = AnnotationBroadState.angled
                        else:
                            if len(self.buffer) != 0:
                                token_attr.append(self.buffer)
                                self.buffer = ''
                    if self.broad_state == AnnotationBroadState.angled and self.angle_bracket_level == 0:
                        if len(self.buffer) != 0:
                            angled_attr.append(self.buffer)
                            self.buffer = ''
        except StopIteration:
            if len(self.buffer) != 0:
                if self.broad_state == AnnotationBroadState.default:
                    token_attr.append(self.buffer)
                elif self.broad_state == AnnotationBroadState.quoted:
                    quote_attr.append(self.buffer)
                elif self.broad_state == AnnotationBroadState.angled:
                    angled_attr.append(self.buffer)
        return (token_attr, quote_attr, angled_attr)
    def load_token_text(self, sentence: str):
        """ タプルに分割
        """
        self.iter = iter(sentence)
        token_attr = []
        quote_attr = []
        angled_attr = []
        self.angle_bracket_level = 0
        self.sqel_bracket_level = 0
        self.tokenized_number = 0
        try:
            while 1:
                self.load_char()
                if self.state != AnnotationState.none:
                    if self.broad_state == AnnotationBroadState.default:
                        if self.is_quoted or self.buffer == 'NIL':
                            self.broad_state = AnnotationBroadState.quoted
                        else:
                            if len(self.buffer) != 0:
                                token_attr.append(self.buffer)
                                self.buffer = ''
                    if self.broad_state == AnnotationBroadState.quoted:
                        if self.is_quoted:
                            if len(self.buffer) != 0:
                                quote_attr.append(self.buffer)
                                self.buffer = ''
                        elif not self.is_quoted:
                            self.broad_state = AnnotationBroadState.angled
                    if self.broad_state == AnnotationBroadState.angled and self.angle_bracket_level == 0:
                        if len(self.buffer) != 0:
                            angled_attr.append(self.buffer)
                            self.buffer = ''
        except StopIteration:
            if len(self.buffer) != 0:
                if self.broad_state == AnnotationBroadState.default:
                    token_attr.append(self.buffer)
                elif self.broad_state == AnnotationBroadState.quoted:
                    quote_attr.append(self.buffer)
                elif self.broad_state == AnnotationBroadState.angled:
                    angled_attr.append(self.buffer)
        return (token_attr, quote_attr, angled_attr)
    def load_char(self):
        """文字列を裏で読み込む
        """
        nowc = next(self.iter)
        if nowc == ' ':
            self.state = AnnotationState.delim
        elif nowc == '<' and self.sqel_bracket_level == 0:
            self.state = AnnotationState.delim
            self.angle_bracket_level += 1
        elif nowc == '>' and self.sqel_bracket_level == 0:
            self.state = AnnotationState.delim
            self.angle_bracket_level -= 1
        elif nowc == '【' and self.angle_bracket_level == 1:
            self.state = AnnotationState.delim
            self.sqel_bracket_level += 1
        elif nowc == '】' and self.angle_bracket_level == 1:
            self.state = AnnotationState.delim
            self.sqel_bracket_level -= 1
        elif nowc == '"':
            self.state = AnnotationState.delim
            self.is_quoted = not self.is_quoted
        else:
            self.buffer += nowc
            self.state = AnnotationState.none
def split_angle_bracket(expr):
    """コーパスの文節アノテーション取得のために>で分割する,最初の文字は必ず<なのでそれも除外する
    """
    items = []

    for item in expr.split('>'):
        items.append(item[1:len(item)])
    return items
def __convert_corpusid__(corpusids):
    """ファイル名としてふられている番号をコーパス番号として整数値に変換
    """
    if len(corpusids) < 4:
        print(corpusids)
        print('CorpusIds needs d-d-[d]d-dd')
        raise RuntimeError()
    cpid = 0
    cpid += int(corpusids[0])*100000
    cpid += int(corpusids[1])*10000
    cpid += int(corpusids[2])*100
    cpid += int(corpusids[3])
    return cpid
class CorpusFile:
    """ロードされたコーパスファイルを構造化
    """
    def __init__(self, filename):
        """ファイルを読み取って初期化する
        Args:
            filename (str): ロードするコーパスファイル（フルパス）
        """
        self.filename = filename
        self.fileid = __convert_corpusid__(self.filename.split('_')[-1].split('-'))
        file = open(self.filename, "r", encoding='euc-jp')
        self.text = []
        for line in file:
            self.text.append(line[0:-1])
        file.close()
    def get_text(self):
        """ロードしたテキストを生で取得
        """
        return self.text

class KNBCLoaderIter:
    """KNBコーパス中のアノテーション済みテキストをロードする
    イテレータ風に使える予定だけどまだ1番目のファイルのロードしかできてない
    """
    def __init__(self, loader):
        """KNBコーパスのインストールディレクトリの位置を指定して初期化を行う
        Args:
            knb_dir_name (str): KNBコーパスをインストールしたディレクトリ
        """
        self.loader = loader
        self.dir_iter = iter(self.loader.directories)
        self.__cur_dir__ = ''
    def __next__(self):
        """次のファイルを取得
        """
        try:
            self.__cur_dir__ = pathexpr(next(self.dir_iter))
        except StopIteration:
            raise
        result = Document(self.__cur_dir__)
        return result
class KNBCLoader:
    """KNBコーパス中のアノテーション済みテキストをロードする
    イテレータ風に使える予定だけどまだ1番目のファイルのロードしかできてない
    """
    def __init__(self, knb_dir_name):
        """KNBコーパスのインストールディレクトリの位置を指定して初期化を行う
        Args:
            knb_dir_name (str): KNBコーパスをインストールしたディレクトリ
        """
        self.rootpath = knb_dir_name
        self.corpuspath = knb_dir_name+pathexpr('/corpus1')
        self.directories = glob.glob(pathexpr(self.corpuspath+'/*'))
    def __iter__(self):
        return KNBCLoaderIter(self)
class Document(nlelement.Document):
    """KNBC用の文章データ
    構造の定義は基底クラスで行っているので
    読み込み処理のみ実装する
    """
    def __init__(self, directory_path):
        """読み込みを含めた初期化を行う
        KNBCでは文章がディレクトリの単位になっている
        Args:
            directory_path (str): 対応するディレクトリのパスを指定する
        """
        nlelement.Document.__init__(self)
        directory_path = directory_path.replace('\\', '/')
        self.name = directory_path.split('/')[-1]
        filenames = glob.glob(directory_path+'/'+self.name+'*')
        corpuslist = []
        for filename in filenames:
            corpus = CorpusFile(filename)
            corpuslist.append((corpus, corpus.fileid, 0))
        corpuslist.sort(key=lambda item: item[1])
        for (sid, sent) in enumerate(corpuslist):
            corpus = sent[0]
            try:
                self.sentences.append(Sentence(sid, corpus.get_text()))
            except LoadError as inst:
                newinst = LoadError(inst=inst)
                newinst.document_name = self.name
                newinst.set_args()
                raise newinst from inst
            except Exception as inst:
                newinst = LoadError(inst=inst)
                newinst.document_name = self.name
                newinst.set_args()
                raise newinst from inst
class Sentence(nlelement.Sentence):
    """文を格納するクラス
    構造の定義は基底クラスで行っているので
    読み込み処理のみ実装する
    """
    def __init__(self, sid, texts):
        """コーパステキストからの読み込み、初期化を同時に行う
        Args:
            sid (int): 文の番号
            texts (list): コーパスのテキストを行区切りのリストとして渡す
        """
        nlelement.Sentence.__init__(self)
        header = texts[0].split(' ')
        self.sid = sid
        self.name = header[1]
        (cid, tid) = (0, 0)
        for line in texts:
            #最後が必ず開業なのでchomp
            if line[0:3] == 'EOS':
                pass
            elif line[0] == '#':
                pass
            elif line[0] == '*' or line[0] == '+':
                try:
                    self.chunks.append(Chunk(sid, cid, line))
                except LoadError as inst:
                    newinst = LoadError(inst=inst)
                    newinst.sent_i = sid
                    newinst.sent_name = self.name
                    newinst.sent_surf = self.get_surface()
                    raise newinst from inst
                cid += 1
            else:
                try:
                    self.tokens.append(Token(tid, line))
                except LoadError as inst:
                    newinst = LoadError(inst=inst)
                    newinst.sent_i = sid
                    newinst.sent_name = self.name
                    newinst.sent_surf = self.get_surface()
                    raise newinst from inst
                self.chunks[-1].add_token(self.tokens[-1])
                if self.chunks[-1].begin_paren:
                    self.__in_q__ += 1
                elif self.chunks[-1].end_paren:
                    self.__in_q__ -= 1
                self.chunks[-1].in_q = self.__in_q__
                tid += 1
        #イニシャライザ内で初期化関数を親クラスに返す、すごく気持ちが悪い
        try:
            self.post_initialize()
        except Exception as inst:
            newinst = LoadError(inst=inst)
            newinst.sent_i = sid
            newinst.sent_name = self.name
            newinst.sent_surf = self.get_surface()
            raise newinst from inst
def __is_case__(token):
    if token is None or token.part != '助詞' or token.attr1 != '格助詞':
        return False
    return True
class CoreferenceEntry(nlelement.CoreferenceEntry):
    """参照解決のためにオーバーライドのないクラス継承をしてる。実はいらない子
    """
    def __init__(self, anaphora_ref, antecedent_ref, begin_token, end_token, surface):
        nlelement.CoreferenceEntry.__init__(self, anaphora_ref, antecedent_ref, begin_token, end_token, surface)
def __get_depend_number__(expr):
    return int(expr.replace('D', '').replace('P', '').replace('I', ''))
class Chunk(nlelement.Chunk):
    """文節チャンクのクラス
    """
    def __init__(self, sid, cid, expr):
        """生情報を構造化する
        Args:
            sid (int): 文番号
            cid (int): 文節番号
            expr (int): 文節を記述したコーパス表現(アノテーション)の行
        """
        nlelement.Chunk.__init__(self)
        (self.sid, self.cid) = (sid, cid)
        parser = AnnotationLineParser()
        try:
            header = parser.load_chunk_text(expr)
            self.link_id = __get_depend_number__(header[0][1])
            if len(header[2]) > 0:
                self.tags = header[2]
                self.__set_coreference_feature__()
        except LoadError as inst:
            newinst = LoadError(inst=inst)
            newinst.input_line = expr
            raise newinst from inst
        except Exception as inst:
            newinst = LoadError(inst=inst)
            newinst.cid = cid
            newinst.input_line = expr
            newinst.problemed = str(header)
            newinst.sent_i = sid
            raise newinst from inst
    def __set_coreference_feature__(self):
        for tag in self.tags:
            items = tag.split(';')
            if len(items) > 1 and items[0] == 'C用':
                try:
                    name = items[2] if len(items) > 2 and len(items[2]) > 0 and items[2] != '=' else 'coref'
                    self.coreference_link[name] = CoreferenceEntry(
                        nlelement.ChunkReference(self.sid, self.cid), nlelement.ChunkReference(self.sid-int(items[3]), int(items[4])),
                        -1, -1, items[1]
                    )
                except IndexError as inst:
                    newinst = LoadError(inst=inst)
                    newinst.cid = self.cid
                    newinst.problemed = str(self.tags)+' :> '+ tag
                    newinst.sent_i = self.sid
                    raise newinst from inst
def tokenline_tokenize(line: str):
    """形態素行の区切りがすごく作りづらいので専用関数化
    表層表現の方にスペースがあるとすべて破綻するので確実性の高い後ろからパース
    後ろ2つをパースしたらデータ数から推定する
    """
    parser = AnnotationLineParser()
    toks = parser.load_token_text(line)
    # 非常に不快なコードだがコーパスのほうが例外なのでしょうがない
    # スペース入り形態素に対しての解析結果がスペース×３だけずれるので後ろにからの要素を挿入することで元に戻す
    try:
        if toks[0][6] == '特殊':
            toks[0].append('0')
            toks[0].append('*')
            toks[0].append('0')
    except IndexError as inst:
        newinst = LoadError(inst=inst)
        newinst.input_line = line
        newinst.problemed = toks
        raise newinst from inst
    if len(toks[0]) != 11:
        # ちょっとこれでいいのか感あるけど 8 引いた値までが表層＋読みなのでそこを3分割までつなげる
        surf_yomi_len = len(toks[0])-8
        surf_yomi_token_len = surf_yomi_len // 3
        #print('len (token) =', str(len(test_tokens)))
        if surf_yomi_len % 3 != 0:
            raise RuntimeError(str(toks[0]))
        for i in [0, 1, 2]:
            start_i = i * surf_yomi_token_len
            toks[0][start_i] = join_with(toks[0][start_i:start_i+surf_yomi_token_len], ' ')
        for i in [0, 1, 2]:
            start_i = i * (surf_yomi_token_len - 1)
            del toks[0][start_i+1:start_i+surf_yomi_token_len]
    if len(toks[1]):
        toks[0].append(toks[1][0])
    toks[0].append(toks[2])
    return toks
class Token(nlelement.Token):
    """形態素（単語）のクラス
    """
    def __init__(self, tid, expr):
        nlelement.Token.__init__(self)
        self.tid = tid
        (header, mid, other) = tokenline_tokenize(expr)
        try:
            # 出力は固定長なので必ず13分割
            self.surface = header[0]
            self.read = header[1]
            self.basic_surface = header[2]
            self.part = header[3]
            self.part_id = int(header[4])
            self.attr1 = header[5]
            self.attr2 = header[7]
            self.pos = self.part + '-' + self.attr1 + '-' + self.attr2
            if self.part == '名詞':
                self.sahen = (self.attr1 == 'サ変名詞')
                self.normalnoun = (self.attr1 == '普通名詞')
                self.adjectivenoun = (self.attr1 == '副詞的名詞')
            self.conj_type = header[7]
            self.conj_form = header[9]
            self.other_features = other
            # 内容語 / 機能語(func)の分別
            if '文節主辞' in self.other_features:
                self.is_content = True
            # 自立語 / 付属語の選別
            if '自立' in self.other_features:
                self.is_indep = True
            # 固有表現の取得
            for feature in self.other_features:
                if re.match('NE:', feature):
                    self.__parse_ne_expr__(feature)
                    break
        except Exception as inst:
            newinst = LoadError(inst=inst)
            newinst.problemed = str(header)
            newinst.input_line = expr
            newinst.token_i = tid
            raise newinst from inst
    def __parse_ne_expr__(self, expr):
        """引数で渡した固有表現タグをもとにした固有表現属性を形態素に設定
        Args:
            expr: 固有表現文字列(NE:ORGANIZATION)のような形式
        """
        ne_features = expr.split(':')
        self.named_entity = ne_features[1]
        self.named_entity_part = ne_features[2] if len(ne_features) > 2 else ''
