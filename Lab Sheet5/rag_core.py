# Lab 5 - shared RAG logic (LangChain + Chroma + Ollama)
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma

DB_DIR, DATA_DIR = "chroma_db", "data"
emb = OllamaEmbeddings(model="qwen3-embedding:0.6b")
db = Chroma(persist_directory=DB_DIR, embedding_function=emb)
llm = ChatOllama(model="llama3.2:3b", temperature=0)
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

def ingest_pdf(path):
    docs = PyMuPDFLoader(path).load()
    for d in docs:
        d.metadata["source"] = os.path.basename(path)
    chunks = splitter.split_documents(docs)
    db.add_documents(chunks)
    return len(chunks)

def ingest_folder(folder=DATA_DIR):
    return {f: ingest_pdf(os.path.join(folder, f))
            for f in os.listdir(folder) if f.lower().endswith(".pdf")}

def list_sources():
    metas = db.get()["metadatas"]
    return sorted({m.get("source") for m in metas if m and m.get("source")})

def retrieve(q, k=5, source=None):
    if source:
        return db.similarity_search(q, k=k, filter={"source": source})
    return db.similarity_search(q, k=k)

def search_text(q, k=4):
    return "\n\n".join(f"Source: {d.metadata.get('source')}, Page: {d.metadata.get('page', 0)+1}\n{d.page_content}"
                       for d in retrieve(q, k)) or "No documents found."

PROMPT = """You are a university assistant. Answer ONLY using the context below.
If the answer is not in the context, say you could not find it.

Context:
{context}

Question: {q}
Answer:"""

def answer(q, source=None):
    docs = retrieve(q, source=source)
    ctx = "\n\n".join(d.page_content for d in docs)
    resp = llm.invoke(PROMPT.format(context=ctx, q=q)).content
    srcs = sorted({f"{d.metadata.get('source')} p.{d.metadata.get('page', 0)+1}" for d in docs})
    return resp, srcs

if __name__ == "__main__":      # python rag_core.py  -> ingest everything in ./data
    os.makedirs(DATA_DIR, exist_ok=True)
    print(ingest_folder())
