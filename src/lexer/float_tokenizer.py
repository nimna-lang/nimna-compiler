# ============================================
# NIMNA Language — Decimal Number Tokenizer
# File: src/lexer/float_tokenizer.py
# Compiler: nimac
# ============================================

from token_types import TokenType
from token import Token
import math


# ============================================
# NIMNA DECIMAL NUMBER TYPE INFO
# ============================================

DECIMAL_TYPE_INFO = {

    "Decimal" : {
        "bits"      : 32,
        "max_abs"   : 3.4028235e+38,
        "min_abs"   : 1.175494e-38,
        "precision" : 7,
        "desc"      : "32-bit decimal number (single precision)"
    },

    "Precise" : {
        "bits"      : 64,
        "max_abs"   : 1.7976931348623157e+308,
        "min_abs"   : 2.2250738585072014e-308,
        "precision" : 15,
        "desc"      : "64-bit decimal number (double precision)"
    },

    "Exact"   : {
        "bits"      : 128,
        "max_abs"   : None,
        "min_abs"   : None,
        "precision" : None,
        "desc"      : "128-bit decimal number (maximum precision)"
    },

}


# ============================================
# DECIMAL NUMBER TOKENIZER CLASS
# ============================================

class DecimalTokenizer:
    """
    NIMNA Decimal Number Tokenizer

    Reads, validates and tokenizes decimal numbers
    according to NIMNA type precision and range.
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename


    def tokenize_decimal(self, raw_number, declared_type, line, column):
        """
        Tokenize a decimal number.

        Parameters:
            raw_number    : str — Raw number string from source code
            declared_type : str — Type declared by the developer
            line          : int — Line number in source file
            column        : int — Column number in source file

        Returns:
            Token — Valid token or error token
        """

        # Step 1: Clean the raw number
        clean_number = raw_number.replace('_', '')

        # Step 2: Convert to float
        try:
            value = float(clean_number)
        except ValueError:
            return self._make_error_token(
                f"'{raw_number}' is not a valid decimal number.",
                line,
                column
            )

        # Step 3: Check for special float values
        if math.isnan(value):
            return self._make_error_token(
                f"'{raw_number}' produces NaN (Not a Number). Not allowed in NIMNA.",
                line,
                column
            )

        if math.isinf(value):
            return self._make_error_token(
                f"'{raw_number}' produces Infinity. Value is out of range.",
                line,
                column
            )

        # Step 4: Validate against declared type
        if declared_type and declared_type in DECIMAL_TYPE_INFO:
            valid, error_msg = self._validate_for_type(value, declared_type)
            if not valid:
                return self._make_error_token(error_msg, line, column)

        # Step 5: Return valid decimal token
        return Token(
            TokenType.DECIMAL,
            value,
            line,
            column,
            self.filename
        )


    def validate_assignment(self, value, declared_type):
        """
        Check if a decimal value fits within declared type range.

        Returns:
            (bool, str) — (is valid, error message)
        """

        if declared_type not in DECIMAL_TYPE_INFO:
            return True, ""

        return self._validate_for_type(value, declared_type)


    def _validate_for_type(self, value, type_name):
        """
        Validate a float value against a specific NIMNA decimal type.
        """

        info = DECIMAL_TYPE_INFO[type_name]

        # Exact type has no limit
        if type_name == "Exact":
            return True, ""

        abs_value = abs(value)
        max_abs   = info["max_abs"]

        if abs_value > max_abs:
            return False, (
                f"Type Error: Value '{value}' is out of range "
                f"for type '{type_name}'.\n"
                f"  '{type_name}' max absolute value : {max_abs}\n"
                f"  Your value                       : {value}\n"
                f"  Suggestion: Use 'Precise' or 'Exact' instead."
            )

        return True, ""


    def _auto_detect_type(self, value):
        """
        Automatically detect the best fitting decimal type for a value.
        """

        abs_value = abs(value)

        if abs_value <= DECIMAL_TYPE_INFO["Decimal"]["max_abs"]:
            return "Decimal"
        elif abs_value <= DECIMAL_TYPE_INFO["Precise"]["max_abs"]:
            return "Precise"
        else:
            return "Exact"


    def get_significant_digits(self, value):
        """
        Count significant digits in a decimal number.
        """
        str_val = str(value).replace('-', '').replace('.', '')
        str_val = str_val.lstrip('0')
        return len(str_val)


    def get_type_info(self, type_name):
        """
        Return information about a given decimal type.
        """
        if type_name in DECIMAL_TYPE_INFO:
            info = DECIMAL_TYPE_INFO[type_name]
            max_val = info["max_abs"] if info["max_abs"] else "Unlimited"
            prec    = info["precision"] if info["precision"] else "Unlimited"
            return (
                f"Type      : {type_name}\n"
                f"Bits      : {info['bits']}\n"
                f"Max Value : {max_val}\n"
                f"Precision : {prec} significant digits\n"
                f"Desc      : {info['desc']}"
            )
        return f"Type '{type_name}' does not exist in NIMNA."


    def _make_error_token(self, message, line, column):
        """
        Create an error token for an invalid decimal number.
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

def get_decimal_type_for_value(value):
    """
    Return the smallest suitable decimal type for a given value.
    """
    abs_value = abs(value)

    if abs_value <= DECIMAL_TYPE_INFO["Decimal"]["max_abs"]:
        return "Decimal"
    elif abs_value <= DECIMAL_TYPE_INFO["Precise"]["max_abs"]:
        return "Precise"
    else:
        return "Exact"


def is_valid_decimal_for_type(value, type_name):
    """
    Check if a decimal value is valid for the given type.
    """
    if type_name not in DECIMAL_TYPE_INFO:
        return False

    if type_name == "Exact":
        return True

    info      = DECIMAL_TYPE_INFO[type_name]
    abs_value = abs(value)
    return abs_value <= info["max_abs"]


def get_all_decimal_type_info():
    """
    Print all NIMNA decimal type information.
    """
    print("=== NIMNA Decimal Number Types ===")
    print("")
    for name, info in DECIMAL_TYPE_INFO.items():
        max_val = info["max_abs"] if info["max_abs"] else "Unlimited"
        prec    = info["precision"] if info["precision"] else "Unlimited"
        print(f"  {name:<10} ({info['bits']}-bit)")
        print(f"    Precision : {prec} significant digits")
        print(f"    Max Value : {max_val}")
        print(f"    Desc      : {info['desc']}")
        print("")
