from typing import Any, Dict, List, Optional
import uuid
from utils.data import initialize_supabase
from model import Chunk, Message, ChatHistory

db = initialize_supabase()

def get_documents_embedding(document_ids: List[str]) -> List[Chunk]:
    chunk = []
    for document_id in document_ids:
        response = db.table("chunks").select("*").eq("document_id", document_id).execute()
        if response.data:
            for item in response.data:
                chunk.append(Chunk(
                    text=item["text"],
                    embedding=item["embedding"],
                    page=item["page"],
                    position=item["position"]
                ))
    return chunk

def create_chat_history(user_id: str, repo_id: str, type: str, title: str) -> str:
    chat_id = str(uuid.uuid4())
    chat = ChatHistory(
        chat_id=chat_id,
        title=title,
        owner_id=user_id,
        repo_source=repo_id,
        type=type
    )
    chat_data = chat.dict()
    response = db.table("chat_histories").insert(chat_data).execute()
    res_user = db.table('users').select('chat_histories').eq('user_id', user_id).limit(1).execute()
    current_docs = res_user.data[0]['chat_histories']
    updated_docs = current_docs + [chat_id]
    db.table('users').update({'chat_histories': updated_docs}).eq('user_id', user_id).execute()
    if len(response.data) > 0:
        return chat_id
    else:
        raise Exception("Error while creating the chat history")
    
def get_chat_history(chat_id: str) -> Optional[ChatHistory]:
    response = db.table("chat_histories").select("*").eq("chat_id", chat_id).eq('is_deleted', False).limit(1).execute()
    if not response.data or len(response.data) == 0:
        return None
    chat_data = response.data[0]
    return ChatHistory(
        chat_id=chat_data["chat_id"],
        owner_id=chat_data["owner_id"],
        messages=chat_data["messages"],
        is_deleted=chat_data["is_deleted"],
        created_at=chat_data["created_at"],
        last_message=Message(**chat_data["last_message"]) if chat_data["last_message"] else None,
        title=chat_data["title"],
        repo_source=chat_data["repo_source"],
        type=chat_data["type"],
        mode=chat_data["mode"]
    ) if chat_data else None
    
def get_user_histories(chat_ids: List[str]) -> List[ChatHistory]:
    histories = []
    for chat_id in chat_ids:
        history = get_chat_history(chat_id)
        if history:
            histories.append(history)
    return histories
    
def update_chat_history(chat_id: str, title: str = None, is_deleted: bool = None, mode: bool = None) -> bool:
    response = db.table('chat_histories').select('*').eq('chat_id', chat_id).limit(1).execute()
    if not response.data or len(response.data) == 0:
        return False
    update_data = {}
    if title:
        update_data['title'] = title
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if mode is not None:
        update_data['mode'] = mode
    response = db.table('chat_histories').update(update_data).eq('chat_id', chat_id).execute()
    return len(response.data) > 0

def create_message(chat_id: str, content: str, is_assistant: bool) -> str:
    message_id = str(uuid.uuid4())
    message = Message(
        message_id=message_id,
        chat_id=chat_id,
        content=content,
        is_assistant=is_assistant
    )
    message_data = message.dict()
    response = db.table("messages").insert(message_data).execute()
    res_chat = db.table('chat_histories').select('messages').eq('chat_id', chat_id).limit(1).execute()
    current_docs = res_chat.data[0]['messages']
    updated_docs = current_docs + [message_id]
    db.table('chat_histories').update({'messages': updated_docs, 'last_message': message_data}).eq('chat_id', chat_id).execute()
    if len(response.data) > 0:
        return message_id
    else:
        raise Exception("Error while creating the message")
    
def get_message(message_id: str) -> Optional[Message]:
    response = db.table("messages").select("*").eq("message_id", message_id).eq('is_deleted', False).limit(1).execute()
    if not response.data or len(response.data) == 0:
        return None
    message_data = response.data[0]
    return Message(
        message_id=message_data["message_id"],
        chat_id=message_data["chat_id"],
        content=message_data["content"],
        is_assistant=message_data["is_assistant"],
        is_deleted=message_data["is_deleted"],
        received_at=message_data["received_at"],
        score=message_data["score"]
    ) if message_data else None
    
def get_chat_messages(message_ids: List[str]) -> List[Message]:
    messages = []
    for message_id in message_ids:
        message = get_message(message_id)
        if message:
            messages.append(message)
    return messages
    
def update_message(message_id: str, is_deleted: bool = None, score: Dict[str, Any] = None) -> bool:
    response = db.table('messages').select('*').eq('message_id', message_id).limit(1).execute()
    if not response.data or len(response.data) == 0:
        return False
    update_data = {}
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if score:
        update_data['score'] = score
    response = db.table('messages').update(update_data).eq('message_id', message_id).execute()
    return len(response.data) > 0