import os
import re
from application import myprogress
from . import nlelement
from . import loadercommon

    
class ChunkMarger:
    def __init__(self):
        self.doc_table = {}
        self.sent_table = {}
        self.error_count = 0
        self.total_error = 0
        self.error_set = set()
    def __map_document__(self, origs):
        self.doc_table = {}
        for orig in origs:
            self.doc_table[orig.name] = orig
    def merge(self, origs, annotations):
        """メモリにロードするデータが多すぎて遅い、iterを使ってください
        """
        self.__map_document__(origs)
        self.error_count = 0
        progress = myprogress.make_progress(max_value=len(annotations))
        count = 0
        for annotation in annotations:
            if annotation.name in self.doc_table:
                self.error_count = 0
                self.__merge_doc__(self.doc_table[annotation.name], annotation)
                if self.error_count > 0:
                    print('error detected:', annotation.name)
                    self.error_set.add(annotation.name)
                    self.total_error += self.error_count
            count += 1
            progress.update(count)
        progress.finish()
    def merge_by_iterator(self, origs, annotation_iter, length):
        self.__map_document__(origs)
        self.error_count = 0
        progress = myprogress.make_progress(max_value=length)
        count = 0
        for annotation in annotation_iter:
            if annotation.name in self.doc_table:
                self.error_count = 0
                self.__merge_doc__(self.doc_table[annotation.name], annotation)
                if self.error_count > 0:
                    print('error detected:', annotation.name)
                    self.error_set.add(annotation.name)
                    self.total_error += self.error_count
            count += 1
            progress.update(count)
        progress.finish()
    def __merge_doc__(self, orig, annotation):
        self.__merge_chunkofdoc__(orig, annotation)
        map_table = self.__map_chunk__(orig, annotation)
        self.__merge_links__(orig, annotation, map_table)
    def __map_chunk__(self, orig, annotation):
        """anno => origの文節オブジェクトの対応テーブルを作成
        """
        map_table = {}
        for orig_chunk, anno_chunk in zip(
            nlelement.chunks(orig), nlelement.chunks(annotation)
        ):
            map_table[id(anno_chunk)] = orig_chunk
        return map_table
    def __merge_links__(self, orig, annotation, map_table):
        """係り受け情報をannotationからコピーする
        """
        for orig_chunk, anno_chunk in zip(
            nlelement.chunks(orig), nlelement.chunks(annotation)
        ):
            orig_chunk.link = map_table[id(anno_chunk.link)] \
                if anno_chunk.link and id(anno_chunk.link) in map_table else None
        for orig_chunk in nlelement.chunks(orig):
            if orig_chunk.link and orig_chunk.sid == orig_chunk.link.sid:
                orig_chunk.link_id = orig_chunk.link.cid
            
    def __merge_chunkofdoc__(self, orig, annotation):
        """annotationにある文節の区切り情報を基にorigにChunkオブジェクトを追加する
        """
        orig_count = 0
        anno_count = 0
        orig_to, anno_to = 0, 0
        orig_cid, anno_cid = 0, 0
        orig_titer = iter(nlelement.tokens(orig))
        for chunk in nlelement.chunks(annotation):
            orig_chunk = nlelement.Chunk()
            orig_ti, anno_ti = -1, -1
            orig_surf, anno_surf = '', ''
            for tok in chunk.tokens:
                anno_surf += tok.surface
                anno_count += tok.get_length()
                anno_ti += 1
                while orig_count < anno_count:
                    try:
                        orig_tok = next(orig_titer)
                    except StopIteration:
                        return
                    orig_count += orig_tok.get_length()
                    orig_chunk.tokens.append(orig_tok)
                    orig_ti += 1
                    orig_surf += orig_tok.surface
                if orig_count == anno_count:
                    if orig_surf != anno_surf:
                        #print('orig:{0} != anno:{1}'.format(orig_surf, anno_surf))
                        self.error_count += 1
                        # TODO:修正用の処理を加える
                    orig_surf = ''
                    anno_surf = ''
                if anno_ti == chunk.head_position:
                    orig_chunk.head_position = orig_ti
                elif anno_ti == chunk.func_position:
                    orig_chunk.func_position = orig_ti
            for chunk in self.__detect_chunk_border__(orig_chunk):
                if chunk.sid < 0:
                    chunk.sid = orig_titer.cur_sent.sid
                orig_sent = orig.refer_sentence(chunk.sid)
                chunk.cid = len(orig_sent.chunks)
                orig_sent.chunks.append(chunk)
    def __detect_chunk_border__(self, chunk):
        border = []
        last_sid = -1
        for i, token in enumerate(chunk.tokens):
            if last_sid != token.sid:
                border.append(i)
                last_sid = token.sid
        if len(border) <= 1:
            border = None
            chunk.sid = last_sid
            chunk.token_num = len(chunk.tokens)
            return [chunk]
        result = []
        border.append(len(chunk.tokens))
        last_i = 0
        for i in border:
            if i != 0:
                result.append(nlelement.Chunk())
                last_chunk = result[-1]
                last_chunk.tokens = chunk.tokens[last_i:i]
                last_chunk.sid = chunk.tokens[last_i].sid
                if i <= chunk.head_position and chunk.head_position < i:
                    last_chunk.head_position = chunk.head_position - last_i
                if i <= chunk.func_position and chunk.func_position < i:
                    last_chunk.func_position = chunk.func_position - last_i
                if last_chunk.head_position >= last_chunk.func_position:
                    last_chunk.func_position = last_chunk.head_position
            last_i = i
            continue
        return result

