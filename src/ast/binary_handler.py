# ============================================
# NIMNA Language — BinaryExpression Handler
# File: src/ast/binary_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    BinaryExpression,
    TypeCastExpression,
    IntegerLiteral,
    DecimalLiteral,
    TextLiteral,
    TruthLiteral,
    Identifier,
)


# ============================================
# OPERATOR CATEGORIES
# ============================================

ARITHMETIC_OPS = {"+", "-", "*", "/", "%", "**"}

COMPARISON_OPS = {"==", "!=", ">", "<", ">=", "<="}

LOGICAL_OPS    = {"&&", "||"}

BITWISE_OPS    = {"&", "|", "^", "~", "<<", ">>"}

RANGE_OPS      = {"..", "..=", "..."}

PIPELINE_OPS   = {"|>", "<|", ">>"}

ALL_BINARY_OPS = (
    ARITHMETIC_OPS |
    COMPARISON_OPS |
    LOGICAL_OPS    |
    BITWISE_OPS    |
    RANGE_OPS      |
    PIPELINE_OPS
)


# ============================================
# TYPE COMPATIBILITY FOR OPERATIONS
# ============================================

# Which types can be used with arithmetic operators
ARITHMETIC_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact"
}

# Which types can be compared
COMPARABLE_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Truth"
}

# Text + Text = Concatenation
TEXT_CONCAT_OP = "+"

# Result types for arithmetic operations
ARITHMETIC_RESULT = {
    ("Tiny",    "Tiny")   : "Tiny",
    ("Short",   "Short")  : "Short",
    ("Whole",   "Whole")  : "Whole",
    ("Long",    "Long")   : "Long",
    ("Huge",    "Huge")   : "Huge",
    ("Decimal", "Decimal"): "Decimal",
    ("Precise", "Precise"): "Precise",
    ("Exact",   "Exact")  : "Exact",
    ("Whole",   "Decimal"): "Decimal",
    ("Decimal", "Whole")  : "Decimal",
    ("Tiny",    "Whole")  : "Whole",
    ("Short",   "Whole")  : "Whole",
    ("Whole",   "Long")   : "Long",
    ("Long",    "Huge")   : "Huge",
}


# ============================================
# BINARY EXPRESSION HANDLER CLASS
# ============================================

class BinaryHandler:
    """
    NIMNA BinaryExpression Handler

    Handles all binary operations:
    - Arithmetic  : + - * / % **
    - Comparison  : == != > < >= <=
    - Logical     : && ||
    - Bitwise     : & | ^ ~ << >>
    - Range       : .. ..= ...
    - Pipeline    : |> <|
    - Type Cast   : as

    Validates:
    - Operator validity
    - Type compatibility
    - Division by zero
    - Text concatenation rules
    - Type casting rules
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename
        self.errors   = []
        self.warnings = []


    def create(self, left, operator, right,
               line=None, column=None):
        """
        Create a validated BinaryExpression node.

        Parameters:
            left     : Node — Left side expression
            operator : str  — Operator string
            right    : Node — Right side expression
            line     : int  — Line number
            column   : int  — Column number

        Returns:
            BinaryExpression node or None if invalid
        """

        # Step 1: Validate operator
        op_valid, op_error = self._validate_operator(operator, line)
        if not op_valid:
            self.errors.append(op_error)
            return None

        # Step 2: Validate operands
        if left is None:
            self.errors.append(
                f"[Line {line}] Missing left operand for '{operator}'."
            )
            return None

        if right is None:
            self.errors.append(
                f"[Line {line}] Missing right operand for '{operator}'."
            )
            return None

        # Step 3: Type compatibility check
        left_type  = self._get_node_type(left)
        right_type = self._get_node_type(right)

        compat_valid, compat_msg = self._check_compatibility(
            left_type, operator, right_type, line
        )
        if not compat_valid:
            self.errors.append(compat_msg)
            return None

        # Step 4: Division by zero check
        if operator == "/" and isinstance(right, IntegerLiteral):
            if right.value == 0:
                self.errors.append(
                    f"[Line {line}] Division by zero detected. "
                    f"Cannot divide by 0."
                )
                return None

        if operator == "/" and isinstance(right, DecimalLiteral):
            if right.value == 0.0:
                self.errors.append(
                    f"[Line {line}] Division by zero detected. "
                    f"Cannot divide by 0.0."
                )
                return None

        # Step 5: Text + non-Text warning
        if (operator == "+" and
            left_type == "Text" and
            right_type != "Text"):
            self.warnings.append(
                f"[Line {line}] Cannot concatenate 'Text' with '{right_type}'. "
                f"Use explicit conversion: Text(value)."
            )

        # Step 6: Create and return node
        return BinaryExpression(
            left     = left,
            operator = operator,
            right    = right,
            line     = line,
            column   = column
        )


    def create_type_cast(self, value, target_type,
                         line=None, column=None):
        """
        Create a TypeCastExpression node.

        Example:
            age as Decimal
            score as Whole
        """

        VALID_CAST_TYPES = {
            "Tiny", "Short", "Whole", "Long", "Huge",
            "Decimal", "Precise", "Exact",
            "Text", "Letter", "Truth"
        }

        # Validate target type
        if target_type not in VALID_CAST_TYPES:
            self.errors.append(
                f"[Line {line}] Invalid cast target type '{target_type}'."
            )
            return None

        # Validate value
        if value is None:
            self.errors.append(
                f"[Line {line}] Missing value for type cast."
            )
            return None

        # Unsafe cast warnings
        source_type = self._get_node_type(value)
        if source_type and source_type != target_type:
            unsafe = self._is_unsafe_cast(source_type, target_type)
            if unsafe:
                self.warnings.append(
                    f"[Line {line}] Casting '{source_type}' to "
                    f"'{target_type}' may cause data loss."
                )

        return TypeCastExpression(
            value       = value,
            target_type = target_type,
            line        = line,
            column      = column
        )


    def get_result_type(self, left_type, operator, right_type):
        """
        Determine the result type of a binary operation.
        """

        if operator in COMPARISON_OPS or operator in LOGICAL_OPS:
            return "Truth"

        if operator in RANGE_OPS:
            return "Range"

        if operator == "+" and left_type == "Text":
            return "Text"

        key = (left_type, right_type)
        if key in ARITHMETIC_RESULT:
            return ARITHMETIC_RESULT[key]

        rev_key = (right_type, left_type)
        if rev_key in ARITHMETIC_RESULT:
            return ARITHMETIC_RESULT[rev_key]

        return left_type


    def _validate_operator(self, operator, line):
        """Validate that operator is a known NIMNA operator."""

        if not operator:
            return False, f"[Line {line}] Empty operator."

        if operator not in ALL_BINARY_OPS:
            return False, (
                f"[Line {line}] Unknown operator '{operator}'."
            )

        return True, ""


    def _get_node_type(self, node):
        """Get the NIMNA type of a node."""

        if isinstance(node, IntegerLiteral):
            return "Whole"
        elif isinstance(node, DecimalLiteral):
            return "Decimal"
        elif isinstance(node, TextLiteral):
            return "Text"
        elif isinstance(node, TruthLiteral):
            return "Truth"
        return None


    def _check_compatibility(self, left_type, operator, right_type, line):
        """
        Check if left and right types are compatible with the operator.
        """

        # Both types unknown — skip check
        if not left_type or not right_type:
            return True, ""

        # Logical operators need Truth types
        if operator in LOGICAL_OPS:
            if left_type != "Truth" or right_type != "Truth":
                return False, (
                    f"[Line {line}] Logical operator '{operator}' "
                    f"requires Truth operands. "
                    f"Got '{left_type}' and '{right_type}'."
                )

        # Text concatenation
        if operator == "+" and left_type == "Text":
            if right_type != "Text":
                return False, (
                    f"[Line {line}] Cannot use '+' between "
                    f"'Text' and '{right_type}'. "
                    f"Convert to Text first: Text(value)."
                )

        # Arithmetic on non-numeric types
        if (operator in ARITHMETIC_OPS - {"+"} and
            left_type == "Text"):
            return False, (
                f"[Line {line}] Cannot use '{operator}' on Text type."
            )

        return True, ""


    def _is_unsafe_cast(self, source_type, target_type):
        """Check if a type cast is potentially unsafe."""

        UNSAFE_CASTS = {
            ("Decimal", "Whole"),
            ("Precise", "Decimal"),
            ("Long",    "Whole"),
            ("Long",    "Short"),
            ("Long",    "Tiny"),
            ("Whole",   "Short"),
            ("Whole",   "Tiny"),
            ("Huge",    "Long"),
        }

        return (source_type, target_type) in UNSAFE_CASTS


    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []
