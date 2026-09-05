"""Download the configured sentence-transformer once for offline RAG use."""
import os

from sentence_transformers import SentenceTransformer


name = os.environ.get("STATSKILL_EMBED_MODEL", "all-MiniLM-L6-v2")
print(f"Caching embedding model: {name}", flush=True)
SentenceTransformer(name)
print("Embedding model is ready.", flush=True)
