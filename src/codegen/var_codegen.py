# ============================================
# NIMNA Language — Variable & Assignment IR
# File: src/codegen/var_codegen.py
# Compiler: nimac
# ============================================

# All NIMNA types → LLVM types
NIMNA_TYPE_MAP = {
    # Integer types
    "Tiny"       : "i8",
    "Short"      : "i16",
    "Whole"      : "i64",
    "Long"       : "i64",
    "Huge"       : "i128",
    # Decimal types
    "Decimal"    : "double",
    "Precise"    : "double",
    "Exact"      : "fp128",
    # Text types
    "Text"       : "i8*",
    "Letter"     : "i8",
    "Symbol"     : "i32",
    # Logic
    "Truth"      : "i1",
    "Bit"        : "i8",
    # Collections
    "Collection" : "i8*",
    "Sequence"   : "i8*",
    "Mapping"    : "i8*",
    "Unique"     : "i8*",
    "Bundle"     : "i8*",
    # Special
    "Wild"       : "i64",
    "Nothing"    : "void",
    "Maybe"      : "i8*",
    "Outcome"    : "i8*",
    "Task"       : "i8*",
    "Flow"       : "i8*",
    "Action"     : "i8*",
}

# Float types set
FLOAT_LLVM_TYPES = {"double", "fp128", "float"}

# Pointer types set
POINTER_LLVM_TYPES = {"i8*"}


