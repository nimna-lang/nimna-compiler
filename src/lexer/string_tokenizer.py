# ============================================
# NIMNA Language — Text (String) Tokenizer
# File: src/lexer/string_tokenizer.py
# Compiler: nimac
# ============================================

from token_types import TokenType
from token import Token


# ============================================
# ESCAPE SEQUENCES MAP
# ============================================

ESCAPE_SEQUENCES = {
    'n'  : '\n',    # New line
    't'  : '\t',    # Tab
    'r'  : '\r',    # Carriage return
    '\\' : '\\',    # Backslash
    '"'  : '"',     # Double quote
    "'"  : "'",     # Single quote
    '0'  : '\0',    # Null character
    '{'  : '{',     # Literal open brace
    '}'  : '}',     # Literal close brace
    'a'  : '\a',    # Bell
    'b'  : '\b',    # Backspace
    'f'  : '\f',    # Form feed
    'v'  : '\v',    # Vertical tab
}


# ============================================
# TEXT TOKENIZER CLASS
# ============================================

class TextTokenizer:
    """
    NIMNA Text (String) Tokenizer

    Handles:
    - Double quoted strings  : "Hello NIMNA"
    - Multiline strings      : `Hello NIMNA`
    - Escape sequences       : \n \t \\ \" ...
    - String interpolation   : "Hello {name}!"
    - Letter literals        : 'A'
    """

    def __init__(self, source, pos, line, column, filename="<nimna>"):
        self.source   = source
        self.pos      = pos
        self.line     = line
        self.column   = column
        self.filename = filename


    def current_char(self):
        """Return current character or None if end of source."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None


    def advance(self):
        """Move forward one character and return it."""
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        return char


    # ============================================
    # DOUBLE QUOTED STRING
    # ============================================

    def read_double_quoted(self):
        """
        Read a double-quoted Text literal.
        Handles escape sequences and string interpolation.

        Example:
            "Hello {name}!\nWelcome to NIMNA"
        """

        start_line   = self.line
        start_column = self.column
        self.advance()  # skip opening "

        text         = ""
        parts        = []    # For interpolation parts
        current_part = ""

        while self.current_char() and self.current_char() != '"':

            char = self.current_char()

            # Handle escape sequences
            if char == '\\':
                self.advance()  # skip backslash
                next_char = self.current_char()

                if next_char in ESCAPE_SEQUENCES:
                    current_part += ESCAPE_SEQUENCES[next_char]
                    self.advance()
                else:
                    # Unknown escape — keep as is
                    current_part += '\\' + (next_char or '')
                    if next_char:
                        self.advance()

            # Handle string interpolation {variable}
            elif char == '{':
                self.advance()  # skip {
                interp_expr = ""

                while self.current_char() and self.current_char() != '}':
                    interp_expr += self.advance()

                if self.current_char() == '}':
                    self.advance()  # skip }

                # Save text before interpolation
                if current_part:
                    parts.append(("text", current_part))
                    current_part = ""

                # Save interpolation expression
                parts.append(("interp", interp_expr.strip()))

            # Unclosed string check
            elif char == '\n':
                return self._make_error_token(
                    "Unclosed string literal. Missing closing '\"'.",
                    start_line,
                    start_column
                )

            else:
                current_part += self.advance()

        # Add remaining text
        if current_part:
            parts.append(("text", current_part))

        # Skip closing "
        if self.current_char() == '"':
            self.advance()

        # Build final text value
        final_text = ""
        for part_type, part_value in parts:
            if part_type == "text":
                final_text += part_value
            elif part_type == "interp":
                final_text += "{" + part_value + "}"

        return Token(
            TokenType.TEXT,
            final_text,
            start_line,
            start_column,
            self.filename
        ), self.pos, self.line, self.column


    # ============================================
    # MULTILINE STRING (Backtick)
    # ============================================

    def read_multiline(self):
        """
        Read a backtick multiline Text literal.

        Example:
            `Hello
             World
             NIMNA`
        """

        start_line   = self.line
        start_column = self.column
        self.advance()  # skip opening backtick

        text = ""

        while self.current_char() and self.current_char() != '`':
            text += self.advance()

        # Skip closing backtick
        if self.current_char() == '`':
            self.advance()

        # Clean up leading/trailing whitespace from each line
        lines       = text.split('\n')
        clean_lines = [line.strip() for line in lines]
        final_text  = '\n'.join(clean_lines).strip()

        return Token(
            TokenType.TEXT,
            final_text,
            start_line,
            start_column,
            self.filename
        ), self.pos, self.line, self.column


    # ============================================
    # LETTER LITERAL (Single Character)
    # ============================================

    def read_letter(self):
        """
        Read a single Letter literal.

        Example:
            'A'  'z'  '5'  '\n'
        """

        start_line   = self.line
        start_column = self.column
        self.advance()  # skip opening '

        char = ""

        # Handle escape in letter
        if self.current_char() == '\\':
            self.advance()  # skip backslash
            next_char = self.current_char()
            if next_char in ESCAPE_SEQUENCES:
                char = ESCAPE_SEQUENCES[next_char]
                self.advance()
            else:
                char = next_char or ''
                if next_char:
                    self.advance()
        elif self.current_char() and self.current_char() != "'":
            char = self.advance()

        # Closing quote
        if self.current_char() == "'":
            self.advance()

        return Token(
            TokenType.LETTER,
            char,
            start_line,
            start_column,
            self.filename
        ), self.pos, self.line, self.column


    # ============================================
    # HELPER
    # ============================================

    def _make_error_token(self, message, line, column):
        """Create an error token."""
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

def process_escape_sequences(raw_text):
    """
    Process escape sequences in a raw string.
    Returns the processed string.
    """
    result = ""
    i      = 0

    while i < len(raw_text):
        if raw_text[i] == '\\' and i + 1 < len(raw_text):
            next_char = raw_text[i + 1]
            if next_char in ESCAPE_SEQUENCES:
                result += ESCAPE_SEQUENCES[next_char]
                i      += 2
            else:
                result += raw_text[i]
                i      += 1
        else:
            result += raw_text[i]
            i      += 1

    return result


def extract_interpolations(text):
    """
    Extract interpolation expressions from a Text literal.

    Example:
        "Hello {name}, you are {age} years old."
        Returns: ["name", "age"]
    """
    expressions = []
    i           = 0

    while i < len(text):
        if text[i] == '{':
            j    = i + 1
            expr = ""
            while j < len(text) and text[j] != '}':
                expr += text[j]
                j    += 1
            if expr.strip():
                expressions.append(expr.strip())
            i = j + 1
        else:
            i += 1

    return expressions


def is_valid_text(raw_text):
    """
    Check if a raw text literal is valid.
    Returns (bool, error_message)
    """
    # Check for unclosed interpolation
    open_count  = raw_text.count('{')
    close_count = raw_text.count('}')

    if open_count != close_count:
        return False, "Unclosed interpolation brace '{' in Text literal."

    return True, ""
