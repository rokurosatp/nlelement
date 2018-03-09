import os
import re
from nlelement import nlelement
from nlelement import loadercommon
from .common import LoadError

class CabochaLoader:
    def __init__(self, morph_dic_name='unidic'):
        self.filenamegetter = re.compile(r'.*[\\|/](.+)\.(cab|cabocha)$')
        self.chunk_ref_pat = re.compile(r'(-?[0-9]+)([A-Z]+)')
        self.item_list = None
        self.doc_file = None
        self.line = None
        self.line_num = None
        self.ids = loadercommon.NlElementIds()
        if morph_dic_name == 'ipadic':
            self.pos_load_func = self.__load_token_pos_ipadic__
        elif morph_dic_name == 'unidic':
            self.pos_load_func = self.__load_token_pos_unidic__
        else:
            self.pos_load_func = self.__load_token_pos_unidic__
    def __get_docname__(self, filename):
        basename = self.filenamegetter.match(filename).group(1)
        docname = '_'.join(basename.split('_')[-2:])
        return docname
    def load(self, text, basename="cabocha_auto_load"):
        ids = loadercommon.IdGenerator()
        docs = []
        try:
            docs = self. __load_document__(text.splitlines())
        except LoadError as inst:
            inst.message = '{0} {1}'.format('Load Failed{0}'.format(basename), inst.args[0])
            raise
        if len(docs) == 1:
            docs[0].name = basename
        else:
            ids.reset()
            for doc in docs:
                doc.name = basename+'_'+str(ids.get())
        return docs
    def load_file(self, file_name, encoding='utf-8'):
        ids = loadercommon.IdGenerator()
        docs = []
        with open(file_name, encoding=encoding) as file:
            basename = self.__get_docname__(file_name)
            try:
                docs = self. __load_document__(file)
            except LoadError as inst:
                inst.message = '{0} {1}'.format('Load Failed{0}'.format(basename), inst.args[0])
                raise
            if len(docs) == 1:
                docs[0].name = basename
            else:
                ids.reset()
                for doc in docs:
                    doc.name = basename+'_'+str(ids.get())
        return docs

    def __handle_comment__(self, comment):
        pass
    def __handle_annotation__(self, tok, annotation):
        pass
    def __validate_sentence__(self, sentence):
        """係り先チャンクが正しい参照先を示しているか確認する
        NOTE: 特殊仕様として係り先が無効の場合は参照を-1に変換する。
        """
        #print('validation:', sentence.get_surface())
        chunk_num = len(sentence.chunks)
        token_num = len(sentence.tokens)
        for chunk in sentence.chunks:
            if chunk.link_id not in range(-1, chunk_num):
                chunk.link_id = -1
                #raise RuntimeError('{2}: {0} not in {1}'.format(chunk.link_id, range(-1, chunk_num), self.doc_file)+sentence.get_surface())

    def __load_document__(self, lines):
        docs = []
        self.ids.sent.reset()
        doc = nlelement.Document()
        docs.append(doc)
        sentence = nlelement.Sentence()
        sentence.sid = self.ids.sent.get()
        self.ids.chunk.reset()
        self.ids.tok.reset()
        
        chunk = None
        for self.line_num, self.line in enumerate(map(lambda x: x.rstrip('\r\n'), lines)):
            if self.line == 'EOT':
                doc = nlelement.Document()
                docs.append(doc)
            elif self.line == 'EOS':
                self.__validate_sentence__(sentence)
                doc.sentences.append(sentence)
                sentence = nlelement.Sentence()
                sentence.sid = self.ids.sent.get()
                chunk = None
                self.ids.chunk.reset()
                self.ids.tok.reset()
            elif self.line[0] == '#':
                if self.line[1] == '!':
                    self.__handle_comment__(self.line)
            elif self.line[0] == '*' or self.line[0] == '+':
                if chunk:
                    chunk.set_token_info()
                chunk = self.__load_chunk__(self.line, sentence.sid)

                chunk.cid = self.ids.chunk.get()
                sentence.chunks.append(chunk)
            elif len(self.line) == 0:
                pass
            else:
                token = self.__load_token__(self.line)
                token.tid = self.ids.tok.get()
                chunk.tokens.append(token)
                chunk.token_num += 1
                self.__token_post_process__(chunk, token)
                sentence.tokens.append(token)
        return docs
    
    def __load_chunk__(self, line, sid):
        chunk = nlelement.Chunk()
        chunk.sid = sid
        try:
            tokens = line.split(' ')
            match = self.chunk_ref_pat.match(tokens[2])
            if not match:
                raise RuntimeError('Invalid Link Expression')
            chunk.link_id = int(match.group(1))
            token_func = tokens[3].split('/')
            if int(token_func[1]) != int(token_func[0]):
                chunk.head_position = int(token_func[0])
                chunk.func_position = int(token_func[1])
            else:
                chunk.func_position = -1
                chunk.head_position = int(token_func[0])
        except Exception as inst:
            newinst = LoadError(inst=inst)
            newinst.problemed = str(tokens)
            newinst.input_line = line
            newinst.token_i = -1
            newinst.line_num = self.line_num
            newinst.file_name = self.doc_file
            newinst.set_args()
            raise newinst from inst     
        return chunk

    def __load_token__(self, line):
        token = nlelement.Token()
        surf_feat = line.split('\t')
        header = surf_feat[1].split(',')
        try:
            # 出力は固定長なので必ず13分割
            token.surface = surf_feat[0]
            token = self.pos_load_func(token, header)
            # 固有表現の取得（汎用を想定しているが、depparaには不要）
            if len(surf_feat) > 2 and re.match('NE:', surf_feat[2]):
                if surf_feat[2][-1] == '\n':
                    surf_feat[2] = surf_feat[2][:-1]
                ne_features = surf_feat[2].split(':')
                token.named_entity = ne_features[1]
                token.named_entity_part = ne_features[2] if len(ne_features) > 2 else ''
            elif len(surf_feat) > 2:
                self.__handle_annotation__(self, surf_feat)
        except Exception as inst:
            newinst = LoadError(inst=inst)
            newinst.problemed = str(header)
            newinst.input_line = line
            newinst.token_i = -1
            newinst.line_num = self.line_num
            newinst.file_name = self.doc_file
            newinst.set_args()
            raise newinst from inst
        return token
    def __token_post_process__(self, chunk, token):
        """トークンをチャンクに追加した後に追加したトークンに応じて属性値を変更する
        内容語の場合は機能表現の位置を+1するとか
        「」が入る場合、begin_paren end_paren emphasisの値が変更される
        """
        if len(chunk.tokens) <= chunk.head_position + 1:
            token.is_content = True
        if token.surface == '「':
            chunk.begin_paren = True
            chunk.emphasis = True
        elif token.surface == '」':
            chunk.end_paren = True
            chunk.emphasis = True
        return token

    def __load_token_pos_unidic__(self, token, header):
        """unidic式のフォーマットに対する形態素のロードを行う
        ARGS:
            token(): このトークンに属性を書き込む
            header(list<str>): csv形式の素性リスト
        """
        token.read = header[9]
        token.basic_surface = header[7]
        token.part = header[0]
        token.part_id = loadercommon.part_id[header[0]] if header[0] in loadercommon.part_id else 10
        token.attr1 = header[1]
        token.attr2 = header[2]
        token.attr3 = header[3]
        token.conj_type = header[4] if header[4] != "*" else ""
        token.conj_form = header[5] if header[5] != "*" else ""
        # attrの設定方法から修正, 0-4には必ず品詞-属性の順番で前から並ぶ
        token.pos = '-'.join(filter(lambda s: s and s != '*',header[0:4]))
        # TODO: それぞれのチャンクにはキャッシュ属性的な属性がかなり付いているが,やっぱり除去したいので使用しているセクションを整理する
        if token.part == '名詞':
            token.sahen = (token.attr2 == 'サ変可能')
            token.normalnoun = (token.attr2 == '一般')
            token.adjectivenoun = (token.attr2 == '副詞可能')
        return token

    def __load_token_pos_ipadic__(self, token, header):
        """ipa式のフォーマットに対する形態素ロードを行う
        TODO: IPA用の辞書は容易だけしてあるが、使用していないのでバグがあるかも、テスト書いてね
        """
        token.read = header[7]
        token.basic_surface = header[6]
        token.part = header[0]
        token.part_id = loadercommon.part_id[header[0]] if header[0] in loadercommon.part_id else 10
        token.attr1 = header[1]
        token.attr2 = header[2]
        token.conj_type = header[4] if header[4] != "*" else ""
        token.conj_form = header[5] if header[5] != "*" else ""
        # attrの設定方法から修正, 0-4には必ず品詞-属性の順番で前から並ぶ
        token.pos = '-'.join(filter(lambda s: s and s != '*',header[0:3]))
        # TODO: それぞれのチャンクにはキャッシュ属性的な属性がかなり付いているが,やっぱり除去したいので使用しているセクションを整理する
        if token.part == '名詞':
            token.sahen = (token.attr1 == 'サ変')
            token.normalnoun = (token.attr1 == '一般')
            token.adjectivenoun = (token.attr1 == '副詞可能')
        return token


