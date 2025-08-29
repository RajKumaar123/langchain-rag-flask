import os
from dotenv import load_dotenv

load_dotenv()

# API / Keys
# Accept either GOOGLE_API_KEY or GEMINI_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
assert GOOGLE_API_KEY, "GOOGLE_API_KEY or GEMINI_API_KEY must be set in .env"

# Models
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "models/gemini-1.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(BASE_DIR, "chroma_store"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))

# Chunking / Retrieval
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "4"))

# Inference controls
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", "32768"))