def test_merger():
    from . import database
    import sys
    doc_name = 'PM41_00304'
    if sys.argv[1:]:
        doc_name = sys.argv[1]
    anno = database.loadone('./out/deppara.db', name=doc_name)[0]
    orig = database.loadone('./out/m_xml.db', name=doc_name)[0]
    merger = ChunkMarger()
    #print('orig: ', '/'.join(map(lambda x:x.surface, nlelement.tokens(orig))))
    #print('anno: ', '/'.join(map(lambda x:x.surface, nlelement.tokens(anno))))
    print('chunking: ', '/'.join(map(lambda x:x.get_surface(), nlelement.chunks(anno))))
    merger.merge([orig], [anno])
    print('retrieved : ', '/'.join(map(lambda x:x.get_surface(), nlelement.chunks(orig))))
    print(anno.name, '/error_count: ', merger.total_error)

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
            self.file_name = ''
            self.message = ''
            self.line_num = -1
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
        self.line_num = src.line_num
        self.file_name = src.file_name
        self.problemed = src.problemed
        self.message = src.message
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
        positional_expr = ''
        if len(self.file_name) > 0:
            positional_expr += self.file_name + ' at '
        if self.line_num > 0:
            positional_expr += 'line ' + str(self.line_num)
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
        result += '\n'.join(result_list)
        return result

def __is_case__(token):
    if token is None or token.part != '助詞' or token.attr1 != '格助詞':
        return False
    return True

def __get_depend_number__(expr):
    return int(expr.replace('D', '').replace('P', '').replace('I', ''))

