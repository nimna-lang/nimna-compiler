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

    Yeh class whole numbers ko padhti hai,
    validate karti hai aur sahi token return
    karti hai.
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename


    def tokenize_number(self, raw_number, declared_type, line, column):
        """
        Ek number ko tokenize karo.

        Parameters:
            raw_number    : str  — Source code se padha hua number
            declared_type : str  — Developer ne kaunsa type declare kiya
            line          : int  — Line number
            column        : int  — Column number

        Returns:
            Token — Sahi token ya error token
        """

        # ── Step 1: String ko integer mein convert karo
        try:
            value = int(raw_number.replace('_', ''))
        except ValueError:
            return self._make_error_token(
                f"'{raw_number}' valid whole number nahi hai.",
                line,
                column
            )

        # ── Step 2: Type declared hai toh range check karo
        if declared_type and declared_type in WHOLE_NUMBER_RANGES:
            range_info = WHOLE_NUMBER_RANGES[declared_type]
            in_range   = self._check_range(value, range_info)

            if not in_range:
                return self._make_error_token(
                    f"Value {value} type '{declared_type}' ki range se bahar hai. "
                    f"({declared_type} range: {range_info['min']} to {range_info['max']})",
                    line,
                    column
                )

            # Sahi token return karo
            return Token(
                TokenType.INTEGER,
                value,
                line,
                column,
                self.filename
            )

        # ── Step 3: Type declare nahi kiya — auto detect karo
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
        Check karo ki value declared type mein fit hoti hai ya nahi.

        Returns:
            (bool, str) — (valid hai ya nahi, error message)
        """

        if declared_type not in WHOLE_NUMBER_RANGES:
            return True, ""

        range_info = WHOLE_NUMBER_RANGES[declared_type]
        in_range   = self._check_range(value, range_info)

        if not in_range:
            error_msg = (
                f"Type Error: Value '{value}' type '{declared_type}' "
                f"mein store nahi ho sakta.\n"
                f"  '{declared_type}' range: "
                f"{range_info['min']} to {range_info['max']}\n"
                f"  Tumhara value: {value}\n"
                f"  Suggestion: '{self._auto_detect_type(value)}' use karo."
            )
            return False, error_msg

        return True, ""


    def _check_range(self, value, range_info):
        """
        Check karo value range ke andar hai ya nahi.
        """
        return range_info["min"] <= value <= range_info["max"]


    def _auto_detect_type(self, value):
        """
        Value ke hisaab se automatically sahi type detect karo.
        """
        for type_name, range_info in WHOLE_NUMBER_RANGES.items():
            if range_info["min"] <= value <= range_info["max"]:
                return type_name
        return "Huge"


    def get_type_info(self, type_name):
        """
        Kisi type ki range information return karo.
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
        return f"Type '{type_name}' NIMNA mein exist nahi karta."


    def _make_error_token(self, message, line, column):
        """
        Error token banao — invalid number ke liye.
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
    Kisi value ke liye sabse chhota suitable type return karo.
    """
    for type_name, range_info in WHOLE_NUMBER_RANGES.items():
        if range_info["min"] <= value <= range_info["max"]:
            return type_name
    return "Huge"


def is_valid_for_type(value, type_name):
    """
    Check karo value us type ke liye valid hai ya nahi.
    """
    if type_name not in WHOLE_NUMBER_RANGES:
        return False
    r = WHOLE_NUMBER_RANGES[type_name]
    return r["min"] <= value <= r["max"]


def get_all_type_ranges():
    """
    Sabhi types ki ranges print karo.
    """
    print("=== NIMNA Whole Number Types ===")
    print("")
    for name, info in WHOLE_NUMBER_RANGES.items():
        print(f"  {name:<8} ({info['bits']}-bit)")
        print(f"    Min : {info['min']}")
        print(f"    Max : {info['max']}")
        print("")
