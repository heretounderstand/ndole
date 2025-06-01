import streamlit as st
from typing import Dict, List
from model import Badge
from utils.badge import BADGES, get_earned_badges
from utils.user import update_user_badges

def display_badges():
    st.title("🏆 My Badges")
    st.markdown("---")
    if hasattr(st.session_state, 'user') and st.session_state.user:
        user_stats = st.session_state.user.get_total_stats()
        earned_badges = get_earned_badges(user_stats)
    else:
        st.warning("⚠️ User not logged in")
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="🏆 Earned Badges",
            value=len(earned_badges),
            delta=f"out of {len(BADGES)}"
        )
    with col2:
        progress = len(earned_badges) / len(BADGES) * 100
        st.metric(
            label="📊 Progress",
            value=f"{progress:.1f}%"
        )
    with col3:
        badge_types = set(badge.badge_type for badge in earned_badges)
        st.metric(
            label="💎 Unlocked Types",
            value=len(badge_types),
            delta="out of 5"
        )
    with col4:
        diamond_badges = len([b for b in earned_badges if b.badge_type == "diamond"])
        st.metric(
            label="💎 Diamond Badges",
            value=diamond_badges
        )
    st.markdown("---")
    st.markdown("### 📈 Overall Progress")
    st.progress(progress / 100)
    st.write(f"**{len(earned_badges)}/{len(BADGES)}** badges unlocked")
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🏆 Earned Badges", "🔒 All Badges", "📊 Statistics"])
    with tab1:
        display_earned_badges(earned_badges)
    with tab2:
        display_all_badges(earned_badges, user_stats)
    with tab3:
        display_badge_statistics(earned_badges, user_stats)
    if len(earned_badges) != len(st.session_state.user.badges):
        update_user_badges(st.session_state.user.user_id, [badge.badge_id for badge in earned_badges])

def get_badge_color(badge_type: str) -> str:
    colors = {
        "bronze": "#CD7F32",
        "silver": "#C0C0C0", 
        "gold": "#FFD700",
        "platinium": "#E5E4E2",
        "diamond": "#B9F2FF"
    }
    return colors.get(badge_type, "#808080")

def display_badge_card(badge: Badge, is_earned: bool = True, progress: float = None):
    color = get_badge_color(badge.badge_type)
    opacity = "1.0" if is_earned else "0.5"
    border_style = "solid" if is_earned else "dashed"
    card_style = f"""
    <div style="
        border: 2px {border_style} {color};
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        opacity: {opacity};
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    ">
        <div style="text-align: center;">
            <div style="font-size: 3em; margin-bottom: 10px;">{badge.icon}</div>
            <h4 style="color: {color}; margin: 5px 0;">{badge.name}</h4>
            <p style="color: #666; font-size: 0.9em; margin: 5px 0;">{badge.description}</p>
            <span style="
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                text-transform: uppercase;
            ">{badge.badge_type}</span>
        </div>
    """
    if progress is not None and not is_earned:
        card_style += f"""
        <div style="margin-top: 10px;">
            <div style="background-color: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden;">
                <div style="background-color: {color}; height: 100%; width: {min(progress * 100, 100):.1f}%; transition: width 0.3s ease;"></div>
            </div>
            <small style="color: #666;">{progress * 100:.1f}% completed</small>
        </div>
        """
    card_style += "</div>"
    return card_style

def display_earned_badges(earned_badges: List[Badge]):
    if not earned_badges:  
        st.info("🎯 No badges earned yet. Keep up the effort!")  
        return 
    st.markdown(f"### 🏆 Earned Badges ({len(earned_badges)})") 
    badges_by_type = {}
    for badge in earned_badges:
        if badge.badge_type not in badges_by_type:
            badges_by_type[badge.badge_type] = []
        badges_by_type[badge.badge_type].append(badge)
    type_order = ["diamond", "platinium", "gold", "silver", "bronze"]
    for badge_type in type_order:
        if badge_type in badges_by_type:
            st.markdown(f"#### {badge_type.title()} ({len(badges_by_type[badge_type])})")
            cols = st.columns(3)
            for i, badge in enumerate(badges_by_type[badge_type]):
                with cols[i % 3]:
                    st.markdown(display_badge_card(badge), unsafe_allow_html=True)

