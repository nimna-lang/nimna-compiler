# ============================================
# NIMNA Language — IfStatement Handler
# File: src/ast/if_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    IfStatement,
    BinaryExpression,
    TruthLiteral,
    Identifier,
)


# ============================================
# IF STATEMENT HANDLER CLASS
# ============================================

class IfHandler:
    """
    NIMNA IfStatement Handler

    Processes if-elif-else statements and validates:
    - Condition expressions
    - Then body
    - Elif clauses
    - Else body
    - Nested if statements
    - Unreachable code detection
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename
        self.errors   = []
        self.warnings = []


    def create(self, condition, then_body, elif_clauses=None,
               else_body=None, line=None, column=None):
        """
        Create a validated IfStatement node.

        Parameters:
            condition    : Node  — Condition expression
            then_body    : list  — Statements if condition is true
            elif_clauses : list  — List of (condition, body) tuples
            else_body    : list  — Statements if all conditions false
            line         : int   — Line number
            column       : int   — Column number

        Returns:
            IfStatement node or None if invalid
        """

        elif_clauses = elif_clauses or []
        else_body    = else_body    or []

        # Step 1: Validate condition
        cond_valid, cond_error = self._validate_condition(condition, line)
        if not cond_valid:
            self.errors.append(cond_error)
            return None

        # Step 2: Validate then body
        if not then_body:
            self.warnings.append(
                f"[Line {line}] 'if' block has an empty body."
            )

        # Step 3: Validate elif clauses
        elif_errors = self._validate_elif_clauses(elif_clauses, line)
        if elif_errors:
            self.errors.extend(elif_errors)
            return None

        # Step 4: Check for constant conditions
        self._check_constant_condition(condition, line)

        # Step 5: Elif without else warning
        if elif_clauses and not else_body:
            self.warnings.append(
                f"[Line {line}] 'elif' present but no 'else' block. "
                f"Consider adding an 'else' for complete coverage."
            )

        # Step 6: Create and return node
        return IfStatement(
            condition    = condition,
            then_body    = then_body,
            elif_clauses = elif_clauses,
            else_body    = else_body,
            line         = line,
            column       = column
        )


    def _validate_condition(self, condition, line):
        """
        Validate that condition is a proper expression.
        """

        if condition is None:
            return False, (
                f"[Line {line}] 'if' statement requires a condition."
            )

        return True, ""


    def _validate_elif_clauses(self, elif_clauses, line):
        """
        Validate all elif clauses.
        Each must have a condition and body.
        """

        errors = []

        for i, (elif_cond, elif_body) in enumerate(elif_clauses):

            if elif_cond is None:
                errors.append(
                    f"[Line {line}] 'elif' clause {i+1} "
                    f"is missing a condition."
                )

            if not elif_body:
                self.warnings.append(
                    f"[Line {line}] 'elif' clause {i+1} has empty body."
                )

        return errors


    def _check_constant_condition(self, condition, line):
        """
        Warn if condition is always true or always false.
        """

        if isinstance(condition, TruthLiteral):
            if condition.value is True:
                self.warnings.append(
                    f"[Line {line}] Condition is always 'true'. "
                    f"Consider using a loop or removing the 'if'."
                )
            elif condition.value is False:
                self.warnings.append(
                    f"[Line {line}] Condition is always 'false'. "
                    f"This 'if' block will never execute."
                )


    def get_structure(self, node):
        """
        Get human readable if statement structure.
        """

        lines = []
        lines.append(
            f"if [condition] {{"
            f" {len(node.then_body)} statement(s) }}"
        )

        for i, (cond, body) in enumerate(node.elif_clauses):
            lines.append(
                f"elif [condition] {{"
                f" {len(body)} statement(s) }}"
            )

        if node.else_body:
            lines.append(
                f"else {{"
                f" {len(node.else_body)} statement(s) }}"
            )

        return "\n  ".join(lines)


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []
