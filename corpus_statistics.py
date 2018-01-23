"""コーパスデータの統計を取る
"""
import texttable
import matplotlib
import json
import re
import pathlib
from nlelement import nlelement, database


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

class CoreferenceStatTable:
    def __init__(self):
        self.in_head_noun = 0
        self.not_noun_coref = 0
        self.pronoun = 0
        self.coreference = 0
        self.head_anaphora = 0
        self.head_antecedent = 0
        self.entities = 0

    def count(self, entity_dict, doc, sent, chunk, tok):
        
        if chunk.head_token() == tok and tok.part in ["名詞", "代名詞"]:
            self.in_head_noun += 1
        if tok.part == "代名詞":    
            #if re.match(r"(これ|それ|あれ|ここ|そこ|あそこ|彼|彼女|あいつ|こいつ|そいつ|)", tok.basic_surface):
            self.pronoun += 1

        if "coref" in tok.coreference_link:
            self.coreference += 1
            if tok.part != "名詞":
                self.not_noun_coref += 1
            ana_ref = nlelement.make_reference(tok)
            ant_ref = tok.coreference_link["coref"].antecedent_ref
            if doc.refer(doc.chunkref_from_tokenref(ana_ref)).head_token().tid == tok.tid:
                self.head_anaphora += 1
            if doc.refer(doc.chunkref_from_tokenref(ant_ref)).head_token().tid == ant_ref.tid:
                self.head_antecedent += 1
            if ant_ref not in entity_dict:
                entity_dict[ant_ref] = 0
                entity_dict[nlelement.make_reference(tok)] = 0
                self.entities += 1
            else:
                entity_dict[nlelement.make_reference(tok)] = 0

    def count_doc(self, doc):
        entity_dict = {}
        for sent in doc.sentences:
            for chunk in sent.chunks:
                for tok in chunk.tokens:
                    self.count(entity_dict, doc, sent, chunk, tok)

    def from_dict(self, dic:dict):
        if "in_head_noun" in dic:
            self.in_head_noun = dic["in_head_noun"]
        if "not_noun_coref" in dic:
            self.not_noun_coref = dic["not_noun_coref"]
        if "pronoun" in dic:
            self.pronoun = dic["pronoun"]
        if "coreference" in dic:
            self.coreference = dic["coreference"]
        if "head_anaphora" in dic:
            self.head_anaphora = dic["head_anaphora"]
        if "head_antecedent" in dic:
            self.head_antecedent = dic["head_antecedent"]
        if "entities" in dic:
            self.entities = dic["entities"]
        
    def to_dict(self):
        return {
            "pronoun": self.pronoun,
            "not_noun_coref": self.not_noun_coref,
            "in_head_noun": self.in_head_noun,
            "coreference": self.coreference,
            "head_anaphora": self.head_anaphora,
            "head_antecedent": self.head_antecedent,
            "entities": self.entities
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
            "pronoun",
            "not_noun_coref",
            "in_head_noun",
            "coreference",
            "head_anaphora",
            "head_antecedent",
            "entities"
        ]:
            self.__show_item__(name)


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
            elif ant_chunk == chunk.link:
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

def plot_coref_stat():
    stats = CoreferenceStatTable()
    stats.load('dat/log/coref_stats.json')
    stats.show()

def plot_pas_stat():
    stats = PredicateStatTable()
    stats.load('dat/log/pas_stats.json')
    stats.show()

def plot_syncha_stat():
    stats = PredicateStatTable()
    stats.load('dat/log/syncha_stats.json')
    stats.show()

def count_coref_stat_of(corpus, outfilename):
    stats = CoreferenceStatTable()
    with database.DatabaseLoader(corpus) as loader:
        for doc in loader.load_as_iter():
            stats.count_doc(doc)
        stats.save(outfilename)
        stats.show()

def count_pred_stat_of(corpus, outfilename):
    stats = PredicateStatTable()
    with database.DatabaseLoader(corpus) as loader:
        for doc in loader.load_as_iter():
            stats.count_doc(doc)
        stats.save(outfilename)
        stats.show()

def count_syncha_stat_of(corpus, outfilename):
    import subprocess
    import sys
    from nlelement import cabocha_extended
    with database.DatabaseLoader(corpus) as loader:
        process = subprocess.Popen(['./predicate/external/syncha-0.3.1.1/syncha', '-I', '2', '-O', '2', '-k'], stdin=subprocess.PIPE)
        for doc in loader.load_as_iter():
            input_str = cabocha_extended.dump_doc(doc, from_label=True)
            process.stdin.write(input_str.encode('utf-8'))
        process.stdin.close()
        process.wait()

def count_stat_of(corpus, outfilepath):
    count_coref_stat_of(corpus, str(pathlib.Path(outfilepath)/"coref_stat.json"))
    count_pred_stat_of(corpus, str(pathlib.Path(outfilepath)/"pred_stat.json"))
    count_syncha_stat_of(corpus, str(pathlib.Path(outfilepath)/"syncha_stat.json"))
