import streamlit as st
import google.generativeai as genai
from typing import List, Optional, Tuple

from model import Message, Chunk, ChatHistory
from utils.embedding import best_matchs
from utils.chat import add_message_to_chat_history, get_chat_history, get_documents_embedding

# Remplace 'TA_CLE_API' par ta clé API Gemini
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# Modèle à utiliser
MODEL_NAME = "gemini-2.0-flash"

# Nombre de chunks à récupérer pour le contexte
DEFAULT_CHUNK_COUNT = 5

# Système de prompts
PROMPTS = {
    "qa": """Tu es un assistant intelligent spécialisé dans la réponse aux questions des utilisateurs.
    Utilise les informations contextuelles fournies ci-dessous pour répondre à la question de l'utilisateur.
    Si tu ne trouves pas la réponse dans le contexte, indique-le clairement et suggère d'autres pistes.
    Réponds de manière concise, claire et précise.
    
    Contexte:
    {context}
    
    Question de l'utilisateur: {user_question}
    """,
    
    "course": """Tu es un professeur expert qui va créer un cours.
    Utilise les informations fournies ci-dessous pour générer un cours structuré et pédagogique.
    Le cours doit être organisé avec une introduction, des parties principales, et une conclusion.
    Inclus des exemples pratiques pour illustrer les concepts présentés.
    
    Contenu de référence:
    {context}
    
    Thème du cours: {topic}
    """,
    
    "exercise": """Tu es un formateur qui crée des exercices pratiques.
    Utilise les informations fournies ci-dessous pour générer un exercice pertinent.
    L'exercice doit tester la compréhension et l'application des concepts.
    Inclus l'énoncé, des instructions claires, et les réponses attendues.
    
    Contenu de référence:
    {context}
    
    Demande d'exercice: {exercise_request}
    """
}

