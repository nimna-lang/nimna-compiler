# ============================================
# NIMNA Language — Main Lexer
# File: src/lexer/lexer.py
# Compiler: nimac
# ============================================

from token_types import TokenType
from token import Token
from keywords import (
    KEYWORDS,
    TYPE_KEYWORDS,
    is_keyword,
    is_type_keyword,
    get_token_type
)


class NIMNALexer:
    """
    NIMNA Main Lexer Class

    Yeh class source code ko read karke
    tokens ki list produce karti hai.

    Usage:
        lexer  = NIMNALexer(source_code, filename)
        tokens = lexer.tokenize()
    """

    def __init__(self, source_code, filename="<nimna>"):
        self.source    = source_code   # Poora source code
        self.filename  = filename      # File ka naam
        self.pos       = 0             # Current position
        self.line      = 1             # Current line number
        self.column    = 1             # Current column number
        self.tokens    = []            # Tokens ki list


    # ============================================
    # CORE READING METHODS
    # ============================================

    def current_char(self):
        """
        Current character return karo.
        Agar file khatam ho gayi toh None return karo.
        """
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None


    def peek_char(self, offset=1):
        """
        Agle character ko dekho — bina aage badhe.
        Yeh operators check karne ke liye zaroori hai.
        Jaise: '=' ke baad '=' hai toh '==' hai.
        """
        peek_pos = self.pos + offset
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None


    def advance(self):
        """
        Ek character aage badho aur use return karo.
        Line aur column number update karo.
        """
        char = self.source[self.pos]
        self.pos    += 1

        if char == '\n':
            self.line   += 1
            self.column  = 1
        else:
            self.column += 1

        return char


    def skip_whitespace(self):
        """
        Spaces, tabs aur carriage returns skip karo.
        Newline skip nahi karte — woh ek token hai.
        """
        while self.current_char() in (' ', '\t', '\r'):
            self.advance()


    def skip_single_comment(self):
        """
        Single line comment skip karo — // se shuru hota hai
        """
        while self.current_char() and self.current_char() != '\n':
            self.advance()


    def skip_multi_comment(self):
        """
        Multi line comment skip karo — /* se shuru, */ pe khatam
        """
        self.advance()  # skip *
        while self.current_char():
            if self.current_char() == '*' and self.peek_char() == '/':
                self.advance()  # skip *
                self.advance()  # skip /
                break
            self.advance()


    def make_token(self, token_type, value):
        """
        Naya token banao current line aur column ke saath
        """
        return Token(token_type, value, self.line, self.column, self.filename)


    # ============================================
    # NUMBER READERS
    # ============================================

    def read_number(self):
        """
        Number padhो — Whole ya Decimal.
        Jaise: 42, 3.14, 1000
        """
        start_col = self.column
        number    = ""
        is_float  = False

        while self.current_char() and (
            self.current_char().isdigit() or
            self.current_char() == '_'    or   # 1_000_000 style allowed
            self.current_char() == '.'
        ):
            if self.current_char() == '.':
                # Dekho agle char bhi digit hai — toh decimal
                if self.peek_char() and self.peek_char().isdigit():
                    is_float = True
                    number  += self.advance()
                else:
                    break
            elif self.current_char() == '_':
                self.advance()  # underscore skip karo — sirf readability ke liye
            else:
                number += self.advance()

        if is_float:
            return Token(
                TokenType.DECIMAL,
                float(number),
                self.line,
                start_col,
                self.filename
            )
        else:
            return Token(
                TokenType.INTEGER,
                int(number),
                self.line,
                start_col,
                self.filename
            )


    # ============================================
    # TEXT READERS
    # ============================================

    def read_text(self):
        """
        Text literal padhо — double quotes ke beech
        Jaise: "Hello NIMNA"
        Escape sequences bhi handle karta hai: \n \t \\
        """
        start_col = self.column
        self.advance()  # opening " skip karo
        text      = ""

        while self.current_char() and self.current_char() != '"':
            if self.current_char() == '\\':
                self.advance()  # backslash skip karo
                escape = self.current_char()
                if escape == 'n':
                    text += '\n'
                elif escape == 't':
                    text += '\t'
                elif escape == '\\':
                    text += '\\'
                elif escape == '"':
                    text += '"'
                elif escape == 'r':
                    text += '\r'
                else:
                    text += escape
                self.advance()
            else:
                text += self.advance()

        if self.current_char() == '"':
            self.advance()  # closing " skip karo

        return Token(
            TokenType.TEXT,
            text,
            self.line,
            start_col,
            self.filename
        )


    def read_letter(self):
        """
        Letter literal padhо — single quotes ke beech
        Jaise: 'A', 'z', '5'
        """
        start_col = self.column
        self.advance()  # opening ' skip karo
        char      = ""

        if self.current_char() and self.current_char() != "'":
            char = self.advance()

        if self.current_char() == "'":
            self.advance()  # closing ' skip karo

        return Token(
            TokenType.LETTER,
            char,
            self.line,
            start_col,
            self.filename
        )


    def read_multiline_text(self):
        """
        Multi-line text padhо — backticks ke beech
        Jaise: `Hello
                World`
        """
        start_col = self.column
        self.advance()  # opening backtick skip karo
        text      = ""

        while self.current_char() and self.current_char() != '`':
            text += self.advance()

        if self.current_char() == '`':
            self.advance()  # closing backtick skip karo

        return Token(
            TokenType.TEXT,
            text,
            self.line,
            start_col,
            self.filename
        )


    # ============================================
    # IDENTIFIER & KEYWORD READER
    # ============================================

    def read_identifier_or_keyword(self):
        """
        Word padhо aur decide karo:
        → Keyword hai (let, fn, if...)
        → Data Type hai (Whole, Text...)
        → Identifier hai (variable naam)
        → Boolean hai (true, false)
        → Nothing hai
        """
        start_col = self.column
        word      = ""

        while self.current_char() and (
            self.current_char().isalnum() or
            self.current_char() == '_'
        ):
            word += self.advance()

        # Boolean check
        if word == "true":
            return Token(TokenType.TRUTH_TRUE, True, self.line, start_col, self.filename)
        if word == "false":
            return Token(TokenType.TRUTH_FALSE, False, self.line, start_col, self.filename)
        if word == "nothing":
            return Token(TokenType.NOTHING, None, self.line, start_col, self.filename)

        # Keyword check
        if is_keyword(word):
            return Token(TokenType.KEYWORD, word, self.line, start_col, self.filename)

        # Data Type check
        if is_type_keyword(word):
            type_token = get_token_type(word)
            return Token(type_token, word, self.line, start_col, self.filename)

        # Identifier
        return Token(TokenType.IDENTIFIER, word, self.line, start_col, self.filename)


    # ============================================
    # MAIN TOKENIZER
    # ============================================

    def tokenize(self):
        """
        Poora source code tokenize karo.
        Tokens ki list return karo.
        """

        while self.pos < len(self.source):

            self.skip_whitespace()

            char = self.current_char()

            if char is None:
                break

            # ── NEWLINE ──────────────────────────
            elif char == '\n':
                self.tokens.append(
                    self.make_token(TokenType.NEWLINE, '\n')
                )
                self.advance()

            # ── NUMBERS ──────────────────────────
            elif char.isdigit():
                self.tokens.append(self.read_number())

            # ── TEXT LITERALS ─────────────────────
            elif char == '"':
                self.tokens.append(self.read_text())

            elif char == "'":
                self.tokens.append(self.read_letter())

            elif char == '`':
                self.tokens.append(self.read_multiline_text())

            # ── IDENTIFIERS / KEYWORDS ────────────
            elif char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier_or_keyword())

            # ── COMMENTS ─────────────────────────
            elif char == '/' and self.peek_char() == '/':
                self.skip_single_comment()

            elif char == '/' and self.peek_char() == '*':
                self.advance()  # skip /
                self.skip_multi_comment()

            # ── OPERATORS ────────────────────────

            elif char == '+':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.PLUS_ASSIGN, '+='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.PLUS, '+'))

            elif char == '-':
                if self.peek_char() == '>':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.ARROW, '->'))
                elif self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.MINUS_ASSIGN, '-='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.MINUS, '-'))

            elif char == '*':
                if self.peek_char() == '*':
                    self.advance()
                    if self.peek_char() == '=':
                        self.advance(); self.advance()
                        self.tokens.append(self.make_token(TokenType.POWER_ASSIGN, '**='))
                    else:
                        self.advance()
                        self.tokens.append(self.make_token(TokenType.POWER, '**'))
                elif self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.MULTIPLY_ASSIGN, '*='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.MULTIPLY, '*'))

            elif char == '/':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.DIVIDE_ASSIGN, '/='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.DIVIDE, '/'))

            elif char == '%':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.REMAIN_ASSIGN, '%='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.REMAINDER, '%'))

            elif char == '=':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.EQUAL, '=='))
                elif self.peek_char() == '>':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.MATCH_ARM, '=>'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.ASSIGN, '='))

            elif char == '!':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.NOT_EQUAL, '!='))
                elif self.peek_char() == '!':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.NOT, '!!'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.UNKNOWN, '!'))

            elif char == '>':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.GREATER_EQ, '>='))
                elif self.peek_char() == '>':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.COMPOSE, '>>'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.GREATER, '>'))

            elif char == '<':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.LESS_EQ, '<='))
                elif self.peek_char() == '<':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.LEFT_SHIFT, '<<'))
                elif self.peek_char() == '|':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.PIPE_BACKWARD, '<|'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.LESS, '<'))

            elif char == '&':
                if self.peek_char() == '&':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.AND, '&&'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.BIT_AND, '&'))

            elif char == '|':
                if self.peek_char() == '|':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.OR, '||'))
                elif self.peek_char() == '>':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.PIPE_FORWARD, '|>'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.BIT_OR, '|'))

            elif char == '^':
                self.advance()
                self.tokens.append(self.make_token(TokenType.BIT_XOR, '^'))

            elif char == '~':
                if self.peek_char() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.PATTERN_EQ, '~='))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.BIT_NOT, '~'))

            elif char == '?':
                if self.peek_char() == '?':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.NULL_DEFAULT, '??'))
                elif self.peek_char() == '.':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.SAFE_ACCESS, '?.'))
                elif self.peek_char() == '!':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.FORCE_UNWRAP, '?!'))
                elif self.peek_char() == ':':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.NULL_TERNARY, '?:'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.UNKNOWN, '?'))

            elif char == '.':
                if self.peek_char() == '.' and self.peek_char(2) == '=':
                    self.advance(); self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.RANGE_IN, '..='))
                elif self.peek_char() == '.' and self.peek_char(2) == '.':
                    self.advance(); self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.RANGE_INF, '...'))
                elif self.peek_char() == '.':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.RANGE_EX, '..'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.DOT, '.'))

            elif char == ':':
                if self.peek_char() == ':':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.DOUBLE_COLON, '::'))
                else:
                    self.advance()
                    self.tokens.append(self.make_token(TokenType.COLON, ':'))

            elif char == '@':
                self.advance()
                self.tokens.append(self.make_token(TokenType.BIND, '@'))

            elif char == '_' and (
                not self.peek_char() or
                not self.peek_char().isalnum()
            ):
                self.advance()
                self.tokens.append(self.make_token(TokenType.WILDCARD, '_'))

            # ── DELIMITERS ────────────────────────
            elif char == '(':
                self.advance()
                self.tokens.append(self.make_token(TokenType.LPAREN, '('))

            elif char == ')':
                self.advance()
                self.tokens.append(self.make_token(TokenType.RPAREN, ')'))

            elif char == '{':
                self.advance()
                self.tokens.append(self.make_token(TokenType.LBRACE, '{'))

            elif char == '}':
                self.advance()
                self.tokens.append(self.make_token(TokenType.RBRACE, '}'))

            elif char == '[':
                self.advance()
                self.tokens.append(self.make_token(TokenType.LBRACKET, '['))

            elif char == ']':
                self.advance()
                self.tokens.append(self.make_token(TokenType.RBRACKET, ']'))

            # ── PUNCTUATION ───────────────────────
            elif char == ',':
                self.advance()
                self.tokens.append(self.make_token(TokenType.COMMA, ','))

            elif char == ';':
                self.advance()
                self.tokens.append(self.make_token(TokenType.SEMICOLON, ';'))

            elif char == '#':
                self.advance()
                self.tokens.append(self.make_token(TokenType.HASH, '#'))

            # ── UNKNOWN ───────────────────────────
            else:
                self.tokens.append(
                    self.make_token(TokenType.UNKNOWN, char)
                )
                self.advance()

        # EOF token add karo — file ka end
        self.tokens.append(
            Token(TokenType.EOF, None, self.line, self.column, self.filename)
        )

        return self.tokens
