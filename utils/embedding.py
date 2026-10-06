from typing import List
import numpy as np
import streamlit as st
from model import Chunk

MODEL_NAME = 'all-MiniLM-L6-v2'
# The model only looks at its first ~256 word pieces; ~1000 characters covers that.
MAX_EMBED_CHARS = 1000
TOP_K = 20


@st.cache_resource(show_spinner="Loading the embedding model...")
def load_model():
    # Imported lazily: torch is slow to import and not needed to render most pages.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> List[float]:
    return load_model().encode(text[:MAX_EMBED_CHARS], normalize_embeddings=True).tolist()


def generate_embeddings(blocks: List[str], page_num: int) -> List[Chunk]:
    texts = [block for block in blocks if block.strip()]
    if not texts:
        return []
    vectors = load_model().encode([t[:MAX_EMBED_CHARS] for t in texts], normalize_embeddings=True, batch_size=32)
    return [
        Chunk(text=text, embedding=vector.tolist(), page=page_num, position=position)
        for position, (text, vector) in enumerate(zip(texts, vectors))
    ]


def rank_chunks(query_embedding: List[float], chunks: List[Chunk], top_k: int = TOP_K) -> List[Chunk]:
    """Return the `top_k` chunks most similar (cosine) to the query embedding."""
    if not chunks:
        return []
    matrix = np.asarray([chunk.embedding for chunk in chunks], dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1.0
    query = np.asarray(query_embedding, dtype=np.float32)
    query /= np.linalg.norm(query) or 1.0
    similarities = (matrix @ query) / norms
    best = np.argsort(similarities)[::-1][:top_k]
    return [chunks[i] for i in best]


def best_matchs(request: str, chunks: List[Chunk], top_k: int = TOP_K) -> List[Chunk]:
    if not chunks:
        return []
    return rank_chunks(generate_embedding(request), chunks, top_k)
