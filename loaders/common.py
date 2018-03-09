
class LoadError(Exception):
    """解析時に発生したエラーを上に伝える
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
        if self.file_name:
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