# ============================================
# NIMNA Language — Function IR Generator
# File: src/codegen/func_codegen.py
# Compiler: nimac
# ============================================

# NIMNA type → LLVM type
NIMNA_TO_LLVM = {
    "Tiny": "i8", "Short": "i16", "Whole": "i64",
    "Long": "i64", "Huge": "i128",
    "Decimal": "double", "Precise": "double", "Exact": "fp128",
    "Text": "i8*", "Letter": "i8", "Symbol": "i32",
    "Truth": "i1", "Bit": "i8",
    "Collection": "i8*", "Sequence": "i8*",
    "Mapping": "i8*", "Unique": "i8*", "Bundle": "i8*",
    "Wild": "i64", "Nothing": "void",
    "Maybe": "i8*", "Outcome": "i8*", "Task": "i8*",
}

# nimna.io built-in functions
BUILTIN_FUNCTIONS = {
    "nimna.io.print"  : ("void",  [("msg", "i8*")]),
    "nimna.io.write"  : ("void",  [("msg", "i8*")]),
    "nimna.io.input"  : ("i8*",   [("prompt", "i8*")]),
    "nimna.math.sqrt" : ("double",[("x", "double")]),
    "nimna.math.abs"  : ("double",[("x", "double")]),
    "nimna.math.pow"  : ("double",[("base","double"),("exp","double")]),
    "nimna.math.min"  : ("i64",   [("a","i64"),("b","i64")]),
    "nimna.math.max"  : ("i64",   [("a","i64"),("b","i64")]),
}


