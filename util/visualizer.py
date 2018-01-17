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
    import pydot_ng
    pydot_imported = True
except ImportError:
    pydot_imported = False

def plot_graph(graph, block=False):
    
    png_str = graph.create_png(prog="dot")
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
    graph.save_png(filepath_str)

def to_graph(element):
    if isinstance(element, nlelement.Sentence):
        return sentence_to_graph(element)
    raise ValueError("cannot viisualize {} object".format(type(element)))

def sentence_to_graph(sentence: nlelement.Sentence):
    graph = pydot_ng.Dot()
    for chk in sentence.chunks:
         graph.add_node(pydot_ng.Node("ch_{}".format(chk.cid), label=chk.get_surface()))
    for chk in sentence.chunks:
        if chk.link: 
            graph.add_edge(pydot_ng.Edge("ch_{}".format(chk.cid), "ch_{}".format(chk.link.cid)))
    return graph

if __name__ == "__main__":
    from test import testsamplemaker
    samples = testsamplemaker.NlElementSampleMaker()
    plot_graph(to_graph(samples.sample1().sentences[0]), block=True)