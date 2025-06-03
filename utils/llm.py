import re
import streamlit as st
import google.generativeai as genai
from typing import Any, Dict, List, Optional, Tuple
from model import Chunk, ChatHistory, Message
from utils.embedding import best_matchs
from utils.chat import create_message

genai.configure(api_key=st.secrets["gemini"]["api_key"])
MODEL_NAME = "gemini-2.0-flash"
DEFAULT_CHUNK_COUNT = 10
INSTRUCTIONS = """
LLM Math Instruction Prompt
When you need to answer questions involving mathematical expressions, equations, or symbolic computations, please follow these instructions:

For any mathematical operation that requires symbolic manipulation, use the SymPy Query Language inside code blocks tagged with sympy-query.
Structure your solution by first explaining your approach in natural language, then performing the calculations using the query language, and finally interpreting the results.
Use the following syntax for the query language code blocks:
sympy# Your query language commands here
let x  # define symbols
let y
# perform operations
solve(x**2 - 4, x)

Common operations available in the query language:

let x - Define a symbol
let y = 5 - Assign a value to a symbol
let f = x**2 - Define an expression
solve(equation, variable) - Solve equations
expand(expression) - Expand expressions
factor(expression) - Factor expressions
simplify(expression) - Simplify expressions
diff(expression, variable) - Find derivatives
integrate(expression, variable) - Find integrals
limit(expression, variable, value) - Find limits
subs(expression, old, new) - Substitute values


For multi-step calculations, you can use the pipe operator | to chain operations:
sympy(x+1)**2 | expand($) | diff($, x)

Use $ to reference the result of the previous operation.
After each code block, explain the results in natural language to ensure understanding.
For particularly complex expressions, explain the approach step by step.

Examples:
Solving a quadratic equation:
sympylet x
solve(x**2 - 5*x + 6, x)
Finding a derivative:
sympylet x
diff(sin(x)**2, x)
Simplifying a complex expression:
sympylet x
let y
simplify((x**2 + 2*x*y + y**2)/(x + y))
Remember to always first establish what symbols you need with let statements before using them in calculations.
"""
PROMPTS = {
    "qa": """You are an intelligent assistant specialized in answering user questions.  
    Use the contextual information provided below to answer the user's question.  

    Priority order:
    1. Always prioritize the provided context when available and relevant
    2. If context is insufficient, you may supplement with your personal knowledge only if you are absolutely certain of its accuracy
    3. Clearly indicate the source of information (context vs personal knowledge)

    If you cannot find the answer in context AND are uncertain about your personal knowledge, clearly state so and suggest alternative leads.  
    Respond in a concise, clear, and precise manner. Answer in the same language as the user's question.  

    Context:  
    {context}  

    User question: {user_question}  
    """,  

    "course": """You are an expert teacher creating a course.  
    Use the information provided below to generate a structured and educational lesson.  

    Priority order:
    1. Always prioritize the provided reference content when available and relevant
    2. If reference content is insufficient, you may supplement with your expertise only if you are absolutely certain of its accuracy
    3. Clearly indicate the source of information (reference content vs personal expertise)

    The course should be organized with an introduction, main sections, and a conclusion.  
    Include practical examples to illustrate the presented concepts. Respond in the language of the course topic.  

    Reference content:  
    {context}  

    Course topic: {topic}  
    """,  

    "exercise": """You are a trainer creating multiple-choice questions (QCM) for practical exercises.

    Use the information provided below to generate relevant multiple-choice questions.

    Priority order:
    1. Always prioritize the provided reference content when available and relevant
    2. If reference content is insufficient, you may supplement with your expertise only if you are absolutely certain of its accuracy
    3. Clearly indicate the source of information (reference content vs personal expertise) in explanations

    The questions should test understanding and application of the concepts.

    For each question:
    1. Create a clear problem statement
    2. Provide exactly 4 answer choices labeled A, B, C, and D
    3. Indicate the correct answer
    4. Include a detailed explanation why the correct answer is right and why the others are wrong

    Format each question as follows:
    <question>
    <stem>Problem statement goes here</stem>
    <options>
    A. First option
    B. Second option
    C. Third option
    D. Fourth option
    </options>
    <answer>X</answer> (where X is the correct option letter)
    <explanation>
    Detailed explanation why the correct answer is right and why the other options are incorrect.
    </explanation>
    </question>

    Generate exactly {number_of_questions} questions (default: 3 if not specified).

    Reference content:
    {context}

    Exercise request: {exercise_request}

    Respond in the language of the exercise request. 
    """  
    }

