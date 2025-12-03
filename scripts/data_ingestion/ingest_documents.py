"""
Ingest documents (legal, code, docs, etc.) into the RAG database.
- Extracts text, chunks, generates embeddings, and stores in DB.
- Supports PDF, HTML, TXT, and more.
- Uses LangChain for embedding and chunking.
"""
import os

import psycopg2
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredHTMLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

DB_URL = os.environ.get("RAG_DB_URL", "postgresql://user:pass@localhost:5432/opendiscourse")

EMBED_DIM = 1536

def connect_db():
    return psycopg2.connect(DB_URL)

def load_document(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)
    elif file_path.endswith(".html"):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError("Unsupported file type")
    return loader.load()

def chunk_and_embed(texts):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(texts)
    embedder = OpenAIEmbeddings()
    embeddings = embedder.embed_documents([chunk.page_content for chunk in chunks])
    return chunks, embeddings

def store_in_db(docs, embeddings):
    conn = connect_db()
    cur = conn.cursor()
    for doc, emb in zip(docs, embeddings):
        cur.execute(
            """
            INSERT INTO documents (title, content, source_url, doc_type, date, embedding, metadata)
            VALUES (%s, %s, %s, %s, now(), %s, %s)
            """,
            (doc.metadata.get('title', 'Untitled'), doc.page_content, doc.metadata.get('source_url'), doc.metadata.get('doc_type', 'text'), emb, doc.metadata)
        )
    conn.commit()
    cur.close()
    conn.close()

def ingest(file_path):
    docs = load_document(file_path)
    chunks, embeddings = chunk_and_embed(docs)
    store_in_db(chunks, embeddings)
    print(f"Ingested {len(chunks)} chunks from {file_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ingest_documents.py <file_path>")
        exit(1)
    ingest(sys.argv[1])
