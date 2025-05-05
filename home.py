import streamlit as st
from datetime import datetime
import shutil

# Import des modules d'authentification
from utils.auth import login_user, register_user, generate_credentials, check_credentials
from utils.user import get_user
from ui.repo import display_repositories
from ui.bot import display_chats

# Configuration de la page
st.set_page_config(
    page_title="Ndolè - Intelligent Learning Assistant",
    page_icon="📚",
    layout="wide"
)

if st.query_params["id"] and st.query_params["id"] != "None":
    st.session_state.user = get_user(st.query_params["id"])
    st.session_state.logged_in = True

# Initialisation des états de session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "registration_method" not in st.session_state:
    st.session_state.registration_method = "manual"  # 'manual' ou 'auto'
    
shutil.copy(".streamlit/dark.toml", ".streamlit/config.toml")

# Fonctions de navigation
def set_page(page_name):
    st.session_state.current_page = page_name

def toggle_login_form():
    st.session_state.show_login = not st.session_state.show_login
    st.session_state.show_register = False

def toggle_register_form():
    st.session_state.show_register = not st.session_state.show_register
    st.session_state.show_login = False

def logout():
    """Déconnexion de Firebase Auth et réinitialisation des états de session"""
    # Réinitialiser les états de session
    st.query_params["id"] = None
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.supabase_token = None
    st.rerun()

def calculate_user_stats(user):
    """Calcule quelques statistiques utilisateur pour l'affichage"""
    # Supposons que created_at est un datetime avec timezone (aware)
    created_at = user.get_created_at()  # Ex: 2023-10-05T14:30:00+02:00

    # 1. Récupérer le fuseau horaire de created_at
    created_at_tz = created_at.tzinfo

    # 2. Appliquer ce fuseau à now
    now = datetime.now(created_at_tz)  # now aura le même fuseau que created_at

    # Calcul sécurisé
    days_since_creation = (now - created_at).days
    
    # Ces données seraient normalement extraites de Firestore
    stats = {
        "documents_count": len(user.repositories) if hasattr(user, "repositories") else 0,
        "conversations_count": len(user.chat_histories) if hasattr(user, "chat_histories") else 0,
        "days_active": days_since_creation,
        "next_level_xp": user.level * 100  # Simulation d'une formule pour le prochain niveau
    }
    return stats

def handle_login(username, password):
    """Gère la connexion avec Firebase Auth"""
    try:
        # Utilisation de notre fonction login_user adaptée pour Firebase
        success, message, user = login_user(username, password)
        
        if success:
            
            # Stocker le token pour les requêtes futures
            st.success(message)
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()

        else:
            st.error(message)
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

def handle_registration(username, password, method="manual"):
    """Gère l'inscription avec Firebase Auth"""
    try:
        if method == "auto":
            credentials = generate_credentials()
            username = credentials["username"]
            password = credentials["password"]
            
        # Utilisation de notre fonction register_user adaptée pour Firebase
        success, message, user = register_user(username, password)
        
        if success:
            
            # Stocker le token pour les requêtes futures
            if method == "auto":
                st.success(f"Account successfully created! Your login credentials are:\nUsername: {username}\nPassword: {password}\n\nPlease make sure to store them in a safe place.")
            else:
                st.success(message)
            st.session_state.logged_in = True
            st.session_state.user = user
            

        else:
            st.error(message)
    except Exception as e:
        st.error(f"Error during registration: {str(e)}")

# Fonction de vérification de session
def verify_session():
    """Vérifie si la session utilisateur est toujours valide"""
    if st.session_state.logged_in and st.session_state.firebase_token:
        try:
            # Vérifier la validité du token (cette étape nécessite généralement une vérification côté serveur)
            # Pour une vérification complète, vous devriez implémenter une validation de token avec Firebase Admin SDK
            
            # Rafraîchir le token si nécessaire
            # Cette étape dépend de la façon dont vous gérez les tokens expirés
            return True
        except Exception:
            # Si le token n'est plus valide, déconnecter l'utilisateur
            logout()
            return False
    return st.session_state.logged_in