class VarCodegen:
    """
    NIMNA Variable & Assignment IR Generator

    Handles:
    1. let    — variable declaration + alloca
    2. constant — constant declaration
    3. =      — simple assignment (store)
    4. +=     — add + store
    5. -=     — sub + store
    6. *=     — mul + store
    7. /=     — div + store
    8. %=     — rem + store
    9. **=    — power + store
    10. Global variables
    11. Function parameters (alloca + store)
    """

    def __init__(self, ir_writer):
        self.ir        = ir_writer
        self.errors    = []
        self.warnings  = []
        # name → (llvm_type, ptr_reg, is_constant)
        self.var_table = {}

    # ==========================================
    # TYPE HELPERS
    # ==========================================

    def get_llvm_type(self, nimna_type):
        """NIMNA type → LLVM type string."""
        return NIMNA_TYPE_MAP.get(nimna_type, "i64")

    def is_float(self, llvm_type):
        return llvm_type in FLOAT_LLVM_TYPES

    def is_pointer(self, llvm_type):
        return llvm_type.endswith("*")

    # ==========================================
    # DECLARATION — let / constant
    # ==========================================

    def emit_let(self, name, nimna_type, init_value=None,
                 init_reg=None):
        """
        let name: Type = value

        Emits:
            %ptr = alloca llvm_type
            store llvm_type value, llvm_type* %ptr

        Returns: (ptr_reg, llvm_type)
        """
        llvm_type = self.get_llvm_type(nimna_type)

        # Alloca
        ptr = self.ir.new_temp()
        if self.is_pointer(llvm_type):
            self.ir.lines.append(
                f"    {ptr} = alloca {llvm_type}"
            )
        else:
            self.ir.lines.append(
                f"    {ptr} = alloca {llvm_type}"
            )

        # Store initial value
        if init_reg is not None:
            self._emit_store(init_reg, llvm_type, ptr)
        elif init_value is not None:
            self._emit_store(
                str(init_value), llvm_type, ptr
            )

        # Register in var table
        self.var_table[name] = (llvm_type, ptr, False)
        return ptr, llvm_type

    def emit_constant(self, name, nimna_type,
                      init_value=None, init_reg=None):
        """
        constant NAME: Type = value

        Same as let but marked is_constant=True.
        Any reassignment → error.

        Returns: (ptr_reg, llvm_type)
        """
        llvm_type = self.get_llvm_type(nimna_type)
        ptr       = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = alloca {llvm_type}"
        )

        if init_reg is not None:
            self._emit_store(init_reg, llvm_type, ptr)
        elif init_value is not None:
            self._emit_store(
                str(init_value), llvm_type, ptr
            )

        # Mark as constant
        self.var_table[name] = (llvm_type, ptr, True)
        return ptr, llvm_type

    def emit_param(self, name, nimna_type, param_reg):
        """
        Function parameter → alloca + store.
        Converts SSA param to addressable variable.

        Returns: (ptr_reg, llvm_type)
        """
        llvm_type = self.get_llvm_type(nimna_type)
        ptr       = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = alloca {llvm_type}"
        )
        self._emit_store(param_reg, llvm_type, ptr)
        self.var_table[name] = (llvm_type, ptr, False)
        return ptr, llvm_type

    # ==========================================
    # LOAD
    # ==========================================

    def emit_load(self, name):
        """
        Variable load karo.

        Returns: (value_reg, llvm_type)
                 or (None, None) if not found
        """
        if name not in self.var_table:
            self.errors.append(
                f"Variable '{name}' not declared."
            )
            return None, None

        llvm_type, ptr, _ = self.var_table[name]
        reg = self.ir.new_temp()

        if self.is_pointer(llvm_type):
            self.ir.lines.append(
                f"    {reg} = load {llvm_type}, "
                f"{llvm_type}* {ptr}"
            )
        else:
            self.ir.lines.append(
                f"    {reg} = load {llvm_type}, "
                f"{llvm_type}* {ptr}"
            )

        return reg, llvm_type

    # ==========================================
    # ASSIGNMENT — = and compound ops
    # ==========================================

    def emit_assign(self, name, value_reg):
        """
        name = value_reg

        Returns: True if success
        """
        if name not in self.var_table:
            self.errors.append(
                f"Variable '{name}' not declared."
            )
            return False

        llvm_type, ptr, is_const = self.var_table[name]

        if is_const:
            self.errors.append(
                f"Cannot reassign constant '{name}'."
            )
            return False

        self._emit_store(value_reg, llvm_type, ptr)
        return True

    def emit_assign_op(self, name, operator, value_reg):
        """
        Compound assignment: +=  -=  *=  /=  %=  **=

        Emits: load → op → store

        Returns: (result_reg, llvm_type)
        """
        if name not in self.var_table:
            self.errors.append(
                f"Variable '{name}' not declared."
            )
            return None, None

        llvm_type, ptr, is_const = self.var_table[name]

        if is_const:
            self.errors.append(
                f"Cannot reassign constant '{name}'."
            )
            return None, None

        # Load current value
        cur = self.ir.new_temp()
        self.ir.lines.append(
            f"    {cur} = load {llvm_type}, "
            f"{llvm_type}* {ptr}"
        )

        # Apply operation
        result = self.ir.new_temp()
        is_fl  = self.is_float(llvm_type)

        if operator == "+=":
            instr = "fadd" if is_fl else "add nsw"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        elif operator == "-=":
            instr = "fsub" if is_fl else "sub nsw"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        elif operator == "*=":
            instr = "fmul" if is_fl else "mul nsw"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        elif operator == "/=":
            instr = "fdiv" if is_fl else "sdiv"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        elif operator == "%=":
            instr = "frem" if is_fl else "srem"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        elif operator == "**=":
            # Power: simplified as mul for now
            self.ir.lines.append(
                f"    ; **= simplified as mul"
            )
            instr = "fmul" if is_fl else "mul nsw"
            self.ir.lines.append(
                f"    {result} = {instr} "
                f"{llvm_type} {cur}, {value_reg}"
            )
        else:
            self.errors.append(
                f"Unknown compound operator '{operator}'."
            )
            return None, None

        # Store result back
        self._emit_store(result, llvm_type, ptr)
        return result, llvm_type

    # ==========================================
    # GLOBAL VARIABLES
    # ==========================================

    def emit_global_int(self, name, nimna_type,
                        value=0):
        """
        Global integer variable emit karo.
        (Outside function scope)
        """
        llvm_type = self.get_llvm_type(nimna_type)
        global_name = f"@{name}"
        self.ir.globals.append(
            f"{global_name} = global {llvm_type} {value}"
        )
        self.var_table[name] = (llvm_type, global_name,
                                False)
        return global_name, llvm_type

    def emit_global_constant(self, name, nimna_type,
                             value=0):
        """
        Global constant emit karo.
        constant MAX: Whole = 100
        """
        llvm_type   = self.get_llvm_type(nimna_type)
        global_name = f"@{name}"
        self.ir.globals.append(
            f"{global_name} = constant {llvm_type} {value}"
        )
        self.var_table[name] = (llvm_type, global_name,
                                True)
        return global_name, llvm_type

    # ==========================================
    # SCOPE MANAGEMENT
    # ==========================================

    def enter_scope(self):
        """New scope ke liye snapshot save karo."""
        return dict(self.var_table)

    def exit_scope(self, saved_table):
        """Previous scope restore karo."""
        self.var_table = saved_table

    def lookup(self, name):
        """
        Variable info lookup karo.
        Returns: (llvm_type, ptr, is_const) or None
        """
        return self.var_table.get(name, None)

    # ==========================================
    # INTERNAL HELPER
    # ==========================================

    def _emit_store(self, value, llvm_type, ptr):
        """Internal store helper."""
        if self.is_pointer(llvm_type):
            self.ir.lines.append(
                f"    store {llvm_type} {value}, "
                f"{llvm_type}* {ptr}"
            )
        else:
            self.ir.lines.append(
                f"    store {llvm_type} {value}, "
                f"{llvm_type}* {ptr}"
            )

    # ==========================================
    # STATUS
    # ==========================================

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0

    def clear_scope(self):
        """Function end pe vars clear karo."""
        self.var_table = {}
