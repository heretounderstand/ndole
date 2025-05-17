import re
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from sympy.printing.latex import latex
from sympy.parsing.latex import parse_latex

class SymPyQueryLanguage:
    """
    A custom query language for SymPy that allows users to perform
    symbolic math operations with an easier syntax.
    """
    
    def __init__(self):
        # Define operation mappings
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
        
        # Initialize symbols dictionary
        self.symbols = {}
        
        # Store the result of the last operation
        self.last_result = None
    
    def parse_query(self, query):
        """Parse a query string and execute the corresponding SymPy operations."""
        query = query.strip()
        
        # Help command
        if query.lower() == "help":
            return self._get_help()
            
        # Define variables or symbols
        if query.startswith("let "):
            return self._define_symbol(query[4:])
            
        # LaTeX input
        if query.startswith("latex "):
            return self._handle_latex(query[6:])
            
        # Chain operations using pipe symbol
        if "|" in query:
            return self._handle_chained_operations(query)
        
        # Use last result with $
        if "$" in query:
            query = query.replace("$", str(self.last_result))
            
        # General operations
        operation_match = re.match(r"(\w+)\s*\((.*)\)", query)
        if operation_match:
            op_name = operation_match.group(1).lower()
            args = operation_match.group(2)
            result = self._execute_operation(op_name, args)
            self.last_result = result
            return result
            
        # If it's just an expression, evaluate it
        try:
            result = self._parse_expression(query)
            self.last_result = result
            return result
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
            
    def _handle_chained_operations(self, query):
        """Handle operations chained with pipe symbol (|)."""
        operations = query.split("|")
        result = None
        
        for i, operation in enumerate(operations):
            operation = operation.strip()
            if i == 0:
                # First operation
                result = self.parse_query(operation)
            else:
                # Subsequent operations, use previous result
                if operation.startswith("let "):
                    # Handle setting a variable with the result
                    var_name = operation[4:].strip()
                    self.symbols[var_name] = result
                    result = f"Symbol '{var_name}' set to {result}"
                else:
                    # Replace $ with the previous result if not already in operation
                    if "$" not in operation:
                        # Check if operation already has parentheses
                        op_match = re.match(r"(\w+)\s*\((.*)\)", operation)
                        if op_match:
                            op_name = op_match.group(1)
                            # Insert the result as the first argument if no arguments
                            args = op_match.group(2).strip()
                            if not args:
                                operation = f"{op_name}({result})"
                            else:
                                # Prepend result to arguments
                                operation = f"{op_name}({result}, {args})"
                        else:
                            # It's just a function name without arguments
                            operation = f"{operation}({result})"
                    else:
                        # $ is already in the operation, just replace it
                        operation = operation.replace("$", str(result))
                    
                    result = self.parse_query(operation)
        
        self.last_result = result
        return result
    
    def _define_symbol(self, definition):
        """Define a new symbol or variable."""
        try:
            parts = definition.split("=", 1)
            if len(parts) == 1:  # Just declaring a symbol
                symbol_name = parts[0].strip()
                self.symbols[symbol_name] = sp.Symbol(symbol_name)
                return f"Symbol '{symbol_name}' created"
            else:  # Defining a value
                symbol_name = parts[0].strip()
                value_expr = self._parse_expression(parts[1])
                self.symbols[symbol_name] = value_expr
                return f"Symbol '{symbol_name}' defined as {value_expr}"
        except Exception as e:
            return f"Error defining symbol: {str(e)}"
    
    def _handle_latex(self, latex_expr):
        """Handle LaTeX input and convert to SymPy expression."""
        try:
            expr = parse_latex(latex_expr)
            return expr
        except Exception as e:
            return f"Error parsing LaTeX: {str(e)}"
    
    def _parse_expression(self, expr_str):
        """Parse a string expression into a SymPy expression."""
        # Replace known symbols with their values
        for name, value in self.symbols.items():
            if isinstance(value, sp.Basic):
                # Already a SymPy expression, no need to do anything
                pass
            else:
                # Convert value to string for replacement
                expr_str = expr_str.replace(name, str(value))
        
        # Parse the expression
        return parse_expr(expr_str, local_dict=self.symbols)
    
    def _execute_operation(self, op_name, args_str):
        """Execute a SymPy operation with the given arguments."""
        if op_name not in self.operations:
            return f"Unknown operation: {op_name}"
        
        try:
            # Split arguments by comma, but respect parentheses
            args = self._split_args(args_str)
            parsed_args = [self._parse_expression(arg) for arg in args]
            
            # Call the operation
            result = self.operations[op_name](*parsed_args)
            return result
        except Exception as e:
            return f"Error executing {op_name}: {str(e)}"
    
    def _split_args(self, args_str):
        """Split arguments respecting parentheses, brackets, etc."""
        args = []
        current_arg = ""
        paren_level = 0
        bracket_level = 0
        
        for char in args_str:
            if char == ',' and paren_level == 0 and bracket_level == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
                if char == '(':
                    paren_level += 1
                elif char == ')':
                    paren_level -= 1
                elif char == '[':
                    bracket_level += 1
                elif char == ']':
                    bracket_level -= 1
        
        if current_arg:
            args.append(current_arg.strip())
        
        return args
    
    def _get_help(self):
        """Return help information about the query language."""
        help_text = """
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
        return help_text


def process_llm_response(text):
    """
    Process an LLM's response to identify and execute SymPy query language commands,
    replacing them with their LaTeX-formatted solutions.
    
    Args:
        text (str): The text response from an LLM
        
    Returns:
        str: The processed text with query language commands replaced by LaTeX solutions
    """
    # Initialize the query language
    sql = SymPyQueryLanguage()
    
    # Define pattern to detect query language commands
    # Looks for ```sympy-query ... ``` blocks
    pattern = r"```sympy-query\s*([\s\S]*?)\s*```"
    
    def replace_with_solution(match):
        # Extract the query commands
        query_block = match.group(1).strip()
        queries = query_block.split('\n')
        
        results = []
        final_result = None
        
        # Execute each query
        for query in queries:
            query = query.strip()
            if not query or query.startswith('#'):
                # Skip empty lines and comments
                results.append(query)
                continue
                
            try:
                # Execute the query
                result = sql.parse_query(query)
                final_result = result
                
                # Format result for display
                if isinstance(result, (sp.Basic, list, tuple, set)):
                    latex_result = f"${latex(result)}$"
                    results.append(f"{query} ➔ {latex_result}")
                else:
                    results.append(f"{query} ➔ {result}")
            except Exception as e:
                results.append(f"{query} ➔ Error: {str(e)}")
        
        # Generate LaTeX result for the final output
        if final_result is not None:
            if isinstance(final_result, (sp.Basic, list, tuple, set)):
                final_latex = f"${latex(final_result)}$"
                results.append(f"\nResult: {final_latex}")
            else:
                results.append(f"\nResult: {final_result}")
        
        # Format the results
        result_text = '\n'.join(results)
        return f"```\n{result_text}\n```"
    
    # Replace all query language blocks with their solutions
    processed_text = re.sub(pattern, replace_with_solution, text)
    return processed_text
