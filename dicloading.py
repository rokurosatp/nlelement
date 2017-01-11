import sys
import KNBCInput
from enum import Enum
"""辞書データを基にしたidの付与と辞書の構築を行う
"""
class IdDicionary:
    """Idを自動で振るときに使う
    """
    def __init__(self):
        self.__dic__ = {}
    def __setitem__(self, name, value):
        self.__dic__[name] = value
    def __getitem__(self, name):
        return self.__dic__[name]
    def __contains__(self, name):
        return name in self.__dic__
    def add_value(self, name):
        """Iｄを追加する
        すでに登録されている場合は何もしない
        """
        if name in self.__dic__:
            pass
        else:
            new_id = len(self.__dic__)
            self.__dic__[name] = new_id
    def __iter__(self):
        return iter(self.__dic__)
    def items(self):
        return self.__dic__.items()
    def __len__(self):
        return len(self.__dic__)
class DicAttributeId(Enum):
    """辞書の要素のID
    """
    word = 0
    word_base = 1
    pos = 2
    netag = 3
    case = 4
    conj = 5
    cl_rank = 6
    cl_order = 7
    case_id = 8
class IdDictionaryList:
    """コーパスから得られる単語やposタグなどの集合から生成した表現-IDの対応付けリスト
    """
    def __init__(self):
        self.word = IdDicionary()
        self.word_base = IdDicionary()
        self.pos = IdDicionary()
        self.netag = IdDicionary()
        self.case = IdDicionary()
        self.conj = IdDicionary()
        self.cl_rank = IdDicionary()
        self.cl_order = IdDicionary()
        self.case_id = IdDicionary()
        self.from_id_dic = {
            DicAttributeId.word : self.word,
            DicAttributeId.word_base : self.word_base,
            DicAttributeId.pos : self.pos,
            DicAttributeId.netag : self.netag,
            DicAttributeId.case : self.case,
            DicAttributeId.conj : self.conj,
            DicAttributeId.cl_order : self.cl_rank,
            DicAttributeId.cl_rank : self.cl_order,
            DicAttributeId.case_id : self.case_id,
        }
    def load(self):
        """設定したディレクトリにある構築済み辞書からロード
        """
        targets = [
            ('dic/word.def', self.word),
            ('dic/wordbasic.def', self.word_base),
            ('dic/pos.def', self.pos),
            ('dic/netag.def', self.netag),
            ('dic/case.def', self.case),
            ('dic/conj.def', self.conj),
            ('dic/case_id.def', self.case_id)
        ]
        for target in targets:
            with open(target[0], 'r') as file:
                for line in file:
                    line = line[0:-1]
                    name_value = line.split(',')
                    target[1][name_value[0]] = int(name_value[1])
    def save(self):
        """構築した辞書をファイルに保存
        """
        targets = [
            ('dic/word.def', self.word),
            ('dic/wordbasic.def', self.word_base),
            ('dic/pos.def', self.pos),
            ('dic/netag.def', self.netag),
            ('dic/case.def', self.case),
            ('dic/conj.def', self.conj),
        ]
        print('saving files')
        for target in targets:
            print(target)
            with open(target[0], 'w') as file:
                print('length:'+str(len(target[1])))
                for (key, value) in target[1].items():
                    file.write(key+','+str(value)+'\n')
                file.close()
    def load_from_corpus(self):
        """辞書データをコーパスから構築
        """
        loader = KNBCInput.KNBCLoader(KNBCInput.get_corpus_path())
        print('loading dic name')
        for doc in loader:
            print(doc.name)
            for sent in doc.sentences:
                for token in sent.tokens:
                    self.word.add_value(token.surface)
                    self.word_base.add_value(token.basic_surface)
                    self.pos.add_value(token.pos)
                    self.netag.add_value(token.named_entity)
                    if token.part == '接続詞':
                        self.conj.add_value(token.surface)
                for chunk in sent.chunks:
                    if chunk.case is not None and len(chunk.case) > 0:
                        self.case.add_value(chunk.case)

def main():
    pass
if __name__ == "__main__":
    main()