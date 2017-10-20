import sqlite3
import os
import gc
from . import myprogress
from . import nlelement
from . import loadercommon

class DatabaseLoader:
    def __init__(self, filename):
        self.connector = sqlite3.connect(filename)
        self.chunkid_contains_list = dict()
        self.chunkid_localize_table = dict()
        #self.tokenid_localize_table = dict()
        self.seeking_sid = -1
        self.file = None
    def __del__(self):
        if self.connector:
            self.connector.close()
            self.connector = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connector:
            self.connector.close()
            self.connector = None
    def update_views(self):
        """ビューを作り直す
        """
        cursor = self.connector.cursor()
        with open('../corpus-extraction/UpdateView.sql') as file:
            result = cursor.executescript(
                '\n'.join(file.readlines())
            )
        self.connector.commit()
        cursor.close()
    def create_tables(self):
        """初期化時にテーブルを作成
        """
        cursor = self.connector.cursor()
        result = cursor.executescript(
            """
            CREATE TABLE Documents(ID INTEGER PRIMARY KEY, NAME TEXT UNIQUE);
            CREATE TABLE Sentences(
                ID INTEGER PRIMARY KEY, DOCUMENT_ID INTEGER, SID INTEGER
            );
            CREATE TABLE Chunks(
                ID INTEGER PRIMARY KEY, DOCUMENT_ID INTEGER, SENTENCE_ID INTEGER,
                CID INTEGER, LINK INTEGER, HEAD INTEGER, FUNC INTEGER
            );
            CREATE TABLE Chunk_Tags(CHUNK INTEGER, NAME TEXT, VALUE TEXT);
            CREATE TABLE Tokens(
                ID INTEGER PRIMARY KEY, DOCUMENT_ID INTEGER, SENTENCE_ID INTEGER, CHUNK_ID INTEGER,
                TID INTEGER, SURFACE TEXT, BASE TEXT, READ TEXT, PART TEXT, ATTR1 TEXT, ATTR2 TEXT,
                CONJ_TYPE TEXT, CONJ_FORM TEXT, NAMED_ENTITY TEXT, PAS_TYPE TEXT
            );
            CREATE TABLE Pas_Annotated(ID INTEGER PRIMARY_KEY, NAME TEXT UNIQUE);
            CREATE TABLE Pth_Annotated(ID INTEGER PRIMARY_KEY, NAME TEXT UNIQUE);
            CREATE TABLE Pth_Annotated_Sent(ID INTEGER PRIMARY_KEY);

            CREATE TABLE Token_Tags(Token INTEGER, NAME TEXT, VALUE TEXT);
            CREATE TABLE Coreference(ANAPHORA INTEGER UNIQUE, LINKTYPE TEXT, ANTECEDENT INTEGER);
            CREATE TABLE PredicateTerm(PREDICATE INTEGER, CASEPT TEXT, LINKTYPE TEXT, ANTECEDENT INTEGER);
            CREATE TABLE SemanticRole(PREDICATE INTEGER, SEMROLE TEXT, ANTECEDENT INTEGER);

            CREATE INDEX Sentence_Idx ON Sentences(DOCUMENT_ID);
            CREATE INDEX Chunk_Idx ON Chunks(SENTENCE_ID);
            CREATE INDEX Chunk_Doc_Idx ON Chunks(DOCUMENT_ID);
            CREATE INDEX Token_Idx ON Tokens(CHUNK_ID);
            CREATE INDEX Token_Sent_Idx ON Tokens(SENTENCE_ID);
            CREATE INDEX Token_Doc_Idx ON Tokens(SENTENCE_ID);
            CREATE INDEX Chunk_Tag_Idx ON Chunk_Tags(CHUNK);
            CREATE INDEX Token_Tag_Idx ON Token_Tags(TOKEN);
            CREATE INDEX Coreference_Idx ON Coreference(ANAPHORA);
            CREATE INDEX Predicate_Idx ON PredicateTerm(Predicate);
            CREATE INDEX Semrole_Idx ON Semanticrole(Predicate);
            CREATE INDEX DOCNAME_IDX ON Documents(Name);
            """
        )
        self.connector.commit()
        cursor.close()
    def clear(self):
        """初期化のために既存のテーブルの内容を消去
        """
        cursor = self.connector.cursor()
        result = cursor.executescript(
            """
            DELETE FROM Documents;
            DELETE FROM Sentences;
            DELETE FROM Chunks;
            DELETE FROM Chunk_Tags;
            DELETE FROM Tokens;
            DELETE FROM Pas_Annotated;
            DELETE FROM Pth_Annotated;
            DELETE FROM Pth_Annotated_Sent;
            DELETE FROM Token_Tags;
            DELETE FROM Coreference;
            DELETE FROM PredicateTerm;
            DELETE FROM SemanticRole;
            """
        )
        self.connector.commit()
        cursor.close()
    def save_in_additional(self, documents):
        """nlelementオブジェクトを追加保存する
        """
        if isinstance(documents, list):
            if documents:
                if isinstance(documents[0], nlelement.Document):
                    file_path = os.path.expanduser('~/Dropbox/Logs/db_coref.log')
                    self.file = open(file_path, 'a')
                    cursor = self.connector.cursor()
                    self.add_documents(cursor, documents, show_progress=False)
                    cursor.close()
                    self.file.close()
                else:
                    raise TypeError(
                        "Type of documents needs list<Document> not list<{0}>".format(
                            type(documents[0]).__name__
                        ))
        else:
            raise TypeError("Type of documents needs list<Document> not {0}".format(
                type(documents).__name__
            ))
        
    def save(self, documents):
        """nlelementオブジェクトをダンプする
        """
        if isinstance(documents, list):
            if documents:
                if isinstance(documents[0], nlelement.Document):
                    file_path = os.path.expanduser('~/Dropbox/Logs/db_coref.log')
                    self.file = open(file_path, 'w')
                    cursor = self.connector.cursor()
                    self.add_documents(cursor, documents)
                    self.connector.commit()
                    cursor.close()
                    self.file.close()
                else:
                    raise TypeError(
                        "Type of documents needs list<Document> not list<{0}>".format(
                            type(documents[0]).__name__
                        ))
        else:
            raise TypeError("Type of documents needs list<Document> not {0}".format(
                type(documents).__name__
            ))
    def add_annotation(self, cursor, doc, did):
        if hasattr(doc, 'pas_annotated') and getattr(doc, 'pas_annotated'):
            cursor.execute(
                "INSERT INTO Pas_Annotated VALUES (?, ?)",
                (did, doc.name)
            )
        if hasattr(doc, 'pt_annotated') and getattr(doc, 'pt_annotated'):
            cursor.execute(
                "INSERT INTO Pth_Annotated VALUES (?, ?)",
                (did, doc.name)
            )
            for sentence in doc.sentences:
                if hasattr(sentence, 'pt_annotated') and getattr(sentence, 'pt_annotated'):
                    cursor.execute(
                        "SELECT id FROM Sentences WHERE sid = ? and document_id = ?",
                        (sentence.sid, did)
                    )
                    sentence_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO Pth_Annotated_Sent VALUES (?)",
                        (sentence_id,)
                    )

    def add_documents(self, cursor: sqlite3.Cursor, documents, show_progress=True):
        did_globaldid_map = dict()
        subcursor = self.connector.cursor()
        
        length = len(documents)
        if show_progress:
            progress = myprogress.make_progress(max_value=length)
        for i, doc in enumerate(documents):
            cursor.execute(
                "INSERT INTO DOCUMENTS(NAME) VALUES (?)", (doc.name,)
            )
            cursor.execute("SELECT ID FROM DOCUMENTS WHERE ROWID IN (SELECT last_insert_rowid())")
            did_globaldid_map[i] = cursor.fetchone()[0]
            #self.add_annotation(subcursor, doc, did_globaldid_map[i])
            if show_progress:
                progress.update(i+1)
        if show_progress:
            progress.finish()
        subcursor.close()
        
        if show_progress:
            progress = myprogress.make_progress(max_value=length)
        for i, doc in enumerate(documents):
            self.add_sentences(cursor, doc, did_globaldid_map[i])
            self.add_coreference_links(cursor, doc, document_id=did_globaldid_map[i])
            self.add_semroles(cursor, doc, document_id=did_globaldid_map[i])
            if show_progress:
                progress.update(i+1)
        if show_progress:
            progress.finish()
        if show_progress:
            progress = myprogress.make_progress(max_value=length)
        for i, doc in enumerate(documents):
            self.add_annotation(cursor, doc, did_globaldid_map[i])
            if show_progress:
                progress.update(i+1)
        if show_progress:
            progress.finish()
        did_globaldid_map = None
    def add_sentences(self, cursor: sqlite3.Cursor, document: nlelement.Document, doc_id):
        sid_globalsid_map = dict()
        for sent in document.sentences:
            cursor.execute(
                "INSERT INTO SENTENCES(DOCUMENT_ID, SID) VALUES (?, ?)"
            , (doc_id, sent.sid))
            cursor.execute("SELECT ID FROM SENTENCES WHERE ROWID IN (SELECT last_insert_rowid())")
            sid_globalsid_map[sent.sid] = cursor.fetchone()[0]
        for sent in document.sentences:
            if len(sent.chunks) == 0 and len(sent.tokens) != 0:
                self.add_tokens_without_chunks(cursor, sent, sid_globalsid_map[sent.sid], doc_id)
            else:
                self.add_chunks(cursor, sent, sid_globalsid_map[sent.sid], doc_id)
        sid_globalsid_map = None
    
    def add_chunks(self, cursor: sqlite3.Cursor, sentence: nlelement.Sentence, sent_id, doc_id):
        cid_globalcid_map = dict()
        def redefine(func_position, head_position):
            """func_positionをNAIST式に振りなおす(実際使うんだから無駄か（笑）)
            """
            return func_position if func_position > 0 else head_position
        for chunk in sentence.chunks:
            cursor.execute(
                "INSERT INTO CHUNKS(DOCUMENT_ID, SENTENCE_ID, CID, LINK, HEAD, FUNC) VALUES (?, ?, ?, 0, ?, ?)", (
                    doc_id, sent_id, chunk.cid, chunk.head_position,
                    redefine(chunk.func_position, chunk.head_position)
                )
            )
            cursor.execute("SELECT ID FROM CHUNKS WHERE ROWID IN (SELECT last_insert_rowid())")
            cid_globalcid_map[chunk.cid] = cursor.fetchone()[0]
        for chunk in sentence.chunks:
            self.add_tokens(cursor, chunk, doc_id, sent_id, cid_globalcid_map[chunk.cid])
            cursor.execute("UPDATE CHUNKS SET LINK=? WHERE ID=?",
                (cid_globalcid_map[chunk.link_id] if chunk.link_id in range(0, len(sentence.tokens)) else -1, cid_globalcid_map[chunk.cid])
            )
        cid_globalcid_map = None
    def add_tokens_without_chunks(self, cursor: sqlite3.Cursor, sentence: nlelement.Sentence, sent_id, doc_id):
        class MyGenerator:
            def __init__(self, sentence, doc_id, sent_id):
                self.sentence = sentence
                self.doc_id, self.sent_id, self.chunk_id = doc_id, sent_id, 0
                self.tok_iter = iter(sentence.tokens)
            def __iter__(self):
                return self
            def __next__(self):
                tok = next(self.tok_iter)
                return (doc_id, sent_id, tok.tid, tok.surface, tok.basic_surface, tok.read, tok.part, tok.attr1, tok.attr2, tok.conj_type, tok.conj_form, tok.named_entity)
        cursor.executemany("""
            INSERT INTO TOKENS(
                DOCUMENT_ID, SENTENCE_ID, CHUNK_ID, TID, SURFACE, BASE, READ, PART, ATTR1, ATTR2, CONJ_TYPE, CONJ_FORM, NAMED_ENTITY
            ) VALUES (
                ?, ?, -1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """, MyGenerator(sentence, doc_id, sent_id))
    def __refer_chunk_id__(self, cursor, doc_id, reference):
        if not isinstance(reference, nlelement.ChunkReference):
            if reference is None:
                return -1
            else:
                raise TypeError(
                    'reference must be ChunkReference , not {0}'.format(type(reference).__name__)
                )
        cursor.execute("""
            SELECT id FROM CHUNKS WHERE SENTENCE_ID IN (
                    SELECT ID FROM SENTENCES WHERE DOCUMENT_ID = ? and SID = ?
                ) and CID = ?;
            """, (doc_id, reference.sid, reference.cid))
        result = cursor.fetchone()
        if not result:
            return -2 # NOTE: 見つからないパターンについての仕様がないので-2をセットする設定で
        return result[0]
    def __refer_token_id__(self, cursor, doc_id, reference):
        if not isinstance(reference, nlelement.TokenReference):
            if reference is None:
                return -1
            else:
                raise TypeError(
                    'reference must be TokenReference , not {0}'.format(type(reference).__name__)
                )
        cursor.execute("""
            SELECT id FROM TOKENS WHERE SENTENCE_ID IN (
                    SELECT ID FROM SENTENCES WHERE DOCUMENT_ID = ? and SID = ?
                ) and TID = ?;
            """, (doc_id, reference.sid, reference.tid))
        result = cursor.fetchone()
        if not result:
            return -2 # NOTE: 見つからないパターンについての仕様がないので-2をセットする設定で
        return result[0]
    def add_semroles(self, cursor: sqlite3.Cursor, document: nlelement.Document, document_id=None):
        if document_id is None:
            cursor.execute("SELECT ID FROM DOCUMENTS WHERE name = ?", (document.name,))
            doc_id = cursor.fetchone()[0]
        else:
            doc_id = document_id
        for token in nlelement.tokens(document):
            if hasattr(token, 'semroles'):
                for semrole, semtok_ref in token.semroles.items():
                    pred_id = self.__refer_token_id__(cursor, doc_id, nlelement.make_reference(token))
                    semtok_id = self.__refer_token_id__(cursor, doc_id, semtok_ref)
                    if pred_id and pred_id >= 0:
                        cursor.execute('INSERT INTO SemanticRole(PREDICATE, SEMROLE, ANTECEDENT) VALUES (?, ?, ?);', (pred_id, semrole, semtok_id))
                    else:
                        print('ana: {0}, ant: {1}'.format(pred_id, semtok_id), file=self.file)
    def add_coreference_links(self, cursor: sqlite3.Cursor, document: nlelement.Document, document_id=None):
        """共参照関係の追加
        """
        import sys
        if document_id is None:
            cursor.execute("SELECT ID FROM DOCUMENTS WHERE name = ?", (document.name,))
            doc_id = cursor.fetchone()[0]
        else:
            doc_id = document_id
        case_set = {'ga', 'o', 'ni'}
        for token in nlelement.tokens(document):
            for name, coref in token.coreference_link.items():
                if name == 'coref':
                    anaphora_id = self.__refer_token_id__(cursor, doc_id, coref.anaphora_ref)
                    antecedent_id = self.__refer_token_id__(cursor, doc_id, coref.antecedent_ref)
                    if anaphora_id and anaphora_id >= 0:
                        try:
                            cursor.execute(
                                "INSERT INTO Coreference(ANAPHORA, LINKTYPE, ANTECEDENT) VALUES (?, ?, ?)",
                                (anaphora_id, coref.link_type, antecedent_id)
                            )
                        except sqlite3.IntegrityError as e:
                            print('ana: {0}, ant: {1}'.format(anaphora_id, antecedent_id), file=self.file)
                            print(e, file=self.file)
                    else:
                        print('ana: {0}, ant: {1}'.format(anaphora_id, antecedent_id), file=self.file)
                elif name in case_set:
                    case = name# case_normalize_table[name]
                    anaphora_id = self.__refer_token_id__(cursor, doc_id, coref.anaphora_ref)
                    antecedent_id = self.__refer_token_id__(cursor, doc_id, coref.antecedent_ref)
                    if anaphora_id and anaphora_id >= 0:
                        try:
                            cursor.execute(
                                "INSERT INTO PredicateTerm(PREDICATE, CASEPT, LINKTYPE, ANTECEDENT) VALUES (?, ?, ?, ?)",
                                (anaphora_id, case, coref.link_type, antecedent_id)
                            )
                        except sqlite3.IntegrityError as e:
                            print('ana: {0}, ant: {1}'.format(anaphora_id, antecedent_id), file=self.file)
                            print(e)
                    else:
                        print('ana: {0}, ant: {1}'.format(anaphora_id, antecedent_id), file=self.file)

    def add_tokens(self, cursor: sqlite3.Cursor, chunk: nlelement.Chunk, doc_id, sent_id, chunk_id):
        """データベースに単語を追加する
        """
        class MyGenerator:
            def __init__(self, chunk, doc_id, sent_id, chunk_id):
                self.chunk = chunk
                self.doc_id, self.sent_id, self.chunk_id = doc_id, sent_id, chunk_id
                self.tok_iter = iter(chunk.tokens)
            def __iter__(self):
                return self
            def __next__(self):
                tok = next(self.tok_iter)
                return (
                        doc_id, sent_id, chunk_id, tok.tid, tok.surface, tok.basic_surface, tok.read, tok.part, 
                        tok.attr1, tok.attr2, tok.conj_type, tok.conj_form, tok.named_entity, tok.pas_type
                    )
        default_tok_attrs = dir(nlelement.Token())
        for tok in chunk.tokens:
            cursor.execute("""
                INSERT INTO TOKENS(
                    DOCUMENT_ID, SENTENCE_ID, CHUNK_ID, TID, SURFACE, BASE, READ, PART, ATTR1, ATTR2, CONJ_TYPE, CONJ_FORM, NAMED_ENTITY, PAS_TYPE
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """, (doc_id, sent_id, chunk_id, tok.tid, tok.surface, tok.basic_surface, tok.read, tok.part, 
                        tok.attr1, tok.attr2, tok.conj_type, tok.conj_form, tok.named_entity, tok.pas_type))
            
            attr_names = list(filter(lambda d: d not in default_tok_attrs and isinstance(getattr(tok, d), (str, float, int, bool)), dir(tok)))
            if attr_names:
                cursor.execute("SELECT ID FROM TOKENS WHERE rowid in (SELECT last_insert_rowid())")
                token_id = cursor.fetchone()[0]
                for name in attr_names:
                    value = getattr(tok, name)
                    cursor.execute("INSERT INTO Token_Tags(token, name, value) VALUES (?, ?, ?)", (token_id, name, value))

        
    def load(self):
        result = self.load_documents()
        return result

    def get_names(self):
        cursor = self.connector.cursor()
        cursor.execute("SELECT NAME FROM DOCUMENTS")
        while True:
            result = cursor.fetchone()
            if result is None:
                break
            yield result[0]
        cursor.close()
        
    def get_document_count(self):
        cursor = self.connector.cursor()
        cursor.execute("SELECT COUNT(*) FROM DOCUMENTS")
        length =  cursor.fetchone()[0]
        cursor.close()
        return length
    def load_annotated(self, doc_id, document):
        cursor = self.connector.cursor()
        cursor.execute("SELECT COUNT(*) FROM Pas_Annotated WHERE ID = ?", (doc_id,))
        if cursor.fetchone()[0] != 0:
            setattr(document, 'pas_annotated', True)
        cursor.execute("SELECT COUNT(*) FROM Pth_Annotated WHERE ID = ?", (doc_id,))
        if cursor.fetchone()[0] != 0:
            setattr(document, 'pt_annotated', True)
            cursor.execute(
                "SELECT sid from sentences where id in (SELECT id FROM Pth_Annotated_Sent) and document_id = ?",
                (doc_id,))
            # , はタイポではない。タプルをアンパックするために必要
            for sid, in cursor.fetchall():
                sent = document.refer_sentence(sid)
                setattr(sent, "pt_annotated", True)
        cursor.close()
    def load_as_iter(self):
        cursor = self.connector.cursor()
        cursor.execute("SELECT * FROM DOCUMENTS")
        for doc_id, name in cursor.fetchall():
            yield self.load_document(doc_id, name)
        cursor.close()
        gc.collect()

    def load_documents(self):
        documents = []
        cursor = self.connector.cursor()
        length = self.get_document_count()
        progress = myprogress.make_progress(max_value=length)
        count = 0
        cursor.execute("SELECT * FROM DOCUMENTS")
        for doc_id, name in cursor.fetchall():
            documents.append(
                self.load_document(doc_id, name)
            )
            count += 1
            progress.update(count)

        progress.finish()
        cursor.close()
        return documents
    def load_one_sample(self, name = None):
        """ドキュメントを１つだけロード
        """
        import random
        documents = []
        cursor = self.connector.cursor()

        cursor.execute("SELECT COUNT(*) FROM DOCUMENTS")
        length = cursor.fetchone()[0]
        if name is None:
            load_id = random.randrange(1, stop=length+1)
            cursor.execute("SELECT * FROM DOCUMENTS WHERE ID = ?", (load_id,))
        else:
            cursor.execute("SELECT * FROM DOCUMENTS WHERE NAME = ?", (name,))
        for doc_id, name in cursor.fetchall():
            documents.append(
                self.load_document(doc_id, name)
            )
        cursor.close()
        return documents
    def load_document(self, doc_id, name):
        doc = nlelement.Document()
        doc.name = name
        try:
            doc.sentences = self.load_sencences(doc_id)
        except IndexError:
            print(doc.name)
            raise
        self.load_coreference_links(doc, doc_id)
        self.load_semroles(doc, doc_id)
        self.load_annotated(doc_id, doc)
        return doc
    def load_sencences(self, doc_id):
        cursor = self.connector.cursor()
        cursor.execute("SELECT * FROM SENTENCES WHERE DOCUMENT_ID = ? ORDER BY SID", (doc_id,))
        sentences = []
        self.chunkid_localize_table = dict()
        for sentence_id, doc_id, self.seeking_sid in cursor.fetchall():
            self.chunkid_contains_list = dict()
            sentence = nlelement.Sentence()
            sentence.sid = self.seeking_sid
            sentence.tokens = self.load_tokens(sentence_id, sentence)
            sentence.chunks = self.load_chunks(sentence_id, sentence)
            sentences.append(sentence)
            self.chunkid_contains_list = None
        cursor.close()
        self.chunkid_localize_table = None
        return sentences
    def load_chunks(self, sentence_id, sentence):
        cursor = self.connector.cursor()
        cursor.execute("SELECT * FROM CHUNKS WHERE SENTENCE_ID = ? ORDER BY CID", (sentence_id,))
        chunks = []
        links = []
        cid_localize_table = dict()
        for chunk_id, doc_id, sent_id, cid, link_chunk_id, head_pos, func_pos in cursor.fetchall():
            chunk = nlelement.Chunk()
            chunk.sid = sentence.sid
            chunk.cid = cid
            chunk.head_position = head_pos
            chunk.func_position = func_pos
            chunks.append(chunk)
            if chunk_id in self.chunkid_contains_list:
                for tid in self.chunkid_contains_list[chunk_id]:
                    try:
                        chunk.tokens.append(sentence.tokens[tid])
                    except IndexError:
                        print(self.chunkid_contains_list)
                        print(sentence.get_surface())
                        raise
            self.__token_post_process__(chunk)
            chunk.set_token_info()
            cid_localize_table[chunk_id] = cid
            self.chunkid_localize_table[chunk_id] = (self.seeking_sid, cid)
            links.append(link_chunk_id)
        cursor.close()
        del_list = []
        for chunk, link_chunk_id in zip(chunks, links):
            if not chunk.tokens:
                del_list.append(chunk)
            if link_chunk_id >= 0:
                chunk.link_id = cid_localize_table[link_chunk_id]
                chunk.link = chunks[chunk.link_id]
                chunks[chunk.link_id].reverse_link_ids.append(chunk.cid)
                chunks[chunk.link_id].reverse_links.append(chunk)
        for chunk in del_list:
            if len(chunks) > chunk.cid + 1:
                chunks[chunk.cid + 1].reverse_link_ids.extend(chunk.reverse_link_ids)
                chunks[chunk.cid + 1].reverse_links.extend(chunk.reverse_links)
                for dtr in chunk.reverse_links:
                    dtr.link = chunks[chunk.cid + 1]
            else:
                for dtr in chunk.reverse_links:
                    dtr.link_id = -1
                    dtr.link = None
            for i in range(chunk.cid + 1, len(chunks)):
                chunks[i].cid -= 1
            for i in range(len(chunks)):
                if chunk.link_id > chunk.cid:
                    chunk.link_id -= 1
                for j in range(len(chunks[i].reverse_link_ids)):
                    if chunks[i].reverse_link_ids[j] > chunk.cid:
                        chunks[i].reverse_link_ids[j] -= 1
            chunks.remove(chunk)
        del_list = None
        cid_localize_table = None
        #print(sentence.get_surface())
        return chunks
    def get_token_ref(self, token_id):
        cursor = self.connector.cursor()
        cursor.execute("""SELECT sent.SID, token.TID From SENTENCES as sent, TOKENS as token
            where sent.id = token.sentence_id and token.id = ?
        """, (token_id,))
        return cursor.fetchone()
    def load_semroles(self, document: nlelement.Document, doc_id):
        cursor = self.connector.cursor()
        cursor.execute("""
            SELECT * FROM SemanticRole WHERE PREDICATE IN (
                SELECT ID FROM TOKENS WHERE DOCUMENT_ID = ?
            )
            """, (doc_id,))
        for pred_token_id, semrole, ant_token_id in cursor.fetchall():
            pred_stid = self.get_token_ref(pred_token_id)
            ant_stid = self.get_token_ref(ant_token_id)
            #pred_stid = self.tokenid_localize_table[pred_token_id] \
            #    if pred_token_id in self.tokenid_localize_table else None
            #ant_stid = self.tokenid_localize_table[ant_token_id] \
            #    if ant_token_id in self.tokenid_localize_table else None
            if pred_stid is not None:
                pred_ref = nlelement.TokenReference(*pred_stid)
                pred = document.refer(pred_ref)
                ant_ref= nlelement.TokenReference(*ant_stid) if ant_stid is not None else None
                if ant_ref:
                    if not pred:
                        print('error pred is none({0}, {1})'.format(pred_ref.sid, pred_ref.tid))
                    else:
                        if not hasattr(pred, 'semroles'):
                            setattr(pred, 'semroles', dict())
                        pred.semroles[semrole] = ant_ref
    def load_coreference_links(self, document: nlelement.Document, doc_id):
        cursor = self.connector.cursor()
        cursor.execute("""
            SELECT * FROM Coreference WHERE ANAPHORA IN (
                SELECT ID FROM TOKENS WHERE SENTENCE_ID IN (SELECT ID FROM SENTENCES WHERE DOCUMENT_ID = ?)
            )
            """, (doc_id,))
        for ana_token_id, link_type, ant_token_id in cursor.fetchall():
            ana_stid = self.get_token_ref(ana_token_id)
            #self.tokenid_localize_table[ana_token_id] \
            #    if ana_token_id in self.tokenid_localize_table else None
            ant_stid = self.get_token_ref(ant_token_id)
            #self.tokenid_localize_table[ant_token_id] \
            #    if ant_token_id in self.tokenid_localize_table else None
            if ana_stid is not None:
                ana_ref = nlelement.TokenReference(*ana_stid)
                anaphora = document.refer(ana_ref)
                ant_ref = nlelement.TokenReference(*ant_stid) if ant_stid is not None else None
                if ant_stid and all(map(lambda x: x>=0, ant_stid)):
                    ant_surface = document.refer(ant_ref).surface 
                else:
                    ant_surface = ""
                entry = nlelement.CoreferenceEntry(
                    ana_ref, ant_ref, -1, -1, ant_surface
                    )
                entry.link_type = link_type
                anaphora.coreference_link['coref'] = entry
        cursor.execute("""
        SELECT * FROM PredicateTerm WHERE Predicate IN (
            SELECT ID FROM TOKENS WHERE SENTENCE_ID IN (SELECT ID FROM SENTENCES WHERE DOCUMENT_ID = ?)
        )
        """, (doc_id,))
        #case_renormalize_table = {
        #    "ga": "ガ",
        #    "wo": "ヲ",
        #    "ni": "二",
        #}
        for ana_token_id, case, link_type, ant_token_id in cursor.fetchall():
            ana_stid = self.get_token_ref(ana_token_id)
            #self.tokenid_localize_table[ana_token_id] \
            #    if ana_token_id in self.tokenid_localize_table else None
            ant_stid = self.get_token_ref(ant_token_id)
            #self.tokenid_localize_table[ant_token_id] \
            #    if ant_token_id in self.tokenid_localize_table else None
            if ana_stid is not None:
                ana_ref = nlelement.TokenReference(*ana_stid)
                anaphora = document.refer(ana_ref)
                ant_ref = nlelement.TokenReference(*ant_stid) if ant_stid is not None else None
                case_kana = case#case_renormalize_table[case]
                if ant_stid and all(map(lambda x: x>=0, ant_stid)):
                    ant_surface = document.refer(ant_ref).surface 
                else:
                    ant_surface = ""
                entry = nlelement.CoreferenceEntry(
                    ana_ref, ant_ref, -1, -1, ant_surface
                    )
                entry.link_type = link_type
                anaphora.coreference_link[case_kana] = entry
        cursor.close()
    def load_tokens(self, sentence_id, sentence):
        cursor = self.connector.cursor()
        attr_cursor = self.connector.cursor()
        tokens = []
        cursor.execute("SELECT * FROM TOKENS WHERE SENTENCE_ID = ? ORDER BY TID", (sentence_id,))
        for token_id, document_id, sentence_id, chunk_id, tid, surface, base, read, part, attr1, attr2, conj_type, conj_form, named_entity, pas_type in cursor.fetchall():
            token = nlelement.Token()
            token.sid = sentence.sid
            token.tid = tid
            token.surface, token.basic_surface = surface, base
            token.read = read
            token.part = part
            token.part_id = loadercommon.part_id[part] if part in loadercommon.part_id else 10
            token.attr1 = attr1
            token.attr2 = attr2
            token.pos = '-'.join((part, attr1, attr2))
            token.conj_type, token.conj_form = conj_type, conj_form
            token.named_entity = named_entity
            token.pas_type = pas_type
            if token.part == '名詞':
                token.sahen = (token.attr1 == 'サ変')
                token.normalnoun = (token.attr1 == '一般')
                token.adjectivenoun = (token.attr1 == '副詞可能')
            attr_cursor.execute("SELECT NAME, VALUE FROM Token_Tags WHERE token = ?", (token_id,))
            for name, value in attr_cursor.fetchall():
                setattr(token, name, value)
            if chunk_id not in self.chunkid_contains_list:
                self.chunkid_contains_list[chunk_id] = list()
            self.chunkid_contains_list[chunk_id].append(tid)
            #self.tokenid_localize_table[token_id] = (self.seeking_sid, tid)
            tokens.append(token)
        attr_cursor.close()
        cursor.close()
        return tokens
    def __token_post_process__(self, chunk):
        """トークンをチャンクに追加した後に追加したトークンに応じて属性値を変更する
        内容語の場合は機能表現の位置を+1するとか
        「」が入る場合、begin_paren end_paren emphasisの値が変更される
        """
        for token_pos, token in enumerate(chunk.tokens):
            if token_pos <= chunk.head_position + 1:
                token.is_content = True
            if token_pos < chunk.func_position:
                token.is_indep = True
            if token.surface == '「':
                chunk.begin_paren = True
                chunk.emphasis = True
            elif token.surface == '」':
                chunk.end_paren = True
                chunk.emphasis = True

class DatabaseWriter:
    def __init__(self, db_filename, append=False):
        self.loader = DatabaseLoader(db_filename)
        cursor = self.loader.connector.cursor()
        cursor.execute("SELECT count(*) from SQLITE_MASTER WHERE TYPE='table'")
        if cursor.fetchone()[0] == 0:
            loader.create_tables()
        elif not append:
            self.loader.clear()
        loader.update_views()
        cursor.close()
        
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.loader.connector.commit()
        self.loader.__exit__(exc_type, exc_value, traceback)

    def add_documents(self, documents):
        self.loader.save_in_additional(documents)


def load(dbname):
    with DatabaseLoader(dbname) as loader:
        result = loader.load()
    return result
    
def loadone(dbname, name=None):
    with DatabaseLoader(dbname) as loader:
        if name is None:
            result = loader.load_one_sample()
        else:
            result = loader.load_one_sample(name)
    return result

def save(dbname, documents):
    loader = DatabaseLoader(dbname)
    cursor = loader.connector.cursor()
    cursor.execute("SELECT count(*) from SQLITE_MASTER WHERE TYPE='table'")
    if cursor.fetchone()[0] == 0:
        loader.create_tables()
        loader.update_views()
    cursor.close()
    loader.save(documents)
