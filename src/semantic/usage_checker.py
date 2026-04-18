# ============================================
# NIMNA Language — Variable Usage Checker
# File: src/semantic/usage_checker.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import SymbolTable, KIND_VARIABLE, KIND_FUNCTION


# ============================================
# BUILT-IN NAMES
# ============================================

# These are always available — no declaration needed
BUILTIN_NAMES = {
    "nimna",
    "true",
    "false",
    "nothing",
}

# Built-in functions available everywhere
BUILTIN_FUNCTIONS = {
    "nimna.io.print",
    "nimna.io.write",
    "nimna.io.input",
    "nimna.math.add",
    "nimna.math.divide",
    "nimna.math.sqrt",
    "nimna.math.abs",
    "nimna.math.pow",
    "nimna.math.min",
    "nimna.math.max",
}

# Type constructors — always valid
TYPE_CONSTRUCTORS = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Truth",
    "Collection", "Mapping", "Sequence",
    "Maybe", "Outcome", "Task", "Flow",
    "Action", "Wild", "Nothing",
}


# ============================================
# USAGE CHECKER CLASS
# ============================================

class UsageChecker:
    """
    NIMNA Variable Usage Checker

    Checks:
    1. Undeclared variable usage
    2. Variable used before assignment
    3. Unused variable warnings
    4. Unused function warnings
    5. Type constructor usage
    6. Built-in name protection
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table    = symbol_table
        self.filename = filename
        self.errors   = []
        self.warnings = []
        self.used_names = set()


    # ==========================================
    # MAIN CHECK METHODS
    # ==========================================

    def check_variable_use(self, name, line):
        """
        Check if a variable is declared before use.

        Parameters:
            name : str — Variable or identifier name
            line : int — Line number

        Returns:
            Symbol if found, None if error
        """

        # Built-in names are always OK
        if name in BUILTIN_NAMES:
            return None

        # Type constructors are always OK
        if name in TYPE_CONSTRUCTORS:
            return None

        # Look up in symbol table
        sym = self.table.lookup(name)

        if sym is None:
            # Check if it looks like a module path
            if "." in name:
                return None

            self.errors.append(
                f"[Line {line}] '{name}' is not declared. "
                f"Did you forget to declare it? "
                f"Use: let {name}: Type = value"
            )
            return None

        # Mark as used
        sym.mark_used()
        self.used_names.add(name)

        return sym


    def check_member_access(self, object_name, member_name, line):
        """
        Check object.member access.

        Examples:
            person.name
            animal.speak()
            nimna.io.print()
        """

        # nimna.* is always OK (standard library)
        if object_name == "nimna":
            return True

        # Look up object
        sym = self.table.lookup(object_name)

        if sym is None:
            self.errors.append(
                f"[Line {line}] '{object_name}' is not declared."
            )
            return False

        sym.mark_used()

        # Check if object has this field
        if hasattr(sym, 'fields') and sym.fields:
            if member_name not in sym.fields:
                self.errors.append(
                    f"[Line {line}] '{sym.name}' has no field "
                    f"or method '{member_name}'."
                )
                return False

        return True


    def check_function_call(self, func_name, arg_count, line):
        """
        Check if a function is declared and called correctly.

        Parameters:
            func_name : str — Function name
            arg_count : int — Number of arguments passed
            line      : int — Line number

        Returns:
            return_type str or None
        """

        # Built-in functions
        if func_name in BUILTIN_FUNCTIONS:
            return "Wild"

        # Check nimna.* paths
        if func_name.startswith("nimna."):
            return "Wild"

        # Type constructors
        base = func_name.split(".")[0]
        if base in TYPE_CONSTRUCTORS:
            return base

        # Look up function
        sym = self.table.lookup(func_name)

        if sym is None:
            self.errors.append(
                f"[Line {line}] Function '{func_name}' is not declared. "
                f"Did you forget to define it?"
            )
            return None

        if sym.kind != KIND_FUNCTION:
            self.errors.append(
                f"[Line {line}] '{func_name}' is not a function "
                f"(it is a {sym.kind})."
            )
            return None

        sym.mark_used()

        # Check argument count
        expected = len(sym.params) if sym.params else 0

        if arg_count != expected:
            self.errors.append(
                f"[Line {line}] '{func_name}' expects "
                f"{expected} argument(s) but got {arg_count}."
            )
            return sym.return_type

        return sym.return_type


    def check_assignment_target(self, name, line):
        """
        Check if a variable can be assigned to.

        Rules:
        - Must be declared
        - Must not be a constant
        """

        sym = self.table.lookup(name)

        if sym is None:
            self.errors.append(
                f"[Line {line}] Cannot assign to '{name}' "
                f"because it is not declared. "
                f"Declare it first: let {name}: Type = value"
            )
            return False

        if sym.is_constant:
            self.errors.append(
                f"[Line {line}] Cannot assign to constant '{name}'. "
                f"It was declared as constant at line {sym.line}."
            )
            return False

        sym.mark_assigned()
        sym.mark_used()
        return True


    def check_unassigned_use(self, name, line):
        """
        Warn if variable is used before being assigned a value.
        """
        sym = self.table.lookup(name)
        if sym and not sym.is_assigned:
            self.warnings.append(
                f"[Line {line}] Variable '{name}' may be used "
                f"before being assigned a value."
            )


    def check_unused_in_scope(self):
        """
        Check for unused variables in all scopes.
        Generates warnings for unused declarations.
        """
        for scope in self.table.scope_stack:
            for sym in scope.symbols.values():
                if (sym.kind in (KIND_VARIABLE,) and
                        not sym.is_used and
                        not sym.name.startswith("_")):
                    self.warnings.append(
                        f"Variable '{sym.name}' declared at "
                        f"line {sym.line} is never used. "
                        f"Prefix with '_' to suppress this warning."
                    )


    def check_builtin_override(self, name, line):
        """
        Error if user tries to declare a built-in name.
        """
        if name in BUILTIN_NAMES:
            self.errors.append(
                f"[Line {line}] Cannot use '{name}' as a variable name. "
                f"It is a built-in NIMNA name."
            )
            return False
        return True


    # ==========================================
    # ERROR AND WARNING GETTERS
    # ==========================================

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors     = []
        self.warnings   = []
        self.used_names = set()
