# ============================================
# NIMNA Language — Identifier Resolver
# File: src/lexer/identifier_resolver.py
# Compiler: nimac
# ============================================

from token_types import TokenType
from token import Token
from keywords import KEYWORDS, TYPE_KEYWORDS


# ============================================
# NAMING RULES FOR NIMNA IDENTIFIERS
# ============================================

# Valid identifier start characters
VALID_START_CHARS = set(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '_'
)

# Valid identifier body characters
VALID_BODY_CHARS = set(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '_'
)

# Reserved words that cannot be used as identifiers
RESERVED_WORDS = set(KEYWORDS.keys()) | set(TYPE_KEYWORDS.keys())

# Boolean literals
BOOLEAN_LITERALS = {
    "true"    : (TokenType.TRUTH_TRUE,  True),
    "false"   : (TokenType.TRUTH_FALSE, False),
}

# Null literal
NULL_LITERAL = "nothing"


# ============================================
# IDENTIFIER RESOLVER CLASS
# ============================================

class IdentifierResolver:
    """
    NIMNA Identifier Resolver

    Resolves a word into its correct token type:
    - Keyword
    - Data Type
    - Boolean Literal
    - Null Literal
    - Valid Identifier
    - Invalid Identifier (with error)
    """

    def __init__(self, filename="<nimna>"):
        self.filename = filename


    def resolve(self, word, line, column):
        """
        Main resolve method.
        Takes a word and returns the correct Token.

        Resolution Order:
        1. Boolean literals (true, false)
        2. Null literal (nothing)
        3. Keywords
        4. Data Types
        5. Valid Identifier
        6. Invalid Identifier (error)
        """

        # Step 1: Boolean literals
        if word in BOOLEAN_LITERALS:
            token_type, value = BOOLEAN_LITERALS[word]
            return Token(token_type, value, line, column, self.filename)

        # Step 2: Null literal
        if word == NULL_LITERAL:
            return Token(TokenType.NOTHING, None, line, column, self.filename)

        # Step 3: Keywords
        if word in KEYWORDS:
            return Token(TokenType.KEYWORD, word, line, column, self.filename)

        # Step 4: Data Types
        if word in TYPE_KEYWORDS:
            type_token = TYPE_KEYWORDS[word]
            return Token(type_token, word, line, column, self.filename)

        # Step 5: Validate identifier
        valid, error_msg = self.validate_identifier(word)

        if not valid:
            return Token(
                TokenType.UNKNOWN,
                f"ERROR: {error_msg}",
                line,
                column,
                self.filename
            )

        # Step 6: Valid identifier
        return Token(TokenType.IDENTIFIER, word, line, column, self.filename)


    def validate_identifier(self, word):
        """
        Validate an identifier against NIMNA naming rules.

        Rules:
        1. Must not be empty
        2. Must start with a letter or underscore
        3. Must contain only letters, digits, underscores
        4. Must not be a reserved word
        5. Must not start with double underscore (reserved for compiler)
        6. Must not be only underscores

        Returns:
            (bool, str) — (is valid, error message)
        """

        # Rule 1: Must not be empty
        if not word:
            return False, "Identifier cannot be empty."

        # Rule 2: Must start with letter or underscore
        if word[0] not in VALID_START_CHARS:
            return False, (
                f"Identifier '{word}' must start with a letter or underscore. "
                f"Got '{word[0]}'."
            )

        # Rule 3: Valid body characters only
        for i, char in enumerate(word[1:], start=1):
            if char not in VALID_BODY_CHARS:
                return False, (
                    f"Identifier '{word}' contains invalid character "
                    f"'{char}' at position {i + 1}."
                )

        # Rule 4: Must not be a reserved word
        if word in RESERVED_WORDS:
            return False, (
                f"'{word}' is a reserved keyword in NIMNA. "
                f"It cannot be used as an identifier."
            )

        # Rule 5: Must not start with double underscore
        if word.startswith('__'):
            return False, (
                f"Identifier '{word}' cannot start with '__'. "
                f"Double underscore prefix is reserved for the NIMNA compiler."
            )

        # Rule 6: Must not be only underscores
        if all(c == '_' for c in word):
            return False, (
                f"Identifier '{word}' cannot consist of only underscores. "
                f"Use '_' alone as a wildcard pattern."
            )

        return True, ""


    def is_keyword(self, word):
        """Check if a word is a NIMNA keyword."""
        return word in KEYWORDS


    def is_type(self, word):
        """Check if a word is a NIMNA data type."""
        return word in TYPE_KEYWORDS


    def is_reserved(self, word):
        """Check if a word is reserved in NIMNA."""
        return word in RESERVED_WORDS


    def is_valid_identifier(self, word):
        """Quick check — is this a valid identifier?"""
        valid, _ = self.validate_identifier(word)
        return valid


    def get_identifier_type(self, word):
        """
        Return what category a word belongs to.
        """
        if word in BOOLEAN_LITERALS:
            return "boolean_literal"
        if word == NULL_LITERAL:
            return "null_literal"
        if word in KEYWORDS:
            return "keyword"
        if word in TYPE_KEYWORDS:
            return "data_type"
        valid, _ = self.validate_identifier(word)
        if valid:
            return "identifier"
        return "invalid"


    def suggest_fix(self, word):
        """
        Suggest a fix for an invalid identifier.
        """
        # Remove invalid characters
        fixed = ""
        for i, char in enumerate(word):
            if i == 0 and char not in VALID_START_CHARS:
                fixed += "_"
            elif char in VALID_BODY_CHARS:
                fixed += char
            else:
                fixed += "_"

        if fixed == word:
            return None

        return fixed
