# ============================================
# NIMNA Language — Decimal IR Generator
# File: src/codegen/float_codegen.py
# Compiler: nimac
# ============================================

# NIMNA decimal types → LLVM types
FLOAT_TYPE_MAP = {
    "Decimal" : "double",
    "Precise" : "double",
    "Exact"   : "fp128",
}

# Precision info
FLOAT_INFO = {
    "Decimal" : {"bits": 64,  "precision": "15-17 digits"},
    "Precise" : {"bits": 64,  "precision": "15-17 digits"},
    "Exact"   : {"bits": 128, "precision": "33-36 digits"},
}


class FloatCodegen:
    """
    NIMNA Decimal IR Generator

    Handles:
    1. Decimal literals  → IR float constants
    2. Decimal variables → alloca/store/load
    3. Decimal arithmetic → fadd/fsub/fmul/fdiv/frem
    4. Decimal comparison → fcmp
    5. Decimal ↔ Integer conversion
    6. Special values (inf, nan)
    """

    def __init__(self, ir_writer):
        self.ir       = ir_writer
        self.errors   = []
        self.warnings = []

    # ==========================================
    # LITERAL
    # ==========================================

    def emit_literal(self, value, nimna_type="Decimal"):
        """
        Decimal literal → IR float constant.
        Returns: (ir_value, llvm_type)
        """
        llvm_type = FLOAT_TYPE_MAP.get(nimna_type, "double")

        # LLVM requires decimal point
        if isinstance(value, int):
            ir_val = f"{value}.0"
        else:
            ir_val = f"{float(value)}"
            # Ensure decimal point present
            if "." not in ir_val and "e" not in ir_val.lower():
                ir_val += ".0"

        return ir_val, llvm_type

    # ==========================================
    # VARIABLE
    # ==========================================

    def emit_declare(self, var_name, nimna_type,
                     init_value=None):
        """
        Decimal variable declare karo.
        Returns: (ptr_reg, llvm_type)
        """
        llvm_type = FLOAT_TYPE_MAP.get(nimna_type, "double")
        ptr       = self.ir.new_temp()
        self.ir.alloca(ptr, llvm_type)

        if init_value is not None:
            ir_val, _ = self.emit_literal(
                init_value, nimna_type
            )
            self.ir.store(ir_val, llvm_type, ptr)

        return ptr, llvm_type

    def emit_store(self, ptr, llvm_type, value):
        """Value store karo decimal variable mein."""
        self.ir.store(value, llvm_type, ptr)

    def emit_load(self, ptr, llvm_type):
        """
        Decimal variable load karo.
        Returns: loaded register
        """
        reg = self.ir.new_temp()
        self.ir.load(reg, llvm_type, ptr)
        return reg

    # ==========================================
    # ARITHMETIC
    # ==========================================

    def emit_add(self, left, right, llvm_type):
        """
        a + b → fadd instruction.
        Returns: (result_reg, llvm_type)
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fadd {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_sub(self, left, right, llvm_type):
        """a - b → fsub instruction."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fsub {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_mul(self, left, right, llvm_type):
        """a * b → fmul instruction."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fmul {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_div(self, left, right, llvm_type):
        """a / b → fdiv instruction."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fdiv {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_rem(self, left, right, llvm_type):
        """a % b → frem instruction."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = frem {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_negate(self, value, llvm_type):
        """
        -value → fneg instruction.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fneg {llvm_type} {value}"
        )
        return dest, llvm_type

    def emit_abs(self, value, llvm_type):
        """
        |value| → llvm.fabs intrinsic.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call {llvm_type} "
            f"@llvm.fabs.{llvm_type}({llvm_type} {value})"
        )
        return dest, llvm_type

    def emit_sqrt(self, value, llvm_type):
        """
        sqrt(value) → llvm.sqrt intrinsic.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call {llvm_type} "
            f"@llvm.sqrt.{llvm_type}({llvm_type} {value})"
        )
        return dest, llvm_type

    def emit_floor(self, value, llvm_type):
        """floor(value) → llvm.floor intrinsic."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call {llvm_type} "
            f"@llvm.floor.{llvm_type}({llvm_type} {value})"
        )
        return dest, llvm_type

    def emit_ceil(self, value, llvm_type):
        """ceil(value) → llvm.ceil intrinsic."""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call {llvm_type} "
            f"@llvm.ceil.{llvm_type}({llvm_type} {value})"
        )
        return dest, llvm_type

    def emit_pow(self, base, exp, llvm_type):
        """
        base ** exp → llvm.pow intrinsic.
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call {llvm_type} "
            f"@llvm.pow.{llvm_type}"
            f"({llvm_type} {base}, {llvm_type} {exp})"
        )
        return dest, llvm_type

    # ==========================================
    # COMPARISON
    # ==========================================

    def emit_compare(self, left, op, right, llvm_type):
        """
        Comparison → fcmp instruction.
        Returns: (result_reg, "i1")

        'o' prefix = ordered (NaN safe)
        """
        op_map = {
            "==" : "oeq",
            "!=" : "one",
            ">"  : "ogt",
            "<"  : "olt",
            ">=" : "oge",
            "<=" : "ole",
        }
        cmp_op = op_map.get(op, "oeq")
        dest   = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fcmp {cmp_op} "
            f"{llvm_type} {left}, {right}"
        )
        return dest, "i1"

    # ==========================================
    # TYPE CONVERSION
    # ==========================================

    def emit_to_int(self, value, float_type, int_type):
        """
        Decimal → Integer (truncate toward zero).
        Returns: result register
        Warning: precision loss
        """
        self.warnings.append(
            f"Converting {float_type} to {int_type} "
            f"— decimal part will be cut."
        )
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fptosi {float_type} "
            f"{value} to {int_type}"
        )
        return dest, int_type

    def emit_from_int(self, value, int_type, float_type):
        """
        Integer → Decimal (exact for small ints).
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sitofp {int_type} "
            f"{value} to {float_type}"
        )
        return dest, float_type

    def emit_extend(self, value, from_type, to_type):
        """
        double → fp128 (extend precision).
        Returns: result register
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fpext {from_type} "
            f"{value} to {to_type}"
        )
        return dest, to_type

    def emit_truncate_float(self, value, from_type, to_type):
        """
        fp128 → double (reduce precision).
        Returns: result register
        """
        self.warnings.append(
            f"Truncating {from_type} to {to_type} "
            f"— precision loss possible."
        )
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = fptrunc {from_type} "
            f"{value} to {to_type}"
        )
        return dest, to_type

    # ==========================================
    # HELPERS
    # ==========================================

    def get_llvm_type(self, nimna_type):
        return FLOAT_TYPE_MAP.get(nimna_type, "double")

    def is_float_type(self, nimna_type):
        return nimna_type in FLOAT_TYPE_MAP

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
