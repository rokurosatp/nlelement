import MeCab
from nlelement import nlelement

class MorphUnpacker:
    """素性タプルから形態素としての属性を取得するための変換器
    辞書ごとに異なる
    """
    def __init__(self):
        self.pos = ()
        self.conj_type = ()
        self.conj_form = ()
        self.basic_surface = ()
        self.basic_surface_normalizer = None
        self.unk_node_length = 6
        self.read = ()
        self.pron = ()

    def unpack(self, surface, feature):
        token = nlelement.Token()
        pos_tup = tuple(map(lambda i: feature[i], self.pos))
        token.surface = surface
        token.pos = "-".join(filter(lambda e: e and e != "*", pos_tup))
        token.part = pos_tup[0]
        token.attr1 = pos_tup[1] if len(pos_tup) > 1 else "*"
        token.attr2 = pos_tup[2] if len(pos_tup) > 2 else "*"
        if len(feature) == self.unk_node_length:
            token.conj_type = ""
            token.conj_form = ""
            token.basic_surface = token.surface
            token.read = ""
        else:
            token.conj_type = "-".join(map(lambda i: feature[i], self.conj_type))
            token.conj_form = "-".join(map(lambda i: feature[i], self.conj_form))
            token.basic_surface = "-".join(map(lambda i: feature[i], self.basic_surface))
            # Unidicの場合英語由来のカタカナ語に対してスペルを割り当てる機能がbasic_surfaceについてたりする
            # 辞書の検索時に邪魔になりそうなので消す
            if self.basic_surface_normalizer:
                token.basic_surface = self.basic_surface_normalizer(token.basic_surface)
            token.read = "-".join(map(lambda i: feature[i], self.read))
        return token

    @staticmethod
    def unidic():
        unpacker = MorphUnpacker()
        unpacker.pos = (0, 1, 2, 3)
        unpacker.conj_type = (4,)
        unpacker.conj_form = (5,)
        unpacker.read = (6,)
        unpacker.basic_surface = (7,)
        unpacker.basic_surface_normalizer = lambda e: e.split('-')[0]
        return unpacker

    @staticmethod
    def ipadic():
        unpacker = MorphUnpacker()
        unpacker.pos = (0, 1, 2, 3)
        unpacker.conj_type = (4,)
        unpacker.conj_form = (5,)
        unpacker.read = (7,)
        unpacker.basic_surface = (6,)
        return unpacker


class ConfigSets:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_option(self):
        option_map = {
            "dicdir": "-d",
            "rcfile": "-r",
            "outputform": "-O",
        }
        options = []
        for key, value in option_map.items():
            if hasattr(self, key):
                options.append((value, getattr(self, key)))
        return " ".join(map(lambda x:" ".join(x), options))

    @staticmethod
    def unidic():
        config = ConfigSets(dicdir="/var/lib/mecab/dic/unidic", pos_unpacker=MorphUnpacker.unidic())
        return config

    @staticmethod
    def ipadic():
        config = ConfigSets(dicdir="/usr/local/lib/mecab/dic/ipadic-utf8", pos_unpacker=MorphUnpacker.unidic())
        return config

class MeCabParser:
    def __init__(self, config=None):
        option = ""
        if config is None:
            option = ""
        else:
            option = config.to_option()
        self.option = option
        self.manalyzer = MeCab.Model(option)
        self.parser = self.manalyzer.createTagger()
        self.unpacker = config.pos_unpacker if hasattr(config, "pos_unpacker") else MorphUnpacker.ipadic()
    stat_dic = {
        MeCab.MECAB_BOS_NODE :'MECAB_BOS_NODE',
        MeCab.MECAB_EON_NODE: 'MECAB_EON_NODE',
        MeCab.MECAB_EOS_NODE: 'MECAB_EOS_NODE',
        MeCab.MECAB_NOR_NODE: 'MECAB_NOR_NODE',
        MeCab.MECAB_UNK_NODE: 'MECAB_UNK_NODE'
    }
    @staticmethod
    def iter_nor_node(bos_node):
        """MeCabの非終端ノードを列挙するジェネレータ
        """
        node = bos_node()
        while node:
            if node.stat == MeCab.MECAB_NOR_NODE or node.stat == MeCab.MECAB_UNK_NODE:
                yield node
            node = node.next

    def parse_sentence(self, raw_sentence, sid=0):
        lattice = self.manalyzer.createLattice()
        lattice.set_sentence(raw_sentence)
        sentence = nlelement.Sentence()
        sentence.sid = sid
        self.parser.parse(lattice)
        for node in MeCabParser.iter_nor_node(lattice.bos_node):
            token = self.unpacker.unpack(node.surface, node.feature.split(','))
            token.tid = len(sentence.tokens)
            token.sid = sentence.sid
            sentence.tokens.append(token)
        return sentence

    def parse(self, raw_document, delimiter=None):
        rawsent_iter = None
        if delimiter is None:
            rawsent_iter = raw_document.splitlines()
        elif isinstance(delimiter, str):
            rawsent_iter = raw_document.split(delimiter)
        document = nlelement.Document()
        for i, raw_sent in enumerate(rawsent_iter):
            document.sentences.append(self.parse_sentence(raw_sent, i))
        return document
