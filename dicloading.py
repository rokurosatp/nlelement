import sys
import yaml
from . import KNBCInput
from . import bccwj, database
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
    connparticle = 9
    semroles = 10
class IdDictionaryList:
    """コーパスから得られる単語やposタグなどの集合から生成した表現-IDの対応付けリスト
    """
    def __init__(self):
        self.word = IdDicionary()
        self.word_base = IdDicionary()
        self.pos = IdDicionary()
        self.netag = IdDicionary()
        self.case = IdDicionary()
        self.connparticle = IdDicionary()
        self.conj = IdDicionary()
        self.cl_rank = IdDicionary()
        self.cl_order = IdDicionary()
        self.case_id = IdDicionary()
        self.semrole = IdDicionary()
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
            DicAttributeId.connparticle : self.connparticle,
            DicAttributeId.semroles : self.semrole,
        }
    def load(self):
        """設定したディレクトリにある構築済み辞書からロード
        """
        targets = [
            ('dat/dic/defs/word.def', self.word),
            ('dat/dic/defs/wordbasic.def', self.word_base),
            ('dat/dic/defs/pos.def', self.pos),
            ('dat/dic/defs/netag.def', self.netag),
            ('dat/dic/defs/case.def', self.case),
            ('dat/dic/defs/connparticle.def', self.connparticle),
            ('dat/dic/defs/conj.def', self.conj),
            ('dat/dic/defs/case_id.def', self.case_id),
            ('dat/dic/defs/semroles.def', self.semrole),
        ]
        for target in targets:
            with open(target[0], 'r', encoding='utf-8') as file:
                for line in file:
                    line = line[0:-1]
                    name_value = line.split(',')
                    target[1][name_value[0]] = int(name_value[1])
    def save(self):
        """構築した辞書をファイルに保存
        """
        targets = [
            ('dat/dic/defs/word.def', self.word),
            ('dat/dic/defs/wordbasic.def', self.word_base),
            ('dat/dic/defs/pos.def', self.pos),
            ('dat/dic/defs/netag.def', self.netag),
            ('dat/dic/defs/case.def', self.case),
            ('dat/dic/defs/connparticle.def', self.connparticle),
            ('dat/dic/defs/conj.def', self.conj),
            ('dat/dic/defs/semroles.def', self.semrole),
        ]
        print('saving files')
        for target in targets:
            print(target)
            with open(target[0], 'w', encoding='utf-8') as file:
                print('length:'+str(len(target[1])))
                for (key, value) in target[1].items():
                    file.write(key+','+str(value)+'\n')
                file.close()
    def load_from_corpus(self, loader):
        """辞書データをコーパスから構築
        """
        print('loading dic name')
        for doc in loader.load_as_iter():
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
                    if chunk.particle is not None and chunk.particle.attr1 in {'係助詞', '副助詞'}:
                        self.connparticle.add_value(chunk.particle.surface)
    def load_from_yaml(self, yamlfile):
        with open(yamlfile) as file:
            result = yaml.load(file)
        for verbs in result['dict']:
            for frame in verbs['frame']:
                for inst in frame['instance']:
                    for case in inst['cases']:
                        self.semrole.add_value(case['semrole'])

def main():
    pass
if __name__ == "__main__":
    main()