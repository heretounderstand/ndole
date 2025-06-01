import os
import uuid
from datetime import datetime
import tempfile
from typing import List, Optional
import pymupdf as pdf
from model import Document, DocumentRepository, Access
from utils.embedding import generate_embeddings
from utils.data import initialize_supabase

db = initialize_supabase()

def create_document_repository(name: str, description: str, owner_id: str, categories: List[str], is_public: bool) -> str:
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
    response = db.table('document_repositories').insert(repo_data).execute()
    res_user = db.table('users').select('repositories').eq('user_id', owner_id).limit(1).execute()
    current_docs = res_user.data[0]['repositories']
    updated_docs = current_docs + [repo_id]
    db.table('users').update({'repositories': updated_docs}).eq('user_id', owner_id).execute()
    if len(response.data) > 0:
        return repo_id
    else:
        raise Exception("Failed to create the document repository")

def get_document_repository(repo_id: str) -> Optional[DocumentRepository]:
    response = db.table('document_repositories').select('*').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
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
    repositories = []
    for repo_id in repo_ids:
        repository = get_document_repository(repo_id)
        if repository:
            repositories.append(repository)
    return repositories

def get_public_repositories(page: int, user_id: str, query: str = None) -> List[DocumentRepository]:
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
    response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    return len(response.data) > 0

def update_repository_access(repo_id: str, access: Access, access_type: str) -> bool:
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
    update_response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    return len(update_response.data) > 0

def update_repository_banner(repo_id: str, file_path:str) -> bool:
    with open(file_path, 'rb') as f:
        file_data = f.read()
    file_size = len(file_data)
    if file_size > 5 * 1024 * 1024:
        return None
    file_options = {}
    extension = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    file_options['content-type'] = mime_types.get(extension, 'application/octet-stream')
    storage_path = f"banners/{repo_id}/{file_path.split('.')[0]}.{extension}"
    db.storage.from_('banners').upload(
        path=f"{repo_id}/{file_path.split('.')[0]}.{extension}",
        file=file_data,
        file_options=file_options
    )
    update_response = db.table('document_repositories').update({'banner': storage_path}).eq('repo_id', repo_id).execute()
    return len(update_response.data) > 0

def load_repository_banner(banner: str) -> Optional[str]:
    banner = banner.lstrip('banners/')
    url = db.storage.from_('banners').create_signed_url(
        path=banner,
        expires_in=3600
    )
    return url['signedURL']

def upload_document(file_data: bytes, filename: str, repo_id: str, owner_id: str, title: str = None, description: str = "", category: str = None) -> Optional[str]:
    if not filename.lower().endswith('.pdf'):
        return None
    file_size = len(file_data)
    if file_size > 25 * 1024 * 1024:
        return None
    doc_id = str(uuid.uuid4())
    doc_id
    word_count = 0
    page_count = 0
    chunks = []
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
        os.unlink(temp_path)
    storage_path = f"documents/{repo_id}/{doc_id}.pdf"
    db.storage.from_('documents').upload(
        path=f"{repo_id}/{doc_id}.pdf",
        file=file_data,
        file_options={"content_type": "application/pdf"}
    )
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
    updated_docs = current_docs + [doc_id]
    db.table('document_repositories').update({'documents': updated_docs}).eq('repo_id', repo_id).execute()
    for i, chunk in enumerate(chunks):
        chunk_id = f"doc_{doc_id}_chunk_{i}"
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
    update_response = db.table('documents').update(update_data).eq('doc_id', doc_id).execute()
    return len(update_response.data) > 0

def get_document(doc_id: str) -> Optional[Document]:
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
    documents = []
    for doc_id in doc_ids:
        document = get_document(doc_id)
        if document:
            documents.append(document)
    return documents

def update_document_cover(doc_id: str, file_path:str) -> bool:
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
    storage_path = f"covers/{doc_id}/{file_path.split('.')[0]}.{extension}"
    db.storage.from_('covers').upload(
        path=f"{doc_id}/{file_path.split('.')[0]}.{extension}",
        file=file_data,
        file_options=file_options
    )
    update_response = db.table('documents').update({'cover': storage_path}).eq('doc_id', doc_id).execute()
    return len(update_response.data) > 0

def load_document_cover(cover: str) -> Optional[str]:
    cover = cover.lstrip('covers/')
    url = db.storage.from_('covers').create_signed_url(
        path=cover,
        expires_in=3600
    )
    return url["signedURL"]

def get_document_download_url(file_path: str) -> Optional[str]:
    file_path = file_path.lstrip('documents/')
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
    