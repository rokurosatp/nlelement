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
