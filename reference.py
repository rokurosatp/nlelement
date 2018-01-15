
class ChunkReference:
    def __init__(self, sid, cid):
        self.sid = sid
        self.cid = cid
    def to_tuple(self):
        return (self.sid, self.cid)
    def __bool__(self):
        return self.sid >= 0 or self.cid >= 0
    def __eq__(self, value):
        if value is None:
            return False
        return self.sid == value.sid and self.cid == value.cid
    def __lt__(self, value):
        return self.sid < value.sid or (self.sid == value.sid and self.cid < value.cid)
    def __hash__(self):
        return hash(self.to_tuple())
    def __repr__(self):
        return '<Ch:{0},{1}>'.format(self.sid, self.cid)

class TokenReference:
    def __init__(self, sid, tid):
        self.sid = sid
        self.tid = tid
    def to_tuple(self):
        return (self.sid, self.tid)
    def __bool__(self):
        return self.sid >= 0 or self.tid >= 0
    def __lt__(self, value):
        return self.sid < value.sid or (self.sid == value.sid and self.tid < value.tid)
    def __eq__(self, value):
        if value is None:
            return False
        return self.sid == value.sid and self.tid == value.tid
    def __hash__(self):
        return hash(self.to_tuple())
    def __repr__(self):
        return '<Tk:{0},{1}>'.format(self.sid, self.tid)

class ExoReference:
    """外界のシンボルの参照(未使用)
    """
    def __init__(self, name=None):
        if name is None:
            self.name = 'Unknown'
    def to_tuple(self):
        return (-2, -2)
    def __bool__(self):
        return False
    def __lt__(self, value):
        if isinstance(value, ExoReference):
            return self.name < value.name
        return True
    def __repr__(self):
        return '<Exo: {}>'.format(self.name)

