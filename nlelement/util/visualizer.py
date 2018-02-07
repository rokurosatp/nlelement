import sys
import os
import io
from pathlib import Path
from .. import nlelement

pyplot_imported = False
try:
    import matplotlib.pyplot as plt
    pyplot_imported = True
except ImportError:
    pyplot_imported = False
pydot_imported = False
mpimg_imported = False
try:
    import matplotlib.image as mpimg
    mpimg_imported = True
except ImportError:
    mpimg_imported = False
pydot_imported = False
try:
    import pydot_ng as pydot
    pydot_imported = True
except ImportError:
    pydot_imported = False

NLELEMENT_VISUALIZER_FONT_NAME = "Yu Gothic UI"
if "USERPROFILE" not in os.environ:
    NLELEMENT_VISUALIZER_FONT_NAME = "Takao Gothic"
    

def plot_graph(graph, block=False):
    try:
        png_str = graph.create_png(prog="dot")
    except pydot.InvocationException:
        print(graph.to_string(), file=sys.stderr)
        raise
    sio = io.BytesIO()
    sio.write(png_str)
    sio.seek(0)
    img = mpimg.imread(sio)
    # plot the image
    imgplot = plt.imshow(img, aspect='equal')
    plt.show(block=block)

def save_graph(graph, filepath):
    if isinstance(filepath, Path):
        filepath_str = str(filepath)
    else:
        filepath_str = filepath
    graph.write_svg(filepath_str)

def to_graph(element):
    """nlelementの特定の要素(Document, Chunk)をpydotのグラフに変換
    """
    if isinstance(element, nlelement.Sentence):
        return sentence_to_graph(element)
    elif isinstance(element, nlelement.Document):
        return document_to_graph(element)
    raise ValueError("cannot viisualize {} object".format(type(element)))

def sentence_to_graph(sentence: nlelement.Sentence):
    global NLELEMENT_VISUALIZER_FONT_NAME
    graph = pydot.Dot()
    graph.set("charset", "UTF-8")
    graph.set_node_defaults(fontname=NLELEMENT_VISUALIZER_FONT_NAME, fontsize=32)
    graph.set_edge_defaults(fontname=NLELEMENT_VISUALIZER_FONT_NAME, fontsize=12)
    
    for chk in sentence.chunks:
        n = pydot.Node("ch_{}".format(chk.cid), label=chk.get_surface())
        #n.set("fontname", NLELEMENT_VISUALIZER_FONT_NAME)
        graph.add_node(n)
    for chk in sentence.chunks:
        if chk.link: 
            graph.add_edge(pydot.Edge("ch_{}".format(chk.cid), "ch_{}".format(chk.link.cid)))
    return graph

def __get_node_id__(ref):
    if isinstance(ref, nlelement.TokenReference):
        return "tk_{}".format(ref.to_tuple())
    elif isinstance(ref, nlelement.ChunkReference):
        return "ch_{}".format(ref.to_tuple())
    raise ValueError("not reference")

def find_edge(graph, src_node_name, dest_node_name):
    edge = []
    #dest_nodes = graph.get_node("\"{}\"".format(src_node_name))
    #src_nodes = graph.get_node("\"{}\"".format(dest_node_name))
    #dest_nodes = graph.get_node('"'+src_node_name+'"')
    #src_nodes = graph.get_node('"'+dest_node_name+'"')
    #print(dest_nodes, src_nodes)
    #if dest_nodes and src_nodes:
    edge = graph.get_edge('"'+src_node_name+'"', dst='"'+dest_node_name+'"')
    #print(graph.obj_dict["edges"])
    #print(edge)
    return edge

def __add_label__(edge, label):
    item = edge.get("label")
    prefix = ""
    if item:
        edge.set_label("{}-{}".format(item, label))
    else:
        edge.set_label("{}".format(label))
    return edge