class CabochaLoader:
    def __init__(self, directory):
        self.directory = directory
        self.target_file = re.compile(r'.*\.(cab|cabocha)$')
        self.filenamegetter = re.compile(r'.*[\\|/](.+)\.(cab|cabocha)$')
        self.chunk_ref_pat = re.compile(r'(-?[0-9]+)([A-Z]+)')
        self.filter_func = lambda name: self.target_file.match(name)
        self.item_list = None
        self.doc_file = None
        self.line = None
        self.line_num = None
        self.ids = loadercommon.NlElementIds()
        self.entity_ids = dict()
    def __get_docname__(self, filename):
        basename = self.filenamegetter.match(filename).group(1)
        docname = '_'.join(basename.split('_')[-2:])
        return docname
    def load(self):
        ids = loadercommon.IdGenerator()
        documents = []
        self.item_list = list(map(lambda x: os.path.join(self.directory, x), filter(self.filter_func, os.listdir(self.directory))))
        progress = myprogress.make_progress(max_value=len(self.item_list))
        count = 0
        for self.doc_file in self.item_list:
            with open(self.doc_file, encoding='utf-8') as file:
                basename = self.__get_docname__(self.doc_file)
                try:
                    docs = self. __load_document__(file)
                except LoadError as inst:
                    inst.message = '{0} {1}'.format('Load Failed{0}'.format(basename), inst.message)
                    raise
                if len(docs) == 1:
                    docs[0].name = basename
                else:
                    ids.reset()
                    for doc in docs:
                        doc.name = basename+'_'+str(ids.get())
                documents.extend(docs)
            count += 1
            progress.update(count)
        progress.finish()
        return documents
    def __handle_comment__(self, comment):
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
        self.entity_ids = dict()
        
        chunk = None
        for self.line_num, self.line in enumerate(map(lambda x: x.rstrip('\r\n'), lines)):
            if self.line == 'EOT':
                self.__resolve_entity_id__(doc)
                self.entity_ids = dict()
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
    
    def __resolve_entity_id__(self, doc):
        """書かれていたidの一覧をすべて解決してtokenのメンバに代入
        """
        for tok in nlelement.tokens(doc):
            if hasattr(tok, "entity_links"):
                for key, value in tok.entity_links.items():
                    if value in self.entity_ids:
                        if key in ['ga', 'o', 'ni']:
                            if hasattr(tok, "predicate_term"):
                                tok.predicate_term = dict()
                            tok.predicate_term[key] = self.entity_ids[value]
                        elif key == "eq":
                            tok.corefernence = self.entity_ids[value]
                        else:
                            if hasattr(tok, "semrole"):
                                tok.semrole = dict()
                            tok.semrole[key] = self.entity_ids[value]

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
            token.read = header[7]
            token.basic_surface = header[6]
            token.part = header[0]
            token.part_id = loadercommon.part_id[header[0]] if header[0] in loadercommon.part_id else 10
            token.attr1 = header[1]
            token.attr2 = header[2]
            token.pos = token.part + '-' + token.attr1 + '-' + token.attr2
            if token.part == '名詞':
                token.sahen = (token.attr1 == 'サ変')
                token.normalnoun = (token.attr1 == '一般')
                token.adjectivenoun = (token.attr1 == '副詞可能')
            token.conj_type = header[4]
            token.conj_form = header[5]
            # 固有表現の取得
            if len(surf_feat) > 2:
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

    
    def __handle_annotation__(self, tok, annotations):
        """固有表現, 述語項, 意味役割の各アノテーションがトークンについている場合に解析する
        """
        for anno in annotations[2:]:
            anno = anno.rstrip('\n')
            if re.match(r'NE:', anno):
                ne_features = anno.split(':')
                tok.named_entity = ne_features[1]
                tok.named_entity_part = ne_features[2] if len(ne_features) > 2 else ''
            elif re.match(r'([^=]+=[\d]+,?)+', anno):
                for id_resolver in anno.split(','):
                    match = re.match(r'([^=]+)=([\d]+)', id_resolver)
                    if match.group(1) == 'id':
                        self.entity_ids[int(match.group(2))] = tok
                    else:
                        if not hasattr(tok, "entity_links"):
                            setattr(tok, "entity_links", dict())
                            tok.entity_links[match.group(1)] = int(match.group(2))
    
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
class CabochaDumper:
    @staticmethod
    def preprocess_doc(document: nlelement.Document):
        """entityの参照生成のためにid=?,eq=?形式のメンバをあらかじめtokenに張り付ける
        """
        refered_entities = []
        for tok in nlelement.tokens(document):
            if hasattr(tok, "predicate_term"):
                for key, value in tok.predicate_term.items():
                    refered_entities.append(nlelement.TokenReference(value.ana_sid, value.ana_tid))
            elif hasattr(tok, "coreference"):
                value = getattr(tok, "coreference")
                refered_entities.append(nlelement.TokenReference(value.ana_sid, value.ana_tid))
            elif hasattr(tok, "semrole"):
                for key, value in tok.semrole.items():
                    refered_entities.append(nlelement.make_reference(value))
        
        refered_entities.sort()
        del_list = []
        last_ent = None
        for ent in refered_entities:
            if last_ent and ent == last_ent:
                del_list.append(ent)
            last_ent = ent
        for ent in del_list:
            refered_entities.remove(ent)
        del_list = None

        entity_id_table = dict()
        for e_id, ref in enumerate(refered_entities):
            setattr(document.refer(ref), "entity_id", e_id)
            entity_id_table[ref.to_tuple()] = e_id
        for tok in nlelement.tokens(document):
            if hasattr(tok, "predicate_term"):
                setattr(tok, "predicate_term", dict())
                for key, value in tok.predicate_term.items():
                    ref = nlelement.TokenReference(value.ana_sid, value.ana_tid)
                    if not hasattr(tok, "entity_links"):
                        tok.entity_links = dict()    
                    tok.entity_links[key] = entity_id_table[ref.to_tuple()]
            elif hasattr(tok, "coreference"):
                value = tok.coreference
                ref = nlelement.TokenReference(value.ana_sid, value.ana_tid)
                if not hasattr(tok, "entity_links"):
                    tok.entity_links = dict()
                tok.entity_links['eq'] = entity_id_table[ref.to_tuple()]
            elif hasattr(tok, "semrole"):
                setattr(tok, "semrole", dict())
                for key, value in tok.semrole.items():
                    ref = nlelement.make_reference(value)
                    if not hasattr(tok, "entity_links"):
                        tok.entity_links = dict()
                    tok.entity_links[key] = entity_id_table[ref.to_tuple()]

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
        result += token.conj_type + ','
        result += token.conj_form + ','
        result += token.basic_surface + ','
        result += token.read + ','
        
        result += token.read + '\t'
        result += 'B-'+token.named_entity if token.named_entity != '' else 'O'

        entity_anno = CabochaDumper.__annotation_to_format__(token)
        if entity_anno:
            result += '\t'
            result += entity_anno

        result += '\n'
        return result

    @staticmethod
    def __annotation_to_format__(token: nlelement.Token):
        result_items = []
        if hasattr(token, 'entity_id'):
            result_items.append('id={}'.format(getattr(token, "entity_id")))
        if hasattr(token, 'entity_links'):
            for key, value in getattr(token, "entity_links").items():
                result_items.append('{}={}'.format(key, value))
        return ';'.join(result_items)

def load(dirname):
    loader = CabochaLoader(dirname)
    return loader.load()
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
