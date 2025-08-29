# rag/retriever.py
import os, uuid, hashlib
import chromadb
from chromadb.config import Settings

# Use a persistent on-disk DB so embeddings survive app restarts
CHROMA_DIR = "chroma_db"
os.makedirs(CHROMA_DIR, exist_ok=True)

# ✅ Persistent client (NOT the in-memory Client)
try:
    # Chroma >= 0.5
    client = chromadb.PersistentClient(path=CHROMA_DIR)
except AttributeError:
    # Older Chroma versions still accept Settings with persist_directory
    client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))

# Create or get the same collection across restarts
collection = client.get_or_create_collection(name="documents")

def compute_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def add_to_index(chunks, embeddings_model, filepath=None):
    """
    Add (text, metadata) pairs into ChromaDB with deduplication & update handling.
    Returns: "indexed", "skipped", or "updated"
    """
    filename = os.path.basename(filepath) if filepath else "unknown"
    file_hash = compute_file_hash(filepath) if filepath else None

    # If exact same file (by hash) exists → skip
    if file_hash:
        existing = collection.get(where={"file_hash": file_hash})
        if existing and existing.get("ids"):
            print(f"⚡ Skipping {filename} → already indexed.")
            return "skipped"

        # If same filename but different hash → replace old
        old = collection.get(where={"orig_filename": filename})
        if old and old.get("ids"):
            collection.delete(ids=old["ids"])
            status = "updated"
        else:
            status = "indexed"
    else:
        status = "indexed"

    texts, metas = zip(*chunks) if chunks else ([], [])
    if not texts:
        print(f"ℹ {filename}: no chunks extracted.")
        return status

    ids = [f"id_{uuid.uuid4().hex}" for _ in texts]
    embeds = embeddings_model.embed_documents(list(texts))

    new_metas = []
    for m in metas:
        m = dict(m) if isinstance(m, dict) else {}
        m.update({"file_hash": file_hash, "orig_filename": filename})
        new_metas.append(m)

    collection.add(
        documents=list(texts),
        embeddings=embeds,
        metadatas=new_metas,
        ids=ids
    )
    print(f"✅ {status.capitalize()} {filename} with {len(texts)} chunks.")
    return status

def query_index(question, embeddings_model, top_k=3):
    """Retrieve top_k chunks from ChromaDB"""
    q_embed = embeddings_model.embed_query(question)
    results = collection.query(query_embeddings=[q_embed], n_results=top_k)

    docs = []
    if results and results.get("documents"):
        for i, txt in enumerate(results["documents"][0]):
            docs.append({
                "content": txt,
                "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
            })
    return docs

def list_indexed_documents():
    """List unique filenames currently in the persistent index (survives restarts)"""
    data = collection.get(include=["metadatas"])
    seen = {}
    for m in data.get("metadatas", []):
        name = m.get("orig_filename")
        if name:
            seen[name] = True
    return sorted(seen.keys())
