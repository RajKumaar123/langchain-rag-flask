"""
Embeddings + LLM wrapper using LangChain's Google GenAI integrations.
If you use a different provider (OpenAI), swap this module accordingly.
"""
from config import GOOGLE_API_KEY, EMBEDDING_MODEL, GENERATION_MODEL, TEMPERATURE, MAX_TOKENS

# langchain-google-genai provides GoogleGenerativeAIEmbeddings and ChatGoogleGenerativeAI
# Fallback to placeholders if import fails (so IDE won't break)
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    embeddings = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model=EMBEDDING_MODEL)
    llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model=GENERATION_MODEL,
                                 temperature=TEMPERATURE, max_output_tokens=MAX_TOKENS)
except Exception:
    # Minimal placeholders: raise helpful error later when used
    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *a, **k):
            raise RuntimeError("Missing langchain_google_genai. Install package or set provider properly.")
        def bind(self, *a, **k):
            return self
    embeddings = _Dummy()
    llm = _Dummy()