def initialize_gemini_model():
    try:
        model = genai.GenerativeModel(
            MODEL_NAME, 
            system_instruction={"role": "system", "parts": [INSTRUCTIONS]}
        )
        return model
    except Exception as e:
        print(f"Error during model initialization: {e}")
        return None

def create_chat_session(messages: List[Message] = None) -> genai.ChatSession:
    model = initialize_gemini_model()
    if not model:
        raise Exception("Failed to initialize the model")
    history=[]
    if messages:
        for msg in messages:
            if not msg.is_deleted:
                if msg.is_assistant:
                    history.append({"role": "model", "parts": [msg.content]})
                else:
                    history.append({"role": "user", "parts": [msg.content]})
    chat = model.start_chat(history=history)
    return chat

def get_context_from_chunks(chunks: List[Chunk], max_chunks: int = DEFAULT_CHUNK_COUNT) -> str:
    context_chunks = chunks[:max_chunks]
    context_text = "\n\n---\n\n".join([f"Page {c.page}, Position {c.position}: {c.text}" for c in context_chunks])
    return context_text

def qa_chat(history: ChatHistory, user_message: str, chunks: List[Chunk], messages: List[Message], chat_session: genai.ChatSession = None) -> Tuple[genai.ChatSession, str, bool, List[Message]]:
    try:
        if not history:
            return None, "Chat history not found", False, []
        msgs = []
        user_msg_id = create_message(history.chat_id, user_message, is_assistant=False)
        msgs.append(
            Message(
                message_id=user_msg_id,
                chat_id=history.chat_id,
                content=user_message,
                is_assistant=False
            ))
        relevant_chunks = best_matchs(user_message, chunks)
        context = get_context_from_chunks(relevant_chunks)
        prompt = PROMPTS["qa"].format(context=context, user_question=user_message)
        if not chat_session:
            chat_session = create_chat_session(messages)
        response = chat_session.send_message(prompt)
        model_response = response.text
        assistant_msg_id = create_message(history.chat_id, model_response, is_assistant=True)
        msgs.append(
            Message(
                message_id=assistant_msg_id,
                chat_id=history.chat_id,
                content=model_response,
                is_assistant=True
            ))
        return chat_session, model_response, True, msgs
    except Exception as e:
        print(f"QA chat error : {e}")
        return None ,f"An error occurred : {str(e)}", False, []

def course_chat(history: ChatHistory, topic: str, chunks: List[Chunk], messages: List[Message], page_number: Optional[int] = None, chat_session: genai.ChatSession = None) -> Tuple[genai.ChatSession, str, bool, List[Message]]:
    try:
        if not history:
            return None, "Chat history not found", False, []
        msgs = []
        user_msg_id = create_message(history.chat_id, content=f"Generate a course on: {topic}", is_assistant=False)
        msgs.append(
            Message(
                message_id=user_msg_id,
                chat_id=history.chat_id,
                content=f"Generate a course on: {topic}",
                is_assistant=False
            ))
        if page_number is not None:
            chunks = [chunk for chunk in chunks if chunk.page == page_number]
        relevant_chunks = best_matchs(topic, chunks)
        context = get_context_from_chunks(relevant_chunks, max_chunks=10)
        prompt = PROMPTS["course"].format(context=context, topic=topic)
        if not chat_session:
            chat_session = create_chat_session(messages)
        response = chat_session.send_message(prompt)
        course_content = response.text
        assistant_msg_id = create_message(history.chat_id, course_content, is_assistant=True)
        msgs.append(
            Message(
                message_id=assistant_msg_id,
                chat_id=history.chat_id,
                content=course_content,
                is_assistant=True
            ))
        return chat_session, course_content, True, msgs
    except Exception as e:
        print(f"Course generation error : {e}")
        return None, f"An error occurred : {str(e)}", False, []