class FuncCodegen:
    """
    NIMNA Function IR Generator

    Handles:
    1. fn declaration  → define llvm_ret @name(params)
    2. async fn        → same as fn (Task return)
    3. give (return)   → ret instruction
    4. Function call   → call instruction
    5. nimna.io.print  → printf wrapper
    6. nimna.io.input  → scanf wrapper
    7. Forward declarations
    8. Recursive functions
    """

    def __init__(self, ir_writer):
        self.ir              = ir_writer
        self.errors          = []
        self.warnings        = []
        # name → {ret_type, params, is_declared}
        self.func_table      = {}
        self.current_fn      = None
        self.current_ret     = None
        self._printf_done    = False
        self._scanf_done     = False
        self._has_return     = False

    # ==========================================
    # HELPERS
    # ==========================================

    def _llvm(self, nimna_type):
        return NIMNA_TO_LLVM.get(nimna_type, "i64")

    def _ensure_printf(self):
        decl = "declare i32 @printf(i8* noundef, ...)"
        if decl not in self.ir.declarations:
            self.ir.declarations.append(decl)
        self._printf_done = True

    def _ensure_scanf(self):
        decl = "declare i32 @scanf(i8* noundef, ...)"
        if decl not in self.ir.declarations:
            self.ir.declarations.append(decl)
        self._scanf_done = True

    def _add_str(self, text):
        """Global string add karo, ptr return karo."""
        gname, glen = None, 0
        for g in self.ir.globals:
            if f'c"{text}\\00"' in g or \
               text.replace("\n","\\0A") in g:
                # Find existing
                pass
        # Always add new for simplicity
        count = len(self.ir.globals) + 1
        gname = f"@.fstr.{count}"
        escaped = text.replace("\n","\\0A")\
                      .replace("\t","\\09")\
                      .replace('"','\\"')
        glen = len(text.encode()) + 1
        self.ir.globals.append(
            f'{gname} = private unnamed_addr constant '
            f'[{glen} x i8] c"{escaped}\\00"'
        )
        return gname, glen

    def _str_ptr(self, gname, glen):
        ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = getelementptr inbounds "
            f"[{glen} x i8], [{glen} x i8]* "
            f"{gname}, i64 0, i64 0"
        )
        return ptr

    # ==========================================
    # FUNCTION DECLARATION
    # ==========================================

    def emit_func_begin(self, name, return_nimna,
                        params, is_async=False):
        """
        fn name(params) -> ReturnType { ...

        params: list of (param_name, nimna_type)

        Emits:
            define ret_type @name(param_types) {
            entry:

        Returns: (ret_llvm_type, llvm_params)
        """
        ret_llvm   = self._llvm(return_nimna) \
                     if return_nimna else "void"
        llvm_params = [
            (pname, self._llvm(ptype))
            for pname, ptype in params
        ]

        param_str = ", ".join(
            f"{ptype} %{pname}"
            for pname, ptype in llvm_params
        )

        self.ir.lines.append(
            f"define {ret_llvm} @{name}({param_str}) {{"
        )
        self.ir.lines.append("entry:")

        # Register function
        self.func_table[name] = {
            "ret_type"   : ret_llvm,
            "ret_nimna"  : return_nimna,
            "params"     : llvm_params,
            "is_async"   : is_async,
            "is_declared": True,
        }

        self.current_fn  = name
        self.current_ret = ret_llvm
        self._has_return = False

        return ret_llvm, llvm_params

    def emit_func_end(self):
        """
        Function body end karo.
        Agar return nahi hai → auto ret void/0.
        """
        if not self._has_return:
            if self.current_ret == "void":
                self.ir.lines.append("    ret void")
            elif self.current_ret in ("i8*", "i8**"):
                self.ir.lines.append(
                    f"    ret {self.current_ret} null"
                )
            else:
                self.ir.lines.append(
                    f"    ret {self.current_ret} 0"
                )

        self.ir.lines.append("}")
        self.ir.lines.append("")
        self.current_fn  = None
        self.current_ret = None
        self._has_return = False

    def emit_forward_declare(self, name, return_nimna,
                             params):
        """
        Forward declaration (recursive ya cross-call).

        Emits:
            declare ret_type @name(param_types)
        """
        ret_llvm  = self._llvm(return_nimna) \
                    if return_nimna else "void"
        param_str = ", ".join(
            self._llvm(ptype)
            for _, ptype in params
        )
        decl = f"declare {ret_llvm} @{name}({param_str})"
        if decl not in self.ir.declarations:
            self.ir.declarations.append(decl)

        self.func_table[name] = {
            "ret_type"   : ret_llvm,
            "ret_nimna"  : return_nimna,
            "params"     : [(n, self._llvm(t))
                            for n, t in params],
            "is_declared": False,
        }
        return ret_llvm

    # ==========================================
    # RETURN — give
    # ==========================================

    def emit_return(self, value_reg=None,
                    value_type=None):
        """
        give value → ret llvm_type value

        Returns: True
        """
        self._has_return = True

        if self.current_ret == "void" or value_reg is None:
            self.ir.lines.append("    ret void")
            return True

        # Type match karo
        ret = self.current_ret
        if value_type and value_type != ret:
            # Auto coerce
            if value_type in ("i8","i16","i32") \
                    and ret == "i64":
                dest = self.ir.new_temp()
                self.ir.lines.append(
                    f"    {dest} = sext {value_type} "
                    f"{value_reg} to i64"
                )
                value_reg = dest
            elif value_type == "i64" \
                    and ret == "double":
                dest = self.ir.new_temp()
                self.ir.lines.append(
                    f"    {dest} = sitofp i64 "
                    f"{value_reg} to double"
                )
                value_reg = dest

        self.ir.lines.append(
            f"    ret {ret} {value_reg}"
        )
        return True

    def emit_return_void(self):
        """ret void emit karo."""
        self._has_return = True
        self.ir.lines.append("    ret void")

    # ==========================================
    # FUNCTION CALL
    # ==========================================

    def emit_call(self, func_name, arg_regs_types):
        """
        func_name(args) → call instruction

        arg_regs_types: list of (reg, llvm_type)

        Returns: (result_reg, ret_type)
                 result_reg is None for void
        """
        # Built-in function check
        if func_name in BUILTIN_FUNCTIONS:
            return self._emit_builtin_call(
                func_name, arg_regs_types
            )

        # nimna.io / nimna.math prefix
        if func_name.startswith("nimna."):
            return self._emit_nimna_call(
                func_name, arg_regs_types
            )

        # User-defined function
        info = self.func_table.get(func_name)
        if info is None:
            self.errors.append(
                f"Function '{func_name}' not declared."
            )
            return None, "void"

        ret_type  = info["ret_type"]
        arg_str   = ", ".join(
            f"{t} {r}" for r, t in arg_regs_types
        )

        if ret_type == "void":
            self.ir.lines.append(
                f"    call void @{func_name}({arg_str})"
            )
            return None, "void"
        else:
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = call {ret_type} "
                f"@{func_name}({arg_str})"
            )
            return dest, ret_type

    def _emit_builtin_call(self, func_name,
                           arg_regs_types):
        """Built-in function call emit karo."""
        ret_type, _ = BUILTIN_FUNCTIONS[func_name]

        if func_name == "nimna.io.print":
            return self._emit_print(arg_regs_types)
        elif func_name == "nimna.io.write":
            return self._emit_write(arg_regs_types)
        elif func_name == "nimna.io.input":
            return self._emit_input(arg_regs_types)
        elif func_name.startswith("nimna.math."):
            return self._emit_math(func_name,
                                   arg_regs_types)
        return None, ret_type

    def _emit_nimna_call(self, func_name,
                         arg_regs_types):
        """nimna.* call handle karo."""
        if "io.print" in func_name:
            return self._emit_print(arg_regs_types)
        elif "io.input" in func_name:
            return self._emit_input(arg_regs_types)
        elif "io.write" in func_name:
            return self._emit_write(arg_regs_types)
        # Unknown nimna.* → return Wild
        return None, "void"

    # ==========================================
    # nimna.io IMPLEMENTATIONS
    # ==========================================

    def _emit_print(self, arg_regs_types):
        """
        nimna.io.print(msg) → printf

        If arg is i8* → printf("%s\n", msg)
        If arg is i64  → printf("%ld\n", msg)
        If arg is double → printf("%f\n", msg)
        """
        self._ensure_printf()

        if not arg_regs_types:
            # Empty print → newline
            gname, glen = self._add_str("\n")
            ptr = self._str_ptr(gname, glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 "
                f"(i8*, ...) @printf(i8* {ptr})"
            )
            return None, "void"

        arg_reg, arg_type = arg_regs_types[0]

        if arg_type == "i8*":
            # String print
            fmt_gname, fmt_glen = self._add_str("%s\n")
            fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 (i8*, ...) @printf"
                f"(i8* {fmt_ptr}, i8* {arg_reg})"
            )
        elif arg_type in ("double", "fp128"):
            fmt_gname, fmt_glen = self._add_str("%f\n")
            fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 (i8*, ...) @printf"
                f"(i8* {fmt_ptr}, double {arg_reg})"
            )
        elif arg_type == "i1":
            # Truth → print 0 or 1
            ext = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ext} = zext i1 {arg_reg} to i64"
            )
            fmt_gname, fmt_glen = self._add_str("%ld\n")
            fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 (i8*, ...) @printf"
                f"(i8* {fmt_ptr}, i64 {ext})"
            )
        else:
            # Integer
            # Extend to i64 if smaller
            val = arg_reg
            if arg_type in ("i8","i16","i32"):
                ext = self.ir.new_temp()
                self.ir.lines.append(
                    f"    {ext} = sext {arg_type} "
                    f"{arg_reg} to i64"
                )
                val = ext
            fmt_gname, fmt_glen = self._add_str("%ld\n")
            fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 (i8*, ...) @printf"
                f"(i8* {fmt_ptr}, i64 {val})"
            )

        return None, "void"

    def _emit_write(self, arg_regs_types):
        """nimna.io.write — same as print without newline."""
        self._ensure_printf()
        if not arg_regs_types:
            return None, "void"

        arg_reg, arg_type = arg_regs_types[0]
        if arg_type == "i8*":
            fmt_gname, fmt_glen = self._add_str("%s")
            fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
            ret = self.ir.new_temp()
            self.ir.lines.append(
                f"    {ret} = call i32 (i8*, ...) @printf"
                f"(i8* {fmt_ptr}, i8* {arg_reg})"
            )
        return None, "void"

    def _emit_input(self, arg_regs_types):
        """
        nimna.io.input("prompt") → scanf → i8*

        Returns: (buf_ptr, "i8*")
        """
        self._ensure_printf()
        self._ensure_scanf()

        # Print prompt first
        if arg_regs_types:
            self._emit_print(arg_regs_types)

        # Allocate 256-byte buffer
        buf = self.ir.new_temp()
        self.ir.lines.append(
            f"    {buf} = alloca [256 x i8]"
        )
        buf_ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {buf_ptr} = getelementptr inbounds "
            f"[256 x i8], [256 x i8]* {buf}, "
            f"i64 0, i64 0"
        )

        # scanf format
        fmt_gname, fmt_glen = self._add_str("%255s")
        fmt_ptr = self._str_ptr(fmt_gname, fmt_glen)
        ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ret} = call i32 (i8*, ...) @scanf"
            f"(i8* {fmt_ptr}, i8* {buf_ptr})"
        )

        return buf_ptr, "i8*"

    def _emit_math(self, func_name, arg_regs_types):
        """nimna.math.* functions."""
        math_fn = func_name.split(".")[-1]

        if math_fn == "sqrt":
            arg_reg, arg_type = arg_regs_types[0]
            decl = "declare double @llvm.sqrt.f64(double)"
            if decl not in self.ir.declarations:
                self.ir.declarations.append(decl)
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = call double "
                f"@llvm.sqrt.f64(double {arg_reg})"
            )
            return dest, "double"

        elif math_fn == "abs":
            arg_reg, arg_type = arg_regs_types[0]
            decl = "declare double @llvm.fabs.f64(double)"
            if decl not in self.ir.declarations:
                self.ir.declarations.append(decl)
            dest = self.ir.new_temp()
            self.ir.lines.append(
                f"    {dest} = call double "
                f"@llvm.fabs.f64(double {arg_reg})"
            )
            return dest, "double"

        return None, "void"

    # ==========================================
    # STATUS
    # ==========================================

    def is_declared(self, name):
        return name in self.func_table

    def get_return_type(self, name):
        info = self.func_table.get(name)
        return info["ret_type"] if info else None

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
