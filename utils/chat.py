from typing import List, Optional
import uuid
from utils.data import initialize_supabase
from model import Chunk, Message, ChatHistory

db = initialize_supabase()

def get_documents_embedding(document_ids: List[str]) -> List[Chunk]:
    """
    Récupère l'embedding d'un document à partir de la base de données Supabase.

    Args:
        document_id (str): L'ID du document dont on veut récupérer l'embedding.

    Returns:
        list: L'embedding du document.
    """
    
    chunk = []
    # Requête pour récupérer l'embedding du document
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

def create_chat_history(user_id: str, repo_id: str, type: str) -> str:
    """
    Crée un historique de chat pour un utilisateur donné et un document spécifique.

    Args:
        user_id (str): L'ID de l'utilisateur.
        document_id (str): L'ID du document.

    Returns:
        ChatHistory: Un objet ChatHistory contenant l'historique du chat.
    """
    
    # Requête pour récupérer l'historique de chat
    chat_id = str(uuid.uuid4())
    
    chat = ChatHistory(
        chat_id=chat_id,
        owner_id=user_id,
        repo_source=repo_id,
        type=type
    )
    
    chat_data = chat.dict()
    
    response = db.table("chat_histories").insert(chat_data).execute()
    
    res_user = db.table('users').select('chat_histories').eq('user_id', user_id).limit(1).execute()
    
    current_docs = res_user.data[0]['chat_histories']
    updated_docs = current_docs + [chat_id]  # Crée une NOUVELLE liste
    
    db.table('users').update({'chat_histories': updated_docs}).eq('user_id', user_id).execute()
    
    # Vérifier si l'insertion a réussi
    if len(response.data) > 0:
        return chat_id
    else:
        raise Exception("Erreur lors de la création du chat history")
    
def get_chat_history(chat_id: str) -> Optional[ChatHistory]:
    """
    Récupère l'historique de chat à partir de la base de données Supabase.

    Args:
        chat_id (str): L'ID du chat dont on veut récupérer l'historique.

    Returns:
        list: L'historique du chat.
    """
    
    # Requête pour récupérer l'historique de chat
    response = db.table("chat_histories").select("*").eq("chat_id", chat_id).eq('is_deleted', False).limit(1).execute()
    
    # Vérifier si des données ont été trouvées
    if not response.data or len(response.data) == 0:
        return None
    
    chat_data = response.data[0]
    
    return ChatHistory(
        chat_id=chat_data["chat_id"],
        owner_id=chat_data["owner_id"],
        messages=[Message(**message) for message in chat_data["messages"]],
        is_deleted=chat_data["is_deleted"],
        created_at=chat_data["created_at"],
        last_message=chat_data["last_message"],
        title=chat_data["title"],
        repo_source=chat_data["repo_source"],
        type=chat_data["type"]
    ) if chat_data else None
    
def get_user_histories(chat_ids: List[str]) -> List[ChatHistory]:
    """
    Récupère l'historique de chat d'un utilisateur donné.

    Args:
        user_id (str): L'ID de l'utilisateur.

    Returns:
        list: La liste des historiques de chat de l'utilisateur.
    """
    
    histories = []
    
    for chat_id in chat_ids:
        response = db.table('chat_histories').select('*').eq('chat_id', chat_id).eq('is_deleted', False).limit(1).execute()
    
        chat_data = response.data[0]
    
        history = ChatHistory(
        chat_id=chat_data["chat_id"],
        owner_id=chat_data["owner_id"],
        messages=[Message(**message) for message in chat_data["messages"]],
        is_deleted=chat_data["is_deleted"],
        created_at=chat_data["created_at"],
        last_message=chat_data["last_message"],
        title=chat_data["title"],
        repo_source=chat_data["repo_source"],
        type=chat_data["type"]
        )
        histories.append(history)
    
    return histories
    
def update_chat_history(chat_id: str, title: str = None, is_deleted: bool = None, messages: List[Message] = None) -> bool:
    """
    Met à jour l'historique de chat dans la base de données Supabase.

    Args:
        chat_id (str): L'ID du chat à mettre à jour.
        messages (list): La liste des messages à mettre à jour.
        last_message (str): Le dernier message du chat.
        title (str): Le titre du chat.

    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """
    
    response = db.table('chat_histories').select('*').eq('chat_id', chat_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return False
    
    update_data = {}
    if title:
        update_data['title'] = title
    if is_deleted is not None:
        update_data['is_deleted'] = is_deleted
    if messages:
        update_data['messages'] = [message.dict() for message in messages]
    
    # Mettre à jour les données dans Supabase
    response = db.table('chat_histories').update(update_data).eq('chat_id', chat_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(response.data) > 0

def add_message_to_chat_history(chat_id: str, message: Message) -> bool:
    """
    Ajoute un message à l'historique de chat dans la base de données Supabase.

    Args:
        chat_id (str): L'ID du chat auquel ajouter le message.
        message (Message): Le message à ajouter.

    Returns:
        bool: True si l'ajout a réussi, False sinon.
    """
    
    # Récupérer l'historique de chat existant
    response = db.table('chat_histories').select('*').eq('chat_id', chat_id).limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        return False
    
    # Ajouter le message à l'historique
    chat_data = response.data[0]
    messages = chat_data['messages']
    
    messages.append(message.dict())
    
    # Mettre à jour l'historique de chat avec le nouveau message
    response = db.table('chat_histories').update({'messages': messages}).eq('chat_id', chat_id).execute()
    
    # Vérifier si la mise à jour a réussi
    return len(response.data) > 0