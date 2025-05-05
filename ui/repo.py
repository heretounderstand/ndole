import streamlit as st

from model import Access
from utils.doc import (
    get_document,
    get_user_repositories, 
    create_document_repository,
    update_document,
    update_document_access,
    update_document_repository,
    upload_document,
    get_document_download_url,
    get_document_stats
)

def display_repositories():
    """
    Page Streamlit pour gérer les repositories de documents et leurs documents.
    Permet de créer, afficher, modifier et supprimer des repositories et documents.
    """
    documents = []
    st.title("Gestion des dépôts de documents")
    
    # Récupérer l'ID de l'utilisateur connecté
    user = st.session_state.get("user")
    if not user:
        st.warning("Vous devez être connecté pour accéder à cette page.")
        return
    
    # Récupérer les repositories de l'utilisateur
    user_repos = get_user_repositories(user.repositories)
    
    # Section pour créer un nouveau repository
    with st.expander("Créer un nouveau dépôt", expanded=False):
        with st.form("create_repo_form"):
            repo_name = st.text_input("Nom du dépôt")
            repo_description = st.text_area("Description")
            is_public = st.checkbox("Dépôt public", value=False)
            submit_button = st.form_submit_button("Créer le dépôt")
            
            if submit_button and repo_name:
                repo_id = create_document_repository(repo_name, repo_description, user.user_id)
                if repo_id:
                    # Mettre à jour le statut public si nécessaire
                    if is_public:
                        update_document_repository(repo_id, is_public=True)
                    st.success(f"Dépôt '{repo_name}' créé avec succès!")
                    st.rerun()  # Actualiser la page pour voir le nouveau dépôt
                else:
                    st.error("Erreur lors de la création du dépôt.")
    
    # Afficher et gérer les repositories existants
    if not user_repos:
        st.info("Vous n'avez pas encore de dépôts de documents. Créez-en un pour commencer!")
    else:
        # Sélecteur de repository
        repo_options = {repo.name: repo for repo in user_repos}
        selected_repo_name = st.selectbox("Sélectionner un dépôt", list(repo_options.keys()))
        selected_repo = repo_options[selected_repo_name]
        st.session_state["repo"] = selected_repo
        
        # Afficher les détails du repository
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(selected_repo.name)
            st.write(f"**Description:** {selected_repo.description if selected_repo.description else 'Aucune description'}")
            st.write(f"**Statut:** {'Public' if selected_repo.is_public else 'Privé'}")
            st.write(f"**Créé le:** {selected_repo.get_created_at().strftime('%d/%m/%Y')}")
            st.write(f"**Dernière modification:** {selected_repo.get_updated_at().strftime('%d/%m/%Y')}")
        
        with col2:
            # Statistiques du repository
            stats = get_document_stats(documents)
            st.metric("Documents", len(selected_repo.documents))
            if stats:
                # Afficher d'autres statistiques si disponibles
                pass
        
        # Boutons d'action pour le repository
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝 Modifier le dépôt"):
                st.session_state["edit_repo"] = selected_repo.repo_id
        with col2:
            delete_repo = st.button("🗑️ Supprimer le dépôt", type="primary", use_container_width=True)
            if delete_repo:
                confirm = st.button("Confirmer la suppression", type="primary")
                if confirm:
                    if update_document_repository(repo_id=selected_repo.repo_id, is_deleted=True):
                        st.success("Dépôt supprimé avec succès!")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la suppression du dépôt.")
        with col3:
            if st.button("📊 Voir les statistiques"):
                st.session_state["show_stats"] = selected_repo.repo_id
        
        # Formulaire pour modifier le repository (si demandé)
        if st.session_state.get("edit_repo") == selected_repo.repo_id:
            with st.form("edit_repo_form"):
                new_name = st.text_input("Nom du dépôt", value=selected_repo.name)
                new_description = st.text_area("Description", value=selected_repo.description)
                new_is_public = st.checkbox("Dépôt public", value=selected_repo.is_public)
                new_categories = st.multiselect("Catégories", options=selected_repo.categories or [], default=selected_repo.categories)
                
                update_button = st.form_submit_button("Mettre à jour")
                cancel_button = st.form_submit_button("Annuler")
                
                if update_button:
                    updated = update_document_repository(
                        selected_repo.repo_id,
                        name=new_name,
                        description=new_description,
                        is_public=new_is_public,
                        categories=new_categories
                    )
                    if updated:
                        st.success("Dépôt mis à jour avec succès!")
                        del st.session_state["edit_repo"]
                        st.rerun()
                    else:
                        st.error("Erreur lors de la mise à jour du dépôt.")
                
                if cancel_button:
                    del st.session_state["edit_repo"]
                    st.rerun()
        
        # Afficher les statistiques (si demandé)
        if st.session_state.get("show_stats") == selected_repo.repo_id:
            
            st.subheader("Statistiques du dépôt")
            stats = get_document_stats(documents)
            # Afficher les statistiques disponibles
            if st.button("Fermer les statistiques"):
                del st.session_state["show_stats"]
                st.rerun()
        
        # Section pour les documents du repository
        st.divider()
        st.subheader("Documents")
        
        # Section pour uploader un nouveau document
        with st.expander("Ajouter un document", expanded=False):
            uploaded_file = st.file_uploader("Choisir un fichier PDF", type="pdf")
            if uploaded_file is not None:
                with st.form("upload_doc_form"):
                    doc_title = st.text_input("Titre du document", value=uploaded_file.name)
                    doc_description = st.text_area("Description")
                    doc_category = st.selectbox("Catégorie", options=[""] + (selected_repo.categories or []))
                    
                    upload_button = st.form_submit_button("Télécharger")
                    if upload_button:
                        file_bytes = uploaded_file.getvalue()
                        doc_id = upload_document(file_bytes, uploaded_file.name, selected_repo.repo_id, user.user_id)
                        if doc_id:
                            # Mettre à jour les métadonnées du document
                            update_doc = update_document(
                                doc_id,
                                title=doc_title,
                                description=doc_description,
                                category=doc_category if doc_category else None,
                                is_index=True  # Indexer le document
                            )
                            if update_doc:
                                st.success(f"Document '{doc_title}' téléchargé et indexé avec succès!")
                                st.rerun()
                            else:
                                st.warning(f"Document téléchargé mais erreur lors de la mise à jour des métadonnées.")
                        else:
                            st.error("Erreur lors du téléchargement du document.")
        
        # Afficher les documents du repository
        if not selected_repo.documents:
            st.info("Ce dépôt ne contient pas encore de documents.")
        else:
            # Récupérer tous les documents du repository
            for doc_id in selected_repo.documents:
                doc = get_document(doc_id)
                if doc:
                    documents.append(doc)
            
            # Filtrage et tri des documents
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                search_term = st.text_input("Rechercher un document", placeholder="Titre ou description...")
            with filter_col2:
                sort_option = st.selectbox(
                    "Trier par", 
                    ["Date (récent d'abord)", "Date (ancien d'abord)", "Titre (A-Z)", "Titre (Z-A)", "Popularité"]
                )
            
            # Appliquer le filtrage
            if search_term:
                filtered_docs = [doc for doc in documents if search_term.lower() in doc.title.lower() or 
                                (doc.description and search_term.lower() in doc.description.lower())]
            else:
                filtered_docs = documents.copy()
            
            # Appliquer le tri
            if sort_option == "Date (récent d'abord)":
                filtered_docs.sort(key=lambda x: x.get_upload_date(), reverse=True)
            elif sort_option == "Date (ancien d'abord)":
                filtered_docs.sort(key=lambda x: x.get_upload_date())
            elif sort_option == "Titre (A-Z)":
                filtered_docs.sort(key=lambda x: x.title)
            elif sort_option == "Titre (Z-A)":
                filtered_docs.sort(key=lambda x: x.title, reverse=True)
            elif sort_option == "Popularité":
                filtered_docs.sort(key=lambda x: len(x.accesses), reverse=True)
            
            # Afficher les documents filtrés et triés
            for i, doc in enumerate(filtered_docs):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.subheader(doc.title)
                        if doc.description:
                            st.write(doc.description)
                        st.write(f"Catégorie: {doc.category or 'Non catégorisé'}")
                        st.write(f"Téléchargé le: {doc.get_upload_date().strftime('%d/%m/%Y')}")
                        if doc.word_count:
                            st.write(f"{doc.word_count} mots | {doc.page_count or '?'} pages")
                    
                    with col2:
                        st.write(f"👁️ {len(doc.accesses)}")
                        st.write(f"👍 {len(doc.likes)}")
                        st.write(f"👎 {len(doc.dislikes)}")
                        st.write(f"🔖 {len(doc.bookmarks)}")
                        st.write(f"📤 {len(doc.shares)}")
                    
                    with col3:
                        # Boutons d'action pour le document
                        if st.button("📝 Modifier", key=f"edit_{doc.doc_id}"):
                            st.session_state["edit_doc"] = doc.doc_id
                        
                        if st.button("🔍 Voir", key=f"view_{doc.doc_id}"):
                            download_url = get_document_download_url(doc.doc_id)
                            if download_url:
                                # Marquer comme accédé
                                access = Access(access_id=user.user_id)
                                update_document_access(doc.doc_id, access, "accesses")
                                st.markdown(f"[Ouvrir le document]({download_url})")
                            else:
                                st.error("Impossible de générer l'URL de téléchargement.")
                        
                        if st.button("🗑️ Supprimer", key=f"delete_{doc.doc_id}"):
                            st.session_state["delete_doc"] = doc.doc_id
                        
                        # Boutons d'interaction
                        action_col1, action_col2, action_col3 = st.columns(3)
                        with action_col1:
                            if st.button("👍", key=f"like_{doc.doc_id}"):
                                access = Access(access_id=user.user_id)
                                update_document_access(doc.doc_id, access, "likes")
                                st.rerun()
                        with action_col2:
                            if st.button("🔖", key=f"bookmark_{doc.doc_id}"):
                                access = Access(access_id=user.user_id)
                                update_document_access(doc.doc_id, access, "bookmarks")
                                st.rerun()
                        with action_col3:
                            if st.button("📤", key=f"share_{doc.doc_id}"):
                                access = Access(access_id=user.user_id)
                                update_document_access(doc.doc_id, access, "shares")
                                # On pourrait ajouter une fonctionnalité de partage ici
                                st.success("Lien de partage copié!")
                    
                    # Formulaire pour modifier le document (si demandé)
                    if st.session_state.get("edit_doc") == doc.doc_id:
                        with st.form(f"edit_doc_form_{doc.doc_id}"):
                            new_doc_title = st.text_input("Titre", value=doc.title)
                            new_doc_description = st.text_area("Description", value=doc.description)
                            new_doc_category = st.selectbox(
                                "Catégorie", 
                                options=[""] + (selected_repo.categories or []),
                                index=0 if not doc.category else (
                                    [""] + selected_repo.categories
                                ).index(doc.category) if doc.category in selected_repo.categories else 0
                            )
                            
                            # Gérer les documents liés
                            related_options = {d.title: d.doc_id for d in documents if d.doc_id != doc.doc_id}
                            selected_related = [d for d in doc.related_documents if d in related_options.values()]
                            new_related = st.multiselect(
                                "Documents liés",
                                options=list(related_options.keys()),
                                default=[k for k, v in related_options.items() if v in selected_related]
                            )
                            new_related_ids = [related_options[title] for title in new_related]
                            
                            # Boutons de formulaire
                            update_doc_button = st.form_submit_button("Mettre à jour")
                            cancel_doc_button = st.form_submit_button("Annuler")
                            
                            if update_doc_button:
                                updated = update_document(
                                    doc.doc_id,
                                    title=new_doc_title,
                                    description=new_doc_description,
                                    category=new_doc_category if new_doc_category else None,
                                    related_documents=new_related_ids,
                                )
                                if updated:
                                    st.success("Document mis à jour avec succès!")
                                    del st.session_state["edit_doc"]
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la mise à jour du document.")
                            
                            if cancel_doc_button:
                                del st.session_state["edit_doc"]
                                st.rerun()
                    
                    # Confirmation de suppression (si demandé)
                    if st.session_state.get("delete_doc") == doc.doc_id:
                        st.warning("Êtes-vous sûr de vouloir supprimer ce document? Cette action est irréversible.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Confirmer la suppression", key=f"confirm_delete_{doc.doc_id}"):
                                if update_document(doc_id=doc.doc_id, is_deleted=True):
                                    st.success("Document supprimé avec succès!")
                                    del st.session_state["delete_doc"]
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression du document.")
                        with col2:
                            if st.button("Annuler", key=f"cancel_delete_{doc.doc_id}"):
                                del st.session_state["delete_doc"]
                                st.rerun()
                
                # Séparateur entre les documents
                st.divider()