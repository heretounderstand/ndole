import streamlit as st
from datetime import datetime
from cryptography.fernet import Fernet
from ui.setting import display_settings
from utils.auth import login_user, register_user, generate_credentials, check_credentials
from utils.user import get_user, list_repositories, list_histories, update_study_stats
from utils.data import controller
from ui.repo import display_document_repositories
from ui.bot import display_chats
from ui.stat import display_statistics
from ui.trophy import display_badges
from model import StudyStats

st.set_page_config(
    page_title="Ndolè - Intelligent Learning Assistant",
    page_icon="📚",
    layout="wide"
)

if "logged_in" not in st.session_state and "user" not in st.session_state:
    key = st.secrets["encryption"]["key"]
    cipher = Fernet(key.encode())
    cookie = controller.get('user_id')
    if cookie:
        real_cookie = cipher.decrypt(cookie).decode()
        st.session_state.user = get_user(real_cookie)
        st.session_state.logged_in = True
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
    st.session_state.registration_method = "manual"

def set_page(page_name):
    st.session_state.current_page = page_name

def toggle_login_form():
    st.session_state.show_login = not st.session_state.show_login
    st.session_state.show_register = False

def toggle_register_form():
    st.session_state.show_register = not st.session_state.show_register
    st.session_state.show_login = False

def logout():
    controller.remove('user_id')
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.supabase_token = None
    st.rerun()

def calculate_user_stats(user):
    created_at = user.get_created_at()
    created_at_tz = created_at.tzinfo
    now = datetime.now(created_at_tz)
    days_since_creation = (now - created_at).days
    stats = {
        "documents_count": len(user.repositories) if hasattr(user, "repositories") else 0,
        "conversations_count": len(user.chat_histories) if hasattr(user, "chat_histories") else 0,
        "days_active": days_since_creation
    }
    return stats

def handle_login(username, password):
    try:
        success, message, user = login_user(username, password)
        if success:
            st.success(message)
            st.session_state.logged_in = True
            st.session_state.user = user
            xp_up = update_study_stats(user.user_id, StudyStats(xp_gained=10), True)
            if xp_up:
                st.session_state.user.experience_points += 10
            st.rerun()
        else:
            st.error(message)
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

def handle_registration(username, password, method="manual"):
    try:
        if method == "auto":
            credentials = generate_credentials()
            username = credentials["username"]
            password = credentials["password"]
        success, message, user = register_user(username, password)
        if success:
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

with st.sidebar:
    st.image("logo.png", width=150)
    st.title("Ndolè")
    st.caption("Your Learning Assistant")
    if st.session_state.logged_in and st.session_state.user:
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
        st.markdown("### About")
        st.markdown("Ndolè is an AI-powered learning assistant that helps you organize your documents and optimize your learning.")
        st.divider()
        st.markdown("### Features")
        st.markdown("• Document management")
        st.markdown("• Conversational AI assistant")
        st.markdown("• Personalized content generation")
        st.markdown("• Tracking & Analytics")
        st.markdown("• Gamification system")

def main_content():
    if st.session_state.logged_in and st.session_state.user:
        if st.session_state.current_page == "home":
            display_user_dashboard()
        elif st.session_state.current_page == "repositories":
            display_document_repositories()
        elif st.session_state.current_page == "assistant":
            display_chats()
        elif st.session_state.current_page == "stats":
            display_statistics()
        elif st.session_state.current_page == "achievements":
            display_badges()
        else:
            display_settings()
    else:
        display_landing_page()

def display_landing_page():
    st.markdown("<h1>🌿 Discover Ndolè: Your Intelligent Learning Assistant</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
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
            st.caption("Organize and search your PDFs instantly.")
            st.markdown("#### 🤖 Conversational AI")
            st.caption("Ask natural questions and get precise answers from your own documents.")
            st.markdown("#### 📝 Custom Content Generation")
            st.caption("Transform your files into courses, quizzes and more.")
        with feature_col2:
            st.markdown("#### 📊 Performance Tracker")
            st.caption("Track your progress and analyze stats.")
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
                            st.error("Passwords do not match.")
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
    st.markdown(f"## 👋 Welcome back, **{user.username}**!")
    st.write("Here’s a snapshot of your progress on Ndolè:")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### 🧠 Your Progress")
        progress = user.experience_points / user.calculate_level(is_next=True)
        st.progress(progress)
        st.caption(f"{user.experience_points} XP / {user.calculate_level(is_next=True)} XP to reach level {user.calculate_level() + 1}")
    with col2:
        st.metric("⭐ Current Level", user.calculate_level())
    st.divider()
    st.markdown("### 📊 Your Activity Overview")
    stats = calculate_user_stats(user)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 Repositories", stats["documents_count"])
    col2.metric("💬 Conversations", stats["conversations_count"])
    col3.metric("📆 Active Days", stats["days_active"])
    col4.metric("🏅 Badges", len(user.badges))
    st.divider()
    repo_col, chat_col = st.columns(2)
    user_repo = list_repositories(user.repositories) if hasattr(user, "repositories") else []
    user_chat = list_histories(user.chat_histories) if hasattr(user, "chat_histories") else []
    with repo_col:
        st.markdown("### 📁 Recent Repositories")
        if user_repo:
            for i, repo in enumerate(user_repo[:3]):
                with st.container():
                    name = repo["name"] if repo["name"] else f"Repository #{i+1}"
                    doc_count = len(repo["documents"]) if repo["documents"] else 0
                    st.write(f"**{name}** — {doc_count} document(s)")
        else:
            st.info("You haven't created any repositories yet.")
            if st.button("➕ Create Your First Repository"):
                set_page("repositories")
    with chat_col:
        st.markdown("### 💬 Recent Conversations")
        if user_chat:
            for i, chat in enumerate(user_chat[:3]):
                with st.container():
                    title = chat["title"] if chat["title"] else f"Conversation #{i+1}"
                    last_msg = (
                        datetime.fromisoformat(chat["last_message"]["received_at"]).strftime("%d/%m/%Y")
                        if chat["last_message"] else datetime.fromisoformat(chat["created_at"]).strftime("%d/%m/%Y")
                    )
                    st.write(f"**{title}** — Last message: *{last_msg}*")
        else:
            st.info("No conversations yet. Start a chat with the assistant!")
            if st.button("💬 Open Assistant"):
                set_page("assistant")
    st.divider()
    st.markdown("### 🎯 Daily Challenges")
    if st.session_state.user.daily_challenges:
        daily_challenges = [challenge for challenge in st.session_state.user.daily_challenges.values()]
        ch1, ch2, ch3 = st.columns(3)
        for i, ch in enumerate(daily_challenges):
            with [ch1, ch2, ch3][i]:
                st.checkbox(ch["name"], value=ch["completed"], disabled=True, key="{ch['name']}_{i}")
                st.caption(f"{"✅ Completed" if ch['completed'] else "⏳ In progress"} | +{ch['xp_reward']} XP")
    else:
        st.info("It looks like you have a clear day! ☀️")
    st.divider()
    st.markdown("### 🤖 Personalized Suggestions")
    s1, s2 = st.columns(2)
    with s1:
        st.info("🚧 This feature will be implemented soon. Stay tuned!")
    with s2:
        st.info("🚧 This feature will be implemented soon. Stay tuned!")

main_content()
