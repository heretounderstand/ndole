from typing import List
import requests
from model import Chunk
import numpy as np

def get_embedding_from_api(text: str) -> bool:
    response = requests.post(
        "http://localhost:8000/generate-embedding",
        json={"text": text}
    )
    return response.json()["embedding"]

def generate_embeddings(blocks: List[str], page_num: int) -> List[Chunk]:
    """
    Génère des chunks à partir du texte avec leurs embeddings correspondants.
    
    Args:
        text: Texte complet du document
        page_word_count: Liste du nombre de mots par page
        
    Returns:
        Liste d'objets Chunk avec texte, embedding et numéro de page
    """
    
    position = 0
    chunks = []
    
    for block in blocks:
        if not block.strip():
            continue
        
        # Générer l'embedding pour ce paragraphe
        MAX_TOKENS = 512  # Taille maximale recommandée pour ce modèle
        truncated_text = block[:MAX_TOKENS] if len(block) > MAX_TOKENS else block
        embedding_vector = get_embedding_from_api(truncated_text)
        
        # Créer et ajouter le chunk
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
    """
    Trouve le meilleur match pour une requête donnée dans une liste de chunks.
    
    Args:
        request: Requête de l'utilisateur
        chunks: Liste de chunks à comparer
        
    Returns:
        Liste de chunks triés par similarité décroissante
    """
    
    # Encoder la requête
    query_embedding = get_embedding_from_api(request)
    
    # Calculer les similarités cosinus (produit scalaire des vecteurs normalisés)
    similarities = [np.dot(chunk.embedding, query_embedding) for chunk in chunks]
    
    # Trouver l'indice du meilleur match
    best_indices = np.argsort(similarities)[-20:][::-1]
    
    # Récupérer les chunks correspondants
    best_chunks = [chunks[i] for i in best_indices]

    return best_chunks