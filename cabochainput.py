from . import nlelement

def doc_to_format(document: nlelement.Document):
    """DocumentオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    for sentence in document.sentences:
        fmt_text += sent_to_format(sentence)
    fmt_text += 'EOT\n'
def sent_to_format(sentence: nlelement.Sentence):
    """SentenceオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    for chunk in sentence.chunks:
        fmt_text += chunk_to_format(chunk)
        for token in chunk.tokens:
            fmt_text += token_to_format(token)
    fmt_text += 'EOS\n'
    return fmt_text
def chunk_to_format(chunk: nlelement.Chunk):
    """ChunkオブジェクトからCaboChaフォーマットを生成する
    """
    fmt_text = ''
    fmt_text += '* ' + '{0} {1}D '.format(chunk.cid, chunk.link_id)
    fmt_text += '{0}/{1}'.format(chunk.func_position, chunk.token_num)
    fmt_text += ' 0.000000\n'
    return fmt_text
def token_to_format(token: nlelement.Token):
    """TokenオブジェクトからCaboCha(ほぼMeCab)フォーマットを生成する
    """
    result = ''
    result += token.surface
    result += '\t'
    result += token.part + ','
    result += token.attr1 + ','
    result += token.attr2 + ','
    result += '*' + ','
    result += token.conj_form + ','
    result += token.conj_type + ','
    result += token.basic_surface + ','
    result += token.read + ','
    result += token.read + '\t'
    result += token.named_entity if token.named_entity != '' else '0'
    result += '\n'
    return result
        
