import streamlit as st
from ui.common import record_activity
from utils.chat import create_chat_history, get_user_histories, update_chat_history, get_chat_messages, update_message, get_documents_embedding
from utils.llm import qa_chat, course_chat, exercise_chat, extract_qcm_data, extract_context
from utils.doc import get_document_repository
from utils.sql import process_llm_response

CHAT_TYPES = {
    "qa": "❓ Q&A",
    "course": "📚 Course generation",
    "exercise": "📝 Exercise generation",
}


@st.cache_data(max_entries=500, show_spinner=False)
def render_message(content: str) -> str:
    # Running the SymPy blocks is pure but not free: cache per message content.
    return process_llm_response(content)


def open_chat(chat_history):
    repo = get_document_repository(chat_history.repo_source)
    if repo is None:
        st.error("The repository used by this conversation no longer exists.")
        return
    st.session_state.chat = chat_history
    st.session_state.repo = repo
    st.session_state.chunks = get_documents_embedding(repo.documents)
    st.session_state.messages = get_chat_messages(chat_history.messages)
    st.session_state.chat_session = None
    st.rerun()


def close_chat():
    st.session_state.chat = None
    st.session_state.messages = []
    st.session_state.chat_session = None


def manage_conversations(user_id: str):
    st.markdown("### ✨ New conversation")
    repo = st.session_state.get("repo")
    if repo and st.session_state.get("chunks"):
        st.caption(f"Based on the repository **{repo.name}**.")
        chat_type = st.selectbox("Chat type", list(CHAT_TYPES), format_func=CHAT_TYPES.get)
        chat_title = st.text_input("Conversation title", value="New conversation", max_chars=80)
        if st.button("➕ Create conversation", type="primary"):
            new_chat_id = create_chat_history(user_id, repo.repo_id, chat_type, chat_title.strip() or "New conversation")
            st.session_state.user.chat_histories.append(new_chat_id)
            record_activity(xp_gained=5, chat_created=1)
            history = next((h for h in get_user_histories([new_chat_id])), None)
            if history:
                open_chat(history)
    else:
        st.warning("Open a repository that contains at least one indexed document (📚 My Repositories → 🔎 View) to create a conversation.")
    st.divider()
    histories = get_user_histories(st.session_state.user.chat_histories)
    if not histories:
        st.info("💡 No existing conversations. Create one to get started!")
        return
    st.markdown("### 📜 My existing conversations")
    for chat_history in histories:
        with st.container(border=True):
            col1, col2 = st.columns([6, 2])
            with col1:
                st.markdown(f"**🗂️ {chat_history.title}** &nbsp; `{CHAT_TYPES.get(chat_history.type, chat_history.type)}`")
                if chat_history.last_message:
                    preview = extract_context(chat_history.last_message.content)
                    st.markdown(f"🕒 **Last message**: {preview[:60]}{'...' if len(preview) > 60 else ''}")
                    st.caption(f"📅 {chat_history.last_message.get_received_at().strftime('%d %b %Y • %H:%M')}")
                else:
                    st.caption(f"📅 Created on {chat_history.get_created_at().strftime('%d %b %Y • %H:%M')}")
            with col2:
                col_select, col_edit, col_delete = st.columns(3)
                if col_select.button("▶️", key=f"select_{chat_history.chat_id}", help="Open"):
                    open_chat(chat_history)
                if col_edit.button("✏️", key=f"edit_{chat_history.chat_id}", help="Rename"):
                    st.session_state.edit_chat = chat_history
                    st.rerun()
                if col_delete.button("🗑️", key=f"delete_{chat_history.chat_id}", help="Delete"):
                    update_chat_history(chat_history.chat_id, is_deleted=True)
                    current = st.session_state.get("chat")
                    if current and current.chat_id == chat_history.chat_id:
                        close_chat()
                    st.rerun()
    chat = st.session_state.get("edit_chat")
    if chat:
        st.divider()
        st.markdown("### 🛠️ Edit conversation")
        new_title = st.text_input("Title", value=chat.title, max_chars=80)
        col_save, col_cancel = st.columns(2)
        if col_save.button("💾 Save"):
            update_chat_history(chat.chat_id, title=new_title.strip())
            current = st.session_state.get("chat")
            if current and current.chat_id == chat.chat_id:
                current.title = new_title.strip()
            st.session_state.edit_chat = None
            st.rerun()
        if col_cancel.button("❌ Cancel"):
            st.session_state.edit_chat = None
            st.rerun()


def display_chats():
    st.title("💬 Chat with AI")
    user_id = st.session_state.user.user_id
    for key, default in (("chat", None), ("messages", []), ("chat_session", None), ("chunks", [])):
        st.session_state.setdefault(key, default)
    with st.expander("📂 Manage my conversations", expanded=st.session_state.chat is None):
        manage_conversations(user_id)
    chat = st.session_state.chat
    if not chat:
        st.info("Select an existing conversation or create a new one to get started.")
        return
    st.subheader(chat.title)
    with st.container(border=True):
        for j, msg in enumerate(st.session_state.messages):
            if not msg.is_assistant:
                st.chat_message("user").markdown(render_message(extract_context(msg.content)))
                continue
            formatted_msg = render_message(msg.content)
            questions = extract_qcm_data(formatted_msg)
            if not questions:
                st.chat_message("assistant").markdown(formatted_msg)
            elif msg.score:
                display_qcm_results(msg.score, questions)
            else:
                qcm_message(questions, j)
    if chat.type == "course" and not chat.mode:
        display_course_form()
    elif chat.type == "exercise" and not chat.mode:
        display_exercise_form()
    else:
        display_follow_up(chat.type)


