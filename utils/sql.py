import re
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from sympy.printing.latex import latex

MAX_QUERY_LENGTH = 300
MAX_DIGITS = 6

# `parse_expr` ends in `eval`, and queries come from chat input and from LLM output
# (which uploaded documents can steer), so input is restricted before parsing:
#  - characters: no quotes, backslashes, `#`, `;`, `@`, `!` or backticks;
#  - no dunder names and no attribute access (`obj.attr`), the usual sandbox escapes;
#  - bounded length and number sizes to avoid `9**9**9`-style CPU exhaustion.
_ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9_\s+\-*/^().,=\[\]{}<>|$]*$")
_ATTRIBUTE_ACCESS = re.compile(r"\.\s*[A-Za-z_]")
_BIG_NUMBER = re.compile(r"\d{%d,}" % (MAX_DIGITS + 1))
_BIG_EXPONENT = re.compile(r"(\*\*|\^)\s*\(?\s*\d{5,}")
_STACKED_POWERS = re.compile(r"(\*\*|\^)[\s()\d]*(\*\*|\^)")
_FORBIDDEN_NAMES = re.compile(r"\b(lambda|import|exec|eval|open|compile|globals|locals|getattr|setattr|delattr|vars|dir|input|breakpoint|help)\b")


class UnsafeExpressionError(ValueError):
    pass


def _check_safe(text: str) -> None:
    if len(text) > MAX_QUERY_LENGTH:
        raise UnsafeExpressionError(f"expression too long (max {MAX_QUERY_LENGTH} characters)")
    if not _ALLOWED_CHARS.match(text):
        raise UnsafeExpressionError("expression contains forbidden characters")
    if "__" in text or _ATTRIBUTE_ACCESS.search(text) or _FORBIDDEN_NAMES.search(text):
        raise UnsafeExpressionError("expression contains forbidden constructs")
    if _BIG_NUMBER.search(text):
        raise UnsafeExpressionError(f"numbers are limited to {MAX_DIGITS} digits")
    if _BIG_EXPONENT.search(text) or _STACKED_POWERS.search(text):
        raise UnsafeExpressionError("exponent too large or nested powers")


def _sympy_namespace() -> dict:
    namespace = {}
    exec("from sympy import *", namespace)
    # Evaluate without Python builtins: names like `__import__` or `open` are unavailable.
    namespace["__builtins__"] = {}
    return namespace


_GLOBALS = _sympy_namespace()
_TRANSFORMATIONS = standard_transformations + (convert_xor,)
_LATEX_TRANSFORMATIONS = standard_transformations + (convert_xor, implicit_multiplication_application)


