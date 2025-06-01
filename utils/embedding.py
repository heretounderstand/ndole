from typing import List
from model import Chunk
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> List[float]:
    model = load_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()

def generate_embeddings(blocks: List[str], page_num: int) -> List[Chunk]:
    position = 0
    chunks = []
    for block in blocks:
        if not block.strip():
            continue
        MAX_TOKENS = 512 
        truncated_text = block[:MAX_TOKENS] if len(block) > MAX_TOKENS else block
        embedding_vector = generate_embedding(truncated_text)
        chunk = Chunk(
            text=block,
            embedding=embedding_vector,
            page=page_num,
            position=position
        )
        chunks.append(chunk)
        position += 1
    return chunks

def best_matchs(request: str, chunks: List[Chunk]) -> List[Chunk]:
    query_embedding = generate_embedding(request)
    similarities = [np.dot(chunk.embedding, query_embedding) for chunk in chunks]
    best_indices = np.argsort(similarities)[-20:][::-1]
    best_chunks = [chunks[i] for i in best_indices]
    return best_chunks