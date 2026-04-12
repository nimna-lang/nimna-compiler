# ============================================
# NIMNA Language — Token Class
# File: src/lexer/token.py
# Compiler: nimac
# ============================================

from token_types import TokenType


class Token:
    """
    NIMNA Token — Har ek token ki poori information
    
    Attributes:
        token_type  : TokenType — Token ki category
        value       : any      — Token ki actual value
        line        : int      — Kis line pe hai
        column      : int      — Kis column pe hai
        source_file : str      — Kis file se aaya
    """

    def __init__(self, token_type, value, line, column, source_file="<nimna>"):
        self.token_type  = token_type
        self.value       = value
        self.line        = line
        self.column      = column
        self.source_file = source_file

    def is_keyword(self):
        """Check karo yeh token keyword hai ya nahi"""
        return self.token_type == TokenType.KEYWORD

    def is_identifier(self):
        """Check karo yeh token identifier hai ya nahi"""
        return self.token_type == TokenType.IDENTIFIER

    def is_type(self):
        """Check karo yeh token data type hai ya nahi"""
        return self.token_type.startswith("TYPE_")

    def is_literal(self):
        """Check karo yeh token literal value hai ya nahi"""
        return self.token_type in (
            TokenType.INTEGER,
            TokenType.DECIMAL,
            TokenType.TEXT,
            TokenType.LETTER,
            TokenType.TRUTH_TRUE,
            TokenType.TRUTH_FALSE,
            TokenType.NOTHING
        )

    def is_operator(self):
        """Check karo yeh token operator hai ya nahi"""
        return self.token_type in (
            TokenType.PLUS, TokenType.MINUS,
            TokenType.MULTIPLY, TokenType.DIVIDE,
            TokenType.REMAINDER, TokenType.POWER,
            TokenType.EQUAL, TokenType.NOT_EQUAL,
            TokenType.GREATER, TokenType.LESS,
            TokenType.GREATER_EQ, TokenType.LESS_EQ,
            TokenType.AND, TokenType.OR, TokenType.NOT,
            TokenType.ASSIGN, TokenType.PLUS_ASSIGN,
            TokenType.MINUS_ASSIGN, TokenType.MULTIPLY_ASSIGN,
            TokenType.DIVIDE_ASSIGN, TokenType.REMAIN_ASSIGN,
            TokenType.POWER_ASSIGN
        )

    def is_eof(self):
        """Check karo file khatam hua ya nahi"""
        return self.token_type == TokenType.EOF

    def location(self):
        """Token ki location return karo — error messages ke liye"""
        return f"{self.source_file}:{self.line}:{self.column}"

    def __repr__(self):
        """Token ko readable format mein print karo"""
        return (
            f"Token("
            f"type={self.token_type}, "
            f"value={repr(self.value)}, "
            f"line={self.line}, "
            f"col={self.column}"
            f")"
        )

    def __eq__(self, other):
        """Do tokens ko compare karo"""
        if not isinstance(other, Token):
            return False
        return (
            self.token_type == other.token_type and
            self.value      == other.value
        )

    def __str__(self):
        """Token ko simple string mein dikhao"""
        return f"[{self.token_type}:{repr(self.value)}] at {self.location()}"
