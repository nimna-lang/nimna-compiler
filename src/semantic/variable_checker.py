# ============================================
# NIMNA Language — Variable Declaration Checker
# File: src/semantic/variable_checker.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import (
    SymbolTable,
    KIND_VARIABLE,
    KIND_CONSTANT,
)


# ============================================
# VALID NIMNA TYPES
# ============================================

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

# Safe auto-conversions allowed
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

# Unsafe conversions — not allowed
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


# ============================================
# VARIABLE CHECKER CLASS
# ============================================

class VariableChecker:
    """
    NIMNA Variable Declaration Checker

    Checks:
    1. Duplicate variable in same scope
    2. Invalid type name
    3. Unsafe type assignment
    4. Constant reassignment
    5. Variable shadowing (warning)
    6. Naming rules
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table    = symbol_table
        self.filename = filename
        self.errors   = []
        self.warnings = []


    # ==========================================
    # MAIN CHECK METHODS
    # ==========================================

    def check_let(self, name, declared_type, value_type, line):
        """
        Check a let statement declaration.

        Parameters:
            name          : str — Variable name
            declared_type : str — Declared NIMNA type or None
            value_type    : str — Inferred type of value
            line          : int — Line number

        Returns:
            True if valid, False if errors found
        """

        valid = True

        # 1. Check naming rules
        if not self._valid_name(name, line):
            return False

        # 2. Check duplicate in current scope
        if self._is_duplicate(name, line):
            valid = False

        # 3. Check declared type is valid
        if declared_type:
            if not self._valid_type(declared_type, line):
                return False

        # 4. Check type compatibility
        if declared_type and value_type:
            if not self._check_type_compat(
                value_type, declared_type, line
            ):
                valid = False

        # 5. Check shadowing in outer scopes
        self._check_shadowing(name, line)

        return valid


    def check_constant(self, name, declared_type, value_type, line):
        """
        Check a constant declaration.

        Parameters:
            name          : str — Constant name
            declared_type : str — Declared NIMNA type or None
            value_type    : str — Inferred type of value
            line          : int — Line number

        Returns:
            True if valid, False if errors found
        """

        valid = True

        # 1. Check naming rules
        if not self._valid_name(name, line):
            return False

        # 2. Check duplicate
        if self._is_duplicate(name, line):
            valid = False

        # 3. Check type valid
        if declared_type:
            if not self._valid_type(declared_type, line):
                return False

        # 4. Check type compatibility
        if declared_type and value_type:
            if not self._check_type_compat(
                value_type, declared_type, line
            ):
                valid = False

        return valid


    def check_reassignment(self, name, new_type, line):
        """
        Check if a variable can be reassigned.

        Checks:
        - Variable exists
        - Not a constant
        - Type is compatible
        """

        sym = self.table.lookup(name)

        # Variable must exist
        if sym is None:
            self.errors.append(
                f"[Line {line}] '{name}' is not declared. "
                f"Declare it first: let {name}: Type = value"
            )
            return False

        # Cannot reassign constant
        if sym.is_constant:
            self.errors.append(
                f"[Line {line}] Cannot reassign constant '{name}'. "
                f"It was declared as constant at line {sym.line}."
            )
            return False

        # Check type compatibility for reassignment
        if new_type and sym.nimna_type and sym.nimna_type != "Wild":
            if not self._check_type_compat(
                new_type, sym.nimna_type, line
            ):
                return False

        return True


    # ==========================================
    # VALIDATION HELPERS
    # ==========================================

    def _valid_name(self, name, line):
        """
        Check identifier naming rules.

        Rules:
        1. Cannot be empty
        2. Must start with letter or underscore
        3. Cannot start with __
        4. Cannot be only underscores
        """

        if not name:
            self.errors.append(
                f"[Line {line}] Variable name cannot be empty."
            )
            return False

        if not (name[0].isalpha() or name[0] == '_'):
            self.errors.append(
                f"[Line {line}] Variable name '{name}' must start "
                f"with a letter or underscore."
            )
            return False

        if name.startswith('__'):
            self.errors.append(
                f"[Line {line}] Variable name '{name}' cannot start "
                f"with '__'. Reserved for compiler use."
            )
            return False

        if all(c == '_' for c in name):
            self.errors.append(
                f"[Line {line}] Variable name cannot consist "
                f"of only underscores."
            )
            return False

        return True


    def _valid_type(self, type_name, line):
        """Check if type name is a valid NIMNA type."""

        if type_name not in VALID_TYPES:
            self.errors.append(
                f"[Line {line}] Unknown type '{type_name}'. "
                f"Did you mean: Whole, Text, Decimal, Truth, ...?"
            )
            return False

        return True


    def _is_duplicate(self, name, line):
        """Check for duplicate in current scope."""

        existing = self.table.lookup_current(name)

        if existing is not None:
            self.errors.append(
                f"[Line {line}] '{name}' is already declared "
                f"in this scope (line {existing.line})."
            )
            return True

        return False


    def _check_type_compat(self, from_type, to_type, line):
        """
        Check if from_type can be assigned to to_type.
        """

        if from_type is None or to_type is None:
            return True

        if from_type == to_type:
            return True

        if from_type == "Wild" or to_type == "Wild":
            return True

        # Safe conversion
        if from_type in SAFE_CONVERSIONS:
            if to_type in SAFE_CONVERSIONS[from_type]:
                return True

        # Unsafe conversion
        key = (from_type, to_type)
        if key in UNSAFE_CONVERSIONS:
            reason = UNSAFE_CONVERSIONS[key]
            self.errors.append(
                f"[Line {line}] Cannot assign '{from_type}' "
                f"to '{to_type}'. {reason} "
                f"Use explicit conversion: {to_type}(value)"
            )
            return False

        # Completely incompatible
        self.errors.append(
            f"[Line {line}] Type mismatch: "
            f"Cannot assign '{from_type}' to '{to_type}'."
        )
        return False


    def _check_shadowing(self, name, line):
        """
        Warn if variable shadows an outer scope variable.
        Only warns — does not block.
        """

        if len(self.table.scope_stack) <= 1:
            return

        # Check outer scopes (not current)
        for scope in list(reversed(self.table.scope_stack))[1:]:
            if scope.has(name):
                outer_sym = scope.lookup(name)
                self.warnings.append(
                    f"[Line {line}] Variable '{name}' shadows "
                    f"'{name}' from outer scope "
                    f"(declared at line {outer_sym.line})."
                )
                break


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
