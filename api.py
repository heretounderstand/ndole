from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')

class TextRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

@app.post("/generate-embedding", response_model=EmbeddingResponse)
def generate_embedding(request: TextRequest):
    embedding = model.encode(request.text, convert_to_tensor=False)
    return {"embedding": embedding.tolist()}
    

# Lancer avec: uvicorn api:app --reload