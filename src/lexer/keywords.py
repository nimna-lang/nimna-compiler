# ============================================
# NIMNA Language — Keywords Dictionary
# File: src/lexer/keywords.py
# Compiler: nimac
# Total Keywords: 80
# ============================================

from token_types import TokenType


# ============================================
# NIMNA KEYWORDS — All 80
# Har keyword ka apna TokenType mapped hai
# ============================================

KEYWORDS = {

    # ─────────────────────────────────────
    # CONTROL FLOW — 14 keywords
    # ─────────────────────────────────────
    "if"      : TokenType.KEYWORD,
    "else"    : TokenType.KEYWORD,
    "elif"    : TokenType.KEYWORD,
    "match"   : TokenType.KEYWORD,
    "when"    : TokenType.KEYWORD,
    "case"    : TokenType.KEYWORD,
    "default" : TokenType.KEYWORD,
    "for"     : TokenType.KEYWORD,
    "while"   : TokenType.KEYWORD,
    "loop"    : TokenType.KEYWORD,
    "repeat"  : TokenType.KEYWORD,
    "until"   : TokenType.KEYWORD,
    "break"   : TokenType.KEYWORD,
    "skip"    : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # FUNCTION SYSTEM — 8 keywords
    # ─────────────────────────────────────
    "fn"      : TokenType.KEYWORD,
    "give"    : TokenType.KEYWORD,
    "lambda"  : TokenType.KEYWORD,
    "produce" : TokenType.KEYWORD,
    "async"   : TokenType.KEYWORD,
    "await"   : TokenType.KEYWORD,
    "defer"   : TokenType.KEYWORD,
    "inline"  : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # MEMORY SAFETY — 10 keywords
    # ─────────────────────────────────────
    "own"     : TokenType.KEYWORD,
    "borrow"  : TokenType.KEYWORD,
    "shared"  : TokenType.KEYWORD,
    "freeze"  : TokenType.KEYWORD,
    "release" : TokenType.KEYWORD,
    "guard"   : TokenType.KEYWORD,
    "shield"  : TokenType.KEYWORD,
    "managed" : TokenType.KEYWORD,
    "raw"     : TokenType.KEYWORD,
    "fence"   : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # TYPE SYSTEM — 9 keywords
    # ─────────────────────────────────────
    "kind"      : TokenType.KEYWORD,
    "record"    : TokenType.KEYWORD,
    "variant"   : TokenType.KEYWORD,
    "blueprint" : TokenType.KEYWORD,
    "contract"  : TokenType.KEYWORD,
    "build"     : TokenType.KEYWORD,
    "grow"      : TokenType.KEYWORD,
    "shape"     : TokenType.KEYWORD,
    "narrow"    : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # MODULE SYSTEM — 7 keywords
    # ─────────────────────────────────────
    "module"  : TokenType.KEYWORD,
    "bring"   : TokenType.KEYWORD,
    "expose"  : TokenType.KEYWORD,
    "from"    : TokenType.KEYWORD,
    "using"   : TokenType.KEYWORD,
    "space"   : TokenType.KEYWORD,
    "bundle"  : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # ERROR HANDLING — 7 keywords
    # ─────────────────────────────────────
    "attempt" : TokenType.KEYWORD,
    "rescue"  : TokenType.KEYWORD,
    "raise"   : TokenType.KEYWORD,
    "always"  : TokenType.KEYWORD,
    "fault"   : TokenType.KEYWORD,
    "recover" : TokenType.KEYWORD,
    "expect"  : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # OBJECT ORIENTED — 8 keywords
    # ─────────────────────────────────────
    "object"   : TokenType.KEYWORD,
    "forge"    : TokenType.KEYWORD,
    "this"     : TokenType.KEYWORD,
    "parent"   : TokenType.KEYWORD,
    "fixed"    : TokenType.KEYWORD,
    "redefine" : TokenType.KEYWORD,
    "extend"   : TokenType.KEYWORD,
    "hidden"   : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # FUNCTIONAL PROGRAMMING — 7 keywords
    # ─────────────────────────────────────
    "transform" : TokenType.KEYWORD,
    "sieve"     : TokenType.KEYWORD,
    "fold"      : TokenType.KEYWORD,
    "chain"     : TokenType.KEYWORD,
    "compose"   : TokenType.KEYWORD,
    "partial"   : TokenType.KEYWORD,
    "memoize"   : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # CONCURRENCY — 6 keywords
    # ─────────────────────────────────────
    "launch"  : TokenType.KEYWORD,
    "tunnel"  : TokenType.KEYWORD,
    "push"    : TokenType.KEYWORD,
    "pull"    : TokenType.KEYWORD,
    "barrier" : TokenType.KEYWORD,
    "atomic"  : TokenType.KEYWORD,

    # ─────────────────────────────────────
    # DECLARATION & SCOPE — 4 keywords
    # ─────────────────────────────────────
    "let"      : TokenType.KEYWORD,
    "constant" : TokenType.KEYWORD,
    "open"     : TokenType.KEYWORD,
    "internal" : TokenType.KEYWORD,

}


# ============================================
# NIMNA DATA TYPES — All 25
# Type names bhi special tokens hain
# ============================================

TYPE_KEYWORDS = {

    # Whole Numbers
    "Tiny"       : TokenType.TYPE_TINY,
    "Short"      : TokenType.TYPE_SHORT,
    "Whole"      : TokenType.TYPE_WHOLE,
    "Long"       : TokenType.TYPE_LONG,
    "Huge"       : TokenType.TYPE_HUGE,

    # Decimal Numbers
    "Decimal"    : TokenType.TYPE_DECIMAL,
    "Precise"    : TokenType.TYPE_PRECISE,
    "Exact"      : TokenType.TYPE_EXACT,

    # Text Types
    "Text"       : TokenType.TYPE_TEXT,
    "Letter"     : TokenType.TYPE_LETTER,
    "Symbol"     : TokenType.TYPE_SYMBOL,

    # Logical
    "Truth"      : TokenType.TYPE_TRUTH,

    # Raw
    "Bit"        : TokenType.TYPE_BIT,

    # Collections
    "Sequence"   : TokenType.TYPE_SEQUENCE,
    "Collection" : TokenType.TYPE_COLLECTION,
    "Mapping"    : TokenType.TYPE_MAPPING,
    "Unique"     : TokenType.TYPE_UNIQUE,
    "Bundle"     : TokenType.TYPE_BUNDLE,

    # Special
    "Maybe"      : TokenType.TYPE_MAYBE,
    "Outcome"    : TokenType.TYPE_OUTCOME,
    "Task"       : TokenType.TYPE_TASK,
    "Flow"       : TokenType.TYPE_FLOW,
    "Action"     : TokenType.TYPE_ACTION,
    "Wild"       : TokenType.TYPE_WILD,
    "Nothing"    : TokenType.TYPE_NOTHING,

}


# ============================================
# HELPER FUNCTIONS
# ============================================

def is_keyword(word):
    """Check karo koi word NIMNA keyword hai ya nahi"""
    return word in KEYWORDS


def is_type_keyword(word):
    """Check karo koi word NIMNA data type hai ya nahi"""
    return word in TYPE_KEYWORDS


def get_token_type(word):
    """
    Kisi word ka sahi TokenType return karo.
    Pehle keywords check karo,
    phir types check karo,
    agar kuch nahi mila toh IDENTIFIER return karo.
    """
    if word in KEYWORDS:
        return KEYWORDS[word]
    if word in TYPE_KEYWORDS:
        return TYPE_KEYWORDS[word]
    return None
