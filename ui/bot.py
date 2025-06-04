import streamlit as st
from utils.chat import create_chat_history, get_user_histories, update_chat_history, get_chat_messages, update_message, get_documents_embedding
from utils.llm import qa_chat, course_chat, exercise_chat, extract_qcm_data, extract_context
from utils.doc import get_document_repository
from utils.sql import process_llm_response
from utils.user import update_study_stats
from model import StudyStats

def display_chats():
    st.title("💬 Chat with AI")
    if 'user' not in st.session_state:
        st.error("You must be logged in to access chats.")
        st.stop()
    user_id = st.session_state.user.user_id
    if 'repo' in st.session_state:
        repo_id = st.session_state.repo.repo_id
    st.session_state.setdefault("chat", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("chat_session", None)
    st.session_state.setdefault("chat_histories", [])
    with st.expander("📂 Manage my conversations", expanded=True):
        st.markdown("### ✨ New conversation")
        chat_type = st.selectbox(
            "Chat type",
            ["qa", "course", "exercise"],
            format_func=lambda x: {
                "qa": "❓ Q&A",
                "course": "📚 Course generation",
                "exercise": "📝 Exercise generation"
            }[x]
        )
        chat_title = st.text_input("Conversation title", value="New conversation")
        if 'repo' in st.session_state and len(st.session_state.chunks)>0:
            if st.button("➕ Create conversation"):
                new_chat_id = create_chat_history(user_id, repo_id, chat_type, chat_title)
                if new_chat_id:
                    st.session_state.user.chat_histories.append(new_chat_id)
                    st.session_state.chat_session = None
                    st.session_state.messages = []
                    xp_up = update_study_stats(user_id, StudyStats(xp_gained=5, chat_created=1))
                    if xp_up:
                        st.session_state.user.experience_points += 5
                    st.success(f"Conversation '{chat_title}' created successfully!")
                    st.rerun()
        else:
            st.warning("Please select a document repository with at least one document to create a conversation.")
        st.divider()
        user_chat_ids = st.session_state.user.chat_histories
        if user_chat_ids:
            st.session_state.chat_histories = get_user_histories(user_chat_ids)
        if st.session_state.chat_histories:
            st.markdown("### 📜 My existing conversations")
            for chat_history in st.session_state.chat_histories:
                with st.container(border=True):
                    col1, col2 = st.columns([6, 2])
                    with col1:
                        st.markdown(f"**🗂️ {chat_history.title}** &nbsp; `({chat_history.type})`")
                        if chat_history.last_message:
                            st.markdown(f"🕒 **Last message**: {chat_history.last_message.content[:50]}...")
                            st.caption(f"📅 {chat_history.last_message.get_received_at().strftime('%d %b %Y • %H:%M')}")
                        else:
                            st.caption(f"📅 Created on {chat_history.get_created_at().strftime('%d %b %Y • %H:%M')}")
                    with col2:
                        col_select, col_edit, col_delete = st.columns([1.5, 1, 1])
                        with col_select:
                            if st.button("▶️", key=f"select_{chat_history.chat_id}"):
                                st.session_state.chat = chat_history
                                st.session_state.repo = get_document_repository(chat_history.repo_source)
                                st.session_state.chunks = get_documents_embedding(st.session_state.repo.documents)
                                message_ids = chat_history.messages
                                st.session_state.messages = get_chat_messages(message_ids)
                                st.session_state.chat_session = None
                                st.rerun()
                        with col_edit:
                            if st.button("✏️", key=f"edit_{chat_history.chat_id}"):
                                st.session_state.edit_chat = chat_history
                                st.rerun()
                        with col_delete:
                            if st.button("🗑️", key=f"delete_{chat_history.chat_id}"):
                                update_chat_history(chat_history.chat_id, is_deleted=True)
                                st.rerun()
        else:
            st.info("💡 No existing conversations. Create one to get started!")
        st.divider()
        if "edit_chat" in st.session_state and st.session_state.edit_chat:
            chat = st.session_state.edit_chat
            st.markdown("### 🛠️ Edit conversation")
            new_title = st.text_input("Current title:", value=chat.title)
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("💾 Save"):
                    update_chat_history(chat.chat_id, title=new_title)
                    st.session_state.edit_chat = None
                    st.success("✏️ Title modified successfully!")
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel"):
                    st.session_state.edit_chat = None
                    st.rerun()
    if st.session_state.chat:
        st.subheader(f"{st.session_state.chat.title}")
        chat_type = st.session_state.chat.type
        chat_container = st.container(border=True)
        with chat_container:
            for j ,msg in enumerate(st.session_state.messages):
                if msg.is_assistant:
                    formatted_msg = process_llm_response(msg.content)
                    questions = extract_qcm_data(formatted_msg)
                    if len(questions) > 0:
                        if msg.score:
                            display_qcm_results(msg.score, questions)
                        else:
                            qcm_message(questions, j)
                    else:
                        st.chat_message("assistant").markdown(formatted_msg)
                else:
                    st.chat_message("user").markdown(extract_context(msg.content))
        st.divider()
        if chat_type == "qa":
            display_qa_interface()
        elif chat_type == "course":
            display_course_interface()
        elif chat_type == "exercise":
            display_exercise_interface()
    else:
        st.info("Select an existing conversation or create a new one to get started.")
        
def display_qa_interface():
    user_message = st.chat_input("Posez votre question...")
    if user_message:
        st.chat_message("user").markdown(user_message)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ Looking for the answer...")
            st.session_state.chat_session ,response, success, msgs = qa_chat(
                st.session_state.chat, 
                user_message, 
                st.session_state.chunks,
                st.session_state.messages,
                st.session_state.chat_session
            )
            if success:
                st.session_state.messages.extend(msgs)
                for msg in msgs:
                    st.session_state.chat.messages.append(msg.message_id)
                message_placeholder.markdown(process_llm_response(response))
                xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=2, messages_sent=1))
                if xp_up:
                    st.session_state.user.experience_points += 2
            else:
                message_placeholder.markdown("❌ " + response)
        st.rerun()