def initialize_gemini_model():
    """
    Initialise et retourne une instance du modèle gemini-2.0-flash
    
    Returns:
        Instance du modèle gemini-2.0-flash
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        return model
    except Exception as e:
        print(f"Erreur lors de l'initialisation du modèle : {e}")
        return None

def create_chat_session(history: Optional[ChatHistory] = None) -> genai.ChatSession:
    """
    Crée une session de chat avec le modèle gemini-2.0-flash en intégrant l'historique existant
    
    Args:
        history: Historique de conversation existant (optionnel)
        
    Returns:
        Une session de chat Gemini
    """
    model = initialize_gemini_model()
    if not model:
        raise Exception("Impossible d'initialiser le modèle gemini")
    
    # Configuration de la session de chat
    chat = model.start_chat(history=[])
    
    # Ajout de l'historique s'il existe
    if history and history.messages:
        for msg in history.messages:
            if not msg.is_deleted:
                if msg.is_assistant:
                    chat.history.append({"role": "model", "parts": [msg.content]})
                else:
                    chat.history.append({"role": "user", "parts": [msg.content]})
    
    return chat

def get_context_from_chunks(chunks: List[Chunk], max_chunks: int = DEFAULT_CHUNK_COUNT) -> str:
    """
    Extrait le texte des chunks et le formate pour le contexte
    
    Args:
        chunks: Liste de chunks triés par pertinence
        max_chunks: Nombre maximum de chunks à inclure
        
    Returns:
        Texte formaté pour le contexte
    """
    context_chunks = chunks[:max_chunks]
    context_text = "\n\n---\n\n".join([f"Page {c.page}, Position {c.position}: {c.text}" for c in context_chunks])
    return context_text

def qa_chat(chat_id: str, user_message: str, document_ids: List[str]) -> Tuple[str, bool]:
    """
    Gère un chat de type question-réponse
    
    Args:
        chat_id: Identifiant de l'historique de chat
        user_message: Message de l'utilisateur
        document_ids: Liste des identifiants de documents à consulter
        
    Returns:
        Tuple contenant (réponse du modèle, succès de l'opération)
    """
    try:
        # Récupération de l'historique
        history = get_chat_history(chat_id)
        if not history:
            return "Historique de chat non trouvé", False
        
        # Ajout du message utilisateur à l'historique
        user_msg = Message(content=user_message, is_assistant=False)
        add_message_to_chat_history(chat_id, user_msg)
        
        # Récupération des embeddings des documents
        chunks = get_documents_embedding(document_ids)
        
        # Recherche des meilleurs chunks correspondant à la question
        relevant_chunks = best_matchs(user_message, chunks)
        
        # Création du contexte
        context = get_context_from_chunks(relevant_chunks)
        
        # Préparation du prompt
        prompt = PROMPTS["qa"].format(context=context, user_question=user_message)
        
        # Création de la session de chat
        chat_session = create_chat_session(history)
        
        # Envoi du prompt au modèle
        response = chat_session.send_message(prompt)
        
        # Extraction de la réponse
        model_response = response.text
        
        # Ajout de la réponse à l'historique
        assistant_msg = Message(content=model_response, is_assistant=True)
        add_message_to_chat_history(chat_id, assistant_msg)
        
        return model_response, True
    
    except Exception as e:
        print(f"Erreur dans le chat QA : {e}")
        return f"Une erreur est survenue : {str(e)}", False

def course_chat(chat_id: str, topic: str, document_ids: List[str], page_number: Optional[int] = None) -> Tuple[str, bool]:
    """
    Génère un cours basé sur des chunks d'une même page
    
    Args:
        chat_id: Identifiant de l'historique de chat
        topic: Thème du cours demandé
        document_ids: Liste des identifiants de documents à consulter
        page_number: Numéro de page spécifique (optionnel)
        
    Returns:
        Tuple contenant (cours généré, succès de l'opération)
    """
    try:
        # Récupération de l'historique
        history = get_chat_history(chat_id)
        if not history:
            return "Historique de chat non trouvé", False
        
        # Ajout de la demande de cours à l'historique
        user_msg = Message(content=f"Génère un cours sur: {topic}")
        add_message_to_chat_history(chat_id, user_msg)
        
        # Récupération des embeddings des documents
        chunks = get_documents_embedding(document_ids)
        
        # Filtrage par page si spécifié
        if page_number is not None:
            chunks = [chunk for chunk in chunks if chunk.page == page_number]
        
        # Recherche des meilleurs chunks correspondant au thème
        relevant_chunks = best_matchs(topic, chunks)
        
        # Création du contexte
        context = get_context_from_chunks(relevant_chunks, max_chunks=10)  # Plus de chunks pour un cours
        
        # Préparation du prompt
        prompt = PROMPTS["course"].format(context=context, topic=topic)
        
        # Création de la session de chat
        chat_session = create_chat_session(history)
        
        # Envoi du prompt au modèle
        response = chat_session.send_message(prompt)
        
        # Extraction de la réponse
        course_content = response.text
        
        # Ajout du cours à l'historique
        assistant_msg = Message(content=course_content, is_assistant=True)
        add_message_to_chat_history(chat_id, assistant_msg)
        
        return course_content, True
    
    except Exception as e:
        print(f"Erreur dans la génération du cours : {e}")
        return f"Une erreur est survenue : {str(e)}", False

def exercise_chat(chat_id: str, exercise_request: str, document_ids: List[str], count: int = 3) -> Tuple[str, bool]:
    """
    Génère des exercices basés sur des chunks choisis au hasard
    
    Args:
        chat_id: Identifiant de l'historique de chat
        exercise_request: Type d'exercice demandé
        document_ids: Liste des identifiants de documents à consulter
        count: Nombre d'exercices à générer
        
    Returns:
        Tuple contenant (exercices générés, succès de l'opération)
    """
    try:
        # Récupération de l'historique
        history = get_chat_history(chat_id)
        if not history:
            return "Historique de chat non trouvé", False
        
        # Ajout de la demande d'exercice à l'historique
        user_msg = Message(content=f"Génère {count} exercices sur: {exercise_request}")
        add_message_to_chat_history(chat_id, user_msg)
        
        # Récupération des embeddings des documents
        chunks = get_documents_embedding(document_ids)
        
        # Recherche des meilleurs chunks correspondant à la demande
        relevant_chunks = best_matchs(exercise_request, chunks)
        
        # Création du contexte
        context = get_context_from_chunks(relevant_chunks, max_chunks=count*2)  # Plus de chunks pour varier les exercices
        
        # Préparation du prompt
        prompt = PROMPTS["exercise"].format(
            context=context, 
            exercise_request=f"{exercise_request} (génère {count} exercices différents)"
        )
        
        # Création de la session de chat
        chat_session = create_chat_session(history)
        
        # Envoi du prompt au modèle
        response = chat_session.send_message(prompt)
        
        # Extraction de la réponse
        exercises_content = response.text
        
        # Ajout des exercices à l'historique
        assistant_msg = Message(content=exercises_content, is_assistant=True)
        add_message_to_chat_history(chat_id, assistant_msg)
        
        return exercises_content, True
    
    except Exception as e:
        print(f"Erreur dans la génération des exercices : {e}")
        return f"Une erreur est survenue : {str(e)}", False

def evaluate_exercise_response(chat_id: str, user_response: str, exercise_content: str) -> Tuple[str, bool]:
    """
    Évalue la réponse de l'utilisateur à un exercice
    
    Args:
        chat_id: Identifiant de l'historique de chat
        user_response: Réponse de l'utilisateur
        exercise_content: Contenu de l'exercice original
        
    Returns:
        Tuple contenant (évaluation de la réponse, succès de l'opération)
    """
    try:
        # Récupération de l'historique
        history = get_chat_history(chat_id)
        if not history:
            return "Historique de chat non trouvé", False
        
        # Ajout de la réponse de l'utilisateur à l'historique
        user_msg = Message(content=user_response, is_assistant=False)
        add_message_to_chat_history(chat_id, user_msg)
        
        # Préparation du prompt pour l'évaluation
        evaluation_prompt = f"""
        Tu es un évaluateur d'exercices précis et pédagogique.
        Voici l'exercice original:
        
        {exercise_content}
        
        Voici la réponse de l'utilisateur:
        
        {user_response}
        
        Évalue cette réponse en fournissant:
        1. Si la réponse est correcte ou non
        2. Les points forts et les points faibles
        3. Des suggestions d'amélioration
        4. Une correction si nécessaire
        """
        
        # Création de la session de chat
        chat_session = create_chat_session(history)
        
        # Envoi du prompt d'évaluation au modèle
        response = chat_session.send_message(evaluation_prompt)
        
        # Extraction de l'évaluation
        evaluation = response.text
        
        # Ajout de l'évaluation à l'historique
        assistant_msg = Message(content=evaluation, is_assistant=True)
        add_message_to_chat_history(chat_id, assistant_msg)
        
        return evaluation, True
    
    except Exception as e:
        print(f"Erreur dans l'évaluation de l'exercice : {e}")
        return f"Une erreur est survenue : {str(e)}", False

def handle_follow_up_question(chat_id: str, user_message: str, document_ids: List[str]) -> Tuple[str, bool]:
    """
    Gère une question de suivi dans un chat existant
    
    Args:
        chat_id: Identifiant de l'historique de chat
        user_message: Question de suivi de l'utilisateur
        document_ids: Liste des identifiants de documents à consulter
        
    Returns:
        Tuple contenant (réponse du modèle, succès de l'opération)
    """
    try:
        # Récupération de l'historique complet
        history = get_chat_history(chat_id)
        if not history:
            return "Historique de chat non trouvé", False
        
        # Ajout du message utilisateur à l'historique
        user_msg = Message(content=user_message, is_assistant=False)
        add_message_to_chat_history(chat_id, user_msg)
        
        # Récupération des embeddings des documents
        chunks = get_documents_embedding(document_ids)
        
        # Recherche des meilleurs chunks correspondant à la question
        relevant_chunks = best_matchs(user_message, chunks)
        
        # Création du contexte
        context = get_context_from_chunks(relevant_chunks)
        
        # Création de la session de chat qui contient déjà l'historique
        chat_session = create_chat_session(history)
        
        # Préparation du prompt contextualisé
        prompt = f"""
        Voici des informations supplémentaires qui pourraient t'aider à répondre à la question:
        
        {context}
        
        La question de suivi est: {user_message}
        
        Réponds en tenant compte de toute la conversation précédente.
        """
        
        # Envoi du prompt au modèle
        response = chat_session.send_message(prompt)
        
        # Extraction de la réponse
        model_response = response.text
        
        # Ajout de la réponse à l'historique
        assistant_msg = Message(content=model_response, is_assistant=True)
        add_message_to_chat_history(chat_id, assistant_msg)
        
        return model_response, True
    
    except Exception as e:
        print(f"Erreur dans la gestion de la question de suivi : {e}")
        return f"Une erreur est survenue : {str(e)}", False