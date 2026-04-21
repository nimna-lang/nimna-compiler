# ============================================
# NIMNA Language — Type Map
# File: src/codegen/type_map.py
# NIMNA types → LLVM IR types
# ============================================

# NIMNA type → LLVM IR type string
NIMNA_TO_LLVM = {
    "Tiny"       : "i8",
    "Short"      : "i16",
    "Whole"      : "i64",
    "Long"       : "i64",
    "Huge"       : "i128",
    "Decimal"    : "double",
    "Precise"    : "double",
    "Exact"      : "fp128",
    "Text"       : "i8*",
    "Letter"     : "i8",
    "Truth"      : "i1",
    "Nothing"    : "void",
    "Wild"       : "i64",
    "Collection" : "i8*",
    "Mapping"    : "i8*",
    "Sequence"   : "i8*",
}

# Default type agar koi nahi mila
DEFAULT_LLVM_TYPE = "i64"

# Numeric LLVM types
LLVM_INT_TYPES    = {"i8", "i16", "i32", "i64", "i128"}
LLVM_FLOAT_TYPES  = {"float", "double", "fp128"}


def nimna_to_llvm(nimna_type):
    """NIMNA type string ko LLVM type string mein convert karo."""
    if nimna_type is None:
        return DEFAULT_LLVM_TYPE
    return NIMNA_TO_LLVM.get(nimna_type, DEFAULT_LLVM_TYPE)


def is_float_type(llvm_type):
    """Check karo yeh float type hai ya nahi."""
    return llvm_type in LLVM_FLOAT_TYPES


def is_int_type(llvm_type):
    """Check karo yeh integer type hai ya nahi."""
    return llvm_type in LLVM_INT_TYPES


def get_zero_value(llvm_type):
    """Type ka zero/default value return karo."""
    if llvm_type in LLVM_FLOAT_TYPES:
        return "0.0"
    if llvm_type == "i1":
        return "false"
    if llvm_type == "i8*":
        return "null"
    return "0"


def get_add_instruction(llvm_type):
    """Addition instruction return karo type ke hisaab se."""
    if llvm_type in LLVM_FLOAT_TYPES:
        return "fadd"
    return "add"


def get_sub_instruction(llvm_type):
    """Subtraction instruction return karo."""
    if llvm_type in LLVM_FLOAT_TYPES:
        return "fsub"
    return "sub"


def get_mul_instruction(llvm_type):
    """Multiplication instruction return karo."""
    if llvm_type in LLVM_FLOAT_TYPES:
        return "fmul"
    return "mul"


def get_div_instruction(llvm_type):
    """Division instruction return karo."""
    if llvm_type in LLVM_FLOAT_TYPES:
        return "fdiv"
    return "sdiv"


def get_cmp_instruction(llvm_type, operator):
    """
    Comparison instruction return karo.
    Integer: icmp
    Float:   fcmp
    """
    op_map_int = {
        "==" : "eq",
        "!=" : "ne",
        ">"  : "sgt",
        "<"  : "slt",
        ">=" : "sge",
        "<=" : "sle",
    }
    op_map_float = {
        "==" : "oeq",
        "!=" : "one",
        ">"  : "ogt",
        "<"  : "olt",
        ">=" : "oge",
        "<=" : "ole",
    }
    if llvm_type in LLVM_FLOAT_TYPES:
        cmp_op = op_map_float.get(operator, "oeq")
        return f"fcmp {cmp_op}"
    else:
        cmp_op = op_map_int.get(operator, "eq")
        return f"icmp {cmp_op}"
