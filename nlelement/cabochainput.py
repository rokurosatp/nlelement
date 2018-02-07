from . import nlelement

"""
KNBコーパスから素性をロードする

TODO　だいぶコードが複雑になってきたのでリファクタリングしたい

"""
import glob
import os
import re
from enum import Enum
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


class Document(nlelement.Document):
    """KNBC用の文章データ
    構造の定義は基底クラスで行っているので
    読み込み処理のみ実装する
    """
    def __init__(self, inputlines):
        """読み込みを含めた初期化を行う
        KNBCでは文章がディレクトリの単位になっている
        Args:
            directory_path (str): 対応するディレクトリのパスを指定する
        """
        nlelement.Document.__init__(self)
        self.name = ''
        sentencelines = []
        for inputline in inputlines:
            if inputline == 'EOT\n':
                break
            elif inputline == 'EOS\n':
                sentencelines.append(inputline)
                self.sentences.append(Sentence(len(self.sentences), sentencelines))
                sentencelines.clear()
            else:
                sentencelines.append(inputline)
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
        self.sid = sid
        self.name = ''
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
        Description:
            ちなみにCaboChaの文節フォーマットはこんな感じ
            * 文節番号 係り先文節IDとその関係（基本D） 文節主辞ID/機能語ID スコア 
            例
            * 1 2D 0/0 0.00000
        """
        nlelement.Chunk.__init__(self)
        (self.sid, self.cid) = (sid, cid)
        tokens = expr.split(' ')
        self.link_id = int(tokens[2][:-1])
        token_func = tokens[3].split('/')
        if int(token_func[1]) != int(token_func[0]):
            self.head_position = int(token_func[0])
            self.func_position = int(token_func[1])
        else:
            self.func_position = -1
            self.head_position = int(token_func[0])
    def on_add_token(self, token):
        """トークンをチャンクに追加した際に追加したトークンに応じて属性値を変更する
        内容語の場合は機能表現の位置を+1するとか
        「」が入る場合、begin_paren end_paren emphasisの値が変更される
        """
        if len(self.tokens) <= self.head_position + 1:
            token.is_content = True
        if token.surface == '「':
            self.begin_paren = True
            self.emphasis = True
        elif token.surface == '」':
            self.end_paren = True
            self.emphasis = True
part_id = {
    '名詞':0,
    '助詞':1,
    '動詞':2,
    '形容詞':3,
    '形容動詞':4,
    '副詞':5,
    '助動詞':6,
    '連体詞':7,
    '記号':8,
    'フィラー':9,
}

class Token(nlelement.Token):
    """形態素（単語）のクラス
    """
    def __init__(self, tid, expr):
        nlelement.Token.__init__(self)
        self.tid = tid
        surf_feat = expr.split('\t')
        header = surf_feat[1].split(',')
        try:
            # 出力は固定長なので必ず13分割
            self.surface = surf_feat[0]
            self.read = header[7]
            self.basic_surface = header[6]
            self.part = header[0]
            self.part_id = part_id[header[0]] if header[0] in part_id else 10
            self.attr1 = header[1]
            self.attr2 = header[2]
            self.pos = self.part + '-' + self.attr1 + '-' + self.attr2
            if self.part == '名詞':
                self.sahen = (self.attr1 == 'サ変')
                self.normalnoun = (self.attr1 == '一般')
                self.adjectivenoun = (self.attr1 == '副詞可能')
            self.conj_type = header[4]
            self.conj_form = header[5]
            # 固有表現の取得
            if re.match('NE:', surf_feat[2]):
                if surf_feat[2][-1] == '\n':
                    surf_feat[2] = surf_feat[2][:-1]
                self.__parse_ne_expr__(surf_feat[2])
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


def doc_to_format(document: nlelement.Document):
    """DocumentオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    for sentence in document.sentences:
        fmt_text += sent_to_format(sentence)
    fmt_text += 'EOT\n'
    return fmt_text
def sent_to_format(sentence: nlelement.Sentence):
    """SentenceオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    for chunk in sentence.chunks:
        fmt_text += chunk_to_format(chunk)
        for token in chunk.tokens:
            fmt_text += token_to_format(token)
    fmt_text += 'EOS\n'
    return fmt_text
def chunk_to_format(chunk: nlelement.Chunk):
    """ChunkオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    fmt_text += '* ' + '{0} {1}D '.format(chunk.cid, chunk.link_id)
    if chunk.func_position == chunk.token_num:
        fmt_text += '{0}/{1}'.format(chunk.head_position, chunk.head_position)
    else:
        fmt_text += '{0}/{1}'.format(chunk.head_position, chunk.func_position)
    fmt_text += ' 0.00000\n'
    return fmt_text
def token_to_format(token: nlelement.Token):
    """TokenオブジェクトからCaboCha(ほぼMeCab)フォーマットを生成する
    """
    result = ''
    result += token.surface
    result += '\t'
    result += token.part + ','
    result += token.attr1 + ','
    result += token.attr2 + ','
    result += '*' + ','
    result += token.conj_type + ','
    result += token.conj_form + ','
    result += token.basic_surface + ','
    result += token.read + ','
    result += token.read + '\t'
    result += 'B-'+token.named_entity if token.named_entity != '' else 'O'
    result += '\n'
    return result
        
