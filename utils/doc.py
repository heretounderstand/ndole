import os
import uuid
from datetime import datetime
import tempfile
from typing import Any, Dict, List, Optional
import pymupdf as pdf

# Importation des classes du model.py
from model import Document, DocumentRepository, Access
from utils.embedding import generate_embeddings
from utils.data import initialize_supabase

db = initialize_supabase()

# Fonctions pour les DocumentRepositories
def create_document_repository(name: str, description: str, owner_id: str) -> str:
    """
    Crée un nouveau repository de documents dans Supabase
    
    Args:
        db: Client Supabase initialisé
        name: Nom du repository
        description: Description du repository
        owner_id: ID de l'utilisateur propriétaire
        
    Returns:
        ID du repository créé
    """
    
    repo_id = str(uuid.uuid4())
    
    repo = DocumentRepository(
        repo_id=repo_id,
        name=name,
        description=description,
        owner_id=owner_id,
    )
    
    repo_data = repo.dict()
    
    # Insérer dans la table document_repositories de Supabase
    response = db.table('document_repositories').insert(repo_data).execute()
    
    res_user = db.table('users').select('repositories').eq('user_id', owner_id).limit(1).execute()
    
    current_docs = res_user.data[0]['repositories']
    updated_docs = current_docs + [repo_id]  # Crée une NOUVELLE liste
    
    db.table('users').update({'repositories': updated_docs}).eq('user_id', owner_id).execute()
    
    # Vérifier si l'insertion a réussi
    if len(response.data) > 0:
        return repo_id
    else:
        raise Exception("Erreur lors de la création du repository de documents")

def get_document_repository(repo_id: str) -> Optional[DocumentRepository]:
    """
    Récupère un repository par son ID
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        
    Returns:
        DocumentRepository ou None si non trouvé
    """
    
    response = db.table('document_repositories').select('*').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
    
    # Vérifier si des données ont été trouvées
    if not response.data or len(response.data) == 0:
        return None
    
    repo_data = response.data[0]
    
    return DocumentRepository(
        repo_id=repo_data['repo_id'],
        name=repo_data['name'],
        description=repo_data['description'],
        owner_id=repo_data['owner_id'],
        is_public=repo_data['is_public'],
        categories=repo_data['categories'],
        created_at=repo_data['created_at'],
        updated_at=repo_data['updated_at'],
        documents=repo_data["documents"],
        is_deleted=repo_data["is_deleted"],
        banner=repo_data["banner"]
    )

def update_document_repository(repo_id: str, name: str = None, description: str = None, 
                              is_public: bool = None, categories: List[str] = None, is_deleted: bool = None, banner: str = None,
                              documents: List[str] = None) -> bool:
    """
    Met à jour un repository
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        name: Nouveau nom (optionnel)
        description: Nouvelle description (optionnel)
        is_public: Nouveau statut public (optionnel)
        categories: Nouvelles catégories (optionnel)
        documents: Nouveaux documents (optionnel)
        
    Returns:
        True si mis à jour avec succès, False sinon
    """
    
    # Vérifier d'abord si le repository existe
    response = db.table('document_repositories').select('*').eq('repo_id', repo_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return False
    
    update_data = {'updated_at': datetime.now().isoformat()}
    if name:
        update_data['name'] = name
    if description:
        update_data['description'] = description
    if is_public is not None:
        update_data['is_public'] = is_public
    if categories:
        update_data['categories'] = categories
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if banner:
        update_data['banner'] = banner
    if documents:
        update_data['documents'] = documents
    
    # Mettre à jour les données dans Supabase
    response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(response.data) > 0

def get_user_repositories(repo_ids: List[str]) -> List[DocumentRepository]:
    """
    Récupère tous les repositories d'un utilisateur
    
    Args:
        db: Client Supabase initialisé
        user_id: ID de l'utilisateur
        
    Returns:
        Liste des repositories de l'utilisateur
    """
    repositories = []
    
    for repo_id in repo_ids:
        response = db.table('document_repositories').select('*').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
    
        repo_data = response.data[0]
    
        repository = DocumentRepository(
            repo_id=repo_data['repo_id'],
            name=repo_data['name'],
            description=repo_data['description'],
            owner_id=repo_data['owner_id'],
            is_public=repo_data['is_public'],
            categories=repo_data['categories'],
            created_at=repo_data['created_at'],
            updated_at=repo_data['updated_at'],
            documents=repo_data["documents"],
            is_deleted=repo_data["is_deleted"],
            banner=repo_data["banner"]
        )
        repositories.append(repository)
    
    return repositories

def get_public_repositories() -> List[DocumentRepository]:
    """
    Récupère tous les repositories publics
    
    Args:
        db: Client Supabase initialisé
        
    Returns:
        Liste des repositories publics
    """
    
    response = db.table('document_repositories').select('*').eq('is_public', True).eq('is_deleted', False).range(0, 19).execute()
    repositories = []
    
    for repo_data in response.data:
        repository = DocumentRepository(
            repo_id=repo_data['repo_id'],
            name=repo_data['name'],
            description=repo_data['description'],
            owner_id=repo_data['owner_id'],
            is_public=repo_data['is_public'],
            categories=repo_data['categories'],
            created_at=repo_data['created_at'],
            updated_at=repo_data['updated_at'],
            documents=repo_data["documents"],
            is_deleted=repo_data["is_deleted"],
            banner=repo_data["banner"]
        )
        repositories.append(repository)
    
    return repositories

def upload_document(file_data: bytes, filename: str, repo_id: str, owner_id: str) -> Optional[str]:
    """
    Upload un document PDF et génère des embeddings
    
    Args:
        file_data: Contenu binaire du fichier
        filename: Nom du fichier
        repo_id: ID du repository
        owner_id: ID de l'utilisateur
        
    Returns:
        ID du document créé ou None en cas d'erreur
    """
    
    # Vérifier si c'est un PDF et sa taille
    if not filename.lower().endswith('.pdf'):
        return None
    
    file_size = len(file_data)
    # Vérifier la taille du fichier (moins de 25 Mo)
    if file_size > 25 * 1024 * 1024:  # 25 Mo en bytes
        return None
    
    # Créer un ID unique pour le document
    doc_id = str(uuid.uuid4())
    doc_id
    word_count = 0
    page_count = 0
    chunks = []
    
    # Extraire le texte du PDF
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_data)
        temp_path = temp_file.name
    
    try:
        with pdf.open(temp_path) as f:
            page_count = len(f)
            for page_num in range(page_count):
                page = f[page_num].get_textpage()
                page_text = page.extractWORDS()
                word_count += len(page_text)
                pdf_blocks = page.extractBLOCKS()
                blocks = [block[4] for block in pdf_blocks if block[6] == 0]
                chunk = generate_embeddings(blocks, page_num)
                chunks.extend(chunk)
    finally:
        os.unlink(temp_path)  # Supprimer le fichier temporaire

    # Uploader le fichier dans Storage
    storage_path = f"documents/{repo_id}/{doc_id}.pdf"
    db.storage.from_('documents').upload(
        path=f"{repo_id}/{doc_id}.pdf",
        file=file_data,
        file_options={"content_type": "application/pdf"}
    )
    
    # Créer l'entrée dans la table documents
    doc = Document(
        title=filename.split('.')[0],
        doc_id=doc_id,
        page_count=page_count,
        word_count=word_count,
        file_size=file_size,
        file_path=storage_path,
        owner_id=owner_id,
        original_repo=repo_id
    )
    
    doc_data = doc.dict()
    
    db.table('documents').insert(doc_data).execute()
    
    res_repo = db.table('document_repositories').select('documents').eq('repo_id', repo_id).limit(1).execute()
    
    current_docs = res_repo.data[0]['documents']
    updated_docs = current_docs + [doc_id]  # Crée une NOUVELLE liste
    
    db.table('document_repositories').update({'documents': updated_docs}).eq('repo_id', repo_id).execute()
    
    # Préparer les données pour Supabase Vector
    for i, chunk in enumerate(chunks):
        chunk_id = f"doc_{doc_id}_chunk_{i}"
        
        # Ajouter chaque chunk à la table "chunks" de Supabase avec son embedding
        db.table('chunks').insert({
            'chunk_id': chunk_id,
            'document_id': doc_id,
            'position': chunk.position,
            'page': chunk.page,
            'text': chunk.text,
            'embedding': chunk.embedding
        }).execute()
    
    return doc_id

