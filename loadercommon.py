from . import nlelement


class IdGenerator:
    def __init__(self):
        self.id = -1
    def reset(self):
        self.id = -1
    def get(self):
        self.id += 1
        return self.id
class NlElementIds:
    def __init__(self):
        self.doc = IdGenerator()
        self.sent = IdGenerator()
        self.chunk = IdGenerator()
        self.tok = IdGenerator()

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