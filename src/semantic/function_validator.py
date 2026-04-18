# ============================================
# NIMNA Language — Function Signature Validator
# File: src/semantic/function_validator.py
# Compiler: nimac
# ============================================

import sys
sys.path.insert(0, '../semantic')

from symbol_table import SymbolTable, KIND_FUNCTION, KIND_PARAM


# ============================================
# TYPE RULES
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

ASYNC_VALID_RETURNS = {
    "Task", "Nothing", "Maybe", "Outcome", "Flow"
}

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


# ============================================
# FUNCTION SIGNATURE VALIDATOR
# ============================================

class FunctionValidator:
    """
    NIMNA Function Signature Validator

    Checks:
    1. Function name validity
    2. Parameter names and types
    3. Duplicate parameter names
    4. Return type validity
    5. Async return type rules
    6. Return statement type matches declared return type
    7. Missing return statement
    8. Duplicate function names
    9. Call argument count and types
    """

    def __init__(self, symbol_table, filename="<nimna>"):
        self.table    = symbol_table
        self.filename = filename
        self.errors   = []
        self.warnings = []


    # ==========================================
    # FUNCTION DECLARATION VALIDATION
    # ==========================================

    def validate_declaration(self, name, params,
                              return_type, is_async, line):
        """
        Validate a full function declaration.

        Parameters:
            name        : str  — Function name
            params      : list — List of Parameter nodes
            return_type : str  — Return type or None
            is_async    : bool — Is async function
            line        : int  — Line number

        Returns:
            True if valid, False if errors
        """

        valid = True

        # 1. Validate function name
        if not self._valid_name(name, line):
            return False

        # 2. Check duplicate function name
        existing = self.table.lookup_current(name)
        if existing is not None and existing.kind == KIND_FUNCTION:
            self.errors.append(
                f"[Line {line}] Function '{name}' is already declared "
                f"(first declared at line {existing.line})."
            )
            return False

        # 3. Validate parameters
        if not self._validate_params(params, line):
            valid = False

        # 4. Validate return type
        if return_type:
            if not self._valid_type(return_type, line):
                valid = False

        # 5. Async return type check
        if is_async and return_type:
            if return_type not in ASYNC_VALID_RETURNS:
                self.errors.append(
                    f"[Line {line}] Async function '{name}' cannot "
                    f"return '{return_type}'. "
                    f"Async functions must return: "
                    f"{', '.join(sorted(ASYNC_VALID_RETURNS))}."
                )
                valid = False

        # 6. Warn if async has no return type
        if is_async and not return_type:
            self.warnings.append(
                f"[Line {line}] Async function '{name}' has no "
                f"return type. Consider returning 'Task' or 'Nothing'."
            )

        return valid


    def validate_return_statement(self, func_name, return_type,
                                   value_type, line):
        """
        Validate that return value matches declared return type.

        Parameters:
            func_name   : str — Current function name
            return_type : str — Declared return type
            value_type  : str — Actual returned value type
            line        : int — Line number

        Returns:
            True if valid, False if mismatch
        """

        # No declared return type — anything is OK
        if not return_type or return_type == "Nothing":
            return True

        # No value type known — skip
        if not value_type or value_type == "Wild":
            return True

        # Same type — always OK
        if return_type == value_type:
            return True

        # Return context safe conversions
        # Note: Text->Whole only allowed from input(), not return
        RETURN_SAFE = {
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
            "Truth"   : {"Whole", "Text"},
            "Letter"  : {"Text", "Whole"},
        }

        if value_type in RETURN_SAFE:
            if return_type in RETURN_SAFE[value_type]:
                return True

        # Type mismatch
        self.errors.append(
            f"[Line {line}] Return type mismatch in '{func_name}'. "
            f"Expected '{return_type}' but got '{value_type}'. "
            f"Change return type or convert the value."
        )
        return False


    def validate_call(self, func_name, arg_types,
                      arg_count, line):
        """
        Validate a function call — argument count and types.

        Parameters:
            func_name : str  — Function being called
            arg_types : list — List of argument types
            arg_count : int  — Number of arguments passed
            line      : int  — Line number

        Returns:
            return_type str or None
        """

        # nimna.* paths — always valid
        if func_name.startswith("nimna."):
            return "Wild"

        # Look up function
        sym = self.table.lookup(func_name)

        if sym is None:
            self.errors.append(
                f"[Line {line}] Function '{func_name}' is not declared."
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
        expected_count = len(sym.params) if sym.params else 0

        if arg_count != expected_count:
            self.errors.append(
                f"[Line {line}] '{func_name}' expects "
                f"{expected_count} argument(s) but got {arg_count}."
            )
            return sym.return_type

        # Check argument types
        if sym.params and arg_types:
            for i, (param, arg_type) in enumerate(
                zip(sym.params, arg_types)
            ):
                param_type = param.param_type
                if arg_type and param_type:
                    compatible = self._types_compatible(
                        arg_type, param_type
                    )
                    if not compatible:
                        self.errors.append(
                            f"[Line {line}] Argument {i+1} of "
                            f"'{func_name}': expected '{param_type}' "
                            f"but got '{arg_type}'."
                        )

        return sym.return_type


    def validate_no_return(self, func_name, return_type, line):
        """
        Warn if function has return type but no return statement.
        """
        if return_type and return_type != "Nothing":
            self.warnings.append(
                f"[Line {line}] Function '{func_name}' declares "
                f"return type '{return_type}' but may not return a value."
            )


    # ==========================================
    # HELPERS
    # ==========================================

    def _valid_name(self, name, line):
        if not name:
            self.errors.append(
                f"[Line {line}] Function name cannot be empty."
            )
            return False
        if not (name[0].isalpha() or name[0] == '_'):
            self.errors.append(
                f"[Line {line}] Function name '{name}' must start "
                f"with a letter or underscore."
            )
            return False
        if name.startswith('__'):
            self.errors.append(
                f"[Line {line}] Function name '{name}' cannot start "
                f"with '__'. Reserved for compiler use."
            )
            return False
        return True

    def _valid_type(self, type_name, line):
        if type_name not in VALID_TYPES:
            self.errors.append(
                f"[Line {line}] Unknown type '{type_name}'. "
                f"Valid types: Whole, Text, Decimal, Truth, Task, ..."
            )
            return False
        return True

    def _validate_params(self, params, line):
        valid      = True
        seen_names = set()
        for param in params:
            # Duplicate param name
            if param.name in seen_names:
                self.errors.append(
                    f"[Line {line}] Duplicate parameter "
                    f"name '{param.name}'."
                )
                valid = False
            else:
                seen_names.add(param.name)
            # Invalid param type
            if param.param_type not in VALID_TYPES:
                self.errors.append(
                    f"[Line {line}] Unknown parameter type "
                    f"'{param.param_type}' for '{param.name}'."
                )
                valid = False
        return valid

    def _types_compatible(self, from_type, to_type):
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
