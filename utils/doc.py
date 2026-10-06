import os
import uuid
from typing import Any, Dict, List, Optional, Tuple
import pymupdf
import streamlit as st
from model import ACCESS_TYPES, Access, Chunk, Document, DocumentRepository, now_iso
from utils.embedding import generate_embeddings
from utils.data import get_db
from utils.user import toggle_access

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIZE = 5 * 1024 * 1024
IMAGE_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
PUBLIC_PAGE_SIZE = 20
# Consecutive PDF text blocks are merged until a chunk reaches about this many characters,
# so that retrieval works on paragraphs rather than on isolated titles or lines.
CHUNK_TARGET_CHARS = 800
SIGNED_URL_TTL = 3600


def _repo_from_row(repo_data: Dict[str, Any]) -> DocumentRepository:
    data = {k: v for k, v in repo_data.items() if v is not None and k in DocumentRepository.model_fields}
    return DocumentRepository(**data)


def create_document_repository(name: str, description: str, owner_id: str, categories: List[str], is_public: bool) -> str:
    repo = DocumentRepository(
        name=name,
        description=description,
        owner_id=owner_id,
        categories=categories,
        is_public=is_public
    )
    db = get_db()
    response = db.table('document_repositories').insert(repo.model_dump()).execute()
    if not response.data:
        raise Exception("Failed to create the document repository")
    res_user = db.table('users').select('repositories').eq('user_id', owner_id).limit(1).execute()
    current = (res_user.data[0]['repositories'] or []) if res_user.data else []
    db.table('users').update({'repositories': current + [repo.repo_id]}).eq('user_id', owner_id).execute()
    return repo.repo_id


def get_document_repository(repo_id: str) -> Optional[DocumentRepository]:
    response = get_db().table('document_repositories').select('*').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
    return _repo_from_row(response.data[0]) if response.data else None


def get_list_of_repositories(repo_ids: List[str]) -> List[DocumentRepository]:
    if not repo_ids:
        return []
    response = get_db().table('document_repositories').select('*').in_('repo_id', repo_ids) \
        .eq('is_deleted', False).order('updated_at', desc=True).execute()
    return [_repo_from_row(row) for row in response.data or []]


def get_public_repositories(page: int, user_id: str, query: str = None) -> List[DocumentRepository]:
    request = get_db().table('document_repositories').select('*') \
        .eq('is_public', True).eq('is_deleted', False).neq('owner_id', user_id)
    if query and query.strip():
        # Escape the LIKE wildcards so the search is a plain "contains".
        term = query.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        request = request.ilike('name', f'%{term}%')
    start = PUBLIC_PAGE_SIZE * (page - 1)
    response = request.order('updated_at', desc=True).range(start, start + PUBLIC_PAGE_SIZE - 1).execute()
    return [_repo_from_row(row) for row in response.data or []]


def update_document_repository(repo_id: str, name: str = None, description: str = None,
                               is_public: bool = None, categories: List[str] = None, is_deleted: bool = None,
                               documents: List[str] = None, is_indexed: bool = None) -> bool:
    db = get_db()
    response = db.table('document_repositories').select('number_of_indexed').eq('repo_id', repo_id).limit(1).execute()
    if not response.data:
        return False
    update_data = {'updated_at': now_iso()}
    if name:
        update_data['name'] = name
    # `is not None` rather than truthiness so a field can be cleared (empty
    # description, no categories, last document removed).
    if description is not None:
        update_data['description'] = description
    if is_public is not None:
        update_data['is_public'] = is_public
    if categories is not None:
        update_data['categories'] = categories
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if documents is not None:
        update_data['documents'] = documents
    if is_indexed is not None:
        current = response.data[0].get('number_of_indexed') or 0
        update_data['number_of_indexed'] = max(current + (1 if is_indexed else -1), 0)
    response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    return len(response.data) > 0