def exercise_chat(history: ChatHistory, exercise_request: str, chunks: List[Chunk], messages: List[Message], count: int = 3, chat_session: genai.ChatSession = None) -> Tuple[genai.ChatSession, str, bool, List[Message]]:
    try:
        if not history:
            return None, "Chat history not found", False, []
        msgs = []
        user_msg_id = create_message(history.chat_id, content=f"Generate {count} exercises on: {exercise_request}", is_assistant=False)
        msgs.append(
            Message(
                message_id=user_msg_id,
                chat_id=history.chat_id,
                content=f"Generate {count} exercises on: {exercise_request}",
                is_assistant=False
            ))
        relevant_chunks = best_matchs(exercise_request, chunks)
        context = get_context_from_chunks(relevant_chunks, max_chunks=count*2)
        prompt = PROMPTS["exercise"].format(
            context=context, 
            exercise_request=exercise_request,
            number_of_questions=count
        )
        if not chat_session:
            chat_session = create_chat_session(messages)
        response = chat_session.send_message(prompt)
        exercises_content = response.text
        assistant_msg_id = create_message(history.chat_id, exercises_content, is_assistant=True)
        msgs.append(
            Message(
                message_id=assistant_msg_id,
                chat_id=history.chat_id,
                content=exercises_content,
                is_assistant=True
            ))
        return chat_session, exercises_content, True, msgs
    except Exception as e:
        print(f"Exercise generation error: {e}")
        return None, f"An error occurred : {str(e)}", False, []
    
def extract_qcm_data(text: str) -> List[Dict[str, Any]]:
    questions = []
    question_regex = re.compile(r'<question>([\s\S]*?)</question>', re.DOTALL)
    stem_regex = re.compile(r'<stem>([\s\S]*?)</stem>', re.DOTALL)
    options_regex = re.compile(r'<options>([\s\S]*?)</options>', re.DOTALL)
    answer_regex = re.compile(r'<answer>([A-D])</answer>')
    explanation_regex = re.compile(r'<explanation>([\s\S]*?)</explanation>', re.DOTALL)
    question_matches = question_regex.finditer(text)
    for question_match in question_matches:
        question_content = question_match.group(1)
        stem_match = stem_regex.search(question_content)
        options_match = options_regex.search(question_content)
        answer_match = answer_regex.search(question_content)
        explanation_match = explanation_regex.search(question_content)
        if stem_match and options_match and answer_match and explanation_match:
            options_text = options_match.group(1)
            option_lines = options_text.strip().split('\n')
            options = {}
            for line in option_lines:
                trimmed_line = line.strip()
                if trimmed_line:
                    option_letter = trimmed_line[0]
                    option_text = trimmed_line[2:].strip()
                    options[option_letter] = option_text
            question = {
                'stem': stem_match.group(1).strip(),
                'options': options,
                'correct_answer': answer_match.group(1),
                'explanation': explanation_match.group(1).strip()
            }
            questions.append(question)
    return questions

def extract_context_from_qa(generated_text):
    pattern = r"User question:\s*(.*?)(?=\s*$)"
    match = re.search(pattern, generated_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return generated_text

def extract_context_from_course(generated_text):
    pattern = r"Course topic:\s*(.*?)(?=\s*$)"
    match = re.search(pattern, generated_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return generated_text

def extract_context_from_exercise(generated_text):
    pattern = r"Exercise request:\s*(.*?)(?=\s*$)"
    match = re.search(pattern, generated_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return generated_text

def extract_context(generated_text: str) -> str:
    if "You are an intelligent assistant specialized in answering user questions." in generated_text[:100]:
        return extract_context_from_qa(generated_text)
    elif "You are an expert teacher creating a course." in generated_text[:100]:
        return extract_context_from_course(generated_text)
    elif "You are a trainer creating multiple-choice questions (QCM) for practical exercises." in generated_text[:100]:
        return extract_context_from_exercise(generated_text)
    return generated_text
