from . import reference

class Relation:
    def __init__(self):
        self.ana_ref = None
        self.ant_ref = None
        self.case = ""

    def get_scheme(self):
        if isinstance(self.ana_ref, reference.ChunkReference):
            if isinstance(self.ant_ref, reference.ChunkReference):
                return "chk_chk"
            elif isinstance(self.ant_ref, reference.TokenReference):
                return "tok_chk"
        elif isinstance(self.ana_ref, reference.TokenReference):
            if isinstance(self.ant_ref, reference.ChunkReference):
                return "chk_tok"
            elif isinstance(self.ant_ref, reference.TokenReference):
                return "tok_tok"
        raise ValueError("invalid reference type ana:{}-ant:{}".format(type(self.ana_ref), type(self.ant_ref)))

    def __eq__(self, right):
        return self.ana_ref == right.ana_ref and self.ant_ref == right.ant_ref and self.case == right.case

    def __lt__(self, right):
        return self.ana_ref < right.ana_ref or (self.ana_ref == right.ana_ref and self.ant_ref < right.ant_ref) or \
            (self.ana_ref == right.ana_ref and self.ana_ref == right.ana_ref and self.case < right.case)

    def __hash__(self):
        return hash((self.ana_ref, self.ana_ref, self.case))


    