def calculate_badge_progress(badge: Badge, stats: Dict) -> float:
    try:
        if badge.badge_type == "bronze":
            order = 0 
        elif badge.badge_type == "silver":
            order = 1
        elif badge.badge_type == "gold": 
            order = 2
        elif badge.badge_type == "platinium": 
            order = 3
        elif badge.badge_type == "diamond": 
            order = 4  
        if "study_" in badge.badge_id.lower():
            targets = [3600, 36000, 180000, 360000, 900000]
            current = stats.get("total_study_time", 0)
            return current / targets[order]
        elif "reader_" in badge.badge_id.lower():
            targets = [1, 25, 100, 250, 500]
            current = stats.get("documents_read", 0)
            return current / targets[order]
        elif "repo_" in badge.badge_id.lower():
            targets = [1, 5, 20, 50, 100]
            current = stats.get("repositories_created", 0)
            return current / targets[order]
        elif "explorer_" in badge.badge_id.lower():
            targets = [1, 50, 150, 300, 500]
            current = stats.get("repositories_accessed", 0)
            return current / targets[order]
        elif "teacher_" in badge.badge_id.lower():
            targets = [1, 10, 25, 50, 100]
            current = stats.get("couses_created", 0)
            return current / targets[order]
        elif "careful_" in badge.badge_id.lower():
            targets = [[10, 0.7], [20, 0.8], [50, 0.95], [100, 0.98], [250, 0.995]]
            current = [stats.get("questions_answered", 0), stats.get("correct_answers", 0) / stats.get("questions_answered", 0)]
            if current[0] > targets[order][0]:
                return current[1] / targets[order][1]
        elif "chatter_" in badge.badge_id.lower():
            targets = [1, 10, 30, 75, 150]
            current = stats.get("chat_created", 0)
            return current / targets[order]
        elif "communicator_" in badge.badge_id.lower():
            targets = [1, 100, 500, 1000, 2500]
            current = stats.get("messages_sent", 0)
            return current / targets[order]
        elif "question_" in badge.badge_id.lower():
            targets = [1, 10, 50, 200, 500]
            current = stats.get("quizzes_created", 0)
            return current / targets[order]
        elif "quiz_" in badge.badge_id.lower():
            targets = [1, 5, 25, 100, 500]
            current = stats.get("quizzes_completed", 0)
            return current / targets[order]
        elif "routine_" in badge.badge_id.lower():
            targets = [3, 7, 30, 100, 365]
            current = stats.get("streak_days", 0)
            return current / targets[order]
        elif "xp_" in badge.badge_id.lower():
            targets = [1000, 10000, 50000, 100000, 500000]
            current = stats.get("xp_gained", 0)
            return current / targets[order]
        elif "content_" in badge.badge_id.lower():
            targets = [5, 25, 100, 500, 1000]
            current = stats.get("documents_uploaded", 0)
            return current / targets[order]
        elif "challenger_" in badge.badge_id.lower():
            targets = [1, 10, 25, 50, 100]
            current = stats.get("challenges_completed", 0)
            return current / targets[order]
        return 0.0
    except:
        return 0.0

def display_all_badges(earned_badges: List[Badge], user_stats: Dict):
    st.markdown("### 🗂️ All Available Badges")
    earned_ids = {badge.badge_id for badge in earned_badges}
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox(
            "Filter by type",
            ["All", "bronze", "silver", "gold", "platinium", "diamond"]
        )
    with col2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Earned", "Not earned"]
        )
    categories = {
        "Study": [b for b in BADGES if b.badge_id.startswith("study_")],
        "Reading": [b for b in BADGES if b.badge_id.startswith("reader_")],
        "Repositories": [b for b in BADGES if b.badge_id.startswith(("repo_", "explorer_"))],
        "Teaching": [b for b in BADGES if b.badge_id.startswith("teacher_")],
        "Communication": [b for b in BADGES if b.badge_id.startswith(("chatter_", "communicator_"))],
        "Quiz": [b for b in BADGES if b.badge_id.startswith(("question_", "quiz_"))],
        "Accuracy": [b for b in BADGES if b.badge_id.startswith("careful_")],
        "Regularity": [b for b in BADGES if b.badge_id.startswith(("routine_", "challenger_"))],
        "Experience": [b for b in BADGES if b.badge_id.startswith("xp_")],
        "Content": [b for b in BADGES if b.badge_id.startswith("content_")]
    }
    for category, badges in categories.items():
        with st.expander(f"📂 {category} ({len(badges)} badges)", expanded=False):
            filtered_badges = badges
            if filter_type != "All":
                filtered_badges = [b for b in filtered_badges if b.badge_type == filter_type]
            if filter_status == "Earned":
                filtered_badges = [b for b in filtered_badges if b.badge_id in earned_ids]
            elif filter_status == "Not earned":
                filtered_badges = [b for b in filtered_badges if b.badge_id not in earned_ids]
            cols = st.columns(2)
            for i, badge in enumerate(filtered_badges):
                with cols[i % 2]:
                    is_earned = badge.badge_id in earned_ids
                    progress = None if is_earned else calculate_badge_progress(badge, user_stats)
                    st.html(display_badge_card(badge, is_earned, progress))

def display_badge_statistics(earned_badges: List[Badge], user_stats: Dict):
    st.markdown("### 📊 Detailed Statistics")
    st.markdown("#### Distribution by Type")
    badge_counts = {}
    earned_counts = {}
    for badge in BADGES:
        badge_type = badge.badge_type
        badge_counts[badge_type] = badge_counts.get(badge_type, 0) + 1
        earned_counts[badge_type] = 0
    for badge in earned_badges:
        earned_counts[badge.badge_type] += 1
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Available Badges by Type:**")
        for badge_type, count in sorted(badge_counts.items()):
            color = get_badge_color(badge_type)
            st.markdown(f"<span style='color: {color}'>● {badge_type.title()}</span>: {count}", unsafe_allow_html=True)
    with col2:
        st.markdown("**Earned Badges by Type:**")
        for badge_type, count in sorted(earned_counts.items()):
            color = get_badge_color(badge_type)
            total = badge_counts[badge_type]
            percentage = (count / total * 100) if total > 0 else 0
            st.markdown(f"<span style='color: {color}'>● {badge_type.title()}</span>: {count}/{total} ({percentage:.1f}%)", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### 🎯 Next Objectives")
    earned_ids = {badge.badge_id for badge in earned_badges}
    next_badges = []
    for badge in BADGES:
        if badge.badge_id not in earned_ids:
            progress = calculate_badge_progress(badge, user_stats)
            if progress > 0:
                next_badges.append((badge, progress))
    next_badges.sort(key=lambda x: x[1], reverse=True)
    if next_badges:
        st.markdown("**Badges closest to being unlocked:**")
        for badge, progress in next_badges[:5]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.markdown(f"{badge.icon}")
            with col2:
                st.markdown(f"**{badge.name}**")
                st.progress(progress)
            with col3:
                st.markdown(f"{progress * 100:.1f}%")
    else:
        st.info("🎉 Congratulations! You're on track to unlock your next badges.")