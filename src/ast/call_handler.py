# ============================================
# NIMNA Language — FunctionCall Handler
# File: src/ast/call_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    CallExpression,
    MemberAccessExpression,
    TypeConstructorExpression,
    Identifier,
    TextLiteral,
    IntegerLiteral,
    DecimalLiteral,
    TruthLiteral,
)


# ============================================
# BUILT-IN FUNCTIONS
# ============================================

BUILTIN_FUNCTIONS = {
    "nimna.io.print"  : {"min_args": 1, "max_args": None},
    "nimna.io.write"  : {"min_args": 1, "max_args": None},
    "nimna.io.input"  : {"min_args": 1, "max_args": 1},
    "nimna.math.add"  : {"min_args": 2, "max_args": 2},
    "nimna.math.divide": {"min_args": 2, "max_args": 2},
    "nimna.math.sqrt" : {"min_args": 1, "max_args": 1},
    "nimna.math.abs"  : {"min_args": 1, "max_args": 1},
}

# Type constructors — for type casting
TYPE_CONSTRUCTORS = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Truth",
}


# ============================================
# CALL HANDLER CLASS
# ============================================

class CallHandler:
    """
    NIMNA FunctionCall Handler

    Handles all function call types:
    - Simple calls      : greet()
    - Calls with args   : add(10, 20)
    - Method calls      : nimna.io.print("Hello")
    - Type constructors : Whole("25")
    - Nested calls      : print(Text(age))

    Validates:
    - Function name
    - Argument count
    - Argument types (where known)
    - Type constructor usage
    """

    def __init__(self, filename="<nimna>"):
        self.filename       = filename
        self.errors         = []
        self.warnings       = []
        self.known_functions = {}


    def register_function(self, name, min_args=0, max_args=None):
        """
        Register a user-defined function for validation.
        """
        self.known_functions[name] = {
            "min_args": min_args,
            "max_args": max_args
        }


    def create_call(self, function_path, arguments,
                    line=None, column=None):
        """
        Create a validated CallExpression node.

        Parameters:
            function_path : str or list — Function name or path
                            e.g. "greet" or ["nimna", "io", "print"]
            arguments     : list — List of argument nodes
            line          : int  — Line number
            column        : int  — Column number

        Returns:
            CallExpression node or None if invalid
        """

        # Step 1: Resolve function name
        if isinstance(function_path, list):
            func_name = ".".join(function_path)
            func_node = self._build_member_access(function_path)
        else:
            func_name = function_path
            func_node = Identifier(function_path, line=line)

        # Step 2: Validate function name
        name_valid, name_error = self._validate_function_name(
            func_name, line
        )
        if not name_valid:
            self.errors.append(name_error)
            return None

        # Step 3: Validate arguments
        arg_valid, arg_error = self._validate_arguments(
            func_name, arguments, line
        )
        if not arg_valid:
            self.errors.append(arg_error)
            return None

        # Step 4: Create and return node
        return CallExpression(
            function  = func_node,
            arguments = arguments or [],
            line      = line,
            column    = column
        )


    def create_type_constructor(self, type_name, argument,
                                line=None, column=None):
        """
        Create a TypeConstructorExpression node.

        Example:
            Whole("25")
            Decimal(age)
            Text(100)
        """

        # Validate type name
        if type_name not in TYPE_CONSTRUCTORS:
            self.errors.append(
                f"[Line {line}] '{type_name}' is not a valid "
                f"type constructor."
            )
            return None

        # Must have exactly one argument
        if argument is None:
            self.errors.append(
                f"[Line {line}] Type constructor '{type_name}' "
                f"requires exactly one argument."
            )
            return None

        return TypeConstructorExpression(
            type_name = type_name,
            argument  = argument,
            line      = line,
            column    = column
        )


    def create_method_call(self, object_path, method_name,
                           arguments, line=None, column=None):
        """
        Create a method call on an object.

        Example:
            nimna.io.print("Hello")
            person.greet()
        """

        # Build full path
        if isinstance(object_path, list):
            full_path = object_path + [method_name]
        else:
            full_path = [object_path, method_name]

        return self.create_call(full_path, arguments, line, column)


    def _build_member_access(self, path):
        """
        Build a MemberAccessExpression from a path list.

        Example:
            ["nimna", "io", "print"]
            →
            MemberAccess(
                MemberAccess(Identifier("nimna"), "io"),
                "print"
            )
        """

        if not path:
            return None

        node = Identifier(path[0])
        for part in path[1:]:
            node = MemberAccessExpression(
                object_expr = node,
                member      = part
            )
        return node


    def _validate_function_name(self, func_name, line):
        """
        Validate function name or path.
        """

        if not func_name:
            return False, (
                f"[Line {line}] Function name cannot be empty."
            )

        parts = func_name.split(".")
        for part in parts:
            if not part:
                return False, (
                    f"[Line {line}] Invalid function path '{func_name}'."
                )
            if not (part[0].isalpha() or part[0] == '_'):
                return False, (
                    f"[Line {line}] Invalid function name part "
                    f"'{part}' in '{func_name}'."
                )

        return True, ""


    def _validate_arguments(self, func_name, arguments, line):
        """
        Validate argument count for known functions.
        """

        arguments = arguments or []
        arg_count = len(arguments)

        # Check built-in functions
        if func_name in BUILTIN_FUNCTIONS:
            info    = BUILTIN_FUNCTIONS[func_name]
            min_arg = info["min_args"]
            max_arg = info["max_args"]

            if arg_count < min_arg:
                return False, (
                    f"[Line {line}] '{func_name}' requires at least "
                    f"{min_arg} argument(s). Got {arg_count}."
                )

            if max_arg is not None and arg_count > max_arg:
                return False, (
                    f"[Line {line}] '{func_name}' accepts at most "
                    f"{max_arg} argument(s). Got {arg_count}."
                )

        # Check user-defined functions
        if func_name in self.known_functions:
            info    = self.known_functions[func_name]
            min_arg = info["min_args"]
            max_arg = info["max_args"]

            if arg_count < min_arg:
                return False, (
                    f"[Line {line}] '{func_name}' requires at least "
                    f"{min_arg} argument(s). Got {arg_count}."
                )

            if max_arg is not None and arg_count > max_arg:
                return False, (
                    f"[Line {line}] '{func_name}' accepts at most "
                    f"{max_arg} argument(s). Got {arg_count}."
                )

        return True, ""


    def get_call_signature(self, node):
        """
        Get human readable call signature.
        """

        if isinstance(node, CallExpression):
            if isinstance(node.function, MemberAccessExpression):
                func_name = self._resolve_member_name(node.function)
            elif isinstance(node.function, Identifier):
                func_name = node.function.name
            else:
                func_name = str(node.function)

            args_str = ", ".join(
                self._describe_arg(a) for a in node.arguments
            )
            return f"{func_name}({args_str})"

        elif isinstance(node, TypeConstructorExpression):
            arg_str = self._describe_arg(node.argument)
            return f"{node.type_name}({arg_str})"

        return str(node)


    def _resolve_member_name(self, node):
        """Resolve member access chain to string."""

        if isinstance(node, Identifier):
            return node.name
        elif isinstance(node, MemberAccessExpression):
            obj  = self._resolve_member_name(node.object_expr)
            return f"{obj}.{node.member}"
        return str(node)


    def _describe_arg(self, arg):
        """Describe an argument node briefly."""

        if isinstance(arg, IntegerLiteral):
            return str(arg.value)
        elif isinstance(arg, DecimalLiteral):
            return str(arg.value)
        elif isinstance(arg, TextLiteral):
            return f'"{arg.value}"'
        elif isinstance(arg, TruthLiteral):
            return str(arg.value).lower()
        elif isinstance(arg, Identifier):
            return arg.name
        elif isinstance(arg, TypeConstructorExpression):
            return f"{arg.type_name}(...)"
        elif isinstance(arg, CallExpression):
            return "call(...)"
        return "expr"


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []
