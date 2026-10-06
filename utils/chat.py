from typing import Any, Dict, List, Optional
import json
from utils.data import get_db
from model import Chunk, Message, ChatHistory


def _as_vector(value) -> List[float]:
    # pgvector columns come back as strings like "[0.1,0.2,...]"; json/float[] columns as lists.
    return json.loads(value) if isinstance(value, str) else value


def get_documents_embedding(document_ids: List[str]) -> List[Chunk]:
    if not document_ids:
        return []
    chunks = []
    page_size = 1000
    start = 0
    while True:
        response = get_db().table("chunks").select("text, embedding, page, position") \
            .in_("document_id", document_ids).range(start, start + page_size - 1).execute()
        rows = response.data or []
        chunks.extend(
            Chunk(text=row["text"], embedding=_as_vector(row["embedding"]), page=row["page"], position=row["position"])
            for row in rows
        )
        if len(rows) < page_size:
            return chunks
        start += page_size


def _append_id(table: str, key: str, key_value: str, column: str, new_id: str) -> None:
    db = get_db()
    response = db.table(table).select(column).eq(key, key_value).limit(1).execute()
    current = (response.data[0][column] or []) if response.data else []
    db.table(table).update({column: current + [new_id]}).eq(key, key_value).execute()


def create_chat_history(user_id: str, repo_id: str, type: str, title: str) -> str:
    chat = ChatHistory(title=title, owner_id=user_id, repo_source=repo_id, type=type)
    response = get_db().table("chat_histories").insert(chat.model_dump()).execute()
    if not response.data:
        raise Exception("Error while creating the chat history")
    _append_id('users', 'user_id', user_id, 'chat_histories', chat.chat_id)
    return chat.chat_id


def _history_from_row(chat_data: Dict[str, Any]) -> ChatHistory:
    return ChatHistory(
        chat_id=chat_data["chat_id"],
        owner_id=chat_data["owner_id"],
        messages=chat_data.get("messages") or [],
        is_deleted=chat_data["is_deleted"],
        created_at=chat_data["created_at"],
        last_message=Message(**chat_data["last_message"]) if chat_data.get("last_message") else None,
        title=chat_data["title"],
        repo_source=chat_data["repo_source"],
        type=chat_data["type"],
        mode=chat_data.get("mode") or False
    )


def get_chat_history(chat_id: str) -> Optional[ChatHistory]:
    response = get_db().table("chat_histories").select("*").eq("chat_id", chat_id).eq('is_deleted', False).limit(1).execute()
    return _history_from_row(response.data[0]) if response.data else None


def get_user_histories(chat_ids: List[str]) -> List[ChatHistory]:
    if not chat_ids:
        return []
    response = get_db().table("chat_histories").select("*").in_("chat_id", chat_ids) \
        .eq('is_deleted', False).order("created_at", desc=True).execute()
    return [_history_from_row(row) for row in response.data or []]


def update_chat_history(chat_id: str, title: str = None, is_deleted: bool = None, mode: bool = None) -> bool:
    update_data = {}
    if title:
        update_data['title'] = title
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if mode is not None:
        update_data['mode'] = mode
    if not update_data:
        return False
    response = get_db().table('chat_histories').update(update_data).eq('chat_id', chat_id).execute()
    return len(response.data) > 0


def create_message(chat_id: str, content: str, is_assistant: bool) -> str:
    message = Message(chat_id=chat_id, content=content, is_assistant=is_assistant)
    message_data = message.model_dump()
    db = get_db()
    response = db.table("messages").insert(message_data).execute()
    if not response.data:
        raise Exception("Error while creating the message")
    res_chat = db.table('chat_histories').select('messages').eq('chat_id', chat_id).limit(1).execute()
    current = (res_chat.data[0]['messages'] or []) if res_chat.data else []
    db.table('chat_histories').update({'messages': current + [message.message_id], 'last_message': message_data}) \
        .eq('chat_id', chat_id).execute()
    return message.message_id


def get_message(message_id: str) -> Optional[Message]:
    response = get_db().table("messages").select("*").eq("message_id", message_id).eq('is_deleted', False).limit(1).execute()
    return Message(**response.data[0]) if response.data else None


def get_chat_messages(message_ids: List[str]) -> List[Message]:
    if not message_ids:
        return []
    by_id = {}
    # Batched so long conversations don't overflow the request URL.
    for i in range(0, len(message_ids), 100):
        response = get_db().table("messages").select("*").in_("message_id", message_ids[i:i + 100]) \
            .eq('is_deleted', False).execute()
        by_id.update({row["message_id"]: Message(**row) for row in response.data or []})
    # Keep the conversation order stored on the chat history.
    return [by_id[mid] for mid in message_ids if mid in by_id]


def update_message(message_id: str, is_deleted: bool = None, score: Dict[str, Any] = None) -> bool:
    update_data = {}
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if score:
        update_data['score'] = score
    if not update_data:
        return False
    response = get_db().table('messages').update(update_data).eq('message_id', message_id).execute()
    return len(response.data) > 0
