"""
Build a simple RAG pipeline using LangChain prompt templates.
This is intentionally small so you can adapt to LangChain versions.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document
from typing import List
from rag.embedder import llm
from rag.retriever import get_retriever

SYSTEM = (
    "You are a helpful RAG assistant. Answer using only the provided context.\n"
    "If you cannot answer from the context, say you don't know. Keep answers concise and cite sources."
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "Question: {question}\n\nContext:\n{context}\n\nAnswer:")
])

def _format_docs(docs: List[Document]) -> str:
    lines = []
    for i, d in enumerate(docs):
        meta = d.metadata or {}
        src = meta.get("orig_filename", meta.get("source", "unknown"))
        preview = d.page_content[:500].replace("\n", " ")
        lines.append(f"[{src}:{i}] {preview}")
    return "\n\n".join(lines)

def build_rag_chain(k: int = 4):
    retriever = get_retriever(k=k)
    # We'll create a simple function-like chain: retrieve -> format -> prompt -> llm
    # For compatibility across LangChain versions we will use a small callable structure
    def chain_invoke(question: str):
        docs = retriever.get_relevant_documents(question) if hasattr(retriever, "get_relevant_documents") else []
        context = _format_docs(docs)
        prompt_text = PROMPT.format_prompt(question=question, context=context).to_string()
        # The llm object may be LangChain wrapper; attempt to call in common patterns
        try:
            # If llm is ChatGoogleGenerativeAI or similar
            out = llm.generate([{"content": prompt_text}])
            # extract text safely
            if hasattr(out, "generations"):
                gens = out.generations
                if gens and gens[0]:
                    return getattr(gens[0][0], "text", str(gens[0][0]))
            return str(out)
        except Exception:
            try:
                # Try calling as callable
                return str(llm(prompt_text))
            except Exception as e:
                return f"Error: LLM invocation failed ({e})"
    # Return an object with .invoke to be compatible with app usage
    class Chain:
        def invoke(self, question):
            return chain_invoke(question)
    return Chain()