def update_repository_access(repo_id: str, access: Access, access_type: str) -> bool:
    if access_type not in ACCESS_TYPES:
        return False
    db = get_db()
    response = db.table('document_repositories').select('*').eq('repo_id', repo_id).limit(1).execute()
    if not response.data:
        return False
    repo_data = response.data[0]
    if repo_data['owner_id'] == access.access_id:
        return False
    update_data = {key: list(repo_data.get(key) or []) for key in ACCESS_TYPES}
    opposite = {'likes': 'dislikes', 'dislikes': 'likes'}.get(access_type)
    update_data[access_type] = toggle_access(update_data[access_type], access, access_type,
                                             update_data[opposite] if opposite else None)
    update_response = db.table('document_repositories').update(update_data).eq('repo_id', repo_id).execute()
    return len(update_response.data) > 0


def _upload_image(bucket: str, folder: str, file_data: bytes, filename: str) -> str:
    """Upload an image to `bucket` and return its stored path ("<bucket>/<folder>/<uuid>.<ext>")."""
    extension = os.path.splitext(filename)[1].lower()
    if extension not in IMAGE_TYPES:
        raise ValueError("Unsupported image type. Use JPG, PNG or WEBP.")
    if len(file_data) > MAX_IMAGE_SIZE:
        raise ValueError("The image is too large (max 5 MB).")
    object_path = f"{folder}/{uuid.uuid4()}{extension}"
    get_db().storage.from_(bucket).upload(
        path=object_path,
        file=file_data,
        file_options={'content-type': IMAGE_TYPES[extension]}
    )
    return f"{bucket}/{object_path}"


def update_repository_banner(owner_id: str, repo_id: str, file_data: bytes, filename: str) -> bool:
    storage_path = _upload_image('banners', f"{owner_id}/{repo_id}", file_data, filename)
    update_response = get_db().table('document_repositories').update({'banner': storage_path}).eq('repo_id', repo_id).execute()
    return len(update_response.data) > 0


def update_document_cover(owner_id: str, doc_id: str, file_data: bytes, filename: str) -> bool:
    storage_path = _upload_image('covers', f"{owner_id}/{doc_id}", file_data, filename)
    update_response = get_db().table('documents').update({'cover': storage_path}).eq('doc_id', doc_id).execute()
    return len(update_response.data) > 0


@st.cache_data(ttl=SIGNED_URL_TTL - 300, show_spinner=False)
def _signed_url(bucket: str, stored_path: str) -> Optional[str]:
    # removeprefix, not lstrip: lstrip('banners/') strips any of those *characters*,
    # which mangled paths whose owner id starts with e.g. "a", "b", "e" or "s".
    object_path = stored_path.removeprefix(f"{bucket}/")
    try:
        url = get_db().storage.from_(bucket).create_signed_url(path=object_path, expires_in=SIGNED_URL_TTL)
    except Exception:
        return None
    return url.get("signedURL") or url.get("signedUrl")


def load_repository_banner(banner: str) -> Optional[str]:
    return _signed_url('banners', banner)


def load_document_cover(cover: str) -> Optional[str]:
    return _signed_url('covers', cover)


def get_document_download_url(file_path: str) -> Optional[str]:
    return _signed_url('documents', file_path)


def group_blocks(blocks: List[str], target_chars: int = CHUNK_TARGET_CHARS) -> List[str]:
    """Merge consecutive text blocks into chunks of roughly `target_chars` characters."""
    groups, current = [], ""
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if current and len(current) + len(block) > target_chars:
            groups.append(current)
            current = block
        else:
            current = f"{current}\n{block}" if current else block
    if current:
        groups.append(current)
    return groups


def extract_pdf(file_data: bytes) -> Tuple[int, int, List[Chunk]]:
    """Return (page_count, word_count, chunks) for a PDF."""
    word_count = 0
    chunks: List[Chunk] = []
    with pymupdf.open(stream=file_data, filetype="pdf") as pdf:
        if pdf.needs_pass:
            raise ValueError("Password-protected PDFs are not supported.")
        for page_num, page in enumerate(pdf):
            word_count += len(page.get_text("words"))
            blocks = [block[4] for block in page.get_text("blocks") if block[6] == 0]
            chunks.extend(generate_embeddings(group_blocks(blocks), page_num))
        return len(pdf), word_count, chunks