def display_course_interface():
    if not st.session_state.chat.mode:
        with st.form("course_form"):
            topic = st.text_input("Course topic", placeholder="E.g.: Introduction to Python, Linear Algebra...")
            col1, col2 = st.columns(2)
            with col1:
                use_specific_page = st.checkbox("Use a specific page")
            with col2:
                page_number = None
                if use_specific_page:
                    page_number = st.number_input("Page number", min_value=1, value=1)
            if st.form_submit_button("Generate the course"):
                if topic:
                    with st.chat_message("user"):
                        st.markdown(f"Generating a course on: **{topic}**")
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("⏳ Generating the course...")
                        st.session_state.chat_session ,response, success, msgs = course_chat(
                            st.session_state.chat,
                            topic,
                            st.session_state.chunks,
                            st.session_state.messages,
                            page_number if use_specific_page else None,
                            st.session_state.chat_session
                        )
                        if success:
                            st.session_state.messages.extend(msgs)
                            for msg in msgs:
                                st.session_state.chat.messages.append(msg.message_id)
                            placeholder.markdown(process_llm_response(response))
                            update_chat_history(
                                st.session_state.chat.chat_id,
                                mode=True
                            )
                            st.session_state.chat.mode = True
                            xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=10, messages_sent=1, couses_created=1))
                            if xp_up:
                                st.session_state.user.experience_points += 10
                        else:
                            placeholder.markdown("❌ " + response)
                    st.rerun()
                else:
                    st.error("Please specify a course topic")
    else:
        user_message = st.chat_input("Ask a question about this course...")
        if user_message:
            st.chat_message("user").markdown(user_message)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("⏳ Looking for the answer...")
                st.session_state.chat_session ,response, success, msgs = qa_chat(
                    st.session_state.chat, 
                    user_message, 
                    st.session_state.chunks,
                    st.session_state.messages,
                    st.session_state.chat_session
                )
                if success:
                    st.session_state.messages.extend(msgs)
                    for msg in msgs:
                        st.session_state.chat.messages.append(msg.message_id)
                    placeholder.markdown(process_llm_response(response))
                    xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=2, messages_sent=1))
                    if xp_up:
                        st.session_state.user.experience_points += 2
                else:
                    placeholder.markdown("❌ " + response)
            st.rerun()
        reset_course = st.button("Generate a new course", key="reset_course_btn")
        if reset_course:
            update_chat_history(
                st.session_state.chat.chat_id,
                mode=False
            )
            st.session_state.chat.mode = False
            st.rerun()

