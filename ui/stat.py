import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from model import parse_dt
from utils.user import get_user

def display_statistics():
    user = get_user(st.session_state.user.user_id) or st.session_state.user
    st.session_state.user = user
    total_stats = user.get_total_stats()
    st.title("📊 My Statistics")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1B5E20, #2E7D32); border-radius: 15px; color: #E0F2F1; margin-bottom: 30px; font-family: 'Segoe UI', sans-serif;">
            <h2 style="margin: 0;">{user.username}</h2>
            <p style="margin: 5px 0;">Member since {user.get_created_at().strftime('%B %d, %Y')}</p>
            <h3 style="margin: 10px 0;">🏆 Level {user.calculate_level()}</h3>
            <p style="margin: 0;">{user.experience_points} XP / {user.calculate_level(is_next=True)} XP</p>
        </div>
        """, unsafe_allow_html=True)
    st.progress(user.level_progress())
    st.caption(f"Progress towards level {user.calculate_level() + 1}")
    if user.study_stats:
        latest_stats = user.study_stats[-1]
        st.markdown("### 📈 Overview")
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "⏱️ Total Study Time",
                f"{total_stats['total_study_time'] // 3600}h {(total_stats['total_study_time'] % 3600) // 60}m",
                delta=(
                    f"+{latest_stats.total_study_time // 3600}h {(latest_stats.total_study_time % 3600) // 60}m"
                    if latest_stats.total_study_time > 0 else None
                )
            )
        with col2:
            st.metric(
                "📚 Challenges Completed",
                total_stats["challenges_completed"],
                delta=f"+{latest_stats.challenges_completed}" if latest_stats.challenges_completed > 0 else None
            )
        with col3:
            streak_delta = (
                latest_stats.streak_days - (user.study_stats[-2].streak_days if len(user.study_stats) > 1 else 0)
            )
            st.metric(
                "🔥 Daily Streak",
                f"{latest_stats.streak_days} days",
                delta=f"+{streak_delta}" if streak_delta > 0 else None
            )
        with col4:
            st.metric(
                "⭐ Total XP",
                f"{user.experience_points} XP",
                delta=f"+{latest_stats.xp_gained}" if latest_stats.xp_gained > 0 else None
            )
        st.markdown("---")
        if len(user.study_stats) > 1:
            xp_history = [stats.xp_gained for stats in user.study_stats]
            dates = [parse_dt(stats.last_activity).date() for stats in user.study_stats]
            fig_xp = px.line(
                x=dates,
                y=xp_history,
                labels={'x': 'Date', 'y': 'XP Gained'},
                title="XP Progress Over Time"
            )
            fig_xp.update_traces(line_width=3)
            fig_xp.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                template="plotly_dark"
            )
            st.plotly_chart(fig_xp, width="stretch")
        else:
            st.info("Not enough data to display XP progression.")
        with st.expander("📂 Documents and Repositories"):
            if len(user.study_stats) > 1:
                dates = [parse_dt(stats.last_activity).date() for stats in user.study_stats]
                metrics = {
                    "Documents Read": [stats.documents_read for stats in user.study_stats],
                    "Documents Uploaded": [stats.documents_uploaded for stats in user.study_stats],
                    "Repositories Accessed": [stats.repositories_accessed for stats in user.study_stats],
                    "Repositories Created": [stats.repositories_created for stats in user.study_stats],
                }
                fig = go.Figure()
                for label, values in metrics.items():
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=values,
                        mode='lines+markers',
                        name=label,
                        line=dict(width=3)
                    ))
                fig.update_layout(
                    height=400,
                    xaxis_title="Date",
                    yaxis_title="Value",
                    template="plotly_dark",
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend_title="Activity"
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Not enough data to display activity evolution.")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📝 Document Activity")
                doc_labels = ['Documents Read', 'Documents Uploaded']
                doc_values = [
                    total_stats["documents_read"],
                    total_stats["documents_uploaded"]
                ]
                fig_pie_docs = px.pie(
                    values=doc_values,
                    names=doc_labels,
                    title="Document Distribution",
                    hole=0.4
                )
                fig_pie_docs.update_traces(textinfo='percent+label')
                fig_pie_docs.update_layout(height=300, template="plotly_dark")
                st.plotly_chart(fig_pie_docs, width="stretch")
            with col2:
                st.markdown("#### 🗃️ Repository Activity")
                repo_labels = ['Repositories Created', 'Repositories Accessed']
                repo_values = [
                    total_stats["repositories_created"],
                    total_stats["repositories_accessed"]
                ]
                fig_pie_repos = px.pie(
                    values=repo_values,
                    names=repo_labels,
                    title="Repository Distribution",
                    hole=0.4
                )
                fig_pie_repos.update_traces(textinfo='percent+label')
                fig_pie_repos.update_layout(height=300, template="plotly_dark")
                st.plotly_chart(fig_pie_repos, width="stretch")
        with st.expander("💬 Chats"):
            if len(user.study_stats) > 1:
                dates = [parse_dt(stats.last_activity).date() for stats in user.study_stats]
                metrics = {
                    "Answered Questions": [stats.questions_answered for stats in user.study_stats],
                    "Correct Answers": [stats.correct_answers for stats in user.study_stats],
                    "Questions Asked": [stats.questions_asked for stats in user.study_stats],
                    "Chats Created": [stats.chat_created for stats in user.study_stats],
                    "Messages Sent": [stats.messages_sent for stats in user.study_stats],
                    "Courses Followed": [stats.couses_created for stats in user.study_stats],
                    "Exercises Created": [stats.quizzes_created for stats in user.study_stats],
                    "Exercises Completed": [stats.quizzes_completed for stats in user.study_stats]
                }
                st.markdown("#### 📈 Activity Progress Over Time")
                fig = go.Figure()
                for label, values in metrics.items():
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=values,
                        mode='lines+markers',
                        name=label,
                        line=dict(width=3)
                    ))
                fig.update_layout(
                    height=400,
                    xaxis_title="Date",
                    yaxis_title="Count",
                    template="plotly_dark",
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend_title="Metric"
                )
                st.plotly_chart(fig, width="stretch")
                st.markdown("#### 🧭 Metric Distribution by Category")
                categories = {
                    "Learning": ["Answered Questions", "Correct Answers", "Questions Asked"],
                    "Communication": ["Chats Created", "Messages Sent"],
                    "Content": ["Courses Followed", "Exercises Created", "Exercises Completed"]
                }
                treemap_data = []
                for category, metric_names in categories.items():
                    for metric_name in metric_names:
                        if metric_name in metrics:
                            total_value = sum(metrics[metric_name])
                            if total_value > 0:
                                treemap_data.append({
                                    'Category': category,
                                    'Metric': metric_name,
                                    'Value': total_value,
                                    'Label': f"{metric_name}<br>{total_value:,}"
                                })
                if not treemap_data:
                    st.info("No activity to break down yet.")
                else:
                    df = pd.DataFrame(treemap_data)
                    fig_treemap = px.treemap(
                        df,
                        path=['Category', 'Metric'],
                        values='Value',
                        color='Value',
                        color_continuous_scale='Tealgrn',
                        hover_data={'Value': ':,'}
                    )
                    fig_treemap.update_traces(
                        textinfo="label+value",
                        textfont_size=12,
                        marker_line_width=2,
                        marker_line_color='white'
                    )
                    fig_treemap.update_layout(
                        title={
                            'text': 'Study Metric Distribution by Category',
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 16}
                        },
                        font=dict(family="Arial", size=10),
                        height=600,
                        margin=dict(t=60, l=20, r=20, b=20),
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_treemap, width="stretch")
            else:
                st.info("Not enough data to display activity metrics.")
        st.markdown("### 💡 Personalized Advice")
        advice_col1, advice_col2 = st.columns(2)
        with advice_col1:
            if latest_stats.streak_days < 3:
                st.warning("🔥 Try to maintain a 7-day study streak to boost your learning!")
            elif latest_stats.streak_days >= 7:
                st.success("🔥 Great streak! Keep up the momentum!")
            else:
                st.info("🚀 You're halfway there! Just a few more days to hit that 7-day streak.")
        with advice_col2:
            if total_stats["questions_answered"] > 0:
                accuracy = (total_stats["correct_answers"] / total_stats["questions_answered"]) * 100
                if accuracy < 70:
                    st.warning("📚 Take more time to review before answering quizzes.")
                elif accuracy >= 90:
                    st.success("🎯 Amazing accuracy! You're mastering the content!")
                else:
                    st.info("👍 You're on the right track! A bit more practice will take you to the top.")
    else:
        st.info("No statistics available yet. Start using the platform to track your progress!")
        st.markdown("## 📊 Basic Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👤 Username", user.username)
        with col2:
            st.metric("📅 Member Since", user.get_created_at().strftime('%d/%m/%Y'))
        with col3:
            st.metric("🏆 Level", user.calculate_level())
    