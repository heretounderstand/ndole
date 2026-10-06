import pytest
from utils.sql import SymPyQueryLanguage, process_llm_response


@pytest.fixture
def q():
    engine = SymPyQueryLanguage()
    engine.parse_query("let x")
    return engine


@pytest.mark.parametrize("query, expected", [
    ("solve(x**2 - 4, x)", "[-2, 2]"),
    ("expand((x+1)**2)", "x**2 + 2*x + 1"),
    ("factor(x**2 + 2*x + 1)", "(x + 1)**2"),
    ("diff(x**3, x)", "3*x**2"),
    ("integrate(x**2, x)", "x**3/3"),
    ("limit(sin(x)/x, x, 0)", "1"),
    ("subs(x**2, x, 2)", "4"),
    ("x^2", "x**2"),
    ("expand((x+1)**2) | factor($)", "(x + 1)**2"),
])
def test_operations(q, query, expected):
    assert str(q.parse_query(query)) == expected


def test_pipe_into_variable_and_reuse(q):
    q.parse_query("x**2 + 2*x + 1 | let r")
    assert str(q.parse_query("diff(r, x)")) == "2*x + 2"


def test_last_result_reference(q):
    q.parse_query("x**2")
    assert str(q.parse_query("diff($, x)")) == "2*x"


def test_latex(q):
    assert str(q.parse_query(r"latex \frac{x^2}{2} + 2x")) == "x**2/2 + 2*x"


@pytest.mark.parametrize("payload", [
    "__import__('os').getcwd()",
    "1 + __import__('os').getcwd().__len__()",
    "simplify(().__class__)",
    "x.func",
    "solve(open, x)",
    "lambda: 1",
    "9**9**9",
    "2**999999",
    "1234567890123 * x",
    "a" * 400,
])
def test_unsafe_input_is_rejected(q, payload):
    result = q.parse_query(payload)
    assert isinstance(result, str) and "rror" in result


def test_let_rejects_dunder_names(q):
    assert "Invalid" in q.parse_query("let __class__ = 1")


def test_process_llm_response_runs_blocks():
    text = "Intro\n```sympy-query\nlet x\n# roots\nsolve(x**2 - 5*x + 6, x)\n```\nEnd"
    out = process_llm_response(text)
    assert "```" not in out
    assert r"\left[ 2, \  3\right]" in out
    assert out.startswith("Intro") and out.endswith("End")


def test_process_llm_response_accepts_plain_sympy_fence():
    out = process_llm_response("```sympy\nlet x\ndiff(x**2, x)\n```")
    assert "2 x" in out


def test_process_llm_response_leaves_other_code_alone():
    text = "```python\nprint(1)\n```"
    assert process_llm_response(text) == text
