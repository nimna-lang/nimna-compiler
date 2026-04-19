# ============================================
# NIMNA Language — Scope Analyzer
# File: src/semantic/scope_analyzer.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import (
    SymbolTable, Symbol,
    KIND_VARIABLE, KIND_CONSTANT,
    KIND_FUNCTION, KIND_PARAM,
    KIND_OBJECT, KIND_RECORD, KIND_FIELD,
)


# ============================================
# SCOPE TYPES
# ============================================

SCOPE_GLOBAL   = "global"
SCOPE_FUNCTION = "function"
SCOPE_BLOCK    = "block"
SCOPE_LOOP     = "loop"
SCOPE_OBJECT   = "object"
SCOPE_RECORD   = "record"


# ============================================
# SCOPE ANALYZER CLASS
# ============================================

class ScopeAnalyzer:
    """
    NIMNA Scope Analyzer

    Enforces block scope rules:
    1. Variables accessible only in their scope
    2. Inner scopes can access outer scopes
    3. Outer scopes cannot access inner scopes
    4. Loop variables only in loop body
    5. Function params only in function body
    6. Object fields accessible via 'this'
    7. break/skip only inside loops
    8. give (return) only inside functions
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table          = symbol_table
        self.filename       = filename
        self.errors         = []
        self.warnings       = []
        self.loop_depth     = 0
        self.function_depth = 0
        self.current_fn     = None
        self.scope_history  = []


    # ==========================================
    # SCOPE ENTRY AND EXIT
    # ==========================================

    def enter_function(self, func_name, line):
        """Enter a function scope."""
        self.function_depth += 1
        self.current_fn      = func_name
        self.scope_history.append(
            (SCOPE_FUNCTION, func_name, line)
        )
        self.table.enter_scope(SCOPE_FUNCTION, func_name)

    def exit_function(self):
        """Exit a function scope."""
        self.function_depth = max(0, self.function_depth - 1)
        if self.scope_history:
            self.scope_history.pop()
        if self.function_depth == 0:
            self.current_fn = None
        elif self.scope_history:
            for entry in reversed(self.scope_history):
                if entry[0] == SCOPE_FUNCTION:
                    self.current_fn = entry[1]
                    break
        self.table.exit_scope()

    def enter_block(self, line):
        """Enter a generic block scope (if, else, etc.)."""
        self.scope_history.append((SCOPE_BLOCK, None, line))
        self.table.enter_scope(SCOPE_BLOCK)

    def exit_block(self):
        """Exit a block scope."""
        if self.scope_history:
            self.scope_history.pop()
        self.table.exit_scope()

    def enter_loop(self, loop_type, line):
        """Enter a loop scope."""
        self.loop_depth += 1
        self.scope_history.append((SCOPE_LOOP, loop_type, line))
        self.table.enter_scope(SCOPE_LOOP, loop_type)

    def exit_loop(self):
        """Exit a loop scope."""
        self.loop_depth = max(0, self.loop_depth - 1)
        if self.scope_history:
            self.scope_history.pop()
        self.table.exit_scope()

    def enter_object(self, obj_name, line):
        """Enter an object scope."""
        self.scope_history.append((SCOPE_OBJECT, obj_name, line))
        self.table.enter_scope(SCOPE_OBJECT, obj_name)

    def exit_object(self):
        """Exit an object scope."""
        if self.scope_history:
            self.scope_history.pop()
        self.table.exit_scope()


    # ==========================================
    # SCOPE CHECKS
    # ==========================================

    def check_variable_accessible(self, name, line):
        """
        Check if a variable is accessible in current scope.

        Returns:
            Symbol if accessible, None if not
        """

        sym = self.table.lookup(name)

        if sym is None:
            return None

        sym.mark_used()
        return sym


    def check_break_valid(self, line):
        """
        Check if 'break' is used inside a loop.
        """

        if self.loop_depth == 0:
            self.errors.append(
                f"[Line {line}] 'break' used outside of a loop. "
                f"'break' can only be used inside a loop body."
            )
            return False
        return True


    def check_skip_valid(self, line):
        """
        Check if 'skip' is used inside a loop.
        """

        if self.loop_depth == 0:
            self.errors.append(
                f"[Line {line}] 'skip' used outside of a loop. "
                f"'skip' can only be used inside a loop body."
            )
            return False
        return True


    def check_return_valid(self, line):
        """
        Check if 'give' is used inside a function.
        """

        if self.function_depth == 0:
            self.errors.append(
                f"[Line {line}] 'give' used outside of a function. "
                f"'give' can only be used inside a function body."
            )
            return False
        return True


    def check_await_valid(self, line):
        """
        Check if 'await' is used inside an async function.
        """

        if self.function_depth == 0:
            self.errors.append(
                f"[Line {line}] 'await' used outside of a function."
            )
            return False
        return True


    def check_shadowing(self, name, line):
        """
        Warn if a variable shadows an outer scope variable.
        """

        if len(self.table.scope_stack) <= 1:
            return

        current_scope = self.table.current_scope()

        # Check outer scopes
        for scope in list(reversed(self.table.scope_stack))[1:]:
            if scope.has(name):
                outer_sym = scope.lookup(name)
                self.warnings.append(
                    f"[Line {line}] '{name}' shadows '{name}' "
                    f"from outer scope (line {outer_sym.line}). "
                    f"Consider renaming to avoid confusion."
                )
                break


    def check_declare_in_scope(self, name, kind, nimna_type,
                                line, is_constant=False):
        """
        Declare a symbol in current scope with scope validation.

        Returns:
            Symbol if declared, None if error
        """

        # Check shadowing first (warning only)
        self.check_shadowing(name, line)

        # Declare in symbol table
        sym = self.table.declare(
            name        = name,
            kind        = kind,
            nimna_type  = nimna_type,
            line        = line,
            is_constant = is_constant
        )

        return sym


    # ==========================================
    # SCOPE INFORMATION
    # ==========================================

    def in_function(self):
        """Check if currently inside a function."""
        return self.function_depth > 0

    def in_loop(self):
        """Check if currently inside a loop."""
        return self.loop_depth > 0

    def current_scope_type(self):
        """Get current scope type."""
        if self.scope_history:
            return self.scope_history[-1][0]
        return SCOPE_GLOBAL

    def scope_depth(self):
        """Get current scope depth."""
        return self.table.scope_depth()

    def get_scope_chain(self):
        """
        Get human readable scope chain.
        Example: global → function(main) → block → loop(for)
        """

        chain = [SCOPE_GLOBAL]
        for scope_type, name, _ in self.scope_history:
            label = f"{scope_type}({name})" if name else scope_type
            chain.append(label)
        return " → ".join(chain)


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
        self.errors   = []
        self.warnings = []
