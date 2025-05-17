import os
import tempfile
from typing import List
import streamlit as st
from model import Access, DocumentRepository
from utils.doc import create_document_repository, get_document_download_url, get_list_of_documents, get_list_of_repositories, get_public_repositories, load_document_cover, load_repository_banner, update_document, update_document_cover, update_document_repository, update_repository_access, update_repository_banner, upload_document, get_owner_name, get_original_repo
from utils.user import get_user

def select_repositories(user_repos: List[DocumentRepository], user_id: str):
    """
    Display an interface for selecting and interacting with document repositories.
    Allows users to view their own or public repositories, interact (like, dislike, bookmark, share),
    and edit them if they are the owner.
    """
    # Check if user is logged in
    if 'user' not in st.session_state or not hasattr(st.session_state.user, 'user_id'):
        st.warning("🔒 You must be logged in to access this page.")
        return

    # Tabs for user's repositories, public repositories, and creating a new one
    tab1, tab2, tab3 = st.tabs(["📂 My Repositories", "🌍 Public Repositories", "➕ Create New Repository"])

    # --- Tab 1: User's Repositories ---
    with tab1:
        st.subheader("Your Repositories")

        if hasattr(st.session_state.user, 'repositories') and st.session_state.user.repositories:
            if user_repos:
                display_repositories(user_repos, user_id)
            else:
                st.info("🚫 You don't have any repositories yet. Create one in the next tab!")
        else:
            st.info("🚫 You don't have any repositories yet. Create one in the next tab!")

    # --- Tab 2: Public Repositories ---
    with tab2:
        st.subheader("Browse Public Repositories")

        # Pagination controls
        st.markdown("Use the page selector to browse through public repositories.")
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("🔍 Search", max_chars=50, key='public_repo_search')
        with col2:
            page = st.number_input("🔢 Page", min_value=1, value=1, step=1, key='public_repo_page')

        # Load public repositories
        public_repos = get_public_repositories(page=page, user_id=user_id, query=query)
        if public_repos:
            display_repositories(public_repos, user_id)
        else:
            st.info("📭 No public repositories available yet.")

    # --- Tab 3: Create New Repository ---
    with tab3:
        st.subheader("Create a New Repository")

        with st.form("new_repo_form"):
            repo_name = st.text_input("📌 Repository Name", max_chars=50, placeholder="e.g. Project Reports")
            repo_desc = st.text_area("📝 Description", max_chars=500, placeholder="Brief description of your repository")
            is_public = st.checkbox("🌐 Make this repository public")

            categories_input = st.text_input(
                "🏷️ Categories (comma-separated)",
                placeholder="e.g. Research, Invoices, Contracts"
            )

            submit_button = st.form_submit_button("✅ Create Repository")

            if submit_button:
                if not repo_name.strip():
                    st.warning("Repository name is required.")
                else:
                    try:
                        categories = [cat.strip() for cat in categories_input.split(",") if cat.strip()]
                        create_document_repository(repo_name, repo_desc, user_id, categories, is_public)
                        st.session_state.user = get_user(user_id)
                        st.success(f"Repository '{repo_name}' created successfully!")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create repository: {str(e)}")

def display_repositories(repositories: List[DocumentRepository], user_id: str):
    """
    Affiche une liste de dépôts sous forme de cartes avec leurs statistiques.
    
    Args:
        repositories: Liste des dépôts à afficher
        user_id: ID de l'utilisateur actuel
        is_owner: Indique si les dépôts affichés appartiennent à l'utilisateur
    """
    for current_repo in repositories:
        display_repository_card(current_repo, user_id, is_owner=(current_repo.owner_id == user_id))

def display_repository_card(repository: DocumentRepository, user_id: str, is_owner: bool = False):
    """
    Display a card for a specific repository with its statistics and interactive options.
    
    Args:
        repository: The repository to display
        user_id: ID of the current user
        is_owner: Indicates whether the user is the repository's owner
    """
    with st.container(border=True):
        # Load banner if available
        banner_url = load_repository_banner(repository.banner) if repository.banner else None
        with st.expander("🖼️ Banner"):
            st.image(banner_url or "banner.png", use_container_width=True)
            if is_owner:
                if st.button("🖼️ Change Banner", key=f"banner_{repository.repo_id}"):
                        st.session_state[f"change_banner_{repository.repo_id}"] = True

        # Title and description
        st.subheader(repository.name)
        st.markdown(f"**Description:** {repository.description}")
        
        if repository.categories:
            st.markdown(f"**Categories:** {', '.join(map(str, repository.categories))}")
        
        st.markdown(f"**Status:** {'Public' if repository.is_public else 'Private'}")

        owner_name = get_owner_name(repository.owner_id)
        if owner_name:
            st.markdown(f"**Owner:** {owner_name}")

        # Repository stats
        stats = repository.get_document_stats()
        stats_col1, stats_col2 = st.columns(2)

        with stats_col1:
            st.metric("📄 Documents", stats['document_count'])
            st.metric("🔍 Indexed", stats['indexed_count'])
            st.metric("🔄 Shared", stats['shared_count'])

        with stats_col2:
            st.metric("👁️ Views", stats['access_count'])
            st.metric("👍 Relevance", stats['pertinence_count'])
            st.metric("🔖 Bookmarks", stats['saved_count'])

        # Owner actions
        if is_owner:
            action_cols = st.columns(2)

            with action_cols[0]:
                if st.button("✏️ Edit", key=f"edit_{repository.repo_id}"):
                    st.session_state[f"edit_repo_{repository.repo_id}"] = True

            with action_cols[1]:
                if st.button("🗑️ Delete", key=f"delete_{repository.repo_id}"):
                    st.session_state[f"delete_repo_{repository.repo_id}"] = True

            # Edit form
            if st.session_state.get(f"edit_repo_{repository.repo_id}", False):
                with st.form(f"edit_form_{repository.repo_id}"):
                    st.subheader("Edit Repository")
                    new_name = st.text_input("📌 Repository Name", max_chars=50, value=repository.name)
                    new_desc = st.text_area("📝 Description", max_chars=500, value=repository.description)
                    new_public = st.checkbox("🌐 Make this repository public", value=repository.is_public)
                    categories_input = st.text_input("🏷️ Categories (comma-separated)",
                        placeholder="e.g. Research, Invoices, Contracts", value=f"{", ".join(map(str, repository.categories))}")

                    col1, col2 = st.columns(2)
                    submit_edit = col1.form_submit_button("✅ Save")
                    cancel_edit = col2.form_submit_button("↩️ Cancel")

                    if submit_edit:
                        try:
                            categories = []
                            if categories_input:
                                categories = [cat.strip() for cat in categories_input.split(",") if cat.strip()]
                            success = update_document_repository(
                                repository.repo_id,
                                name=new_name,
                                description=new_desc,
                                is_public=new_public,
                                categories=categories
                            )
                            if success:
                                st.success("Repository updated successfully!")
                                st.session_state[f"edit_repo_{repository.repo_id}"] = False
                                st.rerun()
                            else:
                                st.error("Failed to update the repository.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                    if cancel_edit:
                        st.session_state[f"edit_repo_{repository.repo_id}"] = False
                        st.rerun()

            # Change banner form
            if st.session_state.get(f"change_banner_{repository.repo_id}", False):
                with st.form(f"banner_form_{repository.repo_id}"):
                    st.subheader("Update Banner")
                    uploaded_file = st.file_uploader("Select an image", type=["jpg", "jpeg", "png"])

                    col1, col2 = st.columns(2)
                    submit_banner = col1.form_submit_button("✅ Upload")
                    cancel_banner = col2.form_submit_button("↩️ Cancel")

                    if submit_banner and uploaded_file:
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                temp_path = tmp_file.name

                            success = update_repository_banner(repository.repo_id, temp_path)
                            os.unlink(temp_path)

                            if success:
                                st.success("Banner updated successfully!")
                                st.session_state[f"change_banner_{repository.repo_id}"] = False
                                st.rerun()
                            else:
                                st.error("Failed to update banner.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                    if cancel_banner:
                        st.session_state[f"change_banner_{repository.repo_id}"] = False
                        st.rerun()

            # Delete confirmation
            if st.session_state.get(f"delete_repo_{repository.repo_id}", False):
                st.warning(" Are you sure you want to delete this repository? This action **cannot be undone**.", icon="⚠️")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🗑️ Confirm Deletion", key=f"confirm_delete_{repository.repo_id}"):
                        try:
                            success = update_document_repository(repository.repo_id, is_deleted=True)
                            if success:
                                st.success("✅ Repository deleted successfully!")
                                st.session_state[f"delete_repo_{repository.repo_id}"] = False
                                st.rerun()
                            else:
                                st.error("Failed to delete the repository.")
                        except Exception as e:
                            st.error(f"🚫 Error: {str(e)}")
                with col2:
                    if st.button("↩️ Cancel", key=f"cancel_delete_{repository.repo_id}"):
                        st.session_state[f"delete_repo_{repository.repo_id}"] = False
                        st.rerun()

        else:
            # Viewer interactions
            action_cols = st.columns(4)

            is_liked = any(access.access_id == user_id for access in repository.likes)
            is_disliked = any(access.access_id == user_id for access in repository.dislikes)
            is_bookmarked = any(access.access_id == user_id for access in repository.bookmarks)

            with action_cols[0]:
                like_label = "👍 Liked" if is_liked else "👍 Like"
                if st.button(like_label, key=f"like_{repository.repo_id}"):
                    update_repository_access(repository.repo_id, Access(access_id=user_id), "likes")
                    st.rerun()

            with action_cols[1]:
                dislike_label = "👎 Disliked" if is_disliked else "👎 Dislike"
                if st.button(dislike_label, key=f"dislike_{repository.repo_id}"):
                    update_repository_access(repository.repo_id, Access(access_id=user_id), "dislikes")
                    st.rerun()

            with action_cols[2]:
                bookmark_label = "🔖 Bookmarked" if is_bookmarked else "🔖 Bookmark"
                if st.button(bookmark_label, key=f"bookmark_{repository.repo_id}"):
                    update_repository_access(repository.repo_id, Access(access_id=user_id), "bookmarks")
                    st.rerun()

            with action_cols[3]:
                if st.button("📤 Share", key=f"share_{repository.repo_id}"):
                    update_repository_access(repository.repo_id, Access(access_id=user_id), "shares")
                    st.rerun()

        # View button
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("🔎 View Repository", key=f"view_{repository.repo_id}", on_click=view_repository, args=(repository,user_id))

        with col2:
            modified_date = repository.get_updated_at()
            st.write("**Last Modified:**")
            st.write(modified_date.strftime("%b %d, %Y %H:%M"))

        with col3:
            created_date = repository.get_created_at()
            st.write("**Created On:**")
            st.write(created_date.strftime("%b %d, %Y %H:%M"))
    
def view_repository(repository: DocumentRepository, user_id: str):
    """
    Enregistre le dépôt sélectionné dans la session et 
    enregistre une vue pour l'utilisateur actuel.
    
    Args:
        repository: Le dépôt à consulter
    """
    # Enregistrer le dépôt dans la session
    st.session_state.repo = repository
    
    # Enregistrer une vue
    access = Access(access_id=user_id)
    update_repository_access(repository.repo_id, access, "accesses")
    
def check_repositories(user_id: str, user_repos: List[DocumentRepository]):
    """
    Affiche la page de détail d'un dépôt sélectionné.
    Permet de visualiser et gérer les documents du dépôt,
    d'uploader de nouveaux documents, et d'interagir avec les documents existants.
    """
    # Check if a repository is selected
    if not st.session_state.get("repo"):
        st.warning("No repository selected. Please select one to continue.")
        st.button("🔙 Back to repository selection", on_click=lambda: st.rerun())
        st.stop()

    # Check if the user is logged in
    if not st.session_state.get("user"):
        st.warning("🔒 You must be logged in to access this page.", icon="🔒")
        clear_repo()
        st.stop()

    repo = st.session_state.repo
    is_owner = repo.owner_id == user_id

    # Header with repository information
    col1, col2 = st.columns([2, 3])

    with col1:
        st.title(repo.name)
        st.markdown(f"**Description:** {repo.description}")
        
        if repo.categories:
            st.markdown(f"**Categories:** {', '.join(map(str, repo.categories))}")
        
        st.markdown(f"**Status:** {'Public' if repo.is_public else 'Private'}")

        owner_name = get_owner_name(repo.owner_id)
        if owner_name:
            st.markdown(f"**Owner:** {owner_name}")

        stats = repo.get_document_stats()
        st.markdown(f"""
        **📊 Statistics:**
        - 📄 Documents: {stats['document_count']}
        - 🔍 Indexed: {stats['indexed_count']}
        - 👁️ Views: {stats['access_count']}
        - 👍 Relevance: {stats['pertinence_count']}
        - 🔖 Bookmarks: {stats['saved_count']}
        - 🔄 Shares: {stats['shared_count']}
        """)

        st.markdown(f"**Created on:** {repo.get_created_at().strftime('%b %d, %Y %H:%M')}")
        st.markdown(f"**Last updated:** {repo.get_updated_at().strftime('%b %d, %Y %H:%M')}")

    with col2:
        banner_url = load_repository_banner(repo.banner) if repo.banner else None
        if banner_url:
            st.image(banner_url, use_container_width=True)
        else:
            st.image("banner.png", use_container_width=True)

        if st.button("🔙 Return", key="return_button"):
            clear_repo()
            st.rerun()

    # Section to upload a document (owners only)
    if is_owner:
        with st.expander("📤 Upload a Document", expanded=False):
            st.subheader("Upload a New Document")
            
            uploaded_file = st.file_uploader(
                "Select a PDF file (max 25 MB)",
                type=["pdf"],
                key="doc_uploader"
            )
            
            if uploaded_file:
                file_size = len(uploaded_file.getvalue())
                
                # Check file size (max 25 MB)
                if file_size > 25 * 1024 * 1024:
                    st.error("The file is too large. Maximum size is 25 MB.")
                else:
                    # Metadata form
                    with st.form(key="upload_doc_form"):
                        doc_title = st.text_input("📄 Document Title", value=uploaded_file.name.split('.')[0], max_chars=50)
                        doc_description = st.text_area("📝 Document Description", max_chars=500)
                        
                        # Category selection
                        doc_category = None
                        if repo.categories:
                            category_options = [""] + repo.categories
                            doc_category = st.selectbox(
                                "🏷️ Category",
                                options=category_options,
                                format_func=lambda x: "None" if x == "" else x
                            )
                        
                        upload_button = st.form_submit_button("✅ Upload")
                        
                        if upload_button:
                            with st.spinner("Uploading and processing the document..."):
                                # Upload the document
                                doc_id = upload_document(
                                    file_data=uploaded_file.getvalue(),
                                    filename=uploaded_file.name,
                                    repo_id=repo.repo_id,
                                    owner_id=user_id,
                                    title=doc_title,
                                    description=doc_description,
                                    category=doc_category if doc_category else None
                                )
                                    
                                st.success("Document uploaded successfully!")
                                st.session_state.repo.documents.append(doc_id)
                                    
                                # Optional: Upload a cover
                                st.markdown("### Add a Cover (Optional)")
                                cover_file = st.file_uploader(
                                    "Select a cover image",
                                    type=["jpg", "jpeg", "png"],
                                    key="cover_uploader"
                                )
                                    
                                if cover_file:
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{cover_file.name.split('.')[-1]}") as tmp:
                                        tmp.write(cover_file.getvalue())
                                        tmp_path = tmp.name
                                    
                                    if update_document_cover(doc_id, tmp_path):
                                        st.success("Cover added successfully!")
                                    else:
                                        st.error("Failed to add cover.")
                                    
                                    try:
                                        os.unlink(tmp_path)
                                    except:
                                        pass
                                
                                # Refresh the page to show the new document
                                st.form_submit_button("Refresh Page", on_click=lambda: st.rerun())
                        else:
                            st.warning("Make sure it is a valid PDF.")


        # Display repository documents
    st.subheader("📚 Available Documents")

    # Filters for the documents
    col1, col2 = st.columns(2)

    with col1:
        # Filter by title
        title_filter = st.text_input(
            "🔍 Filter by title",
            max_chars=50
        )

    with col2:
        # Filter by category
        category_filter = st.selectbox(
            "🏷️ Filter by category",
            options=["All"] + (repo.categories if repo.categories else [])
        )

    # Get all documents from the repository
    if repo.documents:
        documents = get_list_of_documents(repo.documents)

        # Exclude deleted documents
        documents = [doc for doc in documents if not doc.is_deleted]

        # Apply category filter
        if category_filter != "All":
            documents = [doc for doc in documents if doc.category == category_filter]

        # Apply title filter
        if title_filter:
            documents = [doc for doc in documents if doc.title.lower().startswith(title_filter.lower())]

        if not documents:
            st.info(f"No documents found{' in this category' if category_filter != 'All' else ''}.")
        else:
            # Display documents as cards in a grid (3 per row)
            num_cols = 3
            for i in range(0, len(documents), num_cols):
                cols = st.columns(num_cols)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(documents):
                        doc = documents[idx]
                        with col:
                            with st.container(border=True):
                                # Document cover
                                with st.expander("🖼️ Cover"):
                                    cover_url = load_document_cover(doc.cover) if doc.cover else None
                                    if cover_url:
                                        st.image(cover_url, use_container_width=True)
                                    else:
                                        st.image("cover.png", use_container_width=True)

                                st.markdown(f"### {doc.title}")

                                if doc.description:
                                    description = doc.description
                                    with st.expander("📝 Description"):
                                        st.markdown(description)

                                if doc.category:
                                    st.markdown(f"*Category:* {doc.category}")

                                owner_name = get_owner_name(doc.owner_id)
                                if owner_name:
                                    st.markdown(f"**Owner:** {owner_name}")
                                original_repo = get_original_repo(doc.original_repo)
                                if original_repo:
                                    st.markdown(f"**Origin:** {original_repo}")

                                st.markdown(f"📅: {doc.get_upload_date().strftime('%b %d, %Y %H:%M')}")

                                # Extra info
                                if doc.page_count:
                                    st.markdown(f"📄: {doc.page_count} pages")
                                if doc.word_count:
                                    st.markdown(f"📝: {doc.word_count} words")
                                if doc.file_size:
                                    st.markdown(f"💾: {doc.file_size / (1024 * 1024):.2f} MB")

                                # Action buttons
                                col1, col2 = st.columns(2)

                                # Download button
                                download_url = get_document_download_url(doc.file_path) if doc.file_path else None
                                if download_url:
                                    with col1:
                                        st.link_button("📥 Download", download_url)

                                # Edit or add buttons
                                with col2:
                                    if doc.owner_id == user_id:
                                        if st.button("✏️ Edit", key=f"edit_{doc.doc_id}"):
                                            st.session_state.editing_doc = doc
                                            st.rerun()
                                    else:
                                        if st.button("➕ Add", key=f"add_{doc.doc_id}"):
                                            st.session_state.adding_doc = doc
                                            st.rerun()
            st.markdown("---")
    else:
        st.info("This repository doesn't contain any documents.")

    
    # Modal window to edit a document (if in editing mode)
    if st.session_state.get("editing_doc"):
        doc = st.session_state.editing_doc

        with st.expander("Edit Document", expanded=True):
            st.subheader(f"Edit: {doc.title}")

            with st.form(key="edit_doc_form"):
                new_doc_title = st.text_input("📄 Title", value=doc.title)
                new_doc_description = st.text_area("📝 Description", value=doc.description)

                # Category selection
                new_doc_category = None
                if repo.categories:
                    category_options = [""] + repo.categories
                    default_idx = category_options.index(doc.category) if doc.category in category_options else 0
                    new_doc_category = st.selectbox(
                        "🏷️ Category",
                        options=category_options,
                        index=default_idx,
                        format_func=lambda x: "None" if x == "" else x
                    )

                # Upload a new cover
                st.markdown("**Document Cover**")
                new_cover_file = st.file_uploader(
                    "Upload a new cover image",
                    type=["jpg", "jpeg", "png"],
                    key="new_cover_uploader"
                )

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    save_button = st.form_submit_button("✅ Save Changes")
                with col2:
                    cancel_button = st.form_submit_button("↩️ Cancel")

                # Danger zone: delete document
                st.warning("Deleting a document is irreversible!")
                delete_button = st.form_submit_button("🗑️ Delete this Document")

                if save_button:
                    # Update document metadata
                    updated = update_document(
                        doc_id=doc.doc_id,
                        title=new_doc_title,
                        description=new_doc_description,
                        category=new_doc_category if new_doc_category != "" else None
                    )

                    # Update cover if provided
                    if new_cover_file:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{new_cover_file.name.split('.')[-1]}") as tmp:
                            tmp.write(new_cover_file.getvalue())
                            tmp_path = tmp.name

                        cover_updated = update_document_cover(doc.doc_id, tmp_path)

                        try:
                            os.unlink(tmp_path)
                        except:
                            pass

                        if cover_updated:
                            st.success("Cover updated successfully!")
                        else:
                            st.error("Failed to update cover.")

                    if updated:
                        st.success("Document updated successfully!")
                        del st.session_state.editing_doc
                        st.rerun()
                    else:
                        st.error("Failed to update document.")

                elif cancel_button:
                    del st.session_state.editing_doc
                    st.rerun()

                elif delete_button:
                    # Soft-delete the document
                    if update_document(doc_id=doc.doc_id, is_deleted=True):
                        if doc.doc_id in repo.documents:
                            repo.documents.remove(doc.doc_id)
                            update_document_repository(
                                repo_id=repo.repo_id,
                                documents=repo.documents
                            )

                        st.success("Document deleted successfully!")
                        del st.session_state.editing_doc
                        st.rerun()
                    else:
                        st.error("Failed to delete the document.")
  
    # Modal window to add a document to a personal repository
    if st.session_state.get("adding_doc"):
        doc = st.session_state.adding_doc

        with st.expander("Add to My Repository", expanded=True):
            st.subheader(f"Add \"{doc.title}\" to My Repository")

            if not user_repos:
                st.info("You don’t have any repositories yet.")
                if st.button("🔙 Create a New Repository"):
                    clear_repo()
                    st.rerun()
            else:
                with st.form(key="add_to_repo_form"):
                    # Select a repository
                    target_repo_id = st.selectbox(
                        "Select a Repository",
                        options=[r.repo_id for r in user_repos],
                        format_func=lambda x: next((r.name for r in user_repos if r.repo_id == x), x)
                    )

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        add_button = st.form_submit_button("✅ Add to Repository")
                    with col2:
                        cancel_button = st.form_submit_button("↩️ Cancel")

                    if add_button and target_repo_id:
                        target_repo = next((r for r in user_repos if r.repo_id == target_repo_id), None)

                        if target_repo:
                            # Check if the document is already in the selected repository
                            if doc.doc_id in target_repo.documents:
                                st.warning("This document is already in the selected repository.")
                            else:
                                # Add the document to the target repository
                                target_repo.documents.append(doc.doc_id)
                                if update_document_repository(
                                    repo_id=target_repo.repo_id,
                                    documents=target_repo.documents
                                ):
                                    st.success(f"Document successfully added to \"{target_repo.name}\"!")
                                    # Create sharing access
                                    access = Access(access_id=user_id)
                                    update_repository_access(
                                        repo_id=repo.repo_id,
                                        access=access,
                                        access_type="shares"
                                    )
                                    # Clear session state
                                    del st.session_state.adding_doc
                                    st.rerun()
                                else:
                                    st.error("Failed to add the document to the repository.")

                    elif cancel_button:
                        # Cancel the addition
                        del st.session_state.adding_doc
                        st.rerun()

def clear_repo():
    """Vide la variable repo dans la session"""
    if "repo" in st.session_state:
        del st.session_state.repo
            
def display_document_repositories():
    user_id = st.session_state.user.user_id
    user_repos = get_list_of_repositories(st.session_state.user.repositories)
    st.title("📁 My Repositories")
    if hasattr(st.session_state, 'repo') and st.session_state.repo:
        check_repositories(user_id=user_id, user_repos=user_repos)
    else:
        select_repositories(user_repos=user_repos, user_id=user_id)
