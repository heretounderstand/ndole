from model import Access, Chunk
from utils.doc import group_blocks
from utils.embedding import rank_chunks
from utils.llm import extract_context, extract_qcm_data
from utils.user import toggle_access

QCM = """Here you go:
<question>
<stem>2 + 2 = ?</stem>
<options>
A. 3
B) 4
C: 5
D. 22
</options>
<answer> B </answer>
<explanation>Basic arithmetic.</explanation>
</question>
<question><stem>Broken</stem><options>A. x</options><answer>C</answer><explanation>no C option</explanation></question>
"""


def test_extract_qcm_data():
    questions = extract_qcm_data(QCM)
    assert len(questions) == 1
    q = questions[0]
    assert q["options"] == {"A": "3", "B": "4", "C": "5", "D": "22"}
    assert q["correct_answer"] == "B" and q["explanation"] == "Basic arithmetic."


def test_extract_context_for_legacy_prompts():
    assert extract_context("You are an intelligent assistant ...\n Question: What is RAG?\n") == "What is RAG?"
    assert extract_context("plain message") == "plain message"


def test_group_blocks():
    assert group_blocks(["Title", "  ", "a" * 10, "b" * 10], target_chars=15) == ["Title\n" + "a" * 10, "b" * 10]
    assert group_blocks([]) == []


def test_rank_chunks_uses_cosine_similarity():
    chunks = [Chunk(text=t, embedding=e, page=0, position=i)
              for i, (t, e) in enumerate([("far", [0.0, 1.0]), ("close", [10.0, 0.5]), ("zero", [0.0, 0.0])])]
    assert [c.text for c in rank_chunks([1.0, 0.0], chunks, top_k=2)] == ["close", "zero"]
    assert rank_chunks([1.0, 0.0], []) == []


def test_toggle_access():
    a = Access(access_id="u1")
    likes = toggle_access([], a, "likes", [])
    assert [e["access_id"] for e in likes] == ["u1"]
    assert toggle_access(likes, a, "likes", []) == []  # second click un-likes
    dislikes = [a.model_dump()]
    toggle_access([], a, "likes", dislikes)
    assert dislikes == []  # liking removes the dislike
    assert len(toggle_access(likes, a, "accesses")) == 2  # views always append
