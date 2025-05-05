import streamlit as st
from datetime import datetime
from typing import List

from utils.chat import create_chat_history, get_chat_history, get_user_histories, update_chat_history, add_message_to_chat_history
from model import ChatHistory
from utils.llm import qa_chat, course_chat, exercise_chat, evaluate_exercise_response, handle_follow_up_question

# Constantes pour les types de chat
CHAT_TYPES = {
    "qa": "Questions & Réponses",
    "course": "Cours",
    "exercise": "Exercices"
}

def display_chats():
    """
    Affiche l'interface de chat et gère la communication entre l'utilisateur et le LLM
    """
    st.title("Discussions avec l'IA")
    
    # Vérification des données de session nécessaires
    if 'user' not in st.session_state or 'repo' not in st.session_state:
        st.error("Vous devez être connecté et avoir sélectionné un répertoire pour accéder aux chats.")
        return
    
    user_id = st.session_state['user'].user_id
    repo_id = st.session_state['repo'].repo_id
    documents = st.session_state['repo'].documents
    
    # Initialisation de l'état de la session pour les chats
    if 'chat_histories' not in st.session_state:
        st.session_state['chat_histories'] = []
    
    if 'current_chat_id' not in st.session_state:
        st.session_state['current_chat_id'] = None
    
    # Sidebar pour la gestion des chats
    with st.expander("Mes conversations"):
        
        # Bouton pour créer un nouveau chat
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("➕ Q&R", key="new_qa"):
                chat_id = create_chat_history(user_id, repo_id, type="qa")
                if chat_id:
                    update_chat_history(chat_id, title="Nouvelle Q&R", messages=[])
                    st.session_state['current_chat_id'] = chat_id
                    st.session_state['chat_type'] = "qa"
                    st.session_state['chat_histories'] = []  # Forcer rechargement
                    st.rerun()
        
        with col2:
            if st.button("➕ Cours", key="new_course"):
                chat_id = create_chat_history(user_id, repo_id, type="course")
                if chat_id:
                    update_chat_history(chat_id, title="Nouveau Cours", messages=[])
                    st.session_state['current_chat_id'] = chat_id
                    st.session_state['chat_type'] = "course"
                    st.session_state['chat_histories'] = []  # Forcer rechargement
                    st.rerun()
        
        with col3:
            if st.button("➕ Exercices", key="new_exercise"):
                chat_id = create_chat_history(user_id, repo_id, type="exercise")
                if chat_id:
                    update_chat_history(chat_id, title="Nouveaux Exercices", messages=[])
                    st.session_state['current_chat_id'] = chat_id
                    st.session_state['chat_type'] = "exercise"
                    st.session_state['chat_histories'] = []  # Forcer rechargement
                    st.rerun()
        
        st.divider()
        
        # Récupération des historiques de chat de l'utilisateur
        if not st.session_state['chat_histories']:
            # Récupérer les IDs de chat depuis la base de données
            # (Cette partie dépend de votre implémentation exacte)
            chat_ids = []  # À remplacer par la vraie requête pour obtenir les IDs
            
            # Récupération des historiques complets
            if chat_ids:
                st.session_state['chat_histories'] = get_user_histories(chat_ids)
        
        # Affichage des chats existants sous forme de boutons cliquables
        if st.session_state['chat_histories']:
            for history in st.session_state['chat_histories']:
                if not history.is_deleted:
                    # Déterminer le type de chat basé sur le titre ou autre métadonnée
                    chat_type = "qa"  # Par défaut
                    if "Cours" in history.title:
                        chat_type = "course"
                    elif "Exercice" in history.title:
                        chat_type = "exercise"
                    
                    if st.button(
                        f"{history.title} ({datetime.fromisoformat(history.created_at).strftime('%d/%m/%Y')})",
                        key=f"chat_{history.chat_id}"
                    ):
                        st.session_state['current_chat_id'] = history.chat_id
                        st.session_state['chat_type'] = chat_type
                        st.rerun()
        else:
            st.info("Aucune conversation trouvée. Créez votre première conversation!")
    
    # Zone principale pour l'affichage du chat actuel
    if st.session_state['current_chat_id']:
        chat_history = get_chat_history(st.session_state['current_chat_id'])
        
        if not chat_history:
            st.error("Impossible de charger l'historique de chat.")
            return
        
        # Affichage du titre du chat avec option de modification
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                new_title = st.text_input("Titre de la conversation", 
                                     value=chat_history.title, 
                                     key="chat_title")
                if new_title != chat_history.title:
                    update_chat_history(chat_history.chat_id, title=new_title)
                    st.session_state['chat_histories'] = []  # Forcer rechargement
            
            with col2:
                chat_type = st.session_state.get('chat_type', "qa")
                st.caption(f"Type: {CHAT_TYPES.get(chat_type, 'Inconnu')}")
        
        st.divider()
        
        # Affichage des messages existants
        chat_container = st.container()
        with chat_container:
            for msg in chat_history.messages:
                if not msg.is_deleted:
                    if msg.is_assistant:
                        st.chat_message("assistant").markdown(msg.content)
                    else:
                        st.chat_message("user").markdown(msg.content)
        
        # Zone de saisie pour le nouveau message
        st.divider()
        
        # Interface spécifique selon le type de chat
        chat_type = st.session_state.get('chat_type', "qa")
        
        if chat_type == "qa":
            display_qa_interface(chat_history, documents)
        elif chat_type == "course":
            display_course_interface(chat_history, documents)
        elif chat_type == "exercise":
            display_exercise_interface(chat_history, documents)
    else:
        st.info("Sélectionnez une conversation existante ou créez-en une nouvelle pour commencer.")

def display_qa_interface(chat_history: ChatHistory, document_ids: List[str]):
    """
    Affiche l'interface pour le chat de type question-réponse
    """
    user_message = st.chat_input("Posez votre question...")
    if user_message:
        # Affichage du message de l'utilisateur
        st.chat_message("user").markdown(user_message)
        
        # Affichage d'un placeholder pour la réponse en cours
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ Recherche de la réponse...")
            
            # Appel à l'API LLM
            has_context = len(chat_history.messages) > 0
            if has_context:
                response, success = handle_follow_up_question(
                    chat_history.chat_id, 
                    user_message, 
                    document_ids
                )
            else:
                response, success = qa_chat(
                    chat_history.chat_id, 
                    user_message, 
                    document_ids
                )
            
            if success:
                message_placeholder.markdown(response)
            else:
                message_placeholder.markdown("❌ " + response)
        
        # Rechargement de la page pour afficher les nouveaux messages
        st.rerun()

def display_course_interface(chat_history: ChatHistory, document_ids: List[str]):
    """
    Affiche l'interface pour la génération de cours
    """
    if len(chat_history.messages) == 0:
        with st.form("course_form"):
            topic = st.text_input("Sujet du cours", placeholder="Ex: Introduction à Python, Révolution française...")
            
            col1, col2 = st.columns(2)
            with col1:
                use_specific_page = st.checkbox("Utiliser une page spécifique")
            
            with col2:
                page_number = None
                if use_specific_page:
                    page_number = st.number_input("Numéro de page", min_value=1, value=1)
            
            if st.form_submit_button("Générer le cours"):
                if topic:
                    with st.chat_message("user"):
                        st.markdown(f"Génération d'un cours sur: **{topic}**")
                    
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("⏳ Génération du cours en cours...")
                        
                        response, success = course_chat(
                            chat_history.chat_id,
                            topic,
                            document_ids,
                            page_number=page_number if use_specific_page else None
                        )
                        
                        if success:
                            placeholder.markdown(response)
                        else:
                            placeholder.markdown("❌ " + response)
                    
                    st.rerun()
                else:
                    st.error("Veuillez spécifier un sujet pour le cours")
    else:
        # Si un cours existe déjà, permettre de poser des questions dessus
        user_message = st.chat_input("Posez une question sur ce cours...")
        if user_message:
            st.chat_message("user").markdown(user_message)
            
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("⏳ Recherche de la réponse...")
                
                response, success = handle_follow_up_question(
                    chat_history.chat_id,
                    user_message,
                    document_ids
                )
                
                if success:
                    placeholder.markdown(response)
                else:
                    placeholder.markdown("❌ " + response)
            
            st.rerun()

def display_exercise_interface(chat_history: ChatHistory, document_ids: List[str]):
    """
    Affiche l'interface pour la génération et la réponse aux exercices
    """
    # Vérifier si nous avons déjà des exercices générés
    has_exercises = False
    for msg in chat_history.messages:
        if msg.is_assistant and not msg.is_deleted:
            has_exercises = True
            break
    
    if not has_exercises:
        # Interface pour générer de nouveaux exercices
        with st.form("exercise_form"):
            topic = st.text_input("Sujet des exercices", placeholder="Ex: Variables en Python, Équations du second degré...")
            num_exercises = st.slider("Nombre d'exercices", min_value=1, max_value=5, value=3)
            
            if st.form_submit_button("Générer les exercices"):
                if topic:
                    with st.chat_message("user"):
                        st.markdown(f"Génération de {num_exercises} exercices sur: **{topic}**")
                    
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("⏳ Génération des exercices en cours...")
                        
                        response, success = exercise_chat(
                            chat_history.chat_id,
                            topic,
                            document_ids,
                            count=num_exercises
                        )
                        
                        if success:
                            placeholder.markdown(response)
                        else:
                            placeholder.markdown("❌ " + response)
                    
                    st.rerun()
                else:
                    st.error("Veuillez spécifier un sujet pour les exercices")
    else:
        # Interface pour répondre aux exercices
        with st.form("exercise_response_form"):
            user_response = st.text_area("Votre réponse aux exercices", height=150)
            
            if st.form_submit_button("Soumettre la réponse"):
                if user_response:
                    st.chat_message("user").markdown(user_response)
                    
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("⏳ Évaluation de votre réponse...")
                        
                        # Récupérer le dernier message d'exercice pour l'évaluation
                        last_exercise = None
                        for msg in reversed(chat_history.messages):
                            if msg.is_assistant and not msg.is_deleted:
                                last_exercise = msg.content
                                break
                        
                        if last_exercise:
                            response, success = evaluate_exercise_response(
                                chat_history.chat_id,
                                user_response,
                                last_exercise
                            )
                            
                            if success:
                                placeholder.markdown(response)
                            else:
                                placeholder.markdown("❌ " + response)
                        else:
                            placeholder.markdown("❌ Impossible de trouver l'exercice original pour l'évaluation")
                    
                    st.rerun()
                else:
                    st.error("Veuillez entrer votre réponse avant de la soumettre")
        
        # Option pour générer de nouveaux exercices
        if st.button("Générer de nouveaux exercices", key="new_exercises_btn"):
            st.session_state['current_chat_id'] = None
            st.rerun()