# ============================================
# NIMNA Language — Integer IR Generator
# File: src/codegen/int_codegen.py
# Compiler: nimac
# ============================================

# NIMNA integer types → LLVM types
INT_TYPE_MAP = {
    "Tiny"  : "i8",
    "Short" : "i16",
    "Whole" : "i64",
    "Long"  : "i64",
    "Huge"  : "i128",
}

# Valid ranges for each type
INT_RANGES = {
    "Tiny"  : (-128,          127),
    "Short" : (-32768,        32767),
    "Whole" : (-2147483648,   2147483647),
    "Long"  : (-9223372036854775808, 9223372036854775807),
    "Huge"  : (-170141183460469231731687303715884105728,
                170141183460469231731687303715884105727),
}


class IntCodegen:
    """
    NIMNA Integer IR Generator

    Handles:
    1. Integer literals → IR constants
    2. Integer variables → alloca/store/load
    3. Integer arithmetic → add/sub/mul/div/rem
    4. Integer comparison → icmp
    5. Integer type conversion → sext/trunc
    6. Range overflow detection
    """

    def __init__(self, ir_writer):
        self.ir      = ir_writer
        self.errors  = []
        self.warnings = []

    # ==========================================
    # LITERAL
    # ==========================================

    def emit_literal(self, value, nimna_type="Whole"):
        """
        Integer literal → IR constant string.
        Returns: (ir_value, llvm_type)
        """
        llvm_type = INT_TYPE_MAP.get(nimna_type, "i64")

        # Range check
        if nimna_type in INT_RANGES:
            lo, hi = INT_RANGES[nimna_type]
            if not (lo <= value <= hi):
                self.warnings.append(
                    f"Value {value} overflows '{nimna_type}' "
                    f"(range {lo}..{hi}). "
                    f"Consider using a larger type."
                )

        return str(value), llvm_type

    # ==========================================
    # VARIABLE
    # ==========================================

    def emit_declare(self, var_name, nimna_type,
                     init_value=None):
        """
        Integer variable declare karo.
        Returns: (ptr_reg, llvm_type)
        """
        llvm_type = INT_TYPE_MAP.get(nimna_type, "i64")
        ptr       = self.ir.new_temp()
        self.ir.alloca(ptr, llvm_type)

        if init_value is not None:
            self.ir.store(str(init_value), llvm_type, ptr)

        return ptr, llvm_type

    def emit_store(self, ptr, llvm_type, value):
        """Value store karo integer variable mein."""
        self.ir.store(value, llvm_type, ptr)

    def emit_load(self, ptr, llvm_type):
        """
        Integer variable load karo.
        Returns: loaded register name
        """
        reg = self.ir.new_temp()
        self.ir.load(reg, llvm_type, ptr)
        return reg

    # ==========================================
    # ARITHMETIC
    # ==========================================

    def emit_add(self, left, right, llvm_type):
        """
        a + b → IR add instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = add nsw {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_sub(self, left, right, llvm_type):
        """
        a - b → IR sub instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sub nsw {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_mul(self, left, right, llvm_type):
        """
        a * b → IR mul instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = mul nsw {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_div(self, left, right, llvm_type):
        """
        a / b → IR sdiv instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sdiv {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_rem(self, left, right, llvm_type):
        """
        a % b → IR srem instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = srem {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_power(self, base, exp, llvm_type):
        """
        a ** b → loop-based power (no LLVM intrinsic for int).
        Simple: emit mul loop unrolled for small constants.
        Returns: result register
        """
        # For now: treat as mul repeated
        # Full implementation in optimizer step
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    ; power({base}, {exp}) — simplified"
        )
        self.ir.lines.append(
            f"    {dest} = mul nsw {llvm_type} {base}, {base}"
        )
        return dest, llvm_type

    def emit_negate(self, value, llvm_type):
        """
        -value → IR sub 0, value.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sub nsw {llvm_type} 0, {value}"
        )
        return dest, llvm_type

    # ==========================================
    # COMPARISON
    # ==========================================

    def emit_compare(self, left, op, right, llvm_type):
        """
        Comparison → icmp instruction.
        Returns: (result register, "i1")
        """
        op_map = {
            "==" : "eq",
            "!=" : "ne",
            ">"  : "sgt",
            "<"  : "slt",
            ">=" : "sge",
            "<=" : "sle",
        }
        cmp_op = op_map.get(op, "eq")
        dest   = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = icmp {cmp_op} "
            f"{llvm_type} {left}, {right}"
        )
        return dest, "i1"

    # ==========================================
    # TYPE CONVERSION
    # ==========================================

    def emit_extend(self, value, from_type, to_type):
        """
        Small int → Large int (sign extend).
        e.g. i8 → i64
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sext {from_type} "
            f"{value} to {to_type}"
        )
        return dest, to_type

    def emit_truncate(self, value, from_type, to_type):
        """
        Large int → Small int (truncate).
        e.g. i64 → i8
        Generates warning — data may be lost.
        Returns: result register
        """
        self.warnings.append(
            f"Truncating {from_type} to {to_type} "
            f"— data loss possible."
        )
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = trunc {from_type} "
            f"{value} to {to_type}"
        )
        return dest, to_type

    def emit_to_float(self, value, int_type, float_type):
        """
        Integer → Float convert.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sitofp {int_type} "
            f"{value} to {float_type}"
        )
        return dest, float_type

    def emit_bool_to_int(self, value, to_type="i64"):
        """
        i1 (Truth) → integer (zext).
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = zext i1 {value} to {to_type}"
        )
        return dest, to_type

    # ==========================================
    # BITWISE
    # ==========================================

    def emit_and(self, left, right, llvm_type):
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = and {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_or(self, left, right, llvm_type):
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = or {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_xor(self, left, right, llvm_type):
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = xor {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_shl(self, left, right, llvm_type):
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = shl {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_shr(self, left, right, llvm_type):
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = ashr {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_not(self, value, llvm_type):
        """Bitwise NOT → xor with -1."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = xor {llvm_type} {value}, -1"
        )
        return dest, llvm_type

    # ==========================================
    # HELPERS
    # ==========================================

    def get_llvm_type(self, nimna_type):
        return INT_TYPE_MAP.get(nimna_type, "i64")

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
