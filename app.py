# app.py (complete, production-like RAG assistant with image support)
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# LangChain / Gemini
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from google.api_core import exceptions as g_exceptions

# Local modules
from config import UPLOAD_DIR, TOP_K, TEMPERATURE, MAX_TOKENS
from rag.utils import load_and_split_with_images
from rag.retriever import add_to_index, query_index, list_indexed_documents

# ---------------- ENV & API key ----------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Missing API key: set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env")

# ---------------- Flask setup ----------------
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- Models ----------------
primary_model_name = "gemini-1.5-pro"
fallback_model_name = "gemini-1.5-flash"

chat_model = ChatGoogleGenerativeAI(
    google_api_key=API_KEY,
    model=primary_model_name,
    temperature=TEMPERATURE,
    max_output_tokens=MAX_TOKENS,
)
embeddings_model = GoogleGenerativeAIEmbeddings(
    google_api_key=API_KEY,
    model="models/embedding-001",
)

# ---------------- Prompt & Memory ----------------
prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a knowledgeable, friendly assistant that answers ONLY using the supplied context.

Style & behavior:
- Ground every statement in the provided context; do not invent facts or external URLs.
- If figures/images are relevant, reference them by number (e.g., “Figure 5”) and, when possible, mention the page.
- Prefer short paragraphs, clear bullets, and numbered steps for procedures.
- Use a calm, book-like tone aimed at helping a colleague quickly understand.
- If the context doesn’t contain the answer, say so briefly and suggest what to look for.
- Keep answers concise but complete; end with a one-line recap.

OUTPUT STYLE (always return Markdown):
- Start with an appropriate heading for the user’s question (e.g., **Overview**, **Answer**, **Summary**, or the topic).
- Use short paragraphs, clear **bold** for key terms, and bullet/numbered lists where helpful.
- If steps or a procedure are asked, provide a numbered list under **Steps**.
- If tradeoffs/comparisons are relevant, add a **Comparison** section.
- If equations, definitions, or examples help, add **Notes/Examples**.
- If figures/images are referenced in context, cite them by number (e.g., **Figure 5**) and page if available.
- End with a brief **TL;DR** one-liner.

RULES:
- Ground every statement in the given context; do not invent facts or external links.
- If the context is insufficient, clearly say so and suggest what’s missing.
- If the user specifies length (e.g., “in 200 words”), respect it.

When the user asks for a “summary” or mentions “figure/image/diagram/chart”:
- Provide a compact overview first (what/why).
- Then list 3–6 key points as bullets.
- If figures are mentioned in the context, call them out by number (e.g., “see Figure 16”) and give a one-line caption.
- Avoid repeating the same figure multiple times.

Formatting:
- Return Markdown/HTML-friendly text (bold, lists, line breaks).
- Avoid overly long code blocks or tables unless necessary.

Your goal is clarity, comfort, and correctness, grounded strictly in the retrieved context.
"""),
    ("human", "{input}")
])

# memory store per session
_store: dict[str, InMemoryChatMessageHistory] = {}
def get_session_history(session_id: str):
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]

conversation = RunnableWithMessageHistory(
    prompt | chat_model,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

# Serve uploaded/extracted images
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---------------- APIs ----------------
@app.post("/api/upload")
def api_upload():
    """Upload and embed documents into Chroma."""
    if "files" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    files = request.files.getlist("files")
    results = []
    for f in files:
        fname = secure_filename(f.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        f.save(path)

        # Extract chunks (text + images metadata)
        chunks = load_and_split_with_images(path)
        status = add_to_index(chunks, embeddings_model, filepath=path)  # smart dedupe/update
        results.append({"file": fname, "chunks": len(chunks), "status": status})

    return jsonify({"status": "ok", "results": results})

@app.get("/api/indexed")
def api_indexed():
    """List already indexed documents."""
    docs = list_indexed_documents()
    return jsonify({"status": "ok", "documents": docs})

@app.post("/api/chat")
def api_chat():
    """Chat endpoint with memory + fallback model + image return."""
    data = request.get_json(force=True) or {}
    question = (data.get("question") or data.get("message") or "").strip()
    if not question:
        return jsonify({"status": "error", "message": "Empty question"}), 400
    session_id = data.get("session_id", "default")

    # Retrieve docs
    retrieved = query_index(question, embeddings_model, top_k=TOP_K)
    context = "\n".join([d["content"] for d in retrieved])

    # Try pro model → fallback to flash on quota error
    try:
        resp = conversation.invoke(
            {"input": f"Context:\n{context}\n\nQuestion:\n{question}"},
            config={"configurable": {"session_id": session_id}},
        )
    except g_exceptions.ResourceExhausted:
        flash_model = ChatGoogleGenerativeAI(
            google_api_key=API_KEY,
            model=fallback_model_name,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
        )
        alt_conv = RunnableWithMessageHistory(
            prompt | flash_model,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        resp = alt_conv.invoke(
            {"input": f"Context:\n{context}\n\nQuestion:\n{question}"},
            config={"configurable": {"session_id": session_id}},
        )

    # Collect images metadata
    images = []
    for d in retrieved:
        meta = d.get("metadata", {})
        if "image_path" in meta:
            images.append({
                "url": f"/uploads/{meta['image_path']}",
                "figure_no": meta.get("figure_no"),
                "page": meta.get("page"),
                "caption": meta.get("caption", "")
            })

    return jsonify({
        "status": "ok",
        "answer": getattr(resp, "content", str(resp)),
        "sources": retrieved,
        "images": images
    })

@app.get("/api/debug/peek")
def debug_peek():
    """Peek into first 5 docs in Chroma with metadata (debugging)."""
    from rag.retriever import collection
    data = collection.get(limit=5)
    return jsonify({
        "count": len(data.get("ids", [])),
        "sample": [
            {"doc": d, "meta": m}
            for d, m in zip(data.get("documents", []), data.get("metadatas", []))
        ]
    })

# ---------------- Main ----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