class SymPyQueryLanguage:
    def __init__(self):
        self.operations = {
            "solve": sp.solve,
            "expand": sp.expand,
            "factor": sp.factor,
            "simplify": sp.simplify,
            "diff": sp.diff,
            "integrate": sp.integrate,
            "limit": sp.limit,
            "series": sp.series,
            "subs": lambda expr, old, new: expr.subs(old, new),
        }
        self.symbols = {}
        self.last_result = None

    def parse_query(self, query):
        query = query.strip()
        if query.lower() == "help":
            return self._get_help()
        if query.startswith("let "):
            return self._define_symbol(query[4:])
        if query.startswith("latex "):
            return self._handle_latex(query[6:])
        if "|" in query:
            return self._handle_chained_operations(query)
        if "$" in query:
            query = query.replace("$", f"({self.last_result})")
        operation_match = re.fullmatch(r"(\w+)\s*\((.*)\)", query)
        if operation_match and operation_match.group(1).lower() in self.operations:
            result = self._execute_operation(operation_match.group(1).lower(), operation_match.group(2))
            self.last_result = result
            return result
        try:
            result = self._parse_expression(query)
            self.last_result = result
            return result
        except Exception as e:
            return f"Error evaluating expression: {e}"

    def _handle_chained_operations(self, query):
        """Handle operations chained with pipe symbol (|)."""
        result = None
        for i, operation in enumerate(query.split("|")):
            operation = operation.strip()
            if i == 0:
                result = self.parse_query(operation)
            elif operation.startswith("let "):
                var_name = operation[4:].strip()
                if not var_name.isidentifier() or var_name.startswith("_"):
                    return f"Invalid symbol name: {var_name}"
                self.symbols[var_name] = result
                result = f"Symbol '{var_name}' set to {result}"
            else:
                if "$" in operation:
                    operation = operation.replace("$", f"({result})")
                else:
                    op_match = re.fullmatch(r"(\w+)\s*\((.*)\)", operation)
                    if op_match:
                        op_name, args = op_match.group(1), op_match.group(2).strip()
                        operation = f"{op_name}({result}, {args})" if args else f"{op_name}({result})"
                    else:
                        operation = f"{operation}({result})"
                result = self.parse_query(operation)
        self.last_result = result
        return result

    def _define_symbol(self, definition):
        try:
            parts = definition.split("=", 1)
            symbol_name = parts[0].strip()
            if not symbol_name.isidentifier() or symbol_name.startswith("_"):
                return f"Invalid symbol name: {symbol_name}"
            if len(parts) == 1:
                self.symbols[symbol_name] = sp.Symbol(symbol_name)
                return f"Symbol '{symbol_name}' created"
            value_expr = self._parse_expression(parts[1])
            self.symbols[symbol_name] = value_expr
            return f"Symbol '{symbol_name}' defined as {value_expr}"
        except Exception as e:
            return f"Error defining symbol: {e}"

    def _handle_latex(self, latex_expr):
        latex_expr = latex_expr.strip().strip("$")
        if len(latex_expr) > MAX_QUERY_LENGTH:
            return "Error parsing LaTeX: expression too long"
        try:
            # SymPy's own LaTeX parser builds expressions without eval (needs antlr4 runtime).
            from sympy.parsing.latex import parse_latex
            return parse_latex(latex_expr)
        except Exception:
            pass
        # Fallback: a small LaTeX-to-SymPy translation, then the guarded parser.
        expr = latex_expr
        replacements = [
            (r"\\left|\\right", ""), (r"\\cdot|\\times", "*"),
            (r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"((\1)/(\2))"),
            (r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)"),
            (r"\\(sin|cos|tan|ln|log|exp|pi)", r"\1"),
            (r"\{", "("), (r"\}", ")"),
        ]
        for pattern, repl in replacements:
            expr = re.sub(pattern, repl, expr)
        expr = expr.replace("ln(", "log(")
        try:
            _check_safe(expr)
            return parse_expr(expr, local_dict=dict(self.symbols), global_dict=dict(_GLOBALS),
                              transformations=_LATEX_TRANSFORMATIONS)
        except Exception as e:
            return f"Error parsing LaTeX: {e}"

    def _parse_expression(self, expr_str):
        expr_str = expr_str.strip()
        _check_safe(expr_str)
        return parse_expr(expr_str, local_dict=dict(self.symbols), global_dict=dict(_GLOBALS),
                          transformations=_TRANSFORMATIONS)

    def _execute_operation(self, op_name, args_str):
        if op_name not in self.operations:
            return f"Unknown operation: {op_name}"
        try:
            parsed_args = [self._parse_expression(arg) for arg in self._split_args(args_str)]
            return self.operations[op_name](*parsed_args)
        except Exception as e:
            return f"Error executing {op_name}: {e}"

    def _split_args(self, args_str):
        args = []
        current_arg = ""
        depth = 0
        for char in args_str:
            if char == ',' and depth == 0:
                args.append(current_arg.strip())
                current_arg = ""
                continue
            current_arg += char
            if char in "([":
                depth += 1
            elif char in ")]":
                depth -= 1
        if current_arg.strip():
            args.append(current_arg.strip())
        return args

    def _get_help(self):
        return """
SymPy Query Language Help:

1. Define symbols/variables:
   - let x          (define a symbol)
   - let y = 5      (define a variable with value)
   - let f = x**2   (define an expression)

2. Operations:
   - solve(x**2 - 4, x)       (solve equation for x)
   - expand((x+1)**2)         (expand expression)
   - factor(x**2 + 2*x + 1)   (factor expression)
   - simplify(sin(x)**2 + cos(x)**2)
   - diff(x**2, x)            (differentiate)
   - integrate(x**2, x)       (integrate)
   - limit(sin(x)/x, x, 0)    (find limit)
   - series(exp(x), x, 0, 4)  (Taylor series)
   - subs(x**2, x, 2)         (substitute x=2)

3. LaTeX input:
   - latex x^2 + 2x + 1       (parse LaTeX expression)

4. Direct expressions:
   - x**2 + 2*x + 1           (evaluate expression)

5. Chaining operations:
   - expand((x+1)**2) | factor($)    (chain operations with pipe)
   - x**2 + 2*x + 1 | factor($)      (use result in next operation)
   - x**2 + 2*x + 1 | let result     (store result in variable)

6. Using last result:
   - $                               (reference last result)
   - factor($)                       (use last result as input)
   - diff($, x)                      (use last result as first argument)
"""


def _format(result) -> str:
    if isinstance(result, (sp.Basic, list, tuple, set, dict)):
        return f"${latex(result)}$"
    return str(result)


# Accept ```sympy-query (documented) and ```sympy (what models often write).
SYMPY_BLOCK = re.compile(r"```sympy(?:-query)?[ \t]*\n([\s\S]*?)```")


def process_llm_response(text: str) -> str:
    """Run every ```sympy-query block in `text` and replace it with its results."""
    sql = SymPyQueryLanguage()

    def replace_with_solution(match):
        lines = []
        final_result = None
        for query in match.group(1).strip().split('\n'):
            query = query.strip()
            if not query or query.startswith('#'):
                if query:
                    lines.append(f"*{query.lstrip('# ')}*")
                continue
            try:
                result = sql.parse_query(query)
            except Exception as e:
                result = f"Error: {e}"
            final_result = result
            lines.append(f"`{query}` ➔ {_format(result)}")
        if final_result is not None:
            lines.append(f"\n**Result:** {_format(final_result)}")
        return "\n\n".join(lines)

    return SYMPY_BLOCK.sub(replace_with_solution, text)
