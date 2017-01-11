# -*- encoding utf-8 -*-
"""
ツールとコーパスから得られた共参照関係を元にエラーを計算する。
TODO 同じエンティティを指す名詞を差した場合どうするか

"""
def __comp_reference_tuple4__(left, right):
    for i in [0, 1, 2, 3]:
        if left[i] > right[i]:
            return -1
        elif left[i] < right[i]:
            return 1
        else:
            pass
    return 0
def __comp_reference_tuple5__(left, right):
    for i in [0, 1, 2, 3, 4]:
        if left[i] > right[i]:
            return -1
        elif left[i] < right[i]:
            return 1
        else:
            pass
    return 0
def __next_noexcept__(iterator):
    result = None
    try:
        result = next(iterator)
    except StopIteration:
        pass
    return result
class ErrorMakingIteration:
    """結果を比較し、異なる場合に+1または-1をつける反復処理の実装
    """
    def __init__(self, solver_output, theory_output):
        self.solver_output = solver_output
        self.theory_output = theory_output
        self.get_error = lambda item, errorvalue: None
        self.comp_reference_tuple = lambda item1, item2: -1
    def get_error_list(self):
        """エラーのリストを取得
        イテレーターで中身を列挙しながら比較を行うるーぷ
        内部でget_errorとcomp_reference_tupleが呼び出される、
        継承先でこれらのメソッドを変更することで様々な参照に対応してください
        """
        iter_theory, iter_solver = iter(self.theory_output), iter(self.solver_output)
        error_items = []
        item_theory = __next_noexcept__(iter_theory)
        item_solver = __next_noexcept__(iter_solver)
        while item_theory != None or item_solver != None:
            if item_theory != None:
                if item_solver != None:
                    val = self.comp_reference_tuple(item_theory, item_solver)
                    if val < 0:
                        error_items.append(self.get_error(item_theory, -1))
                        item_theory = __next_noexcept__(iter_theory)
                    elif val > 0:
                        error_items.append(self.get_error(item_solver, 1))
                        item_solver = __next_noexcept__(iter_solver)
                    else:
                        item_theory = __next_noexcept__(iter_theory)
                        item_solver = __next_noexcept__(iter_solver)
                else:
                    error_items.append(self.get_error(item_theory, -1))
                    item_theory = __next_noexcept__(iter_theory)
            else:
                if item_solver != None:
                    error_items.append(self.get_error(item_solver, 1))
                    item_solver = __next_noexcept__(iter_solver)
        return error_items
class BasicErrorHandle:
    """エラー比較器
    入力された２つのデータ列（グラフ上の辺みたいな２点間データ）を比較して、その差分を出力する
    """
    def __init__(self):
        self.corpus_output = None
        self.parser_output = None
        self.error_items = []
        self.get_error_operation = None
        self.comp_reference_tuple = None
    def set_corpus_output(self, output):
        """コーパス（理想出力）側のデータへの参照をインスタンスに設定
        """
        self.corpus_output = output
    def set_parser_output(self, output):
        """解析器側のデータへの参照をインスタンスに設定
        """
        self.parser_output = output
    def calc_error_items(self):
        """コーパスの共参照関係、解析器の出力したエラー情報を元にエラー情報を構築する
        今のところは識別タスクでコーパスが示す共参照関係の２名詞句とツールが示す共参照関係の２名詞句が一致した場合のみ正しいと判断
        """
        #イテレーターで中身を列挙しながら比較を行うるーぷ
        iteration = ErrorMakingIteration(self.parser_output, self.corpus_output)
        iteration.get_error = self.get_error_operation
        iteration.comp_reference_tuple = self.comp_reference_tuple
        result = iteration.get_error_list()
        return result
class PredicateHandle(BasicErrorHandle):
    """ツールとコーパスから得られた述語項関係を元にエラーを計算する。
    """
    def __init__(self):
        BasicErrorHandle.__init__(self)
        self.get_error_operation = lambda item, error: (item[0], item[1], item[2], item[3], item[4], error)
        self.comp_reference_tuple = __comp_reference_tuple4__
class CoreferenceHandle(BasicErrorHandle):
    """ツールとコーパスから得られた共参照関係を元にエラーを計算する。
    """
    def __init__(self):
        BasicErrorHandle.__init__(self)
        self.get_error_operation = lambda item, error: (item[0], item[1], item[2], item[3], error)
        self.comp_reference_tuple = __comp_reference_tuple4__
