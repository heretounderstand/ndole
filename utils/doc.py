import os
import uuid
from datetime import datetime
import tempfile
from typing import List, Optional
import pymupdf as pdf

# Importation des classes du model.py
from model import Document, DocumentRepository, Access
from utils.embedding import generate_embeddings
from utils.data import initialize_supabase

db = initialize_supabase()

# Fonctions pour les DocumentRepositories
def create_document_repository(name: str, description: str, owner_id: str, categories: List[str], is_public: bool) -> str:
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
        categories=categories,
        is_public=is_public
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
        raise Exception("Failed to create the document repository")

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
        banner=repo_data["banner"],
        accesses=repo_data['accesses'],
        likes=repo_data['likes'],
        dislikes=repo_data['dislikes'],
        bookmarks=repo_data['bookmarks'],
        shares=repo_data['shares'],
        number_of_indexed=repo_data['number_of_indexed'],
        related_repositories=repo_data['related_repositories']
    )

def get_list_of_repositories(repo_ids: List[str]) -> List[DocumentRepository]:
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
        repository = get_document_repository(repo_id)
        if repository:
            repositories.append(repository)
    
    return repositories

def get_public_repositories(page: int, user_id: str, query: str = None) -> List[DocumentRepository]:
    """
    Récupère tous les repositories publics
    
    Args:
        db: Client Supabase initialisé
        
    Returns:
        Liste des repositories publics
    """
    if query:
        response = db.table('document_repositories').select('*').eq('is_public', True).eq('is_deleted', False).neq('owner_id', user_id).gte('name', query).range(20*(page-1), 20*page).execute()
    else:
        response = db.table('document_repositories').select('*').eq('is_public', True).eq('is_deleted', False).neq('owner_id', user_id).range(20*(page-1), 20*page).execute()  
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
            banner=repo_data["banner"],
            accesses=repo_data['accesses'],
            likes=repo_data['likes'],
            dislikes=repo_data['dislikes'],
            bookmarks=repo_data['bookmarks'],
            shares=repo_data['shares'],
            number_of_indexed=repo_data['number_of_indexed'],
            related_repositories=repo_data['related_repositories']
        )
        repositories.append(repository)
    
    return repositories

def update_document_repository(repo_id: str, name: str = None, description: str = None, 
                              is_public: bool = None, categories: List[str] = None, is_deleted: bool = None,
                              documents: List[str] = None, is_indexed: bool = None) -> bool:
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
    if documents:
        update_data['documents'] = documents
    if is_indexed is not None:
        if is_indexed:
            update_data["number_of_indexed"] += 1
        else:
            update_data['number_of_indexed'] -=1
    
    # Mettre à jour les données dans Supabase
    response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(response.data) > 0

def update_repository_access(repo_id: str, access: Access, access_type: str) -> bool:
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
    response = db.table('document_repositories').select('*').eq('repo_id', repo_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0 or access_type not in ['accesses', 'likes', 'dislikes', 'bookmarks', 'shares']:
        return False
    
    if response.data[0]['owner_id'] == access.access_id:
        return False
    
    repo_data = response.data[0]
    
    update_data = {
        'accesses': repo_data['accesses'], 
        'likes': repo_data['likes'], 
        'dislikes': repo_data['dislikes'], 
        'bookmarks': repo_data['bookmarks'], 
        'shares': repo_data['shares']
    }
    
    if access_type == 'accesses':
        update_data['accesses'].append(access.dict())
    elif access_type == 'likes':
        is_like = False
        for dislike in update_data['dislikes']:
            if dislike["access_id"] == access.access_id:
                update_data['dislikes'].remove(dislike)
        for like in update_data['likes']:
            if like["access_id"] == access.access_id:
                is_like = True
                update_data['likes'].remove(like)
        if not is_like:
            update_data['likes'].append(access.dict())
    elif access_type == 'dislikes':
        is_dislike = False
        for like in update_data['likes']:
            if like["access_id"] == access.access_id:
                update_data['likes'].remove(like)
        for dislike in update_data['dislikes']:
            if dislike["access_id"] == access.access_id:
                is_dislike = True
                update_data['dislikes'].remove(dislike)
        if not is_dislike:
            update_data['dislikes'].append(access.dict())
    elif access_type == 'bookmarks':
        is_bookmark = False
        for bookmark in update_data['bookmarks']:
            if bookmark["access_id"] == access.access_id:
                is_bookmark = True
                update_data['bookmarks'].remove(bookmark)
        if not is_bookmark:
            update_data['bookmarks'].append(access.dict())
    elif access_type == 'shares':
        update_data['shares'].append(access.dict())
    
    # Mettre à jour le document dans Supabase
    update_response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(update_response.data) > 0

def update_repository_banner(repo_id: str, file_path:str) -> bool:
    """
    Met à jour la bannière d'un repository
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        banner: Nouvelle bannière (optionnel)
        banner_data: Données de la bannière (optionnel)
        
    Returns:
        True si mis à jour avec succès, False sinon
    """
    
    # Lire le fichier en mode binaire
    with open(file_path, 'rb') as f:
        file_data = f.read()
        
    file_size = len(file_data)
    # Vérifier la taille du fichier (moins de 5 Mo)
    if file_size > 5 * 1024 * 1024:  # 5 Mo en bytes
        return None
    
    file_options = {}
    
    extension = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    file_options['content-type'] = mime_types.get(extension, 'application/octet-stream')
    
    # Uploader le fichier dans Storage
    storage_path = f"banners/{repo_id}/{file_path.split('.')[0]}.{extension}"
    
    # Uploader le fichier
    db.storage.from_('banners').upload(
        path=f"{repo_id}/{file_path.split('.')[0]}.{extension}",
        file=file_data,
        file_options=file_options
    )
    
    # Mettre à jour le document dans Supabase
    update_response = db.table('document_repositories').update({'banner': storage_path}).eq('repo_id', repo_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(update_response.data) > 0

def load_repository_banner(banner: str) -> Optional[str]:
    """
    Charge la bannière d'un repository
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        
    Returns:
        URL de la bannière ou None si non trouvé
    """
    banner = banner.lstrip('banners/')
    
    # Générer une URL signée valide pendant 1 heure (3600 secondes)
    url = db.storage.from_('banners').create_signed_url(
        path=banner,
        expires_in=3600
    )
    
    return url['signedURL']

def upload_document(file_data: bytes, filename: str, repo_id: str, owner_id: str, title: str = None, description: str = "", category: str = None) -> Optional[str]:
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
        title=title if title else filename.split('.')[0],
        doc_id=doc_id,
        page_count=page_count,
        word_count=word_count,
        file_size=file_size,
        file_path=storage_path,
        owner_id=owner_id,
        original_repo=repo_id,
        description=description,
        category=category
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
                   category: str = None, related_documents: List[str] = None, is_deleted: bool = None) -> bool:
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
    response = db.table('documents').select('*').eq('doc_id', doc_id).eq('is_deleted', False).limit(1).execute()
    
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
        word_count=doc_data['word_count'],
        page_count=doc_data['page_count'],
        related_documents=doc_data['related_documents'],
        original_repo=doc_data['original_repo'],
        type=doc_data["type"],
        is_deleted=doc_data["is_deleted"],
        cover=doc_data["cover"]
    )

