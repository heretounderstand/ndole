import streamlit as st
from model import StudyStats
from utils.user import update_study_stats


def record_activity(is_login: bool = False, **fields) -> int:
    """Record a study event for the current user and keep the session XP in sync."""
    user = st.session_state.get("user")
    if not user:
        return 0
    xp = update_study_stats(user.user_id, StudyStats(**fields), is_login)
    user.experience_points += xp
    return xp