# Barre latérale avec navigation
with st.sidebar:
    st.image("logo.png", width=150)
    st.title("Ndolè")
    st.caption("Your Learning Assistant")
    
    if st.session_state.logged_in and st.session_state.user:
        # Menu for logged-in users
        st.subheader("Navigation")
        if st.button("🏠 Home", use_container_width=True):
            set_page("home")
        if st.button("📚 My Repositories", use_container_width=True):
            set_page("repositories")
        if st.button("🤖 AI Assistant", use_container_width=True):
            set_page("assistant")
        if st.button("📊 Statistics", use_container_width=True):
            set_page("stats")
        if st.button("🏆 Badges and Levels", use_container_width=True):
            set_page("achievements")
        if st.button("⚙️ Settings", use_container_width=True):
            set_page("settings")
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout()
    else:
        # Menu for visitors
        st.markdown("### About")
        st.markdown("Ndolè is an AI-powered learning assistant that helps you organize your documents and optimize your learning.")

        st.divider()
        st.markdown("### Features")
        st.markdown("• Document management")
        st.markdown("• Conversational AI assistant")
        st.markdown("• Personalized content generation")
        st.markdown("• Planning and organization")
        st.markdown("• Gamification system")

# Contenu principal de la page
def main_content():
    if st.session_state.logged_in and st.session_state.user:
        if st.session_state.current_page == "home":
            display_user_dashboard()
        elif st.session_state.current_page == "repositories":
            display_repositories()
        elif st.session_state.current_page == "assistant":
            display_chats()
    else:
        display_landing_page()

