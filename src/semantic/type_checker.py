# ============================================
# NIMNA Language — Type Checker
# File: src/semantic/type_checker.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import SymbolTable


# ============================================
# TYPE CATEGORIES
# ============================================

WHOLE_TYPES   = {"Tiny", "Short", "Whole", "Long", "Huge"}
DECIMAL_TYPES = {"Decimal", "Precise", "Exact"}
NUMERIC_TYPES = WHOLE_TYPES | DECIMAL_TYPES
TEXT_TYPES    = {"Text", "Letter", "Symbol"}

VALID_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Symbol",
    "Truth", "Bit",
    "Sequence", "Collection", "Mapping",
    "Unique", "Bundle",
    "Maybe", "Outcome", "Task",
    "Flow", "Action", "Wild", "Nothing",
}

# Whole number size order (small to large)
WHOLE_ORDER = ["Tiny", "Short", "Whole", "Long", "Huge"]

# Safe auto-conversions
SAFE_CONVERSIONS = {
    "Tiny"    : {"Short", "Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Short"   : {"Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Whole"   : {"Long", "Huge", "Decimal",
                 "Precise", "Exact", "Text"},
    "Long"    : {"Huge", "Precise", "Exact", "Text"},
    "Huge"    : {"Precise", "Exact", "Text"},
    "Decimal" : {"Precise", "Exact", "Text"},
    "Precise" : {"Exact", "Text"},
    "Exact"   : {"Text"},
    "Text"    : {"Whole", "Decimal", "Truth"},
    "Truth"   : {"Whole", "Text"},
    "Letter"  : {"Text", "Whole"},
}

# Unsafe conversions with reasons
UNSAFE_CONVERSIONS = {
    ("Decimal", "Whole")  : "Data loss — decimal part will be cut.",
    ("Decimal", "Tiny")   : "Data loss — decimal part will be cut.",
    ("Decimal", "Short")  : "Data loss — decimal part will be cut.",
    ("Precise", "Decimal"): "Precision loss possible.",
    ("Precise", "Whole")  : "Data loss possible.",
    ("Long",    "Whole")  : "Overflow possible.",
    ("Long",    "Short")  : "Overflow possible.",
    ("Long",    "Tiny")   : "Overflow possible.",
    ("Huge",    "Long")   : "Overflow possible.",
    ("Huge",    "Whole")  : "Overflow possible.",
    ("Whole",   "Short")  : "Overflow possible.",
    ("Whole",   "Tiny")   : "Overflow possible.",
}

# Operator result types
ARITHMETIC_OPS  = {"+", "-", "*", "/", "%", "**"}
COMPARISON_OPS  = {"==", "!=", ">", "<", ">=", "<="}
LOGICAL_OPS     = {"&&", "||"}
BITWISE_OPS     = {"&", "|", "^", "~", "<<", ">>"}
RANGE_OPS       = {"..", "..=", "..."}


# ============================================
# TYPE CHECKER CLASS
# ============================================

class TypeChecker:
    """
    NIMNA Type Checker

    Checks:
    1. Assignment type compatibility
    2. Binary expression type rules
    3. Unary expression type rules
    4. Type cast validity
    5. Collection element types
    6. Operator type requirements
    7. Comparison type compatibility
    8. Logical operator requirements
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table    = symbol_table
        self.filename = filename
        self.errors   = []
        self.warnings = []


    # ==========================================
    # ASSIGNMENT CHECK
    # ==========================================

    def check_assignment(self, target_type, value_type, line,
                         is_input=False):
        """
        Check if value_type can be assigned to target_type.

        Parameters:
            target_type : str  — Declared variable type
            value_type  : str  — Type of the value being assigned
            line        : int  — Line number
            is_input    : bool — Is this from nimna.io.input()?

        Returns:
            True if compatible, False if error
        """

        if not target_type or not value_type:
            return True

        if target_type == "Wild" or value_type == "Wild":
            return True

        if target_type == value_type:
            return True

        # Input special case: Text from input can auto-convert
        if is_input and value_type == "Text":
            if target_type in {"Whole", "Decimal", "Truth",
                               "Tiny", "Short", "Long", "Huge",
                               "Precise", "Exact"}:
                return True

        # Safe conversion
        if value_type in SAFE_CONVERSIONS:
            if target_type in SAFE_CONVERSIONS[value_type]:
                return True

        # Unsafe conversion
        key = (value_type, target_type)
        if key in UNSAFE_CONVERSIONS:
            reason = UNSAFE_CONVERSIONS[key]
            self.errors.append(
                f"[Line {line}] Cannot assign '{value_type}' "
                f"to '{target_type}'. {reason} "
                f"Use explicit conversion: {target_type}(value)"
            )
            return False

        # Incompatible
        self.errors.append(
            f"[Line {line}] Type mismatch: "
            f"Cannot assign '{value_type}' to '{target_type}'."
        )
        return False


    # ==========================================
    # BINARY EXPRESSION CHECK
    # ==========================================

    def check_binary(self, left_type, operator, right_type, line):
        """
        Check binary expression types and return result type.

        Parameters:
            left_type  : str — Left operand type
            operator   : str — Operator
            right_type : str — Right operand type
            line       : int — Line number

        Returns:
            result_type str or None if error
        """

        if not left_type or not right_type:
            return left_type or right_type

        if left_type == "Wild" or right_type == "Wild":
            return "Wild"

        # Comparison operators — always return Truth
        if operator in COMPARISON_OPS:
            return self._check_comparison(
                left_type, operator, right_type, line
            )

        # Logical operators — require Truth
        if operator in LOGICAL_OPS:
            return self._check_logical(
                left_type, operator, right_type, line
            )

        # Range operators
        if operator in RANGE_OPS:
            return self._check_range(
                left_type, right_type, line
            )

        # Arithmetic operators
        if operator in ARITHMETIC_OPS:
            return self._check_arithmetic(
                left_type, operator, right_type, line
            )

        # Bitwise operators
        if operator in BITWISE_OPS:
            return self._check_bitwise(
                left_type, right_type, line
            )

        return left_type


    def _check_comparison(self, left_type, operator, right_type, line):
        """Comparison operators — result is always Truth."""

        # Cannot compare incompatible types
        if (left_type in NUMERIC_TYPES and
                right_type in NUMERIC_TYPES):
            return "Truth"

        if left_type == right_type:
            return "Truth"

        if left_type in TEXT_TYPES and right_type in TEXT_TYPES:
            return "Truth"

        if operator in ("==", "!="):
            # == and != work on any matching types
            return "Truth"

        # Ordering comparison on incompatible types
        if operator in (">", "<", ">=", "<="):
            if (left_type not in NUMERIC_TYPES or
                    right_type not in NUMERIC_TYPES):
                self.errors.append(
                    f"[Line {line}] Cannot use '{operator}' "
                    f"between '{left_type}' and '{right_type}'. "
                    f"Ordering requires numeric types."
                )
                return "Truth"

        return "Truth"


    def _check_logical(self, left_type, operator, right_type, line):
        """Logical operators — require Truth operands."""

        if left_type != "Truth":
            self.errors.append(
                f"[Line {line}] Left operand of '{operator}' "
                f"must be Truth, got '{left_type}'."
            )

        if right_type != "Truth":
            self.errors.append(
                f"[Line {line}] Right operand of '{operator}' "
                f"must be Truth, got '{right_type}'."
            )

        return "Truth"


    def _check_range(self, left_type, right_type, line):
        """Range operators — require numeric types."""

        if left_type not in NUMERIC_TYPES:
            self.errors.append(
                f"[Line {line}] Range start must be numeric, "
                f"got '{left_type}'."
            )

        if right_type and right_type not in NUMERIC_TYPES:
            self.errors.append(
                f"[Line {line}] Range end must be numeric, "
                f"got '{right_type}'."
            )

        return "Range"


    def _check_arithmetic(self, left_type, operator, right_type, line):
        """Arithmetic operators — check numeric + text concat rules."""

        # Text concatenation with +
        if operator == "+" and left_type in TEXT_TYPES:
            if right_type not in TEXT_TYPES:
                self.errors.append(
                    f"[Line {line}] Cannot use '+' between "
                    f"'{left_type}' and '{right_type}'. "
                    f"Convert to Text first: Text(value)"
                )
                return "Text"
            return "Text"

        # Non-numeric arithmetic
        if left_type not in NUMERIC_TYPES:
            self.errors.append(
                f"[Line {line}] Cannot use '{operator}' "
                f"on '{left_type}'. Numeric type required."
            )
            return left_type

        if right_type not in NUMERIC_TYPES:
            self.errors.append(
                f"[Line {line}] Cannot use '{operator}' "
                f"on '{right_type}'. Numeric type required."
            )
            return left_type

        # Division by zero check
        return self._get_numeric_result(left_type, right_type)


    def _check_bitwise(self, left_type, right_type, line):
        """Bitwise operators — require whole number types."""

        if left_type not in WHOLE_TYPES:
            self.errors.append(
                f"[Line {line}] Bitwise operator requires "
                f"whole number type, got '{left_type}'."
            )

        if right_type not in WHOLE_TYPES:
            self.errors.append(
                f"[Line {line}] Bitwise operator requires "
                f"whole number type, got '{right_type}'."
            )

        return self._get_numeric_result(left_type, right_type)


    def _get_numeric_result(self, left_type, right_type):
        """Get result type of numeric operation."""

        # If either is decimal, result is decimal
        if left_type in DECIMAL_TYPES or right_type in DECIMAL_TYPES:
            if left_type == "Exact" or right_type == "Exact":
                return "Exact"
            if left_type == "Precise" or right_type == "Precise":
                return "Precise"
            return "Decimal"

        # Both are whole — return the larger
        li = WHOLE_ORDER.index(left_type)  if left_type  in WHOLE_ORDER else 2
        ri = WHOLE_ORDER.index(right_type) if right_type in WHOLE_ORDER else 2
        return WHOLE_ORDER[max(li, ri)]


    # ==========================================
    # UNARY EXPRESSION CHECK
    # ==========================================

    def check_unary(self, operator, operand_type, line):
        """
        Check unary expression.

        Operators:
            !! → requires Truth, returns Truth
            -  → requires numeric, returns same type
        """

        if not operand_type or operand_type == "Wild":
            return operand_type

        if operator == "!!":
            if operand_type != "Truth":
                self.errors.append(
                    f"[Line {line}] '!!' operator requires "
                    f"Truth type, got '{operand_type}'."
                )
            return "Truth"

        if operator == "-":
            if operand_type not in NUMERIC_TYPES:
                self.errors.append(
                    f"[Line {line}] Unary '-' requires "
                    f"numeric type, got '{operand_type}'."
                )
            return operand_type

        return operand_type


    # ==========================================
    # TYPE CAST CHECK
    # ==========================================

    def check_cast(self, from_type, to_type, line):
        """
        Check 'as' type cast validity.

        Returns:
            to_type if valid, None if error
        """

        if not from_type or not to_type:
            return to_type

        if from_type == to_type:
            return to_type

        if to_type not in VALID_TYPES:
            self.errors.append(
                f"[Line {line}] Invalid cast target type '{to_type}'."
            )
            return None

        # Warn on potentially unsafe casts
        key = (from_type, to_type)
        if key in UNSAFE_CONVERSIONS:
            self.warnings.append(
                f"[Line {line}] Casting '{from_type}' to '{to_type}' "
                f"may cause: {UNSAFE_CONVERSIONS[key]}"
            )

        return to_type


    # ==========================================
    # TYPE CONSTRUCTOR CHECK
    # ==========================================

    def check_type_constructor(self, type_name, arg_type, line):
        """
        Check TypeName(value) constructor call.

        Returns:
            type_name if valid
        """

        if type_name not in VALID_TYPES:
            self.errors.append(
                f"[Line {line}] '{type_name}' is not a valid type."
            )
            return None

        # Warn if conversion is potentially lossy
        if arg_type and arg_type != "Wild":
            key = (arg_type, type_name)
            if key in UNSAFE_CONVERSIONS:
                self.warnings.append(
                    f"[Line {line}] Explicit conversion "
                    f"'{type_name}({arg_type})' may cause: "
                    f"{UNSAFE_CONVERSIONS[key]}"
                )

        return type_name


    # ==========================================
    # COLLECTION TYPE CHECK
    # ==========================================

    def check_collection(self, element_types, line):
        """
        Check collection literal type consistency.
        Warns if elements have mixed types.

        Returns:
            element type or "Wild" if mixed
        """

        if not element_types:
            return "Wild"

        unique_types = set(t for t in element_types if t)

        if len(unique_types) == 1:
            return list(unique_types)[0]

        if len(unique_types) > 1:
            self.warnings.append(
                f"[Line {line}] Collection has mixed types: "
                f"{', '.join(sorted(unique_types))}. "
                f"Consider using a single type."
            )

        return "Wild"


    # ==========================================
    # TYPE UTILITY
    # ==========================================

    def is_numeric(self, type_name):
        return type_name in NUMERIC_TYPES

    def is_whole(self, type_name):
        return type_name in WHOLE_TYPES

    def is_decimal(self, type_name):
        return type_name in DECIMAL_TYPES

    def is_text(self, type_name):
        return type_name in TEXT_TYPES

    def is_valid(self, type_name):
        return type_name in VALID_TYPES

    def are_compatible(self, from_type, to_type):
        """Quick compatibility check without errors."""
        if not from_type or not to_type:
            return True
        if from_type == to_type:
            return True
        if from_type == "Wild" or to_type == "Wild":
            return True
        if from_type in SAFE_CONVERSIONS:
            if to_type in SAFE_CONVERSIONS[from_type]:
                return True
        return False

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear(self):
        self.errors   = []
        self.warnings = []
