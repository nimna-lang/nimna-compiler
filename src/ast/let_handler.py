# ============================================
# NIMNA Language — LetStatement Handler
# File: src/ast/let_handler.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../lexer')

from nodes import (
    LetStatement,
    IntegerLiteral,
    DecimalLiteral,
    TextLiteral,
    LetterLiteral,
    TruthLiteral,
    NothingLiteral,
    CollectionLiteral,
    MappingLiteral,
    Identifier,
    BinaryExpression,
    TypeConstructorExpression,
    CallExpression,
)


# ============================================
# VALID NIMNA TYPES
# ============================================

VALID_TYPES = {
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
    "Maybe", "Outcome", "Task", "Flow", "Action", "Wild", "Nothing",
}


# ============================================
# AUTO CONVERSION RULES
# ============================================

# Safe conversions — allowed automatically
SAFE_CONVERSIONS = {
    "Tiny"    : {"Short", "Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Short"   : {"Whole", "Long", "Huge",
                 "Decimal", "Precise", "Exact", "Text"},
    "Whole"   : {"Long", "Huge", "Decimal", "Precise", "Exact", "Text"},
    "Long"    : {"Huge", "Precise", "Exact", "Text"},
    "Decimal" : {"Precise", "Exact", "Text"},
    "Precise" : {"Exact", "Text"},
    "Text"    : {"Whole", "Decimal", "Truth"},  # Input only
}

# Unsafe conversions — not allowed
UNSAFE_CONVERSIONS = {
    ("Decimal", "Whole")  : "Data loss possible",
    ("Precise", "Decimal"): "Precision loss possible",
    ("Long",    "Whole")  : "Overflow possible",
    ("Whole",   "Tiny")   : "Overflow possible",
    ("Whole",   "Short")  : "Overflow possible",
    ("Long",    "Short")  : "Overflow possible",
    ("Long",    "Tiny")   : "Overflow possible",
}


# ============================================
# LET STATEMENT HANDLER CLASS
# ============================================

class LetStatementHandler:
    """
    NIMNA LetStatement Handler

    Processes variable declarations and validates:
    - Name validity
    - Type validity
    - Value type compatibility
    - Auto conversion rules
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename
        self.errors   = []
        self.warnings = []


    def create(self, name, declared_type, value,
               line=None, column=None):
        """
        Create a validated LetStatement node.

        Parameters:
            name          : str  — Variable name
            declared_type : str  — Declared type or None
            value         : Node — Value expression node
            line          : int  — Line number
            column        : int  — Column number

        Returns:
            LetStatement node or None if invalid
        """

        # Step 1: Validate variable name
        name_valid, name_error = self._validate_name(name)
        if not name_valid:
            self.errors.append(
                f"[Line {line}] {name_error}"
            )
            return None

        # Step 2: Validate declared type
        if declared_type:
            type_valid, type_error = self._validate_type(declared_type)
            if not type_valid:
                self.errors.append(
                    f"[Line {line}] {type_error}"
                )
                return None

        # Step 3: Check value compatibility
        if declared_type and value:
            compat_valid, compat_msg = self._check_compatibility(
                declared_type, value, line
            )
            if not compat_valid:
                self.errors.append(compat_msg)
                return None

        # Step 4: Type inference if no type declared
        if not declared_type and value:
            inferred = self._infer_type(value)
            if inferred:
                self.warnings.append(
                    f"[Line {line}] Type inferred as '{inferred}' "
                    f"for variable '{name}'."
                )

        # Step 5: Create and return node
        return LetStatement(
            name          = name,
            declared_type = declared_type,
            value         = value,
            line          = line,
            column        = column
        )


    def _validate_name(self, name):
        """
        Validate variable name.
        """

        if not name:
            return False, "Variable name cannot be empty."

        if not (name[0].isalpha() or name[0] == '_'):
            return False, (
                f"Variable name '{name}' must start with "
                f"a letter or underscore."
            )

        if name.startswith('__'):
            return False, (
                f"Variable name '{name}' cannot start with '__'. "
                f"Reserved for compiler use."
            )

        if all(c == '_' for c in name):
            return False, (
                f"Variable name cannot be only underscores."
            )

        return True, ""


    def _validate_type(self, type_name):
        """
        Validate declared type name.
        """

        if type_name not in VALID_TYPES:
            return False, (
                f"Unknown type '{type_name}'. "
                f"Valid types: {', '.join(sorted(VALID_TYPES))}"
            )

        return True, ""


    def _check_compatibility(self, declared_type, value, line):
        """
        Check if value is compatible with declared type.
        Handles auto-conversion rules.
        """

        value_type = self._get_value_type(value)

        if not value_type:
            return True, ""

        # Same type — always compatible
        if value_type == declared_type:
            return True, ""

        # Check unsafe conversions
        key = (value_type, declared_type)
        if key in UNSAFE_CONVERSIONS:
            reason = UNSAFE_CONVERSIONS[key]
            return False, (
                f"[Line {line}] Type Error: "
                f"Cannot assign '{value_type}' to '{declared_type}'. "
                f"Reason: {reason}. "
                f"Use explicit conversion: {declared_type}(value)"
            )

        # Check safe conversions
        if value_type in SAFE_CONVERSIONS:
            if declared_type in SAFE_CONVERSIONS[value_type]:
                return True, ""

        return True, ""


    def _get_value_type(self, value):
        """
        Determine the type of a value node.
        """

        if isinstance(value, IntegerLiteral):
            return "Whole"
        elif isinstance(value, DecimalLiteral):
            return "Decimal"
        elif isinstance(value, TextLiteral):
            return "Text"
        elif isinstance(value, LetterLiteral):
            return "Letter"
        elif isinstance(value, TruthLiteral):
            return "Truth"
        elif isinstance(value, NothingLiteral):
            return "Nothing"
        elif isinstance(value, CollectionLiteral):
            return "Collection"
        elif isinstance(value, MappingLiteral):
            return "Mapping"
        elif isinstance(value, TypeConstructorExpression):
            return value.type_name

        return None


    def _infer_type(self, value):
        """
        Infer type from value when no type is declared.
        """

        type_map = {
            IntegerLiteral         : "Whole",
            DecimalLiteral         : "Decimal",
            TextLiteral            : "Text",
            LetterLiteral          : "Letter",
            TruthLiteral           : "Truth",
            NothingLiteral         : "Nothing",
            CollectionLiteral      : "Collection",
            MappingLiteral         : "Mapping",
        }

        for node_type, nimna_type in type_map.items():
            if isinstance(value, node_type):
                return nimna_type

        return None


    def get_errors(self):
        """Return all errors."""
        return self.errors


    def get_warnings(self):
        """Return all warnings."""
        return self.warnings


    def has_errors(self):
        """Check if any errors exist."""
        return len(self.errors) > 0


    def clear(self):
        """Clear errors and warnings."""
        self.errors   = []
        self.warnings = []