def display_landing_page():
    st.markdown("<h1>🌿 Discover Ndolè: Your Intelligent Learning Assistant</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("### 🇨🇲 Inspired by Cameroonian Culture, Powered by AI")
        st.write("""
        **Ndolè** is more than a study platform. It transforms your learning experience by combining AI with cultural values and a deep focus on personalization.
        """)

        st.markdown("### 🚀 Why Choose Ndolè?")
        st.write("""
        Imagine a smart assistant that organizes your documents, answers your questions, and adapts to your learning style. 
        With Ndolè, your documents become an interactive knowledge base.
        """)

        st.markdown("### 💡 Key Features")

        feature_col1, feature_col2 = st.columns(2, gap="medium")

        with feature_col1:
            st.markdown("#### 📚 Intelligent Organization")
            st.caption("Organize and search your PDFs, Word docs and notes instantly.")

            st.markdown("#### 🤖 Conversational AI")
            st.caption("Ask natural questions and get precise answers from your own documents.")

            st.markdown("#### 📝 Custom Content Generation")
            st.caption("Transform your files into courses, quizzes, summaries and more.")

        with feature_col2:
            st.markdown("#### 📅 Smart Study Planner")
            st.caption("Upload your schedule and get optimized plans + Telegram reminders.")

            st.markdown("#### 🏆 Gamified Learning")
            st.caption("Earn points, badges and take on daily learning challenges.")

            st.markdown("#### 🔒 Privacy First")
            st.caption("Your data stays private. You’re always in control.")

    with col2:
        st.markdown("### 🚪 Get Started")

        login_tab, register_tab = st.tabs(["🔐 Login", "📝 Sign Up"])

        with login_tab:
            with st.form("login_form"):
                st.subheader("Welcome Back 👋")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In")

                if submit_login:
                    handle_login(username, password)

        with register_tab:
            registration_option = st.radio(
                "Choose a registration method:",
                ["Create my own account", "Generate one for me"],
                horizontal=True
            )

            if registration_option == "Create my own account":
                with st.form("manual_register_form"):
                    st.subheader("Create Account")
                    username = st.text_input("Choose a Username")
                    password = st.text_input("Create a Password", type="password")
                    password_confirm = st.text_input("Confirm Password", type="password")

                    submit_register = st.form_submit_button("Sign Up")

                    if submit_register:
                        if password != password_confirm:
                            st.error("❌ Passwords do not match.")
                        elif not username or not password:
                            st.warning("Please complete all fields.")
                        else:
                            validation = check_credentials(username, password)
                            if validation["all_valid"]:
                                handle_registration(username, password, "manual")
                            else:
                                if not validation["username_valid"]:
                                    st.error(validation["username_message"])
                                if not validation["password_valid"]:
                                    st.error(validation["password_message"])
            else:
                with st.form("auto_register_form"):
                    st.subheader("Automatic Account Creation")
                    submit_auto_register = st.form_submit_button("Generate My Account")

                    if submit_auto_register:
                        handle_registration("", "", "auto")

    st.divider()

    st.markdown("### 🤝 Our Commitment")
    st.info("""
    Ndolè adapts to all learning styles and disciplines. Whether you're a student, professional, or curious mind, 
    we’re here to support your growth and curiosity.
    """)

    st.success("✨ Join the Ndolè community today and discover a smarter, more personal way to learn!")

def display_user_dashboard():
    user = st.session_state.user
    
    # Header with user info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title(f"Welcome, {user.username} 👋")
        st.write(f"Glad to have you back on Ndolè! Here is your personalized dashboard.")
    
    with col2:
        # Display level and progress
        st.metric("Current Level", user.level)
        progress = (user.experience_points % 100) / 100  # Simulating progress
        st.progress(progress)
        st.caption(f"Progress: {user.experience_points} XP / {user.level * 100} XP to reach the next level")
    
    # Retrieve user statistics
    stats = calculate_user_stats(user)
    
    # Stats in columns
    st.subheader("Your Activity Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", stats["documents_count"])
    with col2:
        st.metric("Conversations", stats["conversations_count"])
    with col3:
        st.metric("Active Days", stats["days_active"])
    with col4:
        st.metric("Badges Unlocked", len(user.badges))
    
    # Recent repositories and conversations
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Your Recent Repositories")
        if hasattr(user, "repositories") and user.repositories:
            for i, repo in enumerate(user.repositories[:3]):
                with st.container():
                    st.write(f"📁 {repo.name if hasattr(repo, 'name') else f'Repository #{i+1}'}")
                    st.caption(f"{len(repo.documents) if hasattr(repo, 'documents') else 0} documents")
        else:
            st.info("You haven't created any repositories yet. Start by creating one!")
            if st.button("Create a Repository"):
                set_page("repositories")
    
    with col_right:
        st.subheader("Recent Conversations")
        if hasattr(user, "chat_histories") and user.chat_histories:
            for i, chat in enumerate(user.chat_histories[:3]):
                with st.container():
                    st.write(f"💬 {chat.title if hasattr(chat, 'title') else f'Conversation #{i+1}'}")
                    st.caption(f"Last activity: {chat.last_updated.strftime('%d/%m/%Y') if hasattr(chat, 'last_updated') else 'N/A'}")
        else:
            st.info("You haven't had any conversations yet. Start chatting with the assistant!")
            if st.button("Open Assistant"):
                set_page("assistant")
    
    # Daily Challenges
    st.subheader("Daily Challenges")
    challenges_col1, challenges_col2, challenges_col3 = st.columns(3)
    
    # Simulating some daily challenges
    daily_challenges = [
        {"name": "Study for 30 minutes", "completed": True},
        {"name": "Add a new document", "completed": False},
        {"name": "Ask 3 questions to the assistant", "completed": False}
    ]
    
    with challenges_col1:
        challenge = daily_challenges[0]
        st.checkbox(challenge["name"], value=challenge["completed"], disabled=True)
        if challenge["completed"]:
            st.caption("✅ Completed | +20 XP")
        else:
            st.caption("⏳ In progress | 0/30 minutes")
    
    with challenges_col2:
        challenge = daily_challenges[1]
        st.checkbox(challenge["name"], value=challenge["completed"], disabled=True)
        if challenge["completed"]:
            st.caption("✅ Completed | +15 XP")
        else:
            st.caption("⏳ In progress | 0/1 documents")
    
    with challenges_col3:
        challenge = daily_challenges[2]
        st.checkbox(challenge["name"], value=challenge["completed"], disabled=True)
        if challenge["completed"]:
            st.caption("✅ Completed | +10 XP")
        else:
            st.caption("⏳ In progress | 0/3 questions")
    
    # Personalized Suggestions
    st.subheader("Personalized Suggestions")
    suggestion_col1, suggestion_col2 = st.columns(2)
    
    with suggestion_col1:
        st.info("📚 **Study Suggestion:** Based on your recent activity, we recommend reviewing your documents on 'Advanced Python'.")
    
    with suggestion_col2:
        st.info("🏆 **Next Badge:** 'Python Expert' - Complete 5 Python quizzes to unlock it.")

# Exécution de la page principale
main_content()