def get_list_of_documents(doc_ids: List[str]) -> List[Document]:
    """
    Récupère tous les repositories d'un utilisateur
    
    Args:
        db: Client Supabase initialisé
        user_id: ID de l'utilisateur
        
    Returns:
        Liste des repositories de l'utilisateur
    """
    documents = []
    
    for doc_id in doc_ids:
        document = get_document(doc_id)
        if document:
            documents.append(document)
    
    return documents

def update_document_cover(doc_id: str, file_path:str) -> bool:
    """
    Met à jour la bannière d'un repository
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        banner: Nouvelle bannière (optionnel)
        banner_data: Données de la bannière (optionnel)
        
    Returns:
        True si mis à jour avec succès, False sinon
    """
    
    # Lire le fichier en mode binaire
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    file_options = {}
    
    extension = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    file_options['content-type'] = mime_types.get(extension, 'application/octet-stream')
    
    # Uploader le fichier dans Storage
    storage_path = f"covers/{doc_id}/{file_path.split('.')[0]}.{extension}"
    
    # Uploader le fichier
    db.storage.from_('covers').upload(
        path=f"{doc_id}/{file_path.split('.')[0]}.{extension}",
        file=file_data,
        file_options=file_options
    )
    
    # Mettre à jour le document dans Supabase
    update_response = db.table('documents').update({'cover': storage_path}).eq('doc_id', doc_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(update_response.data) > 0

def load_document_cover(cover: str) -> Optional[str]:
    """
    Charge la bannière d'un repository
    
    Args:
        db: Client Supabase initialisé
        repo_id: ID du repository
        
    Returns:
        URL de la bannière ou None si non trouvé
    """
    cover = cover.lstrip('covers/')
    
    # Générer une URL signée valide pendant 1 heure (3600 secondes)
    url = db.storage.from_('covers').create_signed_url(
        path=cover,
        expires_in=3600
    )
    
    return url["signedURL"]

def get_document_download_url(file_path: str) -> Optional[str]:
    """
    Génère une URL de téléchargement temporaire pour un document
    
    Args:
        doc_id: ID du document
        
    Returns:
        URL de téléchargement ou None si non trouvé
    """
    file_path = file_path.lstrip('documents/')
    
    # Générer une URL signée valide pendant 1 heure (3600 secondes)
    url = db.storage.from_('documents').create_signed_url(
        path=file_path,
        expires_in=3600
    )
    
    return url["signedURL"]

def get_owner_name(user_id: str) -> Optional[str]:
    response = db.table('users').select('username').eq('user_id', user_id).limit(1).execute()
    return response.data[0]['username'] if response.data else None

def get_original_repo(repo_id: str) -> Optional[str]:
    response = db.table('document_repositories').select('name').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
    return response.data[0]['name'] if response.data else None
    