def document_to_graph(document: nlelement.Document):
    global NLELEMENT_VISUALIZER_FONT_NAME
    graph = pydot.Dot()
    graph.set("charset", "UTF-8")
    graph.set_node_defaults(fontname=NLELEMENT_VISUALIZER_FONT_NAME, fontsize=32)
    graph.set_edge_defaults(fontname=NLELEMENT_VISUALIZER_FONT_NAME, fontsize=12)
    for sentence in document.sentences:
        for chk in sentence.chunks:
            n = pydot.Node(__get_node_id__(nlelement.make_reference(chk)), label=chk.get_surface())
            #n.set("fontname", NLELEMENT_VISUALIZER_FONT_NAME)
            graph.add_node(n)
        for chk in sentence.chunks:
            if chk.link: 
                e = pydot.Edge(
                    __get_node_id__(nlelement.make_reference(chk)),
                    __get_node_id__(nlelement.make_reference(chk.link)), weight=10
                )
                graph.add_edge(e)
            for tok in chk.tokens:
                for case, coref in tok.coreference_link.items():
                    ant_chk_ref = document.chunkref_from_tokenref(coref.antecedent_ref)
                    if ant_chk_ref:
                        ant_node_id = __get_node_id__(ant_chk_ref)
                        ana_node_id = __get_node_id__(nlelement.make_reference(chk))
                        edges = find_edge(graph, ant_node_id, ana_node_id)
                        if not edges:
                            edge = pydot.Edge(ant_node_id, ana_node_id, weight=0.1, style="dashed")
                            graph.add_edge(edge)
                        else:
                            edge = edges[0]
                        __add_label__(edge, case)
                if hasattr(tok, "semroles"):
                    for semrole, semarg in tok.semroles.items():
                        ant_chk_ref = document.chunkref_from_tokenref(semarg)
                        if ant_chk_ref:
                            ant_node_id = __get_node_id__(ant_chk_ref)
                            ana_node_id = __get_node_id__(nlelement.make_reference(chk))
                            edges = find_edge(graph, ant_node_id, ana_node_id)
                            if not edges:
                                edge = pydot.Edge(ant_node_id, ana_node_id, style="dashed")
                                graph.add_edge(edge)
                            else:
                                edge = edges[0]
                            __add_label__(edge, semrole)
                if hasattr(tok, "semrole"):
                    for semrole, semargs in tok.semrole.items():
                        for semarg in filter(lambda a: a.probable > 0.5, semargs):
                            ant_chk_ref = document.chunkref_from_tokenref(semarg.ant_ref())
                            if ant_chk_ref:
                                ant_node_id = __get_node_id__(ant_chk_ref)
                                ana_node_id = __get_node_id__(nlelement.make_reference(chk))
                                edge = pydot.Edge(ant_node_id, ana_node_id, weight=0.01, style="dotted", color="red")
                                graph.add_edge(edge)
                                __add_label__(edge, semrole)
                if hasattr(tok, "predicate_term"):
                    for case, args in tok.predicate_term.items():
                        for arg in filter(lambda a: a.label == 1.0, args):
                            ant_chk_ref = document.chunkref_from_tokenref(arg.ant_ref())
                            #print(ant_chk_ref)
                            if ant_chk_ref:
                                ant_node_id = __get_node_id__(ant_chk_ref)
                                ana_node_id = __get_node_id__(nlelement.make_reference(chk))
                                edge = pydot.Edge(ant_node_id, ana_node_id, weight=0.01, style="dotted", color="red")
                                graph.add_edge(edge)
                                __add_label__(edge, case)
                if hasattr(tok, "coreference"):
                    for arg in filter(lambda a: a.label == 1.0, tok.coreference):
                        ant_chk_ref = document.chunkref_from_tokenref(arg.ant_ref())
                        #print(ant_chk_ref)
                        if ant_chk_ref:
                            ant_node_id = __get_node_id__(ant_chk_ref)
                            ana_node_id = __get_node_id__(nlelement.make_reference(chk))
                            edge = pydot.Edge(ant_node_id, ana_node_id, weight=0.01, style="dotted", color="blue")
                            graph.add_edge(edge)
                            __add_label__(edge, "coref")

                
    return graph

if __name__ == "__main__":
    from test import testsamplemaker
    samples = testsamplemaker.NlElementSampleMaker()
    plot_graph(to_graph(samples.sample1()), block=True)