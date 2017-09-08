"""コーパスデータの統計を取る
"""
import texttable
import matplotlib
import json
from nlelement import nlelement, bccwj, database


class ArgStatElem:
    def __init__(self):
        self.ga = 0
        self.o = 0
        self.ni = 0

    def count(self, case):
        if case == "ga":
            self.ga += 1
        if case == "o":
            self.o += 1
        if case == "ni":
            self.ni += 1
    
    def total(self):
        return self.ga + self.o + self.ni

    def to_dict(self):
        return {"ga": self.ga, "o": self.o, "ni": self.ni}

    def from_dict(self, dic: dict):
        if "ga" in dic:
            self.ga = int(dic["ga"])
        if "o" in dic:
            self.o = int(dic["o"])
        if "ni" in dic:
            self.ni = int(dic["ni"])

class PredicateStatTable:
    def __init__(self):
        self.predicates = 0
        self.in_head_pred = 0
        self.arguments = ArgStatElem()
        self.dep_arguments = ArgStatElem()
        self.adnom_arguments = ArgStatElem()
        self.zero_intra = ArgStatElem()
        self.zero_inter = ArgStatElem()
        self.in_head_args = ArgStatElem()
        self.invalid_args = ArgStatElem()
        self.valid_args = ArgStatElem()

    def count(self, doc, sent, chunk, tok):
        self.predicates += 1
        if chunk.head_token() == tok:
            self.in_head_pred += 1
        for key, arg in tok.coreference_link.items():
            self.arguments.count(key)
            if not arg.antecedent_ref:
                self.invalid_args.count(key)
                continue
            ant_tok = doc.refer(arg.antecedent_ref)
            ant_sent = doc.sentences[arg.antecedent_ref.sid]
            ant_chunk = ant_sent.chunk_from_token(ant_tok)
            if not ant_chunk:
                self.invalid_args.count(key)
                continue
            self.valid_args.count(key)
            if ant_chunk.head_token() == ant_tok:
                self.in_head_args.count(key)
            if ant_sent.sid != sent.sid:
                self.zero_inter.count(key)
            elif ant_chunk in chunk.reverse_links:
                self.dep_arguments.count(key)
            elif ant_chunk.particle and "係助詞" in ant_chunk.particle.pos:
                self.adnom_arguments.count(key)
            else:
                self.zero_intra.count(key)        

    def count_doc(self, doc):
        for sent in doc.sentences:
            for chunk in sent.chunks:
                for tok in chunk.tokens:
                    if tok.pas_type == "pred":
                        self.count(doc, sent, chunk, tok)
    
    def from_dict(self, dic:dict):
        if "predicates" in dic:
            self.predicates = dic["predicates"]
        if "in_head_pred" in dic:
            self.in_head_pred = dic["in_head_pred"]
        if "arguments" in dic:
            self.arguments.from_dict(dic["arguments"])
        if "dep_arguments" in dic:
            self.dep_arguments.from_dict(dic["dep_arguments"])
        if "adnom_arguments" in dic:
            self.adnom_arguments.from_dict(dic["adnom_arguments"])
        if "zero_intra" in dic:
            self.zero_intra.from_dict(dic["zero_intra"])
        if "zero_inter" in dic:
            self.zero_inter.from_dict(dic["zero_inter"])
        if "in_head_args" in dic:
            self.in_head_args.from_dict(dic["in_head_args"])
        if "invalid_args" in dic:
            self.invalid_args.from_dict(dic["invalid_args"])
        if "valid_args" in dic:
            self.valid_args.from_dict(dic["valid_args"])
    
    def to_dict(self):
        return {
            "predicates": self.predicates,
            "in_head_pred": self.in_head_pred,
            "arguments": self.arguments.to_dict(),
            "dep_arguments": self.dep_arguments.to_dict(),
            "adnom_arguments": self.adnom_arguments.to_dict(),
            "zero_intra": self.zero_intra.to_dict(),
            "zero_inter": self.zero_inter.to_dict(),
            "in_head_args": self.in_head_args.to_dict(),
            "invalid_args": self.invalid_args.to_dict(),
            "valid_args": self.valid_args.to_dict()
        }          

    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f)

    def load(self, filename):
        with open(filename) as f:
            self.from_dict(json.load(f))

    def __show_item__(self, name):
        arg = getattr(self, name)
        if isinstance(arg, int):
            print(name, ":", arg)
        else:
            print(name, ":", arg.total())

    def show(self):
        for name in [
            "predicates",
            "in_head_pred",
            "arguments",
            "dep_arguments",
            "adnom_arguments",
            "zero_intra",
            "zero_inter",
            "in_head_args",
            "invalid_args",
            "valid_args"
        ]:
            self.__show_item__(name)

    def plot(self, filename=None):
        pass

def count_pas_stat():
    import re
    stats = PredicateStatTable()
    db = database.DatabaseLoader(bccwj.get_corpus_path())
    for doc in db.load_as_iter():
        if re.match(r"PB.*", doc.name):
            stats.count_doc(doc)
    stats.save('dat/log/pas_stats.json')
    stats.show()

def count_syncha_stat():
    import subprocess
    import resource
    import sys
    from nlelement import cabocha_extended
    stats = PredicateStatTable()
    with open('./dat/log/corpus_statistics_err.log', 'w') as f:
        process = subprocess.Popen(['./predicate/external/syncha-0.3.1.1/syncha', '-I', '2', '-O', '2', '-k'], stdin=subprocess.PIPE, stderr=f)
        db = database.DatabaseLoader(bccwj.get_corpus_path())
        for doc in db.load_as_iter():
            input_str = cabocha_extended.dump_doc(doc, from_label=True)
            process.stdin.write(input_str.encode('utf-8'))
            mem_size = resource.getusage(resource.ru_idrss)
            print('{}'.format(mem_size), file=sys.stderr)
        process.wait()

def plot_pas_stat():
    stats = PredicateStatTable()
    stats.load('dat/log/pas_stats.json')
    stats.show()

def plot_syncha_stat():
    stats = PredicateStatTable()
    stats.load('dat/log/syncha_stats.json')
    stats.show()