def display_exercise_interface():
    if not st.session_state.chat.mode:
        with st.form("exercise_form"):
            topic = st.text_input("Exercises topic", placeholder="E.g.: Variables in Python, Quadratic equations...")
            num_exercises = st.slider("Number of exercises", min_value=1, max_value=5, value=3)
            if st.form_submit_button("Generate exercises"):
                if topic:
                    with st.chat_message("user"):
                        st.markdown(f"Generating {num_exercises} exercises on: **{topic}**")
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("⏳ Generating exercises...")
                        st.session_state.chat_session, response, success, msgs = exercise_chat(
                            st.session_state.chat,
                            topic,
                            st.session_state.chunks,
                            st.session_state.messages,
                            num_exercises,
                            st.session_state.chat_session
                        )
                        if success:
                            st.session_state.messages.extend(msgs)
                            for msg in msgs:
                                st.session_state.chat.messages.append(msg.message_id)
                            placeholder.markdown(process_llm_response(response))
                            update_chat_history(
                                st.session_state.chat.chat_id,
                                mode=True
                            )
                            st.session_state.chat.mode = True
                            xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=5 + num_exercises, 
                                                                                         messages_sent=1, 
                                                                                         quizzes_created=1,
                                                                                         questions_asked=num_exercises
                                                                                         ))
                            if xp_up:
                                st.session_state.user.experience_points += 5 + num_exercises
                        else:
                            placeholder.markdown("❌ " + response)
                    st.rerun()
                else:
                    st.error("Please specify a topic for the exercises")
    else:
        user_message = st.chat_input("Posez une question sur ces exercices...")
        if user_message:
            st.chat_message("user").markdown(user_message)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("⏳ Looking for the answer...")
                st.session_state.chat_session ,response, success, msgs = qa_chat(
                    st.session_state.chat, 
                    user_message, 
                    st.session_state.chunks,
                    st.session_state.messages,
                    st.session_state.chat_session
                )
                if success:
                    st.session_state.messages.extend(msgs)
                    for msg in msgs:
                        st.session_state.chat.messages.append(msg.message_id)
                    placeholder.markdown(process_llm_response(response))
                    xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=2, messages_sent=1))
                    if xp_up:
                        st.session_state.user.experience_points += 2
                else:
                    placeholder.markdown("❌ " + response)
            st.rerun()
        reset_exercise = st.button("Generate new exercises", key="reset_exercise_btn")
        if reset_exercise:
            update_chat_history(
                st.session_state.chat.chat_id,
                mode=False
            )
            st.session_state.chat.mode = False
            st.rerun()
            
def qcm_message(questions: list, j: int):
    with st.form(key=f"qcm_form_{j}"):
        st.subheader("Answer the questions:")
        user_answers = {}
        for i, question in enumerate(questions):
            st.markdown(f"**Question {i+1}**: {question['stem']}")
            options = question["options"]
            answer = st.radio(
                f"Q{i+1}",
                options.keys(),
                format_func=lambda x: f"{x}. {options[x]}",
                key=f"q_{i}"
            )
            user_answers[i] = answer
        submit_button = st.form_submit_button("Submit my answers")
        if submit_button:
            correct_count = 0
            total = len(questions)
            for i, question in enumerate(questions):
                if user_answers[i] == question["correct_answer"]:
                    correct_count += 1
            score = {
                "correct": correct_count,
                "total": total,
                "answers": user_answers
            }
            success = update_message(
                st.session_state.messages[j].message_id,
                score=score
            )
            if success:
                st.session_state.messages[j].score = score
                xp_up = update_study_stats(st.session_state.user.user_id, StudyStats(xp_gained=5 + 2 * correct_count, 
                                                                             quizzes_completed=1, 
                                                                             questions_answered=total,
                                                                             correct_answers=correct_count 
                                                                             ))
                if xp_up:
                    st.session_state.user.experience_points += 5 + 2 * correct_count
            else:
                st.error("Error while submitting answers. Please try again.")
            st.rerun()
            
def display_qcm_results(score, questions):
    correct_count = score["correct"]
    total = score["total"]
    answers = score["answers"]
    if correct_count == total:
        st.success(f"You scored {correct_count}/{total}. 🎉 Excellent work! You got everything right.")
    elif correct_count >= total / 2:
        st.warning(f"You scored {correct_count}/{total}. 👍 Good job! You understood the topic well.")
    else:
        st.error(f"You scored {correct_count}/{total}. ❌ It seems you need to review the topic.")
    with st.expander("See answer details"):
        for i, answer in answers.items():
            st.write(f"{questions[int(i)]["stem"]}: You have answered '{answer}'. The correct answer was: '{questions[int(i)]["correct_answer"]}'.")
            st.info(questions[int(i)]["explanation"])
            st.divider()
