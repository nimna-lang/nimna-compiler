# ============================================
# NIMNA Language — IR Writer
# File: src/codegen/ir_writer.py
# LLVM IR text file generator
# ============================================

from src.codegen.type_map import nimna_to_llvm


class IRWriter:
    """
    NIMNA IR Writer

    Yeh class LLVM IR text banata hai
    jo .ll file mein save hota hai
    aur clang se compile hota hai.
    """

    def __init__(self, module_name="nimna_module"):
        self.module_name   = module_name
        self.lines         = []
        self.global_count  = 0
        self.temp_count    = 0
        self.globals       = []
        self.declarations  = []


    # ==========================================
    # TEMP VARIABLE GENERATOR
    # ==========================================

    def new_temp(self):
        """Naya temporary register naam do."""
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def new_global(self):
        """Naya global variable naam do."""
        self.global_count += 1
        return f"@g{self.global_count}"

    def reset_temps(self):
        """Function ke baad temps reset karo."""
        self.temp_count = 0


    # ==========================================
    # MODULE HEADER
    # ==========================================

    def write_header(self):
        """Module header likho."""
        self.lines.append(
            f'; ============================================'
        )
        self.lines.append(
            f'; NIMNA Compiler — Generated LLVM IR'
        )
        self.lines.append(
            f'; Module: {self.module_name}'
        )
        self.lines.append(
            f'; ============================================'
        )
        self.lines.append('')


    # ==========================================
    # GLOBAL STRING
    # ==========================================

    def add_global_string(self, text):
        """
        Global string constant add karo.
        Returns: global variable naam
        """
        gname  = self.new_global()
        # Null terminate karo
        escaped = text.replace('\\', '\\\\').replace(
            '"', '\\"').replace('\n', '\\0A')
        length = len(text.encode('utf-8')) + 1
        self.globals.append(
            f'{gname} = private unnamed_addr constant '
            f'[{length} x i8] c"{escaped}\\00"'
        )
        return gname, length


    # ==========================================
    # EXTERNAL DECLARATIONS
    # ==========================================

    def declare_printf(self):
        """printf declare karo (C standard library)."""
        decl = 'declare i32 @printf(i8* noundef, ...)'
        if decl not in self.declarations:
            self.declarations.append(decl)

    def declare_scanf(self):
        """scanf declare karo."""
        decl = 'declare i32 @scanf(i8* noundef, ...)'
        if decl not in self.declarations:
            self.declarations.append(decl)

    def declare_malloc(self):
        """malloc declare karo."""
        decl = 'declare i8* @malloc(i64)'
        if decl not in self.declarations:
            self.declarations.append(decl)

    def declare_free(self):
        """free declare karo."""
        decl = 'declare void @free(i8*)'
        if decl not in self.declarations:
            self.declarations.append(decl)

    def declare_strlen(self):
        """strlen declare karo."""
        decl = 'declare i64 @strlen(i8*)'
        if decl not in self.declarations:
            self.declarations.append(decl)


    # ==========================================
    # FUNCTION
    # ==========================================

    def begin_function(self, name, return_type, params):
        """
        Function definition shuru karo.

        params: list of (name, llvm_type) tuples
        """
        self.reset_temps()
        param_str = ", ".join(
            f"{ptype} %{pname}" for pname, ptype in params
        )
        self.lines.append(
            f'define {return_type} @{name}({param_str}) {{'
        )

    def end_function(self):
        """Function definition khatam karo."""
        self.lines.append('}')
        self.lines.append('')


    # ==========================================
    # BASIC BLOCKS
    # ==========================================

    def begin_block(self, label):
        """Basic block shuru karo."""
        self.lines.append(f'{label}:')

    def entry_block(self):
        """Entry block shuru karo."""
        self.lines.append('entry:')


    # ==========================================
    # INSTRUCTIONS
    # ==========================================

    def alloca(self, var_name, llvm_type):
        """Memory allocate karo."""
        self.lines.append(
            f'    {var_name} = alloca {llvm_type}'
        )

    def store(self, value, llvm_type, ptr):
        """Value store karo."""
        self.lines.append(
            f'    store {llvm_type} {value}, '
            f'{llvm_type}* {ptr}'
        )

    def load(self, dest, llvm_type, ptr):
        """Value load karo."""
        self.lines.append(
            f'    {dest} = load {llvm_type}, '
            f'{llvm_type}* {ptr}'
        )

    def add(self, dest, llvm_type, left, right):
        """Addition."""
        instr = "fadd" if llvm_type == "double" else "add"
        self.lines.append(
            f'    {dest} = {instr} {llvm_type} {left}, {right}'
        )

    def sub(self, dest, llvm_type, left, right):
        """Subtraction."""
        instr = "fsub" if llvm_type == "double" else "sub"
        self.lines.append(
            f'    {dest} = {instr} {llvm_type} {left}, {right}'
        )

    def mul(self, dest, llvm_type, left, right):
        """Multiplication."""
        instr = "fmul" if llvm_type == "double" else "mul"
        self.lines.append(
            f'    {dest} = {instr} {llvm_type} {left}, {right}'
        )

    def div(self, dest, llvm_type, left, right):
        """Division."""
        instr = "fdiv" if llvm_type == "double" else "sdiv"
        self.lines.append(
            f'    {dest} = {instr} {llvm_type} {left}, {right}'
        )

    def rem(self, dest, llvm_type, left, right):
        """Remainder."""
        instr = "frem" if llvm_type == "double" else "srem"
        self.lines.append(
            f'    {dest} = {instr} {llvm_type} {left}, {right}'
        )

    def icmp(self, dest, op, llvm_type, left, right):
        """Integer comparison."""
        op_map = {
            "==" : "eq",  "!=" : "ne",
            ">"  : "sgt", "<"  : "slt",
            ">=" : "sge", "<=" : "sle",
        }
        cmp_op = op_map.get(op, "eq")
        self.lines.append(
            f'    {dest} = icmp {cmp_op} '
            f'{llvm_type} {left}, {right}'
        )

    def fcmp(self, dest, op, llvm_type, left, right):
        """Float comparison."""
        op_map = {
            "==" : "oeq", "!=" : "one",
            ">"  : "ogt", "<"  : "olt",
            ">=" : "oge", "<=" : "ole",
        }
        cmp_op = op_map.get(op, "oeq")
        self.lines.append(
            f'    {dest} = fcmp {cmp_op} '
            f'{llvm_type} {left}, {right}'
        )

    def branch(self, label):
        """Unconditional branch."""
        self.lines.append(f'    br label %{label}')

    def cond_branch(self, cond, true_label, false_label):
        """Conditional branch."""
        self.lines.append(
            f'    br i1 {cond}, '
            f'label %{true_label}, '
            f'label %{false_label}'
        )

    def ret(self, llvm_type, value):
        """Return value."""
        self.lines.append(f'    ret {llvm_type} {value}')

    def ret_void(self):
        """Void return."""
        self.lines.append('    ret void')

    def call(self, dest, ret_type, func_name, args):
        """
        Function call.
        args: list of (llvm_type, value) tuples
        """
        arg_str = ", ".join(
            f"{t} {v}" for t, v in args
        )
        if ret_type == "void":
            self.lines.append(
                f'    call void @{func_name}({arg_str})'
            )
        else:
            self.lines.append(
                f'    {dest} = call {ret_type} '
                f'@{func_name}({arg_str})'
            )

    def getelementptr(self, dest, length, global_name):
        """String pointer get karo."""
        self.lines.append(
            f'    {dest} = getelementptr inbounds '
            f'[{length} x i8], [{length} x i8]* '
            f'{global_name}, i64 0, i64 0'
        )

    def phi(self, dest, llvm_type, pairs):
        """
        Phi node — loop ke liye.
        pairs: list of (value, label) tuples
        """
        pair_str = ", ".join(
            f"[ {v}, %{l} ]" for v, l in pairs
        )
        self.lines.append(
            f'    {dest} = phi {llvm_type} {pair_str}'
        )

    def zext(self, dest, from_type, value, to_type):
        """Zero extend — i1 ko i64 mein."""
        self.lines.append(
            f'    {dest} = zext {from_type} {value} '
            f'to {to_type}'
        )

    def sitofp(self, dest, from_type, value, to_type):
        """Integer to float convert."""
        self.lines.append(
            f'    {dest} = sitofp {from_type} {value} '
            f'to {to_type}'
        )

    def fptosi(self, dest, from_type, value, to_type):
        """Float to integer convert."""
        self.lines.append(
            f'    {dest} = fptosi {from_type} {value} '
            f'to {to_type}'
        )

    def comment(self, text):
        """IR comment add karo."""
        self.lines.append(f'    ; {text}')

    def blank(self):
        """Blank line."""
        self.lines.append('')


    # ==========================================
    # FINALIZE — FULL IR TEXT BANAO
    # ==========================================

    def get_ir(self):
        """
        Poora IR text return karo.
        Header + Globals + Declarations + Functions
        """
        result = []

        # Header
        result.append(
            '; ============================================'
        )
        result.append(
            '; NIMNA Compiler — Generated LLVM IR'
        )
        result.append(
            f'; Module: {self.module_name}'
        )
        result.append(
            '; ============================================'
        )
        result.append('')

        # Global strings
        if self.globals:
            result.append('; --- Global Strings ---')
            result.extend(self.globals)
            result.append('')

        # External declarations
        if self.declarations:
            result.append('; --- External Declarations ---')
            result.extend(self.declarations)
            result.append('')

        # Function bodies
        result.append('; --- Functions ---')
        result.extend(self.lines)

        return '\n'.join(result)

    def save(self, filepath):
        """IR ko file mein save karo."""
        ir_text = self.get_ir()
        with open(filepath, 'w') as f:
            f.write(ir_text)
        return filepath
