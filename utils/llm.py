import re
import streamlit as st
import google.generativeai as genai
from typing import Any, Dict, List, Optional, Tuple
from model import Chunk, ChatHistory, Message
from utils.embedding import best_matchs
from utils.chat import create_message

genai.configure(api_key=st.secrets["gemini"]["api_key"])
MODEL_NAME = "gemini-2.5-flash-preview-04-17"
DEFAULT_CHUNK_COUNT = 5
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
    "qa": """You are an intelligent assistant that provides comprehensive and accurate answers to user questions.
    
    Instructions:
    - Use the provided context as supporting evidence when it's relevant and accurate
    - Draw primarily from your extensive knowledge base to provide complete, helpful answers
    - Integrate contextual information seamlessly into your response without explicitly mentioning sources
    - If the context contradicts your knowledge, prioritize the context only if it appears more reliable or recent
    - Always provide a substantive answer even when context is limited - use your training knowledge confidently
    - Never state that you don't have enough information unless you genuinely cannot answer the question at all
    - Respond naturally and conversationally without referencing "context" or "personal knowledge"
    
    Answer in the same language as the user's question with clarity and precision.
    
    Context: {context}
    
    Question: {user_question}  
    """,  
    "course": """You are an expert teacher with extensive pedagogical knowledge and subject matter expertise.

    Create a comprehensive, structured, and engaging course lesson on the given topic.
    
    Instructions:
    - Design a complete educational experience drawing from your deep expertise in teaching and the subject matter
    - Integrate any provided reference content seamlessly to enrich and support your lesson
    - Structure your course with: introduction, main learning sections, practical examples, and conclusion
    - Include concrete examples, exercises, or case studies to illustrate key concepts
    - Use clear, progressive learning sequences that build understanding step by step
    - Adapt your teaching style to make complex concepts accessible and engaging
    - Provide actionable knowledge that learners can immediately apply
    - Write in a natural, authoritative teaching voice without referencing sources
    
    Respond in the language appropriate for the course topic and target audience.
    
    Reference content: {context}
    
    Course topic: {topic}  
    """,  
    "exercise": """You are an experienced trainer and assessment specialist with expertise in creating high-quality multiple-choice questions that effectively test knowledge and skills.
    
    Create engaging and challenging multiple-choice questions that assess both understanding and practical application of concepts. Draw from your extensive expertise in the subject matter and assessment design.
    
    Instructions:
    - Develop questions that test critical thinking, not just memorization
    - Use any provided reference content to enhance and validate your questions
    - Create realistic scenarios and practical applications
    - Ensure distractors (wrong answers) are plausible but clearly incorrect
    - Write clear, unambiguous question stems
    - Provide comprehensive explanations that reinforce learning
    
    Format each question exactly as follows:
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
    Clear explanation of why the correct answer is right and why other options are incorrect, helping reinforce the learning objectives.
    </explanation>
    </question>
    
    Generate exactly {number_of_questions} questions (default: 3 if not specified).
    
    Reference content: {context}
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
    if "You are an intelligent assistant" in generated_text[:35]:
        return extract_context_from_qa(generated_text)
    elif "You are an expert teacher" in generated_text[:25]:
        return extract_context_from_course(generated_text)
    elif "You are an experienced trainer" in generated_text[:30]:
        return extract_context_from_exercise(generated_text)
    return generated_text
