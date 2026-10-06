import streamlit as st
from utils.auth import change_password
from utils.llm import LANGUAGES
from utils.user import update_learning_preferences

DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]
LEARNING_STYLES = ["visual", "auditory", "reading", "kinesthetic"]


def _index(options, value):
    return options.index(value) if value in options else 0


def display_settings():
    st.title("⚙️ Settings")
    user = st.session_state.user

    st.subheader("🎓 Learning preferences")
    st.caption("The AI assistant uses these to adapt the depth, vocabulary and language of its answers.")
    preferences = user.learning_preferences
    with st.form("preferences_form"):
        languages = list(LANGUAGES)
        language = st.selectbox("Preferred language", languages, index=_index(languages, preferences.preferred_language),
                                format_func=lambda code: LANGUAGES[code])
        difficulty = st.select_slider("Level", DIFFICULTY_LEVELS, value=preferences.difficulty_level
                                      if preferences.difficulty_level in DIFFICULTY_LEVELS else DIFFICULTY_LEVELS[0],
                                      format_func=str.title)
        style = st.selectbox("Learning style", LEARNING_STYLES, index=_index(LEARNING_STYLES, preferences.learning_style),
                             format_func=str.title)
        daily_minutes = st.number_input("Daily study goal (minutes)", min_value=0, max_value=600, step=5,
                                        value=preferences.daily_study_time)
        if st.form_submit_button("💾 Save preferences", type="primary"):
            updated = preferences.model_copy(update={
                "preferred_language": language,
                "difficulty_level": difficulty,
                "learning_style": style,
                "daily_study_time": int(daily_minutes),
            })
            if update_learning_preferences(user.user_id, updated):
                user.learning_preferences = updated
                st.success("Preferences saved.")
            else:
                st.error("Could not save your preferences. Please try again.")

    st.divider()
    st.subheader("🔑 Change password")
    with st.form("password_form", clear_on_submit=True):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update password"):
            if not current or not new:
                st.warning("Please complete all fields.")
            elif new != confirm:
                st.error("The new passwords do not match.")
            else:
                ok, message = change_password(user.username, current, new)
                (st.success if ok else st.error)(message)
