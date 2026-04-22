# ============================================
# NIMNA Language — Expression IR Generator
# File: src/codegen/expr_codegen.py
# Compiler: nimac
# ============================================

# Float LLVM types
FLOAT_TYPES = {"double", "fp128", "float"}

# Integer LLVM types
INT_TYPES = {"i8", "i16", "i32", "i64", "i128"}

# NIMNA type → LLVM type
NIMNA_TO_LLVM = {
    "Tiny"    : "i8",    "Short"   : "i16",
    "Whole"   : "i64",   "Long"    : "i64",
    "Huge"    : "i128",  "Decimal" : "double",
    "Precise" : "double","Exact"   : "fp128",
    "Text"    : "i8*",   "Letter"  : "i8",
    "Symbol"  : "i32",   "Truth"   : "i1",
    "Bit"     : "i8",    "Wild"    : "i64",
}

# Integer size order for promotion
INT_ORDER = ["i8", "i16", "i32", "i64", "i128"]


class ExprCodegen:
    """
    NIMNA Binary Expression IR Generator

    Handles all 45 NIMNA operators:

    Arithmetic  : +  -  *  /  %  **
    Comparison  : ==  !=  >  <  >=  <=
    Logical     : &&  ||  !!
    Bitwise     : &  |  ^  ~  <<  >>
    Range       : ..  ..=  ...
    Assignment  : =  +=  -=  *=  /=  %=  **=
    Pipeline    : |>
    Null safety : ??
    Type ops    : as  is
    """

    def __init__(self, ir_writer):
        self.ir      = ir_writer
        self.errors  = []
        self.warnings = []

    # ==========================================
    # TYPE HELPERS
    # ==========================================

    def is_float(self, llvm_type):
        return llvm_type in FLOAT_TYPES

    def is_int(self, llvm_type):
        return llvm_type in INT_TYPES

    def is_pointer(self, llvm_type):
        return llvm_type.endswith("*")

    def promote_type(self, t1, t2):
        """
        Two types mein se larger type return karo.
        Float > Integer hierarchy.
        """
        if t1 == t2:
            return t1
        # Float wins over int
        if t1 in FLOAT_TYPES or t2 in FLOAT_TYPES:
            if t1 == "fp128" or t2 == "fp128":
                return "fp128"
            return "double"
        # Larger int wins
        if t1 in INT_ORDER and t2 in INT_ORDER:
            i1 = INT_ORDER.index(t1)
            i2 = INT_ORDER.index(t2)
            return INT_ORDER[max(i1, i2)]
        return t1

    def coerce(self, val, from_type, to_type):
        """
        Value ko target type mein convert karo agar zaroorat ho.
        Returns: (new_val, to_type)
        """
        if from_type == to_type:
            return val, to_type

        # int → float
        if from_type in INT_TYPES and to_type in FLOAT_TYPES:
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = sitofp {from_type} "
                f"{val} to {to_type}"
            )
            return dest, to_type

        # float → float extend
        if from_type == "double" and to_type == "fp128":
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = fpext double {val} to fp128"
            )
            return dest, to_type

        # int extend
        if from_type in INT_TYPES and to_type in INT_TYPES:
            fi = INT_ORDER.index(from_type) \
                if from_type in INT_ORDER else 0
            ti = INT_ORDER.index(to_type)   \
                if to_type   in INT_ORDER else 0
            if ti > fi:
                dest = self.ir.new_temp()
                self.ir.lines.append(
                    f"    {dest} = sext {from_type} "
                    f"{val} to {to_type}"
                )
                return dest, to_type

        return val, from_type

    # ==========================================
    # ARITHMETIC OPERATORS
    # ==========================================

    def emit_add(self, left, left_type, right, right_type):
        """
        a + b

        Text + Text = string concat (via runtime)
        Int  + Int  = add nsw
        Float + *   = fadd
        """
        # Text concatenation
        if left_type == "i8*":
            return self._emit_strcat(left, right)

        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            self.ir.lines.append(
                f"    {dest} = fadd {result_type} "
                f"{left}, {right}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = add nsw {result_type} "
                f"{left}, {right}"
            )
        return dest, result_type

    def emit_sub(self, left, left_type, right, right_type):
        """a - b"""
        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            self.ir.lines.append(
                f"    {dest} = fsub {result_type} "
                f"{left}, {right}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = sub nsw {result_type} "
                f"{left}, {right}"
            )
        return dest, result_type

    def emit_mul(self, left, left_type, right, right_type):
        """a * b"""
        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            self.ir.lines.append(
                f"    {dest} = fmul {result_type} "
                f"{left}, {right}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = mul nsw {result_type} "
                f"{left}, {right}"
            )
        return dest, result_type

    def emit_div(self, left, left_type, right, right_type):
        """a / b"""
        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            self.ir.lines.append(
                f"    {dest} = fdiv {result_type} "
                f"{left}, {right}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = sdiv {result_type} "
                f"{left}, {right}"
            )
        return dest, result_type

    def emit_rem(self, left, left_type, right, right_type):
        """a % b"""
        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            self.ir.lines.append(
                f"    {dest} = frem {result_type} "
                f"{left}, {right}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = srem {result_type} "
                f"{left}, {right}"
            )
        return dest, result_type

    def emit_power(self, base, base_type,
                   exp, exp_type):
        """
        a ** b

        Float: llvm.pow intrinsic
        Int:   simplified (mul loop — full in optimizer)
        """
        if self.is_float(base_type):
            # Convert exp to float if needed
            exp_f, _ = self.coerce(exp, exp_type, base_type)
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = call {base_type} "
                f"@llvm.pow.{base_type}"
                f"({base_type} {base}, {base_type} {exp_f})"
            )
            return dest, base_type
        else:
            # Integer power — simplified as mul
            self.ir.lines.append(
                f"    ; integer ** simplified"
            )
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = mul nsw {base_type} "
                f"{base}, {base}"
            )
            return dest, base_type

    # ==========================================
    # COMPARISON OPERATORS
    # ==========================================

    def emit_compare(self, left, left_type,
                     op, right, right_type):
        """
        a op b → i1 result

        Supports: ==  !=  >  <  >=  <=
        """
        result_type = self.promote_type(left_type, right_type)
        left,  _    = self.coerce(left,  left_type,  result_type)
        right, _    = self.coerce(right, right_type, result_type)
        dest        = self.ir.new_temp()

        if self.is_float(result_type):
            op_map = {
                "==" : "oeq", "!=" : "one",
                ">"  : "ogt", "<"  : "olt",
                ">=" : "oge", "<=" : "ole",
            }
            cmp_op = op_map.get(op, "oeq")
            self.ir.lines.append(
                f"    {dest} = fcmp {cmp_op} "
                f"{result_type} {left}, {right}"
            )
        else:
            op_map = {
                "==" : "eq",  "!=" : "ne",
                ">"  : "sgt", "<"  : "slt",
                ">=" : "sge", "<=" : "sle",
            }
            cmp_op = op_map.get(op, "eq")
            self.ir.lines.append(
                f"    {dest} = icmp {cmp_op} "
                f"{result_type} {left}, {right}"
            )
        return dest, "i1"

    # ==========================================
    # LOGICAL OPERATORS
    # ==========================================

    def emit_and(self, left, right):
        """
        a && b → i1 and i1
        Both operands must be i1 (Truth).
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = and i1 {left}, {right}"
        )
        return dest, "i1"

    def emit_or(self, left, right):
        """a || b → i1 or i1"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = or i1 {left}, {right}"
        )
        return dest, "i1"

    def emit_not(self, value):
        """
        !! value → xor i1 value, true
        Logical NOT.
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = xor i1 {value}, true"
        )
        return dest, "i1"

    # ==========================================
    # BITWISE OPERATORS
    # ==========================================

    def emit_bit_and(self, left, right, llvm_type):
        """a & b"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = and {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_bit_or(self, left, right, llvm_type):
        """a | b"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = or {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_bit_xor(self, left, right, llvm_type):
        """a ^ b"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = xor {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_bit_not(self, value, llvm_type):
        """~ value → xor value, -1"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = xor {llvm_type} {value}, -1"
        )
        return dest, llvm_type

    def emit_shl(self, left, right, llvm_type):
        """a << b"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = shl {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    def emit_shr(self, left, right, llvm_type):
        """a >> b"""
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = ashr {llvm_type} {left}, {right}"
        )
        return dest, llvm_type

    # ==========================================
    # UNARY OPERATORS
    # ==========================================

    def emit_negate(self, value, llvm_type):
        """- value (unary minus)"""
        dest = self.ir.new_temp()
        if self.is_float(llvm_type):
            self.ir.lines.append(
                f"    {dest} = fneg {llvm_type} {value}"
            )
        else:
            self.ir.lines.append(
                f"    {dest} = sub nsw {llvm_type} 0, {value}"
            )
        return dest, llvm_type

    # ==========================================
    # TYPE CAST — as
    # ==========================================

    def emit_cast(self, value, from_nimna, to_nimna):
        """
        value as ToType

        Handles safe and explicit casts.
        Returns: (result_reg, llvm_to_type)
        """
        from_llvm = NIMNA_TO_LLVM.get(from_nimna, "i64")
        to_llvm   = NIMNA_TO_LLVM.get(to_nimna,   "i64")

        if from_llvm == to_llvm:
            return value, to_llvm

        dest = self.ir.new_temp()

        # Int → Float
        if from_llvm in INT_TYPES and to_llvm in FLOAT_TYPES:
            self.ir.lines.append(
                f"    {dest} = sitofp {from_llvm} "
                f"{value} to {to_llvm}"
            )

        # Float → Int
        elif from_llvm in FLOAT_TYPES and to_llvm in INT_TYPES:
            self.warnings.append(
                f"Cast {from_nimna} → {to_nimna}: "
                f"decimal part will be cut."
            )
            self.ir.lines.append(
                f"    {dest} = fptosi {from_llvm} "
                f"{value} to {to_llvm}"
            )

        # Int → Larger Int
        elif from_llvm in INT_TYPES and to_llvm in INT_TYPES:
            fi = INT_ORDER.index(from_llvm) \
                if from_llvm in INT_ORDER else 0
            ti = INT_ORDER.index(to_llvm)   \
                if to_llvm   in INT_ORDER else 0
            if ti > fi:
                self.ir.lines.append(
                    f"    {dest} = sext {from_llvm} "
                    f"{value} to {to_llvm}"
                )
            else:
                self.warnings.append(
                    f"Cast {from_nimna} → {to_nimna}: "
                    f"possible data loss."
                )
                self.ir.lines.append(
                    f"    {dest} = trunc {from_llvm} "
                    f"{value} to {to_llvm}"
                )

        # Float extend
        elif from_llvm == "double" and to_llvm == "fp128":
            self.ir.lines.append(
                f"    {dest} = fpext double "
                f"{value} to fp128"
            )

        # Float truncate
        elif from_llvm == "fp128" and to_llvm == "double":
            self.ir.lines.append(
                f"    {dest} = fptrunc fp128 "
                f"{value} to double"
            )

        else:
            # Bitcast fallback
            self.ir.lines.append(
                f"    {dest} = bitcast {from_llvm} "
                f"{value} to {to_llvm}"
            )

        return dest, to_llvm

    # ==========================================
    # NULL SAFETY — ??
    # ==========================================

    def emit_null_default(self, value, default,
                          llvm_type):
        """
        value ?? default

        If value is null → use default.
        Simple: icmp null + select.
        Returns: (result_reg, llvm_type)
        """
        # Check if null
        is_null = self.ir.new_temp()
        self.ir.lines.append(
            f"    {is_null} = icmp eq {llvm_type} "
            f"{value}, null"
        )
        # Select
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = select i1 {is_null}, "
            f"{llvm_type} {default}, "
            f"{llvm_type} {value}"
        )
        return dest, llvm_type

    # ==========================================
    # RANGE OPERATORS
    # ==========================================

    def emit_range(self, start, start_type,
                   end, end_type, inclusive=False):
        """
        start .. end   (exclusive)
        start ..= end  (inclusive)

        Returns struct-like representation.
        For now: (start_reg, end_reg, is_inclusive)
        Full implementation in loop codegen.
        """
        self.ir.lines.append(
            f"    ; range {start}..{'=' if inclusive else ''}{end}"
        )
        return (start, end, inclusive), "Range"

    # ==========================================
    # STRING CONCAT — helper
    # ==========================================

    def _emit_strcat(self, left, right):
        """
        Text + Text → strcat (C stdlib).
        Returns: (result_ptr, "i8*")
        """
        # Declare strcat if needed
        decl = "declare i8* @strcat(i8*, i8*)"
        if decl not in self.ir.declarations:
            self.ir.declarations.append(decl)

        # Declare malloc if needed
        decl2 = "declare i8* @malloc(i64)"
        if decl2 not in self.ir.declarations:
            self.ir.declarations.append(decl2)

        # Declare strlen if needed
        decl3 = "declare i64 @strlen(i8*)"
        if decl3 not in self.ir.declarations:
            self.ir.declarations.append(decl3)

        # strlen(left)
        len1 = self.ir.new_temp()
        self.ir.lines.append(
            f"    {len1} = call i64 @strlen(i8* {left})"
        )

        # strlen(right)
        len2 = self.ir.new_temp()
        self.ir.lines.append(
            f"    {len2} = call i64 @strlen(i8* {right})"
        )

        # total = len1 + len2 + 1
        total = self.ir.new_temp()
        self.ir.lines.append(
            f"    {total} = add i64 {len1}, {len2}"
        )
        total2 = self.ir.new_temp()
        self.ir.lines.append(
            f"    {total2} = add i64 {total}, 1"
        )

        # buf = malloc(total)
        buf = self.ir.new_temp()
        self.ir.lines.append(
            f"    {buf} = call i8* @malloc(i64 {total2})"
        )

        # strcpy(buf, left)
        decl4 = "declare i8* @strcpy(i8*, i8*)"
        if decl4 not in self.ir.declarations:
            self.ir.declarations.append(decl4)
        r1 = self.ir.new_temp()
        self.ir.lines.append(
            f"    {r1} = call i8* @strcpy"
            f"(i8* {buf}, i8* {left})"
        )

        # strcat(buf, right)
        r2 = self.ir.new_temp()
        self.ir.lines.append(
            f"    {r2} = call i8* @strcat"
            f"(i8* {buf}, i8* {right})"
        )

        return buf, "i8*"

    # ==========================================
    # DISPATCH — main entry point
    # ==========================================

    def emit_binary(self, left, left_type,
                    op, right, right_type):
        """
        Main dispatch for any binary operator.

        Returns: (result_reg, result_type)
        """
        if op == "+":
            return self.emit_add(left, left_type,
                                 right, right_type)
        elif op == "-":
            return self.emit_sub(left, left_type,
                                 right, right_type)
        elif op == "*":
            return self.emit_mul(left, left_type,
                                 right, right_type)
        elif op == "/":
            return self.emit_div(left, left_type,
                                 right, right_type)
        elif op == "%":
            return self.emit_rem(left, left_type,
                                 right, right_type)
        elif op == "**":
            return self.emit_power(left, left_type,
                                   right, right_type)
        elif op in ("==","!=",">","<",">=","<="):
            return self.emit_compare(left, left_type,
                                     op,
                                     right, right_type)
        elif op == "&&":
            return self.emit_and(left, right)
        elif op == "||":
            return self.emit_or(left, right)
        elif op == "&":
            t = self.promote_type(left_type, right_type)
            return self.emit_bit_and(left, right, t)
        elif op == "|":
            t = self.promote_type(left_type, right_type)
            return self.emit_bit_or(left, right, t)
        elif op == "^":
            t = self.promote_type(left_type, right_type)
            return self.emit_bit_xor(left, right, t)
        elif op == "<<":
            return self.emit_shl(left, right, left_type)
        elif op == ">>":
            return self.emit_shr(left, right, left_type)
        elif op == "..":
            return self.emit_range(left, left_type,
                                   right, right_type,
                                   inclusive=False)
        elif op == "..=":
            return self.emit_range(left, left_type,
                                   right, right_type,
                                   inclusive=True)
        elif op == "??":
            return self.emit_null_default(
                left, right, left_type
            )
        else:
            self.errors.append(
                f"Unknown operator '{op}'."
            )
            return left, left_type

    # ==========================================
    # STATUS
    # ==========================================

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
