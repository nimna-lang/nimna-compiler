# ============================================
# NIMNA Language — Loop Handler
# File: src/ast/loop_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    ForLoop,
    WhileLoop,
    DoUntilLoop,
    ForeachLoop,
    ParallelLoop,
    RangeExpression,
    BinaryExpression,
    Identifier,
    IntegerLiteral,
    TruthLiteral,
    BreakStatement,
    SkipStatement,
)


# ============================================
# LOOP HANDLER CLASS
# ============================================

class LoopHandler:
    """
    NIMNA Loop Handler

    Handles all 5 loop types:
    1. ForLoop      — for i from 0..5 { }
    2. WhileLoop    — while condition { }
    3. DoUntilLoop  — do { } until condition
    4. ForeachLoop  — foreach item from list { }
    5. ParallelLoop — parallel for i from 0..100 { }

    Validates:
    - Loop variable names
    - Range expressions
    - Conditions
    - Loop bodies
    - Break and skip usage
    """

    def __init__(self, filename="<nimna>"):
        self.filename     = filename
        self.errors       = []
        self.warnings     = []
        self.loop_depth   = 0


    # ============================================
    # FOR LOOP
    # ============================================

    def create_for(self, variable, range_expr, body,
                   line=None, column=None):
        """
        Create a validated ForLoop node.

        Example:
            for i from 0..5 {
                nimna.io.print("{i}")
            }
        """

        # Validate loop variable
        var_valid, var_error = self._validate_variable(variable, line)
        if not var_valid:
            self.errors.append(var_error)
            return None

        # Validate range expression
        range_valid, range_error = self._validate_range(range_expr, line)
        if not range_valid:
            self.errors.append(range_error)
            return None

        # Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] 'for' loop has an empty body."
            )

        self.loop_depth += 1
        node = ForLoop(
            variable   = variable,
            range_expr = range_expr,
            body       = body,
            line       = line,
            column     = column
        )
        self.loop_depth -= 1

        return node


    # ============================================
    # WHILE LOOP
    # ============================================

    def create_while(self, condition, body,
                     line=None, column=None):
        """
        Create a validated WhileLoop node.

        Example:
            let count: Whole = 0
            while count < 10 {
                count += 1
            }
        """

        # Validate condition
        cond_valid, cond_error = self._validate_condition(condition, line)
        if not cond_valid:
            self.errors.append(cond_error)
            return None

        # Constant true condition — infinite loop warning
        if isinstance(condition, TruthLiteral) and condition.value is True:
            self.warnings.append(
                f"[Line {line}] 'while true' creates an infinite loop. "
                f"Make sure there is a 'break' inside the loop body."
            )

        # Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] 'while' loop has an empty body."
            )

        self.loop_depth += 1
        node = WhileLoop(
            condition = condition,
            body      = body,
            line      = line,
            column    = column
        )
        self.loop_depth -= 1

        return node


    # ============================================
    # DO-UNTIL LOOP
    # ============================================

    def create_do_until(self, body, condition,
                        line=None, column=None):
        """
        Create a validated DoUntilLoop node.

        Example:
            let x: Whole = 0
            do {
                x += 1
            } until x == 5
        """

        # Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] 'do' loop has an empty body."
            )

        # Validate condition
        cond_valid, cond_error = self._validate_condition(condition, line)
        if not cond_valid:
            self.errors.append(cond_error)
            return None

        # Constant true condition — runs only once
        if isinstance(condition, TruthLiteral) and condition.value is True:
            self.warnings.append(
                f"[Line {line}] 'until true' — loop will only execute once."
            )

        self.loop_depth += 1
        node = DoUntilLoop(
            body      = body,
            condition = condition,
            line      = line,
            column    = column
        )
        self.loop_depth -= 1

        return node


    # ============================================
    # FOREACH LOOP
    # ============================================

    def create_foreach(self, variable, collection, body,
                       line=None, column=None):
        """
        Create a validated ForeachLoop node.

        Example:
            let fruits: Collection = ["Apple", "Mango"]
            foreach fruit from fruits {
                nimna.io.print("{fruit}")
            }
        """

        # Validate loop variable
        var_valid, var_error = self._validate_variable(variable, line)
        if not var_valid:
            self.errors.append(var_error)
            return None

        # Validate collection
        if collection is None:
            self.errors.append(
                f"[Line {line}] 'foreach' loop requires a collection."
            )
            return None

        # Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] 'foreach' loop has an empty body."
            )

        self.loop_depth += 1
        node = ForeachLoop(
            variable   = variable,
            collection = collection,
            body       = body,
            line       = line,
            column     = column
        )
        self.loop_depth -= 1

        return node


    # ============================================
    # PARALLEL LOOP
    # ============================================

    def create_parallel(self, variable, range_expr, body,
                        line=None, column=None):
        """
        Create a validated ParallelLoop node.

        Example:
            parallel for i from 0..1000 {
                process(i)
            }
        """

        # Validate loop variable
        var_valid, var_error = self._validate_variable(variable, line)
        if not var_valid:
            self.errors.append(var_error)
            return None

        # Validate range
        range_valid, range_error = self._validate_range(range_expr, line)
        if not range_valid:
            self.errors.append(range_error)
            return None

        # Empty body warning
        if not body:
            self.warnings.append(
                f"[Line {line}] 'parallel for' loop has an empty body."
            )

        # Parallel loop reminder
        self.warnings.append(
            f"[Line {line}] Parallel loop detected. "
            f"Ensure loop body is thread-safe."
        )

        self.loop_depth += 1
        node = ParallelLoop(
            variable   = variable,
            range_expr = range_expr,
            body       = body,
            line       = line,
            column     = column
        )
        self.loop_depth -= 1

        return node


    # ============================================
    # BREAK AND SKIP VALIDATION
    # ============================================

    def create_break(self, line=None, column=None):
        """
        Create a BreakStatement node.
        Must be inside a loop.
        """

        if self.loop_depth == 0:
            self.errors.append(
                f"[Line {line}] 'break' used outside of a loop."
            )
            return None

        return BreakStatement(line=line, column=column)


    def create_skip(self, line=None, column=None):
        """
        Create a SkipStatement node.
        Must be inside a loop.
        """

        if self.loop_depth == 0:
            self.errors.append(
                f"[Line {line}] 'skip' used outside of a loop."
            )
            return None

        return SkipStatement(line=line, column=column)


    # ============================================
    # HELPERS
    # ============================================

    def _validate_variable(self, variable, line):
        """Validate loop variable name."""

        if not variable:
            return False, (
                f"[Line {line}] Loop variable name cannot be empty."
            )

        if not (variable[0].isalpha() or variable[0] == '_'):
            return False, (
                f"[Line {line}] Loop variable '{variable}' must start "
                f"with a letter or underscore."
            )

        return True, ""


    def _validate_range(self, range_expr, line):
        """Validate range expression."""

        if range_expr is None:
            return False, (
                f"[Line {line}] Loop requires a valid range expression."
            )

        if not isinstance(range_expr, RangeExpression):
            return False, (
                f"[Line {line}] Invalid range expression in loop."
            )

        return True, ""


    def _validate_condition(self, condition, line):
        """Validate loop condition."""

        if condition is None:
            return False, (
                f"[Line {line}] Loop condition cannot be empty."
            )

        return True, ""


    def get_summary(self, node):
        """Get human readable loop summary."""

        if isinstance(node, ForLoop):
            return (
                f"for {node.variable} from [range] "
                f"{{ {len(node.body)} statement(s) }}"
            )
        elif isinstance(node, WhileLoop):
            return (
                f"while [condition] "
                f"{{ {len(node.body)} statement(s) }}"
            )
        elif isinstance(node, DoUntilLoop):
            return (
                f"do {{ {len(node.body)} statement(s) }} "
                f"until [condition]"
            )
        elif isinstance(node, ForeachLoop):
            return (
                f"foreach {node.variable} from [collection] "
                f"{{ {len(node.body)} statement(s) }}"
            )
        elif isinstance(node, ParallelLoop):
            return (
                f"parallel for {node.variable} from [range] "
                f"{{ {len(node.body)} statement(s) }}"
            )
        return str(node)


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []
