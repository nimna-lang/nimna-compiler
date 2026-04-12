# ============================================
# NIMNA Language — Whole Number Tokenizer
# File: src/lexer/number_tokenizer.py
# Compiler: nimac
# ============================================

from token_types import TokenType
from token import Token


# ============================================
# NIMNA WHOLE NUMBER RANGES
# ============================================

WHOLE_NUMBER_RANGES = {

    "Tiny"  : {
        "min"  : -128,
        "max"  : 127,
        "bits" : 8,
        "desc" : "8-bit whole number"
    },

    "Short" : {
        "min"  : -32_768,
        "max"  : 32_767,
        "bits" : 16,
        "desc" : "16-bit whole number"
    },

    "Whole" : {
        "min"  : -2_147_483_648,
        "max"  : 2_147_483_647,
        "bits" : 32,
        "desc" : "32-bit whole number"
    },

    "Long"  : {
        "min"  : -9_223_372_036_854_775_808,
        "max"  : 9_223_372_036_854_775_807,
        "bits" : 64,
        "desc" : "64-bit whole number"
    },

    "Huge"  : {
        "min"  : -170_141_183_460_469_231_731_687_303_715_884_105_728,
        "max"  : 170_141_183_460_469_231_731_687_303_715_884_105_727,
        "bits" : 128,
        "desc" : "128-bit whole number"
    },

}


# ============================================
# WHOLE NUMBER TOKENIZER CLASS
# ============================================

class WholeNumberTokenizer:
    """
    NIMNA Whole Number Tokenizer

    Reads, validates and tokenizes whole numbers
    according to NIMNA type ranges.
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename


    def tokenize_number(self, raw_number, declared_type, line, column):
        """
        Tokenize a whole number.

        Parameters:
            raw_number    : str  — Raw number string from source code
            declared_type : str  — Type declared by the developer
            line          : int  — Line number in source file
            column        : int  — Column number in source file

        Returns:
            Token — Valid token or error token
        """

        # Step 1: Convert string to integer
        try:
            value = int(raw_number.replace('_', ''))
        except ValueError:
            return self._make_error_token(
                f"'{raw_number}' is not a valid whole number.",
                line,
                column
            )

        # Step 2: If type is declared, validate range
        if declared_type and declared_type in WHOLE_NUMBER_RANGES:
            range_info = WHOLE_NUMBER_RANGES[declared_type]
            in_range   = self._check_range(value, range_info)

            if not in_range:
                return self._make_error_token(
                    f"Value {value} is out of range for type '{declared_type}'. "
                    f"({declared_type} range: {range_info['min']} to {range_info['max']})",
                    line,
                    column
                )

            return Token(
                TokenType.INTEGER,
                value,
                line,
                column,
                self.filename
            )

        # Step 3: No type declared — auto detect
        detected_type = self._auto_detect_type(value)

        return Token(
            TokenType.INTEGER,
            value,
            line,
            column,
            self.filename
        )


    def validate_assignment(self, value, declared_type):
        """
        Check if a value fits within the declared type range.

        Returns:
            (bool, str) — (is valid, error message)
        """

        if declared_type not in WHOLE_NUMBER_RANGES:
            return True, ""

        range_info = WHOLE_NUMBER_RANGES[declared_type]
        in_range   = self._check_range(value, range_info)

        if not in_range:
            error_msg = (
                f"Type Error: Value '{value}' cannot be stored in type '{declared_type}'.\n"
                f"  '{declared_type}' range: "
                f"{range_info['min']} to {range_info['max']}\n"
                f"  Your value  : {value}\n"
                f"  Suggestion  : Use '{self._auto_detect_type(value)}' instead."
            )
            return False, error_msg

        return True, ""


    def _check_range(self, value, range_info):
        """
        Check if value is within the given range.
        """
        return range_info["min"] <= value <= range_info["max"]


    def _auto_detect_type(self, value):
        """
        Automatically detect the best fitting type for a value.
        """
        for type_name, range_info in WHOLE_NUMBER_RANGES.items():
            if range_info["min"] <= value <= range_info["max"]:
                return type_name
        return "Huge"


    def get_type_info(self, type_name):
        """
        Return range information for a given type.
        """
        if type_name in WHOLE_NUMBER_RANGES:
            info = WHOLE_NUMBER_RANGES[type_name]
            return (
                f"Type    : {type_name}\n"
                f"Bits    : {info['bits']}\n"
                f"Min     : {info['min']}\n"
                f"Max     : {info['max']}\n"
                f"Desc    : {info['desc']}"
            )
        return f"Type '{type_name}' does not exist in NIMNA."


    def _make_error_token(self, message, line, column):
        """
        Create an error token for an invalid number.
        """
        return Token(
            TokenType.UNKNOWN,
            f"ERROR: {message}",
            line,
            column,
            self.filename
        )


# ============================================
# STANDALONE HELPER FUNCTIONS
# ============================================

def get_whole_type_for_value(value):
    """
    Return the smallest suitable type for a given value.
    """
    for type_name, range_info in WHOLE_NUMBER_RANGES.items():
        if range_info["min"] <= value <= range_info["max"]:
            return type_name
    return "Huge"


def is_valid_for_type(value, type_name):
    """
    Check if a value is valid for the given type.
    """
    if type_name not in WHOLE_NUMBER_RANGES:
        return False
    r = WHOLE_NUMBER_RANGES[type_name]
    return r["min"] <= value <= r["max"]


def get_all_type_ranges():
    """
    Print all NIMNA whole number type ranges.
    """
    print("=== NIMNA Whole Number Types ===")
    print("")
    for name, info in WHOLE_NUMBER_RANGES.items():
        print(f"  {name:<8} ({info['bits']}-bit)")
        print(f"    Min : {info['min']}")
        print(f"    Max : {info['max']}")
        print("")
