import streamlit as st
from datetime import datetime, timezone
from model import parse_dt
from ui.common import record_activity
from ui.setting import display_settings
from ui.game import display_polynomialle
from utils.auth import login_user, register_user, generate_credentials, check_credentials
from utils.user import get_user, list_repositories, list_histories
from ui.repo import display_document_repositories
from ui.bot import display_chats
from ui.stat import display_statistics
from ui.trophy import display_badges

st.set_page_config(
    page_title="Ndolè - Intelligent Learning Assistant",
    page_icon="📚",
    layout="wide"
)


def logout():
    # Clear everything (selected repository, open chat, messages...) so nothing
    # from this account is visible to the next person using the same browser.
    st.session_state.clear()


def calculate_user_stats(user):
    created_at = user.get_created_at()
    return {
        "documents_count": len(user.repositories),
        "conversations_count": len(user.chat_histories),
        "days_active": (datetime.now(timezone.utc) - created_at).days,
    }


def handle_login(username, password):
    success, message, user = login_user(username, password)
    if not success:
        st.error(message)
        return
    st.session_state.user = user
    record_activity(is_login=True, xp_gained=10)
    st.rerun()


def handle_registration(username, password, method="manual"):
    if method == "auto":
        credentials = generate_credentials()
        username, password = credentials["username"], credentials["password"]
    success, message, user = register_user(username, password)
    if not success:
        st.error(message)
        return
    st.session_state.user = user
    if method == "auto":
        st.session_state.new_credentials = {"username": username, "password": password}
    record_activity(is_login=True, xp_gained=10)
    st.rerun()


def display_landing_page():
    st.markdown("# 🌿 Discover Ndolè: Your Intelligent Learning Assistant")
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
                if st.form_submit_button("Log In", type="primary"):
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
                    username = st.text_input("Choose a Username", help="4-20 characters: letters, numbers and _")
                    password = st.text_input("Create a Password", type="password",
                                             help="8+ characters with upper and lower case letters, a number and a special character")
                    password_confirm = st.text_input("Confirm Password", type="password")
                    if st.form_submit_button("Sign Up", type="primary"):
                        if not username or not password:
                            st.warning("Please complete all fields.")
                        elif password != password_confirm:
                            st.error("Passwords do not match.")
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
                    st.caption("We create a username and a strong password for you. You will see them once: save them!")
                    if st.form_submit_button("Generate My Account", type="primary"):
                        handle_registration("", "", "auto")
    st.divider()
    st.markdown("### 🤝 Our Commitment")
    st.info("""
    Ndolè adapts to all learning styles and disciplines. Whether you're a student, professional, or curious mind,
    we’re here to support your growth and curiosity.
    """)
    st.success("✨ Join the Ndolè community today and discover a smarter, more personal way to learn!")


def display_new_credentials():
    credentials = st.session_state.get("new_credentials")
    if not credentials:
        return
    with st.container(border=True):
        st.success("🎉 Your account has been created! Here are your login credentials. "
                   "They will not be shown again, so store them in a safe place.")
        st.code(f"Username: {credentials['username']}\nPassword: {credentials['password']}", language=None)
        if st.button("I have saved them"):
            del st.session_state.new_credentials
            st.rerun()


def display_user_dashboard():
    fresh = get_user(st.session_state.user.user_id)
    if fresh:
        st.session_state.user = fresh
    user = st.session_state.user
    display_new_credentials()
    st.markdown(f"## 👋 Welcome back, **{user.username}**!")
    st.write("Here’s a snapshot of your progress on Ndolè:")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### 🧠 Your Progress")
        st.progress(user.level_progress())
        st.caption(f"{user.experience_points} XP / {user.calculate_level(is_next=True)} XP to reach level {user.calculate_level() + 1}")
    with col2:
        st.metric("⭐ Current Level", user.calculate_level())
    st.divider()
    st.markdown("### 📊 Your Activity Overview")
    stats = calculate_user_stats(user)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 Repositories", stats["documents_count"])
    col2.metric("💬 Conversations", stats["conversations_count"])
    col3.metric("📆 Days since joining", stats["days_active"])
    col4.metric("🏅 Badges", len(user.badges))
    st.divider()
    repo_col, chat_col = st.columns(2)
    user_repo = list_repositories(user.repositories)
    user_chat = list_histories(user.chat_histories)
    with repo_col:
        st.markdown("### 📁 Recent Repositories")
        if user_repo:
            for i, repo in enumerate(user_repo[:3]):
                name = repo["name"] or f"Repository #{i + 1}"
                st.write(f"**{name}** — {len(repo['documents'] or [])} document(s)")
        else:
            st.info("You haven't created any repositories yet.")
            if st.button("➕ Create Your First Repository"):
                st.switch_page(PAGES["repositories"])
    with chat_col:
        st.markdown("### 💬 Recent Conversations")
        if user_chat:
            for i, chat in enumerate(user_chat[:3]):
                title = chat["title"] or f"Conversation #{i + 1}"
                when = chat["last_message"]["received_at"] if chat["last_message"] else chat["created_at"]
                st.write(f"**{title}** — Last message: *{parse_dt(when).strftime('%d/%m/%Y')}*")
        else:
            st.info("No conversations yet. Start a chat with the assistant!")
            if st.button("💬 Open Assistant"):
                st.switch_page(PAGES["assistant"])
    st.divider()
    st.markdown("### 🎯 Daily Challenges")
    if user.daily_challenges:
        columns = st.columns(len(user.daily_challenges))
        for i, (col, ch) in enumerate(zip(columns, user.daily_challenges.values())):
            with col:
                st.checkbox(ch["name"], value=ch["completed"], disabled=True, key=f"challenge_{i}")
                status = "✅ Completed" if ch["completed"] else "⏳ In progress"
                st.caption(f"{status} | +{ch['xp_reward']} XP")
    else:
        st.info("It looks like you have a clear day! ☀️")


def sidebar():
    with st.sidebar:
        st.image("logo.png", width=150)
        st.title("Ndolè")
        st.caption("Your Learning Assistant")
        if st.session_state.get("user"):
            user = st.session_state.user
            st.caption(f"Signed in as **{user.username}** · Level {user.calculate_level()}")
            st.button("Logout", width="stretch", on_click=logout)
        else:
            st.markdown("### About")
            st.markdown("Ndolè is an AI-powered learning assistant that helps you organize your documents and optimize your learning.")
            st.divider()
            st.markdown("### Features")
            st.markdown("• Document management\n• Conversational AI assistant\n• Personalized content generation\n• Tracking & Analytics\n• Gamification system")


PAGES = {
    "home": st.Page(display_user_dashboard, title="Home", icon="🏠", url_path="home", default=True),
    "repositories": st.Page(display_document_repositories, title="My Repositories", icon="📚", url_path="repositories"),
    "assistant": st.Page(display_chats, title="AI Assistant", icon="🤖", url_path="assistant"),
    "stats": st.Page(display_statistics, title="Statistics", icon="📊", url_path="statistics"),
    "achievements": st.Page(display_badges, title="Badges and Levels", icon="🏆", url_path="badges"),
    "settings": st.Page(display_settings, title="Settings", icon="⚙️", url_path="settings"),
    "game": st.Page(display_polynomialle, title="Polynomialle", icon="🎲", url_path="polynomialle"),
}

if st.session_state.get("user"):
    navigation = st.navigation(list(PAGES.values()))
else:
    navigation = st.navigation([st.Page(display_landing_page, title="Welcome", icon="🌿", default=True)])
sidebar()
navigation.run()
