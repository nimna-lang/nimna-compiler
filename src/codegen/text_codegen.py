# ============================================
# NIMNA Language — Text IR Generator
# File: src/codegen/text_codegen.py
# Compiler: nimac
# ============================================

# NIMNA text types → LLVM types
TEXT_TYPE_MAP = {
    "Text"   : "i8*",   # String pointer (char*)
    "Letter" : "i8",    # Single character
    "Symbol" : "i32",   # Unicode code point
}

# Format strings for printf
PRINTF_FORMAT = {
    "Text"   : "%s",
    "Letter" : "%c",
    "Symbol" : "%c",
    "Whole"  : "%ld",
    "Decimal": "%f",
    "Truth"  : "%d",
}


class TextCodegen:
    """
    NIMNA Text IR Generator

    Handles:
    1. Text literals   → global string constants
    2. Letter literals → i8 constants
    3. Text variables  → i8* pointer alloca
    4. Text print      → printf call
    5. Text input      → scanf call
    6. Text comparison → strcmp call
    7. Letter operations → char arithmetic
    8. Interpolation   → format string generation
    """

    def __init__(self, ir_writer):
        self.ir           = ir_writer
        self.errors       = []
        self.warnings     = []
        self._str_cache   = {}
        self._str_count   = 0
        self._printf_done = False
        self._scanf_done  = False
        self._strcmp_done = False
        self._strlen_done = False

    # ==========================================
    # DECLARATIONS
    # ==========================================

    def _ensure_printf(self):
        if not self._printf_done:
            if "declare i32 @printf(i8* noundef, ...)" \
                    not in self.ir.declarations:
                self.ir.declarations.append(
                    "declare i32 @printf(i8* noundef, ...)"
                )
            self._printf_done = True

    def _ensure_scanf(self):
        if not self._scanf_done:
            if "declare i32 @scanf(i8* noundef, ...)" \
                    not in self.ir.declarations:
                self.ir.declarations.append(
                    "declare i32 @scanf(i8* noundef, ...)"
                )
            self._scanf_done = True

    def _ensure_strcmp(self):
        if not self._strcmp_done:
            if "declare i32 @strcmp(i8*, i8*)" \
                    not in self.ir.declarations:
                self.ir.declarations.append(
                    "declare i32 @strcmp(i8*, i8*)"
                )
            self._strcmp_done = True

    def _ensure_strlen(self):
        if not self._strlen_done:
            if "declare i64 @strlen(i8*)" \
                    not in self.ir.declarations:
                self.ir.declarations.append(
                    "declare i64 @strlen(i8*)"
                )
            self._strlen_done = True

    # ==========================================
    # LITERAL
    # ==========================================

    def emit_text_literal(self, text):
        """
        Text literal → global string constant.

        Example:
            "Hello NIMNA" →
            @.str.1 = private unnamed_addr constant
                      [13 x i8] c"Hello NIMNA\00"

        Returns: (global_name, length, "i8*")
        """
        if text in self._str_cache:
            gname, glen = self._str_cache[text]
            return gname, glen, "i8*"

        self._str_count += 1
        gname = f"@.str.{self._str_count}"

        # Escape special characters
        escaped = ""
        for ch in text:
            if ch == "\n":
                escaped += "\\0A"
            elif ch == "\t":
                escaped += "\\09"
            elif ch == "\\":
                escaped += "\\\\"
            elif ch == '"':
                escaped += '\\"'
            elif ch == "\r":
                escaped += "\\0D"
            else:
                escaped += ch

        # +1 for null terminator
        glen = len(text.encode("utf-8")) + 1

        self.ir.globals.append(
            f'{gname} = private unnamed_addr constant '
            f'[{glen} x i8] c"{escaped}\\00"'
        )
        self._str_cache[text] = (gname, glen)
        return gname, glen, "i8*"

    def emit_letter_literal(self, char):
        """
        Letter literal → i8 constant.

        Example:
            'A' → 65

        Returns: (ir_value, "i8")
        """
        if len(char) == 1:
            return str(ord(char)), "i8"
        # Multi-char — take first
        return str(ord(char[0])), "i8"

    def emit_symbol_literal(self, char):
        """
        Symbol literal → i32 unicode codepoint.

        Returns: (ir_value, "i32")
        """
        return str(ord(char)), "i32"

    def get_string_ptr(self, gname, glen):
        """
        Global string ka i8* pointer get karo.
        Returns: ptr register
        """
        ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = getelementptr inbounds "
            f"[{glen} x i8], [{glen} x i8]* "
            f"{gname}, i64 0, i64 0"
        )
        return ptr

    # ==========================================
    # VARIABLE
    # ==========================================

    def emit_text_declare(self, var_name,
                          init_gname=None, init_glen=None):
        """
        Text variable declare karo (i8* pointer).
        Returns: (ptr_reg, "i8*")
        """
        ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = alloca i8*"
        )

        if init_gname is not None:
            str_ptr = self.get_string_ptr(init_gname, init_glen)
            self.ir.lines.append(
                f"    store i8* {str_ptr}, i8** {ptr}"
            )

        return ptr, "i8*"

    def emit_text_load(self, ptr):
        """
        Text variable load karo.
        Returns: loaded i8* register
        """
        reg = self.ir.new_temp()
        self.ir.lines.append(
            f"    {reg} = load i8*, i8** {ptr}"
        )
        return reg

    def emit_letter_declare(self, var_name,
                            init_value=None):
        """
        Letter variable declare karo (i8).
        Returns: (ptr_reg, "i8")
        """
        ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ptr} = alloca i8"
        )
        if init_value is not None:
            self.ir.lines.append(
                f"    store i8 {init_value}, i8* {ptr}"
            )
        return ptr, "i8"

    def emit_letter_load(self, ptr):
        """Letter variable load karo."""
        reg = self.ir.new_temp()
        self.ir.lines.append(
            f"    {reg} = load i8, i8* {ptr}"
        )
        return reg

    # ==========================================
    # PRINT — nimna.io.print
    # ==========================================

    def emit_print_text(self, text_reg):
        """
        Text register print karo.
        nimna.io.print("hello") → printf("%s\n", str)
        """
        self._ensure_printf()

        # Format string "%s\n"
        fmt_gname, fmt_glen, _ = self.emit_text_literal(
            "%s\n"
        )
        fmt_ptr = self.get_string_ptr(fmt_gname, fmt_glen)
        ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ret} = call i32 (i8*, ...) @printf"
            f"(i8* {fmt_ptr}, i8* {text_reg})"
        )
        return ret

    def emit_print_literal(self, text):
        """
        String literal seedha print karo.
        Returns: call register
        """
        self._ensure_printf()
        gname, glen, _ = self.emit_text_literal(text + "\n")
        ptr = self.get_string_ptr(gname, glen)
        ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ret} = call i32 (i8*, ...) @printf"
            f"(i8* {ptr})"
        )
        return ret

    def emit_print_letter(self, letter_reg):
        """
        Letter (char) print karo.
        Returns: call register
        """
        self._ensure_printf()
        fmt_gname, fmt_glen, _ = self.emit_text_literal(
            "%c\n"
        )
        fmt_ptr = self.get_string_ptr(fmt_gname, fmt_glen)
        ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ret} = call i32 (i8*, ...) @printf"
            f"(i8* {fmt_ptr}, i8 {letter_reg})"
        )
        return ret

    # ==========================================
    # INPUT — nimna.io.input
    # ==========================================

    def emit_input_text(self, prompt_text,
                        buffer_size=256):
        """
        nimna.io.input("Enter name: ") →
            printf prompt + scanf into buffer.

        Returns: (buffer_ptr, "i8*")
        """
        self._ensure_printf()
        self._ensure_scanf()

        # Print prompt
        if prompt_text:
            self.emit_print_literal(prompt_text
                                    .rstrip("\n"))

        # Allocate buffer
        buf = self.ir.new_temp()
        self.ir.lines.append(
            f"    {buf} = alloca [{buffer_size} x i8]"
        )

        # Get buffer pointer
        buf_ptr = self.ir.new_temp()
        self.ir.lines.append(
            f"    {buf_ptr} = getelementptr inbounds "
            f"[{buffer_size} x i8], "
            f"[{buffer_size} x i8]* {buf}, i64 0, i64 0"
        )

        # scanf format "%255s"
        fmt_str  = f"%{buffer_size - 1}s"
        fmt_gname, fmt_glen, _ = self.emit_text_literal(
            fmt_str
        )
        fmt_ptr = self.get_string_ptr(fmt_gname, fmt_glen)

        # Call scanf
        ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {ret} = call i32 (i8*, ...) @scanf"
            f"(i8* {fmt_ptr}, i8* {buf_ptr})"
        )

        return buf_ptr, "i8*"

    # ==========================================
    # COMPARISON
    # ==========================================

    def emit_compare_text(self, left_reg, op, right_reg):
        """
        Text comparison → strcmp + icmp.

        strcmp returns:
            0  = equal
            <0 = left < right
            >0 = left > right

        Returns: (result_reg, "i1")
        """
        self._ensure_strcmp()

        # Call strcmp
        cmp_ret = self.ir.new_temp()
        self.ir.lines.append(
            f"    {cmp_ret} = call i32 @strcmp"
            f"(i8* {left_reg}, i8* {right_reg})"
        )

        # Compare result
        op_map = {
            "==" : ("icmp eq",  "0"),
            "!=" : ("icmp ne",  "0"),
            ">"  : ("icmp sgt", "0"),
            "<"  : ("icmp slt", "0"),
            ">=" : ("icmp sge", "0"),
            "<=" : ("icmp sle", "0"),
        }
        instr, cmp_val = op_map.get(op, ("icmp eq", "0"))
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = {instr} i32 "
            f"{cmp_ret}, {cmp_val}"
        )
        return dest, "i1"

    def emit_compare_letter(self, left, op, right):
        """
        Letter comparison → icmp on i8.
        Returns: (result_reg, "i1")
        """
        op_map = {
            "==" : "eq",  "!=" : "ne",
            ">"  : "sgt", "<"  : "slt",
            ">=" : "sge", "<=" : "sle",
        }
        cmp_op = op_map.get(op, "eq")
        dest   = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = icmp {cmp_op} i8 {left}, {right}"
        )
        return dest, "i1"

    # ==========================================
    # LENGTH
    # ==========================================

    def emit_strlen(self, text_reg):
        """
        Text length → strlen call.
        Returns: (length_reg, "i64")
        """
        self._ensure_strlen()
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = call i64 @strlen(i8* {text_reg})"
        )
        return dest, "i64"

    # ==========================================
    # LETTER OPERATIONS
    # ==========================================

    def emit_letter_to_int(self, letter_reg):
        """
        Letter → Whole (char code).
        Returns: (result_reg, "i64")
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = sext i8 {letter_reg} to i64"
        )
        return dest, "i64"

    def emit_int_to_letter(self, int_reg):
        """
        Whole → Letter (truncate to char).
        Returns: (result_reg, "i8")
        """
        dest = self.ir.new_temp()
        self.ir.lines.append(
            f"    {dest} = trunc i64 {int_reg} to i8"
        )
        return dest, "i8"

    # ==========================================
    # HELPERS
    # ==========================================

    def get_llvm_type(self, nimna_type):
        return TEXT_TYPE_MAP.get(nimna_type, "i8*")

    def is_text_type(self, nimna_type):
        return nimna_type in TEXT_TYPE_MAP

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def has_errors(self):
        return len(self.errors) > 0