def upload_document(file_data: bytes, filename: str, repo_id: str, owner_id: str, title: str = None,
                    description: str = "", category: str = None) -> Tuple[str, int]:
    """Store a PDF, index its text, and add it to the repository.

    Returns (doc_id, number_of_indexed_chunks). Raises ValueError on invalid input.
    """
    if not filename.lower().endswith('.pdf'):
        raise ValueError("Only PDF files are supported.")
    if len(file_data) > MAX_DOCUMENT_SIZE:
        raise ValueError("The file is too large (max 10 MB).")
    try:
        page_count, word_count, chunks = extract_pdf(file_data)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"This file could not be read as a PDF ({e}).") from e
    db = get_db()
    doc_id = str(uuid.uuid4())
    storage_path = f"documents/{owner_id}/{doc_id}.pdf"
    db.storage.from_('documents').upload(
        path=f"{owner_id}/{doc_id}.pdf",
        file=file_data,
        file_options={"content-type": "application/pdf"}
    )
    doc = Document(
        title=title or os.path.splitext(filename)[0],
        doc_id=doc_id,
        page_count=page_count,
        word_count=word_count,
        file_size=len(file_data),
        file_path=storage_path,
        owner_id=owner_id,
        original_repo=repo_id,
        description=description,
        category=category
    )
    db.table('documents').insert(doc.model_dump()).execute()
    rows = [{
        'chunk_id': f"doc_{doc_id}_chunk_{i}",
        'document_id': doc_id,
        'position': chunk.position,
        'page': chunk.page,
        'text': chunk.text,
        'embedding': chunk.embedding
    } for i, chunk in enumerate(chunks)]
    for i in range(0, len(rows), 200):
        db.table('chunks').insert(rows[i:i + 200]).execute()
    res_repo = db.table('document_repositories').select('documents').eq('repo_id', repo_id).limit(1).execute()
    current = (res_repo.data[0]['documents'] or []) if res_repo.data else []
    db.table('document_repositories').update({'documents': current + [doc_id], 'updated_at': now_iso()}) \
        .eq('repo_id', repo_id).execute()
    return doc_id, len(chunks)


def update_document(doc_id: str, title: str = None, description: str = None,
                    category: str = None, related_documents: List[str] = None, is_deleted: bool = None) -> bool:
    update_data = {}
    if title:
        update_data['title'] = title
    if description is not None:
        update_data['description'] = description
    if category is not None:
        update_data['category'] = category or None
    if related_documents is not None:
        update_data['related_documents'] = related_documents
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if not update_data:
        return False
    update_response = get_db().table('documents').update(update_data).eq('doc_id', doc_id).execute()
    return len(update_response.data) > 0


def _document_from_row(doc_data: Dict[str, Any]) -> Document:
    data = {k: v for k, v in doc_data.items() if v is not None and k in Document.model_fields}
    return Document(**data)


def get_document(doc_id: str) -> Optional[Document]:
    response = get_db().table('documents').select('*').eq('doc_id', doc_id).eq('is_deleted', False).limit(1).execute()
    return _document_from_row(response.data[0]) if response.data else None


def get_list_of_documents(doc_ids: List[str]) -> List[Document]:
    if not doc_ids:
        return []
    response = get_db().table('documents').select('*').in_('doc_id', doc_ids).eq('is_deleted', False).execute()
    by_id = {row['doc_id']: _document_from_row(row) for row in response.data or []}
    return [by_id[d] for d in doc_ids if d in by_id]


@st.cache_data(ttl=600, show_spinner=False)
def get_owner_name(user_id: str) -> Optional[str]:
    response = get_db().table('users').select('username').eq('user_id', user_id).limit(1).execute()
    return response.data[0]['username'] if response.data else None


@st.cache_data(ttl=600, show_spinner=False)
def get_original_repo(repo_id: str) -> Optional[str]:
    response = get_db().table('document_repositories').select('name').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
    return response.data[0]['name'] if response.data else None
