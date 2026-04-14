# ============================================
# NIMNA Language — FunctionDeclaration Handler
# File: src/ast/function_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    FunctionDeclaration,
    Parameter,
    ReturnStatement,
    Identifier,
)


# ============================================
# VALID RETURN TYPES
# ============================================

VALID_RETURN_TYPES = {
    # Whole Numbers
    "Tiny", "Short", "Whole", "Long", "Huge",
    # Decimal Numbers
    "Decimal", "Precise", "Exact",
    # Text
    "Text", "Letter", "Symbol",
    # Logical
    "Truth",
    # Raw
    "Bit",
    # Collections
    "Sequence", "Collection", "Mapping", "Unique", "Bundle",
    # Special
    "Maybe", "Outcome", "Task", "Flow",
    "Action", "Wild", "Nothing",
}

# Async functions must return Task or Nothing
ASYNC_VALID_RETURNS = {"Task", "Nothing", "Maybe", "Outcome", "Flow"}


# ============================================
# FUNCTION DECLARATION HANDLER CLASS
# ============================================

class FunctionHandler:
    """
    NIMNA FunctionDeclaration Handler

    Processes function declarations and validates:
    - Function name
    - Parameters (name + type)
    - Return type
    - Async rules
    - Body statements
    - Duplicate parameter names
    """

    def __init__(self, filename="<nimna>"):
        self.filename        = filename
        self.errors          = []
        self.warnings        = []
        self.declared_funcs  = set()


    def create(self, name, params, return_type, body,
               is_async=False, line=None, column=None):
        """
        Create a validated FunctionDeclaration node.

        Parameters:
            name        : str   — Function name
            params      : list  — List of (name, type) tuples
            return_type : str   — Return type or None
            body        : list  — List of statement nodes
            is_async    : bool  — Is async function
            line        : int   — Line number
            column      : int   — Column number

        Returns:
            FunctionDeclaration node or None if invalid
        """

        # Step 1: Validate function name
        name_valid, name_error = self._validate_name(name)
        if not name_valid:
            self.errors.append(f"[Line {line}] {name_error}")
            return None

        # Step 2: Check duplicate function name
        if name in self.declared_funcs:
            self.errors.append(
                f"[Line {line}] Function '{name}' is already declared."
            )
            return None

        # Step 3: Validate parameters
        param_nodes, param_errors = self._validate_params(params, line)
        if param_errors:
            self.errors.extend(param_errors)
            return None

        # Step 4: Validate return type
        if return_type:
            rt_valid, rt_error = self._validate_return_type(
                return_type, is_async, line
            )
            if not rt_valid:
                self.errors.append(rt_error)
                return None

        # Step 5: Async function warnings
        if is_async and not return_type:
            self.warnings.append(
                f"[Line {line}] Async function '{name}' has no return type. "
                f"Consider returning 'Task' or 'Nothing'."
            )

        # Step 6: Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] Function '{name}' has an empty body."
            )

        # Step 7: Register function name
        self.declared_funcs.add(name)

        # Step 8: Create and return node
        return FunctionDeclaration(
            name        = name,
            params      = param_nodes,
            return_type = return_type,
            body        = body,
            is_async    = is_async,
            line        = line,
            column      = column
        )


    def _validate_name(self, name):
        """
        Validate function name.
        """

        if not name:
            return False, "Function name cannot be empty."

        if not (name[0].isalpha() or name[0] == '_'):
            return False, (
                f"Function name '{name}' must start with "
                f"a letter or underscore."
            )

        if name.startswith('__'):
            return False, (
                f"Function name '{name}' cannot start with '__'. "
                f"Reserved for compiler use."
            )

        return True, ""


    def _validate_params(self, params, line):
        """
        Validate all parameters.
        Returns (param_nodes, errors)
        """

        param_nodes = []
        errors      = []
        seen_names  = set()

        for param_name, param_type in params:

            # Check duplicate parameter names
            if param_name in seen_names:
                errors.append(
                    f"[Line {line}] Duplicate parameter name "
                    f"'{param_name}' in function declaration."
                )
                continue

            # Validate parameter name
            if not param_name or not (
                param_name[0].isalpha() or param_name[0] == '_'
            ):
                errors.append(
                    f"[Line {line}] Invalid parameter name '{param_name}'."
                )
                continue

            # Validate parameter type
            if param_type not in VALID_RETURN_TYPES:
                errors.append(
                    f"[Line {line}] Unknown parameter type "
                    f"'{param_type}' for parameter '{param_name}'."
                )
                continue

            seen_names.add(param_name)
            param_nodes.append(
                Parameter(
                    name       = param_name,
                    param_type = param_type,
                    line       = line
                )
            )

        return param_nodes, errors


    def _validate_return_type(self, return_type, is_async, line):
        """
        Validate return type.
        Async functions must return Task-compatible types.
        """

        if return_type not in VALID_RETURN_TYPES:
            return False, (
                f"[Line {line}] Unknown return type '{return_type}'. "
                f"Valid types include: Whole, Text, Decimal, Task, etc."
            )

        if is_async and return_type not in ASYNC_VALID_RETURNS:
            return False, (
                f"[Line {line}] Async function cannot return '{return_type}'. "
                f"Async functions must return: "
                f"{', '.join(sorted(ASYNC_VALID_RETURNS))}."
            )

        return True, ""


    def get_signature(self, node):
        """
        Get human readable function signature.
        """

        params_str = ", ".join(
            f"{p.name}: {p.param_type}"
            for p in node.params
        )

        prefix      = "async " if node.is_async else ""
        return_str  = f" -> {node.return_type}" if node.return_type else ""

        return f"{prefix}fn {node.name}({params_str}){return_str}"


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []

    def reset(self):
        self.errors          = []
        self.warnings        = []
        self.declared_funcs  = set()