def _generate(chat_fn, user_display: str, waiting: str, *args) -> bool:
    """Run one generation, streaming it into the chat. Returns True on success."""
    st.chat_message("user").markdown(user_display)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(f"⏳ {waiting}")
        st.session_state.chat_session, response, success, msgs = chat_fn(
            st.session_state.chat,
            *args,
            chat_session=st.session_state.chat_session,
            preferences=st.session_state.user.learning_preferences,
            on_text=lambda text: placeholder.markdown(text + " ▌"),
        )
        if not success:
            placeholder.error(response)
            return False
        placeholder.markdown(render_message(response))
    st.session_state.messages.extend(msgs)
    st.session_state.chat.messages.extend(msg.message_id for msg in msgs)
    return True


def _set_mode(mode: bool):
    update_chat_history(st.session_state.chat.chat_id, mode=mode)
    st.session_state.chat.mode = mode


def display_follow_up(chat_type: str):
    placeholder = {
        "qa": "Ask your question...",
        "course": "Ask a question about this course...",
        "exercise": "Ask a question about these exercises...",
    }[chat_type]
    if chat_type in ("course", "exercise"):
        label = "🔄 Generate a new course" if chat_type == "course" else "🔄 Generate new exercises"
        if st.button(label):
            _set_mode(False)
            st.rerun()
    user_message = st.chat_input(placeholder)
    if user_message:
        user_message = render_message(user_message)
        if _generate(qa_chat, user_message, "Looking for the answer...", user_message,
                     st.session_state.chunks, st.session_state.messages):
            record_activity(xp_gained=2, messages_sent=1)
        st.rerun()


def display_course_form():
    with st.form("course_form"):
        topic = st.text_input("Course topic", placeholder="E.g.: Introduction to Python, Linear Algebra...")
        col1, col2 = st.columns(2)
        use_specific_page = col1.checkbox("Use a specific page")
        page_number = col2.number_input("Page number", min_value=1, value=1)
        submitted = st.form_submit_button("Generate the course", type="primary")
    if not submitted:
        return
    if not topic.strip():
        st.error("Please specify a course topic")
        return
    if _generate(course_chat, f"Generating a course on: **{topic}**", "Generating the course...",
                 topic, st.session_state.chunks, st.session_state.messages,
                 int(page_number) if use_specific_page else None):
        _set_mode(True)
        record_activity(xp_gained=10, messages_sent=1, couses_created=1)
        st.rerun()


def display_exercise_form():
    with st.form("exercise_form"):
        topic = st.text_input("Exercises topic", placeholder="E.g.: Variables in Python, Quadratic equations...")
        num_exercises = st.slider("Number of exercises", min_value=1, max_value=10, value=3)
        submitted = st.form_submit_button("Generate exercises", type="primary")
    if not submitted:
        return
    if not topic.strip():
        st.error("Please specify a topic for the exercises")
        return
    if _generate(exercise_chat, f"Generating {num_exercises} exercises on: **{topic}**", "Generating exercises...",
                 topic, st.session_state.chunks, st.session_state.messages, num_exercises):
        _set_mode(True)
        record_activity(xp_gained=5 + num_exercises, messages_sent=1, quizzes_created=1, questions_asked=num_exercises)
        st.rerun()


def qcm_message(questions: list, j: int):
    with st.form(key=f"qcm_form_{j}"):
        st.subheader("Answer the questions:")
        user_answers = {}
        for i, question in enumerate(questions):
            st.markdown(f"**Question {i + 1}**: {question['stem']}")
            options = question["options"]
            user_answers[i] = st.radio(
                f"Q{i + 1}",
                list(options),
                index=None,
                format_func=lambda x, options=options: f"{x}. {options[x]}",
                key=f"q_{j}_{i}",
                label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit my answers", type="primary")
    if not submitted:
        return
    if any(answer is None for answer in user_answers.values()):
        st.warning("Please answer every question before submitting.")
        return
    total = len(questions)
    correct_count = sum(user_answers[i] == q["correct_answer"] for i, q in enumerate(questions))
    score = {"correct": correct_count, "total": total, "answers": user_answers}
    if update_message(st.session_state.messages[j].message_id, score=score):
        st.session_state.messages[j].score = score
        record_activity(xp_gained=5 + 2 * correct_count, quizzes_completed=1,
                        questions_answered=total, correct_answers=correct_count)
        st.rerun()
    else:
        st.error("Error while submitting answers. Please try again.")


def display_qcm_results(score, questions):
    correct_count = score["correct"]
    total = score["total"]
    if correct_count == total:
        st.success(f"You scored {correct_count}/{total}. 🎉 Excellent work! You got everything right.")
    elif correct_count >= total / 2:
        st.warning(f"You scored {correct_count}/{total}. 👍 Good job! You understood the topic well.")
    else:
        st.error(f"You scored {correct_count}/{total}. ❌ It seems you need to review the topic.")
    with st.expander("See answer details"):
        # Keys come back from the JSON column as strings.
        for i, answer in score["answers"].items():
            if int(i) >= len(questions):
                continue
            question = questions[int(i)]
            icon = "✅" if answer == question["correct_answer"] else "❌"
            st.markdown(f"{icon} **{question['stem']}**")
            st.write(f"You answered '{answer}'. The correct answer was '{question['correct_answer']}'.")
            st.info(question["explanation"])
            st.divider()
