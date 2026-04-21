# ============================================
# NIMNA Language — LLVM Module Manager
# File: src/codegen/nimna_module.py
# Compiler: nimac
# ============================================

import os
import subprocess
from src.codegen.ir_writer import IRWriter
from src.codegen.type_map  import nimna_to_llvm


# ============================================
# NIMNA MODULE CLASS
# ============================================

class NIMNAModule:
    """
    NIMNA LLVM Module Manager

    Har .nim file ke liye ek Module hota hai.
    Yeh class:
    1. IR writer manage karta hai
    2. Global strings track karta hai
    3. Functions register karta hai
    4. .ll file save karta hai
    5. clang se compile karta hai
    """

    def __init__(self, module_name="nimna_program",
                 source_file="<nimna>"):
        self.module_name    = module_name
        self.source_file    = source_file
        self.ir             = IRWriter(module_name)

        # Registered functions: name → return_type
        self.functions      = {}

        # Global string cache: text → (gname, glen)
        self.string_cache   = {}

        # Current function context
        self.current_fn     = None
        self.current_fn_ret = None

        # Block label counter
        self.block_count    = 0

        # Local variables: name → (llvm_type, ptr_reg)
        self.locals         = {}

        # Standard declarations added?
        self._printf_added  = False
        self._scanf_added   = False

        # Output paths
        self.ll_path        = None
        self.bin_path       = None


    # ==========================================
    # STANDARD LIBRARY SETUP
    # ==========================================

    def setup_std(self):
        """
        Standard external functions declare karo.
        (printf, scanf, malloc, free)
        """
        self.ir.declare_printf()
        self.ir.declare_scanf()
        self.ir.declare_malloc()
        self.ir.declare_free()
        self.ir.declare_strlen()
        self._printf_added = True
        self._scanf_added  = True


    # ==========================================
    # STRING MANAGEMENT
    # ==========================================

    def get_string(self, text):
        """
        Global string get karo ya banao.
        Cache use karta hai duplicate avoid karne ke liye.

        Returns: (global_name, length)
        """
        if text not in self.string_cache:
            gname, glen = self.ir.add_global_string(text)
            self.string_cache[text] = (gname, glen)
        return self.string_cache[text]


    # ==========================================
    # FUNCTION MANAGEMENT
    # ==========================================

    def register_function(self, name, return_nimna_type,
                          param_list):
        """
        Function ko module mein register karo.

        param_list: list of (name, nimna_type)
        """
        llvm_ret = nimna_to_llvm(return_nimna_type)
        llvm_params = [
            (pname, nimna_to_llvm(ptype))
            for pname, ptype in param_list
        ]
        self.functions[name] = {
            "return_type"  : llvm_ret,
            "params"       : llvm_params,
            "nimna_return" : return_nimna_type,
        }
        return llvm_ret, llvm_params

    def begin_function(self, name, return_nimna_type,
                       param_list):
        """
        Function IR likhna shuru karo.
        """
        llvm_ret, llvm_params = self.register_function(
            name, return_nimna_type, param_list
        )
        self.current_fn     = name
        self.current_fn_ret = llvm_ret
        self.locals         = {}
        self.block_count    = 0

        self.ir.begin_function(name, llvm_ret, llvm_params)
        self.ir.entry_block()
        return llvm_ret, llvm_params

    def end_function(self):
        """Function IR khatam karo."""
        self.ir.end_function()
        self.current_fn     = None
        self.current_fn_ret = None
        self.locals         = {}


    # ==========================================
    # LOCAL VARIABLE MANAGEMENT
    # ==========================================

    def declare_local(self, name, nimna_type):
        """
        Local variable ke liye alloca karo.
        Returns: (ptr_register, llvm_type)
        """
        llvm_type = nimna_to_llvm(nimna_type)
        ptr       = self.ir.new_temp()
        self.ir.alloca(ptr, llvm_type)
        self.locals[name] = (llvm_type, ptr)
        return ptr, llvm_type

    def store_local(self, name, value):
        """Local variable mein value store karo."""
        if name in self.locals:
            llvm_type, ptr = self.locals[name]
            self.ir.store(value, llvm_type, ptr)
            return True
        return False

    def load_local(self, name):
        """
        Local variable load karo.
        Returns: (register, llvm_type)
        """
        if name in self.locals:
            llvm_type, ptr = self.locals[name]
            reg = self.ir.new_temp()
            self.ir.load(reg, llvm_type, ptr)
            return reg, llvm_type
        return None, None

    def get_param_reg(self, name):
        """Function parameter ka register naam."""
        return f"%{name}"


    # ==========================================
    # BLOCK LABEL MANAGEMENT
    # ==========================================

    def new_label(self, prefix="block"):
        """Naya unique block label banao."""
        self.block_count += 1
        return f"{prefix}_{self.block_count}"

    def begin_block(self, label):
        """New basic block shuru karo."""
        self.ir.begin_block(label)


    # ==========================================
    # NIMNA.IO FUNCTIONS
    # ==========================================

    def emit_print(self, text_value, is_literal=True):
        """
        nimna.io.print() → printf call emit karo.

        is_literal=True  → text_value ek string hai
        is_literal=False → text_value ek register hai
        """
        if not self._printf_added:
            self.ir.declare_printf()
            self._printf_added = True

        if is_literal:
            # String literal
            gname, glen = self.get_string(text_value + "\n")
            ptr = self.ir.new_temp()
            self.ir.getelementptr(ptr, glen, gname)
            ret = self.ir.new_temp()
            self.ir.call(
                ret, 'i32', 'printf',
                [('i8*', ptr)]
            )
        else:
            # Register se string print
            ret = self.ir.new_temp()
            fmt_gname, fmt_glen = self.get_string("%s\n")
            fmt_ptr = self.ir.new_temp()
            self.ir.getelementptr(fmt_ptr, fmt_glen, fmt_gname)
            self.ir.call(
                ret, 'i32', 'printf',
                [('i8*', fmt_ptr), ('i8*', text_value)]
            )

    def emit_print_int(self, int_register):
        """Integer value print karo."""
        if not self._printf_added:
            self.ir.declare_printf()
            self._printf_added = True

        fmt_gname, fmt_glen = self.get_string("%ld\n")
        fmt_ptr = self.ir.new_temp()
        self.ir.getelementptr(fmt_ptr, fmt_glen, fmt_gname)
        ret = self.ir.new_temp()
        self.ir.call(
            ret, 'i32', 'printf',
            [('i8*', fmt_ptr), ('i64', int_register)]
        )

    def emit_print_float(self, float_register):
        """Float value print karo."""
        if not self._printf_added:
            self.ir.declare_printf()
            self._printf_added = True

        fmt_gname, fmt_glen = self.get_string("%f\n")
        fmt_ptr = self.ir.new_temp()
        self.ir.getelementptr(fmt_ptr, fmt_glen, fmt_gname)
        ret = self.ir.new_temp()
        self.ir.call(
            ret, 'i32', 'printf',
            [('i8*', fmt_ptr), ('double', float_register)]
        )


    # ==========================================
    # COMPILE PIPELINE
    # ==========================================

    def get_ir_text(self):
        """Poora IR text return karo."""
        return self.ir.get_ir()

    def save_ll(self, output_dir=None):
        """
        .ll file save karo.
        Returns: ll file path
        """
        if output_dir is None:
            output_dir = os.path.expanduser("~/tmp")

        os.makedirs(output_dir, exist_ok=True)
        ll_path = os.path.join(
            output_dir, f"{self.module_name}.ll"
        )
        self.ir.save(ll_path)
        self.ll_path = ll_path
        return ll_path

    def compile_to_binary(self, output_dir=None,
                          optimization="-O1"):
        """
        .ll → binary compile karo clang se.

        Returns: (success, binary_path, error_message)
        """
        if output_dir is None:
            output_dir = os.path.expanduser("~/tmp")

        os.makedirs(output_dir, exist_ok=True)

        # Pehle .ll save karo
        ll_path = self.save_ll(output_dir)

        # Binary path
        bin_path = os.path.join(
            output_dir, self.module_name
        )
        self.bin_path = bin_path

        # Clang command
        cmd = [
            "clang",
            optimization,
            ll_path,
            "-o", bin_path,
            "-lm",           # Math library
            "-Wno-override-module",  # Warning suppress
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 30
            )

            if result.returncode == 0:
                return True, bin_path, None
            else:
                return False, None, result.stderr

        except subprocess.TimeoutExpired:
            return False, None, "Compilation timed out"
        except FileNotFoundError:
            return False, None, "clang not found"

    def run_binary(self):
        """
        Compiled binary run karo.
        Returns: (stdout, returncode)
        """
        if not self.bin_path:
            return None, -1

        try:
            result = subprocess.run(
                [self.bin_path],
                capture_output = True,
                text           = True,
                timeout        = 10
            )
            return result.stdout, result.returncode
        except Exception as e:
            return str(e), -1


    # ==========================================
    # MODULE INFO
    # ==========================================

    def get_info(self):
        """Module ki summary print karo."""
        print(f"Module     : {self.module_name}")
        print(f"Source     : {self.source_file}")
        print(f"Functions  : {list(self.functions.keys())}")
        print(f"Globals    : {len(self.ir.globals)}")
        print(f"LL path    : {self.ll_path}")
        print(f"Binary     : {self.bin_path}")
