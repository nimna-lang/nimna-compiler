# ============================================
# NIMNA Language — Token Types
# File: src/lexer/token_types.py
# Compiler: nimac
# ============================================

class TokenType:

    # ─────────────────────────────
    # LITERALS — Actual values
    # ─────────────────────────────
    INTEGER     = "INTEGER"      # 42, 100, 999
    DECIMAL     = "DECIMAL"      # 3.14, 2.71
    TEXT        = "TEXT"         # "Hello World"
    LETTER      = "LETTER"       # 'A', 'z'
    TRUTH_TRUE  = "TRUTH_TRUE"   # true
    TRUTH_FALSE = "TRUTH_FALSE"  # false
    NOTHING     = "NOTHING"      # nothing (null)

    # ─────────────────────────────
    # IDENTIFIERS & KEYWORDS
    # ─────────────────────────────
    IDENTIFIER  = "IDENTIFIER"   # variable names, function names
    KEYWORD     = "KEYWORD"      # let, fn, if, while ...

    # ─────────────────────────────
    # DATA TYPES
    # ─────────────────────────────
    TYPE_TINY       = "TYPE_TINY"       # Tiny
    TYPE_SHORT      = "TYPE_SHORT"      # Short
    TYPE_WHOLE      = "TYPE_WHOLE"      # Whole
    TYPE_LONG       = "TYPE_LONG"       # Long
    TYPE_HUGE       = "TYPE_HUGE"       # Huge
    TYPE_DECIMAL    = "TYPE_DECIMAL"    # Decimal
    TYPE_PRECISE    = "TYPE_PRECISE"    # Precise
    TYPE_EXACT      = "TYPE_EXACT"      # Exact
    TYPE_TEXT       = "TYPE_TEXT"       # Text
    TYPE_LETTER     = "TYPE_LETTER"     # Letter
    TYPE_SYMBOL     = "TYPE_SYMBOL"     # Symbol
    TYPE_TRUTH      = "TYPE_TRUTH"      # Truth
    TYPE_BIT        = "TYPE_BIT"        # Bit
    TYPE_SEQUENCE   = "TYPE_SEQUENCE"   # Sequence
    TYPE_COLLECTION = "TYPE_COLLECTION" # Collection
    TYPE_MAPPING    = "TYPE_MAPPING"    # Mapping
    TYPE_UNIQUE     = "TYPE_UNIQUE"     # Unique
    TYPE_BUNDLE     = "TYPE_BUNDLE"     # Bundle
    TYPE_MAYBE      = "TYPE_MAYBE"      # Maybe
    TYPE_OUTCOME    = "TYPE_OUTCOME"    # Outcome
    TYPE_TASK       = "TYPE_TASK"       # Task
    TYPE_FLOW       = "TYPE_FLOW"       # Flow
    TYPE_ACTION     = "TYPE_ACTION"     # Action
    TYPE_WILD       = "TYPE_WILD"       # Wild
    TYPE_NOTHING    = "TYPE_NOTHING"    # Nothing

    # ─────────────────────────────
    # ARITHMETIC OPERATORS
    # ─────────────────────────────
    PLUS        = "PLUS"         # +
    MINUS       = "MINUS"        # -
    MULTIPLY    = "MULTIPLY"     # *
    DIVIDE      = "DIVIDE"       # /
    REMAINDER   = "REMAINDER"    # %
    POWER       = "POWER"        # **

    # ─────────────────────────────
    # COMPARISON OPERATORS
    # ─────────────────────────────
    EQUAL       = "EQUAL"        # ==
    NOT_EQUAL   = "NOT_EQUAL"    # !=
    GREATER     = "GREATER"      # >
    LESS        = "LESS"         # <
    GREATER_EQ  = "GREATER_EQ"   # >=
    LESS_EQ     = "LESS_EQ"      # <=

    # ─────────────────────────────
    # LOGICAL OPERATORS
    # ─────────────────────────────
    AND         = "AND"          # &&
    OR          = "OR"           # ||
    NOT         = "NOT"          # !!

    # ─────────────────────────────
    # ASSIGNMENT OPERATORS
    # ─────────────────────────────
    ASSIGN          = "ASSIGN"         # =
    PLUS_ASSIGN     = "PLUS_ASSIGN"    # +=
    MINUS_ASSIGN    = "MINUS_ASSIGN"   # -=
    MULTIPLY_ASSIGN = "MULTIPLY_ASSIGN"# *=
    DIVIDE_ASSIGN   = "DIVIDE_ASSIGN"  # /=
    REMAIN_ASSIGN   = "REMAIN_ASSIGN"  # %=
    POWER_ASSIGN    = "POWER_ASSIGN"   # **=

    # ─────────────────────────────
    # BITWISE OPERATORS
    # ─────────────────────────────
    BIT_AND     = "BIT_AND"      # &
    BIT_OR      = "BIT_OR"       # |
    BIT_XOR     = "BIT_XOR"      # ^
    BIT_NOT     = "BIT_NOT"      # ~
    LEFT_SHIFT  = "LEFT_SHIFT"   # <<
    RIGHT_SHIFT = "RIGHT_SHIFT"  # >>

    # ─────────────────────────────
    # RANGE OPERATORS
    # ─────────────────────────────
    RANGE_EX    = "RANGE_EX"     # .. (exclusive)
    RANGE_IN    = "RANGE_IN"     # ..= (inclusive)
    RANGE_INF   = "RANGE_INF"    # ... (infinite)

    # ─────────────────────────────
    # PIPELINE OPERATORS
    # ─────────────────────────────
    PIPE_FORWARD  = "PIPE_FORWARD"   # |>
    PIPE_BACKWARD = "PIPE_BACKWARD"  # <|
    COMPOSE       = "COMPOSE"        # >>

    # ─────────────────────────────
    # NULL SAFETY OPERATORS
    # ─────────────────────────────
    NULL_DEFAULT  = "NULL_DEFAULT"   # ??
    SAFE_ACCESS   = "SAFE_ACCESS"    # ?.
    FORCE_UNWRAP  = "FORCE_UNWRAP"   # ?!
    NULL_TERNARY  = "NULL_TERNARY"   # ?:

    # ─────────────────────────────
    # PATTERN MATCHING OPERATORS
    # ─────────────────────────────
    MATCH_ARM     = "MATCH_ARM"      # =>
    BIND          = "BIND"           # @
    PATTERN_EQ    = "PATTERN_EQ"     # ~=
    WILDCARD      = "WILDCARD"       # _

    # ─────────────────────────────
    # TYPE OPERATORS
    # ─────────────────────────────
    TYPE_CAST     = "TYPE_CAST"      # as
    TYPE_CHECK    = "TYPE_CHECK"     # is
    INSTANCE_OF   = "INSTANCE_OF"    # of

    # ─────────────────────────────
    # DELIMITERS
    # ─────────────────────────────
    LPAREN        = "LPAREN"         # (
    RPAREN        = "RPAREN"         # )
    LBRACE        = "LBRACE"         # {
    RBRACE        = "RBRACE"         # }
    LBRACKET      = "LBRACKET"       # [
    RBRACKET      = "RBRACKET"       # ]

    # ─────────────────────────────
    # PUNCTUATION
    # ─────────────────────────────
    COMMA         = "COMMA"          # ,
    COLON         = "COLON"          # :
    SEMICOLON     = "SEMICOLON"      # ;
    DOT           = "DOT"            # .
    ARROW         = "ARROW"          # ->
    DOUBLE_COLON  = "DOUBLE_COLON"   # ::
    HASH          = "HASH"           # #

    # ─────────────────────────────
    # SPECIAL
    # ─────────────────────────────
    NEWLINE       = "NEWLINE"        # \n
    EOF           = "EOF"            # End of file
    UNKNOWN       = "UNKNOWN"        # Unknown character