def update_document(doc_id: str, title: str = None, description: str = None, 
                   category: str = None, related_documents: List[str] = None, is_deleted: bool = None, cover: str = None, 
                   is_index: bool = None) -> bool:
    """
    Met à jour un document
    
    Args:
        db: Client Supabase initialisé
        doc_id: ID du document
        title: Nouveau titre (optionnel)
        description: Nouvelle description (optionnel)
        category: Nouvelle catégorie (optionnel)
        related_documents: Nouveaux documents liés (optionnel)
        is_index: Statut d'indexation (optionnel)
        
    Returns:
        True si mis à jour avec succès, False sinon
    """
    
    # Récupérer d'abord le document existant
    response = db.table('documents').select('*').eq('doc_id', doc_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return False
    
    doc_data = response.data[0]
    
    update_data = {}
    if title:
        update_data['title'] = title
    if description:
        update_data['description'] = description
    if category:
        update_data['category'] = category
    if related_documents:
        update_data['related_documents'] = related_documents
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if cover:
        update_data['cover'] = cover
    if is_index is not None:
        if is_index:
            update_data['number_of_indexed'] = doc_data['number_of_indexed'] + 1
        else:
            update_data['number_of_indexed'] = doc_data['number_of_indexed'] - 1
    
    # Mettre à jour le document dans Supabase
    update_response = db.table('documents').update(update_data).eq('doc_id', doc_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(update_response.data) > 0

def update_document_access(doc_id: str, access: Access, access_type: str) -> bool:
    """
    Met à jour le type d'accès d'un document (like, dislike, bookmark, share)
    
    Args:
        db: Client Supabase initialisé
        doc_id: ID du document
        access: Objet Access contenant les informations d'accès
        access_type: Type d'accès (like, dislike, bookmark, share)
        
    Returns:
        True si mis à jour avec succès, False sinon
    """
    
    # Récupérer d'abord le document existant
    response = db.table('documents').select('*').eq('doc_id', doc_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0 or access_type not in ['accesses', 'likes', 'dislikes', 'bookmarks', 'shares']:
        return False
    
    if response.data[0]['owner_id'] == access.access_id:
        return False
    
    doc_data = response.data[0]
    
    update_data = {
        'accesses': doc_data['accesses'], 
        'likes': doc_data['likes'], 
        'dislikes': doc_data['dislikes'], 
        'bookmarks': doc_data['bookmarks'], 
        'shares': doc_data['shares']
    }
    
    if access_type == 'accesses':
        update_data['accesses'].append(access)
    elif access_type == 'likes':
        is_like = False
        for dislike in update_data['dislikes']:
            if dislike["access_id"] == access.access_id:
                update_data['dislikes'].remove(dislike)
        for like in update_data['likes']:
            if like["access_id"] == access.access_id:
                is_like = True
                update_data['likes'].remove(like)
        if is_like:
            update_data['likes'].append(access)
    elif access_type == 'dislikes':
        is_dislike = False
        for like in update_data['likes']:
            if like["access_id"] == access.access_id:
                update_data['likes'].remove(like)
        for dislike in update_data['dislikes']:
            if dislike["access_id"] == access.access_id:
                is_dislike = True
                update_data['dislikes'].remove(dislike)
        if is_dislike:
            update_data['dislikes'].append(access)
    elif access_type == 'bookmarks':
        is_bookmark = False
        for bookmark in update_data['bookmarks']:
            if bookmark["access_id"] == access.access_id:
                is_bookmark = True
                update_data['bookmarks'].remove(bookmark)
        if not is_bookmark:
            update_data['bookmarks'].append(access)
    elif access_type == 'shares':
        update_data['shares'].append(access)
    
    # Mettre à jour le document dans Supabase
    update_response = db.table('documents').update(update_data).eq('doc_id', doc_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(update_response.data) > 0

def get_document(doc_id: str) -> Optional[Document]:
    """
    Récupère un document par son ID
    
    Args:
        db: Client Supabase initialisé
        doc_id: ID du document
        
    Returns:
        Document ou None si non trouvé
    """
    
    response = db.table('documents').select('*').eq('doc_id', doc_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return None
    
    doc_data = response.data[0]
    
    return Document(
        doc_id=doc_data['doc_id'],
        title=doc_data['title'],
        description=doc_data['description'],
        owner_id=doc_data['owner_id'],
        file_path=doc_data['file_path'],
        file_size=doc_data['file_size'],
        upload_date=doc_data['upload_date'],
        category=doc_data['category'],
        accesses=doc_data['accesses'],
        likes=doc_data['likes'],
        dislikes=doc_data['dislikes'],
        bookmarks=doc_data['bookmarks'],
        shares=doc_data['shares'],
        number_of_indexed=doc_data['number_of_indexed'],
        word_count=doc_data['word_count'],
        page_count=doc_data['page_count'],
        related_documents=doc_data['related_documents'],
        original_repo=doc_data['original_repo'],
        type=doc_data["type"],
        is_deleted=doc_data["is_deleted"],
        cover=doc_data["cover"]
    )

def get_document_download_url(doc_id: str) -> Optional[str]:
    """
    Génère une URL de téléchargement temporaire pour un document
    
    Args:
        doc_id: ID du document
        
    Returns:
        URL de téléchargement ou None si non trouvé
    """
    
    response = db.table('documents').select('file_path').eq('doc_id', doc_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0 or 'file_path' not in response.data[0]:
        return None
    
    doc_data = response.data[0]
    
    # Générer une URL signée valide pendant 1 heure (3600 secondes)
    url = db.storage.from_('documents').create_signed_url(
        path=doc_data['file_path'],
        expires_in=3600
    )
    
    return url

def search_related_documents(doc_id: str) -> List[Document]:
    """
    Recherche des documents similaires à un document donné
    
    Args:
        doc_id: ID du document
        
    Returns:
        Liste de documents similaires
    """
    
    # Récupérer le document
    response = db.table('documents').select('*').eq('doc_id', doc_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return []
    
    doc_data = response.data[0]
    related_docs = []
    
    if 'related_documents' not in doc_data or not doc_data['related_documents']:
        return []
    
    # Pour chaque document lié, récupérer les informations
    for related_doc_id in doc_data['related_documents']:
        related_response = db.table('documents').select('*').eq('doc_id', related_doc_id).limit(1).execute()
        
        if not related_response.data or len(related_response.data) == 0:
            continue
        
        related_doc_data = related_response.data[0]
        
        related_docs.append(Document(
            doc_id=related_doc_data['doc_id'],
            title=related_doc_data['title'],
            description=related_doc_data['description'],
            owner_id=related_doc_data['owner_id'],
            file_path=related_doc_data['file_path'],
            file_size=related_doc_data['file_size'],
            upload_date=related_doc_data['upload_date'],
            category=related_doc_data['category'],
            accesses=related_doc_data['accesses'],
            likes=related_doc_data['likes'],
            dislikes=related_doc_data['dislikes'],
            bookmarks=related_doc_data['bookmarks'],
            shares=related_doc_data['shares'],
            number_of_indexed=related_doc_data['number_of_indexed'],
            word_count=related_doc_data['word_count'],
            page_count=related_doc_data['page_count'],
            original_repo=related_doc_data['original_repo'],
            related_documents=related_doc_data['related_documents'],
            is_deleted=related_doc_data["is_deleted"],
            cover=related_doc_data["cover"],
            type=related_doc_data["type"]
        ))
    
    return related_docs

def get_filtred_documents(filter: str, value: str) -> List[Document]:
    """
    Récupère tous les documents filtrés selon un critère
    
    Args:
        filter: Champ à filtrer
        value: Valeur du filtre
        
    Returns:
        Liste des documents correspondant au filtre
    """
    
    response = db.table('documents').select('*').eq(filter, value).eq('is_deleted', False).execute()
    documents = []
    
    for doc_data in response.data:
        document = Document(
            doc_id=doc_data['doc_id'],
            title=doc_data['title'],
            description=doc_data['description'],
            owner_id=doc_data['owner_id'],
            file_path=doc_data['file_path'],
            file_size=doc_data['file_size'],
            upload_date=doc_data['upload_date'],
            category=doc_data['category'],
            accesses=doc_data['accesses'],
            likes=doc_data['likes'],
            dislikes=doc_data['dislikes'],
            bookmarks=doc_data['bookmarks'],
            shares=doc_data['shares'],
            number_of_indexed=doc_data['number_of_indexed'],
            word_count=doc_data['word_count'],
            page_count=doc_data['page_count'],
            original_repo=doc_data['original_repo'],
            type=doc_data["type"],
            is_deleted=doc_data["is_deleted"],
            cover=doc_data["cover"],
            related_documents=doc_data['related_documents']
        )
        documents.append(document)
    
    return documents

def get_document_stats(docs: List[Document]) -> Dict[str, Any]:
        """Retourne des statistiques sur les documents du dépôt"""
        if not docs:
            return {
                "total": 0,
                "by_type": {},
                "by_category": {},
                "average_indexed_count": 0,
                "average_viewed_count": 0,
                "average_pertinence": 0,
                "average_shared_count": 0,
                "average_saved_count": 0,
                "average_size": 0
            }
        
        # Calculer les statistiques
        by_type = {}
        by_category = {}
        indexed_count = 0
        total_size = 0
        
        for doc in docs:
            # Compter par type
            file_type = doc.type
            by_type[file_type] = by_type.get(file_type, 0) + 1
            
            # Compter par catégorie
            category = doc.category or "Not categorized"
            by_category[category] = by_category.get(category, 0) + 1
            
            # Compter les documents indexés
            indexed_count += doc.number_of_indexed
            viewed_count = len(doc.accesses)
            shared_count = len(doc.shares)
            saved_count = len(doc.bookmarks)
            pertinence = len(doc.likes) - len(doc.dislikes)
            
            # Additionner les tailles
            total_size += doc.file_size
        
        return {
            "total": len(docs),
            "by_type": by_type,
            "by_category": by_category,
            "average_indexed_count": indexed_count / len(docs),
            "average_pertinence": pertinence / len(docs),
            "average_shared_count": shared_count / len(docs),
            "average_saved_count": saved_count / len(docs),
            "average_viewed_count": viewed_count  / len(docs),
            "average_size": total_size / len(docs)
        }
    