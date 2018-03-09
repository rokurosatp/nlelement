DROP VIEW IF EXISTS TokenView;
DROP VIEW IF EXISTS ChunkView;
DROP VIEW IF EXISTS SentenceView;
DROP VIEW IF EXISTS LinkView;
DROP VIEW IF EXISTS CoreferenceView;
DROP VIEW IF EXISTS PredicateView;
DROP VIEW IF EXISTS SemroleView;

CREATE TABLE IF NOT EXISTS A_Dummy_Table(ID INTEGER PRIMARY KEY, INFO TEXT);

CREATE VIEW TokenView as
    SELECT token.id, token.surface, doc.name as doc_name, sentence.sid, chunks.cid, token.tid
    from tokens as token, chunks, sentences as sentence, documents as doc
    WHERE token.chunk_id = chunks.id and token.sentence_id = sentence.id and token.document_id = doc.id;
CREATE VIEW ChunkView as
    SELECT chunks.*, group_concat(tokens.surface, "") as surface from tokens, chunks
    where chunks.id = tokens.chunk_id group by chunks.id;
CREATE VIEW SentenceView as
    SELECT documents.name, sentences.id, sentences.sid, group_concat(tokens.surface, "") as surface
    from tokens, sentences, documents
    where documents.id = sentences.document_id and sentences.id = tokens.SENTENCE_ID group by sentences.id;
CREATE VIEW LinkView as
    SELECT chunk.id, chunk.surface, link.surface from chunkview as chunk, chunkview as link
    WHERE chunk.link = link.id;
CREATE VIEW CoreferenceView as
    SELECT token.id as id, token.surface as anaphora, link.surface as antecedent, doc.name as doc_name, ana_sent.surface as ana_sent_surf, ant_sent.surface as ant_sent_surf
    from tokens as token, tokens as link, coreference as coref, SENTENCEVIEW as ana_sent, SENTENCEVIEW as ant_sent, DOCUMENTS as doc
    WHERE token.id = coref.anaphora and link.id = coref.antecedent and token.sentence_id = ana_sent.id and link.sentence_id = ant_sent.id and token.document_id = doc.id;
CREATE VIEW PredicateView as
    SELECT token.id as id, token.surface as predicate, link.surface as antecedent, pred.casept as casept, doc.name as doc_name, pred_s.surface as pred_sent, arg_s.surface as arg_sent
    from tokens as token, tokens as link, PredicateTerm as pred, SENTENCEVIEW as pred_s, SENTENCEVIEW as arg_s, DOCUMENTS as doc
    WHERE token.id = pred.predicate and link.id = pred.antecedent and token.sentence_id = pred_s.id and link.sentence_id = arg_s.id and token.document_id = doc.id;
CREATE VIEW SemroleView as
    SELECT sm.predicate as id, p.surface as predicate, sm.semrole , a.surface as antecedent, doc.name as doc_name, s.sid
    FROM SEMANTICROLE as sm, TOKENS as p, TOKENS as a, SENTENCES as s, DOCUMENTS as doc
    WHERE sm.predicate = p.id and sm.antecedent = a.id and p.sentence_id = s.id and p.document_id = doc.id;