# ============================================
# NIMNA Data Types — Quick Reference
# ============================================

NIMNA_TYPES = {
    "Tiny", "Short", "Whole", "Long", "Huge",
    "Decimal", "Precise", "Exact",
    "Text", "Letter", "Symbol",
    "Truth", "Bit",
    "Sequence", "Collection", "Mapping", "Unique", "Bundle",
    "Maybe", "Outcome", "Task", "Flow", "Action", "Wild", "Nothing"
}


# ============================================
# NIMNA Keywords — All 80
# ============================================

NIMNA_KEYWORDS = {
    # Control Flow
    "if", "else", "elif", "match", "when",
    "case", "default", "for", "while", "loop",
    "repeat", "until", "break", "skip",

    # Function System
    "fn", "give", "lambda", "produce",
    "async", "await", "defer", "inline",

    # Memory Safety
    "own", "borrow", "shared", "freeze", "release",
    "guard", "shield", "managed", "raw", "fence",

    # Type System
    "kind", "record", "variant", "blueprint",
    "contract", "build", "grow", "shape", "narrow",

    # Module System
    "module", "bring", "expose", "from",
    "using", "space", "bundle",

    # Error Handling
    "attempt", "rescue", "raise", "always",
    "fault", "recover", "expect",

    # Object Oriented
    "object", "forge", "this", "parent",
    "fixed", "redefine", "extend", "hidden",

    # Functional Programming
    "transform", "sieve", "fold", "chain",
    "compose", "partial", "memoize",

    # Concurrency
    "launch", "tunnel", "push", "pull",
    "barrier", "atomic",

    # Declaration & Scope
    "let", "constant", "open", "internal"
}