class CabochaDumper:
    @staticmethod
    def doc_to_format(document: nlelement.Document):
        """DocumentオブジェクトからCaboChaフォーマットを生成する
        """
        fmt_text = ''
        for sentence in document.sentences:
            fmt_text += CabochaDumper.sent_to_format(sentence)
        fmt_text += 'EOT\n'
        return fmt_text
    @staticmethod
    def sent_to_format(sentence: nlelement.Sentence):
        """SentenceオブジェクトからCaboChaフォーマットを生成する
        """
        fmt_text = ''
        for chunk in sentence.chunks:
            fmt_text += CabochaDumper.chunk_to_format(chunk)
            for token in chunk.tokens:
                fmt_text += CabochaDumper.token_to_format(token)
        fmt_text += 'EOS\n'
        return fmt_text
    @staticmethod
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
    @staticmethod
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
        result += token.conj_type if token.conj_type else "*" + ','
        result += token.conj_form if token.conj_form else "*" + ','
        result += token.basic_surface + ','
        result += token.read + ','
        result += token.read + '\t'
        result += 'B-'+token.named_entity if token.named_entity != '' else 'O'
        result += '\n'
        return result
def load(path, encoding='utf-8'):
    if os.path.isdir(path):
        return load_directory(path, encoding=encoding)
    return load_file(path, encoding=encoding)

def load_directory(dirname, encoding='utf-8'):
    loader = CabochaLoader()
    return loader.load(dirname, encoding=encoding)

def load_file(filename, encoding='utf-8'):
    loader = CabochaLoader()
    return loader.load_file(filename, encoding=encoding)

def dump(elem):
    if isinstance(elem, nlelement.Document):
        return CabochaDumper.doc_to_format(elem)
    elif isinstance(elem, nlelement.Sentence):
        return CabochaDumper.sent_to_format(elem)
    elif isinstance(elem, nlelement.Chunk):
        return CabochaDumper.chunk_to_format(elem)
    elif isinstance(elem, nlelement.Token):
        return CabochaDumper.token_to_format(elem)
    raise TypeError('The function could dump not {0} but Document, Chunk, Sentence, Token'.format(type(elem)))
