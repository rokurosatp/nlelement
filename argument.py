"""述語項、共参照、意味役割の項オブジェクト
"""
from . import nlelement

class PredicateArgument:
    def __init__(self, *args):
        self.ana_sid = args[0]
        self.ana_tid = args[1]
        self.ant_sid = args[2]
        self.ant_tid = args[3]
        self.case = args[4]
        self.label = args[5]
        self.probable =  args[6]
    def to_tuple(self):
        """タプルに変換
        """
        return (
            self.ana_sid, self.ana_tid,
            self.ant_sid, self.ant_tid, self.case,
            self.label, self.probable
        )
    def get_repr(self, doc):
        return '{0} -{1:4}-> {2}: '.format(
            doc.refer(self.ana_ref()).get_surface(), self.case, doc.refer(self.ant_ref()).get_surface()
        ) + '{0}|{1}'.format(self.label, self.probable)
    def ana_ref(self):
        return nlelement.TokenReference(self.ana_sid, self.ana_tid)
    def ant_ref(self):
        return nlelement.TokenReference(self.ant_sid, self.ant_tid)

class CoreferenceArgument:
    def __init__(self, *args):
        self.ana_sid = args[0]
        self.ana_tid = args[1]
        self.ant_sid = args[2]
        self.ant_tid = args[3]
        self.label = args[4]
        self.probable =  args[5]
    def to_tuple(self):
        """タプルに変換
        """
        return (
            self.ana_sid, self.ana_tid,
            self.ant_sid, self.ant_tid,
            self.label, self.probable
        )
    def get_repr(self, doc):
        return '{0} ------> {1}: '.format(
            doc.refer(self.ana_ref()).get_surface(), doc.refer(self.ant_ref()).get_surface()
        ) + '{0}|{1}'.format(self.label, self.probable)
    def ana_ref(self):
        return nlelement.TokenReference(self.ana_sid, self.ana_tid)
    def ant_ref(self):
        return nlelement.TokenReference(self.ant_sid, self.ant_tid)
